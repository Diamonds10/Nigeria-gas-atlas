"""
Downloads public REA / NEP / DARES / Solar Power Naija pages that are useful for
auditing and extending Nigeria's renewable off-grid and mini-grid asset layer.

This is intentionally conservative: it gathers public-source pages, preserves the
original URLs, and provides a reproducible intake step for later asset curation.
"""

import argparse
from pathlib import Path
import sys

import requests

RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "07_renewables"
PUBLIC_SOURCES = [
    {
        "name": "REA_home",
        "url": "https://rea.gov.ng/",
        "filename": "rea_home.html",
    },
    {
        "name": "NEP_home",
        "url": "https://nep.rea.gov.ng/",
        "filename": "nep_home.html",
    },
    {
        "name": "DARES",
        "url": "https://nep.rea.gov.ng/dares.html",
        "filename": "dares.html",
    },
    {
        "name": "SPN_home",
        "url": "https://spn.rea.gov.ng/",
        "filename": "spn_home.html",
    },
    {
        "name": "WorldBank_mini_grids",
        "url": "https://www.worldbank.org/en/topic/energy/publication/mini-grids-for-half-a-billion-people",
        "filename": "worldbank_mini_grids.html",
    },
]


def download_file(url: str, dest_path: Path, force: bool = False) -> Path:
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if dest_path.exists() and not force:
        print(f"Skipping existing file: {dest_path}")
        return dest_path

    print(f"Downloading {url}\n  -> {dest_path}")
    try:
        response = requests.get(url, timeout=60, headers={"User-Agent": "nigeria-gas-atlas-research/1.0"})
        response.raise_for_status()
        dest_path.write_text(response.text, encoding="utf-8")
    except requests.RequestException as exc:
        raise RuntimeError(f"Download failed for {url}: {exc}") from exc

    print(f"Downloaded {dest_path.name} ({dest_path.stat().st_size} bytes)")
    return dest_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download public REA / NEP / DARES / SPN pages for renewable off-grid and mini-grid asset discovery."
    )
    parser.add_argument("--output-dir", type=Path, default=RAW_DATA_DIR)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    for source in PUBLIC_SOURCES:
        dest_path = output_dir / source["filename"]
        print(f"\nSource: {source['name']}")
        try:
            download_file(source["url"], dest_path, force=args.force)
        except RuntimeError as exc:
            print(exc, file=sys.stderr)
            return 1

    print("\nDownload complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
