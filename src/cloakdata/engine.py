import polars as pl

from .conditions import apply_conditioned_expr
from .native_methods.catalog import NATIVE_FRAME_METHODS, NATIVE_METHODS
from .registry import build_dispatch_map
from .types import DispatchMap
from .validate import ParsedRule, build_native_expr, parse_config


class TransformationError(RuntimeError):
    """A transformation could not be executed on the input."""


def _prepare_frame(df: pl.DataFrame, rules_by_column: dict[str, list[ParsedRule]]) -> pl.DataFrame:
    drops = [col for col, rules in rules_by_column.items() if rules[0].method == "drop"]
    available = set(df.columns)
    added = []
    for col, rules in rules_by_column.items():
        if col in available or rules[0].method == "drop":
            continue
        if not any(rule.predicate is not None for rule in rules):
            raise ValueError(f"Target column '{col}' is missing from input")
        added.append(pl.repeat(None, pl.len()).alias(col))
        available.add(col)

    available.difference_update(drops)
    for col, rules in rules_by_column.items():
        for rule in rules:
            if rule.predicate is None:
                continue
            missing = set(rule.predicate.meta.root_names()) - available
            if missing:
                raise ValueError(f"Column '{col}': missing condition columns {sorted(missing)}")

    if added:
        df = df.with_columns(added)
    return df.drop(drops, strict=False) if drops else df


def _rule_expression(
    df: pl.DataFrame, col: str, rule: ParsedRule, dispatch: DispatchMap, predicate: pl.Expr | None
) -> pl.Expr:
    method = dispatch[rule.method]
    if rule.method in NATIVE_METHODS:
        expr = build_native_expr(method, df, col, rule)
    else:
        try:
            expr = method(df, col, rule.params)
        except Exception as err:
            raise TransformationError(f"Custom method '{rule.method}' failed for '{col}'") from err

    if not isinstance(expr, pl.Expr):
        raise TransformationError(f"Method '{rule.method}' for '{col}' must return a Polars Expr")
    return apply_conditioned_expr(pl.col(col), expr, predicate).alias(col)


def _run_chain(
    df: pl.DataFrame, col: str, rules: list[ParsedRule], dispatch: DispatchMap
) -> pl.Series:
    # Keep input predicates outside the staged schema so selectors see only input columns.
    conditions = [
        rule.predicate.alias(str(index))
        for index, rule in enumerate(rules)
        if rule.predicate is not None
    ]
    predicates = df.select(conditions).to_dict() if conditions else {}
    plan = df.lazy()
    for index, rule in enumerate(rules):
        method_input = df
        if index and (rule.method not in NATIVE_METHODS or rule.method in NATIVE_FRAME_METHODS):
            # Data-dependent methods still receive a real DataFrame with the public columns.
            method_input = plan.collect()
            plan = method_input.lazy()
        value = predicates.get(str(index))
        predicate = pl.lit(value) if value is not None else None
        expr = _rule_expression(method_input, col, rule, dispatch, predicate)
        plan = plan.with_columns(expr)
    return plan.select(col).collect().get_column(col)


class AnonymizerEngine:
    """Apply per-column rules in order while conditions read the original values."""

    @classmethod
    def anonymize(cls, df: pl.DataFrame, config: dict) -> pl.DataFrame:
        dispatch = build_dispatch_map()
        rules_by_column = parse_config(config, dispatch)
        df = _prepare_frame(df, rules_by_column)
        output: list[pl.Expr | pl.Series] = []
        for col, rules in rules_by_column.items():
            rule = rules[0]
            if rule.method == "drop":
                continue
            try:
                if len(rules) == 1:
                    output.append(_rule_expression(df, col, rule, dispatch, rule.predicate))
                else:
                    output.append(_run_chain(df, col, rules, dispatch))
            except pl.exceptions.ColumnNotFoundError:
                raise
            except pl.exceptions.PolarsError as err:
                raise TransformationError(f"Could not transform column '{col}': {err}") from err
        try:
            return df.with_columns(output) if output else df
        except pl.exceptions.ColumnNotFoundError:
            raise
        except pl.exceptions.PolarsError as err:
            raise TransformationError(f"Could not apply transformations: {err}") from err
