"""
Process the raw EIA Nigeria crude oil production JSON into a cleaned CSV.

This script expects that the raw JSON has already been downloaded into
`data/raw/01_resource/` using the downloader script.
"""

import argparse
import json
from pathlib import Path
import sys

import pandas as pd

RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "01_resource"
PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed" / "01_resource"
RAW_FILENAME = "eia_nigeria_crude_oil_production_1973-present.json"
OUTPUT_FILENAME = "eia_nigeria_crude_oil_production_1973-present.csv"
KEEP_UNIT = "TBPD"  # thousand barrels per day


def get_input_path(input_dir: Path) -> Path:
    path = input_dir / RAW_FILENAME
    if not path.exists():
        raise FileNotFoundError(
            f"Required raw file not found: {path}\n"
            "Run scripts/01_resource/03_download_eia_petroleum.py first."
        )
    return path


def process(input_path: Path, output_path: Path) -> None:
    rows = json.loads(input_path.read_text())
    df = pd.DataFrame(rows)
    df = df[df["unit"] == KEEP_UNIT].copy()
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value"])
    df["year"] = df["period"].astype(int)
    df = df.rename(columns={"value": "crude_oil_production_kbbl_day"})
    df = df[["year", "crude_oil_production_kbbl_day"]].sort_values("year").reset_index(drop=True)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Saved processed CSV: {output_path} ({len(df)} rows)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert downloaded EIA JSON to a cleaned CSV of Nigeria crude oil production."
    )
    parser.add_argument("--raw-dir", type=Path, default=RAW_DATA_DIR)
    parser.add_argument("--processed-dir", type=Path, default=PROCESSED_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    raw_dir = args.raw_dir.expanduser().resolve()
    processed_dir = args.processed_dir.expanduser().resolve()

    try:
        input_path = get_input_path(raw_dir)
        process(input_path, processed_dir / OUTPUT_FILENAME)
    except (FileNotFoundError, OSError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
