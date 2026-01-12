import polars as pl
from loguru import logger

from cloakdata import anonymize

df = pl.DataFrame(
    {
        "city": ["Curitiba", "Joinville", "São Paulo", "Curitiba", None, "Florianópolis"],
    }
)

df = df.with_columns(
    [
        pl.col("city").alias("choice_default"),
        pl.col("city").alias("choice_seed_42"),
        pl.col("city").alias("choice_custom_choices"),
        pl.col("city").alias("choice_noisy_many_choices"),
    ]
)

config = {
    "columns": {
        # Default behavior: choices=["X","Y"] and seed=0 (deterministic)
        "choice_default": {"method": "random_choice"},
        # Deterministic with an explicit seed
        "choice_seed_42": {"method": "random_choice", "params": {"seed": 42}},
        # Custom replacement set
        "choice_custom_choices": {
            "method": "random_choice",
            "params": {"choices": ["A", "B", "C"], "seed": 7},
        },
        # Another custom set (larger), still deterministic via seed
        "choice_noisy_many_choices": {
            "method": "random_choice",
            "params": {"choices": ["tok_1", "tok_2", "tok_3", "tok_4", "tok_5"], "seed": 123},
        },
    }
}

out = anonymize(df, config)
logger.info(out)
