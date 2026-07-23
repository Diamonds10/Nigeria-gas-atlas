"""
Process World Bank GGFR flaring Excel files into cleaned CSV outputs.

This script expects that the raw World Bank Excel files have already been downloaded
into `data/raw/03_environmental/` using the downloader script.
"""

import argparse
from pathlib import Path
import sys

import pandas as pd

RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "03_environmental"
PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed" / "03_environmental"

INPUTS = [
    {
        "filename": "ggfr_flare_volume_and_intensity_estimates_2012-2025.xlsx",
        "sheet": "Flare volume",
        "output": "ggfr_flare_volume_2012-2025.csv",
        "value_name": "flare_volume_bcm",
    },
    {
        "filename": "ggfr_flare_volume_and_intensity_estimates_2012-2025.xlsx",
        "sheet": "Flaring intensity",
        "output": "ggfr_flaring_intensity_2012-2025.csv",
        "value_name": "flare_intensity_m3_per_bbl",
    },
    {
        "filename": "ggfr_flare_volume_and_intensity_estimates_2012-2025.xlsx",
        "sheet": "Oil production",
        "output": "ggfr_oil_production_2012-2025.csv",
        "value_name": "oil_production_kbbl_day",
    },
]


def get_input_path(filename: str, input_dir: Path) -> Path:
    path = input_dir / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Required raw file not found: {path}\n"
            "Run scripts/03_environmental/01_download_ggfr_flaring.py first."
        )
    return path


def clean_sheet(df: pd.DataFrame, value_name: str) -> pd.DataFrame:
    df = df.copy()
    if df.columns.size < 2:
        raise ValueError("Expected at least two columns: country plus year values.")

    first_col = df.columns[0]
    df = df.rename(columns={first_col: "country"})
    df["country"] = df["country"].astype(str).str.strip()

    year_cols = [col for col in df.columns if col != "country"]
    melted = df.melt(
        id_vars=["country"],
        value_vars=year_cols,
        var_name="year",
        value_name=value_name,
    )
    melted = melted.dropna(subset=[value_name])
    melted["year"] = melted["year"].astype(str).str.extract(r"(\d{4})")[0]
    melted = melted.dropna(subset=["year"])
    melted["year"] = melted["year"].astype(int)
    melted = melted.reset_index(drop=True)
    return melted[["country", "year", value_name]]


def apply_country_filter(df: pd.DataFrame, country: str) -> pd.DataFrame:
    normalized = country.strip().lower()
    filtered = df[df["country"].str.strip().str.lower() == normalized].reset_index(drop=True)
    if filtered.empty:
        raise ValueError(f"No rows found for country: {country}")
    return filtered


def apply_country_exclusion(df: pd.DataFrame, country: str) -> pd.DataFrame:
    normalized = country.strip().lower()
    excluded = df[df["country"].str.strip().str.lower() != normalized].reset_index(drop=True)
    if excluded.empty:
        raise ValueError(f"No rows remain after excluding country: {country}")
    return excluded


def build_filtered_path(output_path: Path, country: str | None, exclude_country: str | None) -> Path:
    if country:
        suffix = f"_{country.strip().lower().replace(' ', '_')}"
    elif exclude_country:
        suffix = f"_no_{exclude_country.strip().lower().replace(' ', '_')}"
    else:
        return output_path
    return output_path.with_name(f"{output_path.stem}{suffix}{output_path.suffix}")


def process_sheet(
    input_path: Path,
    sheet_name: str,
    output_path: Path,
    value_name: str,
    country: str | None = None,
    exclude_country: str | None = None,
) -> None:
    print(f"Processing sheet '{sheet_name}' from {input_path.name}")
    df = pd.read_excel(input_path, sheet_name=sheet_name, engine="openpyxl")
    processed = clean_sheet(df, value_name=value_name)
    if country is not None:
        processed = apply_country_filter(processed, country)
    elif exclude_country is not None:
        processed = apply_country_exclusion(processed, exclude_country)
    output_path = build_filtered_path(output_path, country, exclude_country)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    processed.to_csv(output_path, index=False)
    print(f"Saved processed CSV: {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert downloaded GGFR Excel files to cleaned CSV outputs."
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=RAW_DATA_DIR,
        help="Directory containing downloaded raw Excel files.",
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=PROCESSED_DIR,
        help="Directory where processed CSV files will be saved.",
    )
    parser.add_argument(
        "--sheet",
        choices=[item["sheet"] for item in INPUTS],
        help="Only process a single sheet.",
    )
    parser.add_argument(
        "--country",
        type=str,
        help="Keep only rows for this country.",
    )
    parser.add_argument(
        "--exclude-country",
        type=str,
        help="Exclude rows for this country.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    raw_dir = args.raw_dir.expanduser().resolve()
    processed_dir = args.processed_dir.expanduser().resolve()

    selected = [item for item in INPUTS if args.sheet is None or item["sheet"] == args.sheet]
    if not selected:
        print("No sheets to process.", file=sys.stderr)
        return 1

    for item in selected:
        try:
            input_path = get_input_path(item["filename"], raw_dir)
            output_path = processed_dir / item["output"]
            process_sheet(
                input_path,
                item["sheet"],
                output_path,
                item["value_name"],
                country=args.country,
                exclude_country=args.exclude_country,
            )
        except (FileNotFoundError, ValueError, OSError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    print("\nProcessing complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
