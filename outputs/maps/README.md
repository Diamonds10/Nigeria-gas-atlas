# Public map outputs

This folder collects ready-to-share visual artifacts for the Nigeria Infrastructure Atlas.

The current snapshot is intentionally a public screening view. It is designed to show where major energy and distributed-energy assets appear in Nigeria, not to act as a complete or live operating registry.

## Current snapshot

- `nigeria_public_asset_snapshot.png` — the main public-facing atlas snapshot, showing the current state-labeled context for power-producing plants, substations, demand centres, and mini-grids.
- `public_asset_benchmark_summary.json` — a machine-readable benchmark summary for the public atlas, including counts, state coverage, capacity coverage, customer coverage, status mix, and geocode precision.

## What the current snapshot says

The snapshot is best understood as a public screening view rather than a complete operating registry. In the current benchmarked layer:

- 193 power-producing plant records are shown
- 390 substation records are shown
- 28 demand-centre records are shown
- 66 mini-grid records are shown

The mini-grid layer is especially useful because it provides a public, site-level, geocoded distributed-energy view with evidence on status and technology mix.

## Benchmark interpretation

The companion benchmark file shows that the current mini-grid evidence is materially stronger than a generic programme page:

- 66 sites across 26 states and the FCT
- 50 operational, 13 under construction, 2 commissioned, 1 unknown
- 43 solar and 22 hybrid mini-grid sites
- exact-site geocoding for all 66 records in the current processed layer

This means the public layer is strongest for:

- screening where distributed-energy assets appear
- benchmarking state-level coverage
- identifying likely project status and tech mix
- giving a transparent public picture of distributed-energy context

## What it does not claim

The public layer should not be interpreted as:

- a complete registry of all off-grid household solar systems
- a live commercial operating database
- a substitute for field verification or commercial diligence

## Intended usage

Use this map as a public summary figure for:

- investor-facing repo previews
- academic and student presentations
- practitioner briefing notes
- quick visual context before opening the processed CSV layer files

## Downloading and using the underlying datasets

The processed datasets are stored in `data/processed/` and are ready for analysis.

If users want to fetch the raw public inputs and reproduce the repo, run the layer-specific `01_download_*` and `0*_process_*` scripts in `scripts/`.

For applications, use this map for quick screening and use the processed CSV files for deeper asset, infrastructure, demand, or renewable planning analyses.
