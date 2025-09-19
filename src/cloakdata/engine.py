import polars as pl
from loguru import logger

from .conditions import apply_conditioned_expr, condition_to_str
from .registry import build_dispatch_map


class AnonymizerEngine:
    """
    Orquestra a aplicação das regras de anonimização em um DataFrame.
    Mantém comportamento do método `anonymize` original (compat 1:1).
    """

    @classmethod
    def anonymize(cls, df: pl.DataFrame, config: dict) -> pl.DataFrame:
        logger.info("🔐 Starting anonymization process...")
        exprs = []
        dispatch_map = build_dispatch_map()

        dropped_cols = [
            col
            for col, rule in config["columns"].items()
            if isinstance(rule, dict) and rule.get("method") == "drop"
        ]
        if dropped_cols:
            logger.warning(f"⚠️ Dropping columns: {dropped_cols}")
            df = df.drop(dropped_cols, strict=False)

        for col, rule in config["columns"].items():
            column_exists = col in df.columns
            has_condition = (isinstance(rule, dict) and "condition" in rule) or (
                isinstance(rule, list)
                and any(isinstance(r, dict) and "condition" in r for r in rule)
            )

            if not column_exists:
                if has_condition:
                    logger.info(
                        f"➕ Column '{col}' not found — adding as null to apply conditional rule."
                    )
                    df = df.with_columns(pl.lit(None).alias(col))
                else:
                    logger.warning(f"⏭️ Skipping Unknown column: {col}")
                    continue

            rule_list = [rule] if isinstance(rule, str | dict) else rule
            current_expr = pl.col(col)

            for r in rule_list:
                if isinstance(r, str):
                    method, params, condition = r, {}, None
                else:
                    method = r.get("method")
                    params = r.get("params") or {}
                    condition = r.get("condition")

                if method not in dispatch_map:
                    logger.error(f"❌ Unknown method '{method}' for column '{col}'. Skipping.")
                    continue

                if condition:
                    logger.debug(
                        f"🔧 Applying method '{method}' to column '{col}' "
                        f"with condition '{condition_to_str(condition)}'"
                    )
                else:
                    logger.debug(f"🔧 Applying method '{method}' to column '{col}' (no condition)")

                new_expr = dispatch_map[method](df, col, params)
                current_expr = (
                    apply_conditioned_expr(current_expr, new_expr, condition)
                    if condition
                    else new_expr
                )

            exprs.append(current_expr.alias(col))

        result_df = df.with_columns(exprs) if exprs else df
        logger.success(f"✅ Anonymization complete. {len(exprs)} column(s) processed.")
        return result_df
