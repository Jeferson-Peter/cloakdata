import polars as pl
from loguru import logger

from cloakdata import anonymize

# Original dataset
df = pl.DataFrame(
    {
        "email_primary": [None, "user2@main.com", None],
        "email_secondary": ["user1@backup.com", None, None],
        "email_fallback": ["fallback1@mail.com", "fallback2@mail.com", "fallback3@mail.com"],
    }
)

# Duplicate / target column where the coalesced result will be written
df = df.with_columns(
    [
        pl.col("email_primary").alias("email_final"),
    ]
)

config = {
    "columns": {
        # Take the first non-null value in order:
        # email_primary → email_secondary → email_fallback
        "email_final": {
            "method": "coalesce_cols",
            "params": {
                "columns": [
                    "email_primary",
                    "email_secondary",
                    "email_fallback",
                ]
            },
        }
    }
}

out = anonymize(df, config)
logger.info(out)
