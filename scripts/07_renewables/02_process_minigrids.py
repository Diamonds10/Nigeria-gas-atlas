"""
Process the raw Nigeria SE4ALL mini-grids GeoJSON into a cleaned CSV matching the
schema proposed in docs/renewable_offgrid_minigrid_asset_layer_spec.md.

This script expects that the raw GeoJSON has already been downloaded into
`data/raw/07_renewables/` using the downloader script. The source dataset has no
`state` field (only LGA/community), so state is derived here via a point-in-polygon
spatial join against geoBoundaries' Nigeria ADM1 boundaries, fetched at run time.
"""

import argparse
import json
from datetime import date
from pathlib import Path
import sys

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import shape

RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "07_renewables"
PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed" / "07_renewables"
RAW_FILENAME = "se4all_minigrids_nigeria.json"
OUTPUT_FILENAME = "renewable_offgrid_minigrid_nigeria.csv"

STATES_BOUNDARY_URL = (
    "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/"
    "NGA/ADM1/geoBoundaries-NGA-ADM1_simplified.geojson"
)

SOURCE_NAME = "Nigeria SE4ALL Open Data Portal"
SOURCE_URL = "https://data.nigeriase4all.gov.ng/catalogue/#/dataset/1"

TECH_MAP = {
    "solar": "solar",
    "solar hybrid": "hybrid_mini_grid",
    "biogas": "other",
}


def get_input_path(input_dir: Path) -> Path:
    path = input_dir / RAW_FILENAME
    if not path.exists():
        raise FileNotFoundError(
            f"Required raw file not found: {path}\n"
            "Run scripts/07_renewables/01_download_minigrids.py first."
        )
    return path


def fetch_states_boundary() -> gpd.GeoDataFrame:
    response = requests.get(STATES_BOUNDARY_URL, timeout=60)
    response.raise_for_status()
    return gpd.GeoDataFrame.from_features(response.json()["features"], crs="EPSG:4326")


def normalize_status(row) -> str:
    status = str(row.get("status") or "").strip().lower()
    condition = str(row.get("condition") or "").strip().lower()
    if "construction" in status:
        return "under_construction"
    if "existing" in status and "operational" in condition and "non" not in condition:
        return "operational"
    if "existing" in status:
        return "commissioned"
    return "unknown"


def process(input_path: Path, output_path: Path) -> None:
    raw = json.loads(input_path.read_text())
    sites = gpd.GeoDataFrame.from_features(raw["features"], crs="EPSG:4326")

    states = fetch_states_boundary()
    joined = gpd.sjoin(sites, states[["shapeName", "geometry"]], how="left", predicate="within")

    today = date.today().isoformat()
    rows = []
    for i, row in joined.iterrows():
        power_system = str(row.get("power_system") or "").strip()
        rows.append({
            "asset_id": f"se4all-mg-{row.get('cluster_offgrid_id', i)}" if row.get("cluster_offgrid_id") else f"se4all-mg-{i}",
            "asset_name": row.get("community") or "Unnamed site",
            "asset_type": "mini_grid",
            "program_name": row.get("project"),
            "state": row.get("shapeName"),
            "lga": row.get("lga_name"),
            "community": row.get("community"),
            "developer": row.get("owner"),
            "owner_operator": row.get("owner"),
            "technology": TECH_MAP.get(power_system.lower(), power_system.lower() or None),
            "status": normalize_status(row),
            "capacity_kw": row.get("power_kw"),
            "customers_served": row.get("number_of_connections"),
            "financing_source": row.get("fund_type"),
            "latitude": row.get("lat"),
            "longitude": row.get("lon"),
            "geocode_precision": "exact_site",
            "source_name": SOURCE_NAME,
            "source_url": SOURCE_URL,
            "source_date_accessed": today,
            "notes": f"raw status='{row.get('status')}', condition='{row.get('condition')}'",
        })

    df = pd.DataFrame(rows).sort_values(["state", "asset_name"]).reset_index(drop=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Saved processed CSV: {output_path} ({len(df)} rows)")
    missing_state = df["state"].isna().sum()
    if missing_state:
        print(f"Note: {missing_state} site(s) did not resolve to a state via spatial join (check coordinates)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert the downloaded SE4ALL mini-grids GeoJSON to a cleaned CSV."
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
    except (FileNotFoundError, requests.RequestException, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
