#!/usr/bin/env python3
"""Download Nigeria population and settlement/access context source files."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import requests

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RAW_DIR = ROOT / "data" / "raw" / "08_context"

DRE_URL = (
    "https://energydata.info/dataset/8db756b9-180b-42aa-8990-87662f81b838/"
    "resource/3e8c78a6-d39b-408e-aefa-cac738d4e711/download/"
    "nigeria_dre_atlas_settlements.csv"
)
WORLDPOP_ADMIN_URL = (
    "https://data.worldpop.org/repo/wopr/NGA/population/v3.0/"
    "NGA_population_v3_0_admin.zip"
)

DOWNLOADS = {
    "nigeria_dre_atlas_settlements.csv": DRE_URL,
    "NGA_population_v3_0_admin.zip": WORLDPOP_ADMIN_URL,
}


def download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    print(f"Downloading {destination.name}")
    with requests.get(url, stream=True, timeout=(30, 300)) as response:
        response.raise_for_status()
        with temporary.open("wb") as output:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    output.write(chunk)
    temporary.replace(destination)
    print(f"Saved {destination} ({destination.stat().st_size / 1_000_000:.1f} MB)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    raw_dir = args.raw_dir.resolve()
    try:
        for filename, url in DOWNLOADS.items():
            destination = raw_dir / filename
            if destination.exists() and not args.force:
                print(f"Using existing {destination}")
                continue
            download(url, destination)
    except (OSError, requests.RequestException) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
