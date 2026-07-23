"""
Downloads Global Energy Monitor's Global Iron and Steel Tracker (GSPT) plant-level
data, served publicly by GreenInfo Network's steel tracker map viewer.

Source: https://globalenergymonitor.org/projects/global-iron-and-steel-tracker
Mirror queried: https://greeninfo-network.github.io/steel-tracker/
License: CC-BY 4.0 (per GEM's stated data policy; not explicitly restated on the
GreenInfo mirror page, confirm before redistributing)
Coverage: global, plant-level, with lat/lng
"""

import argparse
from pathlib import Path
import sys

import requests

RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "04_demand"
DATASETS = [
    {
        "description": "Global steel plants (all countries)",
        "url": "https://greeninfo-network.github.io/steel-tracker/data/data.csv",
        "filename": "gspt_steel_plants_all_countries.csv",
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
    parser = argparse.ArgumentParser(description="Download GSPT steel plant data.")
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
