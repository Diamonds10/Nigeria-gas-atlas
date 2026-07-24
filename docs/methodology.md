# Atlas methodology

The atlas is built as a reproducible geospatial evidence pipeline that converts publicly available datasets into a national-scale, multi-layer view of Nigeria's gas and associated energy system.

## Core design

The `v0.4` public atlas is organized around seven implemented analytical layers:

- Resource: reserves, production, discoveries, and field-level site information.
- Infrastructure: pipelines, LNG terminals, refineries, and power assets.
- Environmental: flaring and protected-area context.
- Demand: industrial and demand-center locations relevant to gas consumption.
- Connectivity: roads, rail, ports, and grid infrastructure.
- Renewables: site-level off-grid and mini-grid assets.
- People & Access: population, settlement, night-light, and grid-distance
  screening context.

Security is a planned layer. Candidate sources are documented, but no
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

## State intelligence method

The public build assigns each display feature to every ADM1 boundary its
geometry intersects. Point features normally belong to one state; pipelines,
roads, railways, grid lines, and protected areas may intersect several states.
Offshore features remain in the Nigeria profile but are not artificially
assigned to a coastal state.

State profiles therefore report **public-map records intersecting a state**,
not unique facilities or official administrative statistics. Power totals sum
unit-level reported capacity, refinery totals sum reported nameplate capacity,
and mini-grid totals sum records with published capacity. These summaries are
appropriate for screening and comparison but require source-level review before
operational or investment use.

## Off-grid registry and state coverage audit

The renewable layer merges 66 structured Nigeria SE4ALL records with a
conservative 14-record supplement drawn from named official REA/NEP/DARES,
ECREEE, NEMSA, and institutional evidence. Stable asset IDs prevent duplicate
append operations. Each supplementary record preserves evidence level,
coordinate source, and whether its point is exact-site, facility, campus, or
community precision.

The accompanying audit covers all 36 states and the FCT. It distinguishes:

- states with one or more named catalogued public records;
- states with official programme or procurement evidence but no verified,
  geocoded commissioned record;
- public-evidence gaps.

Counts are therefore labelled **catalogued mini-grid and off-grid sites**. Zero means the
implemented sources did not yield a verified map record; it never establishes
that a state has no off-grid assets. Programme announcements and tenders are
not promoted to asset records until location and delivery status are supported.

## Population, settlement, and access context

WorldPop v3.0 supplies 2025 state population estimates. The World Bank Nigeria
Distributed Renewable Energy Atlas supplies settlement clusters, modelled
population, mapped-building counts, night-light detection, and distances to
transmission and grid-light targets.

The processing pipeline drops the source's large polygon geometry for the
analysis-ready settlement table and retains centroid coordinates and selected
planning attributes. It then creates:

- a complete 154,319-row settlement-cluster table;
- a 0.25-degree, population-weighted grid for responsive national mapping;
- the 40 highest-population settlement records per state for place-level display;
- a 37-row state summary joined to WorldPop totals.

The night-light population share is the share of modelled settlement
population located in clusters where the source reports a night-light signal.
It is useful for comparative screening, but it is **not** a household survey,
an official electrification rate, or proof that every person in a lit cluster
has electricity access. Conversely, no detected night light does not prove
that a settlement is wholly unelectrified.

## Catalogue quality grades

The website catalogue uses three concise screening grades:

- A: authoritative or exact-site source geometry suitable for strong public screening
- B: usable public geometry with material currency, completeness, or attribute caveats
- C: derived or partly approximate compilation requiring closer source review

Grades describe fitness for public screening. They are not certifications of
accuracy, legal reuse, or commercial reliability.

## Status and time filters

Source status labels are preserved and also mapped into six interface groups:
operating, development, proposed, inactive, other, and unknown. The normalized
group is stored as `_status_group` on every public API feature.

Time filtering is intentionally conservative. `_year` is populated only where
a layer supports a defensible discovery, start, commissioning, or designation
year, and `_year_label` records that meaning. When a cutoff is enabled, the
atlas includes only dated records at or before the selected year. Undated
records are excluded rather than silently assumed to have existed historically.

## Static API and filtered downloads

API v1 is generated with the map bundle and served from `docs/api/v1/`. It
contains a manifest, catalogue, state profiles, ADM1 boundaries, and one
GeoJSON FeatureCollection per map layer. Browser-generated national and state
downloads use the same status and time predicates as the visible map and record
the active selection in `atlas_selection`.

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
