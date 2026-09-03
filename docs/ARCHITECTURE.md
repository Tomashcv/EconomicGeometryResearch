# Architecture

## Research layers

The project is organized as a sequence of evidence layers rather than one monolithic model.

1. **Theory and contracts** — define the economic construct, target dimensions, admissible evidence and interpretation limits.
2. **Source acquisition and schema QA** — verify official sources, file identities, field definitions and survey structure.
3. **Estimator construction** — encode weights, replicate designs, imputation and cohort rules for each source family.
4. **Coordinate construction** — transform validated estimates into dimensionless economic-state coordinates.
5. **Descriptive geometry** — compare frozen state points under precommitted metrics without post-hoc ranking.
6. **Multiyear comparability** — prove that source definitions and estimators remain comparable before temporal geometry is opened.

## Why scripts retain stage identifiers

Names such as `E4C9A` and `E4D1D3` are provenance identifiers. They make it possible to distinguish a scientific execution from a repair, preflight, schema forensic or post-execution validator. Flattening them into generic names would remove useful chronology from an active research record.

## Data boundary

The public repository contains executable research logic and selected derived summaries. Source microdata and the large raw acquisition tree remain outside the repository.
