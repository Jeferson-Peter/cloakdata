import random
import string
from datetime import datetime

import polars as pl


class AnonymizationMethods:
    """
    A collection of static methods for anonymizing or masking sensitive data in Polars DataFrames.

    This class provides various anonymization strategies such as full -masking, email obfuscation,
    data generalization, conditional replacement, pseudonymization, and more.

    Each method returns a `pl.Expr` that can be applied to a column in a Polars DataFrame.
    """

    @staticmethod
    def full_mask(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
        """
        Fully masks values with a minimal config surface.

        params (optional):
          - char: str = "*"
          - len: int = 5
          - mask_literal: str | None = None   # if present, it wins
          - match_length: bool = False        # repeats `char` to original length
          - preserve_nulls: bool = True
        """
        s = pl.col(col).cast(pl.Utf8)
        preserve_nulls = bool(params.get("preserve_nulls", True))
        char = str(params.get("char", "*"))
        length_fixed = int(params.get("len", 5))
        mask_literal = params.get("mask_literal")
        match_length = bool(params.get("match_length", False))

        if mask_literal is not None:
            core = pl.lit(str(mask_literal))
        elif match_length:
            core = s.str.replace_all(r".", char, literal=False)
        else:
            core = pl.lit(char * length_fixed)

        expr = pl.when(s.is_null()).then(pl.lit(None)).otherwise(core) if preserve_nulls else core
        return expr

    @staticmethod
    def mask_email(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
        """
        Masks the local part of email addresses, keeping or replacing the domain.

        Parameters:
            _df (pl.DataFrame): The input DataFrame (not used in this method).
            col (str): The name of the column containing email addresses.
            params (dict, optional): {
                "mask": str = "xxxxx",           # replacement for the local part
                "fallback_domain": str = "hidden.com",  # used when input is not a valid email
                "preserve_nulls": bool = True    # if False, replace nulls with mask@fallback_domain
            }

        Returns:
            pl.Expr: An expression masking email addresses while preserving domain.
        """
        s = pl.col(col).cast(pl.Utf8)
        mask = params.get("mask", "xxxxx")
        fallback_domain = params.get("fallback_domain", "hidden.com")
        preserve_nulls = bool(params.get("preserve_nulls", True))

        masked = s.str.replace(r"^[^@]+@", mask + "@", literal=False)

        expr = (
            pl.when(s.is_null())
            .then(pl.lit(None) if preserve_nulls else pl.lit(f"{mask}@{fallback_domain}"))
            .when(s.str.contains("@"))
            .then(masked)
            .otherwise(pl.lit(f"{mask}@{fallback_domain}"))
        )
        return expr.alias(col)

    @staticmethod
    def mask_number(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
        """
        Masks part of a numeric string, preserving the first `keep` characters.

        params (optional):
          - keep: int = 3                  # how many leading chars to preserve
          - mask: str = "*"                # mask character
          - len: int | None = None         # fixed number of mask chars (else: fill the rest)
          - preserve_nulls: bool = True    # keep nulls untouched
        """
        s = pl.col(col).cast(pl.Utf8)
        keep = int(params.get("keep", 3))
        mask_char = str(params.get("mask", "*"))
        mask_len = params.get("len")  # None -> dynamic
        preserve_nulls = bool(params.get("preserve_nulls", True))

        prefix = s.str.slice(0, keep)

        if mask_len is not None:
            # fixed number of mask chars
            mask_expr = pl.lit(mask_char * int(mask_len))
        else:
            # dynamic: mask everything after the first `keep` chars
            rest = s.str.slice(keep)  # empty if length <= keep; null stays null
            mask_expr = rest.str.replace_all(r".", mask_char, literal=False)

        core = prefix + mask_expr
        return pl.when(s.is_null()).then(pl.lit(None)).otherwise(core) if preserve_nulls else core

    @staticmethod
    def replace_with_value(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
        """
        Replace all values in the column with a static value.

        Required:
          - value: Any scalar (str/int/float/bool/...).
        Optional:
          - preserve_nulls: bool = False  # if True, keeps nulls unchanged
        """
        if "value" not in params:
            raise ValueError("replace_with_value: 'value' parameter is required")

        value = params["value"]
        preserve_nulls = bool(params.get("preserve_nulls", False))

        expr = pl.lit(value)
        if preserve_nulls:
            expr = pl.when(pl.col(col).is_null()).then(None).otherwise(expr)
        return expr.alias(col)

    @staticmethod
    def replace_by_contains(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
        """
        Replace values in `col` when they CONTAIN given substrings.

        Notes:
          - Literal substring matching by default (no regex).
          - Rules are applied in order; first match wins.
          - Nulls are preserved.

        Params:
          - mapping: dict[str, str]  # substring -> replacement
          - substr + replacement: convenience for single mapping
          - case_sensitive: bool = True
          - use_regex: bool = False
        """
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
            pattern = sub if use_regex else sub
            cond = acc.str.contains(pattern, literal=not use_regex).fill_null(False)

            if not case_sensitive and not use_regex:
                cond = (
                    acc.str.to_lowercase().str.contains(sub.lower(), literal=True).fill_null(False)
                )

            acc = pl.when(cond).then(pl.lit(rep)).otherwise(acc)

        return acc.alias(col)

    @staticmethod
    def replace_exact(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
        """
        Exact-value replacement using a mapping.
        - Values not in the mapping are left unchanged.
        - Dtype is inferred from replacements (no forced Utf8).
        - Optional explicit None mapping supported via params['map_null'].
        Params:
          - mapping (dict): {original_value: replacement_value}  [required]
          - map_null (bool): if True and None in mapping, apply to nulls. Default False.
        """
        mapping: dict = params.get("mapping", {})

        old = list(mapping.keys())
        new = list(mapping.values())

        expr = pl.col(col).replace(old, new)

        return expr.alias(col)

    @staticmethod
    def sequential_numeric(df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
        """
        Replace unique values with sequential numeric labels.
        Duplicates get the same pseudonym.

        Params:
          - start (int, default=1)
          - prefix (str | None, default="val")
            * None -> retorna inteiros reais (dtype Int64)
            * string -> retorna rótulos de texto (dtype Utf8)
        """
        params = params or {}
        start = int(params.get("start", 1))
        prefix = params.get("prefix", "val")

        uniq_s = df.select(pl.col(col)).unique().to_series()

        if prefix is None:
            labels_int = list(range(start, start + len(uniq_s)))
            mapping = dict(zip(uniq_s.to_list(), labels_int, strict=False))
            expr = pl.col(col).replace(list(mapping.keys()), list(mapping.values()))
            return expr.cast(pl.Int64).alias(col)

        old_utf8 = uniq_s.cast(pl.Utf8).to_list()
        new_utf8 = [f"{prefix} {i}" for i in range(start, start + len(old_utf8))]
        expr = pl.col(col).cast(pl.Utf8).replace(old_utf8, new_utf8).cast(pl.Utf8)
        return expr.alias(col)

    @staticmethod
    def sequential_alpha(df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
        """
        Replace unique values in the column with alphabetically indexed labels.
        Repeated values receive the same label. Order follows first appearance.

        Example:
            "Alice", "Bob", "Alice" → "val A", "val B", "val A"

        Params:
          - start (str, default="A"): starting label ("A", "Z", "AA", ...)
          - prefix (str | None, default="val"): optional prefix; None → no prefix
        """

        def alpha_to_num(s: str) -> int:
            s = (s or "A").strip().upper()
            if not s:
                return 1
            n = 0
            for ch in s:
                if "A" <= ch <= "Z":
                    n = n * 26 + (ord(ch) - 64)
            return max(n, 1)

        def num_to_alpha(n: int) -> str:
            out = ""
            while n > 0:
                n, r = divmod(n - 1, 26)
                out = chr(65 + r) + out
            return out

        params = params or {}
        start_label = params.get("start", "A")
        start_idx = alpha_to_num(start_label)
        prefix = params.get("prefix", "val")

        uniques = df.select(pl.col(col)).unique(maintain_order=True).to_series().to_list()

        labels = [
            f"{prefix} {num_to_alpha(idx)}" if prefix is not None else num_to_alpha(idx)
            for idx, _ in enumerate(uniques, start=start_idx)
        ]

        mapping = dict(zip(uniques, labels, strict=False))
        return pl.col(col).replace(list(mapping.keys()), list(mapping.values())).alias(col)

    @staticmethod
    def truncate(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
        """
        Truncate string values in the column to a fixed maximum length.

        Params:
          - length (int, required): number of chars to keep (must be >= 0)
          - preserve_nulls (bool): keep nulls unchanged (default: True)
        """
        length = params.get("length", 4)
        preserve_nulls = params.get("preserve_nulls", True)

        try:
            length = int(length)
        except Exception as err:
            raise ValueError("'length' must be an integer.") from err

        if length < 0:
            raise ValueError("'length' must be >= 0.")

        s = pl.col(col).cast(pl.Utf8)

        truncated = s.str.slice(0, length)

        if preserve_nulls:
            return pl.when(s.is_null()).then(None).otherwise(truncated).alias(col)

        return truncated.alias(col)

    @staticmethod
    def initials_only(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
        """
        Convert names into initials.

        Examples:
          - "John Doe"          → "J.D."
          - "Ana   Clara Silva" → "A.C.S."
          - "Madonna"           → "M."
          - "   "               → ""
          - Already-initials like "J.D." stay unchanged.

        Rules:
          - None → None
          - "" / whitespace → ""
          - Non-string values are cast to string first.
        """
        _preserve_nulls = params.get("preserve_nulls", True)

        orig = pl.col(col).cast(pl.Utf8)

        s = orig.fill_null("")

        trimmed = s.str.strip_chars()

        is_initials = trimmed.str.contains(r"^([A-Z]\.)+$", literal=False)
        is_empty = trimmed.str.len_chars() == 0

        core = trimmed.str.split(" ").list.eval(
            pl.element().filter(pl.element().str.len_chars() > 0).str.slice(0, 1).str.to_uppercase()
        )

        computed = core.list.join(".") + pl.lit(".")

        initials_body = (
            pl.when(is_initials).then(trimmed).when(is_empty).then(pl.lit("")).otherwise(computed)
        )

        result = pl.when(orig.is_null()).then(None).otherwise(initials_body)

        return result.alias(col)

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
        return (base.cast(pl.Utf8) + pl.lit("-") + (base + 9).cast(pl.Utf8)).alias(col)

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
        Substitui cada valor por uma escolha aleatória dentre `choices`.
        Se `seed` for fornecido em params, o resultado é determinístico.
        Preserva None.
        """
        params = params or {}
        choices = params.get("choices", ["X", "Y"])
        seed = params.get("seed", None)

        rng = random.Random(seed) if seed is not None else random

        return (
            pl.col(col)
            .map_elements(
                lambda v: None if v is None else rng.choice(choices),
                return_dtype=pl.Utf8,
            )
            .alias(col)
        )

    @staticmethod
    def replace_with_random_digits(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
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
            .map_elements(
                lambda _: "".join(random.choices(string.digits, k=params.get("digits", 11))),
                return_dtype=pl.Utf8,
            )
            .alias(col)
        )

    @staticmethod
    def shuffle(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
        """
        Randomly shuffles the values in the specified column.

        Note:
            This method preserves the original values but reorders them randomly.

        Parameters:
            _df (pl.DataFrame): The input DataFrame (not used directly).
            col (str): The name of the column to shuffle.
            params (dict): Parameters dictionary.

        Returns:
            pl.Expr: An expression that shuffles the column values.
        """
        params = params or {}
        seed = params.get("seed")
        return pl.col(col).shuffle(seed=seed).alias(col)

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
        params = params or {}
        min_days = int(params.get("min_days", 0))
        max_days = int(params.get("max_days", 0))
        seed = int(params.get("seed", 0))

        if max_days < min_days:
            min_days, max_days = max_days, min_days

        span = (max_days - min_days) + 1

        base = pl.col(col).str.strptime(pl.Date, format="%Y-%m-%d", strict=False)

        idx = pl.arange(0, pl.len(), eager=False).cast(pl.UInt64)
        rnd = idx.hash(seed=seed)
        offset = (rnd % span).cast(pl.Int64) + min_days

        return (
            pl.when(base.is_not_null())
            .then((base + pl.duration(days=offset)).dt.strftime("%Y-%m-%d"))
            .otherwise(pl.lit(None))
            .alias(col)
        )

    @staticmethod
    def coalesce_cols(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
        """
        Returns the first non-null value from a list of columns and assigns
        it to the target column.

        Example:
            If column "A" is null, but "B" has a value, it will use "B". Follows
            the order of the list.

        Parameters:
            _df (pl.DataFrame): The input DataFrame (not used directly).
            col (str): The name of the resulting column.
            params (dict): Dictionary containing:
                - "columns" (list): List of column names to coalesce
                 (in order of priority).

        Returns:
            pl.Expr: An expression that returns the first non-null
             value among the given columns.

        Raises:
            ValueError: If the "columns" parameter is not provided.
        """
        cols = params.get("columns", [])
        if not cols:
            raise ValueError("❌ 'columns' param is required for 'coalesce_cols'")
        return pl.coalesce([pl.col(c) for c in cols]).alias(col)

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
                    x[:visible_start]
                    + mask_char * (len(x) - visible_start - visible_end)
                    + x[-visible_end:]
                    if len(x) > visible_start + visible_end
                    else x
                ),
                return_dtype=pl.Utf8,
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
                - "mode" (str): Rounding mode: "month" or "year"
                 (default: "day", which means no rounding).

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

        return pl.col(col).cast(pl.Utf8).map_elements(rounder, return_dtype=pl.Utf8).alias(col)
