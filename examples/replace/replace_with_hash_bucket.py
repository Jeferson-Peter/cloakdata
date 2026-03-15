import polars as pl
from loguru import logger

from cloakdata import anonymize

df = pl.DataFrame(
    {
        "customer_id": ["alice", "bob", "charlie", "alice", None],
    }
)

config = {
    "columns": {
        "customer_id": {
            "method": "replace_with_hash_bucket",
            "params": {
                "buckets": 8,
                "prefix": "group",
                "seed": 42,
            },
        },
    }
}

out = anonymize(df, config)
logger.info(out)
