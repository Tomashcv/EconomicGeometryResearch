# E4C5D — K/D replicate transform-domain feasibility audit

E4C5C R5R0 froze the exact cohort replicate inventory:

- 8 target cells per component;
- 999 replicate IDs;
- 7,992 K rows;
- 7,992 D rows;
- contrast rows excluded;
- no transformed replicate values computed.

E4C5D answers one narrow question before any transformed uncertainty calculation:

**Is the already-frozen point transform defined on every frozen cohort replicate estimate?**

## K

The point coordinate is already frozen as:

`K_STATE = ln(1 + K_FIN_MEAN / 38640)`

Its replicate-level mathematical domain would require:

`raw K_FIN_MEAN > -38640`.

Before inspecting the full replicate distribution, E4C5D freezes three exhaustive bins:

1. `raw <= -38640`: invalid for the frozen log transform;
2. `-38640 < raw < 0`: log-domain valid, negative raw replicate;
3. `raw >= 0`: log-domain valid, nonnegative raw replicate.

## D

`D_STATE = -PIRTOTAL` is linear. Any finite selected raw replicate is in its transform domain.

## Decision tree frozen before counts

If K has zero invalid replicates, E4C5E may evaluate whether direct replicate transformation is statistically appropriate given the already-frozen SCF multiple-imputation/replicate architecture.

If K has one or more invalid replicates, direct transformation of the full K replicate set is blocked by mathematics. E4C5E must then evaluate an analytic uncertainty method, such as delta propagation from the already-frozen raw combined variance, without changing the frozen K point transform.

E4C5D itself authorizes neither method.

The audit also checks replicate-ID alignment across all cells and between K and D, but computes no K-D covariance.

No owner/renter direction, significance, or effect magnitude is used as a selection gate. No cross-coordinate metric scale or geometry is authorized.
