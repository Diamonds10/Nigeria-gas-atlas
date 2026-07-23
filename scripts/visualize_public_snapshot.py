#!/usr/bin/env python3
"""
Generate a public-facing Nigeria atlas map snapshot that shows the current
verified asset counts and major public layer context.

This script is intentionally simple and reproducible: it reads the processed
CSV outputs already present in the repository and writes a single PNG snapshot
into outputs/maps/ for public-facing use.
"""

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import requests
import shapely.wkt

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs" / "maps"
OUTPUT_FILE = OUTPUT_DIR / "nigeria_public_asset_snapshot.png"

STATE_BOUNDARY_URL = (
    "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/"
    "NGA/ADM1/geoBoundaries-NGA-ADM1_simplified.geojson"
)

POWER_PLANTS_PATH = ROOT / "data/processed/02_infrastructure/gogpt_oil_gas_plants_nigeria.csv"
SUBSTATIONS_PATH = ROOT / "data/processed/05_connectivity/osm_power_grid_nigeria.csv"
DEMAND_CENTERS_PATH = ROOT / "data/processed/04_demand/demand_centers_nigeria.csv"
MINI_GRIDS_PATH = ROOT / "data/processed/07_renewables/renewable_offgrid_minigrid_nigeria.csv"


def fetch_states() -> gpd.GeoDataFrame:
    response = requests.get(STATE_BOUNDARY_URL, timeout=60)
    response.raise_for_status()
    return gpd.GeoDataFrame.from_features(response.json()["features"], crs="EPSG:4326")


def build_power_plants_gdf() -> gpd.GeoDataFrame:
    df = pd.read_csv(POWER_PLANTS_PATH)
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["lng"], df["lat"]),
        crs="EPSG:4326",
    )
    return gdf


def build_substations_gdf() -> gpd.GeoDataFrame:
    df = pd.read_csv(SUBSTATIONS_PATH)
    df = df[df["power"] == "substation"].copy()
    df["geometry"] = df["geometry"].apply(shapely.wkt.loads)
    return gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")


def build_demand_gdf() -> gpd.GeoDataFrame:
    df = pd.read_csv(DEMAND_CENTERS_PATH)
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["lon"], df["lat"]),
        crs="EPSG:4326",
    )
    return gdf


def build_minigrids_gdf() -> gpd.GeoDataFrame:
    df = pd.read_csv(MINI_GRIDS_PATH)
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
        crs="EPSG:4326",
    )
    return gdf


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    states = fetch_states()
    power_plants = build_power_plants_gdf()
    substations = build_substations_gdf()
    demand = build_demand_gdf()
    mini_grids = build_minigrids_gdf()

    states = states.to_crs(epsg=3857)
    power_plants = power_plants.to_crs(epsg=3857)
    substations = substations.to_crs(epsg=3857)
    demand = demand.to_crs(epsg=3857)
    mini_grids = mini_grids.to_crs(epsg=3857)

    fig, ax = plt.subplots(figsize=(14, 14))
    states.plot(ax=ax, facecolor="#f5f7f9", edgecolor="#7d93a7", linewidth=0.6)

    for _, row in states.iterrows():
        centroid = row.geometry.centroid
        ax.text(
            centroid.x,
            centroid.y,
            row.get("shapeName", ""),
            fontsize=5,
            color="#4f5d75",
            ha="center",
            va="center",
            alpha=0.75,
        )

    power_plants.plot(
        ax=ax,
        color="#b22234",
        markersize=8,
        alpha=0.85,
        label=f"Power-producing plants ({len(power_plants)})",
    )
    substations.plot(
        ax=ax,
        color="#1f77b4",
        markersize=3,
        alpha=0.7,
        label=f"Substations ({len(substations)})",
    )
    demand.plot(
        ax=ax,
        color="#2ca02c",
        markersize=80,
        alpha=0.9,
        label=f"Demand centres ({len(demand)})",
    )
    mini_grids.plot(
        ax=ax,
        color="#f0ad4e",
        markersize=35,
        alpha=0.9,
        label=f"Mini-grids ({len(mini_grids)})",
    )

    ax.set_title("Nigeria public energy atlas snapshot", fontsize=16, weight="bold")
    ax.set_axis_off()
    ax.legend(loc="upper right", frameon=True, fontsize=9)
    ax.text(
        0.02,
        0.02,
        "Public-facing screening snapshot: 193 power-producing plants, 390 substations, 28 demand centres, and 66 mini-grids.",
        transform=ax.transAxes,
        fontsize=9,
        color="#1f2937",
        bbox=dict(boxstyle="round,pad=0.35", facecolor="white", alpha=0.85),
    )

    plt.tight_layout()
    plt.savefig(OUTPUT_FILE, dpi=200, bbox_inches="tight")
    print(f"Saved public snapshot: {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
