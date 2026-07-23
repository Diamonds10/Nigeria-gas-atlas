"""
Downloads OPEC Annual Statistical Bulletin (ASB) PDF editions used to build a
Nigeria crude oil and natural gas reserves time series.

Source: https://www.opec.org/annual-statistical-bulletin.html
License: Open (public OPEC publication)
Coverage per edition: each ASB shows a trailing 5-year reserves table. The editions
below are chosen to give a continuous, non-overlapping series from 2007-2024:
  - asb-2012 -> 2007-2011
  - asb-2015 -> 2010-2014 (overlaps 2010-2011 with asb-2012 as a consistency check)
  - asb-2020 -> 2015-2019
  - asb-2025 -> 2020-2024
Earlier editions (2010, 2011) are not published at this URL pattern (404), so 2007
is the earliest year reachable this way.
"""

import argparse
from pathlib import Path
import sys

import requests

RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "01_resource"
EDITIONS = [2012, 2015, 2020, 2025]


def download_file(url: str, dest_path: Path, force: bool = False) -> Path:
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if dest_path.exists() and not force:
        print(f"Skipping existing file: {dest_path}")
        return dest_path

    print(f"Downloading {url}\n  -> {dest_path}")
    try:
        with requests.get(url, stream=True, timeout=120, headers={"User-Agent": "Mozilla/5.0"}) as response:
            response.raise_for_status()
            with dest_path.open("wb") as out_file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        out_file.write(chunk)
    except requests.RequestException as exc:
        raise RuntimeError(f"Download failed for {url}: {exc}") from exc

    print(f"Downloaded {dest_path.name} ({dest_path.stat().st_size} bytes)")
    return dest_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download OPEC ASB PDF editions.")
    parser.add_argument("--output-dir", type=Path, default=RAW_DATA_DIR)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    for year in EDITIONS:
        url = f"https://www.opec.org/assets/assetdb/asb-{year}.pdf"
        dest_path = output_dir / f"opec_asb_{year}.pdf"
        try:
            download_file(url, dest_path, force=args.force)
        except RuntimeError as exc:
            print(exc, file=sys.stderr)
            return 1

    print("\nDownload complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
