import re

import polars as pl

from cloakdata import anonymize


def excel_letters(n: int) -> list[str]:
    out = []
    for i in range(1, n + 1):
        s = ""
        x = i
        while x > 0:
            x, r = divmod(x - 1, 26)
            s = chr(65 + r) + s
        out.append(s)
    return out


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


def test_sequential_alpha_basic(df_factory, cfg_factory):
    df = df_factory(col=["x", "y", "z"])
    cfg = cfg_factory("sequential_alpha", "col", start="A")

    out = anonymize(df, cfg)
    assert out["col"].to_list() == ["A", "B", "C"], f"Expected A,B,C; got {out['col'].to_list()}"


def test_sequential_alpha_wraps_after_z(df_factory, cfg_factory):
    n = 28
    df = df_factory(col=[f"v{i}" for i in range(n)])
    cfg = cfg_factory("sequential_alpha", "col", start="A")

    out = anonymize(df, cfg)
    expected = excel_letters(n)
    assert (
        out["col"].to_list() == expected
    ), f"Expected {expected[-3:]} at the tail; got {out['col'].to_list()[-3:]}"


def test_sequential_numeric_duplicates_with_prefix(df_factory, cfg_factory):
    """Duplicates receive the same label; number of distinct labels equals #unique values."""
    df = df_factory(col=["Alice", "Bob", "Alice", "Carol", "Bob"])
    cfg = cfg_factory("sequential_numeric", "col", start=1, prefix="val")

    out = anonymize(df, cfg)["col"].to_list()

    assert out[0] == out[2], "Same value should map to the same label (Alice)"
    assert out[1] == out[4], "Same value should map to the same label (Bob)"
    assert out[3] != out[0] and out[3] != out[1], "Different value should get a different label"

    unique_inputs = len(set(df["col"].to_list()))
    assert len(set(out)) == unique_inputs


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
    df = df_factory(col=[10, 20, 10, True, False, True])  # uniques: {10,20,True,False} => 4 labels
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
