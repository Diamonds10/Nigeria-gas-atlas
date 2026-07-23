"""
Extract Nigeria's crude oil and natural gas proven reserves from the downloaded
OPEC Annual Statistical Bulletin (ASB) PDFs and stitch them into one continuous
annual time series.

This script expects that the raw PDFs have already been downloaded into
`data/raw/01_resource/` using the downloader script.
"""

import argparse
from pathlib import Path
import re
import sys

import pandas as pd
import pdfplumber

RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "01_resource"
PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed" / "01_resource"
EDITIONS = [2012, 2015, 2020, 2025]
OUTPUT_FILENAME = "opec_nigeria_oil_gas_reserves_2007-2024.csv"

OIL_TABLE_KEYWORD = "world proven crude oil reserves by country"
GAS_TABLE_KEYWORD = "world proven natural gas reserves by country"
YEAR_RE = re.compile(r"\b((?:19|20)\d{2})\b")
NUMBER_RE = re.compile(r"-?[\d,]+\.?\d*")


def extract_nigeria_row(pdf_path: Path, table_keyword: str) -> list[tuple[str, float]] | None:
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            if table_keyword not in text.lower():
                continue

            years: list[str] | None = None
            values: list[str] | None = None
            for line in text.split("\n"):
                if years is None and len(YEAR_RE.findall(line)) >= 5:
                    years = YEAR_RE.findall(line)[:5]
                if line.strip().lower().startswith("nigeria"):
                    nums = NUMBER_RE.findall(line[len("nigeria"):])
                    cleaned = [n.replace(",", "") for n in nums if n.strip() not in ("", "-")]
                    values = cleaned[:5]

            if years and values and len(years) == len(values):
                return list(zip(years, (float(v) for v in values)))
    return None


def get_input_path(input_dir: Path, year: int) -> Path:
    path = input_dir / f"opec_asb_{year}.pdf"
    if not path.exists():
        raise FileNotFoundError(
            f"Required raw file not found: {path}\n"
            "Run scripts/01_resource/07_download_opec_asb.py first."
        )
    return path


def build_series(raw_dir: Path) -> pd.DataFrame:
    oil_by_year: dict[str, float] = {}
    gas_by_year: dict[str, float] = {}

    for year in EDITIONS:
        input_path = get_input_path(raw_dir, year)
        oil_rows = extract_nigeria_row(input_path, OIL_TABLE_KEYWORD)
        gas_rows = extract_nigeria_row(input_path, GAS_TABLE_KEYWORD)
        if not oil_rows or not gas_rows:
            raise ValueError(f"Could not locate Nigeria reserves rows in {input_path.name}")
        oil_by_year.update(dict(oil_rows))
        gas_by_year.update(dict(gas_rows))

    years = sorted(set(oil_by_year) | set(gas_by_year))
    rows = [
        {
            "year": int(year),
            "oil_reserves_mb": oil_by_year.get(year),
            "gas_reserves_bn_scm": gas_by_year.get(year),
        }
        for year in years
    ]
    return pd.DataFrame(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract and stitch Nigeria oil/gas reserves from OPEC ASB PDFs."
    )
    parser.add_argument("--raw-dir", type=Path, default=RAW_DATA_DIR)
    parser.add_argument("--processed-dir", type=Path, default=PROCESSED_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    raw_dir = args.raw_dir.expanduser().resolve()
    processed_dir = args.processed_dir.expanduser().resolve()

    try:
        df = build_series(raw_dir)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    output_path = processed_dir / OUTPUT_FILENAME
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Saved processed CSV: {output_path} ({len(df)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
