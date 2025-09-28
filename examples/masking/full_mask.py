import polars as pl
from loguru import logger

from cloakdata import anonymize

df = pl.DataFrame({"ssn": ["123-45-6789", "987-65-4321", None]})

df = df.with_columns(
    [
        pl.col("ssn").alias("ssn_fixed_default"),
        pl.col("ssn").alias("ssn_fixed_custom"),
        pl.col("ssn").alias("ssn_literal"),
        pl.col("ssn").alias("ssn_dynamic"),
        pl.col("ssn").alias("ssn_overwrite_nulls"),
    ]
)

config = {
    "columns": {
        "ssn_fixed_default": {"method": "full_mask"},
        "ssn_fixed_custom": {"method": "full_mask", "params": {"char": "X", "len": 8}},
        "ssn_literal": {"method": "full_mask", "params": {"mask_literal": "REDACTED"}},
        "ssn_dynamic": {"method": "full_mask", "params": {"match_length": True, "char": "#"}},
        "ssn_overwrite_nulls": {"method": "full_mask", "params": {"preserve_nulls": False}},
    }
}

out = anonymize(df, config)

logger.info(out)
