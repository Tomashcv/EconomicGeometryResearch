# E4C5G — first transformed K/D cell-level inference execution

E4C5G is the first phase authorized to compute transformed K/D implicate values, transformed replicate values, and transformed cell-level uncertainty.

The method family and operational variance engine were frozen before these values were opened.

## Exact cell universe

Four age bands × OWNER/RENTER = eight cells per component.

Primary statistic IDs are fixed to `K_FIN_MEAN` and `D_PIRTOTAL_MEAN`. Only exact `COHORT` rows and exact OWNER/RENTER tenure labels are allowed.

## Frozen point coordinates

K uses `ln(1 + raw/38640)` and D uses `-raw`.

The cell point estimate remains the transform of the frozen raw pooled point. In particular, the nonlinear K point is **not** redefined as the average of the five transformed implicates.

## Frozen transformed uncertainty engine

For each cell, E4C5G transforms all five primary implicate estimates and all 999 primary sampling-replicate estimates. It then calls the frozen E4A2E `_sample_variance` helper for both variance components and uses the frozen `MI_MULTIPLIER = 1.2` combination rule. Combined SE is the square root of combined variance.

Before producing transformed outputs, E4C5G must reproduce the already-frozen raw E4A2F cell inference from the raw implicate and replicate tables using the exact E4A2E engine. This proves that row selection and the engine adapter are correct.

E4C5D already proved all 7,992 exact cohort K replicates are nonnegative. E4C5G additionally checks the 40 K implicate values. If any implicate lies outside `raw > -38640`, execution fails and is preserved; the transform and method may not be changed in response.

No owner/renter transformed contrast is computed. No K-D covariance, cross-coordinate metric scale, geometry, dimensionality test, Real Inflation estimate, or final scalar is authorized.
