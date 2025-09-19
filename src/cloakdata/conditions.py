from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from functools import reduce
from operator import and_, or_
from typing import Any

import polars as pl

_BETWEEN_LEN = 2


def _cast_for_value(col: pl.Expr, val: Any) -> pl.Expr:
    if isinstance(val, float):
        return col.cast(pl.Float64)
    if isinstance(val, int):
        return col.cast(pl.Int64)
    if isinstance(val, str):
        return col.cast(pl.Utf8)
    return col


def _safe_reduce(
    conj: Callable[[pl.Expr, pl.Expr], pl.Expr], parts: Iterable[pl.Expr]
) -> pl.Expr | None:
    parts = [p for p in parts if p is not None]
    if not parts:
        return None
    return reduce(conj, parts)


def _as_bool(expr: pl.Expr | None) -> pl.Expr | None:
    return expr.fill_null(False) if expr is not None else None


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


def _leaf_predicate(cond: Mapping[str, Any]) -> pl.Expr | None:
    if not cond:
        return None

    col_name = cond.get("column", cond.get("col"))
    op = str(cond.get("operator", cond.get("op", "equals"))).lower()
    val = cond.get("value", cond.get("val"))

    if col_name is None and op not in _UNARY_OPS:
        return None

    col_expr = pl.col(col_name) if col_name is not None else None

    if op in _UNARY_OPS:
        return _UNARY_OPS[op](col_expr)

    fn = _OPS.get(op)
    if fn is None:
        return None

    if op == "between":
        if not (isinstance(val, list | tuple) and len(val) == _BETWEEN_LEN):
            return None

    col_expr = _cast_for_value(col_expr, val)
    return fn(col_expr, val)


def _join_parts(parts: list[str], logical: str) -> str:
    parts = [p for p in parts if p]
    if not parts:
        return ""
    sep = f" {logical} "
    return f"({sep.join(parts)})"


def _build_condition_expr(spec: Any) -> pl.Expr | None:
    """
    Constrói a expressão Polars a partir da spec.
    Regras simétricas às de condition_to_str.
    """
    expr: pl.Expr | None = None

    if isinstance(spec, dict):
        # 1) {"conditions": [...], "logical": "and"|"or"}
        if "conditions" in spec:
            logical = str(spec.get("logical", "and")).lower()
            subs = (_build_condition_expr(it) for it in (spec.get("conditions") or []))
            expr = _safe_reduce(
                and_ if logical == "and" else or_,
                (s for s in subs if s is not None),
            )
        # 2) {"all": [...]}
        elif "all" in spec:
            subs = (_build_condition_expr(it) for it in (spec.get("all") or []))
            expr = _safe_reduce(and_, (s for s in subs if s is not None))
        # 3) {"any": [...]}
        elif "any" in spec:
            subs = (_build_condition_expr(it) for it in (spec.get("any") or []))
            expr = _safe_reduce(or_, (s for s in subs if s is not None))
        # 4) {"not": {...}}
        elif "not" in spec:
            inner = _build_condition_expr(spec.get("not"))
            expr = (~inner) if inner is not None else None
        # 5) folha
        else:
            expr = _leaf_predicate(spec)

    elif isinstance(spec, list | tuple):
        subs = (_build_condition_expr(it) for it in spec)
        expr = _safe_reduce(and_, (s for s in subs if s is not None))

    else:
        expr = None

    return expr


def apply_conditioned_expr(
    current_expr: pl.Expr, new_expr: pl.Expr, condition_spec: Any
) -> pl.Expr:
    """
    Aplica `new_expr` onde `condition_spec` é True; mantém `current_expr` no resto.
    Suporta:
      - folha
      - lista (AND implícito)
      - {"conditions":[...], "logical":"and"|"or"}
      - {"all":[...]}, {"any":[...]}, {"not": {...}} (aninhado)
    """
    cond = _as_bool(_build_condition_expr(condition_spec))
    if cond is None:
        return new_expr
    return pl.when(cond).then(new_expr).otherwise(current_expr)


_OP_TEMPLATES: Mapping[str, str] = {
    "equals": "{c} == {v}",
    "==": "{c} == {v}",
    "not_equals": "{c} != {v}",
    "!=": "{c} != {v}",
    "in": "{c} IN {v}",
    "not_in": "{c} NOT IN {v}",
    ">": "{c} > {v}",
    "gt": "{c} > {v}",
    ">=": "{c} >= {v}",
    "gte": "{c} >= {v}",
    "<": "{c} < {v}",
    "lt": "{c} < {v}",
    "<=": "{c} <= {v}",
    "lte": "{c} <= {v}",
    "contains": "{c} CONTAINS {v}",
    "not_contains": "{c} NOT CONTAINS {v}",
    "startswith": "{c} STARTS WITH {v}",
    "endswith": "{c} ENDS WITH {v}",
    "between": "{c} BETWEEN {lo} AND {hi}",
    "is_null": "{c} IS NULL",
    "not_null": "{c} IS NOT NULL",
    "is_true": "{c} IS TRUE",
    "is_false": "{c} IS FALSE",
}


def _fmt_value(v: Any) -> str:
    if isinstance(v, list | tuple | set):
        return "[" + ", ".join(repr(x) for x in v) + "]"
    return repr(v)


def _leaf_to_str(cond: Mapping[str, Any]) -> str:
    c = cond.get("column", cond.get("col"))
    op = str(cond.get("operator", cond.get("op", "equals"))).lower()
    v = cond.get("value", cond.get("val"))

    tpl = _OP_TEMPLATES.get(op)
    if not tpl:
        return f"{c} {op} {v!r}"

    if op == "between":
        try:
            lo, hi = v
        except Exception:
            return f"{c} BETWEEN {v!r}"
        return tpl.format(c=c, lo=lo, hi=hi)

    return tpl.format(c=c, v=_fmt_value(v))


def condition_to_str(spec: Any) -> str:
    """
    Converte uma spec de condição (dict/list/aninhado) em string legível.
    Regras:
      - list/tuple => AND
      - {"conditions":[...], "logical":"or"|"and"} => OR/AND
      - {"all":[...]}, {"any":[...]}, {"not": {...}} => grupos aninhados
      - folhas delegam para _leaf_to_str(spec)
    """
    result = ""

    if spec is None:
        return result

    if isinstance(spec, dict):
        # 1) {"conditions": [...], "logical": "and"|"or"}
        if "conditions" in spec:
            logical = str(spec.get("logical", "and")).upper()
            parts = [condition_to_str(x) for x in (spec.get("conditions") or [])]
            result = _join_parts(parts, logical)
        # 2) {"all": [...]}
        elif "all" in spec:
            parts = [condition_to_str(x) for x in (spec.get("all") or [])]
            result = _join_parts(parts, "AND")
        # 3) {"any": [...]}
        elif "any" in spec:
            parts = [condition_to_str(x) for x in (spec.get("any") or [])]
            result = _join_parts(parts, "OR")
        # 4) {"not": {...}}
        elif "not" in spec:
            inner = condition_to_str(spec.get("not"))
            result = f"(NOT {inner})" if inner else ""
        # 5) folha
        else:
            result = _leaf_to_str(spec)

    elif isinstance(spec, list | tuple):
        parts = [condition_to_str(x) for x in spec]
        result = _join_parts(parts, "AND")

    else:
        # fallback: forçar string
        result = str(spec)

    return result
