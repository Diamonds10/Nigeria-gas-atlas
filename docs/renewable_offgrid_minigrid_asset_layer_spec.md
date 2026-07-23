# Renewable off-grid and mini-grid asset layer specification

**Status: implemented (2026-07-23).** A 66-site mini-grid inventory was built at
`data/processed/07_renewables/renewable_offgrid_minigrid_nigeria.csv` via
`scripts/07_renewables/`, sourced from the Nigeria SE4ALL Open Data Portal's
GeoServer backend rather than compiled by hand from programme pages — see
`docs/data_sources.md` (Layer 7) for details and known gaps (no standalone SHS
layer yet; the portal's settlement-cluster electrification-planning datasets
are a candidate for a future extension, not yet built).

## Purpose

This document proposes the next high-value public dataset to add to the Nigeria Infrastructure Atlas: a distributed renewable energy asset layer for Nigeria.

The goal is to create a map-ready public-source layer for:

- solar mini-grids
- off-grid solar systems / solar home systems where geocoded public records exist
- donor or program-supported distributed-energy assets
- state-level screening of last-mile electrification opportunity

This layer should complement the existing gas, power, connectivity, and demand layers rather than replace them.

## Why this layer matters

The atlas already had a strong gas-resource and power-grid footprint. The
implemented mini-grid dataset and public map now provide the first renewable
distributed-access layer for investors, policymakers, lecturers, students, and
practitioners.

That missing layer would let the atlas answer questions such as:

- where are mini-grid and off-grid renewable assets clustered?
- which states or industrial corridors are most exposed to distributed energy opportunity?
- where do gas infrastructure and off-grid renewable access overlap or compete?
- which areas may need a stronger last-mile electrification strategy?

## Recommended public-source inputs

The strongest public sources to start from are:

1. REA – Nigeria Electrification Programme (NEP)
   - https://nep.rea.gov.ng/
2. REA – DARES
   - https://nep.rea.gov.ng/dares.html
3. Solar Power Naija
   - https://spn.rea.gov.ng/
4. REA public programme and project pages
5. World Bank mini-grid market and electrification publications
   - https://www.worldbank.org/en/topic/energy/publication/mini-grids-for-half-a-billion-people

## Proposed output dataset

Recommended output path:

- `data/processed/07_renewables/renewable_offgrid_minigrid_nigeria.csv`

Recommended output schema:

| Field | Description |
|---|---|
| asset_id | Stable unique asset identifier |
| asset_name | Project or site name |
| asset_type | mini_grid, solar_home_system, hybrid_mini_grid, productive_use, other |
| program_name | NEP, DARES, Solar Power Naija, donor, private programme, etc. |
| state | Nigerian state |
| lga | Local government area when available |
| community | Community or settlement name |
| developer | Developer or implementing company |
| owner_operator | Project owner or operator where known |
| technology | solar, solar_hybrid, diesel_hybrid, wind, other |
| status | planned, under_construction, commissioned, operational, decommissioned |
| capacity_kw | Installed or planned capacity in kW if public |
| customers_served | Number of households / MSMEs / users if public |
| financing_source | donor, commercial, concessional, public, mixed |
| latitude | Decimal latitude |
| longitude | Decimal longitude |
| geocode_precision | exact_site, community, lga, state, derived_centroid |
| source_name | Public source title |
| source_url | Public source URL |
| source_date_accessed | Date accessed |
| notes | Public-data caveats and interpretation notes |

## Suggested collection approach

The collection workflow should be public-source led and transparent:

1. Compile programme pages and project announcements from REA, NEP, DARES, and SPN.
2. Capture project names, locations, statuses, and any system size or customer metrics that are publicly reported.
3. Convert each entry into a standard record with a quality flag.
4. Geocode the facility to the best available precision.
5. Add a confidence column so users know whether a coordinate is exact, community-level, or derived.

## Geocoding rule

Coordinates should be added only when the source or a public geocoder can support them.

Use the following hierarchy:

1. exact parcel/site coordinate if publicly available
2. community or settlement centroid if a verified site location is not available
3. LGA centroid if only administrative resolution is known
4. state centroid only as a last-resort screening placeholder, clearly flagged as approximate

## Quality principles

This layer should be labeled as a public-source screening layer, not as a complete operating registry.

The following quality rules are recommended:

- do not imply exact site footprint if only a community or town-level coordinate exists
- preserve the public source date and URL for every row
- keep status fields clearly separated from operational certainty
- avoid over-claiming coverage if a program has only partial public geocoding
- mark all records with a confidence and precision label

## Recommended map usage

On the map, this layer should be shown as:

- a separate renewable access / distributed energy overlay
- optionally filterable by technology and status
- distinguishable from gas infrastructure and traditional grid assets

Suggested legend categories:

- operational mini-grid
- planned mini-grid
- off-grid solar / SHS deployment
- donor or programme-supported access asset

## Public-facing interpretation

The most useful framing for the repository is:

- this is an evidence layer for screening and public transparency
- it is useful for understanding where distributed renewable access is emerging
- it should be combined with the existing gas and power layers for a more complete systems view

## Next extension

The next step is to extend the implemented 66-site layer only where additional
public records have defensible site identity, provenance, and coordinate
precision.

That pilot should prioritize:

- state
- community/site name
- programme name
- status
- technology type
- coordinates if public
- public-source URL

This will create a credible foundation for a broader renewable access asset layer without overstating certainty.
