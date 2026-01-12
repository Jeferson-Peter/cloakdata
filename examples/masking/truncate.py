"""
Examples: truncate string values to a fixed length.

This method trims strings to a maximum number of characters.
- Nulls remain null.
- Non-string inputs are cast to strings before truncation.

Config options:
    length (int): Maximum number of characters to retain (default: 4)
"""

import polars as pl
from loguru import logger

from cloakdata import anonymize

LENGTH_NUMBER = 4

df = pl.DataFrame(
    {
        "city": ["Porto Alegre", "Roma", "NY", None, "São Paulo"],
    }
)

df = df.with_columns(
    [
        pl.col("city").alias("city_default"),
        pl.col("city").alias("city_len2"),
        pl.col("city").alias("city_len0"),
        pl.col("city").alias("city_mixed"),
    ]
).with_columns(
    pl.when(pl.arange(0, pl.len()) == LENGTH_NUMBER)
    .then(12345)
    .otherwise(pl.col("city_mixed"))
    .alias("city_mixed")
)

config = {
    "columns": {
        "city_default": {
            "method": "truncate",
            "params": {},
        },
        "city_len2": {
            "method": "truncate",
            "params": {
                "length": 2,
            },
        },
        "city_len0": {
            "method": "truncate",
            "params": {
                "length": 0,
            },
        },
        "city_mixed": {
            "method": "truncate",
            "params": {
                "length": 3,
            },
        },
    }
}

logger.info("Original DataFrame:")
logger.info(df)

out = anonymize(df, config)

logger.info("After truncate:")
logger.info(out)
