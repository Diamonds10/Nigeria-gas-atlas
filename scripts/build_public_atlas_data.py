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
from shapely.geometry import LineString, MultiLineString, Point, mapping, shape
from shapely.prepared import prep

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
DEFAULT_STATES = ROOT / "data" / "final" / "nigeria_adm1_simplified.geojson"
DEFAULT_OUTPUT = ROOT / "docs" / "assets" / "atlas_data.json"
PUBLIC_SIMPLIFY_TOLERANCE = 0.005
PUBLIC_COORDINATE_PRECISION = 5
REPOSITORY_RAW = "https://raw.githubusercontent.com/Diamonds10/Nigeria-gas-atlas/main"

CATALOGUE = {
    "fields": {
        "description": "Site-level Nigerian oil and gas fields with status, fuel, operator, and ownership context.",
        "source": "Global Energy Monitor / GreenInfo Network GOGET mirror",
        "source_date": "2026-07-21",
        "license": "CC BY 4.0 inferred; verify before redistribution",
        "quality": "B",
        "quality_note": "Verified source points; field snapshot dates from August 2023.",
        "path": "data/processed/01_resource/goget_fields_nigeria_2023-08.csv",
    },
    "gas_pipelines": {
        "description": "Gas transmission pipeline routes that include Nigeria.",
        "source": "Global Energy Monitor / GreenInfo Network GGIT mirror",
        "source_date": "2026-07-21",
        "license": "CC BY 4.0 inferred; verify before redistribution",
        "quality": "B",
        "quality_note": "Public route geometry; cross-border projects may extend beyond Nigeria.",
        "path": "data/processed/02_infrastructure/ggit_gas_pipelines_nigeria.csv",
    },
    "oil_pipelines": {
        "description": "Oil and NGL transmission pipeline routes that include Nigeria.",
        "source": "Global Energy Monitor / GreenInfo Network GOIT mirror",
        "source_date": "2026-07-21",
        "license": "CC BY 4.0 inferred; verify before redistribution",
        "quality": "B",
        "quality_note": "Public route geometry; storage terminals are not included.",
        "path": "data/processed/02_infrastructure/goit_oil_ngl_pipelines_nigeria.csv",
    },
    "lng_terminals": {
        "description": "Nigerian LNG terminal train records with capacity and status context.",
        "source": "Global Energy Monitor / GreenInfo Network GGIT mirror",
        "source_date": "2026-07-21",
        "license": "CC BY 4.0 inferred; verify before redistribution",
        "quality": "B",
        "quality_note": "Site points with train-level records; multiple records may share a facility.",
        "path": "data/processed/02_infrastructure/ggit_lng_terminals_nigeria.csv",
    },
    "power_plants": {
        "description": "Oil- and gas-fired generating units across Nigerian power stations.",
        "source": "Global Energy Monitor / GreenInfo Network GOGPT mirror",
        "source_date": "2026-07-21",
        "license": "CC BY 4.0 inferred; verify before redistribution",
        "quality": "B",
        "quality_note": "Unit-level records; counts are not unique power-station counts.",
        "path": "data/processed/02_infrastructure/gogpt_oil_gas_plants_nigeria.csv",
    },
    "refineries": {
        "description": "Major Nigerian refinery sites with nameplate capacity and public status context.",
        "source": "Atlas compilation from public reporting",
        "source_date": "2026-07-21",
        "license": "Derived compilation; review underlying sources",
        "quality": "C",
        "quality_note": "Major refineries only; some coordinates are approximate and modular refineries are incomplete.",
        "path": "data/processed/02_infrastructure/refineries_nigeria.csv",
    },
    "protected_areas": {
        "description": "Protected and conserved areas including forest reserves, parks, and wetlands.",
        "source": "UNEP-WCMC / IUCN Protected Planet",
        "source_date": "2026-07-22",
        "license": "Source-specific terms; non-commercial restrictions apply",
        "quality": "A",
        "quality_note": "Authoritative source geometry, simplified only for web display.",
        "path": "data/processed/03_environmental/wdpa_protected_areas_nigeria.csv",
    },
    "demand_centers": {
        "description": "Cross-category industrial demand centres covering cement, steel, fertiliser, and refining.",
        "source": "Atlas compilation reconciled against GEM and OpenStreetMap",
        "source_date": "2026-07-21",
        "license": "Derived compilation; OSM-derived elements are ODbL",
        "quality": "C",
        "quality_note": "Most sites were independently checked; eight locations remain less precisely verified.",
        "path": "data/processed/04_demand/demand_centers_nigeria.csv",
    },
    "roads": {
        "description": "Motorway and trunk road segments used in the public web map.",
        "source": "OpenStreetMap via Overpass API",
        "source_date": "2026-07-23",
        "license": "ODbL",
        "quality": "B",
        "quality_note": "Web subset only; the processed CSV also includes primary and secondary roads.",
        "path": "data/processed/05_connectivity/osm_roads_major_nigeria.csv",
    },
    "railways": {
        "description": "Mapped Nigerian railway line segments.",
        "source": "OpenStreetMap via Overpass API",
        "source_date": "2026-07-23",
        "license": "ODbL",
        "quality": "B",
        "quality_note": "Geometry reflects OSM mapping, not confirmed operational service.",
        "path": "data/processed/05_connectivity/osm_railways_nigeria.csv",
    },
    "rail_stations": {
        "description": "Mapped Nigerian railway stations.",
        "source": "OpenStreetMap via Overpass API",
        "source_date": "2026-07-23",
        "license": "ODbL",
        "quality": "B",
        "quality_note": "Locations reflect OSM coverage and may include inactive stations.",
        "path": "data/processed/05_connectivity/osm_railways_nigeria.csv",
    },
    "power_grid": {
        "description": "Mapped electricity transmission and minor-line segments.",
        "source": "OpenStreetMap via Overpass API",
        "source_date": "2026-07-23",
        "license": "ODbL",
        "quality": "B",
        "quality_note": "Useful for geometry screening; voltage attributes are incomplete.",
        "path": "data/processed/05_connectivity/osm_power_grid_nigeria.csv",
    },
    "substations": {
        "description": "Mapped electricity substations represented as display points.",
        "source": "OpenStreetMap via Overpass API",
        "source_date": "2026-07-23",
        "license": "ODbL",
        "quality": "B",
        "quality_note": "Footprints are converted to centroids in the web bundle; electrical specifications are incomplete.",
        "path": "data/processed/05_connectivity/osm_power_grid_nigeria.csv",
    },
    "ports": {
        "description": "Nigerian seaports and offshore oil and gas terminals.",
        "source": "NGA World Port Index via HDX",
        "source_date": "2026-07-23",
        "license": "US government public data",
        "quality": "B",
        "quality_note": "Locations are stable, but facility attributes come from a 2017 source file.",
        "path": "data/processed/05_connectivity/world_port_index_nigeria.csv",
    },
    "minigrids": {
        "description": "Site-level off-grid and mini-grid inventory with technology, status, and reported capacity.",
        "source": "Nigeria SE4ALL Open Data Portal",
        "source_date": "2026-07-23",
        "license": "Public portal; explicit redistribution terms not stated",
        "quality": "A",
        "quality_note": "All current records are exact-site geocoded; not a complete solar-home-system registry.",
        "path": "data/processed/07_renewables/renewable_offgrid_minigrid_nigeria.csv",
    },
}


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


def status_bucket(props: dict[str, Any]) -> str:
    raw = str(props.get("status") or props.get("STATUS") or "").lower()
    if not raw:
        return "unknown"
    if any(value in raw for value in ("operat", "active", "in use", "commissioned")):
        return "operating"
    if any(value in raw for value in ("construction", "development", "pre-production")):
        return "development"
    if any(value in raw for value in ("proposed", "planned", "announced", "discovered")):
        return "proposed"
    if any(value in raw for value in ("mothballed", "cancelled", "shelved", "shut in", "retired")):
        return "inactive"
    return "other"


def empty_profile(name: str, sublayer_keys: list[str]) -> dict[str, Any]:
    return {
        "name": name,
        "mapped_records": 0,
        "counts": {key: 0 for key in sublayer_keys},
        "category_counts": {
            "resource": 0,
            "infrastructure": 0,
            "environmental": 0,
            "demand": 0,
            "connectivity": 0,
            "renewables": 0,
        },
        "capacity": {
            "power_mw": 0.0,
            "refinery_bpd": 0.0,
            "minigrid_kw": 0.0,
        },
        "status": {
            "operating": 0,
            "development": 0,
            "proposed": 0,
            "inactive": 0,
            "other": 0,
            "unknown": 0,
        },
    }


def update_profile(
    profile: dict[str, Any],
    category_key: str,
    sublayer_key: str,
    props: dict[str, Any],
) -> None:
    profile["mapped_records"] += 1
    profile["counts"][sublayer_key] += 1
    profile["category_counts"][category_key] += 1
    profile["status"][status_bucket(props)] += 1

    if sublayer_key == "power_plants":
        profile["capacity"]["power_mw"] += float(props.get("capacity") or 0)
    elif sublayer_key == "refineries":
        profile["capacity"]["refinery_bpd"] += float(props.get("capacity_bpd") or 0)
    elif sublayer_key == "minigrids":
        profile["capacity"]["minigrid_kw"] += float(props.get("capacity_kw") or 0)


def add_catalogue_and_state_profiles(
    bundle: dict[str, Any],
) -> None:
    """Add machine-readable catalogue metadata and state-level screening summaries."""
    sublayer_keys = [
        sublayer_key
        for layer in bundle["layers"].values()
        for sublayer_key in layer["sublayers"]
    ]
    state_geometries = []
    for state_feature in bundle["states"]["features"]:
        state_name = state_feature["properties"]["name"]
        state_geometry = shape(state_feature["geometry"])
        state_geometries.append((state_name, state_geometry, prep(state_geometry)))

    profiles = {"Nigeria": empty_profile("Nigeria", sublayer_keys)}
    for state_name, _, _ in state_geometries:
        profiles[state_name] = empty_profile(state_name, sublayer_keys)

    catalogue = []
    for category_key, layer in bundle["layers"].items():
        for sublayer_key, definition in layer["sublayers"].items():
            metadata = dict(CATALOGUE[sublayer_key])
            metadata.update(
                {
                    "key": sublayer_key,
                    "label": definition["label"],
                    "category": category_key,
                    "category_label": layer["label"],
                    "record_count": len(definition["data"]["features"]),
                    "download_url": f"{REPOSITORY_RAW}/{metadata['path']}",
                }
            )
            definition["metadata"] = metadata
            catalogue.append(metadata)

            for item in definition["data"]["features"]:
                geometry = shape(item["geometry"])
                if geometry.geom_type == "Point":
                    state_names = [
                        name
                        for name, _, prepared in state_geometries
                        if prepared.covers(geometry)
                    ]
                else:
                    state_names = [
                        name
                        for name, _, prepared in state_geometries
                        if prepared.intersects(geometry)
                    ]
                item["properties"]["_states"] = state_names
                update_profile(
                    profiles["Nigeria"],
                    category_key,
                    sublayer_key,
                    item["properties"],
                )
                for state_name in state_names:
                    update_profile(
                        profiles[state_name],
                        category_key,
                        sublayer_key,
                        item["properties"],
                    )

    for profile in profiles.values():
        for capacity_key, value in profile["capacity"].items():
            profile["capacity"][capacity_key] = round(value, 2)

    bundle["release"] = {
        "version": "0.2.0",
        "date": "2026-07-24",
        "title": "State Intelligence and Data Catalogue",
    }
    bundle["catalogue"] = catalogue
    bundle["state_profiles"] = profiles


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

    bundle = {
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
    add_catalogue_and_state_profiles(bundle)
    return bundle


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
