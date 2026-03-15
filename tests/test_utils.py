import polars as pl
import pytest

from cloakdata import anonymize


def test_coalesce_cols_basic(df_factory, cfg_factory):
    df = df_factory(city=[None, "Curitiba", None], email=["a@x.com", "b@x.com", "c@x.com"])
    cfg = cfg_factory("coalesce_cols", "city", columns=["city", "email"])
    out = anonymize(df, cfg)
    assert out["city"].to_list() == ["a@x.com", "Curitiba", "c@x.com"]
    assert set(out.columns) == {"city", "email"}


def test_coalesce_cols_all_nulls_yields_null(df_factory, cfg_factory):
    df = df_factory(a=[None, None], b=[None, None])
    cfg = cfg_factory("coalesce_cols", "a", columns=["a", "b"])
    out = anonymize(df, cfg)
    assert out["a"].to_list() == [None, None]


def test_coalesce_cols_order_matters(df_factory, cfg_factory):
    df = df_factory(primary=[None, "P2", None], backup=["B1", "B2", None], third=["T1", None, "T3"])
    cfg = cfg_factory("coalesce_cols", "primary", columns=["primary", "backup", "third"])
    out = anonymize(df, cfg)
    assert out["primary"].to_list() == ["B1", "P2", "T3"]


def test_coalesce_cols_missing_columns_param_raises(df_factory, cfg_factory):
    df = df_factory(a=[None, "x"])
    try:
        anonymize(df, cfg_factory("coalesce_cols", "a"))
        raise AssertionError("Expected ValueError when columns param is missing")
    except ValueError:
        pass


def test_coalesce_cols_raises_if_any_source_column_missing(df_factory, cfg_factory):
    df = df_factory(a=[None, "x"])
    cfg = cfg_factory("coalesce_cols", "a", columns=["a", "does_not_exist"])
    with pytest.raises(pl.exceptions.ColumnNotFoundError):
        anonymize(df, cfg)


def test_null_if_matches_exact_values(df_factory, cfg_factory):
    df = df_factory(status=["N/A", "active", "", None])
    cfg = cfg_factory("null_if_matches", "status", values=["N/A", ""])

    out = anonymize(df, cfg)["status"].to_list()

    assert out == [None, "active", None, None]


def test_null_if_matches_regex_pattern(df_factory, cfg_factory):
    df = df_factory(doc=["12345678901", "abc", None])
    cfg = cfg_factory("null_if_matches", "doc", pattern=r"^\d{11}$")

    out = anonymize(df, cfg)["doc"].to_list()

    assert out == [None, "abc", None]


def test_null_if_matches_case_insensitive_values(df_factory, cfg_factory):
    df = df_factory(status=["unknown", "UNKNOWN", "Known"])
    cfg = cfg_factory("null_if_matches", "status", values=["UNKNOWN"], case_sensitive=False)

    out = anonymize(df, cfg)["status"].to_list()

    assert out == [None, None, "Known"]


def test_null_if_matches_supports_values_and_pattern(df_factory, cfg_factory):
    df = df_factory(col=["N/A", "unknown", "12345678901", "ok"])
    cfg = cfg_factory(
        "null_if_matches",
        "col",
        values=["N/A", "unknown"],
        pattern=r"^\d{11}$",
    )

    out = anonymize(df, cfg)["col"].to_list()

    assert out == [None, None, None, "ok"]


def test_null_if_matches_requires_values_or_pattern(df_factory, cfg_factory):
    df = df_factory(col=["a"])

    with pytest.raises(ValueError, match="values"):
        anonymize(df, cfg_factory("null_if_matches", "col"))


def test_null_if_matches_requires_list_values(df_factory, cfg_factory):
    df = df_factory(col=["a"])

    with pytest.raises(ValueError, match="must be a list"):
        anonymize(df, cfg_factory("null_if_matches", "col", values="a"))
