import polars as pl
from loguru import logger

from cloakdata import anonymize

df = pl.DataFrame(
    {
        "txt": [
            "foo",
            "bar",
            "baz",
            "foobar",
            "barfoo",
            "Hello",
            "heLLo",
            "id=123",
            "noid",
            None,
        ]
    }
).with_columns(
    [
        pl.col("txt").alias("literal_ba"),
        pl.col("txt").alias("multi_rules"),
        pl.col("txt").alias("case_insensitive"),
        pl.col("txt").alias("regex_digits"),
        pl.col("txt").alias("single_substr"),
    ]
)

config = {
    "columns": {
        "literal_ba": {
            "method": "replace_by_contains",
            "params": {"mapping": {"ba": "X"}},
        },
        "multi_rules": {
            "method": "replace_by_contains",
            "params": {"mapping": {"foo": "A", "bar": "B"}},
        },
        "case_insensitive": {
            "method": "replace_by_contains",
            "params": {
                "mapping": {"hello": "X"},
                "case_sensitive": False,
            },
        },
        "regex_digits": {
            "method": "replace_by_contains",
            "params": {
                "mapping": {r"\d{3}": "HIT"},
                "use_regex": True,
            },
        },
        "single_substr": {
            "method": "replace_by_contains",
            "params": {"substr": "noid", "replacement": "FOUND"},
        },
    }
}

out = anonymize(df, config)
logger.info(out)
