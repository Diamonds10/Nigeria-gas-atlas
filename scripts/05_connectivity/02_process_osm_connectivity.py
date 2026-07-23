"""
Process the raw Overpass JSON responses (roads, railways, power grid) into cleaned
CSVs with WKT geometry.

This script expects that the raw JSON files have already been downloaded into
`data/raw/05_connectivity/` using the downloader script.
"""

import argparse
import json
from pathlib import Path
import sys

import pandas as pd
from shapely.geometry import LineString, Point, Polygon

RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "05_connectivity"
PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed" / "05_connectivity"

JOBS = [
    {
        "input": "osm_roads_major_nigeria.json",
        "output": "osm_roads_major_nigeria.csv",
        "tag_keys": ["highway", "name", "ref", "surface", "lanes"],
    },
    {
        "input": "osm_railways_nigeria.json",
        "output": "osm_railways_nigeria.csv",
        "tag_keys": ["railway", "name", "operator", "gauge"],
    },
    {
        "input": "osm_power_grid_nigeria.json",
        "output": "osm_power_grid_nigeria.csv",
        "tag_keys": ["power", "name", "operator", "voltage"],
    },
]


def element_geometry(element: dict):
    if element["type"] == "node":
        return Point(element["lon"], element["lat"])

    geom_points = element.get("geometry")
    if not geom_points:
        return None
    coords = [(pt["lon"], pt["lat"]) for pt in geom_points]
    if len(coords) < 2:
        return None
    if element.get("tags", {}).get("power") == "substation" and coords[0] == coords[-1] and len(coords) >= 4:
        return Polygon(coords)
    return LineString(coords)


def get_input_path(input_dir: Path, filename: str) -> Path:
    path = input_dir / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Required raw file not found: {path}\n"
            "Run scripts/05_connectivity/01_download_osm_connectivity.py first."
        )
    return path


def process(input_path: Path, output_path: Path, tag_keys: list[str]) -> None:
    print(f"Processing {input_path.name}")
    payload = json.loads(input_path.read_text())
    elements = payload.get("elements", [])

    rows = []
    for element in elements:
        geom = element_geometry(element)
        if geom is None:
            continue
        tags = element.get("tags", {})
        row = {"osm_type": element["type"], "osm_id": element["id"]}
        row.update({key: tags.get(key) for key in tag_keys})
        row["geometry"] = geom.wkt
        rows.append(row)

    df = pd.DataFrame(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Saved processed CSV: {output_path} ({len(df)} rows)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert downloaded Overpass JSON files to cleaned CSVs with WKT geometry."
    )
    parser.add_argument("--raw-dir", type=Path, default=RAW_DATA_DIR)
    parser.add_argument("--processed-dir", type=Path, default=PROCESSED_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    raw_dir = args.raw_dir.expanduser().resolve()
    processed_dir = args.processed_dir.expanduser().resolve()

    for job in JOBS:
        try:
            input_path = get_input_path(raw_dir, job["input"])
            process(input_path, processed_dir / job["output"], job["tag_keys"])
        except (FileNotFoundError, OSError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
