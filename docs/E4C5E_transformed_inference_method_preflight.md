# E4C5E — transformed inference method preflight

E4C5D established that all 7,992 exact-cohort K replicate estimates are nonnegative. The frozen log transform is therefore defined on the complete K replicate set. D is linear and finite on all 7,992 D replicates.

This makes direct atomic transformation mathematically feasible, but mathematical feasibility alone does not authorize a new variance formula.

E4C5E freezes the method family before any transformed replicate or uncertainty value is computed:

1. Preserve the already-frozen transformed point estimate.
2. Transform each frozen primary implicate estimate on the state scale.
3. Transform each frozen primary sampling-replicate estimate on the state scale.
4. Feed those transformed atomic estimates through the **same frozen E4A2F imputation, sampling-replicate, and MI-combination variance engine** used on the raw scale.
5. Do not invent a new coefficient, denominator, replicate factor, or MI rule.

For K this preserves the nonlinear behavior of the already-frozen `ln(1+x/38640)` map rather than replacing it with a first-order delta approximation when direct transformation is feasible.

For D the sign flip is linear, so the direct transformed engine should be algebraically equivalent to the raw-scale variance, but E4C5E still requires the same engine path for consistency and auditability.

E4C5E does not execute transformed inference. It inventories the tracked E4A2F inference implementation and the headers of the frozen implicate/replicate/combined tables so the exact engine can be frozen next without guessing.

Owner/renter differences may later be recomputed from transformed cohort coordinates using aligned replicate IDs. Ratios are not automatically authorized on signed state coordinates. No K-D covariance, cross-coordinate scale, geometry, dimensionality test, Real Inflation estimate, or final scalar is authorized here.
