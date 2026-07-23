# Atlas methodology

The atlas is built as a reproducible geospatial evidence pipeline that converts publicly available datasets into a national-scale, multi-layer view of Nigeria's gas and associated energy system.

## Core design

The `v0.1` public atlas is organized around six implemented analytical layers:

- Resource: reserves, production, discoveries, and field-level site information.
- Infrastructure: pipelines, LNG terminals, refineries, and power assets.
- Environmental: flaring and protected-area context.
- Demand: industrial and demand-center locations relevant to gas consumption.
- Connectivity: roads, rail, ports, and grid infrastructure.
- Renewables: site-level off-grid and mini-grid assets.

Security is a planned seventh layer. Candidate sources are documented, but no
security dataset is currently processed, validated, or published in the map.

Each layer is stored and documented separately so users can combine them for different analytical questions.

## Processing logic

The workflow generally follows this pattern:

1. Download public data sources into `data/raw/`.
2. Normalize formats and metadata into `data/processed/`.
3. Merge, clean, validate, and standardize geospatial fields.
4. Publish final outputs to `data/final/`.

The scripts under `scripts/` are meant to be the reproducibility backbone for that pipeline.

The final public map bundle is generated from processed CSVs with `make atlas`
(or `python scripts/build_public_atlas_data.py`). For browser performance, that
build publishes motorway and trunk roads, simplifies display geometry to a
screening-appropriate tolerance, and retains the full-resolution major-road
table in `data/processed/`. Release checks in `tests/` verify the committed
bundle, expected counts, key schemas, and coordinate bounds.

## Data quality principles

A public atlas needs a transparent quality standard. This repository uses the following principles:

- Prefer source data with a public provenance trail.
- Record the exact date of access for each source.
- Preserve the original source's resolution and scope rather than silently over-claiming precision.
- Flag uncertain coordinates, status labels, and duplicate cross-layer matches.
- Separate “analysis-ready” data from “raw” downloaded inputs.

## Known limitations

The atlas should be used with these caveats in mind:

- Some facilities have point coordinates rather than footprints.
- Some status labels reflect reporting at a particular point in time and may not reflect the latest operational status.
- Several layers combine data with different spatial resolutions and precision levels.
- Public data sources are heterogeneous, so not every layer is equally current or complete.

## Why this matters for public use

For a wider audience, the project is not merely a collection of files. It is a reproducible analytical frame for asking questions such as:

- Where are Nigeria's gas assets, bottlenecks, and demand centers?
- Which industrial corridors are most relevant for gas-based development?
- Where environmental constraints intersect with infrastructure?
- How compatible are public datasets for national planning and research?

That framing is what makes the repository usable beyond a narrow technical audience.
