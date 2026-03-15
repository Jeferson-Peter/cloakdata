from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from cloakdata import anonymize


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    input_path = base_dir / "sample.parquet"
    config_path = base_dir / "config.json"
    output_path = base_dir / "sample_anonymized.parquet"

    df = pl.read_parquet(input_path)
    config = json.loads(config_path.read_text(encoding="utf-8"))

    out = anonymize(df, config)
    out.write_parquet(output_path)

    print(f"Input: {input_path}")
    print(f"Config: {config_path}")
    print(f"Output: {output_path}")
    print(out)


if __name__ == "__main__":
    main()
