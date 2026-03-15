import hashlib

import pytest
from polars import Boolean, Utf8

from cloakdata import anonymize

EXPECTED_DIGITS = 8
DEFAULT_DIGITS = 11
NULL_COUNT_TWO = 2
NULL_COUNT_THREE = 3


def test_replace_exact(city_df, cfg_factory):
    """Replaces values that exactly match mapping keys, leaves others unchanged."""
    cfg = cfg_factory("replace_exact", "city", mapping={"Curitiba": "CWB"})
    out = anonymize(city_df, cfg)
    assert out["city"].to_list() == ["CWB", "Joinville", "São Paulo"]


def test_replace_by_contains_requires_mapping_or_substr(df_factory, cfg_factory):
    """Raises ValueError if neither 'mapping' nor 'substr' is provided."""
    df = df_factory(txt=["foo", "bar", None])
    cfg = cfg_factory("replace_by_contains", "txt")
    with pytest.raises(ValueError):
        anonymize(df, cfg)


def test_replace_by_contains_literal_match(df_factory, cfg_factory):
    """Replaces values when they contain given substrings (literal matching)."""
    df = df_factory(txt=["foo", "bar", "baz", None])
    cfg = cfg_factory(
        "replace_by_contains",
        "txt",
        mapping={"ba": "X"},
    )
    out = anonymize(df, cfg)["txt"].to_list()
    assert out == ["foo", "X", "X", None]


def test_replace_by_contains_regex_enabled(df_factory, cfg_factory):
    """Supports regex when use_regex=True."""
    df = df_factory(txt=["id=123", "noid", "id=999", None])
    cfg = cfg_factory(
        "replace_by_contains",
        "txt",
        mapping={r"\d{3}": "HIT"},
        use_regex=True,
    )
    out = anonymize(df, cfg)["txt"].to_list()
    assert out == ["HIT", "noid", "HIT", None]


def test_replace_by_contains_case_insensitive(df_factory, cfg_factory):
    """Case-insensitive matching when case_sensitive=False."""
    df = df_factory(txt=["Hello", "heLLo", "world", None])
    cfg = cfg_factory(
        "replace_by_contains",
        "txt",
        mapping={"hello": "X"},
        case_sensitive=False,
    )
    out = anonymize(df, cfg)["txt"].to_list()
    assert out == ["X", "X", "world", None]


def test_replace_by_contains_first_match_wins(df_factory, cfg_factory):
    """Rules are applied left-to-right; the first matching rule wins."""
    df = df_factory(txt=["foobar", "barfoo", "xx", None])
    mapping = {"foo": "A", "bar": "B"}
    cfg = cfg_factory("replace_by_contains", "txt", mapping=mapping)
    out = anonymize(df, cfg)["txt"].to_list()
    assert out == ["A", "A", "xx", None]


def test_replace_by_contains_single_substr_convenience(df_factory, cfg_factory):
    """Works with single 'substr' + 'replacement' convenience params."""
    df = df_factory(txt=["abc", "zzz", None])
    cfg = cfg_factory(
        "replace_by_contains",
        "txt",
        substr="ab",
        replacement="HIT",
    )
    out = anonymize(df, cfg)["txt"].to_list()
    assert out == ["HIT", "zzz", None]


def test_replace_with_value_requires_value(df_factory, cfg_factory):
    """Raises ValueError if no 'value' parameter is provided."""
    df = df_factory(col=["a", None])
    cfg = cfg_factory("replace_with_value", "col")
    with pytest.raises(ValueError):
        anonymize(df, cfg)


def test_replace_with_value_preserves_dtype_and_nulls(df_factory, cfg_factory):
    """Preserves dtype of 'value' and respects preserve_nulls=True."""
    df = df_factory(col=[1, None, 2])
    cfg = cfg_factory("replace_with_value", "col", value=123, preserve_nulls=True)
    out = anonymize(df, cfg)["col"]
    assert out.to_list() == [123, None, 123]
    assert out.dtype.is_integer()

    df2 = df_factory(col=[0.1, None, 9.9])
    cfg2 = cfg_factory("replace_with_value", "col", value=3.14)
    out2 = anonymize(df2, cfg2)["col"]
    assert out2.to_list() == [3.14, 3.14, 3.14]
    assert out2.dtype.is_float()

    df3 = df_factory(col=[True, None, False])
    cfg3 = cfg_factory("replace_with_value", "col", value=False, preserve_nulls=True)
    out3 = anonymize(df3, cfg3)["col"]
    assert out3.to_list() == [False, None, False]
    assert out3.dtype == Boolean

    df4 = df_factory(col=["a", None, "b"])
    cfg4 = cfg_factory("replace_with_value", "col", value="X")
    out4 = anonymize(df4, cfg4)["col"]
    assert out4.to_list() == ["X", "X", "X"]
    assert out4.dtype == Utf8


def test_replace_with_random_digits_default_len_and_nulls(df_factory, cfg_factory):
    """
    Default behavior: generates 11-digit strings for non-null values and preserves nulls.
    """
    df = df_factory(doc=["a", None, "b", "c", None])
    cfg = cfg_factory("replace_with_random_digits", "doc")  # digits=11, seed=0 by default

    out = anonymize(df, cfg)["doc"]

    assert out.null_count() == NULL_COUNT_TWO

    values = out.to_list()
    for v in values:
        if v is None:
            continue
        assert isinstance(v, str)
        assert len(v) == DEFAULT_DIGITS
        assert v.isdigit()


def test_replace_with_random_digits_custom_digits(df_factory, cfg_factory):
    """
    Custom digits length must be respected for all non-null values.
    """
    digits = 5
    df = df_factory(doc=["x", "y", None])
    cfg = cfg_factory("replace_with_random_digits", "doc", digits=digits, seed=123)

    out = anonymize(df, cfg)["doc"].to_list()

    assert out[2] is None
    assert len(out[0]) == digits
    assert len(out[1]) == digits
    assert out[0].isdigit()
    assert out[1].isdigit()


def test_replace_with_random_digits_is_deterministic_with_seed(df_factory, cfg_factory):
    """
    Same length + same seed + same number of rows must yield the exact same output.
    (Note: mapping is index-based, not value-based.)
    """
    df = df_factory(doc=["a", "b", "c", "d", "e"])
    cfg = cfg_factory("replace_with_random_digits", "doc", digits=8, seed=42)

    out1 = anonymize(df, cfg)["doc"].to_list()
    out2 = anonymize(df, cfg)["doc"].to_list()

    assert out1 == out2


def test_replace_with_random_digits_diff_seed_changes_output(df_factory, cfg_factory):
    """
    Different seeds should generally produce different outputs.
    """
    df = df_factory(doc=[f"v{i}" for i in range(30)])
    cfg1 = cfg_factory("replace_with_random_digits", "doc", digits=10, seed=1)
    cfg2 = cfg_factory("replace_with_random_digits", "doc", digits=10, seed=2)

    out1 = anonymize(df, cfg1)["doc"].to_list()
    out2 = anonymize(df, cfg2)["doc"].to_list()

    assert out1 != out2


def test_replace_with_random_digits_does_not_depend_on_input_values(df_factory, cfg_factory):
    """
    Since mapping is index-based, changing the input values (but keeping the same length)
    should not change the output for the same seed/digits.
    """
    df1 = df_factory(doc=["a", "b", "c", "d", "e"])
    df2 = df_factory(doc=["xxx", "yyy", "zzz", "www", "vvv"])
    cfg = cfg_factory("replace_with_random_digits", "doc", digits=6, seed=999)

    out1 = anonymize(df1, cfg)["doc"].to_list()
    out2 = anonymize(df2, cfg)["doc"].to_list()

    assert out1 == out2


def test_replace_with_random_digits_all_null_column(df_factory, cfg_factory):
    """
    A fully-null column remains fully-null (no accidental string generation).
    """
    df = df_factory(doc=[None, None, None])
    cfg = cfg_factory("replace_with_random_digits", "doc", digits=7, seed=0)

    out = anonymize(df, cfg)["doc"]

    assert out.null_count() == NULL_COUNT_THREE
    assert out.to_list() == [None, None, None]


@pytest.mark.parametrize("digits", [0, -1, -10])
def test_replace_with_random_digits_invalid_digits_raises(df_factory, cfg_factory, digits):
    """
    digits must be a positive integer.
    """
    df = df_factory(doc=["a"])

    with pytest.raises(ValueError):
        anonymize(df, cfg_factory("replace_with_random_digits", "doc", digits=digits))


def test_replace_with_random_digits_non_int_digits_raises(df_factory, cfg_factory):
    """
    digits must be int (e.g., '11' should raise).
    """
    df = df_factory(doc=["a"])

    with pytest.raises(ValueError):
        anonymize(df, cfg_factory("replace_with_random_digits", "doc", digits="11"))


def test_replace_with_random_digits_keeps_length_and_utf8(df_factory, cfg_factory):
    """
    Output keeps the same length and should be Utf8 dtype.
    """
    df = df_factory(doc=["a", None, "b", "c"])
    cfg = cfg_factory("replace_with_random_digits", "doc", digits=4, seed=0)

    out_df = anonymize(df, cfg)
    out = out_df["doc"]

    assert out_df.height == df.height
    assert out.dtype == Utf8


def test_hash_value_default_sha256_and_nulls(df_factory, cfg_factory):
    df = df_factory(col=["alice@example.com", None, "bob@example.com"])
    cfg = cfg_factory("hash_value", "col")

    out = anonymize(df, cfg)["col"].to_list()

    assert out[0] == hashlib.sha256(b"alice@example.com").hexdigest()
    assert out[1] is None
    assert out[2] == hashlib.sha256(b"bob@example.com").hexdigest()


def test_hash_value_with_salt_is_deterministic(df_factory, cfg_factory):
    df = df_factory(col=["alice@example.com", "alice@example.com"])
    cfg = cfg_factory("hash_value", "col", salt="team-2026")

    out = anonymize(df, cfg)["col"].to_list()
    expected = hashlib.sha256(b"team-2026alice@example.com").hexdigest()

    assert out == [expected, expected]


def test_hash_value_salt_changes_output(df_factory, cfg_factory):
    df = df_factory(col=["alice@example.com"])
    out1 = anonymize(df, cfg_factory("hash_value", "col", salt="salt-a"))["col"].to_list()
    out2 = anonymize(df, cfg_factory("hash_value", "col", salt="salt-b"))["col"].to_list()

    assert out1 != out2


def test_hash_value_supports_non_string_inputs(df_factory, cfg_factory):
    df_int = df_factory(col=[12345, 67890])
    df_bool = df_factory(col=[True, False])
    cfg = cfg_factory("hash_value", "col")

    out_int = anonymize(df_int, cfg)["col"].to_list()
    out_bool = anonymize(df_bool, cfg)["col"].to_list()

    assert out_int[0] == hashlib.sha256(b"12345").hexdigest()
    assert out_int[1] == hashlib.sha256(b"67890").hexdigest()
    assert out_bool[0] == hashlib.sha256(str(True).encode("utf-8")).hexdigest()
    assert out_bool[1] == hashlib.sha256(str(False).encode("utf-8")).hexdigest()


def test_hash_value_invalid_algorithm_raises(df_factory, cfg_factory):
    df = df_factory(col=["alice@example.com"])
    cfg = cfg_factory("hash_value", "col", algorithm="not-real")

    with pytest.raises(ValueError, match="Unsupported hash algorithm"):
        anonymize(df, cfg)


def test_redact_regex_requires_pattern(df_factory, cfg_factory):
    df = df_factory(txt=["alice@example.com"])
    cfg = cfg_factory("redact_regex", "txt")

    with pytest.raises(ValueError, match="pattern"):
        anonymize(df, cfg)


def test_redact_regex_replaces_matches_in_free_text(df_factory, cfg_factory):
    df = df_factory(txt=["Contact alice@example.com for details", "no email here", None])
    cfg = cfg_factory(
        "redact_regex",
        "txt",
        pattern=r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        replacement="[EMAIL]",
    )

    out = anonymize(df, cfg)["txt"].to_list()

    assert out == ["Contact [EMAIL] for details", "no email here", None]


def test_redact_regex_uses_default_replacement(df_factory, cfg_factory):
    df = df_factory(txt=["CPF 12345678901", "doc 98765432100"])
    cfg = cfg_factory("redact_regex", "txt", pattern=r"\d{11}")

    out = anonymize(df, cfg)["txt"].to_list()

    assert out == ["CPF [REDACTED]", "doc [REDACTED]"]


def test_redact_regex_supports_non_string_columns(df_factory, cfg_factory):
    df = df_factory(txt=[12345678901, None, 98765432100])
    cfg = cfg_factory("redact_regex", "txt", pattern=r"\d{11}", replacement="[DOC]")

    out = anonymize(df, cfg)["txt"].to_list()

    assert out == ["[DOC]", None, "[DOC]"]


def test_replace_with_hash_bucket_is_deterministic(df_factory, cfg_factory):
    df = df_factory(col=["alice", "bob", None, "alice"])
    cfg = cfg_factory("replace_with_hash_bucket", "col", buckets=10, prefix="group", seed=42)

    out1 = anonymize(df, cfg)["col"].to_list()
    out2 = anonymize(df, cfg)["col"].to_list()

    assert out1 == out2


def test_replace_with_hash_bucket_preserves_nulls_and_prefix(df_factory, cfg_factory):
    df = df_factory(col=["alice", None, "bob"])
    cfg = cfg_factory("replace_with_hash_bucket", "col", buckets=8, prefix="bucket")

    out = anonymize(df, cfg)["col"].to_list()

    assert out[0].startswith("bucket_")
    assert out[1] is None
    assert out[2].startswith("bucket_")


def test_replace_with_hash_bucket_same_input_same_bucket(df_factory, cfg_factory):
    df = df_factory(col=["alice", "alice", "bob"])
    cfg = cfg_factory("replace_with_hash_bucket", "col", buckets=10, prefix="grp", seed=7)

    out = anonymize(df, cfg)["col"].to_list()

    assert out[0] == out[1]
    assert out[0].startswith("grp_")


def test_replace_with_hash_bucket_different_seed_changes_output(df_factory, cfg_factory):
    df = df_factory(col=["alice", "bob", "charlie"])

    out1 = anonymize(
        df,
        cfg_factory("replace_with_hash_bucket", "col", buckets=10, prefix="group", seed=1),
    )["col"].to_list()
    out2 = anonymize(
        df,
        cfg_factory("replace_with_hash_bucket", "col", buckets=10, prefix="group", seed=2),
    )["col"].to_list()

    assert out1 != out2


@pytest.mark.parametrize("buckets", [0, -1, "10"])
def test_replace_with_hash_bucket_invalid_buckets_raises(df_factory, cfg_factory, buckets):
    df = df_factory(col=["alice"])
    cfg = cfg_factory("replace_with_hash_bucket", "col", buckets=buckets)

    with pytest.raises(ValueError, match="buckets"):
        anonymize(df, cfg)
