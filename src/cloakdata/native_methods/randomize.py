import polars as pl

from .catalog import native_method


@native_method
def random_choice(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    params = params or {}
    choices = params.get("choices", ["X", "Y"])
    seed = params.get("seed", 0)

    if not choices:
        raise ValueError("random_choice: 'choices' must be a non-empty list")

    n = len(choices)
    idx = pl.arange(0, pl.len()).hash(seed=seed).abs() % n
    mapped_expr = pl.lit(choices[-1])
    for i in range(n - 2, -1, -1):
        mapped_expr = pl.when(idx == i).then(pl.lit(choices[i])).otherwise(mapped_expr)

    return pl.when(pl.col(col).is_null()).then(None).otherwise(mapped_expr).alias(col)


@native_method
def noise_numeric(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    params = params or {}
    min_delta = params.get("min_delta")
    max_delta = params.get("max_delta")
    seed = params.get("seed", 0)

    if min_delta is None or max_delta is None:
        raise ValueError("noise_numeric: 'min_delta' and 'max_delta' parameters are required")

    if not isinstance(min_delta, (int, float)) or not isinstance(max_delta, (int, float)):
        raise TypeError("noise_numeric: 'min_delta' and 'max_delta' must be numeric")

    if min_delta > max_delta:
        raise ValueError("noise_numeric: 'min_delta' cannot be greater than 'max_delta'")

    span = float(max_delta) - float(min_delta)
    base = pl.arange(0, pl.len()).hash(seed=seed).abs().cast(pl.Float64)
    fraction = (base % 1_000_000) / 1_000_000.0
    noise = pl.lit(float(min_delta)) + (fraction * pl.lit(span))

    return (
        pl.when(pl.col(col).is_null())
        .then(None)
        .otherwise(pl.col(col).cast(pl.Float64) + noise)
        .alias(col)
    )


@native_method
def shuffle(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    params = params or {}
    seed = params.get("seed")

    if seed is not None and not isinstance(seed, int):
        raise TypeError("shuffle: 'seed' must be an integer")

    return pl.col(col).shuffle(seed=seed).alias(col)
