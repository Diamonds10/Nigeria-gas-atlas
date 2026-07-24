"""
Process the raw Nigeria SE4ALL gas_infrastructure WFS extract into a cleaned
CSV of point assets (compressor stations, gas plants, FPSOs, LNG plants,
terminals, refineries, etc.), flagging the handful of records that duplicate
facilities already tracked elsewhere in this layer (GGIT LNG terminals,
refineries) so they aren't double-counted on the map.

This script expects that the raw JSON has already been downloaded into
`data/raw/02_infrastructure/` using
scripts/02_infrastructure/07_download_se4all_gas_infrastructure.py.

The source has no stable ID field for cross-referencing facility identity, so
duplicates below were identified manually by name/location inspection rather
than fuzzy matching, and are necessarily a judgement call, not a formal join.
"""

import argparse
from pathlib import Path
import sys

import geopandas as gpd

RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "02_infrastructure"
PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed" / "02_infrastructure"
RAW_FILENAME = "se4all_gas_infrastructure_nigeria.json"
OUTPUT_FILENAME = "se4all_gas_infrastructure_nigeria_2026-07.csv"

# SE4ALL name -> matching project name already present in this layer's
# refineries_nigeria.csv or ggit_lng_terminals_nigeria.csv, identified by manual
# inspection (name + facility type + rough location).
KNOWN_DUPLICATES = {
    "kaduna refinery": "Kaduna Refining and Petrochemical Company (refineries_nigeria.csv)",
    "port-harcourt refinery": "Port Harcourt Refining Company (old + new plants) (refineries_nigeria.csv)",
    "warri refinery": "Warri Refining and Petrochemical Company (refineries_nigeria.csv)",
    "bonny nlng": "Nigeria LNG Terminal (ggit_lng_terminals_nigeria.csv)",
    "bonny lng plant": "Nigeria LNG Terminal (ggit_lng_terminals_nigeria.csv)",
    "brass lng": "Brass LNG Terminal (ggit_lng_terminals_nigeria.csv)",
    "ok lng": "Olokola LNG Terminal (ggit_lng_terminals_nigeria.csv)",
}

KEEP_COLUMNS = [
    "name", "type", "status", "company", "location", "design_cap", "operating",
    "date_of_co", "possible_duplicate_of", "geometry",
]


def get_input_path(input_dir: Path) -> Path:
    path = input_dir / RAW_FILENAME
    if not path.exists():
        raise FileNotFoundError(
            f"Required raw file not found: {path}\n"
            "Run scripts/02_infrastructure/07_download_se4all_gas_infrastructure.py first."
        )
    return path


def process(raw_path: Path, output_path: Path) -> None:
    gdf = gpd.read_file(raw_path)

    n_total = len(gdf)
    gdf["name"] = gdf["name"].astype(str).str.strip()
    gdf = gdf[~gdf["name"].isin(["", "None", "nan"])].reset_index(drop=True)
    n_dropped_noname = n_total - len(gdf)

    gdf["possible_duplicate_of"] = gdf["name"].str.lower().map(KNOWN_DUPLICATES)

    gdf["geometry"] = gdf["geometry"].apply(lambda geom: geom.wkt if geom is not None else None)
    available_columns = [col for col in KEEP_COLUMNS if col in gdf.columns]
    gdf = gdf[available_columns]
    gdf = gdf.sort_values(["type", "name"]).reset_index(drop=True)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_csv(output_path, index=False)

    n_dupes = gdf["possible_duplicate_of"].notna().sum()
    print(
        f"Saved processed CSV: {output_path} ({len(gdf)} rows; dropped {n_dropped_noname} "
        f"unnamed records; {n_dupes} rows flagged as likely duplicates of existing "
        f"refinery/LNG terminal records)"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert the downloaded SE4ALL gas_infrastructure JSON to a cleaned CSV, "
        "flagged for likely duplicates against existing refinery/LNG terminal records."
    )
    parser.add_argument("--raw-dir", type=Path, default=RAW_DATA_DIR)
    parser.add_argument("--processed-dir", type=Path, default=PROCESSED_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    raw_dir = args.raw_dir.expanduser().resolve()
    processed_dir = args.processed_dir.expanduser().resolve()

    try:
        raw_path = get_input_path(raw_dir)
        process(raw_path, processed_dir / OUTPUT_FILENAME)
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
