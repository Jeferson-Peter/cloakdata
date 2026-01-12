import polars as pl
from loguru import logger

from cloakdata import anonymize

# Original dataset
df = pl.DataFrame(
    {
        "date": [
            "2025-07-29",
            "2024-01-15",
            "2023-12-31",
            None,
            "invalid-date",
        ]
    }
)

# Duplicate column to demonstrate different configurations
df = df.with_columns(
    [
        pl.col("date").alias("round_month"),
        pl.col("date").alias("round_year"),
    ]
)

config = {
    "columns": {
        # Round to start of the month
        # "2025-07-29" → "2025-07-01"
        "round_month": {
            "method": "round_date",
            "params": {
                "mode": "month",
            },
        },
        # Round to start of the year
        # "2025-07-29" → "2025-01-01"
        "round_year": {
            "method": "round_date",
            "params": {
                "mode": "year",
            },
        },
    }
}

out = anonymize(df, config)
logger.info(out)
