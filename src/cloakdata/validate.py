from collections.abc import Mapping
from typing import NamedTuple

import polars as pl

from .conditions import condition_expr
from .native_methods.catalog import NATIVE_METHODS
from .registry import build_dispatch_map
from .types import DispatchMap, MethodCallable

_RULE_KEYS = {"method", "params", "condition"}
_BOOLEAN_PARAMS = {
    "preserve_nulls",
    "case_sensitive",
    "use_regex",
    "match_length",
    "include_weekends",
}


class ParsedRule(NamedTuple):
    method: str
    params: dict
    predicate: pl.Expr | None


def _parse_rule(item: object, dispatch: DispatchMap) -> ParsedRule:
    if isinstance(item, str):
        item = {"method": item}
    if not isinstance(item, Mapping) or item.keys() - _RULE_KEYS:
        raise ValueError("rule must be a method name or a mapping with method, params, condition")

    method = item.get("method")
    if not isinstance(method, str) or not method:
        raise ValueError("rule requires a non-empty method name")
    if method != "drop" and method not in dispatch:
        raise ValueError(f"unknown method '{method}'")
    params = item.get("params")
    if params is not None and not isinstance(params, Mapping):
        raise ValueError(f"'{method}' params must be a mapping")
    params = dict(params) if params is not None else {}
    condition = item.get("condition")
    if method == "drop" and (params or condition is not None):
        raise ValueError("'drop' takes no parameters or condition")
    if method in NATIVE_METHODS:
        for name in params.keys() & _BOOLEAN_PARAMS:
            if not isinstance(params[name], bool):
                raise ValueError(f"'{method}' parameter '{name}' must be a boolean")
    predicate = condition_expr(condition) if condition is not None else None
    return ParsedRule(method, params, predicate)


def parse_config(config: object, dispatch: DispatchMap) -> dict[str, list[ParsedRule]]:
    if not isinstance(config, Mapping) or not isinstance(config.get("columns"), Mapping):
        raise ValueError("Config requires a 'columns' mapping")

    parsed = {}
    for column, rules in config["columns"].items():
        if not isinstance(column, str) or not column:
            raise ValueError("Config column names must be non-empty strings")
        entries = rules if isinstance(rules, list | tuple) else [rules]
        if not entries:
            raise ValueError(f"Column '{column}' requires at least one rule")
        current = []
        for index, entry in enumerate(entries, start=1):
            try:
                current.append(_parse_rule(entry, dispatch))
            except (TypeError, ValueError, OverflowError, pl.exceptions.PolarsError) as err:
                raise ValueError(f"Column '{column}', rule {index}: {err}") from err
        if len(current) > 1 and any(rule.method == "drop" for rule in current):
            raise ValueError(f"Column '{column}': 'drop' must be the only rule")
        parsed[column] = current
    return parsed


def build_native_expr(
    func: MethodCallable, df: pl.DataFrame, column: str, rule: ParsedRule
) -> pl.Expr:
    try:
        return func(df, column, rule.params)
    except (ValueError, TypeError, OverflowError) as err:
        error_type = TypeError if isinstance(err, TypeError) else ValueError
        raise error_type(f"Column '{column}', method '{rule.method}': {err}") from err


def validate_config(config: dict, dispatch_map: DispatchMap) -> None:
    """Validate structure and native parameters without running custom code."""
    parsed = parse_config(config, dispatch_map)
    # Data-inspecting methods can build an expression against an empty input.
    sample = pl.DataFrame(schema={"__value": pl.String})
    for column, rules in parsed.items():
        for rule in rules:
            method = NATIVE_METHODS.get(rule.method)
            if method is not None and dispatch_map.get(rule.method) is method:
                try:
                    method(sample, "__value", rule.params)
                except (ValueError, TypeError, OverflowError, pl.exceptions.PolarsError) as err:
                    raise ValueError(f"Column '{column}', method '{rule.method}': {err}") from err


def validate(config: dict) -> None:
    """Validate configuration without a DataFrame or custom method execution."""
    validate_config(config, build_dispatch_map())
