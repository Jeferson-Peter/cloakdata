import polars as pl

from cloakdata import anonymize


def test_full_mask(city_df, cfg_factory):
    cfg = cfg_factory("full_mask", "city")
    out = anonymize(city_df, cfg)
    assert all(v == "*****" for v, s in zip(out["city"], city_df["city"], strict=False))


def test_mask_partial(city_df, cfg_factory):
    cfg = cfg_factory("mask_partial", "city", prefix=1, suffix=1, mask="*")
    out = anonymize(city_df, cfg)
    assert len(out["city"][0]) == len(city_df["city"][0])
    assert out["city"][0][0] == city_df["city"][0][0]
    assert out["city"][0][-1] == city_df["city"][0][-1]


def test_truncate(city_df, cfg_factory):
    cfg = cfg_factory("truncate", "city", length=3)
    out = anonymize(city_df, cfg)
    assert out["city"].to_list() == [s[:3] for s in city_df["city"].to_list()]


def test_mask_number(numeric_df, cfg_factory):
    cfg = cfg_factory("mask_number", "num", keep=1, mask="X")
    out = anonymize(numeric_df, cfg)
    assert out["num"].dtype == pl.Utf8
