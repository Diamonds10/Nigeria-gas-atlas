"""
Process the Global Energy Monitor GOGET country-level dashboard workbook into
cleaned, Nigeria-filtered CSV outputs.

This script expects that the raw workbook has already been downloaded into
`data/raw/01_resource/` using the downloader script.
"""

import argparse
from pathlib import Path
import sys

import pandas as pd

RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "01_resource"
PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed" / "01_resource"
RAW_FILENAME = "goget_dashboard_2026-03.xlsx"
HEADER_ROW = 3

# Sheets keyed by Country/Area with one row of metrics per country.
WIDE_SHEETS = [
    {
        "sheet": "Count of Gas Extraction Sites b",
        "output": "goget_gas_site_counts_by_status_2026-03.csv",
    },
    {
        "sheet": "Count of Oil Extraction Sites b",
        "output": "goget_oil_site_counts_by_status_2026-03.csv",
    },
    {
        "sheet": "All extraction sites by Country",
        "output": "goget_all_site_counts_by_status_2026-03.csv",
    },
    {
        "sheet": "Production by CountryArea",
        "output": "goget_production_2026-03.csv",
    },
]

# Sheets keyed by Country/Area with one column per year, melted into long format.
YEAR_SHEETS = [
    {
        "sheet": "Discoveries by Year and Country",
        "output": "goget_discoveries_by_year_2026-03.csv",
        "value_name": "discoveries_count",
    },
    {
        "sheet": "Yearly FIDs Approved by Country",
        "output": "goget_fids_by_year_2026-03.csv",
        "value_name": "fids_approved_count",
    },
]


def get_input_path(input_dir: Path) -> Path:
    path = input_dir / RAW_FILENAME
    if not path.exists():
        raise FileNotFoundError(
            f"Required raw file not found: {path}\n"
            "Run scripts/01_resource/01_download_goget.py first."
        )
    return path


def apply_country_filter(df: pd.DataFrame, country: str) -> pd.DataFrame:
    normalized = country.strip().lower()
    filtered = df[df["country"].str.strip().str.lower() == normalized].reset_index(drop=True)
    if filtered.empty:
        raise ValueError(f"No rows found for country: {country}")
    return filtered


def process_wide_sheet(input_path: Path, sheet_name: str, output_path: Path, country: str) -> None:
    print(f"Processing sheet '{sheet_name}'")
    df = pd.read_excel(input_path, sheet_name=sheet_name, header=HEADER_ROW, engine="openpyxl")
    first_col = df.columns[0]
    df = df.rename(columns={first_col: "country"})
    df["country"] = df["country"].astype(str).str.strip()
    df = apply_country_filter(df, country)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Saved processed CSV: {output_path}")


def process_year_sheet(
    input_path: Path, sheet_name: str, output_path: Path, value_name: str, country: str
) -> None:
    print(f"Processing sheet '{sheet_name}'")
    df = pd.read_excel(input_path, sheet_name=sheet_name, header=HEADER_ROW, engine="openpyxl")
    first_col = df.columns[0]
    df = df.rename(columns={first_col: "country"})
    df["country"] = df["country"].astype(str).str.strip()
    df = apply_country_filter(df, country)

    year_cols = [col for col in df.columns if col != "country"]
    melted = df.melt(id_vars=["country"], value_vars=year_cols, var_name="year", value_name=value_name)
    melted = melted.dropna(subset=[value_name])
    melted = melted[melted["year"].astype(str) != "Before 2016"]
    melted["year"] = melted["year"].astype(str).str.extract(r"(\d{4})")[0]
    melted = melted.dropna(subset=["year"])
    melted["year"] = melted["year"].astype(int)
    melted = melted.sort_values("year").reset_index(drop=True)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    melted.to_csv(output_path, index=False)
    print(f"Saved processed CSV: {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert the downloaded GOGET dashboard workbook to cleaned, Nigeria-filtered CSVs."
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=RAW_DATA_DIR,
        help="Directory containing the downloaded raw workbook.",
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=PROCESSED_DIR,
        help="Directory where processed CSV files will be saved.",
    )
    parser.add_argument(
        "--country",
        type=str,
        default="Nigeria",
        help="Country/area name to filter rows to (must match GOGET's Country/Area labels).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    raw_dir = args.raw_dir.expanduser().resolve()
    processed_dir = args.processed_dir.expanduser().resolve()

    try:
        input_path = get_input_path(raw_dir)

        for item in WIDE_SHEETS:
            process_wide_sheet(
                input_path, item["sheet"], processed_dir / item["output"], args.country
            )

        for item in YEAR_SHEETS:
            process_year_sheet(
                input_path,
                item["sheet"],
                processed_dir / item["output"],
                item["value_name"],
                args.country,
            )
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("\nProcessing complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
