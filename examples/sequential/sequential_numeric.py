import polars as pl
from loguru import logger

from cloakdata import anonymize

df = pl.DataFrame({"name": ["Alice", "Bob", "Alice", "Carol", "Bob", None]})

df = df.with_columns(
    [
        pl.col("name").alias("seq_default"),
        pl.col("name").alias("seq_custom_start"),
        pl.col("name").alias("seq_no_prefix"),
    ]
)

config = {
    "columns": {
        "seq_default": {"method": "sequential_numeric"},
        "seq_custom_start": {"method": "sequential_numeric", "params": {"start": 100}},
        "seq_no_prefix": {"method": "sequential_numeric", "params": {"prefix": None, "start": 1}},
    }
}

out = anonymize(df, config)
logger.info(out)
