import polars as pl
from loguru import logger

from cloakdata import anonymize

df = pl.DataFrame({"col": ["a", None, "b", "c"]}).with_columns(
    [
        pl.col("col").alias("str_fill"),
        pl.col("col").alias("str_keep_nulls"),
        pl.col("col").alias("int_fill"),
        pl.col("col").alias("bool_keep_nulls"),
    ]
)

config = {
    "columns": {
        "str_fill": {"method": "replace_with_value", "params": {"value": "X"}},
        "str_keep_nulls": {
            "method": "replace_with_value",
            "params": {"value": "LABEL", "preserve_nulls": True},
        },
        "int_fill": {"method": "replace_with_value", "params": {"value": 123}},
        "bool_keep_nulls": {
            "method": "replace_with_value",
            "params": {"value": False, "preserve_nulls": True},
        },
    }
}

out = anonymize(df, config)
logger.info(out)
