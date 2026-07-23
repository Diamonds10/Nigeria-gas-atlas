"""
Downloads the Nigeria-only extract of the World Database on Protected Areas (WDPA),
direct from UNEP-WCMC's public CloudFront distribution -- no API token required.

Source: https://www.protectedplanet.net/country/NGA
License: Open, for non-commercial use (see WDPA_WDOECM_Manual_1_6.pdf bundled in the
download for full terms)
Coverage: Current monthly release

The WDPA is republished monthly under a filename like
WDPA_WDOECM_<Mon><Year>_Public_NGA.zip. This script tries the current month and
steps backward a few months to find the latest available release, since the exact
publish day within a month varies.
"""

import argparse
from datetime import date
from pathlib import Path
import sys

import requests

RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "03_environmental"
BASE_URL = "https://d1gam3xoknrgr2.cloudfront.net/current/WDPA_WDOECM_{month_tag}_Public_NGA.zip"
MONTHS_TO_TRY = 4


def month_tag(year: int, month: int) -> str:
    return date(year, month, 1).strftime("%b%Y")


def candidate_urls(months_back: int) -> list[str]:
    today = date.today()
    year, month = today.year, today.month
    urls = []
    for _ in range(months_back):
        urls.append(BASE_URL.format(month_tag=month_tag(year, month)))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return urls


def download_first_available(dest_path: Path, force: bool = False) -> Path:
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if dest_path.exists() and not force:
        print(f"Skipping existing file: {dest_path}")
        return dest_path

    last_error: Exception | None = None
    for url in candidate_urls(MONTHS_TO_TRY):
        print(f"Trying {url}")
        try:
            response = requests.get(url, stream=True, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
            if response.status_code == 404:
                print("  not found, trying an earlier month")
                continue
            response.raise_for_status()
            with dest_path.open("wb") as out_file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        out_file.write(chunk)
            print(f"Downloaded {dest_path.name} ({dest_path.stat().st_size} bytes) from {url}")
            return dest_path
        except requests.RequestException as exc:
            last_error = exc
            continue

    raise RuntimeError(
        f"Could not find a WDPA release in the last {MONTHS_TO_TRY} months. "
        f"Last error: {last_error}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download the Nigeria WDPA extract.")
    parser.add_argument("--output-dir", type=Path, default=RAW_DATA_DIR)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    dest_path = output_dir / "wdpa_wdoecm_nigeria.zip"

    try:
        download_first_available(dest_path, force=args.force)
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 1

    print("\nDownload complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
