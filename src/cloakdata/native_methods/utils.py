import polars as pl

from .catalog import native_method


@native_method
def coalesce_cols(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    cols = params.get("columns", [])
    if not cols:
        raise ValueError("coalesce_cols: 'columns' param is required")
    return pl.coalesce([pl.col(c) for c in cols]).alias(col)


@native_method
def null_if_matches(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    params = params or {}
    values = params.get("values")
    pattern = params.get("pattern")
    case_sensitive = bool(params.get("case_sensitive", True))

    if not values and not pattern:
        raise ValueError("null_if_matches: provide 'values' and/or 'pattern'")

    orig = pl.col(col)
    cond = pl.lit(False)

    if values:
        if not isinstance(values, list):
            raise ValueError("null_if_matches: 'values' must be a list")

        if case_sensitive:
            cond = cond | orig.is_in(values)
        else:
            normalized_values = [str(v).lower() for v in values]
            cond = cond | orig.cast(pl.Utf8).str.to_lowercase().is_in(normalized_values)

    if pattern:
        source = orig.cast(pl.Utf8)
        if not case_sensitive:
            pattern = f"(?i){pattern}"
        cond = cond | source.str.contains(pattern, literal=False).fill_null(False)

    return pl.when(cond).then(None).otherwise(orig).alias(col)
