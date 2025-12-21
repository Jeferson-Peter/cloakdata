import polars as pl
from loguru import logger

from cloakdata import anonymize

# Original dataset
df = pl.DataFrame(
    {
        "city": [
            "Curitiba",
            "Joinville",
            "São Paulo",
            None,
            "Florianópolis",
        ]
    }
)

# Duplicate column to demonstrate different configurations
df = df.with_columns(
    [
        pl.col("city").alias("city_shuffle_default"),
        pl.col("city").alias("city_shuffle_seeded"),
    ]
)

config = {
    "columns": {
        # Random shuffle (non-deterministic)
        "city_shuffle_default": {
            "method": "shuffle",
        },
        # Deterministic shuffle using a fixed seed
        "city_shuffle_seeded": {
            "method": "shuffle",
            "params": {"seed": 42},
        },
    }
}

out = anonymize(df, config)
logger.info(out)
