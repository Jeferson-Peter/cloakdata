import polars as pl

from .catalog import native_method

@native_method
def generalize_age(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    params = params or {}
    size = params.get("size", 10)

    try:
        size = int(size)
    except Exception as err:
        raise ValueError("'size' must be an integer.") from err

    if size <= 0:
        raise ValueError("'size' must be > 0.")

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
        raise ValueError(f"Invalid mode '{mode}' for generalize_date.")

    return pl.when(is_null).then(None).otherwise(out).alias(col)


@native_method
def generalize_number_range(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    params = params or {}
    interval = params.get("interval", 10)

    if not isinstance(interval, int) or interval <= 0:
        raise ValueError("'interval' must be a positive integer")

    orig = pl.col(col)
    is_null = orig.is_null()
    value = orig.cast(pl.Int64)
    base = (value // interval) * interval
    upper = base + interval - 1
    bucket = base.cast(pl.Utf8) + pl.lit(" to ") + upper.cast(pl.Utf8)
    return pl.when(is_null).then(None).otherwise(bucket).alias(col)
