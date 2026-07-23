"""
Process the raw GOGPT asset CSV into a cleaned, Nigeria-filtered output.

This script expects that the raw CSV has already been downloaded into
`data/raw/02_infrastructure/` using the downloader script.
"""

import argparse
from pathlib import Path
import sys

import pandas as pd

RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "02_infrastructure"
PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed" / "02_infrastructure"
RAW_FILENAME = "gogpt_oil_gas_plants_all_countries.csv"
OUTPUT_FILENAME = "gogpt_oil_gas_plants_nigeria.csv"


def get_input_path(input_dir: Path) -> Path:
    path = input_dir / RAW_FILENAME
    if not path.exists():
        raise FileNotFoundError(
            f"Required raw file not found: {path}\n"
            "Run scripts/02_infrastructure/05_download_gas_plants.py first."
        )
    return path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert the downloaded GOGPT CSV to a cleaned, Nigeria-filtered CSV."
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
    df["country"] = df["country"].astype(str).str.strip()
    normalized = args.country.strip().lower()
    filtered = df[df["country"].str.lower() == normalized].reset_index(drop=True)

    output_path = processed_dir / OUTPUT_FILENAME
    output_path.parent.mkdir(parents=True, exist_ok=True)
    filtered.to_csv(output_path, index=False)
    print(f"Saved processed CSV: {output_path} ({len(filtered)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
