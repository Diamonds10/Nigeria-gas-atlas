# Asset visibility and map upgrade notes

## What the current atlas already shows

A fresh verification of the repository's existing processed data shows:

- 193 oil/gas power plant records in `data/processed/02_infrastructure/gogpt_oil_gas_plants_nigeria.csv`
- 390 substation records (plus 894 transmission line and 37 minor line segments, 1,321 rows total) in `data/processed/05_connectivity/osm_power_grid_nigeria.csv`
- 28 demand-center records in `data/processed/04_demand/demand_centers_nigeria.csv`

This means the atlas already contains a meaningful asset base for power-system visualization, but the public-facing map currently needs clearer labels and a more explicit asset summary.

## Recommended map polish

### Suggested public map caption

The map should display a compact asset-callout block such as:

- 193 power-producing plants
- 390 substations
- 28 demand centres
- 80 catalogued off-grid sites

This makes the visual layer legible to public readers before they open the source tables.

### 1. Add state names and state-level context

State names and state boundaries would materially improve map readability.

Recommended improvements:

- overlay Nigeria state boundaries as a light administrative reference layer
- label states with a readable, low-contrast font
- use a state name callout layer for the major clusters around Lagos, Rivers, Delta, Ogun, Kano, and Abuja
- add a small choropleth or circle legend showing concentrations by state where relevant

This would make the map more legible to investors, students, and non-technical readers who are looking for geography first, not asset codes.

### 2. Surface the key counts directly in the map legend

The map should visibly show the major asset counts not just as hidden data tables.

Recommended visible summary blocks:

- `power-producing plants`: 193
- `substations`: 390
- `demand centers`: 28
- `catalogued off-grid sites`: 80

These counts should appear in the map caption or legend area, not only in CSV files.

### 3. Separate gas-asset and power-system asset layers

The current atlas blends gas infrastructure, power generation, and demand centers. For a public map, that is a strength, but it should be set out more clearly.

Suggested visual treatment:

- gas resources and pipelines in one layer
- power plants and substations in another
- demand centers and industrial sites in a third
- security and environmental overlays as optional filters

## Renewable off-grid and minigrid opportunity

This is the most material missing addition for the repo's public value.

### What is publicly available right now

The strongest public sources identified so far are:

- Rural Electrification Agency (REA) Nigeria Electrification Programme (NEP)
- REA DARES
- Solar Power Naija
- World Bank mini-grid market outlook material
- EnergyData / public energy dashboards where they expose Nigeria-centric access-related dashboards

### What these sources help with

They provide strong evidence for:

- national off-grid and mini-grid policy direction
- deployment targets
- programme scale and financing posture
- public narrative around distributed renewable energy deployment

### What they do not yet provide cleanly

They do not yet appear to provide a single, publicly complete, geocoded national asset inventory with consistent facility-level coordinates, status, operator, and commissioning date.

That means the repo's most valuable next step is not simply to add more policy text. It is to build a structured asset inventory layer from public sources, even if that layer is initially partial and attribution-heavy.

## Recommended next data-build step

The next, high-value dataset to add should be:

- Nigeria distributed renewable assets layer
  - solar mini-grids
  - off-grid solar systems / SHS deployment footprints where public
  - REA-funded or donor-supported site lists
  - project status, technology type, and state

## Suggested public-facing interpretation

For external audiences, this layer should be described as:

- a renewable access asset layer for screening and planning
- a public-source evidence layer, not a full operating asset registry
- a partially observed, partially geocoded dataset that improves over time

This framing will make the atlas both more useful and more credible.
