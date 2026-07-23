# Renewable asset intake workflow

**Status: superseded (2026-07-23).** This manual page-by-page intake path was the
right plan when written, on the assumption that no clean geocoded source existed.
That assumption turned out to be wrong: the Nigeria SE4ALL Open Data Portal's
GeoServer backend has a real 66-site geocoded mini-grid inventory, now the primary
Layer 7 dataset at `data/processed/07_renewables/renewable_offgrid_minigrid_nigeria.csv`
(built by `scripts/07_renewables/01_download_minigrids.py` /
`02_process_minigrids.py` — see `docs/data_sources.md`, Layer 7). The `first_pass`
and template files this workflow originally produced have been removed as
superseded. What remains from this workflow is `01_download_rea_public_offgrid.py`
and `02_process_rea_public_offgrid.py`, kept only to produce
`rea_public_offgrid_sources_manifest.csv` — a provenance record of the programme
pages (REA, NEP, DARES, Solar Power Naija, World Bank) consulted, since those pages
still carry useful programme-level context even though they aren't a site inventory.

## Objective

This workflow provides a first practical intake path for adding renewable off-grid and mini-grid assets into the Nigeria Gas Atlas.

## Intake principles

- Use only public sources.
- Preserve the public source URL and date accessed.
- Keep a confidence level for every row.
- Separate programme-level records from site-level records.
- Do not treat community-level or LGA-level coordinates as verified facility footprints.

## Suggested workflow

1. Download public pages from REA, NEP, DARES, Solar Power Naija, and World Bank mini-grid materials.
2. Convert those pages into a `first_pass` CSV with rows for:
   - programme records
   - announced project records
   - site-level records where public locations are clear
3. Assign `geocode_precision` values of:
   - `exact_site`
   - `community`
   - `lga`
   - `state`
   - `derived_centroid`
4. Flag every record with notes so users know what is confirmed versus inferred.
5. Promote higher-confidence rows into a future cleaned and geocoded layer.

## Current first-pass output

The repository now includes a starter intake file:

- `data/processed/07_renewables/rea_public_offgrid_first_pass.csv`

That file is intentionally conservative and public-facing. It should be treated as a screening intake rather than a definitive asset registry.
