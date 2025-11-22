import re

import polars as pl

from cloakdata import anonymize


def _numeric_suffixes(labels: list[str], prefix: str) -> list[int]:
    """Extract numeric suffixes from labels like 'val 12'. Assumes consistent
    '<prefix> <n>' pattern."""
    out = []
    pat = re.compile(rf"^{re.escape(prefix)}\s+(\d+)$")
    for s in labels:
        m = pat.match(s)
        assert m, f"Label '{s}' does not match pattern '{prefix} <n>'"
        out.append(int(m.group(1)))
    return out


def test_sequential_alpha_duplicates_share_label(df_factory, cfg_factory):
    """Duplicates reuse the same alphabetic label; first appearance defines order."""
    df = df_factory(col=["Alice", "Bob", "Alice", "Carol", "Bob"])
    cfg = cfg_factory("sequential_alpha", "col", start="A", prefix="val")
    out = anonymize(df, cfg)["col"].to_list()
    assert out[0] == out[2] and out[1] == out[4] and out[3] != out[0] != out[1]


def test_sequential_alpha_custom_start_wraps(df_factory, cfg_factory):
    """Start near 'Z' wraps to AA, AB, ..."""
    df = df_factory(col=[f"v{i}" for i in range(5)])
    cfg = cfg_factory("sequential_alpha", "col", start="X", prefix=None)
    out = anonymize(df, cfg)["col"].to_list()
    assert out == ["X", "Y", "Z", "AA", "AB"]


def test_sequential_alpha_lowercase_start(df_factory, cfg_factory):
    """Lowercase start is accepted (normalized)."""
    df = df_factory(col=["u1", "u2", "u3"])
    cfg = cfg_factory("sequential_alpha", "col", start="a", prefix="val")
    out = anonymize(df, cfg)["col"].to_list()
    assert out == ["val A", "val B", "val C"]


def test_sequential_alpha_prefix_none(df_factory, cfg_factory):
    """With prefix=None, output is plain letters (Utf8)."""
    df = df_factory(col=["x", "y", "x", "z"])
    cfg = cfg_factory("sequential_alpha", "col", start="A", prefix=None)
    s = anonymize(df, cfg)["col"]
    assert s.dtype == pl.Utf8
    assert s.to_list() == ["A", "B", "A", "C"]


def test_sequential_alpha_preserves_height(df_factory, cfg_factory):
    """Row count preserved."""
    df = df_factory(col=["x"] * 7)
    cfg = cfg_factory("sequential_alpha", "col", start="A", prefix="val")
    out = anonymize(df, cfg)
    assert out.height == df.height


def test_sequential_numeric_start_and_range_with_prefix(df_factory, cfg_factory):
    """Numeric parts are a contiguous range starting at 'start' with size == #unique values."""
    df = df_factory(col=["a", "b", "c", "a"])  # 3 uniques
    start = 10
    prefix = "val"
    cfg = cfg_factory("sequential_numeric", "col", start=start, prefix=prefix)

    out = anonymize(df, cfg)["col"].to_list()
    uniq_labels = sorted(set(out))
    nums = sorted(_numeric_suffixes(uniq_labels, prefix))

    assert nums == list(range(start, start + len(nums))), f"Expected contiguous range from {start}"


def test_sequential_numeric_dtype_switch_by_prefix(df_factory, cfg_factory):
    df = df_factory(col=["x", "y", "x"])
    out_none = anonymize(df, cfg_factory("sequential_numeric", "col", start=5, prefix=None))["col"]
    assert out_none.dtype.is_integer()

    out_str = anonymize(df, cfg_factory("sequential_numeric", "col", start=5, prefix="val"))["col"]
    assert out_str.dtype == pl.Utf8


def test_sequential_numeric_handles_nulls(df_factory, cfg_factory):
    """Nulls are mapped consistently as well (current behavior), counting as a unique category."""
    df = df_factory(col=["a", None, "a", "b", None, "b"])  # uniques: {"a","b",None} => 3 labels
    cfg = cfg_factory("sequential_numeric", "col", start=1, prefix="val")

    out = anonymize(df, cfg)["col"].to_list()
    assert out[1] == out[4], "Nulls should map to the same label"
    assert out[1] is not None, "Nulls are currently mapped to a label (not preserved)"

    assert out[0] == out[2]
    assert out[3] == out[5]

    uniq_inputs = len(set(df["col"].to_list()))
    assert len(set(out)) == uniq_inputs


def test_sequential_numeric_non_string_inputs(df_factory, cfg_factory):
    """Works with non-strings (ints/bools) and still groups equal values into same id."""
    df = df_factory(col=[10, 20, 10, True, False, True])
    cfg = cfg_factory("sequential_numeric", "col", start=1, prefix="val")

    out = anonymize(df, cfg)["col"].to_list()

    assert out[0] == out[2]
    assert out[3] == out[5]
    assert out[1] != out[0] and out[1] != out[3] and out[1] != out[4]

    expected_unique = 4
    assert len(set(out)) == expected_unique


def test_sequential_numeric_large_cardinality(df_factory, cfg_factory):
    """Scales to many uniques and generates the correct count of distinct labels."""
    n = 200
    df = df_factory(col=[f"id{i}" for i in range(n)])
    cfg = cfg_factory("sequential_numeric", "col", start=1, prefix="val")

    out = anonymize(df, cfg)["col"].to_list()
    assert len(set(out)) == n, "Each distinct input should yield a distinct label"
