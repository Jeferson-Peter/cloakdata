import polars as pl

from .catalog import native_method

@native_method
def coalesce_cols(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    cols = params.get("columns", [])
    if not cols:
        raise ValueError("'columns' param is required for 'coalesce_cols'")
    return pl.coalesce([pl.col(c) for c in cols]).alias(col)
