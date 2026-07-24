#!/usr/bin/env python3
"""Create compact Nigeria population, settlement, and access-proxy datasets.

The World Bank DRE settlement file supplies settlement clusters, population
estimates, night-light detection, and grid-distance indicators. Night-light
detection is retained as a screening signal and must not be interpreted as a
measured household electricity-access rate.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import zipfile

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RAW_DIR = ROOT / "data" / "raw" / "08_context"
DEFAULT_PROCESSED_DIR = ROOT / "data" / "processed" / "08_context"

DRE_FILENAME = "nigeria_dre_atlas_settlements.csv"
WORLDPOP_FILENAME = "NGA_population_v3_0_admin.zip"
GRID_SIZE_DEGREES = 0.25
MAJOR_SETTLEMENTS_PER_STATE = 40

DRE_COLUMNS = [
    "geohash",
    "lat",
    "lon",
    "village_name",
    "admin_cgaz_1",
    "admin_cgaz_2",
    "hull_area",
    "building_density_percent",
    "num_buildings",
    "population",
    "main_road_access",
    "dist_main_road_km",
    "has_education_facility",
    "has_health_facility",
    "mean_rwi",
    "distance_to_existing_transmission_lines",
    "distance_to_existing_hv_transmission_lines",
    "has_nightlight",
    "distance_to_gridlight_targets",
    "pv_value",
    "num_connections",
    "demand",
    "demand_connection",
]

STATE_NAME_MAP = {
    "Federal Capital Territory": "Abuja Federal Capital Territory",
    "Federal Capital": "Abuja Federal Capital Territory",
    "FCT": "Abuja Federal Capital Territory",
    "Fct": "Abuja Federal Capital Territory",
    "FCT Abuja": "Abuja Federal Capital Territory",
    "Cross-River": "Cross River",
    "plateau": "Plateau",
}


def require(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(
            f"Required source not found: {path}\n"
            "Run scripts/08_context/01_download_population_settlements_access.py first."
        )
    return path


def as_boolean(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin({"true", "1", "yes"})


def load_dre(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, usecols=DRE_COLUMNS, low_memory=False)
    numeric_columns = [
        "lat",
        "lon",
        "hull_area",
        "building_density_percent",
        "num_buildings",
        "population",
        "dist_main_road_km",
        "mean_rwi",
        "distance_to_existing_transmission_lines",
        "distance_to_existing_hv_transmission_lines",
        "distance_to_gridlight_targets",
        "pv_value",
        "num_connections",
        "demand",
        "demand_connection",
    ]
    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    for column in [
        "main_road_access",
        "has_education_facility",
        "has_health_facility",
        "has_nightlight",
    ]:
        frame[column] = as_boolean(frame[column])

    frame = frame.dropna(subset=["geohash", "lat", "lon", "population"]).copy()
    frame = frame[frame["population"] >= 0].copy()
    frame["state"] = (
        frame["admin_cgaz_1"]
        .replace(STATE_NAME_MAP)
        .fillna("Unknown")
        .astype(str)
        .str.strip()
    )
    frame["lga"] = frame["admin_cgaz_2"].fillna("Unknown").astype(str).str.strip()
    frame["settlement_name"] = (
        frame["village_name"].fillna("Unnamed settlement").astype(str).str.strip()
    )
    frame["nightlight_signal"] = np.where(
        frame["has_nightlight"],
        "nightlight_detected",
        "no_nightlight_detected",
    )
    frame["population_without_nightlight_signal"] = np.where(
        frame["has_nightlight"],
        0,
        frame["population"],
    )
    frame["population_with_nightlight_signal"] = np.where(
        frame["has_nightlight"],
        frame["population"],
        0,
    )
    return frame


def find_zip_member(zip_path: Path, suffix: str) -> str:
    with zipfile.ZipFile(zip_path) as archive:
        matches = [name for name in archive.namelist() if name.endswith(suffix)]
    if not matches:
        raise ValueError(f"Could not find {suffix} inside {zip_path}")
    return matches[0]


def load_worldpop_states(zip_path: Path) -> pd.DataFrame:
    try:
        member = find_zip_member(zip_path, "states_pop_total_scaled.csv")
    except ValueError:
        member = find_zip_member(zip_path, "state_pop_total_scaled.csv")
    with zipfile.ZipFile(zip_path) as archive:
        with archive.open(member) as source:
            frame = pd.read_csv(source)
    frame.columns = [str(column).strip().lower() for column in frame.columns]
    state_column = next(
        column
        for column in frame.columns
        if column in {"state", "state_name", "statename", "admin1name"}
    )
    population_column = next(
        column
        for column in frame.columns
        if "pop" in column
        and (
            "total" in column
            or "scaled" in column
            or column == "population"
        )
    )
    output = frame[[state_column, population_column]].copy()
    output.columns = ["state", "worldpop_population_2025"]
    output["state"] = output["state"].replace(STATE_NAME_MAP).astype(str).str.strip()
    output["worldpop_population_2025"] = pd.to_numeric(
        output["worldpop_population_2025"], errors="coerce"
    )
    return output.dropna(subset=["worldpop_population_2025"])


def weighted_mean(frame: pd.DataFrame, value_column: str) -> float:
    valid = frame[value_column].notna() & frame["population"].gt(0)
    if not valid.any():
        return np.nan
    return float(
        np.average(
            frame.loc[valid, value_column],
            weights=frame.loc[valid, "population"],
        )
    )


def aggregate_group(frame: pd.DataFrame) -> pd.Series:
    population = frame["population"].sum()
    lit_population = frame["population_with_nightlight_signal"].sum()
    return pd.Series(
        {
            "settlement_count": len(frame),
            "named_settlement_count": frame["settlement_name"].ne("Unnamed settlement").sum(),
            "population_estimate": population,
            "population_with_nightlight_signal": lit_population,
            "population_without_nightlight_signal": frame[
                "population_without_nightlight_signal"
            ].sum(),
            "nightlight_population_share_pct": (
                100 * lit_population / population if population > 0 else np.nan
            ),
            "total_buildings": frame["num_buildings"].sum(min_count=1),
            "reported_connections": frame["num_connections"].sum(min_count=1),
            "modeled_demand": frame["demand"].sum(min_count=1),
            "population_weighted_distance_transmission_km": weighted_mean(
                frame, "distance_to_existing_transmission_lines"
            ),
            "population_weighted_distance_gridlight_km": weighted_mean(
                frame, "distance_to_gridlight_targets"
            ),
        }
    )


def build_grid(frame: pd.DataFrame) -> pd.DataFrame:
    grid = frame.copy()
    grid["grid_lon"] = (
        np.floor(grid["lon"] / GRID_SIZE_DEGREES) * GRID_SIZE_DEGREES
        + GRID_SIZE_DEGREES / 2
    )
    grid["grid_lat"] = (
        np.floor(grid["lat"] / GRID_SIZE_DEGREES) * GRID_SIZE_DEGREES
        + GRID_SIZE_DEGREES / 2
    )
    grouped = (
        grid.groupby(["grid_lat", "grid_lon"], sort=True, observed=True)
        .apply(aggregate_group, include_groups=False)
        .reset_index()
    )
    grouped.insert(
        0,
        "cell_id",
        grouped.apply(
            lambda row: f"nga_{row['grid_lat']:.3f}_{row['grid_lon']:.3f}",
            axis=1,
        ),
    )
    return grouped


def build_state_summary(frame: pd.DataFrame, worldpop: pd.DataFrame) -> pd.DataFrame:
    summary = (
        frame.groupby("state", sort=True, observed=True)
        .apply(aggregate_group, include_groups=False)
        .reset_index()
    )
    summary = summary.rename(columns={"population_estimate": "dre_cluster_population"})
    summary = summary.merge(worldpop, on="state", how="outer")
    summary["dre_vs_worldpop_difference_pct"] = (
        100
        * (summary["dre_cluster_population"] - summary["worldpop_population_2025"])
        / summary["worldpop_population_2025"]
    )
    return summary.sort_values("state").reset_index(drop=True)


def build_major_settlements(frame: pd.DataFrame) -> pd.DataFrame:
    ranked = frame.sort_values(
        ["state", "population", "settlement_name"],
        ascending=[True, False, True],
    ).copy()
    ranked["state_population_rank"] = (
        ranked.groupby("state", observed=True).cumcount() + 1
    )
    ranked = ranked[
        ranked["state_population_rank"] <= MAJOR_SETTLEMENTS_PER_STATE
    ].copy()
    columns = [
        "geohash",
        "settlement_name",
        "state",
        "lga",
        "lat",
        "lon",
        "population",
        "state_population_rank",
        "num_buildings",
        "building_density_percent",
        "nightlight_signal",
        "distance_to_existing_transmission_lines",
        "distance_to_existing_hv_transmission_lines",
        "distance_to_gridlight_targets",
        "main_road_access",
        "dist_main_road_km",
        "has_education_facility",
        "has_health_facility",
        "mean_rwi",
        "pv_value",
        "num_connections",
        "demand",
        "demand_connection",
    ]
    return ranked[columns].sort_values(
        ["state", "state_population_rank"]
    ).reset_index(drop=True)


def write_outputs(
    dre: pd.DataFrame,
    worldpop: pd.DataFrame,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    settlement_columns = [
        "geohash",
        "settlement_name",
        "state",
        "lga",
        "lat",
        "lon",
        "hull_area",
        "building_density_percent",
        "num_buildings",
        "population",
        "nightlight_signal",
        "distance_to_existing_transmission_lines",
        "distance_to_existing_hv_transmission_lines",
        "distance_to_gridlight_targets",
        "main_road_access",
        "dist_main_road_km",
        "has_education_facility",
        "has_health_facility",
        "mean_rwi",
        "pv_value",
        "num_connections",
        "demand",
        "demand_connection",
    ]
    settlements = dre[settlement_columns].sort_values("geohash").reset_index(drop=True)
    grid = build_grid(dre)
    state_summary = build_state_summary(dre, worldpop)
    major = build_major_settlements(dre)

    outputs = {
        "dre_settlement_context_nigeria.csv": settlements,
        "population_access_grid_nigeria.csv": grid,
        "state_population_access_summary_nigeria.csv": state_summary,
        "major_settlements_nigeria.csv": major,
    }
    for filename, frame in outputs.items():
        path = output_dir / filename
        frame.to_csv(path, index=False)
        print(f"Saved {path} ({len(frame):,} rows)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--processed-dir", type=Path, default=DEFAULT_PROCESSED_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        dre = load_dre(require(args.raw_dir / DRE_FILENAME))
        worldpop = load_worldpop_states(require(args.raw_dir / WORLDPOP_FILENAME))
        write_outputs(dre, worldpop, args.processed_dir)
    except (FileNotFoundError, ValueError, OSError, pd.errors.ParserError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
