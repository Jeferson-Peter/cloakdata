import polars as pl
from loguru import logger

from cloakdata import anonymize

df = pl.DataFrame({"email": ["john.doe@example.com", "maria@domain.org", "invalid", None]})

df = df.with_columns(
    [
        pl.col("email").alias("email_default"),
        pl.col("email").alias("email_custom_mask"),
        pl.col("email").alias("email_custom_fallback"),
        pl.col("email").alias("email_overwrite_nulls"),
    ]
)

config = {
    "columns": {
        "email_default": {"method": "mask_email"},
        "email_custom_mask": {"method": "mask_email", "params": {"mask": "***"}},
        "email_custom_fallback": {"method": "mask_email", "params": {"fallback_domain": "anon.io"}},
        "email_overwrite_nulls": {"method": "mask_email", "params": {"preserve_nulls": False}},
    }
}

out = anonymize(df, config)

logger.info(out)
