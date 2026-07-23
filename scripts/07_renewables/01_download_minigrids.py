"""
Downloads Nigeria's mini-grid asset inventory from the Nigeria SE4ALL (Sustainable
Energy for All) open data portal, a GeoNode/GeoServer instance operated as part of
the national electrification-planning platform.

Source: https://data.nigeriase4all.gov.ng (dataset "se4allWS:minigrids")
Catalogue page: https://data.nigeriase4all.gov.ng/catalogue/#/dataset/1
License: Not explicitly stated on the dataset page -- open data portal, government
of Nigeria / SE4ALL initiative; confirm terms before redistributing downstream.
Coverage: 66 mini-grid sites nationally as of access date, with lat/lon, capacity,
status, funder, and owner/developer.

This is a genuine site-level asset inventory (not a policy/programme page), found
by inspecting the portal's GeoServer WFS backend rather than scraping the map UI.
"""

import argparse
import json
from pathlib import Path
import sys

import requests

RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "07_renewables"
WFS_URL = (
    "https://data.nigeriase4all.gov.ng/geoserver/ows"
    "?service=WFS&version=1.0.0&request=GetFeature"
    "&typename=se4allWS:minigrids&outputFormat=json&srsName=EPSG:4326"
)


def download_file(url: str, dest_path: Path, force: bool = False) -> Path:
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if dest_path.exists() and not force:
        print(f"Skipping existing file: {dest_path}")
        return dest_path

    print(f"Downloading {url}\n  -> {dest_path}")
    response = requests.get(url, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    payload = response.json()
    if "features" not in payload:
        raise RuntimeError(f"Unexpected WFS response shape (no 'features' key): {list(payload.keys())}")

    dest_path.write_text(json.dumps(payload))
    print(f"Saved {len(payload['features'])} features -> {dest_path}")
    return dest_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download the Nigeria SE4ALL mini-grids dataset.")
    parser.add_argument("--output-dir", type=Path, default=RAW_DATA_DIR)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    dest_path = output_dir / "se4all_minigrids_nigeria.json"

    try:
        download_file(WFS_URL, dest_path, force=args.force)
    except (requests.RequestException, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("\nDownload complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
