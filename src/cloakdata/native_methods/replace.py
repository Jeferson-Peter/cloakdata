import hashlib
import hmac

import polars as pl

from ..validators import validate_regex
from .catalog import native_method

_MIN_HMAC_KEY_BYTES = 32


@native_method
def replace_with_value(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    if "value" not in params:
        raise ValueError("replace_with_value: 'value' parameter is required")

    value = params["value"]
    preserve_nulls = bool(params.get("preserve_nulls", False))

    expr = pl.lit(value)
    if preserve_nulls:
        expr = pl.when(pl.col(col).is_null()).then(None).otherwise(expr)
    return expr.alias(col)


@native_method
def replace_by_contains(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    mapping = params.get("mapping")
    if mapping is not None and not isinstance(mapping, dict):
        raise ValueError("replace_by_contains: 'mapping' must be a dictionary")
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
    haystack = s.str.to_lowercase() if not case_sensitive and not use_regex else s
    result = s
    for sub, rep in reversed(mapping.items()):
        if not isinstance(sub, str):
            raise ValueError("replace_by_contains: mapping keys must be strings")
        pattern = sub
        if not case_sensitive:
            pattern = f"(?i){sub}" if use_regex else sub.lower()
        if use_regex:
            validate_regex(pattern, "replace_by_contains: mapping key or 'substr'")
        result = (
            pl.when(haystack.str.contains(pattern, literal=not use_regex))
            .then(pl.lit(rep))
            .otherwise(result)
        )
    return result.alias(col)


@native_method
def replace_exact(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    mapping: dict = params.get("mapping", {})
    if not isinstance(mapping, dict):
        raise ValueError("replace_exact: 'mapping' must be a dictionary")
    old = list(mapping.keys())
    new = list(mapping.values())
    return pl.col(col).replace(old, new).alias(col)


@native_method
def redact_regex(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    params = params or {}
    pattern = params.get("pattern")
    replacement = str(params.get("replacement", "[REDACTED]"))

    if not isinstance(pattern, str) or not pattern:
        raise ValueError("redact_regex: 'pattern' parameter must be a non-empty string")
    validate_regex(pattern, "redact_regex: 'pattern'")

    return (
        pl.when(pl.col(col).is_null())
        .then(None)
        .otherwise(pl.col(col).cast(pl.Utf8).str.replace_all(pattern, replacement))
        .alias(col)
    )


@native_method
def replace_with_random_digits(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    params = params or {}
    digits = params.get("digits", 11)
    seed = params.get("seed", 0)

    if not isinstance(digits, int) or digits <= 0:
        raise ValueError("replace_with_random_digits: 'digits' must be a positive integer")

    base = pl.arange(0, pl.len()).hash(seed=seed).abs()
    digit_exprs = [((base + i).hash(seed=seed + i) % 10).cast(pl.Utf8) for i in range(digits)]
    random_number = pl.concat_str(digit_exprs)

    return pl.when(pl.col(col).is_null()).then(None).otherwise(random_number).alias(col)


@native_method
def hash_value(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    """Hash UTF-8 text prefixed with a salt, preserving nulls by default."""
    params = params or {}
    algorithm = str(params.get("algorithm", "sha256")).lower()
    salt = str(params.get("salt", ""))
    preserve_nulls = bool(params.get("preserve_nulls", True))

    if algorithm not in hashlib.algorithms_available:
        raise ValueError(f"hash_value: unsupported hash algorithm '{algorithm}'")
    salted = hashlib.new(algorithm, salt.encode())
    if salted.digest_size == 0:
        raise ValueError("hash_value: select a fixed-length hash algorithm")

    def compute_hash(value: object | None) -> str:
        if value is None:
            return salted.hexdigest()
        digest = salted.copy()
        digest.update(f"{value}".encode())
        return digest.hexdigest()

    return (
        pl.col(col)
        .map_elements(compute_hash, return_dtype=pl.String, skip_nulls=preserve_nulls)
        .alias(col)
    )


@native_method
def hmac_value(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    """Create stable HMAC-SHA256 pseudonyms using a caller-supplied secret."""
    key = params.get("key")
    if not isinstance(key, bytes) or len(key) < _MIN_HMAC_KEY_BYTES:
        raise ValueError("hmac_value: 'key' must be at least 32 secret bytes")
    keyed = hmac.new(key, digestmod="sha256")

    def compute_hmac(value: str) -> str:
        digest = keyed.copy()
        digest.update(value.encode())
        return digest.hexdigest()

    return pl.col(col).cast(pl.String).map_elements(compute_hmac, return_dtype=pl.String).alias(col)


@native_method
def replace_with_hash_bucket(_df: pl.DataFrame, col: str, params: dict) -> pl.Expr:
    params = params or {}
    buckets = params.get("buckets", 10)
    prefix = str(params.get("prefix", "group"))
    seed = params.get("seed", 0)
    preserve_nulls = bool(params.get("preserve_nulls", True))

    if not isinstance(buckets, int) or buckets <= 0:
        raise ValueError("replace_with_hash_bucket: 'buckets' must be a positive integer")

    width = max(2, len(str(buckets - 1)))
    bucket_idx = pl.col(col).cast(pl.Utf8).hash(seed=seed).abs() % buckets
    bucket_label = pl.lit(f"{prefix}_") + bucket_idx.cast(pl.Utf8).str.zfill(width)

    expr = bucket_label
    if preserve_nulls:
        expr = pl.when(pl.col(col).is_null()).then(None).otherwise(expr)

    return expr.alias(col)
