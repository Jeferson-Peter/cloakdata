import polars as pl

from .catalog import native_method

@native_method
def round_number(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    digits = params.get("digits", 0)
    return pl.col(col).cast(pl.Float64).round(digits).alias(col)


@native_method
def clip_range(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    params = params or {}
    min_value = params.get("min")
    max_value = params.get("max")

    if min_value is None and max_value is None:
        raise ValueError("clip_range: provide 'min' and/or 'max'")

    if min_value is not None and not isinstance(min_value, (int, float)):
        raise TypeError("clip_range: 'min' must be numeric")

    if max_value is not None and not isinstance(max_value, (int, float)):
        raise TypeError("clip_range: 'max' must be numeric")

    if min_value is not None and max_value is not None and min_value > max_value:
        raise ValueError("clip_range: 'min' cannot be greater than 'max'")

    expr = pl.col(col).cast(pl.Float64)
    if min_value is not None:
        expr = expr.clip(lower_bound=float(min_value))
    if max_value is not None:
        expr = expr.clip(upper_bound=float(max_value))

    return expr.alias(col)


@native_method
def round_date(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    mode = params.get("mode", "month")
    s = pl.col(col).cast(pl.Utf8)
    parsed = s.str.strptime(pl.Date, strict=False)

    if mode == "month":
        rounded = parsed.dt.month_start().dt.strftime("%Y-%m-%d")
    elif mode == "year":
        rounded = parsed.dt.truncate("1y").dt.strftime("%Y-%m-%d")
    else:
        return s.alias(col)

    return (
        pl.when(s.is_null())
        .then(None)
        .when(parsed.is_null())
        .then(pl.lit("invalid"))
        .otherwise(rounded)
        .alias(col)
    )


@native_method
def date_offset(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    params = params or {}
    min_days = int(params.get("min_days", 0))
    max_days = int(params.get("max_days", 0))
    seed = int(params.get("seed", 0))

    if max_days < min_days:
        min_days, max_days = max_days, min_days

    span = (max_days - min_days) + 1
    if span <= 0:
        raise ValueError("Invalid date offset range")

    orig = pl.col(col)
    base = orig.cast(pl.Utf8).str.strptime(pl.Date, strict=False)
    idx = pl.arange(0, pl.len()).cast(pl.UInt64)
    rnd = idx.hash(seed=seed)
    offset = (rnd % span).cast(pl.Int64) + min_days

    return (
        pl.when(base.is_not_null())
        .then((base + pl.duration(days=offset)).dt.strftime("%Y-%m-%d"))
        .otherwise(pl.lit(None))
        .alias(col)
    )
