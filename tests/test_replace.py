import random

import pytest
from polars import Boolean, Utf8

from cloakdata import anonymize

EXPECTED_DIGITS = 8


def test_replace_exact(city_df, cfg_factory):
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


def test_replace_with_random_digits_generates_digit_strings(df_factory, cfg_factory):
    df = df_factory(doc=["123", "456", "789"])
    cfg = cfg_factory("replace_with_random_digits", "doc", digits=8)

    random.seed(42)

    out = anonymize(df, cfg)
    values = out["doc"].to_list()

    assert all(
        len(v) == EXPECTED_DIGITS and v.isdigit() for v in values
    ), f"Expected 8-digit numeric strings, got {values}"

    assert values != df["doc"].to_list(), "Output should not match original values"
