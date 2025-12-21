from datetime import date, datetime

import pytest

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


def test_generalize_date_default_month_from_strings(df_factory, cfg_factory):
    """Default mode='month': reduce ISO strings to YYYY-MM."""
    df = df_factory(dt=["2024-05-17", "2024-12-01"])
    cfg = cfg_factory("generalize_date", "dt")  # mode default is "month"

    out = anonymize(df, cfg)["dt"].to_list()
    assert out == ["2024-05", "2024-12"]


def test_generalize_date_year_mode_with_nulls(df_factory, cfg_factory):
    """mode='year' keeps only the year and preserves nulls."""
    df = df_factory(dt=["2024-05-17", None, "1999-01-01"])
    cfg = cfg_factory("generalize_date", "dt", mode="year")

    out = anonymize(df, cfg)["dt"]
    assert out.to_list() == ["2024", None, "1999"]
    assert out.null_count() == 1


def test_generalize_date_month_from_date_type(df_factory, cfg_factory):
    """mode='month' works with Python date objects."""
    df = df_factory(
        dt=[
            date(2024, 5, 17),
            date(2025, 1, 1),
        ]
    )
    cfg = cfg_factory("generalize_date", "dt", mode="month")

    out = anonymize(df, cfg)["dt"].to_list()
    assert out == ["2024-05", "2025-01"]


def test_generalize_date_quarter(df_factory, cfg_factory):
    """mode='quarter' returns labels like YYYY-Q1 based on calendar quarter."""
    df = df_factory(
        dt=[
            "2024-01-10",  # Q1
            "2024-03-31",  # Q1
            "2024-04-01",  # Q2
            "2024-06-30",  # Q2
            "2024-07-01",  # Q3
            "2024-09-30",  # Q3
            "2024-10-01",  # Q4
            "2024-12-31",  # Q4
        ]
    )
    cfg = cfg_factory("generalize_date", "dt", mode="quarter")

    out = anonymize(df, cfg)["dt"].to_list()
    assert out == [
        "2024-Q1",
        "2024-Q1",
        "2024-Q2",
        "2024-Q2",
        "2024-Q3",
        "2024-Q3",
        "2024-Q4",
        "2024-Q4",
    ]


def test_generalize_date_semester(df_factory, cfg_factory):
    """mode='semester' maps months 1–6 to S1 and 7–12 to S2."""
    df = df_factory(
        dt=[
            "2024-01-10",  # S1
            "2024-06-30",  # S1
            "2024-07-01",  # S2
            "2024-12-31",  # S2
        ]
    )
    cfg = cfg_factory("generalize_date", "dt", mode="semester")

    out = anonymize(df, cfg)["dt"].to_list()
    assert out == ["2024-S1", "2024-S1", "2024-S2", "2024-S2"]


def test_generalize_date_week_truncation(df_factory, cfg_factory):
    """
    mode='week' truncates to the start of the week and formats as YYYY-Www.

    Weeks are aligned with Monday. Example (2024):
      - 2024-05-01 (Wed) → 2024-W18
      - 2024-05-05 (Sun) → 2024-W18
      - 2024-05-06 (Mon) → 2024-W19
    """
    df = df_factory(
        dt=[
            date(2024, 5, 1),
            date(2024, 5, 5),
            date(2024, 5, 6),
        ]
    )
    cfg = cfg_factory("generalize_date", "dt", mode="week")

    out = anonymize(df, cfg)["dt"].to_list()
    assert out == ["2024-W18", "2024-W18", "2024-W19"]


def test_generalize_date_mode_date(df_factory, cfg_factory):
    """mode='date' keeps only the calendar date (YYYY-MM-DD)."""
    df = df_factory(
        dt=[
            datetime(2024, 5, 1, 10, 30, 45),
            datetime(2024, 12, 31, 23, 59, 59),
        ]
    )
    cfg = cfg_factory("generalize_date", "dt", mode="date")

    out = anonymize(df, cfg)["dt"].to_list()
    assert out == ["2024-05-01", "2024-12-31"]


def test_generalize_date_mode_datetime(df_factory, cfg_factory):
    """mode='datetime' formats full timestamp as ISO-like YYYY-MM-DDTHH:MM:SS."""
    df = df_factory(
        dt=[
            datetime(2024, 5, 1, 10, 30, 45),
            datetime(2024, 5, 1, 0, 0, 0),
        ]
    )
    cfg = cfg_factory("generalize_date", "dt", mode="datetime")

    out = anonymize(df, cfg)["dt"].to_list()
    assert out == ["2024-05-01T10:30:45", "2024-05-01T00:00:00"]


def test_generalize_date_preserves_nulls(df_factory, cfg_factory):
    """Null values are preserved in all modes."""
    df = df_factory(dt=[None, "2024-05-17"])
    cfg = cfg_factory("generalize_date", "dt", mode="month")

    out = anonymize(df, cfg)["dt"]
    assert out.to_list() == [None, "2024-05"]
    assert out.null_count() == 1


def test_generalize_number_range_buckets(df_factory, cfg_factory):
    df = df_factory(num=[-1.2, 0.0, 2.5, 42.0, None])
    cfg = cfg_factory("generalize_number_range", "num", interval=10)

    out = anonymize(df, cfg)
    vals = [v for v in out["num"].to_list() if v is not None]

    assert set(vals) == {"-10 to -1", "0 to 9", "40 to 49"}
    assert out.height == df.height


def test_generalize_number_range_preserves_nulls(df_factory, cfg_factory):
    df = df_factory(num=[None, -1.0, 2.5, 42.0])
    cfg = cfg_factory("generalize_number_range", "num", interval=10)

    out = anonymize(df, cfg)

    assert out["num"][0] is None
    assert out["num"].to_list()[1:] == [
        "-10 to -1",
        "0 to 9",
        "40 to 49",
    ]


def test_generalize_number_range_boundary_values(df_factory, cfg_factory):
    """
    Values exactly on bucket boundaries must fall into the correct range.
    """
    df = df_factory(num=[0, 9, 10, 19, 20, 29])
    cfg = cfg_factory("generalize_number_range", "num", interval=10)

    out = anonymize(df, cfg)["num"].to_list()

    assert out == [
        "0 to 9",
        "0 to 9",
        "10 to 19",
        "10 to 19",
        "20 to 29",
        "20 to 29",
    ]


def test_generalize_number_range_negative_boundaries(df_factory, cfg_factory):
    """
    Negative values must map correctly using the same separator.
    """
    df = df_factory(num=[-20, -11, -10, -1, 0])
    cfg = cfg_factory("generalize_number_range", "num", interval=10)

    out = anonymize(df, cfg)["num"].to_list()

    assert out == [
        "-20 to -11",
        "-20 to -11",
        "-10 to -1",
        "-10 to -1",
        "0 to 9",
    ]


def test_generalize_number_range_all_null_column(df_factory, cfg_factory):
    """
    A fully-null column must remain fully null.
    """
    df = df_factory(num=[None, None])
    cfg = cfg_factory("generalize_number_range", "num", interval=10)

    out = anonymize(df, cfg)["num"]

    assert out.to_list() == [None, None]
    assert out.null_count() == len(out)


@pytest.mark.parametrize("interval", [0, -1, -10])
def test_generalize_number_range_invalid_interval_raises(df_factory, cfg_factory, interval):
    """
    Interval must be a positive integer.
    """
    df = df_factory(num=[1, 2, 3])
    cfg = cfg_factory("generalize_number_range", "num", interval=interval)

    with pytest.raises(ValueError):
        anonymize(df, cfg)


def test_generalize_number_range_non_int_interval_raises(df_factory, cfg_factory):
    """
    Non-integer intervals should raise an error.
    """
    df = df_factory(num=[1, 2, 3])
    cfg = cfg_factory("generalize_number_range", "num", interval=2.5)

    with pytest.raises(ValueError):
        anonymize(df, cfg)
