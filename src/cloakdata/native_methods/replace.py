import polars as pl

from .catalog import native_method

@native_method
def replace_with_value(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    if "value" not in params:
        raise ValueError("replace_with_value: 'value' parameter is required")

    value = params["value"]
    preserve_nulls = bool(params.get("preserve_nulls", False))

    expr = pl.lit(value)
    if preserve_nulls:
        expr = pl.when(pl.col(col).is_null()).then(None).otherwise(expr)
    return expr.alias(col)


@native_method
def replace_by_contains(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    mapping = params.get("mapping")
    if not mapping:
        substr = params.get("substr")
        if not substr:
            raise ValueError(
                "replace_by_contains: provide 'mapping' or ('substr' + 'replacement')."
            )
        mapping = {substr: params.get("replacement", "")}

    case_sensitive = bool(params.get("case_sensitive", True))
    use_regex = bool(params.get("use_regex", False))

    s = pl.col(col).cast(pl.Utf8)
    acc = s

    for sub, rep in mapping.items():
        cond = acc.str.contains(sub, literal=not use_regex).fill_null(False)

        if not case_sensitive and not use_regex:
            cond = acc.str.to_lowercase().str.contains(sub.lower(), literal=True).fill_null(False)

        acc = pl.when(cond).then(pl.lit(rep)).otherwise(acc)

    return acc.alias(col)


@native_method
def replace_exact(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    mapping: dict = params.get("mapping", {})
    old = list(mapping.keys())
    new = list(mapping.values())
    return pl.col(col).replace(old, new).alias(col)


@native_method
def replace_with_random_digits(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    params = params or {}
    digits = params.get("digits", 11)
    seed = params.get("seed", 0)

    if not isinstance(digits, int) or digits <= 0:
        raise ValueError("'digits' must be a positive integer")

    base = pl.arange(0, pl.len()).hash(seed=seed).abs()
    digit_exprs = [((base + i).hash(seed=seed + i) % 10).cast(pl.Utf8) for i in range(digits)]
    random_number = pl.concat_str(digit_exprs)

    return pl.when(pl.col(col).is_null()).then(None).otherwise(random_number).alias(col)
