import polars as pl
from loguru import logger

from cloakdata import anonymize

# Original dataset
df = pl.DataFrame(
    {
        "event_date": [
            "2024-01-10",
            "2024-01-15",
            "2024-01-20",
            None,
        ]
    }
)

# Duplicate column to demonstrate different configurations
df = df.with_columns(
    [
        pl.col("event_date").alias("date_default"),
        pl.col("event_date").alias("date_small_offset"),
        pl.col("event_date").alias("date_large_offset"),
        pl.col("event_date").alias("date_deterministic"),
    ]
)

config = {
    "columns": {
        # Default behavior: min_days=0, max_days=0 (no shift)
        "date_default": {
            "method": "date_offset",
        },
        # Small random offset between -1 and +1 day
        "date_small_offset": {
            "method": "date_offset",
            "params": {
                "min_days": -1,
                "max_days": 1,
            },
        },
        # Larger random offset between -7 and +7 days
        "date_large_offset": {
            "method": "date_offset",
            "params": {
                "min_days": -7,
                "max_days": 7,
            },
        },
        # Deterministic offset using a fixed seed
        "date_deterministic": {
            "method": "date_offset",
            "params": {
                "min_days": -3,
                "max_days": 3,
                "seed": 42,
            },
        },
    }
}

out = anonymize(df, config)

logger.info(out)
