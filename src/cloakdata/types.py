from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Literal, NotRequired, TypedDict

import polars as pl

MethodCallable = Callable[[pl.DataFrame, str, dict], pl.Expr]

DispatchMap = Mapping[str, MethodCallable]


class Condition(TypedDict, total=False):
    column: str
    col: str
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
    ]
    value: object


class RuleObj(TypedDict, total=False):
    method: str
    params: NotRequired[dict]
    condition: NotRequired[Condition]


Rule = str | RuleObj


class Config(TypedDict):
    columns: Mapping[str, Rule | Sequence[Rule]]
