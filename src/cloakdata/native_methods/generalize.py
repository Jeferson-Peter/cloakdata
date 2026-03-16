import polars as pl

from .catalog import native_method

@native_method
def generalize_age(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    params = params or {}
    size = params.get("size", 10)

    try:
        size = int(size)
    except Exception as err:
        raise ValueError("generalize_age: 'size' must be an integer") from err

    if size <= 0:
        raise ValueError("generalize_age: 'size' must be > 0")

    s = pl.col(col).cast(pl.Int64)
    base = (s // size) * size
    lower = base
    upper = base + (size - 1)
    label = lower.cast(pl.Utf8) + pl.lit("-") + upper.cast(pl.Utf8)
    return pl.when(s.is_null()).then(None).otherwise(label).alias(col)


@native_method
def generalize_date(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    mode = params.get("mode", "month")
    orig = pl.col(col)
    dt = orig.cast(pl.Utf8).str.strptime(pl.Datetime, strict=False)
    is_null = orig.is_null()

    if mode == "year":
        out = dt.dt.truncate("1y").dt.strftime("%Y")
    elif mode == "month":
        out = dt.dt.truncate("1mo").dt.strftime("%Y-%m")
    elif mode == "quarter":
        out = dt.dt.truncate("1q").dt.strftime("%Y-Q%q")
    elif mode == "semester":
        truncated = dt.dt.truncate("6mo")
        year_str = truncated.dt.strftime("%Y")
        semester_num = ((dt.dt.month() - 1) // 6 + 1).cast(pl.Utf8)
        out = year_str + pl.lit("-S") + semester_num
    elif mode == "week":
        out = dt.dt.truncate("1w").dt.strftime("%Y-W%W")
    elif mode == "date":
        out = dt.dt.strftime("%Y-%m-%d")
    elif mode == "datetime":
        out = dt.dt.strftime("%Y-%m-%dT%H:%M:%S")
    else:
        raise ValueError(f"generalize_date: invalid mode '{mode}'")

    return pl.when(is_null).then(None).otherwise(out).alias(col)


@native_method
def generalize_number_range(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    params = params or {}
    interval = params.get("interval", 10)

    if not isinstance(interval, int) or interval <= 0:
        raise ValueError("generalize_number_range: 'interval' must be a positive integer")

    orig = pl.col(col)
    is_null = orig.is_null()
    value = orig.cast(pl.Int64)
    base = (value // interval) * interval
    upper = base + interval - 1
    bucket = base.cast(pl.Utf8) + pl.lit(" to ") + upper.cast(pl.Utf8)
    return pl.when(is_null).then(None).otherwise(bucket).alias(col)


@native_method
def top_k_bucket(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    params = params or {}
    k = params.get("k", 5)
    other_label = str(params.get("other_label", "OTHER"))

    if not isinstance(k, int) or k <= 0:
        raise ValueError("top_k_bucket: 'k' must be a positive integer")

    top_values = (
        _df.select(pl.col(col))
        .drop_nulls()
        .group_by(col)
        .len()
        .sort(["len", col], descending=[True, False])
        .head(k)
        .select(col)
        .to_series()
        .to_list()
    )

    return (
        pl.when(pl.col(col).is_null())
        .then(None)
        .when(pl.col(col).is_in(top_values))
        .then(pl.col(col).cast(pl.Utf8))
        .otherwise(pl.lit(other_label))
        .alias(col)
    )


@native_method
def generalize_zip_code(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    params = params or {}
    visible_prefix = params.get("visible_prefix", 3)
    mask_char = str(params.get("mask_char", "*"))

    if not isinstance(visible_prefix, int) or visible_prefix < 0:
        raise ValueError("generalize_zip_code: 'visible_prefix' must be an integer >= 0")

    s = pl.col(col).cast(pl.Utf8)
    total_len = s.str.len_chars()
    visible = s.str.slice(0, visible_prefix)
    suffix = s.str.slice(visible_prefix).str.replace_all(r"[A-Za-z0-9]", mask_char)
    masked = visible + suffix

    return (
        pl.when(s.is_null())
        .then(None)
        .when(total_len <= visible_prefix)
        .then(s)
        .otherwise(masked)
        .alias(col)
    )


@native_method
def coarsen_datetime(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    params = params or {}
    mode = params.get("mode", "bucket")
    minutes = params.get("minutes", 60)
    output = params.get("output", "time")

    s = pl.col(col).cast(pl.Utf8)
    parsed = s.str.strptime(pl.Datetime, "%Y-%m-%dT%H:%M:%S", strict=False)

    if mode == "bucket":
        if not isinstance(minutes, int) or minutes <= 0:
            raise ValueError("coarsen_datetime: 'minutes' must be a positive integer")
        out = parsed.dt.truncate(f"{minutes}m").dt.strftime("%Y-%m-%dT%H:%M:%S")
    elif mode == "minute_of_day_bucket":
        if not isinstance(minutes, int) or minutes <= 0:
            raise ValueError("coarsen_datetime: 'minutes' must be a positive integer")
        if output not in {"time", "datetime"}:
            raise ValueError(
                "coarsen_datetime: 'output' must be 'time' or 'datetime' for minute_of_day_bucket"
            )
        truncated = parsed.dt.truncate(f"{minutes}m")
        out = (
            truncated.dt.strftime("%H:%M")
            if output == "time"
            else truncated.dt.strftime("%Y-%m-%dT%H:%M:%S")
        )
    elif mode == "hour":
        out = parsed.dt.truncate("1h").dt.strftime("%Y-%m-%dT%H:%M:%S")
    elif mode == "part_of_day":
        hour = parsed.dt.hour()
        out = (
            pl.when(hour < 6)
            .then(pl.lit("night"))
            .when(hour < 12)
            .then(pl.lit("morning"))
            .when(hour < 18)
            .then(pl.lit("afternoon"))
            .otherwise(pl.lit("evening"))
        )
    elif mode == "weekday":
        out = parsed.dt.strftime("%A").str.to_lowercase()
    elif mode == "weekend_weekday":
        weekday_num = parsed.dt.weekday()
        out = (
            pl.when(weekday_num >= 6)
            .then(pl.lit("weekend"))
            .otherwise(pl.lit("weekday"))
        )
    elif mode == "business_hours":
        start_hour = params.get("start_hour", 9)
        end_hour = params.get("end_hour", 18)
        include_weekends = bool(params.get("include_weekends", False))

        if not isinstance(start_hour, int) or not isinstance(end_hour, int):
            raise ValueError(
                "coarsen_datetime: 'start_hour' and 'end_hour' must be integers for business_hours"
            )
        if not (0 <= start_hour <= 23 and 0 <= end_hour <= 24):
            raise ValueError(
                "coarsen_datetime: 'start_hour' must be 0-23 and 'end_hour' must be 0-24"
            )
        if start_hour >= end_hour:
            raise ValueError("coarsen_datetime: 'start_hour' must be less than 'end_hour'")

        hour = parsed.dt.hour()
        weekday_num = parsed.dt.weekday()
        is_business_day = pl.lit(True) if include_weekends else weekday_num <= 5
        out = (
            pl.when(is_business_day & (hour >= start_hour) & (hour < end_hour))
            .then(pl.lit("business_hours"))
            .otherwise(pl.lit("off_hours"))
        )
    else:
        raise ValueError(
            "coarsen_datetime: supported modes are 'bucket', 'minute_of_day_bucket', "
            "'hour', 'part_of_day', 'weekday', 'weekend_weekday', and 'business_hours'"
        )

    return (
        pl.when(s.is_null())
        .then(None)
        .when(parsed.is_null())
        .then(pl.lit("invalid"))
        .otherwise(out)
        .alias(col)
    )
