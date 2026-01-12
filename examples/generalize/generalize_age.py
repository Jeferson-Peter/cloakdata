import polars as pl
from loguru import logger

from cloakdata import anonymize

df = pl.DataFrame({"age": [25, 41, 7, 19, 20, 29, None]})

df = df.with_columns(
    [
        pl.col("age").alias("age_default"),
        pl.col("age").alias("age_bucket_5"),
        pl.col("age").alias("age_bucket_20"),
    ]
)

config = {
    "columns": {
        # Standard 10-year buckets: 25 → "20-29"
        "age_default": {"method": "generalize_age"},
        # Custom size=5: 22 → "20-24"
        "age_bucket_5": {"method": "generalize_age", "params": {"size": 5}},
        # Custom size=20: 47 → "40-59"
        "age_bucket_20": {"method": "generalize_age", "params": {"size": 20}},
    }
}

out = anonymize(df, config)
logger.info(out)
