"""
Downloads Nigeria crude oil production time series from the EIA International
Energy Statistics API (v2).

Source: https://www.eia.gov/opendata/browser/international
License: Open (U.S. government public data)
Coverage: Annual, 1973-present

Note: this EIA v2 API route only exposes petroleum production/consumption/imports/
stocks facets for international data -- it does not expose natural gas production or
reserves figures (checked against the productId/activityId facets on 2026-07-21).
Reserves and natural gas figures should come from NUPRC/NEITI reports or GOGET instead.

Requires an EIA API key. Register for free at https://www.eia.gov/opendata/register.php
and set it as EIA_API_KEY, either as an environment variable or in a .env file at the
repo root (EIA_API_KEY=...).
"""

import argparse
import json
import os
from pathlib import Path
import sys

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = REPO_ROOT / "data" / "raw" / "01_resource"
API_URL = "https://api.eia.gov/v2/international/data/"
PRODUCT_ID = "57"  # Crude oil including lease condensate
ACTIVITY_ID = "1"  # Production
COUNTRY_ID = "NGA"


def load_api_key() -> str:
    key = os.environ.get("EIA_API_KEY")
    if key:
        return key

    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.strip().startswith("EIA_API_KEY="):
                return line.split("=", 1)[1].strip()

    raise RuntimeError(
        "EIA_API_KEY not found. Register at https://www.eia.gov/opendata/register.php "
        "and set it as an environment variable or in a .env file at the repo root."
    )


def fetch_all_rows(api_key: str) -> list[dict]:
    rows: list[dict] = []
    offset = 0
    length = 500
    while True:
        params = {
            "api_key": api_key,
            "frequency": "annual",
            "data[0]": "value",
            "facets[activityId][]": ACTIVITY_ID,
            "facets[productId][]": PRODUCT_ID,
            "facets[countryRegionId][]": COUNTRY_ID,
            "sort[0][column]": "period",
            "sort[0][direction]": "asc",
            "offset": offset,
            "length": length,
        }
        response = requests.get(API_URL, params=params, timeout=60)
        response.raise_for_status()
        payload = response.json()
        batch = payload["response"]["data"]
        rows.extend(batch)
        total = int(payload["response"]["total"])
        offset += len(batch)
        if not batch or offset >= total:
            break
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download Nigeria crude oil production data from the EIA API."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=RAW_DATA_DIR,
        help="Directory where the downloaded raw JSON will be saved.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        api_key = load_api_key()
        rows = fetch_all_rows(api_key)
    except (RuntimeError, requests.RequestException) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    dest_path = output_dir / "eia_nigeria_crude_oil_production_1973-present.json"
    dest_path.write_text(json.dumps(rows, indent=2))
    print(f"Saved {len(rows)} rows -> {dest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
