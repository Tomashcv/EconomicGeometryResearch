# E4C5B — first K/D transform execution preflight

## Scope

E4C5B opens no target numerical K or D result.

Its purpose is to freeze the exact bounded source pool from which E4C5C may extract the already-frozen primary K and D target estimates.

Candidate result files are SHA-256 hashed, but their economic result contents are not parsed in E4C5B.

## Frozen transform parameters

K:

`K_STATE = ln(1 + K_FIN_MEAN / 38640)`

D:

`D_STATE = -D_PIRTOTAL_MEAN`

`PIRTOTAL` is already frozen as a fraction, so there is no `0.01` multiplier.

Both state coordinates are higher-is-better.

## Source pool

E4C5B discovers candidate target result artifacts only from:

1. tracked E4A result paths;
2. result paths referenced by tracked E4A/E4B3/E4C0/E4C1 scripts, docs, and metadata;
3. result paths referenced by the already-frozen K/D semantic-lineage files.

The pool is frozen by path and SHA-256 before E4C5C can inspect any target numerical value.

The pool is intentionally allowed to contain nonprimary K/D or nearby E4A artifacts. E4C5C must use a precommitted parser that selects only the primary `K_FIN`/`FIN` and `PIRTOTAL` estimands.

## Cohorts

The required target universe remains exactly:

`AGE_BAND × TENURE`

with four age bands and OWNER/RENTER, giving 8 cells per component.

A successful first point transformation must therefore produce 8 K rows and 8 D rows.

## Replicates and uncertainty

E4C5B does not assume a replicate table shape before source inventory.

E4C5C must inventory the frozen source structure and preserve whatever primary replicate architecture is already frozen.

If transformed uncertainty is later produced, the same fixed K reference and D unit/sign transform must be applied to the corresponding frozen replicate estimates.

No transformed ratio or difference inference is authorized merely by this preflight.

## Boundary

Dimensionless K and D still do not make the full coordinate system metric-ready.

Cross-coordinate scale, geometry, dimensionality testing, Real Inflation, and the final scalar remain unauthorized.
