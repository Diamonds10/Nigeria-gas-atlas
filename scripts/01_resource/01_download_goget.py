"""
Downloads Global Energy Monitor's Global Oil and Gas Extraction Tracker (GOGET)
country-level dashboard tables.

Source: https://globalenergymonitor.org/projects/global-oil-gas-extraction-tracker
License: CC-BY 4.0 (per GEM's stated data policy)
Coverage: Country/area-level counts, production, discoveries and FIDs; latest release March 2026

Note: this pulls the public dashboard summary workbook (aggregated by country), not the
full field-level asset database. The field-level database with per-field coordinates,
operator and reserves is distributed as a separate .xls file gated behind a download
form on the GEM website and must be requested/downloaded manually.
"""

import argparse
from pathlib import Path
import sys

import requests

RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "01_resource"
SPREADSHEET_ID = "1JHt24Rmm6e0DyeTSqvqH1i9nJ876iYrq6X1InCAHcf0"
DATASETS = [
    {
        "description": "GOGET country-level dashboard (all sheets)",
        "url": f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=xlsx",
        "filename": "goget_dashboard_2026-03.xlsx",
    },
]


def download_file(url: str, dest_path: Path, force: bool = False) -> Path:
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if dest_path.exists() and not force:
        print(f"Skipping existing file: {dest_path}")
        return dest_path

    print(f"Downloading {url}\n  -> {dest_path}")
    try:
        with requests.get(url, stream=True, timeout=60, headers={"User-Agent": "Mozilla/5.0"}) as response:
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
    parser = argparse.ArgumentParser(
        description="Download Global Energy Monitor GOGET country-level dashboard tables."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=RAW_DATA_DIR,
        help="Directory where downloaded files will be saved.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download files even if they already exist.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    for dataset in DATASETS:
        dest_path = output_dir / dataset["filename"]
        print(f"\nDataset: {dataset['description']}")
        try:
            download_file(dataset["url"], dest_path, force=args.force)
        except RuntimeError as exc:
            print(exc, file=sys.stderr)
            return 1

    print("\nDownload complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
