import polars as pl
from loguru import logger

from cloakdata import anonymize

df = pl.DataFrame(
    {
        "cpf": [
            "12345678901",
            "123.456.789-01",
            None,
        ],
    }
)

config = {
    "columns": {
        "cpf": {
            "method": "mask_cpf",
            "params": {
                "keep_last": 2,
                "mask_char": "*",
            },
        },
    }
}

out = anonymize(df, config)
logger.info(out)
