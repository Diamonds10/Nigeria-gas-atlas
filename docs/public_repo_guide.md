# Public repository guide

This repository is designed to help four audiences use the same evidence base in different ways:

- Investors: screening infrastructure exposure, demand centres, and market adjacency.
- Academics: reproducible geospatial analysis across resources, infrastructure, environmental risk, connectivity, and security.
- Students: learning how to move from raw public datasets to a national-scale atlas with clear provenance.
- Practitioners: planning, policy, and field operations with a shared baseline of evidence.

## What the atlas contains

The atlas organizes Nigeria's gas-related system into six linked layers:

1. Resource
2. Infrastructure
3. Environmental
4. Demand
5. Connectivity
6. Security

Those layers can be used separately or combined into a national systems view.

## How to navigate the repository

- `README.md`: one-page project summary and repository map.
- `docs/executive_summary.md`: short public-facing summary.
- `docs/data_sources.md`: source-by-source provenance, dates accessed, and important limitations.
- `docs/methodology.md`: how the layers are built and interpreted.
- `docs/asset_visibility_and_map_upgrade.md`: map readability and asset-count visibility recommendations.
- `data/processed/`: cleaned and normalized datasets ready for analysis.
- `data/final/`: final publishable geospatial outputs.
- `scripts/`: reproducible pipeline code for downloading and processing raw inputs.
- `notebooks/`: exploratory workflows and visual analysis.

## Recommended reading order

If you are new to the repo, start here:

1. Read `README.md` for the project framing.
2. Review `docs/executive_summary.md` for a concise public explanation.
3. Review `docs/data_sources.md` before drawing conclusions.
4. Inspect the processed data in `data/processed/` to understand the most usable analysis-ready tables.
5. Use the scripts to reproduce or extend the workflow.

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

A public snapshot figure is available at [outputs/maps/nigeria_public_asset_snapshot.png](outputs/maps/nigeria_public_asset_snapshot.png). It is intended to provide a quick visual summary of the atlas's public asset context before readers dive into the layered CSV files.

The current processed data already contains a meaningful asset base for power-system visualization, including the major counts reflected in the map-upgrade notes:

- power-producing plants
- substations
- demand centres

The repo also now includes a site-level renewable distributed-access layer for mini-grids. Verified public-source evidence currently comprises 66 mini-grid sites across 26 states and the FCT, with operational, under-construction, and commissioned status context where publicly reported.

The missing public-facing improvement is not data absence; it is stronger visual communication of that asset context and a clearer narrative around what is confirmed versus provisional.
