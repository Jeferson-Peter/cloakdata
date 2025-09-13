from collections import Counter

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
