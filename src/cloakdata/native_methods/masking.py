import polars as pl

from .catalog import native_method


@native_method
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


@native_method
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


@native_method
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
    mask_len = params.get("len")
    preserve_nulls = bool(params.get("preserve_nulls", True))

    prefix = s.str.slice(0, keep)

    if mask_len is not None:
        mask_expr = pl.lit(mask_char * int(mask_len))
    else:
        rest = s.str.slice(keep)
        mask_expr = rest.str.replace_all(r".", mask_char, literal=False)

    core = prefix + mask_expr
    return pl.when(s.is_null()).then(pl.lit(None)).otherwise(core) if preserve_nulls else core


@native_method
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


@native_method
def initials_only(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    """
    Convert names into initials.

    Examples:
      - "John Doe"          -> "J.D."
      - "Ana   Clara Silva" -> "A.C.S."
      - "Madonna"           -> "M."
      - "   "               -> ""
      - Already-initials like "J.D." stay unchanged.

    Rules:
      - None -> None
      - "" / whitespace -> ""
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


@native_method
def mask_partial(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    """
    Partially masks values by keeping the beginning and end visible, and masking the middle.

    Example:
        Value: "abcdef", visible_start: 2, visible_end: 2 -> "ab**ef"

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
    visible_start = int(params.get("visible_start", params.get("prefix", 2)))
    visible_end = int(params.get("visible_end", params.get("suffix", 2)))
    mask_char = str(params.get("mask_char", params.get("mask", "*")))

    if visible_start < 0 or visible_end < 0:
        raise ValueError("'visible_start' and 'visible_end' must be >= 0.")

    s = pl.col(col).cast(pl.Utf8)
    total_len = s.str.len_chars()
    middle_len = total_len - (visible_start + visible_end)

    prefix = s.str.slice(0, visible_start)
    middle = s.str.slice(visible_start, middle_len).str.replace_all(r".", mask_char, literal=False)
    suffix = pl.lit("") if visible_end == 0 else s.str.slice(-visible_end)

    masked = prefix + middle + suffix

    return (
        pl.when(s.is_null())
        .then(None)
        .when(total_len > visible_start + visible_end)
        .then(masked)
        .otherwise(s)
        .alias(col)
    )


@native_method
def mask_credit_card(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    params = params or {}
    keep_last = int(params.get("keep_last", 4))
    mask_char = str(params.get("mask_char", params.get("mask", "*")))
    preserve_nulls = bool(params.get("preserve_nulls", True))

    if keep_last < 0:
        raise ValueError("mask_credit_card: 'keep_last' must be >= 0")
    s = pl.col(col).cast(pl.Utf8)
    digits_only = s.str.replace_all(r"\D", "")
    digit_count = digits_only.str.len_chars()

    if keep_last == 0:
        masked = s.str.replace_all(r"\d", mask_char)
    else:
        preserved_suffix = digits_only.str.slice(-keep_last)

        grouped_16 = (
            (pl.lit(mask_char * 4) + pl.lit(" "))
            + (pl.lit(mask_char * 4) + pl.lit(" "))
            + (pl.lit(mask_char * 4) + pl.lit(" "))
            + preserved_suffix
        )
        grouped_16_hyphen = (
            (pl.lit(mask_char * 4) + pl.lit("-"))
            + (pl.lit(mask_char * 4) + pl.lit("-"))
            + (pl.lit(mask_char * 4) + pl.lit("-"))
            + preserved_suffix
        )
        plain_16 = pl.lit(mask_char * 12) + preserved_suffix
        fallback = s

        masked = (
            pl.when(s.str.contains(r"^\d{16}$", literal=False))
            .then(plain_16)
            .when(s.str.contains(r"^\d{4} \d{4} \d{4} \d{4}$", literal=False))
            .then(grouped_16)
            .when(s.str.contains(r"^\d{4}-\d{4}-\d{4}-\d{4}$", literal=False))
            .then(grouped_16_hyphen)
            .otherwise(fallback)
        )

    expr = pl.when(digit_count <= keep_last).then(s).otherwise(masked)

    if preserve_nulls:
        expr = pl.when(s.is_null()).then(None).otherwise(expr)

    return expr.alias(col)


@native_method
def mask_cpf(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    params = params or {}
    keep_last = int(params.get("keep_last", 2))
    mask_char = str(params.get("mask_char", params.get("mask", "*")))
    preserve_nulls = bool(params.get("preserve_nulls", True))

    if keep_last < 0:
        raise ValueError("mask_cpf: 'keep_last' must be >= 0")

    s = pl.col(col).cast(pl.Utf8)
    digits_only = s.str.replace_all(r"\D", "")
    digit_count = digits_only.str.len_chars()

    if keep_last == 0:
        plain_masked = pl.lit(mask_char * 11)
        formatted_masked = pl.lit(f"{mask_char * 3}.{mask_char * 3}.{mask_char * 3}-{mask_char * 2}")
    else:
        visible_suffix = digits_only.str.slice(-keep_last)
        masked_digits = pl.lit(mask_char * (11 - keep_last)) + visible_suffix

        # Only preserve punctuation for the common CPF display format.
        plain_masked = masked_digits
        formatted_masked = (
            masked_digits.str.slice(0, 3)
            + pl.lit(".")
            + masked_digits.str.slice(3, 3)
            + pl.lit(".")
            + masked_digits.str.slice(6, 3)
            + pl.lit("-")
            + masked_digits.str.slice(9, 2)
        )

    masked = (
        pl.when(s.str.contains(r"^\d{11}$", literal=False))
        .then(plain_masked)
        .when(s.str.contains(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", literal=False))
        .then(formatted_masked)
        .otherwise(s)
    )

    expr = pl.when(digit_count <= keep_last).then(s).otherwise(masked)

    if preserve_nulls:
        expr = pl.when(s.is_null()).then(None).otherwise(expr)

    return expr.alias(col)
