import hashlib
import hmac
from copy import deepcopy

import polars as pl
import pytest
from polars import selectors as cs

from cloakdata import TransformationError, anonymize, register_method, unregister_method
from cloakdata.validate import validate


def test_chain_uses_previous_result_and_keeps_other_columns_on_input_snapshot():
    frame = pl.DataFrame({"id": ["SECRET", None], "flag": [True, False]})
    config = {
        "columns": {
            "flag": {"method": "replace_with_value", "params": {"value": False}},
            "id": [
                {
                    "method": "replace_with_value",
                    "params": {"value": "SAFE"},
                    "condition": {"col": "flag", "op": "is_true"},
                },
                {"method": "truncate", "params": {"length": 3}},
            ],
        }
    }
    out = anonymize(frame, config)
    assert out.to_dict(as_series=False) == {"id": ["SAF", None], "flag": [False, False]}


def test_eager_custom_method_receives_previous_stage_and_other_input_columns():
    def use_values(df, col, _params):
        assert df.columns == ["id", "flag"]
        assert df["flag"].to_list() == [True, False]
        return pl.lit(df[col][0].lower())

    name = register_method(use_values)
    try:
        cfg = {
            "columns": {
                "id": [
                    {"method": "replace_with_value", "params": {"value": "SAFE"}},
                    {
                        "method": name,
                        "condition": {"col": "id", "op": "not_null"},
                    },
                ],
                "flag": "full_mask",
            }
        }
        assert anonymize(pl.DataFrame({"id": ["SECRET", None], "flag": [True, False]}), cfg)[
            "id"
        ].to_list() == ["safe", "SAFE"]
    finally:
        unregister_method(name)


@pytest.mark.parametrize("custom_first", [True, False])
def test_custom_wildcard_cannot_see_internal_condition_columns(custom_first):
    def mask_without_consent(_df, col, _params):
        return pl.when(pl.any_horizontal(cs.boolean())).then(pl.col(col)).otherwise(pl.lit("MASK"))

    name = register_method(mask_without_consent)
    try:
        frame = pl.DataFrame(
            {"id": ["sample-a", "sample-b"], "flag": [1, 0], "retain": [False, False]}
        )
        condition = {"col": "flag", "op": "equals", "value": 1}
        truncate = {"method": "truncate", "params": {"length": 6}}
        if custom_first:
            rules = [{"method": name, "condition": condition}, truncate]
        else:
            rules = [truncate, {"method": name, "condition": condition}]
        assert anonymize(frame, {"columns": {"id": rules}})["id"].to_list() == ["MASK", "sample"]
    finally:
        unregister_method(name)


def test_eager_native_method_receives_previous_stage():
    df = pl.DataFrame({"id": ["id-a", "id-b", "hide-c"]})
    rules = [
        {"method": "truncate", "params": {"length": 2}},
        {"method": "top_k_bucket", "params": {"k": 1}},
    ]
    assert anonymize(df, {"columns": {"id": rules}})["id"].to_list() == ["id", "id", "OTHER"]


@pytest.mark.parametrize("config", [None, {}, {"columns": []}, {"columns": {1: "full_mask"}}])
def test_malformed_config_shape(config):
    df = pl.DataFrame({"id": ["sample"]})
    with pytest.raises(ValueError, match="[Cc]olumn"):
        validate(config)
    with pytest.raises(ValueError, match="[Cc]olumn"):
        anonymize(df, config)


@pytest.mark.parametrize(
    "rule",
    [
        [],
        "full_maks",
        ["drop", "full_mask"],
        {"method": []},
        {"method": "full_mask", "params": []},
        {"method": "full_mask", "params": {"preserve_nulls": "false"}},
        {"method": "full_mask", "conditions": []},
        {"method": "truncate", "params": {"length": -1}},
        {"method": "round_date", "params": {"mode": "typo"}},
        {"method": "coalesce_cols", "params": {"columns": "id"}},
        {"method": "random_choice", "params": {"choices": "ab"}},
        {"method": "replace_exact", "params": {"mapping": []}},
        {"method": "full_mask", "condition": {}},
        {"method": "full_mask", "condition": {"col": "flag", "op": "in", "value": "yes"}},
        {"method": "full_mask", "condition": {"conditions": [{}], "logical": "xor"}},
        {
            "method": "full_mask",
            "condition": {"all": [{"col": "flag", "op": "is_true"}, {"col": "flag", "op": "typo"}]},
        },
        {"method": "drop", "condition": {"col": "flag", "op": "is_true"}},
    ],
)
def test_config_rejected_by_validation_and_execution(rule):
    config = {"columns": {"id": rule}}
    with pytest.raises(ValueError, match="id"):
        validate(config)
    with pytest.raises(ValueError, match="id"):
        anonymize(pl.DataFrame({"id": ["secret"], "flag": [True]}), config)


def test_missing_columns_and_string_drop():
    df = pl.DataFrame({"id": ["secret"], "keep": [1]})
    with pytest.raises(ValueError, match="missing_target"):
        anonymize(df, {"columns": {"missing_target": "full_mask"}})
    rule = {"method": "full_mask", "condition": {"col": "missing_predicate", "value": True}}
    with pytest.raises(ValueError, match="missing_predicate"):
        anonymize(df, {"columns": {"id": rule}})
    assert anonymize(df, {"columns": {"id": "drop"}}).columns == ["keep"]


def test_conditional_creation_keeps_zero_row_count():
    rule = {
        "method": "full_mask",
        "params": {"preserve_nulls": False},
        "condition": {"col": "target", "op": "is_null"},
    }
    out = anonymize(pl.DataFrame(), {"columns": {"target": rule}})
    assert out.shape == (0, 1)


def test_execution_errors_are_distinct_from_configuration_errors():
    df = pl.DataFrame({"id": ["nonnumeric"]})
    config = {"columns": {"id": "generalize_age"}}
    validate(config)
    with pytest.raises(TransformationError) as raised:
        anonymize(df, config)
    assert isinstance(raised.value.__cause__, pl.exceptions.PolarsError)


@pytest.mark.parametrize(
    ("rule", "context"),
    [
        ({"method": "redact_regex", "params": {"pattern": "["}}, "redact_regex"),
        ({"method": "null_if_matches", "params": {"pattern": "(?=a)"}}, "null_if_matches"),
        (
            {"method": "replace_by_contains", "params": {"mapping": {"[": "x"}, "use_regex": True}},
            "replace_by_contains",
        ),
        (
            {
                "method": "replace_by_contains",
                "params": {"substr": "[", "replacement": "x", "use_regex": True},
            },
            "replace_by_contains",
        ),
        (
            {
                "method": "full_mask",
                "condition": {"all": [{"col": "id", "op": "contains", "value": "["}]},
            },
            "contains",
        ),
        (
            {
                "method": "full_mask",
                "condition": {"not": {"col": "id", "op": "not_contains", "value": "["}},
            },
            "not_contains",
        ),
    ],
)
def test_invalid_patterns_fail_before_execution(rule, context):
    config = {"columns": {"id": rule}}
    with pytest.raises(ValueError, match=rf"id.*{context}.*invalid regex"):
        validate(config)
    with pytest.raises(ValueError, match=rf"id.*{context}.*invalid regex"):
        anonymize(pl.DataFrame(schema={"id": pl.String}), config)


def test_regex_validation_uses_polars_dialect_and_preserves_literal_matches():
    df = pl.DataFrame({"letters": ["ação", "12"], "literal": ["[", "]"]})
    config = {
        "columns": {
            "letters": {"method": "redact_regex", "params": {"pattern": r"\p{L}+"}},
            "literal": {
                "method": "replace_by_contains",
                "params": {"substr": "[", "replacement": "x"},
            },
        }
    }
    validate(config)
    assert anonymize(df, config).to_dict(as_series=False) == {
        "letters": ["[REDACTED]", "12"],
        "literal": ["x", "]"],
    }


def test_is_false_preserves_legacy_behavior_for_missing_flags():
    df = pl.DataFrame({"id": ["A", "B", "C"], "flag": [False, True, None]})
    rule = {"method": "full_mask", "condition": {"col": "flag", "op": "is_false"}}
    assert anonymize(df, {"columns": {"id": rule}})["id"].to_list() == ["*****", "B", "*****"]


@pytest.mark.parametrize("use_regex", [False, True])
def test_substring_replacement_matches_original_value_once(use_regex):
    config = {
        "columns": {
            "id": {
                "method": "replace_by_contains",
                "params": {
                    "mapping": {"FIRST": "SECOND", "SECOND": "MASK"},
                    "use_regex": use_regex,
                    "case_sensitive": False,
                },
            }
        }
    }
    df = pl.DataFrame({"id": ["first", "first second", "second", None]})
    assert anonymize(df, config)["id"].to_list() == ["SECOND", "SECOND", "MASK", None]


def test_hash_opt_in_null_encoding_preserves_existing_digest_for_non_null_input():
    config = {
        "columns": {
            "id": {
                "method": "hash_value",
                "params": {
                    "salt": "salt",
                    "preserve_nulls": False,
                },
            }
        }
    }
    df = pl.DataFrame({"id": ["ação", None]})
    expected = [hashlib.sha256(f"salt{value}".encode()).hexdigest() for value in ("ação", "")]
    assert anonymize(df, config)["id"].to_list() == expected


@pytest.mark.parametrize(
    ("method", "params"),
    [
        ("full_mask", {"match_length": True}),
        ("mask_number", {"keep": 0}),
        ("mask_partial", {"visible_start": 0, "visible_end": 0}),
    ],
)
def test_mask_treats_newlines_and_replacement_characters_literally(method, params):
    df = pl.DataFrame({"id": ["é\n", None, ""]})
    rule = {"method": method, "params": {**params, "mask_char": "$0"}}
    assert anonymize(df, {"columns": {"id": rule}})["id"].to_list() == ["$0$0", None, ""]


def test_hmac_sha256_is_stable_and_keyed():
    df = pl.DataFrame({"id": ["ação", None, "ação", ""]})
    key = bytes(range(32))
    config = {"columns": {"id": {"method": "hmac_value", "params": {"key": key}}}}
    validate(config)
    expected = hmac.digest(key, "ação".encode(), "sha256").hex()
    blank = hmac.digest(key, b"", "sha256").hex()
    assert anonymize(df, config)["id"].to_list() == [expected, None, expected, blank]
    assert anonymize(df.head(0), config).schema == df.schema
    changed = deepcopy(config)
    changed["columns"]["id"]["params"]["key"] = bytes(reversed(key))
    assert anonymize(df, changed)["id"][0] != expected


@pytest.mark.parametrize("params", [{}, {"key": b"short"}, {"key": "a" * 32}])
def test_hmac_rejects_missing_weak_or_wrong_type_keys(params):
    config = {"columns": {"id": {"method": "hmac_value", "params": params}}}
    with pytest.raises(ValueError, match="key"):
        validate(config)
    with pytest.raises(ValueError, match="key"):
        anonymize(pl.DataFrame({"id": ["sample"]}), config)
