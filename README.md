# Nigeria Infrastructure Atlas

A national-scale, geospatial evidence atlas for Nigeria's infrastructure
system, including energy, transport, demand centres, connectivity, renewables,
population, settlements, electricity-access context, and environmental exposure.

## Quick start

- Clone the repository and install dependencies from `environment.yml`.
- Process or inspect the cleaned datasets in `data/processed/`.
- Open the canonical interactive atlas in `docs/index.html` or through GitHub Pages.
- View the public snapshot image at `outputs/maps/nigeria_public_asset_snapshot.png`.
- Reproduce the raw data workflow with the download and process scripts in `scripts/`.
- Read `docs/data_sources.md` before using the data for analysis.

## Why this repository exists

Nigeria Infrastructure Atlas is a public-interest, reproducible evidence repository for understanding how Nigeria's energy, transport, and infrastructure system is organized across multiple spatial layers.

It is designed to support:

- investors screening market adjacency, infrastructure corridors, and industrial demand centres
- academics producing reproducible spatial research on energy, infrastructure, and environmental risk
- students learning how raw public datasets become an analytical atlas
- practitioners working in planning, policy, field operations, and market intelligence

## What the atlas contains

The current public atlas is organized into seven published analytical layers:

1. Resource
2. Infrastructure
3. Environmental
4. Demand
5. Connectivity
6. Renewables
7. People & Access

A security layer is planned, but it is not part of the `v0.4` processed
dataset or public map. This boundary is intentional: the source register records
candidate security sources without presenting them as implemented evidence.

The public value of the atlas is not any single output file. It is the combination of transparent provenance, reproducible workflows, and a structured way to compare upstream resources with downstream infrastructure and demand.

## Current public-facing value

A live `v0.4` state-intelligence experience is available at
[diamonds10.github.io/Nigeria-gas-atlas](https://diamonds10.github.io/Nigeria-gas-atlas/).
It provides profiles for all 36 states and the FCT, state-specific shareable
links and GeoJSON downloads, and a searchable catalogue covering all 22
published map datasets. Normalized status and evidence-year filters apply
consistently to the map, search results, visible counts, shared URLs, and
downloads.

State profiles now include WorldPop 2025 population estimates and World Bank
DRE Atlas settlement-cluster, night-light, and grid-distance indicators.
Night-light detection is published only as an electricity-access screening
signal, not as a measured household electrification rate.

Developers can use the versioned, read-only static API at
[diamonds10.github.io/Nigeria-gas-atlas/api/](https://diamonds10.github.io/Nigeria-gas-atlas/api/).
API v1 publishes a manifest, catalogue, state profiles, ADM1 boundaries, and
one GeoJSON endpoint per public map layer without requiring an API key.

A ready-to-use public snapshot image is now available in [outputs/maps/nigeria_public_asset_snapshot.png](outputs/maps/nigeria_public_asset_snapshot.png). It presents a concise, state-labeled public atlas view with the current asset-count callouts for the main layer categories.

The snapshot image itself is explicitly framed as a public screening snapshot, not a complete operating registry. A companion benchmark summary JSON is also available in [outputs/maps/public_asset_benchmark_summary.json](outputs/maps/public_asset_benchmark_summary.json), highlighting the public mini-grid evidence strength, status distribution, technology mix, and geographic coverage.

Public evidence-quality signal from the current benchmark:

- 80 catalogued mini-grid and off-grid sites across 30 states and the FCT
- 52 operational, 13 under construction, 13 commissioned, 1 under
  rehabilitation, and 1 unknown
- 66 Nigeria SE4ALL records plus 14 named official-source additions
- 67 exact-site coordinates; 13 campus, community, or facility-level coordinates
- a 37-state/FCT coverage audit that distinguishes catalogued records from
  official programme-only evidence

For a concise repo-level interpretation of that benchmark, see [docs/public_evidence_quality.md](docs/public_evidence_quality.md).

For quick visual browsing, see also [outputs/maps/README.md](outputs/maps/README.md).

## Downloading the datasets

This repository is open source and the cleaned, analysis-ready datasets are already available in `data/processed/`.

If users want to reproduce the data ingestion from public source, they can run the downloader and processor scripts in `scripts/`:

- `scripts/01_resource/` for resource and production datasets
- `scripts/02_infrastructure/` for gas and power infrastructure
- `scripts/03_environmental/` for environmental risk and protected-area sources
- `scripts/04_demand/` for demand centres and industrial nodes
- `scripts/05_connectivity/` for power-grid and OSM-based connectivity data
- `scripts/07_renewables/` for mini-grid downloads and renewable asset intake
- `scripts/08_context/` for population, settlements, and electricity-access context

The general pattern is:

1. clone the repo
2. install the environment with `environment.yml` or your preferred Python environment
3. run the layer-specific `01_download_*.py` script to fetch raw source files
4. run the matching `0*_process_*.py` script to generate the processed CSV outputs
5. inspect `docs/data_sources.md` for provenance, source URLs, licenses, and caveats
6. rebuild the Pages map bundle with `make atlas` (or
   `python scripts/build_public_atlas_data.py`)

If readers only need the finished datasets, open the files in `data/processed/` directly or use the public snapshot image and benchmark JSON in `outputs/maps/`.

## How to use the datasets for applications

This atlas is best used as a public screening and planning foundation rather than an exhaustive operating registry.

Recommended usage patterns:

- infrastructure screening: combine `data/processed/02_infrastructure/` and `data/processed/05_connectivity/` to map corridors, stations, and grid assets
- energy access planning: combine `data/processed/07_renewables/` with
  `data/processed/08_context/` to screen mini-grid coverage against settlement
  population, night-light signals, and grid distance
- investment benchmarking: compare asset clusters, status distributions, and technology mixes across states using `outputs/maps/public_asset_benchmark_summary.json`
- environmental risk: overlay protected-area context with infrastructure to identify risk-sensitive zones
- multidisciplinary systems planning: use the repo’s structured layers together to align gas, power, demand, transport, and future telecom/data-centre expansions

Always cross-check with the original source and consult `docs/data_sources.md`
and `THIRD_PARTY_DATA.md` for each dataset’s license, access terms, attribution,
and limitations. The repository's CC0 dedication does not override third-party
data rights.

The current map palette has been chosen for clear UI visibility: distinct red, blue, green, and orange asset markers with soft state boundary contrast. It is suitable for public-facing screen and print use, while the `outputs/maps/README.md` notes how the snapshot should be interpreted.

The repository already contains a meaningful evidence base for screening and research, including:

- gas and oil infrastructure records
- power-producing plant and substation context
- demand-centre reference points
- environmental overlays, with security documented as a planned future layer
- a public-source off-grid inventory covering 80 named records across 30 states
  and the FCT, with source-specific status, capacity, coordinate precision, and
  operator context
- a first conservative intake framework for renewable off-grid and mini-grid assets beyond the currently structured mini-grid layer
- 154,319 processed settlement clusters, a compact 1,278-cell population/access
  web layer, and 2025 population estimates for every state and the FCT

Current verified public-facing asset snapshot:

- 193 oil/gas power-producing plant records
- 390 substation records
- 28 demand-centre records
- 80 catalogued mini-grid and off-grid records

The interactive map now surfaces state-level screening summaries, direct
processed-data downloads, quality grades, source dates, licensing caveats, and
visible counts for every published layer.

## Repository structure

- `data/raw/`: downloaded source files before cleaning
- `data/processed/`: normalized, analysis-ready datasets
- `data/final/`: publishable geospatial outputs
- `scripts/`: reproducible download and processing pipelines
- `tests/`: release-gate checks for schemas, counts, coordinates, and the web bundle
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
11. Check `docs/release_notes.md` for the current release boundary.
12. Read `THIRD_PARTY_DATA.md` before redistributing derived datasets.

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
- continued verified expansion of the audited public-source off-grid registry
- a consistent gallery of output maps and thumbnails for public browsing
- a concise release note describing what is verified versus provisional

For the detailed dataset inventory and limitations, see `docs/data_sources.md`.
