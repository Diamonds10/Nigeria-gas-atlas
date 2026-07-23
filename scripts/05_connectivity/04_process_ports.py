"""
Process the downloaded World Port Index shapefile (inside a zip) into a cleaned,
Nigeria-filtered CSV.

This script expects that the raw zip has already been downloaded into
`data/raw/05_connectivity/` using the downloader script. Reads directly from the
zip via GDAL's /vsizip/ support (through the "zip://" URL scheme) -- no manual
extraction needed.
"""

import argparse
from pathlib import Path
import sys

import geopandas as gpd

RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "05_connectivity"
PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed" / "05_connectivity"
RAW_FILENAME = "world_port_index.zip"
OUTPUT_FILENAME = "world_port_index_nigeria.csv"

KEEP_COLUMNS = [
    "PORT_NAME", "HARBORSIZE", "HARBORTYPE", "SHELTER", "CARGOWHARF", "CARGO_ANCH",
    "CRANEFIXED", "CRANEMOBIL", "RAILWAY", "COMM_RAIL", "MAX_VESSEL", "geometry",
]


def get_input_path(input_dir: Path) -> Path:
    path = input_dir / RAW_FILENAME
    if not path.exists():
        raise FileNotFoundError(
            f"Required raw file not found: {path}\n"
            "Run scripts/05_connectivity/03_download_ports.py first."
        )
    return path


def process(zip_path: Path, output_path: Path, country_code: str) -> None:
    gdf = gpd.read_file(f"zip://{zip_path}!WPI.shp")
    filtered = gdf[gdf["COUNTRY"] == country_code].reset_index(drop=True)
    if filtered.empty:
        raise ValueError(f"No rows found for country code: {country_code}")

    available_columns = [col for col in KEEP_COLUMNS if col in filtered.columns]
    filtered = filtered[available_columns].copy()
    filtered["geometry"] = filtered["geometry"].apply(lambda geom: geom.wkt if geom is not None else None)
    filtered = filtered.sort_values("PORT_NAME").reset_index(drop=True)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    filtered.to_csv(output_path, index=False)
    print(f"Saved processed CSV: {output_path} ({len(filtered)} rows)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert the downloaded World Port Index zip to a cleaned, Nigeria-filtered CSV."
    )
    parser.add_argument("--raw-dir", type=Path, default=RAW_DATA_DIR)
    parser.add_argument("--processed-dir", type=Path, default=PROCESSED_DIR)
    parser.add_argument("--country-code", type=str, default="NG", help="ISO2 country code as used by WPI.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    raw_dir = args.raw_dir.expanduser().resolve()
    processed_dir = args.processed_dir.expanduser().resolve()

    try:
        input_path = get_input_path(raw_dir)
        process(input_path, processed_dir / OUTPUT_FILENAME, args.country_code)
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
