# Public repository guide

This repository is designed to help four audiences use the same evidence base in different ways:

- Investors: screening infrastructure exposure, demand centres, and market adjacency.
- Academics: reproducible geospatial analysis across resources, infrastructure,
  environmental risk, connectivity, and renewables.
- Students: learning how to move from raw public datasets to a national-scale atlas with clear provenance.
- Practitioners: planning, policy, and field operations with a shared baseline of evidence.

## What the atlas contains

The `v0.1` public atlas organizes Nigeria's infrastructure system into six
implemented layers:

1. Resource
2. Infrastructure
3. Environmental
4. Demand
5. Connectivity
6. Renewables

Those layers can be used separately or combined into a national systems view.
Security is a planned extension and is not yet represented by a processed
dataset or public-map layer.

## How to navigate the repository

- `README.md`: one-page project summary and repository map.
- `docs/executive_summary.md`: short public-facing summary.
- `docs/data_sources.md`: source-by-source provenance, dates accessed, and important limitations.
- `docs/methodology.md`: how the layers are built and interpreted.
- `docs/asset_visibility_and_map_upgrade.md`: map readability and asset-count visibility recommendations.
- `data/processed/`: cleaned and normalized datasets ready for analysis.
- `data/final/`: final publishable geospatial outputs.
- `scripts/`: reproducible pipeline code for downloading and processing raw inputs.
- `scripts/build_public_atlas_data.py`: deterministic build for the canonical Pages map.
- `tests/`: automated release checks.
- `notebooks/`: exploratory workflows and visual analysis.

## Recommended reading order

If you are new to the repo, start here:

1. Read `README.md` for the project framing.
2. Review `docs/executive_summary.md` for a concise public explanation.
3. Review `docs/data_sources.md` before drawing conclusions.
4. Inspect the processed data in `data/processed/` to understand the most usable analysis-ready tables.
5. Use the scripts to reproduce or extend the workflow.
6. Rebuild the canonical web bundle with `make atlas`.

## Interpretation advice

This atlas is strongest when interpreted as a layered evidence platform, not a single definitive “truth file.”

A few practical rules:

- use point locations when assets are known but exact footprints are unavailable
- treat status labels as indicative rather than necessarily operationally current
- cross-check layer-specific gap areas with local administrative or facility-level records
- use the atlas as a screening and scoping tool rather than a substitute for field verification

## Public release expectations

For a public repository, the following need to be visible and easy to find:

- clear project scope
- data provenance and caveats
- reproducible workflow steps
- a simple path from raw inputs to outputs
- an explicit statement of what is known and unknown

This repository already has the data and processing structure to support that. The main remaining work is to make those strengths obvious to a broader external audience.

## Current map-readiness framing

A public snapshot figure is available at
[outputs/maps/nigeria_public_asset_snapshot.png](../outputs/maps/nigeria_public_asset_snapshot.png).
It is intended to provide a quick visual summary of the atlas's public asset
context before readers dive into the layered CSV files.

The current processed data already contains a meaningful asset base for power-system visualization, including the major counts reflected in the map-upgrade notes:

- power-producing plants
- substations
- demand centres

The repo also now includes a site-level renewable distributed-access layer for mini-grids. Verified public-source evidence currently comprises 66 mini-grid sites across 26 states and the FCT, with operational, under-construction, and commissioned status context where publicly reported.

A concise evidence-quality interpretation is provided in
[public_evidence_quality.md](public_evidence_quality.md). That note explains the
public-screening strength of the current layer while keeping the boundary clear:
it is not a complete registry of all off-grid solar activity.

## Downloading the datasets

The cleaned datasets are already available in `data/processed/` for direct analysis.

To reproduce or refresh data from public source, use the repo’s downloader and processor scripts in `scripts/`. For example:

- `scripts/02_infrastructure/01_download_gas_infrastructure.py`
- `scripts/02_infrastructure/02_process_gas_infrastructure.py`
- `scripts/07_renewables/01_download_minigrids.py`
- `scripts/07_renewables/02_process_minigrids.py`

This is the reproducible workflow:

1. clone the repository
2. create a Python environment from `environment.yml`
3. run the layer-specific `01_download_*` script
4. run the matching `0*_process_*` script
5. consult `docs/data_sources.md` for source provenance and license details

## Best uses for the datasets

This repository is best used as a screening and planning atlas for:

- infrastructure corridor and asset screening
- distributed energy access planning
- demand and industrial node analysis
- environmental risk overlay
- early-stage investment benchmarking
- multidisciplinary energy-infrastructure system planning

Use the public snapshot for quick visual context, and use the processed CSV files for deeper geospatial or tabular analysis.

The canonical public product is the custom Leaflet application in `docs/`.
Standalone Folium outputs may be useful for exploration, but they are not the
versioned release artifact.
