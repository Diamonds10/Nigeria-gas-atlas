# Release notes

## v0.2.0 — State Intelligence and Data Catalogue

Released 2026-07-24.

### Included

- reproducible profiles for Nigeria, all 36 states, and the FCT
- per-feature ADM1 memberships derived from the committed state boundaries
- state selection by dropdown or direct map click
- shareable state URLs and state-specific GeoJSON downloads
- national and state summaries for key asset counts and reported capacities
- searchable catalogue for all 15 public map datasets
- source, access-date, reuse, quality, limitation, record-count, and CSV-download metadata
- automated profile and catalogue consistency checks

### Interpretation boundary

State figures count public-map records whose display geometry intersects a
state. Lines and polygons can appear in multiple profiles, unit-level datasets
can contain several records at one facility, and offshore features remain
national rather than being forced into coastal states.

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
