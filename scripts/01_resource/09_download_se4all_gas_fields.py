"""
Downloads Nigeria's oil/gas field boundary polygons from the Nigeria SE4ALL
Open Data Portal (the same GeoNode/GeoServer instance used for the mini-grid
inventory in Layer 7).

Source: https://data.nigeriase4all.gov.ng (dataset "geonode:gas_fields")
Catalogue page: https://data.nigeriase4all.gov.ng/catalogue/#/dataset/15
License: Not explicitly stated on the dataset page -- public government/donor
open data portal; confirm terms before redistributing.
Coverage: 124 field-polygon records (57 unique field names, since several
fields are mapped as multiple non-contiguous polygon parts) as of access date.

This complements (not replaces) the GOGET field-level data already in this
layer: GOGET has point coordinates for 180 named fields; this dataset adds
actual footprint polygons and includes ~33 field names not present in GOGET
at all. See scripts/01_resource/10_process_se4all_gas_fields.py for how the
two are reconciled.
"""

import argparse
import json
from pathlib import Path
import sys

import requests

RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "01_resource"
WFS_URL = (
    "https://data.nigeriase4all.gov.ng/geoserver/ows"
    "?service=WFS&version=1.0.0&request=GetFeature"
    "&typename=geonode:gas_fields&outputFormat=json&srsName=EPSG:4326"
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
    parser = argparse.ArgumentParser(description="Download the Nigeria SE4ALL gas_fields dataset.")
    parser.add_argument("--output-dir", type=Path, default=RAW_DATA_DIR)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    dest_path = output_dir / "se4all_gas_fields_nigeria.json"

    try:
        download_file(WFS_URL, dest_path, force=args.force)
    except (requests.RequestException, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("\nDownload complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
