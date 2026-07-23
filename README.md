# Nigeria Gas Atlas

A national-scale, geospatial evidence atlas for Nigeria's gas resources, infrastructure, environmental footprint, demand centres, connectivity, and security exposure.

## Why this repository exists

Nigeria Gas Atlas is a public-interest, reproducible evidence repository for understanding how Nigeria's energy and infrastructure system is organized across multiple spatial layers.

It is designed to support:

- investors screening market adjacency, infrastructure corridors, and industrial demand centres
- academics producing reproducible spatial research on energy, infrastructure, and environmental risk
- students learning how raw public datasets become an analytical atlas
- practitioners working in planning, policy, field operations, and market intelligence

## What the atlas contains

The repository is organized into six linked analytical layers:

1. Resource
2. Infrastructure
3. Environmental
4. Demand
5. Connectivity
6. Security

The public value of the atlas is not any single output file. It is the combination of transparent provenance, reproducible workflows, and a structured way to compare upstream resources with downstream infrastructure and demand.

## Current public-facing value

A ready-to-use public snapshot image is now available in [outputs/maps/nigeria_public_asset_snapshot.png](outputs/maps/nigeria_public_asset_snapshot.png). It presents a concise, state-labeled public atlas view with the current asset-count callouts for the main layer categories.

For quick visual browsing, see also [outputs/maps/README.md](outputs/maps/README.md).

The repository already contains a meaningful evidence base for screening and research, including:

- gas and oil infrastructure records
- power-producing plant and substation context
- demand-centre reference points
- environmental and security overlays where publicly available
- a verified site-level mini-grid inventory covering 66 sites across 26 states and the FCT, with public-source status, capacity, and operator context
- a first conservative intake framework for renewable off-grid and mini-grid assets beyond the currently structured mini-grid layer

Current verified public-facing asset snapshot:

- 193 oil/gas power-producing plant records
- 390 substation records
- 28 demand-centre records
- 66 mini-grid records

For the map layer specifically, the current asset visibility notes already identify the main public-facing upgrade path:

- add state names and state-boundary context
- surface visible counts for power-producing plants and substations
- clarify which layers are operational, policy-led, or provisional

## Repository structure

- `data/raw/`: downloaded source files before cleaning
- `data/processed/`: normalized, analysis-ready datasets
- `data/final/`: publishable geospatial outputs
- `scripts/`: reproducible download and processing pipelines
- `docs/`: methodology, provenance, and public-repo guidance
- `notebooks/`: exploratory and visualization workflows
- `outputs/`: generated maps and derived artifacts

## Recommended reading order

To understand the repository quickly, start in this order:

1. Read this README for the project framing.
2. Review `docs/executive_summary.md` for a concise public-facing orientation.
3. Review `docs/data_sources.md` for source provenance, dates accessed, and caveats.
4. Review `docs/methodology.md` for how the atlas layers are built and interpreted.
5. Use `docs/public_repo_guide.md` for a quick external-use guide.
6. Use `docs/asset_visibility_and_map_upgrade.md` for the map-visibility and asset-count improvement path.
7. Use `docs/offgrid_minigrid_public_sources.md` for public-source renewable off-grid and mini-grid context.
8. Use `docs/renewable_offgrid_minigrid_asset_layer_spec.md` for the proposed asset-layer schema.
9. Use `docs/renewable_asset_intake_workflow.md` for the first practical intake workflow.
10. Use `docs/citation_and_reuse.md` when you plan to cite or reuse the repository externally.
11. Check `docs/release_notes.md` for current status and public-readiness framing.

## Public repo interpretation

For external audiences, the repository should be treated as a transparent evidence platform rather than a single definitive answer file.

That framing matters because it keeps the atlas useful for:

- hypothesis generation
- market reconnaissance
- reproducible research
- screening and planning support

It should not be used as a substitute for:

- local verification
- asset-level commercial diligence
- legal or regulatory compliance checks

## Key caveats

Please treat outputs as an evidence scaffold rather than a verified operating registry.

Important caveats include:

- some records are point-based rather than footprint-based
- some status labels reflect reporting timing rather than current operational reality
- some layers are more complete and current than others
- dataset coverage and licensing terms should be reviewed before broad reuse

## Best next public-facing upgrades

To strengthen the repo for investors, academics, students, and practitioners, the most valuable next additions are:

- clearer state labels and state-boundary context on the main map
- visible counts for power-producing plants and substations in the map legend or caption
- a fuller, geocoded public-source renewable off-grid / mini-grid asset layer
- a consistent gallery of output maps and thumbnails for public browsing
- a concise release note describing what is verified versus provisional

For the detailed dataset inventory and limitations, see `docs/data_sources.md`.
