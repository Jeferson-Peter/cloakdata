import random

from cloakdata import anonymize

EXPECTED_DIGITS = 8


def test_replace_exact(city_df, cfg_factory):
    cfg = cfg_factory("replace_exact", "city", mapping={"Curitiba": "CWB"})
    out = anonymize(city_df, cfg)
    assert out["city"].to_list() == ["CWB", "Joinville", "São Paulo"]


def test_replace_by_contains(city_df, cfg_factory):
    cfg = cfg_factory("replace_by_contains", "city", mapping={"São": "SP"})
    out = anonymize(city_df, cfg)
    assert out["city"].to_list() == ["Curitiba", "Joinville", "SP"]


def test_replace_with_value(city_df, cfg_factory):
    cfg = cfg_factory("replace_with_value", "city", value="REDACTED")
    out = anonymize(city_df, cfg)
    assert out["city"].to_list() == ["REDACTED"] * 3


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
