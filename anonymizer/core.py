import random
import string
from datetime import datetime, timedelta

import polars as pl
import inspect

from loguru import logger


class AnonymizationMethods:
    """
    A collection of static methods for anonymizing or masking sensitive data in Polars DataFrames.

    This class provides various anonymization strategies such as full masking, email obfuscation,
    data generalization, conditional replacement, pseudonymization, and more.

    Each method returns a `pl.Expr` that can be applied to a column in a Polars DataFrame.
    """

    @staticmethod
    def full_mask(_df: pl.DataFrame, col: str, _params: dict) -> pl.Expr:
        """
        Fully masks all values in the specified column with a fixed placeholder.

        Parameters:
            _df (pl.DataFrame): The input DataFrame (not used in this method).
            col (str): The name of the column to be masked.
            _params (dict): Parameters dictionary (not used in this method).

        Returns:
            pl.Expr: An expression that replaces all values in the column with "*****".
        """
        return pl.lit("*****").alias(col)

    @staticmethod
    def mask_email(_df: pl.DataFrame, col: str, _params: dict) -> pl.Expr:
        """
        Masks the local part of email addresses in the specified column, keeping the domain.

        Example:
            "john.doe@example.com" → "xxxxx@example.com"
            "invalid_email" → "xxxxx@hidden.com"

        Parameters:
            _df (pl.DataFrame): The input DataFrame (not used in this method).
            col (str): The name of the column containing email addresses.
            _params (dict): Parameters dictionary (not used in this method).

        Returns:
            pl.Expr: An expression that masks email addresses while preserving the domain.
        """
        return (
            pl.when(pl.col(col).str.contains("@"))
            .then(pl.lit("xxxxx@") + pl.col(col).str.split("@").list.get(1))
            .otherwise(pl.lit("xxxxx@hidden.com"))
            .alias(col)
        )

    @staticmethod
    def mask_number(_df: pl.DataFrame, col: str, _params: dict) -> pl.Expr:
        """
        Masks part of a numeric string in the specified column, keeping the first few characters.

        Example:
            "123456789" → "123*****"

        Parameters:
            _df (pl.DataFrame): The input DataFrame (not used in this method).
            col (str): The name of the column to be masked.
            _params (dict): Parameters dictionary (not used in this method).

        Returns:
            pl.Expr: An expression that preserves the first 3 characters and masks the rest.
        """
        return (
            pl.col(col).cast(pl.Utf8).str.slice(0, 3) + pl.lit("*****")
        ).alias(col)

    @staticmethod
    def replace_with_value(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
        """
        Replaces all values in the specified column with a static value.

        Parameters:
            _df (pl.DataFrame): The input DataFrame (not used in this method).
            col (str): The name of the column to be replaced.
            params (dict): Dictionary containing the key "value" with the replacement string.
                           If not provided, defaults to "Unknow".

        Returns:
            pl.Expr: An expression that replaces all values with the specified static value.
        """
        return pl.lit(params.get("value", "Unknow")).alias(col)

    @staticmethod
    def replace_by_contains(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
        """
        Replaces values in the column based on whether they contain specific substrings.

        Parameters:
            _df (pl.DataFrame): The input DataFrame (not used directly).
            col (str): The name of the column to be processed.
            params (dict): Dictionary with one of the following:
                - "mapping" (dict): Keys are substrings to look for, values are replacements.
                - OR "substr" (str) and "replacement" (str): fallback single rule if no mapping is provided.

        Returns:
            pl.Expr: An expression that replaces values based on substring matching.
        """
        mapping = params.get("mapping") or {
            params.get("substr", ""): params.get("replacement", "Unknow")
        }
        expr = pl.col(col)
        for substr, replacement in mapping.items():
            expr = pl.when(expr.cast(pl.Utf8).str.contains(substr)).then(pl.lit(replacement)).otherwise(expr)
        return expr.alias(col)

    @staticmethod
    def replace_exact(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
        """
        Replaces values in the column that exactly match a given set of keys.

        Parameters:
            _df (pl.DataFrame): The input DataFrame (not used directly).
            col (str): The name of the column to be processed.
            params (dict): Dictionary containing a "mapping" key with a dict of
                           {original_value: replacement_value}.

        Returns:
            pl.Expr: An expression that performs exact value replacements.
        """
        expr = pl.col(col).cast(pl.Utf8)
        for old, new in params.get("mapping", {}).items():
            expr = pl.when(expr == old).then(pl.lit(new)).otherwise(expr)
        return expr.alias(col)

    @staticmethod
    def sequential_numeric(df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
        """
        Replaces unique values in the column with sequentially numbered strings.

        Example:
            "Alice", "Bob", "Alice" → "val 1", "val 2", "val 1"

        Parameters:
            df (pl.DataFrame): The input DataFrame, used to extract unique values.
            col (str): The name of the column to be pseudonymized.
            params (dict): Optional parameters:
                - "prefix" (str): A prefix to add to the generated values (default: "val").

        Returns:
            pl.Expr: An expression replacing values with numeric pseudonyms.
        """
        unique_vals = df.select(pl.col(col).unique()).to_series().to_list()
        mapping = {val: f"{params.get("prefix", "val")} {i + 1}" for i, val in enumerate(unique_vals)}
        return pl.col(col).replace(mapping).alias(col)

    @staticmethod
    def sequential_alpha(df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
        """
        Replaces unique values in the column with alphabetically indexed pseudonyms.

        Example:
            "Alice", "Bob", "Alice" → "val A", "val B", "val A"

        Parameters:
            df (pl.DataFrame): The input DataFrame, used to extract unique values.
            col (str): The name of the column to be pseudonymized.
            params (dict): Optional parameters:
                - "prefix" (str): A prefix to add to the generated values (default: "val").

        Returns:
            pl.Expr: An expression replacing values with alphabetic pseudonyms (A, B, ..., Z, AA, AB, ...).
        """
        def num_to_alpha(n: int) -> str:
            result = ""
            while n >= 0:
                result = chr(65 + (n % 26)) + result
                n = n // 26 - 1
            return result

        unique_vals = df.select(pl.col(col).unique()).to_series().to_list()
        mapping = {val: f"{params.get("prefix", "val")} {num_to_alpha(i)}" for i, val in enumerate(unique_vals)}
        return pl.col(col).replace(mapping).alias(col)

    @staticmethod
    def truncate(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
        """
        Truncates string values in the column to a fixed length.

        Example:
            "Alexander" with length=4 → "Alex"

        Parameters:
            _df (pl.DataFrame): The input DataFrame (not used directly).
            col (str): The name of the column to be truncated.
            params (dict): Parameters containing:
                - "length" (int): The maximum number of characters to retain (default: 4).

        Returns:
            pl.Expr: An expression that truncates each string to the specified length.
        """
        return pl.col(col).cast(pl.Utf8).str.slice(0, params.get("length", 4)).alias(col)

    @staticmethod
    def initials_only(_df: pl.DataFrame, col: str, _params: dict) -> pl.Expr:
        """
        Converts full names into initials. For example, "John Doe" becomes "J.D."

        Parameters:
            _df (pl.DataFrame): The input DataFrame (not used directly).
            col (str): The name of the column containing full names.
            _params (dict): Parameters dictionary (not used in this method).

        Returns:
            pl.Expr: An expression that converts names to initials format.
        """
        return (
            pl.col(col)
            .cast(pl.Utf8)
            .map_elements(
                lambda x: "".join([n[0].upper() + "." for n in str(x).split() if n]),
                return_dtype=pl.Utf8
            )
            .alias(col)
        )

    @staticmethod
    def generalize_age(_df: pl.DataFrame, col: str, _params: dict) -> pl.Expr:
        """
        Generalizes age values into 10-year intervals.

        Example:
            25 → "20-29"
            41 → "40-49"

        Parameters:
            _df (pl.DataFrame): The input DataFrame (not used directly).
            col (str): The name of the column containing age values.
            _params (dict): Parameters dictionary (not used in this method).

        Returns:
            pl.Expr: An expression that converts numeric ages into age groups.
        """
        base = (pl.col(col).cast(pl.Int64) // 10) * 10
        return (
            (base.cast(pl.Utf8) + pl.lit("-") + (base + 9).cast(pl.Utf8))
            .alias(col)
        )

    @staticmethod
    def generalize_date(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
        """
        Generalizes a date column by reducing its granularity (e.g., to month or year).

        Parameters:
            _df (pl.DataFrame): The input DataFrame (not used directly).
            col (str): The name of the column containing date strings in "YYYY-MM-DD" format.
            params (dict): Dictionary containing:
                - "mode" (str): Either "month_year" to keep "YYYY-MM", or "year" to keep "YYYY".
                                Defaults to "month_year".

        Returns:
            pl.Expr: An expression that truncates the date based on the selected mode.
        """
        mode = params.get("mode", "month_year")
        if mode == "month_year":
            return pl.col(col).str.slice(0, 7).alias(col)
        elif mode == "year":
            return pl.col(col).str.slice(0, 4).alias(col)
        else:
            return pl.lit("invalid_mode").alias(col)

    @staticmethod
    def random_choice(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
        """
        Replaces each value in the column with a random choice from a predefined list.

        Example:
            Original: "A", "B", "C"
            After: "X", "Y", "X" (randomly assigned)

        Parameters:
            _df (pl.DataFrame): The input DataFrame (not used directly).
            col (str): The name of the column to anonymize.
            params (dict): Dictionary containing:
                - "choices" (list): List of possible values to randomly assign. Defaults to ["X", "Y"].

        Returns:
            pl.Expr: An expression that replaces values with random selections from the list.
        """
        choices = params.get("choices", ["X", "Y"])
        return (
            pl.col(col)
            .map_elements(lambda _: random.choice(choices), return_dtype=pl.Utf8)
            .alias(col)
        )

    @staticmethod
    def replace_with_fake(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
        """
        Replaces each value in the column with a randomly generated fake number (e.g., CPF, ID).

        Example:
            Original: "123456789" → "80239485711" (random 11-digit string)

        Parameters:
            _df (pl.DataFrame): The input DataFrame (not used directly).
            col (str): The name of the column to anonymize.
            params (dict): Dictionary containing:
                - "digits" (int): Number of digits to generate (default: 11).

        Returns:
            pl.Expr: An expression that replaces values with random digit strings.
        """
        return (
            pl.col(col)
            .map_elements(lambda _: "".join(random.choices(string.digits, k=params.get("digits", 11))),
                          return_dtype=pl.Utf8)
            .alias(col)
        )

    @staticmethod
    def shuffle(_df: pl.DataFrame, col: str, _params: dict) -> pl.Expr:
        """
        Randomly shuffles the values in the specified column.

        Note:
            This method preserves the original values but reorders them randomly.

        Parameters:
            _df (pl.DataFrame): The input DataFrame (not used directly).
            col (str): The name of the column to shuffle.
            _params (dict): Parameters dictionary (not used in this method).

        Returns:
            pl.Expr: An expression that shuffles the column values.
        """
        return pl.col(col).shuffle().alias(col)

    @staticmethod
    def date_offset(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
        """
        Applies a random date offset (in days) to each value in the column.

        Example:
            "2025-07-20" → "2025-07-18" (random within range)

        Parameters:
            _df (pl.DataFrame): The input DataFrame (not used directly).
            col (str): The name of the column containing date strings (format "YYYY-MM-DD").
            params (dict): Dictionary containing:
                - "min_days" (int): Minimum number of days to shift (default: -3).
                - "max_days" (int): Maximum number of days to shift (default: 3).

        Returns:
            pl.Expr: An expression that offsets dates randomly within the given range.
        """
        def shift(date_str: str) -> str:
            try:
                min_days = params.get("min_days", -3)
                max_days = params.get("max_days", 3)
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

    @staticmethod
    def coalesce_cols(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
        """
        Returns the first non-null value from a list of columns and assigns it to the target column.

        Example:
            If column "A" is null, but "B" has a value, it will use "B". Follows the order of the list.

        Parameters:
            _df (pl.DataFrame): The input DataFrame (not used directly).
            col (str): The name of the resulting column.
            params (dict): Dictionary containing:
                - "columns" (list): List of column names to coalesce (in order of priority).

        Returns:
            pl.Expr: An expression that returns the first non-null value among the given columns.

        Raises:
            ValueError: If the "columns" parameter is not provided.
        """
        cols = params.get("columns", [])
        if not cols:
            raise ValueError("❌ 'columns' param is required for 'coalesce_cols'")
        return pl.coalesce([pl.col(c) for c in cols]).alias(col)

    @staticmethod
    def split_name_parts(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
        """
        Splits a full name string and extracts either the first or last part.

        Example:
            "John Doe Smith" with part="first" → "John"
            "John Doe Smith" with part="last" → "Smith"

        Parameters:
            _df (pl.DataFrame): The input DataFrame (not used directly).
            col (str): The name of the column containing full names.
            params (dict): Dictionary containing:
                - "part" (str): Must be either "first" or "last". Defaults to "first".

        Returns:
            pl.Expr: An expression that extracts the desired part of the name.
        """
        part = params.get("part", "first")

        if part == "first":
            return pl.col(col).cast(pl.Utf8).str.split(" ").list.get(0).alias(col)
        elif part == "last":
            return pl.col(col).cast(pl.Utf8).str.split(" ").list.get(-1).alias(col)
        else:
            return pl.lit("").alias(col)

    @staticmethod
    def generalize_number_range(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
        """
        Generalizes numeric values into intervals of fixed size (e.g., 0-9, 10-19, etc.).

        Example:
            Value: 23, interval: 10 → "20-29"

        Parameters:
            _df (pl.DataFrame): The input DataFrame (not used directly).
            col (str): The name of the column with numeric values.
            params (dict): Dictionary containing:
                - "interval" (int): Size of each numeric range (default: 10).

        Returns:
            pl.Expr: An expression that groups numbers into interval buckets.
        """
        interval = params.get("interval", 10)
        base = (pl.col(col).cast(pl.Int64) // interval) * interval
        return (base.cast(pl.Utf8) + pl.lit("-") + (base + interval - 1).cast(pl.Utf8)).alias(col)

    @staticmethod
    def mask_partial(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
        """
        Partially masks values by keeping the beginning and end visible, and masking the middle.

        Example:
            Value: "abcdef", visible_start: 2, visible_end: 2 → "ab**ef"

        Parameters:
            _df (pl.DataFrame): The input DataFrame (not used directly).
            col (str): The name of the column to mask.
            params (dict): Dictionary containing:
                - "visible_start" (int): Number of visible characters at the start (default: 2).
                - "visible_end" (int): Number of visible characters at the end (default: 2).
                - "mask_char" (str): Character used for masking (default: "*").

        Returns:
            pl.Expr: An expression that partially masks each string value.
        """
        visible_start = params.get("visible_start", 2)
        visible_end = params.get("visible_end", 2)
        mask_char = params.get("mask_char", "*")

        return (
            pl.col(col)
            .cast(pl.Utf8)
            .map_elements(
                lambda x: (
                    x[:visible_start] + mask_char * (len(x) - visible_start - visible_end) + x[-visible_end:]
                    if len(x) > visible_start + visible_end else x
                ),
                return_dtype=pl.Utf8
            )
            .alias(col)
        )

    @staticmethod
    def round_number(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
        """
        Rounds numeric values in the column to a specified number of decimal places.

        Example:
            3.14159 with digits=2 → 3.14

        Parameters:
            _df (pl.DataFrame): The input DataFrame (not used directly).
            col (str): The name of the numeric column to round.
            params (dict): Dictionary containing:
                - "digits" (int): Number of decimal places to keep (default: 0).

        Returns:
            pl.Expr: An expression that rounds numbers to the specified precision.
        """
        digits = params.get("digits", 0)
        return pl.col(col).cast(pl.Float64).round(digits).alias(col)

    @staticmethod
    def round_date(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
        """
        Rounds date values down to the start of the month or year.

        Example:
            "2025-07-29" with mode="month" → "2025-07-01"
            "2025-07-29" with mode="year" → "2025-01-01"

        Parameters:
            _df (pl.DataFrame): The input DataFrame (not used directly).
            col (str): The name of the column containing date strings in "YYYY-MM-DD" format.
            params (dict): Dictionary containing:
                - "mode" (str): Rounding mode: "month" or "year" (default: "day", which means no rounding).

        Returns:
            pl.Expr: An expression that returns rounded date strings.
        """
        mode = params.get("mode", "day")

        def rounder(s: str) -> str:
            try:
                d = datetime.strptime(s, "%Y-%m-%d")
                if mode == "month":
                    return d.replace(day=1).strftime("%Y-%m-%d")
                elif mode == "year":
                    return d.replace(month=1, day=1).strftime("%Y-%m-%d")
                return s
            except Exception:
                return "invalid"

        return (
            pl.col(col)
            .cast(pl.Utf8)
            .map_elements(rounder, return_dtype=pl.Utf8)
            .alias(col)
        )

    @staticmethod
    def apply_conditioned_expr(col: str, expr: pl.Expr, condition: dict) -> pl.Expr:
        """
        Applies an expression only to rows that satisfy a given condition.

        If the condition is not met, the original value is kept.

        Parameters:
            col (str): The name of the target column being transformed.
            expr (pl.Expr): The transformation expression to apply conditionally.
            condition (dict): A dictionary defining the condition with:
                - "column" (str): Column to evaluate.
                - "operator" (str): One of ["equals", "not_equals", "in", "not_in", "gt", "gte",
                                            "lt", "lte", "contains", "not_contains"].
                - "value" (any): The value to compare against.

        Returns:
            pl.Expr: The resulting expression with conditional logic applied.

        Raises:
            ValueError: If an unsupported operator is provided or required keys are missing.
        """
        condition_col = condition.get("column")
        operator = condition.get("operator", "equals")
        value = condition.get("value")

        if not condition_col or value is None:
            return expr

        col_expr = pl.col(condition_col)

        if isinstance(value, (int, float)):
            col_expr = col_expr.cast(pl.Float64 if isinstance(value, float) else pl.Int64)
        elif isinstance(value, str):
            col_expr = col_expr.cast(pl.Utf8)
        elif isinstance(value, list) and all(isinstance(v, str) for v in value):
            col_expr = col_expr.cast(pl.Utf8)

        cond_expr = {
            "equals": col_expr == value,
            "not_equals": col_expr != value,
            "in": col_expr.is_in(value),
            "not_in": ~col_expr.is_in(value),
            "gt": col_expr > value,
            "gte": col_expr >= value,
            "lt": col_expr < value,
            "lte": col_expr <= value,
            "contains": col_expr.cast(pl.Utf8).str.contains(value),
            "not_contains": ~col_expr.cast(pl.Utf8).str.contains(value),
        }.get(operator)

        if cond_expr is None:
            raise ValueError(f"Unsupported operator: {operator}")

        return pl.when(cond_expr).then(expr).otherwise(pl.col(col)).alias(col)

    @classmethod
    def anonymize(cls, df: pl.DataFrame, config: dict) -> pl.DataFrame:
        """
        Applies one or more anonymization methods to a Polars DataFrame based on a given configuration.

        The configuration allows defining one or more anonymization strategies per column,
        optionally using conditions to apply them selectively.

        Parameters:
            df (pl.DataFrame): The original input DataFrame.
            config (dict): A dictionary with the following structure:
                {
                    "columns": {
                        "column_name": "method_name" | {
                            "method": "method_name",
                            "params": { ... },
                            "condition": { ... }
                        } | [ ... multiple rules ... ]
                    }
                }

        Special Cases:
            - If a column method is "drop", the column will be removed.
            - If a method includes a "condition", it will only be applied where the condition is satisfied.
            - Columns not found in the DataFrame will be skipped unless used in a conditional rule,
              in which case a `null` column will be added before applying the condition.

        Returns:
            pl.DataFrame: A new DataFrame with the applied anonymization rules.
        """
        logger.info("🔐 Starting anonymization process...")
        exprs = []
        dispatch_map = cls.build_dispatch_map()

        dropped_cols = [col for col, rule in config["columns"].items()
                        if isinstance(rule, dict) and rule.get("method") == "drop"]

        if dropped_cols:
            logger.warning(f"⚠️ Dropping columns: {dropped_cols}")
            df = df.drop(dropped_cols)

        for col, rule in config["columns"].items():
            column_exists = col in df.columns
            has_condition = (
                                    isinstance(rule, dict) and "condition" in rule
                            ) or (
                                    isinstance(rule, list) and any(
                                isinstance(r, dict) and "condition" in r for r in rule
                            )
                            )

            if not column_exists:
                if has_condition:
                    logger.info(f"➕ Column '{col}' not found — adding as null to apply conditional rule.")
                    df = df.with_columns(pl.lit(None).alias(col))
                else:
                    logger.warning(f"⏭️ Skipping unknown column: {col}")
                    continue

            rule_list = [rule] if isinstance(rule, (str, dict)) else rule
            current_expr = pl.col(col)

            for r in rule_list:
                method, params = (r, {}) if isinstance(r, str) else (r.get("method"), r.get("params", {}))
                condition = r.get("condition") if isinstance(r, dict) else None

                if method not in dispatch_map:
                    logger.error(f"❌ Unknown method '{method}' for column '{col}'. Skipping.")
                    continue

                logger.debug(f"🔧 Applying method '{method}' to column '{col}'"
                             f"{' with condition' if condition else ''}")
                expr = dispatch_map[method](df, col, params)
                expr = cls.apply_conditioned_expr(col, expr, condition) if condition else expr
                current_expr = expr

            exprs.append(current_expr.alias(col))

        result_df = df.with_columns(exprs) if exprs else df
        logger.success(f"✅ Anonymization complete. {len(exprs)} column(s) processed.")
        return result_df

    @classmethod
    def build_dispatch_map(cls):
        """
        Builds a mapping between method names (as strings) and their corresponding
        anonymization functions defined in this class.

        This is used internally by `anonymize()` to dynamically dispatch method calls
        based on the configuration.

        Returns:
            dict: A dictionary where keys are method names and values are callables with signature:
                  (df: pl.DataFrame, col: str, params: dict) → pl.Expr
        """
        return {
            name: (lambda m: (lambda df, col, params: m(df, col, params)))(method)
            for name, method in inspect.getmembers(cls, predicate=inspect.isfunction)
            if not name.startswith("_") and name not in {"apply_conditioned_expr", "anonymize", "build_dispatch_map"}
        }
