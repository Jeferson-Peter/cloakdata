import polars as pl
from loguru import logger

from cloakdata import anonymize

df = pl.DataFrame(
    {
        "email": ["alice@example.com", "bob@example.com", None],
    }
).with_columns(
    [
        pl.col("email").alias("email_sha256"),
        pl.col("email").alias("email_sha256_salted"),
    ]
)

config = {
    "columns": {
        "email_sha256": {
            "method": "hash_value",
        },
        "email_sha256_salted": {
            "method": "hash_value",
            "params": {
                "algorithm": "sha256",
                "salt": "team-2026",
            },
        },
    }
}

out = anonymize(df, config)
logger.info(out)
