"""
Process the raw Nigeria SE4ALL gas_fields WFS extract into a cleaned CSV with
WKT polygon geometry, and reconcile it against the existing GOGET field-level
inventory (goget_fields_nigeria_2023-08.csv) so downstream users know which
field-name polygons are genuinely new versus which upgrade an already-known
GOGET point to a real footprint.

This script expects that the raw JSON has already been downloaded into
`data/raw/01_resource/` using scripts/01_resource/09_download_se4all_gas_fields.py,
and that goget_fields_nigeria_2023-08.csv already exists in the processed dir
(built by scripts/01_resource/06_process_goget_fields.py).
"""

import argparse
from pathlib import Path
import sys

import geopandas as gpd
import pandas as pd

RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "01_resource"
PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed" / "01_resource"
RAW_FILENAME = "se4all_gas_fields_nigeria.json"
GOGET_FIELDS_FILENAME = "goget_fields_nigeria_2023-08.csv"
OUTPUT_FILENAME = "se4all_gas_fields_nigeria_2026-07.csv"


def get_input_path(input_dir: Path, filename: str, download_script: str) -> Path:
    path = input_dir / filename
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}\nRun {download_script} first.")
    return path


def load_goget_names(goget_path: Path) -> set:
    df = pd.read_csv(goget_path)
    return set(df["project"].astype(str).str.strip().str.lower())


def process(raw_path: Path, goget_path: Path, output_path: Path) -> None:
    gdf = gpd.read_file(raw_path)
    gdf = gdf.rename(columns={"field_tpye": "field_type"})
    gdf["name"] = gdf["name"].astype(str).str.strip()
    gdf["field_type"] = gdf["field_type"].fillna("Unspecified")

    goget_names = load_goget_names(goget_path)
    gdf["name_key"] = gdf["name"].str.lower()
    gdf["in_goget_fields"] = gdf["name_key"].isin(goget_names)

    gdf["geometry"] = gdf["geometry"].apply(lambda geom: geom.wkt if geom is not None else None)
    gdf = gdf.drop(columns=["fid", "objectid", "shape_leng", "shape_area", "name_key"], errors="ignore")
    gdf = gdf.sort_values(["name", "field_type"]).reset_index(drop=True)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_csv(output_path, index=False)

    n_new = (~gdf["in_goget_fields"]).sum()
    n_matched = gdf["in_goget_fields"].sum()
    n_unique_names = gdf["name"].nunique()
    print(
        f"Saved processed CSV: {output_path} ({len(gdf)} polygon rows, "
        f"{n_unique_names} unique field names: {n_matched} rows already in GOGET, "
        f"{n_new} rows for field names not present in GOGET)"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert the downloaded SE4ALL gas_fields JSON to a cleaned CSV with WKT geometry, "
        "flagged against the existing GOGET field inventory."
    )
    parser.add_argument("--raw-dir", type=Path, default=RAW_DATA_DIR)
    parser.add_argument("--processed-dir", type=Path, default=PROCESSED_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    raw_dir = args.raw_dir.expanduser().resolve()
    processed_dir = args.processed_dir.expanduser().resolve()

    try:
        raw_path = get_input_path(raw_dir, RAW_FILENAME, "scripts/01_resource/09_download_se4all_gas_fields.py")
        goget_path = get_input_path(
            processed_dir, GOGET_FIELDS_FILENAME, "scripts/01_resource/06_process_goget_fields.py"
        )
        process(raw_path, goget_path, processed_dir / OUTPUT_FILENAME)
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
