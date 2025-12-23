import polars as pl
from loguru import logger

from cloakdata import anonymize

# Original dataset
df = pl.DataFrame(
    {
        "value": [
            3.14159,
            2.71828,
            10.0,
            -2.345,
            None,
        ]
    }
)

# Duplicate column to demonstrate different configurations
df = df.with_columns(
    [
        pl.col("value").alias("round_default"),
        pl.col("value").alias("round_2_digits"),
        pl.col("value").alias("round_1_digit"),
        pl.col("value").alias("round_0_digits_explicit"),
    ]
)

config = {
    "columns": {
        # Default behavior: digits=0
        # 3.14159 -> 3.0
        "round_default": {
            "method": "round_number",
        },
        # Keep 2 decimal places
        # 3.14159 -> 3.14
        "round_2_digits": {
            "method": "round_number",
            "params": {"digits": 2},
        },
        # Keep 1 decimal place (also shows negative rounding)
        # -2.345 -> -2.3 (Polars rounding rules apply)
        "round_1_digit": {
            "method": "round_number",
            "params": {"digits": 1},
        },
        # Explicit digits=0 (same as default)
        # 2.71828 -> 3.0
        "round_0_digits_explicit": {
            "method": "round_number",
            "params": {"digits": 0},
        },
    }
}

out = anonymize(df, config)
logger.info(out)
