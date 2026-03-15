import polars as pl

from .catalog import native_method

@native_method
def random_choice(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    params = params or {}
    choices = params.get("choices", ["X", "Y"])
    seed = params.get("seed", 0)

    if not choices:
        raise ValueError("'choices' must be a non-empty list")

    n = len(choices)
    idx = pl.arange(0, pl.len()).hash(seed=seed).abs() % n
    mapped_expr = pl.lit(choices[-1])
    for i in range(n - 2, -1, -1):
        mapped_expr = pl.when(idx == i).then(pl.lit(choices[i])).otherwise(mapped_expr)

    return pl.when(pl.col(col).is_null()).then(None).otherwise(mapped_expr).alias(col)


@native_method
def shuffle(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    params = params or {}
    seed = params.get("seed")

    if seed is not None and not isinstance(seed, int):
        raise TypeError("'seed' must be an integer")

    return pl.col(col).shuffle(seed=seed).alias(col)
