"""
Downloads Nigeria's major road network, railways, and electricity grid (transmission
lines + substations) from OpenStreetMap via the Overpass API.

Source: https://www.openstreetmap.org (queried via Overpass API)
License: ODbL
Coverage: Current OSM data for Nigeria (OSM relation 192787)

Roads are limited to motorway/trunk/primary/secondary (major network) rather than
every mapped street, to keep volume relevant for a national-scale atlas. The public
Overpass instances used here are shared infrastructure and occasionally return
406/504 errors under load; this script retries across mirrors with backoff.
"""

import argparse
import json
from pathlib import Path
import sys
import time

import requests

RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "05_connectivity"
NIGERIA_AREA_ID = 3600192787  # OSM relation 192787 (Nigeria) + 3600000000 offset
MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.fr/api/interpreter",
]

QUERIES = {
    "osm_roads_major_nigeria.json": (
        f"[out:json][timeout:180];area({NIGERIA_AREA_ID})->.ng;"
        '(way["highway"~"^(motorway|trunk|primary|secondary)$"](area.ng););out geom;'
    ),
    "osm_railways_nigeria.json": (
        f"[out:json][timeout:180];area({NIGERIA_AREA_ID})->.ng;"
        '(way["railway"~"^(rail|narrow_gauge)$"](area.ng);'
        'node["railway"="station"](area.ng););out geom;'
    ),
    "osm_power_grid_nigeria.json": (
        f"[out:json][timeout:180];area({NIGERIA_AREA_ID})->.ng;"
        '(way["power"="line"](area.ng);way["power"="minor_line"](area.ng);'
        'node["power"="substation"](area.ng);way["power"="substation"](area.ng););out geom;'
    ),
}


def run_query(query: str, retries: int = 3) -> dict:
    last_error: Exception | None = None
    for attempt in range(retries):
        for mirror in MIRRORS:
            try:
                response = requests.post(
                    mirror,
                    data={"data": query},
                    timeout=200,
                    headers={"User-Agent": "nigeria-gas-atlas-research/1.0 (DPhil thesis data collection)"},
                )
                if response.status_code == 200:
                    return response.json()
                print(f"  {mirror} returned {response.status_code}, trying next option")
            except requests.RequestException as exc:
                last_error = exc
                print(f"  {mirror} failed: {exc}")
        wait = 5 * (attempt + 1)
        print(f"  retrying in {wait}s (attempt {attempt + 1}/{retries})")
        time.sleep(wait)
    raise RuntimeError(f"All Overpass attempts failed. Last error: {last_error}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download Nigeria roads, railways, and power grid data from OSM via Overpass."
    )
    parser.add_argument("--output-dir", type=Path, default=RAW_DATA_DIR)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    for filename, query in QUERIES.items():
        dest_path = output_dir / filename
        if dest_path.exists() and not args.force:
            print(f"Skipping existing file: {dest_path}")
            continue

        print(f"\nQuerying: {filename}")
        try:
            result = run_query(query)
        except RuntimeError as exc:
            print(exc, file=sys.stderr)
            return 1

        dest_path.write_text(json.dumps(result))
        print(f"Saved {len(result.get('elements', []))} elements -> {dest_path}")

    print("\nDownload complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
