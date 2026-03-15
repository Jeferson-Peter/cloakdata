import polars as pl
from loguru import logger

from cloakdata import anonymize

df = pl.DataFrame(
    {
        "age": [12.0, 18.0, 42.0, 97.0, None],
    }
)

config = {
    "columns": {
        "age": {
            "method": "clip_range",
            "params": {
                "min": 18,
                "max": 90,
            },
        },
    }
}

out = anonymize(df, config)
logger.info(out)
