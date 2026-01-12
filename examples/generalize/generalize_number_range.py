import polars as pl
from loguru import logger

from cloakdata import anonymize

# Original dataset
df = pl.DataFrame(
    {
        "amount": [
            -3.5,
            0.0,
            4.2,
            9.9,
            10.0,
            17.3,
            42.0,
            None,
        ]
    }
)

# Duplicate column to demonstrate different configurations
df = df.with_columns(
    [
        pl.col("amount").alias("range_default"),
        pl.col("amount").alias("range_5"),
        pl.col("amount").alias("range_20"),
    ]
)

config = {
    "columns": {
        # Default interval = 10
        # 4.2 → "0-9", 17.3 → "10-19"
        "range_default": {
            "method": "generalize_number_range",
        },
        # Custom interval = 5
        # 4.2 → "0-4", 9.9 → "5-9"
        "range_5": {
            "method": "generalize_number_range",
            "params": {"interval": 5},
        },
        # Custom interval = 20
        # 17.3 → "0-19", 42 → "40-59"
        "range_20": {
            "method": "generalize_number_range",
            "params": {"interval": 20},
        },
    }
}

out = anonymize(df, config)
logger.info(out)
