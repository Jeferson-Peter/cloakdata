import polars as pl
from loguru import logger

from cloakdata import anonymize

df = pl.DataFrame(
    {
        "event_time": [
            "2024-05-01T07:45:00",
            "2024-05-01T10:20:00",
            "2024-05-01T19:10:00",
            "2024-05-04T10:15:00",
            "2024-05-05T21:30:00",
            None,
        ],
    }
).with_columns(
    [
        pl.col("event_time").alias("event_time_bucket"),
        pl.col("event_time").alias("event_time_minute_of_day_bucket"),
        pl.col("event_time").alias("event_time_minute_of_day_bucket_datetime"),
        pl.col("event_time").alias("event_time_hour"),
        pl.col("event_time").alias("event_time_part_of_day"),
        pl.col("event_time").alias("event_time_weekday"),
        pl.col("event_time").alias("event_time_weekend_weekday"),
        pl.col("event_time").alias("event_time_business_hours"),
        pl.col("event_time").alias("event_time_business_hours_with_weekends"),
    ]
)

config = {
    "columns": {
        "event_time_bucket": {
            "method": "coarsen_datetime",
            "params": {
                "mode": "bucket",
                "minutes": 15,
            },
        },
        "event_time_minute_of_day_bucket": {
            "method": "coarsen_datetime",
            "params": {
                "mode": "minute_of_day_bucket",
                "minutes": 30,
            },
        },
        "event_time_minute_of_day_bucket_datetime": {
            "method": "coarsen_datetime",
            "params": {
                "mode": "minute_of_day_bucket",
                "minutes": 30,
                "output": "datetime",
            },
        },
        "event_time_hour": {
            "method": "coarsen_datetime",
            "params": {
                "mode": "hour",
            },
        },
        "event_time_part_of_day": {
            "method": "coarsen_datetime",
            "params": {
                "mode": "part_of_day",
            },
        },
        "event_time_weekday": {
            "method": "coarsen_datetime",
            "params": {
                "mode": "weekday",
            },
        },
        "event_time_weekend_weekday": {
            "method": "coarsen_datetime",
            "params": {
                "mode": "weekend_weekday",
            },
        },
        "event_time_business_hours": {
            "method": "coarsen_datetime",
            "params": {
                "mode": "business_hours",
                "start_hour": 8,
                "end_hour": 18,
                "include_weekends": False,
            },
        },
        "event_time_business_hours_with_weekends": {
            "method": "coarsen_datetime",
            "params": {
                "mode": "business_hours",
                "start_hour": 8,
                "end_hour": 18,
                "include_weekends": True,
            },
        },
    }
}

out = anonymize(df, config)
logger.info(out)
