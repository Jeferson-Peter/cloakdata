import polars as pl
from loguru import logger

from cloakdata import anonymize

df = pl.DataFrame({"name": ["Alice", "Bob", "Alice", "Carol"]}).with_columns(
    [
        pl.col("name").alias("alpha_default"),
        pl.col("name").alias("alpha_start_X"),
        pl.col("name").alias("alpha_no_prefix"),
    ]
)

config = {
    "columns": {
        "alpha_default": {"method": "sequential_alpha"},
        "alpha_start_X": {"method": "sequential_alpha", "params": {"start": "X"}},
        "alpha_no_prefix": {"method": "sequential_alpha", "params": {"prefix": None}},
    }
}

out = anonymize(df, config)
logger.info(out)
