# Public sources for renewable off-grid and mini-grid assets in Nigeria

**Status: active source audit (updated 2026-07-24).** The Nigeria SE4ALL portal
provided the initial 66 geocoded records, but a national state review confirmed
that it is not complete. Official REA/NEP/DARES, ECREEE, NEMSA, and beneficiary
institution records now provide a conservative 14-record supplement. The
combined registry and 37-state/FCT audit are documented in
`docs/data_sources.md` (Layer 7).

This note captures the most relevant public-facing sources that can support a future renewable distributed-energy asset layer.

## Priority public sources

### 1. Rural Electrification Agency (REA) – Nigeria Electrification Programme (NEP)

Source: https://nep.rea.gov.ng/

What it offers:

- programme-level framing for private-sector distributed renewable access
- national targets for households, MSMEs, and solar deployment
- public narrative on mini-grid, standalone solar, and productive-use deployment

What it does not yet offer cleanly:

- a single, consistent, geocoded, national asset registry with full coordinates and commissioning status

The lack of a complete public export is material: REA reported more than 200
mini-grids deployed during 2025, while the implemented SE4ALL source exposed
only 66 records. The atlas therefore publishes “catalogued public records,”
never an asserted total asset count.

### 2. REA – DARES

Source: https://nep.rea.gov.ng/dares.html

What it offers:

- explicit targets for distributed renewable-energy scale-up
- deployment goals for mini-grids and standalone solar systems
- strong policy and market context for off-grid and mini-grid planning

What it does not yet offer cleanly:

- a stable asset-list file with standardized geography for all projects

### 3. Solar Power Naija

Source: https://spn.rea.gov.ng/

What it offers:

- program documentation for off-grid solar connections
- policy and implementation framework for SHS and mini-grid participation
- public-facing market and developer program context

What it does not yet offer cleanly:

- a complete, machine-readable national asset geodatabase of deployed sites

### 4. World Bank mini-grid market outlook

Source: https://www.worldbank.org/en/topic/energy/publication/mini-grids-for-half-a-billion-people

What it offers:

- global and regional mini-grid market context
- evidence on scaling pathways, investment logic, and policy relevance
- useful framing for why mini-grids matter in Nigeria and other access-deficit markets

What it does not yet offer cleanly:

- Nigeria-specific facility-level asset inventory that can be mapped directly

## Why this matters for the atlas

For the Nigeria Infrastructure Atlas, this is the missing asset layer with the highest public value.

A renewable off-grid / mini-grid layer would materially improve the atlas because it would:

- connect infrastructure with underserved-demand geography
- show where distributed renewable energy can complement the grid
- give investors and practitioners a better view of “last-mile” electrification opportunity
- create a stronger bridge between gas infrastructure, power assets, and rural-energy access

## Recommended next repository step

The next recommended build is a derived asset layer that compiles the public ministry/program sources above into a structured file with at least:

- state
- location name or site description
- technology type
- programme name
- status
- source URL
- source date accessed
- coordinate if publicly available

This should be labeled as a public-source asset layer, not as a full commercial operating registry.
