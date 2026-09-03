# E4C5C R0 — header estimate resolver repair

The E4C5C scientific precommit succeeded.

The first header-only pass opened only the point-source header and stopped before any data row was opened because three columns matched the generic estimate resolver:

- `point_estimate_raw`
- `point_estimate_state_oriented`
- `sampling_replicate_mean`

E4C5C itself applies the frozen state transformations. Therefore the point input must be `point_estimate_raw`.

Using `point_estimate_state_oriented` could double-apply the D sign orientation, while `sampling_replicate_mean` would substitute a replicate summary for the frozen full-sample point estimand.

R0 changes only header-column resolver precedence. It gives exact `POINT_ESTIMATE_RAW` first priority and, for the replicate source, prefers explicitly raw replicate estimate/statistic fields while excluding oriented and inferential-summary fields.

If the replicate header remains ambiguous, R0 stops again in header-only mode before any data row opens.

FIN/PIRTOTAL primary semantics, K reference 38640, D sign, cohort universe, outcome gates, and geometry boundaries are unchanged.
