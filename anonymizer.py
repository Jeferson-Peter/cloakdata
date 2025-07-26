from datetime import datetime, timedelta

import polars as pl
import random
import string

def full_mask(col: str) -> pl.Expr:
    return pl.lit("*****").alias(col)

def mask_email(col: str) -> pl.Expr:
    return (
        pl.when(pl.col(col).str.contains("@"))
        .then(pl.lit("xxxxx@") + pl.col(col).str.split("@").list.get(1))
        .otherwise(pl.lit("xxxxx@hidden.com"))
        .alias(col)
    )

def mask_number(col: str) -> pl.Expr:
    return (
        pl.col(col).cast(pl.Utf8).str.slice(0, 3) + pl.lit("*****")
    ).alias(col)

def replace_with_value(col: str, value: str = "REDACTED") -> pl.Expr:
    return pl.lit(value).alias(col)

def replace_by_contains(col: str, mapping: dict) -> pl.Expr:
    expr = pl.col(col)
    for substr, replacement in mapping.items():
        expr = pl.when(expr.cast(pl.Utf8).str.contains(substr)).then(pl.lit(replacement)).otherwise(expr)
    return expr.alias(col)

def replace_exact(col: str, mapping: dict[str, str]) -> pl.Expr:
    expr = pl.col(col).cast(pl.Utf8)
    for old, new in mapping.items():
        expr = pl.when(expr == old).then(pl.lit(new)).otherwise(expr)
    return expr.alias(col)

def sequential_numeric(df: pl.DataFrame, col: str, prefix: str = "val") -> pl.Expr:
    unique_vals = df[col].unique().to_list()
    mapping = {val: f"{prefix} {i+1}" for i, val in enumerate(unique_vals)}
    return pl.col(col).replace(mapping).alias(col)

def sequential_alpha(df: pl.DataFrame, col: str, prefix: str = "val") -> pl.Expr:
    def num_to_alpha(n: int) -> str:
        result = ""
        while n >= 0:
            result = chr(65 + (n % 26)) + result
            n = n // 26 - 1
        return result

    unique_vals = df[col].unique().to_list()
    mapping = {val: f"{prefix} {num_to_alpha(i)}" for i, val in enumerate(unique_vals)}
    return pl.col(col).replace(mapping).alias(col)

def truncate(col: str, length: int) -> pl.Expr:
    return pl.col(col).cast(pl.Utf8).str.slice(0, length).alias(col)

def initials_only(col: str) -> pl.Expr:
    return (
        pl.col(col)
        .cast(pl.Utf8)
        .map_elements(
            lambda x: "".join([n[0].upper() + "." for n in str(x).split() if n]),
            return_dtype=pl.Utf8
        )
        .alias(col)
    )

def generalize_age(col: str) -> pl.Expr:
    base = (pl.col(col).cast(pl.Int64) // 10) * 10
    return (
        (base.cast(pl.Utf8) + pl.lit("-") + (base + 9).cast(pl.Utf8))
        .alias(col)
    )

def generalize_date(col: str, mode: str = "month_year") -> pl.Expr:
    if mode == "month_year":
        return pl.col(col).str.slice(0, 7).alias(col)  # YYYY-MM
    elif mode == "year":
        return pl.col(col).str.slice(0, 4).alias(col)  # YYYY
    else:
        return pl.lit("invalid_mode").alias(col)

def random_choice(col: str, choices: list) -> pl.Expr:
    # Gere uma série aleatória da mesma altura do DataFrame
    return (
        pl.col(col)
        .map_elements(lambda _: random.choice(choices), return_dtype=pl.Utf8)
        .alias(col)
    )

def replace_with_fake(col: str, digits: int = 11) -> pl.Expr:
    return (
        pl.col(col)
        .map_elements(lambda _: "".join(random.choices(string.digits, k=digits)), return_dtype=pl.Utf8)
        .alias(col)
    )

def shuffle(col: str) -> pl.Expr:
    return pl.col(col).shuffle().alias(col)

def date_offset(col: str, min_days: int = -3, max_days: int = 3) -> pl.Expr:
    def shift(date_str: str) -> str:
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d")
            offset = timedelta(days=random.randint(min_days, max_days))
            return (d + offset).strftime("%Y-%m-%d")
        except:
            return "invalid"

    return (
        pl.col(col)
        .cast(pl.Utf8)
        .map_elements(shift, return_dtype=pl.Utf8)
        .alias(col)
    )

def apply_conditioned_expr(col: str, expr: pl.Expr, condition: dict) -> pl.Expr:
    condition_col = condition.get("column")
    operator = condition.get("operator", "equals")
    value = condition.get("value")

    if not condition_col or value is None:
        return expr

    cond_expr = {
        "equals": pl.col(condition_col) == value,
        "not_equals": pl.col(condition_col) != value,
        "in": pl.col(condition_col).is_in(value),
        "not_in": ~pl.col(condition_col).is_in(value),
        "gt": pl.col(condition_col) > value,
        "gte": pl.col(condition_col) >= value,
        "lt": pl.col(condition_col) < value,
        "lte": pl.col(condition_col) <= value,
        "contains": pl.col(condition_col).cast(pl.Utf8).str.contains(value),
        "not_contains": ~pl.col(condition_col).cast(pl.Utf8).str.contains(value),
    }.get(operator)

    if cond_expr is None:
        raise ValueError(f"Unsupported operator: {operator}")

    return pl.when(cond_expr).then(expr).otherwise(pl.col(col)).alias(col)

def anonymize(df: pl.DataFrame, config: dict) -> pl.DataFrame:
    exprs = []

    dispatch_map = {
        "full_mask": lambda col, params: full_mask(col),
        "mask_email": lambda col, params: mask_email(col),
        "mask_number": lambda col, params: mask_number(col),
        "replace_with_value": lambda col, params: replace_with_value(col, params.get("value", "REDACTED")),
        "replace_by_contains": lambda col, params: replace_by_contains(
            col,
            params.get("mapping") or {params.get("substr", ""): params.get("replacement", "REDACTED")}
        ),
        "replace_exact": lambda col, params: replace_exact(col, params.get("mapping", {})),
        "sequential_numeric": lambda col, params: sequential_numeric(df, col, params.get("prefix", "val")),
        "sequential_alpha": lambda col, params: sequential_alpha(df, col, params.get("prefix", "val")),
        "truncate": lambda col, params: truncate(col, params.get("length", 4)),
        "initials_only": lambda col, params: initials_only(col),
        "generalize_age": lambda col, params: generalize_age(col),
        "generalize_date": lambda col, params: generalize_date(col, params.get("mode", "month_year")),
        "random_choice": lambda col, params: random_choice(col, params.get("choices", ["X", "Y"])),
        "replace_with_fake": lambda col, params: replace_with_fake(col, params.get("digits", 11)),
        "shuffle": lambda col, params: shuffle(col),
        "date_offset": lambda col, params: date_offset(col, params.get("min_days", -3), params.get("max_days", 3)),
    }

    dropped_cols = [col for col, rule in config["columns"].items() if
                    isinstance(rule, dict) and rule.get("method") == "drop"]
    df = df.drop(dropped_cols)

    for col, rule in config["columns"].items():
        if col not in df.columns:
            continue

        method, params = (rule, {}) if isinstance(rule, str) else (
            rule.get("method"), rule.get("params", {})
        )
        condition = rule.get("condition") if isinstance(rule, dict) else None

        if method in dispatch_map:
            expr = dispatch_map[method](col, params)
            if condition:
                expr = apply_conditioned_expr(col, expr, condition)
            exprs.append(expr)

    return df.with_columns(exprs) if exprs else df
