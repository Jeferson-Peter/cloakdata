from __future__ import annotations

from collections.abc import Callable, Mapping
from functools import reduce
from operator import and_, or_
from typing import Any

import polars as pl

from .validators import validate_regex

_BETWEEN_LEN = 2


def _cast_for_value(col: pl.Expr, val: Any) -> pl.Expr:
    if isinstance(val, float):
        return col.cast(pl.Float64)
    if isinstance(val, int):
        return col.cast(pl.Int64)
    if isinstance(val, str):
        return col.cast(pl.Utf8)
    return col


_OPS: Mapping[str, Callable[[pl.Expr, Any], pl.Expr]] = {
    "equals": lambda c, v: c == v,
    "==": lambda c, v: c == v,
    "not_equals": lambda c, v: c != v,
    "!=": lambda c, v: c != v,
    "in": lambda c, v: c.is_in(v),
    "not_in": lambda c, v: ~c.is_in(v),
    ">": lambda c, v: c > v,
    "gt": lambda c, v: c > v,
    ">=": lambda c, v: c >= v,
    "gte": lambda c, v: c >= v,
    "<": lambda c, v: c < v,
    "lt": lambda c, v: c < v,
    "<=": lambda c, v: c <= v,
    "lte": lambda c, v: c <= v,
    "contains": lambda c, v: c.cast(pl.Utf8).str.contains(str(v)),
    "not_contains": lambda c, v: ~c.cast(pl.Utf8).str.contains(str(v)),
    "startswith": lambda c, v: c.cast(pl.Utf8).str.starts_with(str(v)),
    "endswith": lambda c, v: c.cast(pl.Utf8).str.ends_with(str(v)),
    "between": lambda c, v: (c >= v[0]) & (c <= v[1]),
}

_UNARY_OPS: Mapping[str, Callable[[pl.Expr], pl.Expr]] = {
    "is_null": lambda c: c.is_null(),
    "not_null": lambda c: c.is_not_null(),
    "is_true": lambda c: c.cast(pl.Boolean).fill_null(False),
    "is_false": lambda c: ~c.cast(pl.Boolean).fill_null(False),
}


def _leaf_predicate(cond: Mapping[str, Any]) -> pl.Expr:
    col = cond.get("column", cond.get("col"))
    operator = cond.get("operator", cond.get("op", "equals"))
    value = cond.get("value", cond.get("val"))

    if not isinstance(col, str) or not col:
        raise ValueError("condition requires a non-empty column name")
    if not isinstance(operator, str):
        raise ValueError("condition operator must be a string")

    op = operator.lower()
    expr = pl.col(col)
    if op in _UNARY_OPS:
        return _UNARY_OPS[op](expr)
    if op not in _OPS:
        raise ValueError(f"unsupported condition operator '{op}'")
    if value is None:
        raise ValueError(f"condition operator '{op}' requires a value; use is_null for nulls")
    if op == "between" and not (isinstance(value, list | tuple) and len(value) == _BETWEEN_LEN):
        raise ValueError("condition operator 'between' requires two bounds")
    if op in {"in", "not_in"} and not isinstance(value, list | tuple | set | frozenset):
        raise ValueError(f"condition operator '{op}' requires a collection")
    if op in {"contains", "not_contains", "startswith", "endswith"} and not isinstance(value, str):
        raise ValueError(f"condition operator '{op}' requires a string value")
    if op in {"contains", "not_contains"}:
        validate_regex(value, f"condition operator '{op}' on '{col}'")
    return _OPS[op](_cast_for_value(expr, value), value)


def _build_condition_expr(spec: Any) -> pl.Expr:
    if not isinstance(spec, Mapping):
        return _condition_group(spec, "and")

    groups = {"conditions", "all", "any", "not"} & spec.keys()
    if not groups:
        if spec.keys() - {"column", "col", "operator", "op", "value", "val"}:
            raise ValueError("unexpected key in condition")
        return _leaf_predicate(spec)

    group = next(iter(groups))
    allowed = {"conditions", "logical"} if group == "conditions" else {group}
    if spec.keys() - allowed:
        raise ValueError("condition must contain exactly one group")
    if group == "not":
        return ~_build_condition_expr(spec[group])
    if group == "conditions":
        logical = spec.get("logical", "and")
        if not isinstance(logical, str) or logical.lower() not in {"and", "or"}:
            raise ValueError("condition 'logical' must be 'and' or 'or'")
        return _condition_group(spec[group], logical.lower())
    return _condition_group(spec[group], "and" if group == "all" else "or")


def _condition_group(spec: Any, logical: str) -> pl.Expr:
    if not isinstance(spec, list | tuple) or not spec:
        raise ValueError("condition group must be a non-empty list of conditions")
    return reduce(and_ if logical == "and" else or_, map(_build_condition_expr, spec))


def condition_expr(spec: Any) -> pl.Expr:
    return _build_condition_expr(spec).fill_null(False)


def apply_conditioned_expr(
    current_expr: pl.Expr, new_expr: pl.Expr, condition_spec: Any
) -> pl.Expr:
    """Apply a compiled predicate or condition spec, preserving other rows."""
    if condition_spec is None:
        return new_expr
    predicate = (
        condition_spec if isinstance(condition_spec, pl.Expr) else condition_expr(condition_spec)
    )
    return pl.when(predicate).then(new_expr).otherwise(current_expr)
