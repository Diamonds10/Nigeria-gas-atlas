"""
Process the downloaded Nigeria WDPA extract (a File Geodatabase inside a zip) into a
cleaned CSV with WKT geometry, combining the polygon and point protected-area layers.

This script expects that the raw zip has already been downloaded into
`data/raw/03_environmental/` using the downloader script. Reads directly from the
zip (no manual extraction needed) since the internal .gdb and layer names embed the
release month/year and would otherwise need to be hardcoded.
"""

import argparse
from pathlib import Path
import sys
import zipfile

import geopandas as gpd
import pandas as pd

RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "03_environmental"
PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed" / "03_environmental"
RAW_FILENAME = "wdpa_wdoecm_nigeria.zip"
OUTPUT_FILENAME = "wdpa_protected_areas_nigeria.csv"

KEEP_COLUMNS = [
    "SITE_ID", "NAME", "DESIG_ENG", "DESIG_TYPE", "IUCN_CAT", "REP_AREA", "GIS_AREA",
    "STATUS", "STATUS_YR", "GOV_TYPE", "OWN_TYPE", "MANG_AUTH", "geometry_type", "geometry",
]


def get_input_path(input_dir: Path) -> Path:
    path = input_dir / RAW_FILENAME
    if not path.exists():
        raise FileNotFoundError(
            f"Required raw file not found: {path}\n"
            "Run scripts/03_environmental/03_download_wdpa.py first."
        )
    return path


def find_gdb_name(zip_path: Path) -> str:
    with zipfile.ZipFile(zip_path) as zf:
        top_level = {name.split("/")[0] for name in zf.namelist()}
    gdb_names = sorted(name for name in top_level if name.endswith(".gdb"))
    if not gdb_names:
        raise ValueError(f"No .gdb found inside {zip_path}")
    return gdb_names[0]


def load_layer(zip_path: Path, gdb_name: str, layer_prefix: str) -> gpd.GeoDataFrame:
    vsi_path = f"zip://{zip_path}!{gdb_name}"
    layers = gpd.list_layers(vsi_path)
    matches = [name for name in layers["name"] if name.startswith(layer_prefix)]
    if not matches:
        raise ValueError(f"No layer starting with '{layer_prefix}' found in {gdb_name}")
    return gpd.read_file(vsi_path, layer=matches[0])


def process(zip_path: Path, output_path: Path) -> None:
    gdb_name = find_gdb_name(zip_path)
    print(f"Reading {gdb_name} from {zip_path.name}")

    poly = load_layer(zip_path, gdb_name, "WDPA_WDOECM_poly_")
    poly["geometry_type"] = "polygon"
    points = load_layer(zip_path, gdb_name, "WDPA_WDOECM_point_")
    points["geometry_type"] = "point"

    combined = pd.concat([poly, points], ignore_index=True)
    available_columns = [col for col in KEEP_COLUMNS if col in combined.columns]
    combined = combined[available_columns]
    combined["geometry"] = combined["geometry"].apply(lambda geom: geom.wkt if geom is not None else None)
    combined = combined.sort_values("NAME").reset_index(drop=True)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(output_path, index=False)
    print(f"Saved processed CSV: {output_path} ({len(combined)} rows: {len(poly)} polygons, {len(points)} points)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert the downloaded WDPA Nigeria zip to a cleaned CSV with WKT geometry."
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
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
