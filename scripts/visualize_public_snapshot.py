#!/usr/bin/env python3
"""
Generate a public-facing Nigeria atlas map snapshot that shows the current
verified asset counts and major public layer context.

This script is intentionally simple and reproducible: it reads the processed
CSV outputs already present in the repository and writes a single PNG snapshot
into outputs/maps/ for public-facing use.
"""

import json
from pathlib import Path

import geopandas as gpd
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import pandas as pd
import requests
import shapely.wkt

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs" / "maps"
OUTPUT_FILE = OUTPUT_DIR / "nigeria_public_asset_snapshot.png"
BENCHMARK_FILE = OUTPUT_DIR / "public_asset_benchmark_summary.json"

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


def build_benchmark_summary(
    power_plants: pd.DataFrame,
    substations: pd.DataFrame,
    demand: pd.DataFrame,
    mini_grids: pd.DataFrame,
) -> dict:
    mini_status = mini_grids["status"].value_counts(dropna=False).to_dict()
    mini_technology = mini_grids["technology"].value_counts(dropna=False).to_dict()
    mini_precision = mini_grids["geocode_precision"].value_counts(dropna=False).to_dict()

    benchmark = {
        "asset_counts": {
            "power_plants": int(len(power_plants)),
            "substations": int(len(substations)),
            "demand_centres": int(len(demand)),
            "mini_grids": int(len(mini_grids)),
        },
        "mini_grid_benchmark": {
            "states_covered": int(mini_grids["state"].nunique()),
            "capacity_coverage": int(mini_grids["capacity_kw"].notna().sum()),
            "customers_coverage": int(mini_grids["customers_served"].notna().sum()),
            "technology_coverage": int(mini_grids["technology"].notna().sum()),
            "developer_coverage": int(mini_grids["developer"].notna().sum()),
            "status_distribution": mini_status,
            "technology_distribution": mini_technology,
            "geocode_precision_distribution": mini_precision,
        },
        "public_dashboard_signal": {
            "best_for": [
                "site-level mini-grid screening",
                "state coverage benchmarking",
                "status and capacity scans",
                "public distributed-energy context",
            ],
            "limitations": [
                "not a complete solar home system registry",
                "not a full live operating asset database",
                "public metadata is thinner than a commercial operating platform",
                "zero catalogued records in a state does not mean zero assets",
            ],
        },
    }
    return benchmark


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    states = fetch_states()
    power_plants = build_power_plants_gdf()
    substations = build_substations_gdf()
    demand = build_demand_gdf()
    mini_grids = build_minigrids_gdf()

    power_plants_df = pd.read_csv(POWER_PLANTS_PATH)
    substations_df = pd.read_csv(SUBSTATIONS_PATH)
    substations_df = substations_df[substations_df["power"] == "substation"].copy()
    demand_df = pd.read_csv(DEMAND_CENTERS_PATH)
    mini_grids_df = pd.read_csv(MINI_GRIDS_PATH)

    benchmark = build_benchmark_summary(
        power_plants=power_plants_df,
        substations=substations_df,
        demand=demand_df,
        mini_grids=mini_grids_df,
    )
    BENCHMARK_FILE.write_text(json.dumps(benchmark, indent=2), encoding="utf-8")

    states = states.to_crs(epsg=3857)
    power_plants = power_plants.to_crs(epsg=3857)
    substations = substations.to_crs(epsg=3857)
    demand = demand.to_crs(epsg=3857)
    mini_grids = mini_grids.to_crs(epsg=3857)

    fig, ax = plt.subplots(figsize=(16, 14), facecolor="#f8fafc")
    ax.set_facecolor("#f8fafc")
    states.plot(ax=ax, facecolor="#f5f7f9", edgecolor="#7d93a7", linewidth=0.6)
    states.boundary.plot(ax=ax, color="#98a8b8", linewidth=0.45, alpha=0.8)

    for _, row in states.iterrows():
        centroid = row.geometry.centroid
        label = row.get("shapeName", "")
        text = ax.text(
            centroid.x,
            centroid.y,
            label,
            fontsize=6,
            color="#334155",
            ha="center",
            va="center",
            alpha=0.85,
            weight="bold",
        )
        text.set_path_effects([
            pe.Stroke(linewidth=3, foreground="white"),
            pe.Normal(),
        ])

    power_plants.plot(
        ax=ax,
        color="#b22234",
        markersize=9,
        alpha=0.9,
    )
    substations.plot(
        ax=ax,
        color="#1f77b4",
        markersize=4,
        alpha=0.8,
    )
    demand.plot(
        ax=ax,
        color="#2ca02c",
        markersize=100,
        alpha=0.9,
    )
    mini_grids.plot(
        ax=ax,
        color="#f0ad4e",
        markersize=55,
        alpha=0.92,
    )

    legend_handles = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#b22234", markersize=8, label=f"Power-producing plants ({len(power_plants)})"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#1f77b4", markersize=7, label=f"Substations ({len(substations)})"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#2ca02c", markersize=10, label=f"Demand centres ({len(demand)})"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#f0ad4e", markersize=9, label=f"Mini-grids ({len(mini_grids)})"),
    ]

    ax.set_title(
        "Nigeria public energy atlas snapshot",
        fontsize=18,
        weight="bold",
        color="#0f172a",
        pad=18,
    )
    ax.set_axis_off()
    legend = ax.legend(
        handles=legend_handles,
        title="Public asset layers",
        loc="upper right",
        frameon=True,
        fontsize=10,
        title_fontsize=11,
    )
    legend.get_frame().set_facecolor("white")
    legend.get_frame().set_edgecolor("#cbd5e1")

    ax.text(
        0.02,
        0.94,
        "Public screening snapshot — not a complete operating registry.",
        transform=ax.transAxes,
        fontsize=10,
        color="#0f172a",
        weight="semibold",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="white", alpha=0.92, edgecolor="#cbd5e1"),
    )

    ax.text(
        0.02,
        0.02,
        (
            "Public-facing screening snapshot: "
            f"{benchmark['asset_counts']['power_plants']} power-producing plants, "
            f"{benchmark['asset_counts']['substations']} substations, "
            f"{benchmark['asset_counts']['demand_centres']} demand centres, and "
            f"{benchmark['asset_counts']['mini_grids']} mini-grids. "
            f"Mini-grid benchmark: {benchmark['mini_grid_benchmark']['states_covered']} states/territories, "
            f"{benchmark['mini_grid_benchmark']['capacity_coverage']} with reported capacity, "
            f"{benchmark['mini_grid_benchmark']['customers_coverage']} with customer counts."
        ),
        transform=ax.transAxes,
        fontsize=9.5,
        color="#1f2937",
        bbox=dict(boxstyle="round,pad=0.45", facecolor="white", alpha=0.92),
    )

    plt.tight_layout()
    plt.savefig(OUTPUT_FILE, dpi=240, bbox_inches="tight")
    print(f"Saved public snapshot: {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
