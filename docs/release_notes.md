# Release notes

## v0.1.0 — Public Atlas

Released 2026-07-23.

This milestone establishes a reproducible, research-grade public atlas release.

### Included

- canonical Leaflet/GitHub Pages atlas with 9,531 public-map features across 15 sublayers
- deterministic `scripts/build_public_atlas_data.py` web-bundle build
- committed simplified ADM1 boundary input under `data/final/`
- automated schema, count, coordinate, JavaScript, and reproducibility checks
- GitHub Actions validation workflow
- six implemented layers: resource, infrastructure, environmental, demand,
  connectivity, and renewables
- 66-site mini-grid inventory across 26 states and the FCT
- machine-readable citation metadata and explicit third-party data-rights guidance

### Explicitly not included

- a processed security layer; candidate sources are documented for future work
- a complete live operating registry
- standalone solar-home-system coverage
- field verification or commercial diligence

### Canonical map

The static Leaflet application under `docs/` is the canonical public map. The
PNG snapshot remains the canonical print/static summary. Experimental Folium
outputs are not versioned release artifacts.

### Known follow-up work

- verify ambiguous redistribution terms with source publishers
- add the security layer only after source licensing and processing are complete
- extend renewable coverage beyond the current mini-grid inventory
- introduce dated dataset snapshots as sources are refreshed
