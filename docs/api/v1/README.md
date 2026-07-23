# Nigeria Infrastructure Atlas static API v1

Base URL:

`https://diamonds10.github.io/Nigeria-gas-atlas/api/v1/`

This is a versioned, read-only static API served by GitHub Pages. It needs no
API key and supports normal HTTP caching. Start with `manifest.json`.

## Endpoints

- `manifest.json` — API contract, release information, filter fields, and layer endpoints
- `catalogue.json` — provenance, quality, licensing, and download metadata
- `schema.json` — JSON Schema for normalized public feature fields
- `state-profiles.json` — Nigeria and ADM1 screening summaries
- `states.geojson` — simplified Nigeria ADM1 boundaries
- `layers/{layer-key}.geojson` — one GeoJSON FeatureCollection per public map layer

## Filter fields

Layer features include:

- `_states`: state boundaries intersected by the public display geometry
- `_status_group`: `operating`, `development`, `proposed`, `inactive`, `other`, or `unknown`
- `_year`: relevant discovery, start, commissioning, or designation year when supported
- `_year_label`: the meaning of `_year` for that record

When applying a year cutoff, exclude records without `_year`. Do not assume an
undated record existed before the selected year.

## Stability

The `/api/v1/` contract will remain backward compatible within API version 1.
Dataset contents can change with atlas releases; inspect `atlas_release` and
source dates when reproducibility matters.
