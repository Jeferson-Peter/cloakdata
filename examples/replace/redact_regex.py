import polars as pl
from loguru import logger

from cloakdata import anonymize

df = pl.DataFrame(
    {
        "notes": [
            "Contact alice@example.com for details",
            "CPF 12345678901 created the ticket",
            None,
        ],
    }
).with_columns(
    [
        pl.col("notes").alias("notes_email_redacted"),
        pl.col("notes").alias("notes_doc_redacted"),
    ]
)

config = {
    "columns": {
        "notes_email_redacted": {
            "method": "redact_regex",
            "params": {
                "pattern": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
                "replacement": "[EMAIL]",
            },
        },
        "notes_doc_redacted": {
            "method": "redact_regex",
            "params": {
                "pattern": r"\d{11}",
                "replacement": "[DOC]",
            },
        },
    }
}

out = anonymize(df, config)
logger.info(out)
