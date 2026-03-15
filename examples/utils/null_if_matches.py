import polars as pl
from loguru import logger

from cloakdata import anonymize

df = pl.DataFrame(
    {
        "status": ["N/A", "unknown", "active", "", None],
        "document": ["12345678901", "ABC123", None, "98765432100", "ok"],
    }
)

config = {
    "columns": {
        "status": {
            "method": "null_if_matches",
            "params": {
                "values": ["N/A", "unknown", ""],
                "case_sensitive": False,
            },
        },
        "document": {
            "method": "null_if_matches",
            "params": {
                "pattern": r"^\d{11}$",
            },
        },
    }
}

out = anonymize(df, config)
logger.info(out)
