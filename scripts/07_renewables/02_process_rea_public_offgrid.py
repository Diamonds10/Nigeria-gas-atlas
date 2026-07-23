"""
Process the downloaded public-source HTML pages into a minimal manifest documenting
which REA/NEP/DARES/SPN/World Bank programme pages were consulted while building
the Nigeria renewable off-grid and mini-grid asset layer.

Note: the actual site-level asset data for this layer comes from a different,
better source -- see scripts/07_renewables/01_download_minigrids.py and
02_process_minigrids.py, which pull a real geocoded inventory (66 sites) from the
Nigeria SE4ALL Open Data Portal's GeoServer backend. These programme pages don't
carry clean geocoded site lists (see docs/offgrid_minigrid_public_sources.md), so
this script only produces a source manifest for provenance, not an asset table.
"""

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "07_renewables"
PROCESSED_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "processed" / "07_renewables"

PUBLIC_SOURCES = [
    {"name": "REA_home", "url": "https://rea.gov.ng/", "filename": "rea_home.html"},
    {"name": "NEP_home", "url": "https://nep.rea.gov.ng/", "filename": "nep_home.html"},
    {"name": "DARES", "url": "https://nep.rea.gov.ng/dares.html", "filename": "dares.html"},
    {"name": "SPN_home", "url": "https://spn.rea.gov.ng/", "filename": "spn_home.html"},
    {
        "name": "WorldBank_mini_grids",
        "url": "https://www.worldbank.org/en/topic/energy/publication/mini-grids-for-half-a-billion-people",
        "filename": "worldbank_mini_grids.html",
    },
]

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a source manifest documenting the REA/NEP/DARES/SPN/World Bank pages consulted."
    )
    parser.add_argument("--raw-dir", type=Path, default=RAW_DATA_DIR)
    parser.add_argument("--output-dir", type=Path, default=PROCESSED_DATA_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    raw_dir = args.raw_dir.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    downloaded_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    manifest_path = output_dir / "rea_public_offgrid_sources_manifest.csv"

    with manifest_path.open("w", newline="", encoding="utf-8") as manifest_file:
        writer = csv.DictWriter(
            manifest_file,
            fieldnames=["source_name", "source_url", "page_file", "downloaded_at", "notes"],
        )
        writer.writeheader()

        for source in PUBLIC_SOURCES:
            page_file = raw_dir / source["filename"]
            writer.writerow(
                {
                    "source_name": source["name"],
                    "source_url": source["url"],
                    "page_file": str(page_file.name),
                    "downloaded_at": downloaded_at,
                    "notes": "Public source page retained for later asset curation and geocoding.",
                }
            )

    print(f"Created manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
