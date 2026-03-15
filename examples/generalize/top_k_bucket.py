import polars as pl
from loguru import logger

from cloakdata import anonymize

df = pl.DataFrame(
    {
        "city": ["SP", "SP", "RJ", "RJ", "MG", "BA", None],
    }
)

config = {
    "columns": {
        "city": {
            "method": "top_k_bucket",
            "params": {
                "k": 2,
                "other_label": "OTHER",
            },
        },
    }
}

out = anonymize(df, config)
logger.info(out)
