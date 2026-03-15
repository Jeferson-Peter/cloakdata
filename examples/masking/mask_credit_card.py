import polars as pl
from loguru import logger

from cloakdata import anonymize

df = pl.DataFrame(
    {
        "card": [
            "4111111111111111",
            "5555-4444-3333-2222",
            "4111 1111 1111 1111",
            None,
        ],
    }
)

config = {
    "columns": {
        "card": {
            "method": "mask_credit_card",
            "params": {
                "keep_last": 4,
                "mask_char": "*",
            },
        },
    }
}

out = anonymize(df, config)
logger.info(out)
