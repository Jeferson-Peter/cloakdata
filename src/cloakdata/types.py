from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Literal, NotRequired, TypedDict

import polars as pl

MethodCallable = Callable[[pl.DataFrame, str, dict], pl.Expr]

DispatchMap = Mapping[str, MethodCallable]


class Condition(TypedDict, total=False):
    column: str
    col: str
    op: str
    operator: Literal[
        "equals",
        "==",
        "not_equals",
        "!=",
        "in",
        "not_in",
        ">",
        ">=",
        "<",
        "<=",
        "gt",
        "gte",
        "lt",
        "lte",
        "contains",
        "not_contains",
        "startswith",
        "endswith",
        "between",
        "is_null",
        "not_null",
        "is_true",
        "is_false",
    ]
    value: object
    val: object


class RuleObj(TypedDict, total=False):
    method: str
    params: NotRequired[dict]
    condition: NotRequired[Condition | Mapping[str, object] | Sequence[object] | None]


Rule = str | RuleObj


class Config(TypedDict):
    columns: Mapping[str, Rule | Sequence[Rule]]
