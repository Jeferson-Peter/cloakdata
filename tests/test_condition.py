"""
Conditional anonymization test suite.

Covers:
- Single conditions and null handling
- String operators (contains/starts/ends)
- Compound logic (AND lists, logical OR)
- Nested groups (all/any/not)
- Missing target column creation
- Rule ordering/overrides on the same column
"""

from cloakdata import anonymize


def test_condition_apply_only_when_true(df_factory, cfg_factory):
    df = df_factory(age=[22, 31, 41], city=["Curitiba", "Joinville", "São Paulo"])

    cfg = cfg_factory(
        "replace_with_value",
        "city",
        value="REDACTED",
        condition={"col": "age", "op": ">", "value": 30},
    )

    out = anonymize(df, cfg)
    assert out["city"].to_list() == ["Curitiba", "REDACTED", "REDACTED"]


def test_condition_leaves_others_untouched(df_factory, cfg_factory):
    df = df_factory(age=[10, 20, 30], city=["A", "B", "C"])

    cfg = cfg_factory(
        "replace_with_value",
        "city",
        value="X",
        condition={"col": "age", "op": ">", "value": 30},
    )

    out = anonymize(df, cfg)
    assert out["city"].to_list() == ["A", "B", "C"]


def test_condition_on_missing_target_column_creates_and_sets(df_factory, cfg_factory):
    df = df_factory(age=[18, 35, 50])

    cfg = cfg_factory(
        "replace_with_value",
        "flag",
        value="ADULT",
        condition={"col": "age", "op": ">=", "value": 35},
    )

    out = anonymize(df, cfg)
    assert out.columns == ["age", "flag"]
    assert out["flag"].to_list() == [None, "ADULT", "ADULT"]


def test_multiple_rules_on_same_column_with_and_without_condition(df_factory, cfg_factory):
    df = df_factory(age=[25, 40, 60], city=["A", "B", "C"])

    cfg = cfg_factory(
        None,
        "city",
        rules=[
            {"method": "replace_with_value", "params": {"value": "DEFAULT"}},
            {
                "method": "replace_with_value",
                "params": {"value": "COND"},
                "condition": {"col": "age", "op": ">=", "value": 40},
            },
        ],
    )

    out = anonymize(df, cfg)
    assert out["city"].to_list() == ["DEFAULT", "COND", "COND"]


def test_condition_with_nulls_in_condition_column(df_factory, cfg_factory):
    df = df_factory(age=[None, 29, 31], city=["X", "Y", "Z"])

    cfg = cfg_factory(
        "replace_with_value",
        "city",
        value="OK",
        condition={"col": "age", "op": ">", "value": 30},
    )

    out = anonymize(df, cfg)
    assert out["city"].to_list() == ["X", "Y", "OK"]


def test_condition_contains_string(df_factory, cfg_factory):
    df = df_factory(city=["Rua A", "Avenida Central", "Travessa B"])

    cfg = cfg_factory(
        "replace_with_value",
        "city",
        value="MASK",
        condition={"col": "city", "op": "contains", "value": "Avenida"},
    )

    out = anonymize(df, cfg)
    assert out["city"].to_list() == ["Rua A", "MASK", "Travessa B"]


def test_condition_list_and(df_factory, cfg_factory):
    df = df_factory(
        age=[17, 25, 25, 40], country=["BR", "BR", "US", "BR"], city=["A", "B", "C", "D"]
    )

    cfg = cfg_factory(
        "replace_with_value",
        "city",
        value="OK",
        condition=[
            {"col": "country", "op": "in", "value": ["BR", "PT"]},
            {"col": "age", "op": ">=", "value": 25},
        ],
    )

    out = anonymize(df, cfg)
    assert out["city"].to_list() == ["A", "OK", "C", "OK"]


def test_condition_logical_or(df_factory, cfg_factory):
    df = df_factory(
        age=[17, 25, 40, 60], status=["active", "archived", "active", "archived"], city=list("ABCD")
    )

    cfg = cfg_factory(
        "replace_with_value",
        "city",
        value="MASK",
        condition={
            "logical": "or",
            "conditions": [
                {"column": "status", "operator": "equals", "value": "archived"},
                {"column": "age", "operator": "<", "value": 20},
            ],
        },
    )

    out = anonymize(df, cfg)
    assert out["city"].to_list() == ["MASK", "MASK", "C", "MASK"]


def test_condition_all_any_not_nested(df_factory, cfg_factory):
    df = df_factory(
        score=[95, 88, 91, 70],
        region=["EU", "AM", "APAC", "EU"],
        status=["active", "archived", "archived", "active"],
        city=list("WXYZ"),
    )

    cfg = cfg_factory(
        "replace_with_value",
        "city",
        value="HIT",
        condition={
            "any": [
                {
                    "all": [
                        {"col": "score", "op": ">=", "value": 90},
                        {"col": "region", "op": "in", "value": ["EU", "AM"]},
                    ]
                },
                {"not": {"column": "status", "operator": "equals", "value": "archived"}},
            ]
        },
    )

    out = anonymize(df, cfg)
    assert out["city"].to_list() == ["HIT", "X", "Y", "HIT"]


def test_condition_between_inclusive(df_factory, cfg_factory):
    df = df_factory(age=[9, 10, 15, 20, 21], city=list("ABCDE"))

    cfg = cfg_factory(
        "replace_with_value",
        "city",
        value="RANGE",
        condition={"col": "age", "op": "between", "value": [10, 20]},
    )

    out = anonymize(df, cfg)
    assert out["city"].to_list() == ["A", "RANGE", "RANGE", "RANGE", "E"]


def test_condition_startswith_endswith(df_factory, cfg_factory):
    df = df_factory(email=["alice@test.com", "bob@corp.org", "carol@test.com", "dave@x.io"])

    cfg = cfg_factory(
        "replace_with_value",
        "email",
        value="MASK",
        condition={
            "logical": "or",
            "conditions": [
                {"col": "email", "op": "startswith", "value": "alice"},
                {"col": "email", "op": "endswith", "value": "corp.org"},
            ],
        },
    )

    out = anonymize(df, cfg)
    assert out["email"].to_list() == ["MASK", "MASK", "carol@test.com", "dave@x.io"]


def test_condition_is_null_and_not_null(df_factory, cfg_factory):
    df = df_factory(code=[None, "A", None, "B"])

    cfg = cfg_factory(
        None,
        "code",
        rules=[
            {
                "method": "replace_with_value",
                "params": {"value": "NULL"},
                "condition": {"col": "code", "op": "is_null"},
            },
            {
                "method": "replace_with_value",
                "params": {"value": "NOTNULL"},
                "condition": {"col": "code", "op": "not_null"},
            },
        ],
    )

    out = anonymize(df, cfg)
    assert out["code"].to_list() == ["NULL", "NOTNULL", "NULL", "NOTNULL"]


def test_condition_on_missing_target_with_list(df_factory, cfg_factory):
    df = df_factory(age=[18, 35, 50])

    cfg = cfg_factory(
        "replace_with_value",
        "flag",
        value="ADULT",
        condition=[
            {"col": "age", "op": ">=", "value": 35},
            {"col": "age", "op": "<=", "value": 60},
        ],
    )

    out = anonymize(df, cfg)
    assert out.columns == ["age", "flag"]
    assert out["flag"].to_list() == [None, "ADULT", "ADULT"]
