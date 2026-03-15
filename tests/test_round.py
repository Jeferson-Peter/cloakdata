from datetime import date

from cloakdata import anonymize

MAX_DELTA_DAYS = 3


def test_round_number_digits(df_factory, cfg_factory):
    df = df_factory(num=[1.234, 5.678, None, 9.0])
    cfg = cfg_factory("round_number", "num", digits=1)
    out = anonymize(df, cfg)
    assert out["num"].to_list() == [1.2, 5.7, None, 9.0]


def test_round_number_zero_digits(df_factory, cfg_factory):
    df = df_factory(num=[1.6, 2.4, -2.6])
    cfg = cfg_factory("round_number", "num", digits=0)
    out = anonymize(df, cfg)
    assert out["num"].to_list() == [2.0, 2.0, -3.0]


def test_round_date_to_month(df_factory, cfg_factory):
    df = df_factory(d=["2024-01-15", "1999-12-31", None])
    cfg = cfg_factory("round_date", "d", mode="month")
    out = anonymize(df, cfg)
    vals = out["d"].to_list()
    assert vals[0] == "2024-01-01"
    assert vals[1] == "1999-12-01"
    assert vals[2] is None


def test_round_date_to_year(df_factory, cfg_factory):
    df = df_factory(d=["2024-01-15", "1999-12-31"])
    cfg = cfg_factory("round_date", "d", mode="year")
    out = anonymize(df, cfg)
    assert out["d"].to_list() == ["2024-01-01", "1999-01-01"]


def test_round_date_invalid_values_become_invalid(df_factory, cfg_factory):
    df = df_factory(d=["2024-01-15", "not-a-date", None])
    cfg = cfg_factory("round_date", "d", mode="month")
    out = anonymize(df, cfg)
    assert out["d"].to_list() == ["2024-01-01", "invalid", None]


def test_date_offset_is_deterministic_and_within_bounds(df_factory, cfg_factory):
    df = df_factory(d=["2024-01-10", "2024-01-20", None])
    min_days, max_days, seed = 1, 3, 123

    cfg = cfg_factory("date_offset", "d", min_days=min_days, max_days=max_days, seed=seed)

    out1 = anonymize(df, cfg)
    out2 = anonymize(df, cfg)

    assert out1["d"].to_list() == out2["d"].to_list()

    def parse(s: str | None) -> date | None:
        return None if s is None else date.fromisoformat(s)

    for orig, new in zip(df["d"].to_list(), out1["d"].to_list(), strict=False):
        if orig is None:
            assert new is None
            continue

        d0, d1 = parse(orig), parse(new)
        delta = (d1 - d0).days  # signed

        assert min_days <= delta <= max_days
