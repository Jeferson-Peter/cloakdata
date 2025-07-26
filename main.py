
import polars as pl
import json
from anonymizer import anonymize

def main():
    input_path = "input/sensitive_data.csv"
    config_path = "config.json"
    output_path = "output/anonymized_data.csv"

    df = pl.read_csv(input_path)
    with open(config_path) as f:
        config = json.load(f)

    anonymized_df = anonymize(df, config)
    anonymized_df.write_csv(output_path)
    print("✅ Anonymized data saved to:", output_path)

if __name__ == "__main__":
    main()
