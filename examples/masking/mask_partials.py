import polars as pl
from loguru import logger

from cloakdata import anonymize

# Original dataset
df = pl.DataFrame(
    {
        "text": [
            "abcdef",
            "1234567890",
            "email@example.com",
            "short",
            None,
        ]
    }
)

# Duplicate column to demonstrate different configurations
df = df.with_columns(
    [
        pl.col("text").alias("default_mask"),
        pl.col("text").alias("custom_visibility"),
        pl.col("text").alias("only_suffix_visible"),
        pl.col("text").alias("custom_mask_char"),
    ]
)

config = {
    "columns": {
        # Default behavior: visible_start=2, visible_end=2, mask_char="*"
        # "abcdef" → "ab**ef"
        "default_mask": {
            "method": "mask_partial",
        },
        # Custom visibility: keep 3 chars at start and end
        # "abcdef" → "abc*def"
        "custom_visibility": {
            "method": "mask_partial",
            "params": {
                "visible_start": 3,
                "visible_end": 3,
            },
        },
        # Only suffix visible
        # "1234567890" → "********90"
        "only_suffix_visible": {
            "method": "mask_partial",
            "params": {
                "visible_start": 0,
                "visible_end": 2,
            },
        },
        # Custom masking character
        # "email@example.com" → "e###############m"
        "custom_mask_char": {
            "method": "mask_partial",
            "params": {
                "visible_start": 1,
                "visible_end": 1,
                "mask_char": "#",
            },
        },
    }
}

out = anonymize(df, config)
logger.info(out)
