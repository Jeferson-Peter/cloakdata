import polars as pl
from loguru import logger

from cloakdata import anonymize

df = pl.DataFrame(
    {
        "num": ["123456789", "42", None, "98765", "7", ""],
    }
)

df = df.with_columns(
    [
        pl.col("num").alias("num_default"),
        pl.col("num").alias("num_custom"),
        pl.col("num").alias("num_fixed_len"),
        pl.col("num").alias("num_overwrite_nulls"),
    ]
)

config = {
    "columns": {
        "num_default": {"method": "mask_number"},
        "num_custom": {"method": "mask_number", "params": {"keep": 2, "mask_char": "X"}},
        "num_fixed_len": {
            "method": "mask_number",
            "params": {"keep": 2, "mask_char": "#", "len": 4},
        },
        "num_overwrite_nulls": {
            "method": "mask_number",
            "params": {"keep": 3, "mask_char": "*", "preserve_nulls": False},
        },
    }
}

out = anonymize(df, config)

logger.info(out)
