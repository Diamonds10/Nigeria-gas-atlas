"""
Process the raw GOGET field-level asset CSV into a cleaned, Nigeria-only output
with point geometry (lat/lng) ready for downstream geospatial use.

This script expects that the raw CSV has already been downloaded into
`data/raw/01_resource/` using the downloader script.
"""

import argparse
from pathlib import Path
import sys

import pandas as pd

RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "01_resource"
PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed" / "01_resource"
RAW_FILENAME = "goget_fields_all_countries_2023-08.csv"
OUTPUT_FILENAME = "goget_fields_nigeria_2023-08.csv"


def get_input_path(input_dir: Path) -> Path:
    path = input_dir / RAW_FILENAME
    if not path.exists():
        raise FileNotFoundError(
            f"Required raw file not found: {path}\n"
            "Run scripts/01_resource/05_download_goget_fields.py first."
        )
    return path


def process(input_path: Path, output_path: Path, country: str) -> None:
    df = pd.read_csv(input_path)
    df["country"] = df["country"].astype(str).str.strip()
    normalized = country.strip().lower()
    filtered = df[df["country"].str.lower() == normalized].reset_index(drop=True)
    if filtered.empty:
        raise ValueError(f"No rows found for country: {country}")

    filtered = filtered.dropna(subset=["lat", "lng"]).reset_index(drop=True)
    filtered = filtered.sort_values("project").reset_index(drop=True)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    filtered.to_csv(output_path, index=False)
    print(f"Saved processed CSV: {output_path} ({len(filtered)} rows)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert the downloaded GOGET field-level CSV to a cleaned, country-filtered CSV."
    )
    parser.add_argument("--raw-dir", type=Path, default=RAW_DATA_DIR)
    parser.add_argument("--processed-dir", type=Path, default=PROCESSED_DIR)
    parser.add_argument("--country", type=str, default="Nigeria")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    raw_dir = args.raw_dir.expanduser().resolve()
    processed_dir = args.processed_dir.expanduser().resolve()

    try:
        input_path = get_input_path(raw_dir)
        process(input_path, processed_dir / OUTPUT_FILENAME, args.country)
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
