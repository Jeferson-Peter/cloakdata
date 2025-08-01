import polars as pl
import json
import time
from datetime import timedelta
from loguru import logger
from pathlib import Path
from src.cloakdata.core import AnonymizationMethods
from src.cloakdata.validate import validate_config


def format_duration(ms: float) -> str:
    """
    Converts milliseconds into a human-readable duration (HH:MM:SS).

    Parameters:
        ms (float): Duration in milliseconds.

    Returns:
        str: Formatted duration string.
    """
    return str(timedelta(milliseconds=ms))


def read_dataframe(file_path: str) -> pl.DataFrame:
    """
    Reads a DataFrame from a file in supported formats.

    Supported formats: .csv, .json, .parquet, .xlsx

    Parameters:
        file_path (str): Path to the input file.

    Returns:
        pl.DataFrame: Loaded DataFrame.

    Raises:
        ValueError: If the file extension is not supported.
    """
    ext = Path(file_path).suffix.lower()
    match ext:
        case ".csv":
            return pl.read_csv(file_path)
        case ".json":
            return pl.read_json(file_path)
        case ".parquet":
            return pl.read_parquet(file_path)
        case ".xlsx":
            return pl.read_excel(file_path)
        case _:
            raise ValueError(f"❌ Unsupported input file format: {ext}")


def write_dataframe(df: pl.DataFrame, file_path: str) -> None:
    """
    Writes a DataFrame to the specified file format.

    Supported formats: .csv, .json, .parquet, .xlsx

    Parameters:
        df (pl.DataFrame): The DataFrame to save.
        file_path (str): Destination path for the output file.

    Raises:
        ValueError: If the file extension is not supported.
    """
    ext = Path(file_path).suffix.lower()
    match ext:
        case ".csv":
            df.write_csv(file_path)
        case ".json":
            df.write_json(file_path)
        case ".parquet":
            df.write_parquet(file_path)
        case ".xlsx":
            df.write_excel(file_path)
        case _:
            raise ValueError(f"❌ Unsupported output file format: {ext}")


def main():
    """
    Main execution logic:
    - Reads input DataFrame.
    - Loads anonymization config from JSON.
    - Applies anonymization.
    - Saves the result.
    - Logs processing time and output.
    """
    input_path = "input/sensitive_data.parquet"
    config_path = "config.json"
    output_path = "output/anonymized_data.parquet"

    logger.info(f"📥 Reading data from: {input_path}")
    df = read_dataframe(input_path)

    logger.info(f"⚙️  Loading anonymization config from: {config_path}")
    with open(config_path) as f:
        config = json.load(f)

    validate_config(config, AnonymizationMethods.build_dispatch_map())

    logger.info("🔐 Applying anonymization rules...")
    start_time = time.perf_counter()
    anonymized_df = AnonymizationMethods.anonymize(df, config)
    elapsed_ms = (time.perf_counter() - start_time) * 1000
    elapsed_str = format_duration(elapsed_ms)

    logger.info(f"💾 Saving anonymized data to: {output_path}")
    write_dataframe(anonymized_df, output_path)

    logger.success(f"✅ Anonymized data saved successfully.")
    logger.info(f"⏱️ Elapsed time: {elapsed_str}")


if __name__ == "__main__":
    main()
