# Renewable asset intake workflow

**Status: implemented as a hybrid intake (updated 2026-07-24).** The Nigeria
SE4ALL WFS supplies 66 structured source records. A state-by-state audit showed
that this omits documented assets, including Bayero University Kano. The current
processor therefore merges that source with
`data/curated/07_renewables/verified_public_offgrid_supplement.csv` and writes
both the 80-record canonical registry and a 37-state/FCT coverage audit.

## Objective

This workflow provides a first practical intake path for adding renewable off-grid and mini-grid assets into the Nigeria Infrastructure Atlas.

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

## Current outputs

- `data/processed/07_renewables/renewable_offgrid_minigrid_nigeria.csv`
- `data/processed/07_renewables/minigrid_state_coverage_audit.csv`

Only named records with defensible public evidence and usable location
precision enter the map. Programme agreements, tenders, and announced targets
remain coverage-audit evidence until commissioning and location can be verified.
