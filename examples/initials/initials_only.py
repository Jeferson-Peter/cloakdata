import polars as pl
from loguru import logger

from cloakdata import anonymize

df = pl.DataFrame(
    {
        "name": [
            "John Doe",
            " Ana   Clara Silva ",
            None,
            "   ",
            "Madonna",
        ]
    }
).with_columns(
    [
        pl.col("name").alias("initials_default"),
        pl.col("name").alias("initials_no_preserve_nulls"),
    ]
)

config = {
    "columns": {
        # default → null preserved
        "initials_default": {
            "method": "initials_only",
        },
        # preserve_nulls = False → null becomes ""
        "initials_no_preserve_nulls": {
            "method": "initials_only",
            "params": {"preserve_nulls": False},
        },
    }
}

out = anonymize(df, config)
logger.info(out)
