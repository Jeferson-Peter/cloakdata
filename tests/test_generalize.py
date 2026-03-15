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


def test_top_k_bucket_keeps_most_frequent_values(df_factory, cfg_factory):
    df = df_factory(city=["SP", "SP", "RJ", "RJ", "MG", "BA", None])
    cfg = cfg_factory("top_k_bucket", "city", k=2, other_label="OTHER")

    out = anonymize(df, cfg)["city"].to_list()

    assert out == ["SP", "SP", "RJ", "RJ", "OTHER", "OTHER", None]


def test_top_k_bucket_preserves_nulls(df_factory, cfg_factory):
    df = df_factory(city=[None, "SP", "MG"])
    cfg = cfg_factory("top_k_bucket", "city", k=1)

    out = anonymize(df, cfg)["city"].to_list()

    assert out[0] is None


def test_top_k_bucket_uses_custom_other_label(df_factory, cfg_factory):
    df = df_factory(city=["SP", "RJ", "MG", "BA"])
    cfg = cfg_factory("top_k_bucket", "city", k=1, other_label="RARE")

    out = anonymize(df, cfg)["city"].to_list()

    assert out.count("RARE") == 3


def test_top_k_bucket_is_deterministic_on_ties(df_factory, cfg_factory):
    df = df_factory(city=["B", "A", "C", "B", "A", "D"])
    cfg = cfg_factory("top_k_bucket", "city", k=2, other_label="OTHER")

    out = anonymize(df, cfg)["city"].to_list()

    assert out == ["B", "A", "OTHER", "B", "A", "OTHER"]


@pytest.mark.parametrize("k", [0, -1, "2"])
def test_top_k_bucket_invalid_k_raises(df_factory, cfg_factory, k):
    df = df_factory(city=["SP", "RJ"])
    cfg = cfg_factory("top_k_bucket", "city", k=k)

    with pytest.raises(ValueError):
        anonymize(df, cfg)


def test_generalize_zip_code_masks_suffix(df_factory, cfg_factory):
    df = df_factory(zip_code=["81320-000", "10001", None])
    cfg = cfg_factory("generalize_zip_code", "zip_code", visible_prefix=3)

    out = anonymize(df, cfg)["zip_code"].to_list()

    assert out == ["813**-***", "100**", None]


def test_generalize_zip_code_preserves_short_values(df_factory, cfg_factory):
    df = df_factory(zip_code=["123", "12", "1"])
    cfg = cfg_factory("generalize_zip_code", "zip_code", visible_prefix=3)

    out = anonymize(df, cfg)["zip_code"].to_list()

    assert out == ["123", "12", "1"]


def test_generalize_zip_code_supports_custom_mask_char(df_factory, cfg_factory):
    df = df_factory(zip_code=["12345-6789"])
    cfg = cfg_factory("generalize_zip_code", "zip_code", visible_prefix=5, mask_char="#")

    out = anonymize(df, cfg)["zip_code"].to_list()

    assert out == ["12345-####"]


def test_generalize_zip_code_supports_alphanumeric_postal_codes(df_factory, cfg_factory):
    df = df_factory(zip_code=["SW1A 1AA"])
    cfg = cfg_factory("generalize_zip_code", "zip_code", visible_prefix=4)

    out = anonymize(df, cfg)["zip_code"].to_list()

    assert out == ["SW1A ***"]


@pytest.mark.parametrize("visible_prefix", [-1, "3"])
def test_generalize_zip_code_invalid_visible_prefix_raises(
    df_factory, cfg_factory, visible_prefix
):
    df = df_factory(zip_code=["81320-000"])
    cfg = cfg_factory("generalize_zip_code", "zip_code", visible_prefix=visible_prefix)

    with pytest.raises(ValueError, match="visible_prefix"):
        anonymize(df, cfg)


def test_coarsen_datetime_bucket_hour(df_factory, cfg_factory):
    df = df_factory(dt=["2024-05-01T14:37:22", "2024-05-01T00:05:00", None])
    cfg = cfg_factory("coarsen_datetime", "dt", mode="bucket", minutes=60)

    out = anonymize(df, cfg)["dt"].to_list()

    assert out == ["2024-05-01T14:00:00", "2024-05-01T00:00:00", None]


def test_coarsen_datetime_bucket_15_minutes(df_factory, cfg_factory):
    df = df_factory(dt=["2024-05-01T14:37:22", "2024-05-01T14:14:59"])
    cfg = cfg_factory("coarsen_datetime", "dt", mode="bucket", minutes=15)

    out = anonymize(df, cfg)["dt"].to_list()

    assert out == ["2024-05-01T14:30:00", "2024-05-01T14:00:00"]


def test_coarsen_datetime_minute_of_day_bucket(df_factory, cfg_factory):
    df = df_factory(dt=["2024-05-01T14:37:22", "2024-05-01T09:12:00", None])
    cfg = cfg_factory("coarsen_datetime", "dt", mode="minute_of_day_bucket", minutes=30)

    out = anonymize(df, cfg)["dt"].to_list()

    assert out == ["14:30", "09:00", None]


def test_coarsen_datetime_minute_of_day_bucket_datetime_output(df_factory, cfg_factory):
    df = df_factory(dt=["2024-05-01T14:37:22"])
    cfg = cfg_factory(
        "coarsen_datetime",
        "dt",
        mode="minute_of_day_bucket",
        minutes=30,
        output="datetime",
    )

    out = anonymize(df, cfg)["dt"].to_list()

    assert out == ["2024-05-01T14:30:00"]


def test_coarsen_datetime_invalid_values_become_invalid(df_factory, cfg_factory):
    df = df_factory(dt=["not-a-datetime", None])
    cfg = cfg_factory("coarsen_datetime", "dt", mode="bucket", minutes=30)

    out = anonymize(df, cfg)["dt"].to_list()

    assert out == ["invalid", None]


def test_coarsen_datetime_part_of_day(df_factory, cfg_factory):
    df = df_factory(
        dt=[
            "2024-05-01T02:00:00",
            "2024-05-01T08:30:00",
            "2024-05-01T14:00:00",
            "2024-05-01T20:15:00",
            None,
        ]
    )
    cfg = cfg_factory("coarsen_datetime", "dt", mode="part_of_day")

    out = anonymize(df, cfg)["dt"].to_list()

    assert out == ["night", "morning", "afternoon", "evening", None]


def test_coarsen_datetime_part_of_day_invalid_values_become_invalid(df_factory, cfg_factory):
    df = df_factory(dt=["bad-value", None])
    cfg = cfg_factory("coarsen_datetime", "dt", mode="part_of_day")

    out = anonymize(df, cfg)["dt"].to_list()

    assert out == ["invalid", None]


def test_coarsen_datetime_hour(df_factory, cfg_factory):
    df = df_factory(dt=["2024-05-01T14:37:22", "2024-05-01T00:59:59"])
    cfg = cfg_factory("coarsen_datetime", "dt", mode="hour")

    out = anonymize(df, cfg)["dt"].to_list()

    assert out == ["2024-05-01T14:00:00", "2024-05-01T00:00:00"]


def test_coarsen_datetime_weekday(df_factory, cfg_factory):
    df = df_factory(dt=["2024-05-01T14:37:22", "2024-05-04T10:00:00"])
    cfg = cfg_factory("coarsen_datetime", "dt", mode="weekday")

    out = anonymize(df, cfg)["dt"].to_list()

    assert out == ["wednesday", "saturday"]


def test_coarsen_datetime_weekend_weekday(df_factory, cfg_factory):
    df = df_factory(dt=["2024-05-01T14:37:22", "2024-05-04T10:00:00"])
    cfg = cfg_factory("coarsen_datetime", "dt", mode="weekend_weekday")

    out = anonymize(df, cfg)["dt"].to_list()

    assert out == ["weekday", "weekend"]


def test_coarsen_datetime_business_hours(df_factory, cfg_factory):
    df = df_factory(
        dt=[
            "2024-05-01T10:00:00",
            "2024-05-01T20:00:00",
            "2024-05-04T10:00:00",
        ]
    )
    cfg = cfg_factory("coarsen_datetime", "dt", mode="business_hours")

    out = anonymize(df, cfg)["dt"].to_list()

    assert out == ["business_hours", "off_hours", "off_hours"]


def test_coarsen_datetime_business_hours_custom_range(df_factory, cfg_factory):
    df = df_factory(
        dt=[
            "2024-05-01T08:00:00",
            "2024-05-01T17:59:59",
            "2024-05-01T18:00:00",
        ]
    )
    cfg = cfg_factory(
        "coarsen_datetime",
        "dt",
        mode="business_hours",
        start_hour=8,
        end_hour=18,
    )

    out = anonymize(df, cfg)["dt"].to_list()

    assert out == ["business_hours", "business_hours", "off_hours"]


def test_coarsen_datetime_business_hours_include_weekends(df_factory, cfg_factory):
    df = df_factory(
        dt=[
            "2024-05-04T10:00:00",
            "2024-05-05T10:00:00",
        ]
    )
    cfg = cfg_factory(
        "coarsen_datetime",
        "dt",
        mode="business_hours",
        include_weekends=True,
    )

    out = anonymize(df, cfg)["dt"].to_list()

    assert out == ["business_hours", "business_hours"]


@pytest.mark.parametrize("minutes", [0, -1, "15"])
def test_coarsen_datetime_invalid_minutes_raises(df_factory, cfg_factory, minutes):
    df = df_factory(dt=["2024-05-01T14:37:22"])
    cfg = cfg_factory("coarsen_datetime", "dt", mode="bucket", minutes=minutes)

    with pytest.raises(ValueError, match="minutes"):
        anonymize(df, cfg)


def test_coarsen_datetime_invalid_mode_raises(df_factory, cfg_factory):
    df = df_factory(dt=["2024-05-01T14:37:22"])
    cfg = cfg_factory("coarsen_datetime", "dt", mode="not-supported")

    with pytest.raises(ValueError, match="mode"):
        anonymize(df, cfg)


def test_coarsen_datetime_minute_of_day_bucket_invalid_output_raises(df_factory, cfg_factory):
    df = df_factory(dt=["2024-05-01T14:37:22"])
    cfg = cfg_factory(
        "coarsen_datetime",
        "dt",
        mode="minute_of_day_bucket",
        minutes=30,
        output="bad",
    )

    with pytest.raises(ValueError, match="output"):
        anonymize(df, cfg)


def test_coarsen_datetime_business_hours_invalid_bounds_raise(df_factory, cfg_factory):
    df = df_factory(dt=["2024-05-01T14:37:22"])

    with pytest.raises(ValueError, match="start_hour"):
        anonymize(
            df,
            cfg_factory(
                "coarsen_datetime",
                "dt",
                mode="business_hours",
                start_hour=18,
                end_hour=9,
            ),
        )

    with pytest.raises(ValueError, match="start_hour"):
        anonymize(
            df,
            cfg_factory(
                "coarsen_datetime",
                "dt",
                mode="business_hours",
                start_hour="8",
                end_hour=18,
            ),
        )
