"""
Process the raw GGIT asset CSV into cleaned, Nigeria-filtered outputs, split by
asset type (gas pipelines vs LNG terminals).

This script expects that the raw CSV has already been downloaded into
`data/raw/02_infrastructure/` using the downloader script.
"""

import argparse
from pathlib import Path
import sys

import pandas as pd

RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "02_infrastructure"
PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed" / "02_infrastructure"
RAW_FILENAME = "ggit_gas_pipelines_lng_terminals_all_countries.csv"

OUTPUTS = [
    {"types": ["gas_pipelines"], "output": "ggit_gas_pipelines_nigeria.csv"},
    {
        "types": ["lng_terminals__export", "lng_terminals__import"],
        "output": "ggit_lng_terminals_nigeria.csv",
    },
]


def get_input_path(input_dir: Path) -> Path:
    path = input_dir / RAW_FILENAME
    if not path.exists():
        raise FileNotFoundError(
            f"Required raw file not found: {path}\n"
            "Run scripts/02_infrastructure/01_download_gas_infrastructure.py first."
        )
    return path


def filter_country(df: pd.DataFrame, country: str) -> pd.DataFrame:
    mask = df["countries"].astype(str).str.contains(country, case=False, na=False)
    return df[mask].reset_index(drop=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert the downloaded GGIT CSV to cleaned, Nigeria-filtered CSVs by asset type."
    )
    parser.add_argument("--raw-dir", type=Path, default=RAW_DATA_DIR)
    parser.add_argument("--processed-dir", type=Path, default=PROCESSED_DIR)
    parser.add_argument("--country", type=str, default="Nigeria")
    args = parser.parse_args()

    raw_dir = args.raw_dir.expanduser().resolve()
    processed_dir = args.processed_dir.expanduser().resolve()

    try:
        input_path = get_input_path(raw_dir)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    df = pd.read_csv(input_path)
    country_df = filter_country(df, args.country)

    for item in OUTPUTS:
        subset = country_df[country_df["type"].isin(item["types"])].reset_index(drop=True)
        output_path = processed_dir / item["output"]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        subset.to_csv(output_path, index=False)
        print(f"Saved processed CSV: {output_path} ({len(subset)} rows)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
