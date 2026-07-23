#!/usr/bin/env python3
"""
Generate an interactive Nigeria Infrastructure Atlas map with layer toggles.

This map includes gas and oil field points as an optional toggleable layer,
plus power-producing plants, substations, demand centres, and mini-grids.
"""

from pathlib import Path

import folium
import geopandas as gpd
import pandas as pd
import requests
import shapely.wkt

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs" / "maps"
OUTPUT_FILE = OUTPUT_DIR / "nigeria_infrastructure_atlas_interactive.html"

STATE_BOUNDARY_URL = (
    "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/"
    "NGA/ADM1/geoBoundaries-NGA-ADM1_simplified.geojson"
)

POWER_PLANTS_PATH = ROOT / "data" / "processed" / "02_infrastructure" / "gogpt_oil_gas_plants_nigeria.csv"
SUBSTATIONS_PATH = ROOT / "data" / "processed" / "05_connectivity" / "osm_power_grid_nigeria.csv"
DEMAND_CENTERS_PATH = ROOT / "data" / "processed" / "04_demand" / "demand_centers_nigeria.csv"
MINI_GRIDS_PATH = ROOT / "data" / "processed" / "07_renewables" / "renewable_offgrid_minigrid_nigeria.csv"
GAS_FIELDS_PATH = ROOT / "data" / "processed" / "01_resource" / "goget_fields_nigeria_2023-08.csv"


def fetch_states() -> gpd.GeoDataFrame:
    response = requests.get(STATE_BOUNDARY_URL, timeout=60)
    response.raise_for_status()
    return gpd.GeoDataFrame.from_features(response.json()["features"], crs="EPSG:4326")


def build_power_plants_gdf() -> gpd.GeoDataFrame:
    df = pd.read_csv(POWER_PLANTS_PATH)
    return gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["lng"], df["lat"]),
        crs="EPSG:4326",
    )


def build_substations_gdf() -> gpd.GeoDataFrame:
    df = pd.read_csv(SUBSTATIONS_PATH)
    df = df[df["power"] == "substation"].copy()
    df["geometry"] = df["geometry"].apply(shapely.wkt.loads)
    return gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")


def build_demand_gdf() -> gpd.GeoDataFrame:
    df = pd.read_csv(DEMAND_CENTERS_PATH)
    return gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["lon"], df["lat"]),
        crs="EPSG:4326",
    )


def build_minigrids_gdf() -> gpd.GeoDataFrame:
    df = pd.read_csv(MINI_GRIDS_PATH)
    return gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
        crs="EPSG:4326",
    )


def build_gas_fields_gdf() -> gpd.GeoDataFrame:
    df = pd.read_csv(GAS_FIELDS_PATH)
    df = df.dropna(subset=["lat", "lng"]).copy()
    return gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["lng"], df["lat"]),
        crs="EPSG:4326",
    )


import collections


def add_feature_group(map_obj, gdf, name, color, radius=5, popup_template=None, show=True):
    feature_group = folium.FeatureGroup(name=name, show=show)
    for _, row in gdf.iterrows():
        popup_text = ""
        if popup_template is not None:
            safe_data = collections.defaultdict(str, row.to_dict())
            popup_text = popup_template.format_map(safe_data)

        geom = row.geometry
        if not geom.geom_type == "Point":
            geom = geom.centroid

        folium.CircleMarker(
            location=(geom.y, geom.x),
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.85,
            popup=folium.Popup(popup_text, max_width=280),
        ).add_to(feature_group)
    feature_group.add_to(map_obj)


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    states = fetch_states()
    power_plants = build_power_plants_gdf()
    substations = build_substations_gdf()
    demand = build_demand_gdf()
    mini_grids = build_minigrids_gdf()
    gas_fields = build_gas_fields_gdf()

    m = folium.Map(location=[9.0820, 8.6753], zoom_start=5.5, tiles="CartoDB positron")

    folium.GeoJson(
        states,
        name="State boundaries",
        style_function=lambda feature: {
            "fillColor": "#f8fafc",
            "color": "#7d93a7",
            "weight": 1,
            "fillOpacity": 0.1,
        },
        tooltip=folium.GeoJsonTooltip(fields=["shapeName"], aliases=["State:"]),
    ).add_to(m)

    add_feature_group(
        m,
        power_plants,
        "Power-producing plants",
        "#b22234",
        radius=6,
        popup_template="<b>{project}</b><br>Fuel: {fuel_type}<br>Status: {status}",
        show=True,
    )

    add_feature_group(
        m,
        substations,
        "Substations",
        "#1f77b4",
        radius=4,
        popup_template="<b>{name}</b><br>Voltage: {voltage}<br>Status: {status}",
        show=True,
    )

    add_feature_group(
        m,
        demand,
        "Demand centres",
        "#2ca02c",
        radius=8,
        popup_template="<b>{demand_center}</b><br>Type: {category}<br>Status: {status}",
        show=True,
    )

    add_feature_group(
        m,
        mini_grids,
        "Mini-grids",
        "#f0ad4e",
        radius=6,
        popup_template="<b>{asset_name}</b><br>Technology: {technology}<br>Status: {status}",
        show=True,
    )

    add_feature_group(
        m,
        gas_fields,
        "Gas and oil fields",
        "#6f42c1",
        radius=5,
        popup_template=(
            "<b>{project}</b><br>Fuel: {fuel_type}<br>Status: {status}" 
            "<br>Operator: {operator}<br>Owner: {owner}"
        ),
        show=False,
    )

    folium.LayerControl(collapsed=False).add_to(m)
    m.save(OUTPUT_FILE)
    print(f"Saved interactive atlas: {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
