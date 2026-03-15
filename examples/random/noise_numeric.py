import polars as pl
from loguru import logger

from cloakdata import anonymize

df = pl.DataFrame(
    {
        "salary": [3500.0, 4200.0, None, 5100.0],
    }
)

config = {
    "columns": {
        "salary": {
            "method": "noise_numeric",
            "params": {
                "min_delta": -150.0,
                "max_delta": 150.0,
                "seed": 42,
            },
        },
    }
}

out = anonymize(df, config)
logger.info(out)
