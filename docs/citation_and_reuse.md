# Citation and reuse guidance

## Recommended citation

If you use this repository in research, teaching, or public-facing work, the recommended approach is to cite the repository as a whole and the specific dataset or layer used.

Suggested format:

Nigeria Infrastructure Atlas contributors. 2026. *Nigeria Infrastructure
Atlas*, version 0.1.0. GitHub. Accessed YYYY-MM-DD.

The repository also includes machine-readable citation metadata in
`CITATION.cff`.

For a layer-specific citation, cite the relevant source dataset listed in `docs/data_sources.md` and the derived repository file used in your analysis.

## Reuse guidance

This repository is a derived public-data product. Reuse should follow three principles:

1. Preserve source provenance.
2. Respect the original source license and redistribution terms.
3. Disclose that derived outputs may be approximate or incomplete.

The root CC0 dedication applies only where the repository contributors hold the
necessary rights. It does not relicense third-party source data. Review
`THIRD_PARTY_DATA.md` and the source-specific terms in `docs/data_sources.md`
before redistribution or commercial use.

## Attribution expectations

When reusing files, please attribute:

- the repository name
- the relevant source dataset(s)
- the date of access or publication window
- any known limitations that affect interpretation

## Best practice for downstream use

For public-facing or external reporting:

- do not imply that a point coordinate is a verified facility footprint unless the source supports that claim
- distinguish between analysis-ready and raw data
- pair repository outputs with field verification where accuracy matters
