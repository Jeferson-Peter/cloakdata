import inspect
from collections.abc import Callable

import polars as pl

EXPECT_NUM_PARAMS = 3


def validate_regex(pattern: str, context: str) -> None:
    """Compile a pattern with Polars on a dummy value, without accessing input data."""
    try:
        pl.select(pl.lit("").str.contains(pattern))
    except pl.exceptions.ComputeError as err:
        raise ValueError(f"{context}: invalid regex; use Polars (Rust regex) syntax") from err


def validate_signature_only(func: Callable) -> None:
    """
    Ensure the anonymization method has signature (df, col, params).
    """
    sig = inspect.signature(func)
    params = list(sig.parameters.values())
    if len(params) != EXPECT_NUM_PARAMS:
        raise TypeError(
            f"{func.__name__} must take exactly 3 parameters: " "'df', 'col', and 'params'."
        )
    if any(
        p.kind not in {inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD}
        for p in params
    ):
        raise TypeError("Custom method parameters must accept three positional arguments")

    def ok(nm: str, expect: str) -> bool:
        # PLR1714: use membership instead of chained ORs
        return nm in {expect, f"_{expect}"}

    got = [p.name for p in params]
    if not (ok(got[0], "df") and ok(got[1], "col") and ok(got[2], "params")):
        raise TypeError(
            f"{func.__name__} parameters must be named "
            "('df', 'col', 'params') or prefixed with underscores."
        )
