from cloakdata import anonymize


def test_generalize_age_decades_basic(df_factory, cfg_factory):
    df = df_factory(age=[25, 41, 0, 9, 10, 19, 20, 29])
    cfg = cfg_factory("generalize_age", "age")

    out = anonymize(df, cfg)
    expected = ["20-29", "40-49", "0-9", "0-9", "10-19", "10-19", "20-29", "20-29"]
    assert out["age"].to_list() == expected


def test_generalize_age_preserves_nulls(df_factory, cfg_factory):
    df = df_factory(age=[25, None, 41])
    cfg = cfg_factory("generalize_age", "age")

    out = anonymize(df, cfg)["age"].to_list()

    assert out == ["20-29", None, "40-49"]


def test_generalize_age_float_input(df_factory, cfg_factory):
    df = df_factory(age=[25.9, 41.2, 9.99])
    cfg = cfg_factory("generalize_age", "age")

    out = anonymize(df, cfg)["age"].to_list()

    assert out == ["20-29", "40-49", "0-9"]


def test_generalize_age_custom_bucket(df_factory, cfg_factory):
    df = df_factory(age=[25, 26, 27])
    cfg = cfg_factory("generalize_age", "age", size=5)

    out = anonymize(df, cfg)["age"].to_list()

    assert out == ["25-29", "25-29", "25-29"]


def test_generalize_date_defaults_to_month_year(df_factory, cfg_factory):
    df = df_factory(d=["2024-01-15", "1999-12-31", None])
    cfg = cfg_factory("generalize_date", "d")

    out = anonymize(df, cfg)
    result = out["d"].to_list()

    assert result[0] == "2024-01"
    assert result[1] == "1999-12"
    assert result[2] is None


def test_generalize_date_to_year(df_factory, cfg_factory):
    df = df_factory(d=["2024-01-15", "1999-12-31", None])
    cfg = cfg_factory("generalize_date", "d", mode="year")

    out = anonymize(df, cfg)
    result = out["d"].to_list()

    assert result[0] == "2024"
    assert result[1] == "1999"
    assert result[2] is None


def test_generalize_date_invalid_mode(df_factory, cfg_factory):
    df = df_factory(d=["2024-01-15", "1999-12-31"])
    cfg = cfg_factory("generalize_date", "d", mode="invalid")

    out = anonymize(df, cfg)
    result = set(out["d"].to_list())

    assert result == {"invalid_mode"}, f"Expected all 'invalid_mode', got {result}"


def test_generalize_number_range_buckets(df_factory, cfg_factory):
    df = df_factory(num=[-1.2, 0.0, 2.5, 42.0, None])
    cfg = cfg_factory("generalize_number_range", "num", interval=10)

    out = anonymize(df, cfg)
    vals = [v for v in out["num"].to_list() if v is not None]

    assert set(vals) == {"-10--1", "0-9", "40-49"}
    assert out.height == df.height


def test_generalize_number_range_preserves_nulls(df_factory, cfg_factory):
    df = df_factory(num=[None, -1.0, 2.5, 42.0])
    cfg = cfg_factory("generalize_number_range", "num", interval=10)

    out = anonymize(df, cfg)

    assert out["num"][0] is None

    assert out["num"].to_list()[1:] == ["-10--1", "0-9", "40-49"]
