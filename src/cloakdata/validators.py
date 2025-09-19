import inspect
from collections.abc import Callable

EXPECT_NUM_PARAMS = 3


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

    def ok(nm: str, expect: str) -> bool:
        # PLR1714: use membership instead of chained ORs
        return nm in {expect, f"_{expect}"}

    got = [p.name for p in params]
    if not (ok(got[0], "df") and ok(got[1], "col") and ok(got[2], "params")):
        raise TypeError(
            f"{func.__name__} parameters must be named "
            "('df', 'col', 'params') or prefixed with underscores."
        )
