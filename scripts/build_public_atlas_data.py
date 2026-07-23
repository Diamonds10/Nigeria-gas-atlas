#!/usr/bin/env python3
"""Build the deterministic GeoJSON bundle used by the GitHub Pages atlas.

The public web map is deliberately a screening product. To keep the bundle
responsive it includes motorway and trunk roads, while the analysis-ready CSV
retains all four processed major-road classes.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
from shapely import from_wkt
from shapely.geometry import LineString, MultiLineString, Point, mapping

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
DEFAULT_STATES = ROOT / "data" / "final" / "nigeria_adm1_simplified.geojson"
DEFAULT_OUTPUT = ROOT / "docs" / "assets" / "atlas_data.json"
PUBLIC_SIMPLIFY_TOLERANCE = 0.005
PUBLIC_COORDINATE_PRECISION = 5


def clean_value(value: Any) -> Any:
    """Convert pandas/numpy scalar values into strict JSON-compatible values."""
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def properties(row: pd.Series, columns: Iterable[str], label_column: str) -> dict[str, Any]:
    result = {}
    for column in columns:
        value = clean_value(row.get(column))
        if value is not None and value != "":
            result[column] = value
    result["_label"] = clean_value(row.get(label_column))
    return result


def feature(geometry: Any, props: dict[str, Any]) -> dict[str, Any]:
    geometry = geometry.simplify(PUBLIC_SIMPLIFY_TOLERANCE, preserve_topology=True)
    geojson_geometry = mapping(geometry)
    geojson_geometry["coordinates"] = round_coordinates(geojson_geometry["coordinates"])
    return {
        "type": "Feature",
        "properties": props,
        "geometry": geojson_geometry,
    }


def round_coordinates(value: Any) -> Any:
    if isinstance(value, (list, tuple)):
        return [round_coordinates(item) for item in value]
    return round(float(value), PUBLIC_COORDINATE_PRECISION)


def point_features(
    path: Path,
    longitude: str,
    latitude: str,
    columns: list[str],
    label_column: str,
) -> list[dict[str, Any]]:
    frame = pd.read_csv(path)
    frame = frame.dropna(subset=[longitude, latitude])
    return [
        feature(
            Point(float(row[longitude]), float(row[latitude])),
            properties(row, columns, label_column),
        )
        for _, row in frame.iterrows()
    ]


def wkt_features(
    path: Path,
    geometry_column: str,
    columns: list[str],
    label_column: str,
    *,
    where: tuple[str, set[str]] | None = None,
    centroid: bool = False,
) -> list[dict[str, Any]]:
    frame = pd.read_csv(path)
    if where:
        column, allowed = where
        frame = frame[frame[column].isin(allowed)]
    frame = frame.dropna(subset=[geometry_column])
    output = []
    for _, row in frame.iterrows():
        geometry = from_wkt(row[geometry_column])
        if geometry.geom_type == "MultiPoint" and len(geometry.geoms) == 1:
            geometry = geometry.geoms[0]
        if centroid and geometry.geom_type != "Point":
            geometry = geometry.centroid
        output.append(feature(geometry, properties(row, columns, label_column)))
    return output


def route_features(
    path: Path,
    columns: list[str],
    label_column: str,
) -> list[dict[str, Any]]:
    """Parse GEM routes encoded as colon-separated ``lat,lng`` pairs."""
    frame = pd.read_csv(path).dropna(subset=["route"])
    output = []
    for _, row in frame.iterrows():
        lines = []
        for encoded_line in str(row["route"]).split(";"):
            coordinates = []
            for pair in encoded_line.split(":"):
                latitude, longitude = pair.split(",", maxsplit=1)
                coordinates.append((float(longitude), float(latitude)))
            if len(coordinates) >= 2:
                lines.append(coordinates)
        if lines:
            geometry = LineString(lines[0]) if len(lines) == 1 else MultiLineString(lines)
            output.append(
                feature(
                    geometry,
                    properties(row, columns, label_column),
                )
            )
    return output


def sublayer(label: str, geometry_type: str, features: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "label": label,
        "geomType": geometry_type,
        "data": {"type": "FeatureCollection", "features": features},
    }


def build_bundle(states_path: Path = DEFAULT_STATES) -> dict[str, Any]:
    states = json.loads(states_path.read_text(encoding="utf-8"))

    fields = point_features(
        PROCESSED / "01_resource/goget_fields_nigeria_2023-08.csv",
        "lng", "lat",
        [
            "project", "status", "operator", "owner", "fuel_type",
            "discovery_year", "start_year", "url",
        ],
        "project",
    )
    gas_pipelines = route_features(
        PROCESSED / "02_infrastructure/ggit_gas_pipelines_nigeria.csv",
        [
            "project", "parent", "status", "start_year", "capacity",
            "capacity_units", "url",
        ],
        "project",
    )
    oil_pipelines = route_features(
        PROCESSED / "02_infrastructure/goit_oil_ngl_pipelines_nigeria.csv",
        ["project", "parent", "status", "capacity", "url"],
        "project",
    )
    lng_terminals = point_features(
        PROCESSED / "02_infrastructure/ggit_lng_terminals_nigeria.csv",
        "lng", "lat",
        ["project", "unit", "parent", "status", "capacity", "capacity_units", "url"],
        "project",
    )
    power_plants = point_features(
        PROCESSED / "02_infrastructure/gogpt_oil_gas_plants_nigeria.csv",
        "lng", "lat",
        [
            "project", "unit", "province", "status", "fuel_type", "capacity",
            "technology", "start_year", "owner", "url",
        ],
        "project",
    )
    refineries = point_features(
        PROCESSED / "02_infrastructure/refineries_nigeria.csv",
        "lng", "lat",
        ["project", "operator", "state", "status", "capacity_bpd", "commissioned_year"],
        "project",
    )
    protected_areas = wkt_features(
        PROCESSED / "03_environmental/wdpa_protected_areas_nigeria.csv",
        "geometry",
        ["NAME", "DESIG_ENG", "IUCN_CAT", "GIS_AREA", "STATUS", "STATUS_YR", "GOV_TYPE"],
        "NAME",
    )
    demand_centers = point_features(
        PROCESSED / "04_demand/demand_centers_nigeria.csv",
        "lon", "lat",
        ["demand_center", "category", "state_or_region", "status", "notes"],
        "demand_center",
    )
    roads = wkt_features(
        PROCESSED / "05_connectivity/osm_roads_major_nigeria.csv",
        "geometry", ["highway", "name", "ref", "surface", "lanes"], "name",
        where=("highway", {"motorway", "trunk"}),
    )
    railways = wkt_features(
        PROCESSED / "05_connectivity/osm_railways_nigeria.csv",
        "geometry", ["railway", "name", "operator", "gauge"], "name",
        where=("railway", {"rail"}),
    )
    rail_stations = wkt_features(
        PROCESSED / "05_connectivity/osm_railways_nigeria.csv",
        "geometry", ["name"], "name",
        where=("railway", {"station"}),
    )
    power_grid = wkt_features(
        PROCESSED / "05_connectivity/osm_power_grid_nigeria.csv",
        "geometry", ["power", "name", "operator", "voltage"], "name",
        where=("power", {"line", "minor_line"}),
    )
    substations = wkt_features(
        PROCESSED / "05_connectivity/osm_power_grid_nigeria.csv",
        "geometry", ["power", "name", "operator", "voltage"], "name",
        where=("power", {"substation"}),
        centroid=True,
    )
    ports = wkt_features(
        PROCESSED / "05_connectivity/world_port_index_nigeria.csv",
        "geometry",
        [
            "PORT_NAME", "HARBORSIZE", "HARBORTYPE", "CARGOWHARF",
            "CRANEFIXED", "RAILWAY", "MAX_VESSEL",
        ],
        "PORT_NAME",
        centroid=True,
    )
    minigrids = point_features(
        PROCESSED / "07_renewables/renewable_offgrid_minigrid_nigeria.csv",
        "longitude", "latitude",
        [
            "asset_name", "state", "lga", "technology", "status", "capacity_kw",
            "customers_served", "developer", "financing_source", "source_url",
        ],
        "asset_name",
    )

    return {
        "states": states,
        "layers": {
            "resource": {
                "label": "Resource",
                "sublayers": {"fields": sublayer("Oil & Gas Fields", "point", fields)},
            },
            "infrastructure": {
                "label": "Infrastructure",
                "sublayers": {
                    "gas_pipelines": sublayer("Gas Pipelines", "line", gas_pipelines),
                    "oil_pipelines": sublayer("Oil & NGL Pipelines", "line", oil_pipelines),
                    "lng_terminals": sublayer("LNG Terminals", "point", lng_terminals),
                    "power_plants": sublayer("Gas & Oil Power Plants", "point", power_plants),
                    "refineries": sublayer("Refineries", "point", refineries),
                },
            },
            "environmental": {
                "label": "Environmental",
                "sublayers": {
                    "protected_areas": sublayer(
                        "Protected Areas (WDPA)", "polygon", protected_areas
                    )
                },
            },
            "demand": {
                "label": "Demand",
                "sublayers": {
                    "demand_centers": sublayer("Demand Centers", "point", demand_centers)
                },
            },
            "connectivity": {
                "label": "Connectivity",
                "sublayers": {
                    "roads": sublayer("Major Roads", "line", roads),
                    "railways": sublayer("Railways", "line", railways),
                    "rail_stations": sublayer("Railway Stations", "point", rail_stations),
                    "power_grid": sublayer("Power Grid Lines", "line", power_grid),
                    "substations": sublayer("Substations", "point", substations),
                    "ports": sublayer("Ports & Terminals", "point", ports),
                },
            },
            "renewables": {
                "label": "Renewables",
                "sublayers": {
                    "minigrids": sublayer("Off-grid & Mini-grids", "point", minigrids)
                },
            },
        },
    }


def write_bundle(bundle: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(bundle, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--states", type=Path, default=DEFAULT_STATES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    bundle = build_bundle(args.states.resolve())
    write_bundle(bundle, args.output.resolve())
    total = sum(
        len(sub["data"]["features"])
        for layer in bundle["layers"].values()
        for sub in layer["sublayers"].values()
    )
    print(f"Saved {args.output} with {total:,} public map features")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
