import polars as pl
from loguru import logger

from cloakdata import anonymize

df = pl.DataFrame(
    {
        "city": ["Curitiba", "Joinville", "São Paulo"],
        "status": ["ok", "fail", None],
        "code": [1, 2, 3],
        "flag": [True, False, None],
    }
).with_columns(
    [
        pl.col("city").alias("city_mapped"),
        pl.col("status").alias("status_mapped"),
        pl.col("code").alias("code_mapped"),
        pl.col("flag").alias("flag_mapped"),
        pl.col("city").alias("no_mapping"),
    ]
)

config = {
    "columns": {
        "city_mapped": {
            "method": "replace_exact",
            "params": {"mapping": {"Curitiba": "CWB"}},
        },
        "status_mapped": {
            "method": "replace_exact",
            "params": {"mapping": {"ok": "OK", "fail": "FAIL"}},
        },
        "code_mapped": {
            "method": "replace_exact",
            "params": {"mapping": {1: 99, 3: -1}},
        },
        "flag_mapped": {
            "method": "replace_exact",
            "params": {"mapping": {True: False, False: True}},
        },
        "no_mapping": {
            "method": "replace_exact",
            "params": {"mapping": {}},
        },
    }
}

out = anonymize(df, config)
logger.info(out)
