"""
Downloads the World Port Index (WPI), NGA's global database of ports and shipping
terminals, via its Humanitarian Data Exchange (HDX) mirror.

Source: https://data.humdata.org/dataset/world-port-index (originally NGA Pub. 150)
License: Open (public U.S. government data)
Coverage: Global, last updated 2017 per the underlying file (ports/terminals rarely
relocate, but facility-level details like cranes/rail service may be stale)
"""

import argparse
from pathlib import Path
import sys

import requests

RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "05_connectivity"
HDX_PACKAGE_API = "https://data.humdata.org/api/3/action/package_show?id=world-port-index"


def resolve_download_url() -> str:
    response = requests.get(HDX_PACKAGE_API, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    response.raise_for_status()
    resources = response.json()["result"]["resources"]
    for resource in resources:
        if resource["name"].endswith(".zip"):
            return resource["url"]
    raise RuntimeError("Could not find a .zip resource in the HDX world-port-index package")


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
    parser = argparse.ArgumentParser(description="Download the World Port Index dataset.")
    parser.add_argument("--output-dir", type=Path, default=RAW_DATA_DIR)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    dest_path = output_dir / "world_port_index.zip"

    try:
        url = resolve_download_url()
        download_file(url, dest_path, force=args.force)
    except (RuntimeError, requests.RequestException) as exc:
        print(exc, file=sys.stderr)
        return 1

    print("\nDownload complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
