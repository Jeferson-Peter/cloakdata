import polars as pl
from loguru import logger

from cloakdata import anonymize

# Original dataset
df = pl.DataFrame(
    {
        "cpf": [
            "12345678901",
            "98765432100",
            None,
            "11122233344",
        ]
    }
)

# Duplicate column to demonstrate different configurations
df = df.with_columns(
    [
        pl.col("cpf").alias("cpf_default"),
        pl.col("cpf").alias("cpf_8_digits"),
        pl.col("cpf").alias("cpf_deterministic"),
    ]
)

config = {
    "columns": {
        # Default: 11 random digits
        "cpf_default": {
            "method": "replace_with_random_digits",
        },
        # Custom length: 8 digits
        "cpf_8_digits": {
            "method": "replace_with_random_digits",
            "params": {"digits": 8},
        },
        # Deterministic output using a fixed seed
        "cpf_deterministic": {
            "method": "replace_with_random_digits",
            "params": {"digits": 11, "seed": 42},
        },
    }
}

out = anonymize(df, config)
logger.info(out)
