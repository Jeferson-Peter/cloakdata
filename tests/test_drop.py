import polars as pl
from polars.testing import assert_frame_equal

from cloakdata import anonymize


def _cols_except(df: pl.DataFrame, drops: set[str]) -> list[str]:
    return [c for c in df.columns if c not in drops]


def test_drop_single_existing_column(base_df, cfg_factory):
    cfg = cfg_factory("drop", "age")

    out = anonymize(base_df, cfg)

    assert "age" not in out.columns, f"'age' should be dropped, got columns: {out.columns}"
    assert (
        out.height == base_df.height
    ), f"Row count mismatch: expected {base_df.height}, got {out.height}"

    expected_cols = _cols_except(base_df, {"age"})
    assert out.columns == expected_cols, f"Expected columns {expected_cols}, got {out.columns}"
    assert_frame_equal(out.select(out.columns), base_df.drop("age"))

    assert "age" in base_df.columns


def test_drop_unknown_is_noop(base_df, cfg_factory):
    cfg = cfg_factory("drop", "no_such_col")

    out = anonymize(base_df, cfg)

    assert out.shape == base_df.shape, f"Expected shape {base_df.shape}, got {out.shape}"
    assert_frame_equal(out, base_df)
    assert out is not base_df, "anonymize() should return a new DataFrame instance"


def test_drop_multiple_columns(base_df):
    cfg = {
        "columns": {
            "age": {"method": "drop"},
            "city": {"method": "drop"},
        }
    }

    out = anonymize(base_df, cfg)

    drops = {"age", "city"}
    expected_cols = _cols_except(base_df, drops)

    assert all(
        col not in out.columns for col in drops
    ), f"Columns {drops} should be dropped, got {out.columns}"
    assert out.columns == expected_cols, f"Expected columns {expected_cols}, got {out.columns}"
    assert out.height == base_df.height
    assert_frame_equal(out.select(out.columns), base_df.drop(list(drops)))


def test_drop_mixed_existing_and_unknown(base_df):
    cfg = {
        "columns": {
            "age": {"method": "drop"},
            "nope": {"method": "drop"},
        }
    }

    out = anonymize(base_df, cfg)

    expected_cols = _cols_except(base_df, {"age"})
    assert "age" not in out.columns and "nope" not in out.columns
    assert out.columns == expected_cols
    assert out.height == base_df.height
    assert_frame_equal(out.select(out.columns), base_df.drop("age"))
