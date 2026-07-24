"""
Process the raw Nigeria SE4ALL mini-grids GeoJSON into a cleaned CSV matching the
schema proposed in docs/renewable_offgrid_minigrid_asset_layer_spec.md.

This script expects that the raw GeoJSON has already been downloaded into
`data/raw/07_renewables/` using the downloader script. The source dataset has no
`state` field (only LGA/community), so state is derived here via a point-in-polygon
spatial join against geoBoundaries' Nigeria ADM1 boundaries, fetched at run time.
"""

import argparse
import json
from datetime import date
from pathlib import Path
import sys

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import shape

RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "07_renewables"
PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed" / "07_renewables"
CURATED_DIR = Path(__file__).resolve().parents[2] / "data" / "curated" / "07_renewables"
RAW_FILENAME = "se4all_minigrids_nigeria.json"
OUTPUT_FILENAME = "renewable_offgrid_minigrid_nigeria.csv"
SUPPLEMENT_FILENAME = "verified_public_offgrid_supplement.csv"
AUDIT_FILENAME = "minigrid_state_coverage_audit.csv"

STATES_BOUNDARY_URL = (
    "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/"
    "NGA/ADM1/geoBoundaries-NGA-ADM1_simplified.geojson"
)

SOURCE_NAME = "Nigeria SE4ALL Open Data Portal"
SOURCE_URL = "https://data.nigeriase4all.gov.ng/catalogue/#/dataset/1"

TECH_MAP = {
    "solar": "solar",
    "solar hybrid": "hybrid_mini_grid",
    "biogas": "other",
}

PROGRAMME_ONLY_EVIDENCE = {
    "Abia": {
        "evidence": "DARES grant agreement includes future Darway Coast mini-grids across Abia and five other states; named commissioned Abia sites were not published.",
        "source_url": "https://nep.rea.gov.ng/posts/news_2ND_PBG_GRANT_SIGNING_FOR_NIGERIA_DARES.html",
    },
    "Borno": {
        "evidence": "EEP Phase II includes a 12 MW solar-hybrid project for the University of Maiduguri and Teaching Hospital; commissioning was not confirmed by the audited source.",
        "source_url": "https://www.dares.rea.gov.ng/energizing-education-rea-secures-universitys-commitment-to-eep-sustainability.html",
    },
    "Ekiti": {
        "evidence": "REA/NEP lists Ekiti in a later AfDB mini-grid tender and Federal University Oye-Ekiti in the public-institution pipeline; no named commissioned record was verified.",
        "source_url": "https://nep.rea.gov.ng/solar-hybrid-mini-grid-for-economic-development-afdb.html",
    },
    "Enugu": {
        "evidence": "REA/NEP lists Enugu in a later AfDB mini-grid tender; no named commissioned record was verified.",
        "source_url": "https://nep.rea.gov.ng/solar-hybrid-mini-grid-for-economic-development-afdb.html",
    },
    "Imo": {
        "evidence": "EEP Phase III includes an 8.2 MW solar-hybrid project for FUTO and DARES agreements include future Imo deployments; commissioning was not confirmed.",
        "source_url": "https://www.dares.rea.gov.ng/energizing-education-rea-secures-universitys-commitment-to-eep-sustainability.html",
    },
    "Zamfara": {
        "evidence": "REA procurement records include proposed solar mini-grid work in Zamfara; a named commissioned record was not verified.",
        "source_url": "https://rea.gov.ng/wp-content/uploads/2021/07/Y2021-Capital-Project-Advert-v11.pdf",
    },
}


def get_input_path(input_dir: Path) -> Path:
    path = input_dir / RAW_FILENAME
    if not path.exists():
        raise FileNotFoundError(
            f"Required raw file not found: {path}\n"
            "Run scripts/07_renewables/01_download_minigrids.py first."
        )
    return path


def fetch_states_boundary() -> gpd.GeoDataFrame:
    response = requests.get(STATES_BOUNDARY_URL, timeout=60)
    response.raise_for_status()
    return gpd.GeoDataFrame.from_features(response.json()["features"], crs="EPSG:4326")


def normalize_status(row) -> str:
    status = str(row.get("status") or "").strip().lower()
    condition = str(row.get("condition") or "").strip().lower()
    if "construction" in status:
        return "under_construction"
    if "existing" in status and "operational" in condition and "non" not in condition:
        return "operational"
    if "existing" in status:
        return "commissioned"
    return "unknown"


def build_state_audit(
    frame: pd.DataFrame,
    states: gpd.GeoDataFrame,
    output_path: Path,
) -> None:
    rows = []
    for state_name in sorted(states["shapeName"].dropna().unique()):
        state_records = frame[frame["state"] == state_name]
        origins = state_records["record_origin"].value_counts()
        mapped_count = len(state_records)
        programme = PROGRAMME_ONLY_EVIDENCE.get(state_name, {})
        if mapped_count:
            coverage_status = "catalogued_public_records"
            interpretation = (
                f"{mapped_count} named public record(s) are catalogued; this is "
                "not evidence that the state has only this many assets."
            )
        elif programme:
            coverage_status = "official_pipeline_only"
            interpretation = (
                "No named, geocoded commissioned record was verified in this "
                "audit; official programme or procurement evidence exists. "
                "This must not be interpreted as zero assets."
            )
        else:
            coverage_status = "public_evidence_gap"
            interpretation = (
                "No named, geocoded commissioned record was verified in this "
                "audit. This must not be interpreted as zero assets."
            )
        rows.append(
            {
                "state": state_name,
                "catalogued_record_count": mapped_count,
                "se4all_record_count": int(origins.get("nigeria_se4all", 0)),
                "official_supplement_count": int(
                    origins.get("official_supplement", 0)
                ),
                "exact_site_record_count": int(
                    state_records["geocode_precision"].eq("exact_site").sum()
                ),
                "operational_or_commissioned_count": int(
                    state_records["status"].isin(
                        {"operational", "commissioned"}
                    ).sum()
                ),
                "coverage_status": coverage_status,
                "coverage_interpretation": interpretation,
                "programme_evidence": programme.get("evidence"),
                "programme_source_url": programme.get("source_url"),
                "audit_date": "2026-07-24",
            }
        )
    pd.DataFrame(rows).to_csv(output_path, index=False)
    print(f"Saved state coverage audit: {output_path} ({len(rows)} rows)")


def process(input_path: Path, output_path: Path) -> None:
    raw = json.loads(input_path.read_text())
    sites = gpd.GeoDataFrame.from_features(raw["features"], crs="EPSG:4326")

    states = fetch_states_boundary()
    joined = gpd.sjoin(sites, states[["shapeName", "geometry"]], how="left", predicate="within")

    today = date.today().isoformat()
    rows = []
    for i, row in joined.iterrows():
        power_system = str(row.get("power_system") or "").strip()
        rows.append({
            "asset_id": f"se4all-mg-{row.get('cluster_offgrid_id', i)}" if row.get("cluster_offgrid_id") else f"se4all-mg-{i}",
            "asset_name": row.get("community") or "Unnamed site",
            "asset_type": "mini_grid",
            "program_name": row.get("project"),
            "state": row.get("shapeName"),
            "lga": row.get("lga_name"),
            "community": row.get("community"),
            "developer": row.get("owner"),
            "owner_operator": row.get("owner"),
            "technology": TECH_MAP.get(power_system.lower(), power_system.lower() or None),
            "status": normalize_status(row),
            "capacity_kw": row.get("power_kw"),
            "customers_served": row.get("number_of_connections"),
            "financing_source": row.get("fund_type"),
            "latitude": row.get("lat"),
            "longitude": row.get("lon"),
            "geocode_precision": "exact_site",
            "coordinate_source": "Nigeria SE4ALL source coordinates",
            "source_name": SOURCE_NAME,
            "source_url": SOURCE_URL,
            "source_date_accessed": today,
            "evidence_level": "source_portal_record",
            "record_origin": "nigeria_se4all",
            "notes": (
                f"raw status='{None if pd.isna(row.get('status')) else row.get('status')}', "
                f"condition='{None if pd.isna(row.get('condition')) else row.get('condition')}'"
            ),
        })

    df = pd.DataFrame(rows)
    supplement_path = CURATED_DIR / SUPPLEMENT_FILENAME
    supplement = pd.read_csv(supplement_path)
    missing_columns = set(df.columns) - set(supplement.columns)
    if missing_columns:
        raise ValueError(
            f"Supplement is missing canonical columns: {sorted(missing_columns)}"
        )
    supplement = supplement[df.columns]
    df = pd.concat([df, supplement], ignore_index=True)
    if not df["asset_id"].is_unique:
        duplicates = df.loc[df["asset_id"].duplicated(), "asset_id"].tolist()
        raise ValueError(f"Duplicate asset_id values after merge: {duplicates}")
    df = df.sort_values(["state", "asset_name"]).reset_index(drop=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Saved processed CSV: {output_path} ({len(df)} rows)")
    build_state_audit(df, states, output_path.parent / AUDIT_FILENAME)
    missing_state = df["state"].isna().sum()
    if missing_state:
        print(f"Note: {missing_state} site(s) did not resolve to a state via spatial join (check coordinates)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert the downloaded SE4ALL mini-grids GeoJSON to a cleaned CSV."
    )
    parser.add_argument("--raw-dir", type=Path, default=RAW_DATA_DIR)
    parser.add_argument("--processed-dir", type=Path, default=PROCESSED_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    raw_dir = args.raw_dir.expanduser().resolve()
    processed_dir = args.processed_dir.expanduser().resolve()

    try:
        input_path = get_input_path(raw_dir)
        process(input_path, processed_dir / OUTPUT_FILENAME)
    except (FileNotFoundError, ValueError, requests.RequestException, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
