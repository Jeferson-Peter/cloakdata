from collections import Counter

import polars as pl
import pytest

from cloakdata import anonymize


def test_random_choice_is_deterministic(df_factory, cfg_factory):
    df = df_factory(city=["Curitiba", "Joinville", "São Paulo", "Curitiba"])
    cfg = cfg_factory("random_choice", "city", choices=["X", "Y"], seed=42)

    out1 = anonymize(df, cfg)
    out2 = anonymize(df, cfg)

    assert (
        out1["city"].to_list() == out2["city"].to_list()
    ), "With a fixed seed, random_choice must be deterministic"


def test_random_choice_respects_choices_and_nulls(df_factory, cfg_factory):
    df = df_factory(city=["Curitiba", None, "São Paulo", "Joinville"])
    cfg = cfg_factory("random_choice", "city", choices=["A", "B", "C"], seed=7)

    out = anonymize(df, cfg)
    vals = out["city"].to_list()

    non_null = [v for v in vals if v is not None]
    assert set(non_null).issubset({"A", "B", "C"}), f"Unexpected values: {set(non_null)}"

    assert vals[1] is None, "Nulls should be preserved if present"


def test_shuffle_is_deterministic(df_factory, cfg_factory):
    df = df_factory(city=["A", "B", "C", "D", "E"])
    cfg = cfg_factory("shuffle", "city", seed=123)

    out1 = anonymize(df, cfg)
    out2 = anonymize(df, cfg)

    assert (
        out1["city"].to_list() == out2["city"].to_list()
    ), "With a fixed seed, shuffle must be deterministic"


def test_shuffle_is_permutation_not_identity(df_factory, cfg_factory):
    df = df_factory(city=["A", "B", "C", "D", "E"])
    cfg = cfg_factory("shuffle", "city", seed=999)

    out = anonymize(df, cfg)
    orig = df["city"].to_list()
    res = out["city"].to_list()

    assert Counter(res) == Counter(
        orig
    ), f"Shuffled column must be a permutation of the original: {orig} vs {res}"

    assert res != orig, "Shuffled order should usually differ from original (rare seeds may match)"


def test_shuffle_handles_nulls(df_factory, cfg_factory):
    df = df_factory(city=["A", None, "B", None, "C"])
    cfg = cfg_factory("shuffle", "city", seed=2024)

    out = anonymize(df, cfg)
    orig = df["city"].to_list()
    res = out["city"].to_list()

    assert Counter(res) == Counter(
        orig
    ), f"Shuffle must preserve value counts (including None): {orig} vs {res}"

    assert len(res) == len(orig)


def test_shuffle_without_seed_is_permutation(df_factory, cfg_factory):
    """Without seed, shuffle must still preserve value counts (multiset)."""
    df = df_factory(city=["A", "B", "B", "C", None, "D"])
    cfg = cfg_factory("shuffle", "city")  # no seed

    out = anonymize(df, cfg)
    assert Counter(out["city"].to_list()) == Counter(df["city"].to_list())
    assert out.height == df.height


def test_shuffle_all_nulls_stays_all_nulls(df_factory, cfg_factory):
    """A fully-null column remains fully-null after shuffle."""
    df = df_factory(city=[None, None, None])
    cfg = cfg_factory("shuffle", "city", seed=1)

    out = anonymize(df, cfg)["city"]
    assert out.null_count() == df.height
    assert out.to_list() == [None, None, None]


def test_shuffle_single_element_is_noop(df_factory, cfg_factory):
    """Shuffling a single-element column should keep the same value."""
    df = df_factory(city=["A"])
    cfg = cfg_factory("shuffle", "city", seed=123)

    out = anonymize(df, cfg)["city"].to_list()
    assert out == ["A"]


def test_random_choice_default_choices_preserves_nulls(df_factory, cfg_factory):
    """
    Uses default choices ['X', 'Y'], keeps nulls as null, and returns only values from choices.
    """
    df = df_factory(col=["a", "b", None, "c", "d", None])
    cfg = cfg_factory("random_choice", "col")  # defaults

    out = anonymize(df, cfg)["col"]

    expected_nulls = df["col"].null_count()
    assert out.null_count() == expected_nulls
    non_null = [v for v in out.to_list() if v is not None]
    assert set(non_null).issubset({"X", "Y"})
    assert len(non_null) == df.height - 2


def test_random_choice_deterministic_with_same_seed(df_factory, cfg_factory):
    """
    Same input + same seed must yield the exact same output.
    """
    df = df_factory(col=["a", "b", "c", "d", "e", "f"])
    cfg = cfg_factory("random_choice", "col", choices=["X", "Y", "Z"], seed=123)

    out1 = anonymize(df, cfg)["col"].to_list()
    out2 = anonymize(df, cfg)["col"].to_list()

    assert out1 == out2


def test_random_choice_diff_seed_changes_result_most_of_time(df_factory, cfg_factory):
    """
    Different seeds should generally produce different outputs.
    (Not mathematically guaranteed, but very likely for reasonable lengths.)
    """
    df = df_factory(col=[f"v{i}" for i in range(30)])
    cfg1 = cfg_factory("random_choice", "col", choices=["X", "Y", "Z"], seed=1)
    cfg2 = cfg_factory("random_choice", "col", choices=["X", "Y", "Z"], seed=2)

    out1 = anonymize(df, cfg1)["col"].to_list()
    out2 = anonymize(df, cfg2)["col"].to_list()

    assert out1 != out2


def test_random_choice_does_not_depend_on_input_values(df_factory, cfg_factory):
    """
    Since mapping is index-based, different input values with same length
    should produce the same output for the same seed/choices.
    """
    df1 = df_factory(col=["a", "b", "c", "d", "e"])
    df2 = df_factory(col=["xxx", "yyy", "zzz", "www", "vvv"])
    cfg = cfg_factory("random_choice", "col", choices=["X", "Y"], seed=999)

    out1 = anonymize(df1, cfg)["col"].to_list()
    out2 = anonymize(df2, cfg)["col"].to_list()

    assert out1 == out2


def test_random_choice_empty_choices_raises(df_factory, cfg_factory):
    """
    choices must be non-empty.
    """
    df = df_factory(col=["a", "b", None])
    cfg = cfg_factory("random_choice", "col", choices=[])

    with pytest.raises(ValueError):
        anonymize(df, cfg)


def test_random_choice_all_null_column(df_factory, cfg_factory):
    """
    A fully-null column remains fully-null.
    """
    df = df_factory(col=[None, None, None])
    cfg = cfg_factory("random_choice", "col", choices=["X", "Y"], seed=42)

    out = anonymize(df, cfg)["col"]

    expected_nulls = len(df)
    assert out.null_count() == expected_nulls
    assert out.to_list() == [None, None, None]


def test_random_choice_keeps_output_length_and_dtype(df_factory, cfg_factory):
    """
    Output keeps same length; dtype should be Utf8 (because mapped is a string Series).
    """
    df = df_factory(col=["a", None, "b", "c"])
    cfg = cfg_factory("random_choice", "col", choices=["A", "B"], seed=0)

    out = anonymize(df, cfg)["col"]

    assert out.len() == df.height
    assert out.dtype == pl.Utf8


def test_noise_numeric_is_deterministic(df_factory, cfg_factory):
    df = df_factory(col=[10.0, 20.0, None, 30.0])
    cfg = cfg_factory("noise_numeric", "col", min_delta=-1.5, max_delta=1.5, seed=42)

    out1 = anonymize(df, cfg)["col"].to_list()
    out2 = anonymize(df, cfg)["col"].to_list()

    assert out1 == out2


def test_noise_numeric_preserves_nulls_and_changes_non_nulls(df_factory, cfg_factory):
    df = df_factory(col=[100.0, None, 200.0])
    cfg = cfg_factory("noise_numeric", "col", min_delta=-5.0, max_delta=5.0, seed=7)

    out = anonymize(df, cfg)["col"].to_list()

    assert out[1] is None
    assert out[0] != 100.0
    assert out[2] != 200.0


def test_noise_numeric_respects_delta_bounds(df_factory, cfg_factory):
    df = df_factory(col=[10.0, 20.0, 30.0])
    cfg = cfg_factory("noise_numeric", "col", min_delta=-2.0, max_delta=3.0, seed=1)

    out = anonymize(df, cfg)["col"].to_list()
    original = [10.0, 20.0, 30.0]

    for actual, expected in zip(out, original):
        delta = actual - expected
        assert -2.0 <= delta <= 3.0


def test_noise_numeric_different_seed_changes_output(df_factory, cfg_factory):
    df = df_factory(col=[10.0, 20.0, 30.0, 40.0])

    out1 = anonymize(
        df,
        cfg_factory("noise_numeric", "col", min_delta=-1.0, max_delta=1.0, seed=1),
    )["col"].to_list()
    out2 = anonymize(
        df,
        cfg_factory("noise_numeric", "col", min_delta=-1.0, max_delta=1.0, seed=2),
    )["col"].to_list()

    assert out1 != out2


def test_noise_numeric_requires_bounds(df_factory, cfg_factory):
    df = df_factory(col=[10.0])

    with pytest.raises(ValueError, match="min_delta"):
        anonymize(df, cfg_factory("noise_numeric", "col"))


def test_noise_numeric_rejects_invalid_bounds(df_factory, cfg_factory):
    df = df_factory(col=[10.0])

    with pytest.raises(TypeError, match="must be numeric"):
        anonymize(df, cfg_factory("noise_numeric", "col", min_delta="a", max_delta=1.0))

    with pytest.raises(ValueError, match="cannot be greater"):
        anonymize(df, cfg_factory("noise_numeric", "col", min_delta=2.0, max_delta=1.0))
