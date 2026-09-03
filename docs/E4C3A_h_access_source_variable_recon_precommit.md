# E4C3A — H_ACCESS source + variable reconnaissance precommit

## Decision boundary

This phase identifies promising public sources and variables. It does **not** select an H_ACCESS estimand and opens no microdata values.

## Primary reconnaissance source: 2022 ACS 1-year PUMS

The 2022 ACS PUMS is the strongest primary reconnaissance source because it is aligned to the project's 2022 cohort year and contains housing-unit variables directly on the housing record.

The source exposes:

- `HHLDRAGEP`: age of the householder;
- `TEN`: tenure;
- `WGTP`, `WGTP1` through `WGTP80`: housing-unit full and replicate weights;
- `GRPIP`: gross rent as percent of household income;
- `OCPIP`: selected monthly owner costs as percent of household income;
- `RMSP`: rooms;
- `BDSP`: bedrooms;
- `NP`: number of persons in the household;
- `PLM`, `BATH`, `KIT`, `SINK`, `STOV`: basic facility indicators;
- `MV` / `MIG`: move timing or mobility measures.

Direct `HHLDRAGEP` is especially useful because an AGE_BAND × TENURE housing-unit cohort can potentially be constructed without a person-level join.

ACS PUMS variance estimation supports `WGTP` with 80 housing replicate weights and the SDR variance factor `4/80`.

## Candidate implications

### Affordability

`GRPIP` and `OCPIP` are directly relevant but are tenure-specific measures. They cannot simply be concatenated into one estimand until a common semantic/harmonization contract is frozen.

### Space / crowding

`NP`, `RMSP`, and `BDSP` support direct crowding/space constructions such as persons per room. Threshold choice and eventual higher-is-better orientation remain unselected.

### Physical adequacy

ACS includes basic plumbing, bath, kitchen, sink, and stove indicators. These provide limited physical-adequacy evidence but are materially narrower than a dedicated housing adequacy index.

### Stability

`MV` and `MIG` indicate move timing/mobility, not involuntary displacement. E4C3A therefore does not authorize them as housing-security measures.

## Secondary reconnaissance source: 2023 AHS

The 2023 American Housing Survey is richer for H semantics.

Its PUF/codebook includes a recoded housing adequacy measure (`ZADEQ`) and housing-insecurity variables covering difficulty paying, missed payments, worry about forced moves, and move frequency.

However 2023 is not the frozen primary year 2022. It is retained as a secondary source or sensitivity path until an explicit year-alignment decision is precommitted.

Tenure-specific foreclosure/eviction items also cannot be mechanically pooled into a common owner/renter outcome without a harmonization contract.

## Source decision

E4C3A selects **ACS 2022 PUMS as the primary source for the next metadata-and-harmonization audit**, not as the selected H_ACCESS variable.

AHS 2023 remains a richer secondary route.

The next step must acquire/freeze the exact 2022 ACS variable codes/universes and decide, before opening microdata values, whether affordability, crowding, limited adequacy, or a multi-subcoordinate representation is scientifically preferred.

No H values or geometry are authorized.
