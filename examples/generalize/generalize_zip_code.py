import polars as pl
from loguru import logger

from cloakdata import anonymize

df = pl.DataFrame(
    {
        "zip_code": ["81320-000", "10001", "12345-6789", "SW1A 1AA", None],
    }
)

config = {
    "columns": {
        "zip_code": {
            "method": "generalize_zip_code",
            "params": {
                "visible_prefix": 3,
                "mask_char": "*",
            },
        },
    }
}

out = anonymize(df, config)
logger.info(out)
