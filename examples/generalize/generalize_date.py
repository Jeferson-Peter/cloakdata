import polars as pl
from loguru import logger

from cloakdata import anonymize

df = pl.DataFrame(
    {
        "dt": [
            "2024-05-17",
            "2024-12-01",
            "2023-01-10",
            None,
        ]
    }
)

df = df.with_columns(
    [
        pl.col("dt").alias("dt_year"),
        pl.col("dt").alias("dt_month"),
        pl.col("dt").alias("dt_quarter"),
        pl.col("dt").alias("dt_semester"),
        pl.col("dt").alias("dt_week"),
        pl.col("dt").alias("dt_date"),
    ]
)

config = {
    "columns": {
        # Year granularity: "2024-05-17" → "2024"
        "dt_year": {
            "method": "generalize_date",
            "params": {"mode": "year"},
        },
        # Month granularity (default): "2024-05-17" → "2024-05"
        "dt_month": {
            "method": "generalize_date",
            "params": {"mode": "month"},
        },
        # Quarter granularity: "2024-05-17" → "2024-Q2"
        "dt_quarter": {
            "method": "generalize_date",
            "params": {"mode": "quarter"},
        },
        # Semester granularity: "2024-05-17" → "2024-S1"
        "dt_semester": {
            "method": "generalize_date",
            "params": {"mode": "semester"},
        },
        # Week granularity (ISO-like): "2024-05-17" → "2024-W20"
        "dt_week": {
            "method": "generalize_date",
            "params": {"mode": "week"},
        },
        # Date only: "2024-05-17T10:30:00" → "2024-05-17"
        "dt_date": {
            "method": "generalize_date",
            "params": {"mode": "date"},
        },
    }
}

out = anonymize(df, config)
logger.info(out)
