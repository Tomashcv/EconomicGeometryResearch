# E4D0B — multiyear semantic + design comparability adjudication preflight

E4D0B freezes the adjudication method before any 2019↔2022 semantic conclusions are produced.

The candidate temporal pair remains 2019→2022. E4D0B does not yet declare 2019 comparable and does not freeze a common-year grid.

The adjudication works at the level of the five frozen numerical coordinates and the three source surveys. A year can enter the temporal state only if every required axis is PASS or, where explicitly allowed, VERSIONED_PASS.

PASS means the same frozen estimand is directly supported in both years. VERSIONED_PASS is narrower: the implementation or design may differ, but official evidence must show that an ex-ante year-specific bridge preserves the same frozen estimand. VERSIONED_PASS never permits fitting a bridge to observed 2019 economic values.

FAIL and UNRESOLVED both block E4D1.

The preflight adds an explicit REFERENCE_PERIOD_ALIGNMENT axis. Survey-wave labels are not assumed to be identical economic timestamps. In particular, CPS ASEC variables may mix current survey status and prior-calendar-year work-experience concepts; that timing must be preserved rather than silently relabeled.

For K, a nominal monetary variable cannot become temporally comparable until a price-level/reference-scale bridge is frozen before opening 2019 K values. The 2022 reference scale cannot be refit after seeing 2019.

Sampling-design differences are treated separately from estimand differences. A changed sample design is not automatically a semantic failure if official year-specific replicate/weight procedures validly estimate the same target, but such a case must be explicitly VERSIONED_PASS.

No interpolation, carry-forward, cross-year zero-covariance assumption, PCA, geometry, dimensionality, welfare interpretation, inflation-rate interpretation, or final scalar is authorized by this phase.
