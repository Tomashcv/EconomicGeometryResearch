# E4C4 — I employment / labor-market security representation

## Scope

E4C4 is values-closed.

It does not read CPS microdata, prior I result tables, new replicate estimates, or owner/renter outcomes. It uses only frozen semantic lineage.

## Conceptual target

The current I target is:

`EMPLOYMENT_AND_LABOR_MARKET_SECURITY`

The concept is not assumed to be one-dimensional merely because the project uses the label `I`.

## Current operating primary representation

E4C4 retains two primary subcoordinates.

### 1. FYFT attachment

`I_FYFT_SHARE = 1[WEWKRS == 1]`

Higher is better.

This measures strong full-year/full-time labor-force attachment under the already-frozen CPS semantic definition.

### 2. Search security

The frozen raw search burden is:

`1[WEUEMP in {2,3,4,5,6,7}]`

Burden is worse. The state-oriented representation is therefore the negative of search burden:

`I_SEARCH_SECURITY = - SEARCH_BURDEN`

Higher is better.

No new numerical values are computed in E4C4.

## Sensitivities retained

The previously defined long-search burden using `WEUEMP in {6,7}` remains a sensitivity.

The previously defined any-work share using `WRK_CK == 1` remains a sensitivity.

Neither replaces the two primary subcoordinates in this phase.

## Why no I scalar

An equal-weight average of FYFT attachment and search security has no frozen theoretical justification.

Fitting weights, PCA, or whitening on the same eight target AGE_BAND × TENURE cells would make semantic construction depend on the target sample and potentially on the geometry we later want to test.

Therefore:

- no equal-weight I scalar;
- no target-cell-fitted weights;
- no PCA on the eight target cells;
- no cross-survey whitening;
- no scalar is required for the project to progress.

If a scalar I is later needed, it requires either predeclared theory weights or an independent reference/training sample.

## Dimensionality consequence

Five conceptual labels do not imply five numerical coordinates.

The operating state may contain both I subcoordinates, so the eventual coordinate count may exceed five.

Both I primaries are already dimensionless, but that does not make them geometry-ready: relative metric scale across I, H_ACCESS, K, and D must still be frozen independently before geometry.

## Next step

E4C4 authorizes E4C5 to freeze dimensionless, monotone, higher-is-better transforms for K and D and to define the remaining metric-scale readiness rules.

No geometry, dimensionality result, Real Inflation estimate, or final scalar is authorized here.
