#!/usr/bin/env python3
"""Generate one consistent static PNG thumbnail per published atlas category.

Reads the same GeoJSON bundle that powers the live GitHub Pages map
(docs/assets/atlas_data.json) rather than re-parsing the underlying CSVs, so
the gallery can never drift from what the interactive site actually shows,
and reuses that site's validated per-category colors. Re-run this after
scripts/build_public_atlas_data.py whenever the bundle changes.
"""

import json
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[1]
ATLAS_PATH = ROOT / "docs" / "assets" / "atlas_data.json"
OUTPUT_DIR = ROOT / "outputs" / "maps" / "gallery"

# Matches NIGERIA_BOUNDS in docs/assets/app.js. Some GEM pipeline routes (e.g.
# Trans-Sahara Gas Pipeline) legitimately extend far outside Nigeria -- see the
# "not exclusively Nigerian assets" limitation in docs/data_sources.md -- so
# every thumbnail is clipped to the country's extent rather than auto-scaling
# to whatever geometry happens to be in a layer.
NIGERIA_LON_RANGE = (2.5, 14.8)
NIGERIA_LAT_RANGE = (3.9, 14.0)

# Light-mode category colors, copied from docs/assets/app.css so the static
# gallery matches the interactive map's validated, colorblind-checked palette.
CATEGORY_COLORS = {
    "resource": "#9A640E",
    "infrastructure": "#007C90",
    "environmental": "#24763F",
    "demand": "#AD3F76",
    "connectivity": "#35548F",
    "renewables": "#545B00",
    "context": "#6B4C9A",
}

# Mirrors docs/assets/app.js's SHAPE_BY_SUB, mapped to matplotlib marker codes.
MARKER_BY_SUBLAYER = {
    "fields_oil": "o", "fields_gas": "D", "fields_mixed": "h",
    "lng_terminals": "h", "power_plants": "s", "refineries": "^",
    "gas_infrastructure": "D", "demand_centers": "D", "rail_stations": "s",
    "substations": "^", "ports": "*", "minigrids": "P", "settlements": "o",
    "population_access": ".",
}
DEFAULT_MARKER = "o"


def load_bundle() -> dict:
    return json.loads(ATLAS_PATH.read_text(encoding="utf-8"))


def to_geoseries(features: list) -> gpd.GeoSeries:
    return gpd.GeoSeries([shape(f["geometry"]) for f in features], crs="EPSG:4326")


def plot_sublayers(ax, category: dict, color: str) -> list:
    legend_handles = []
    for sub_key, sub in category["sublayers"].items():
        features = sub["data"]["features"]
        if not features:
            continue
        geoms = to_geoseries(features)
        geom_type = sub["geomType"]
        if geom_type == "point":
            marker = MARKER_BY_SUBLAYER.get(sub_key, DEFAULT_MARKER)
            size = 5 if len(features) > 500 else (12 if len(features) > 100 else 26)
            geoms.plot(ax=ax, color=color, markersize=size, marker=marker, alpha=0.85, linewidth=0)
            legend_handles.append(
                Line2D(
                    [0], [0], marker=marker, color="w", markerfacecolor=color,
                    markersize=8, label=f"{sub['label']} ({len(features)})",
                )
            )
        elif geom_type == "line":
            geoms.plot(ax=ax, color=color, linewidth=1.1, alpha=0.8)
            legend_handles.append(
                Line2D([0], [0], color=color, linewidth=2, label=f"{sub['label']} ({len(features)})")
            )
        else:  # polygon
            geoms.plot(ax=ax, facecolor=color, edgecolor="none", alpha=0.3)
            geoms.boundary.plot(ax=ax, color=color, linewidth=0.9, alpha=0.95)
            legend_handles.append(
                Line2D(
                    [0], [0], marker="s", color="w", markerfacecolor=color,
                    markersize=10, alpha=0.7, label=f"{sub['label']} ({len(features)})",
                )
            )
    return legend_handles


def render_category(states: gpd.GeoDataFrame, category_key: str, category: dict, output_path: Path) -> int:
    color = CATEGORY_COLORS.get(category_key, "#334155")
    fig, ax = plt.subplots(figsize=(9, 8.2), facecolor="#f8f7f4")
    ax.set_facecolor("#f8f7f4")
    states.plot(ax=ax, facecolor="#efeee9", edgecolor="#b9b6ac", linewidth=0.5)

    handles = plot_sublayers(ax, category, color)
    total = sum(len(sub["data"]["features"]) for sub in category["sublayers"].values())

    ax.set_title(f"{category['label']} — {total:,} mapped records", fontsize=15, weight="bold", color="#1c1a16", pad=12)
    ax.set_xlim(*NIGERIA_LON_RANGE)
    ax.set_ylim(*NIGERIA_LAT_RANGE)
    ax.set_aspect("equal")
    ax.set_axis_off()
    if handles:
        legend = ax.legend(handles=handles, loc="lower left", frameon=True, fontsize=8, title_fontsize=9)
        legend.get_frame().set_facecolor("white")
        legend.get_frame().set_alpha(0.92)
        legend.get_frame().set_edgecolor("#cbd5e1")
    ax.text(
        0.99, 0.01, "Nigeria Infrastructure Atlas — public screening view",
        transform=ax.transAxes, fontsize=7.5, color="#57534e", ha="right", va="bottom",
    )
    fig.tight_layout()
    fig.savefig(output_path, dpi=170, bbox_inches="tight")
    plt.close(fig)
    return total


def main() -> int:
    bundle = load_bundle()
    states = gpd.GeoDataFrame.from_features(bundle["states"]["features"], crs="EPSG:4326")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for category_key, category in bundle["layers"].items():
        output_path = OUTPUT_DIR / f"{category_key}.png"
        total = render_category(states, category_key, category, output_path)
        print(f"Saved {output_path} ({total:,} records)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
