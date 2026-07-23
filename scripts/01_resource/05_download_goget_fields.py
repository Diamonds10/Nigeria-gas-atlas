"""
Downloads the field-level Global Oil and Gas Extraction Tracker (GOGET) dataset
served by GreenInfo Network's public GOGET map viewer (built for Global Energy Monitor).

Source: https://greeninfo-network.github.io/global-oil-gas-extraction-tracker/
License: CC-BY 4.0 (per GEM's stated GOGET data policy)
Coverage: Snapshot dated 2023-08-02 (per HTTP Last-Modified header) -- older than the
March 2026 country-level dashboard already downloaded via 01_download_goget.py, so
per-field counts will not exactly match those aggregate totals.

This is the only field-level GOGET data (project name, status, operator, owner, fuel
type, lat/lng) found to be openly downloadable without an email/form gate. GEM's own
current-release field-level file is distributed via a gated download form -- contact
scott.zimmerman@globalenergymonitor.org for that if a more current snapshot is needed.
"""

import argparse
from pathlib import Path
import sys

import requests

RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "01_resource"
DATASETS = [
    {
        "description": "GOGET field-level asset data (all countries)",
        "url": "https://greeninfo-network.github.io/global-oil-gas-extraction-tracker/data/data.csv",
        "filename": "goget_fields_all_countries_2023-08.csv",
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
        description="Download the GOGET field-level asset dataset."
    )
    parser.add_argument("--output-dir", type=Path, default=RAW_DATA_DIR)
    parser.add_argument("--force", action="store_true")
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
