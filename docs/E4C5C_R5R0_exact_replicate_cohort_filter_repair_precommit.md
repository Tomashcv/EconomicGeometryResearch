# E4C5C R5R0 — exact replicate cohort filter repair

The first R5 wrapper stopped before writing or staging any repository artifact. Its structural-check regex was over-escaped, so it could not parse an integer line that was present in the already-frozen E4C5C execution audit.

R5R0 preserves that wrapper failure and then performs the intended structural check correctly.

The frozen R4 inventory contains 999 replicate IDs and exactly 8 target cohort cells but 11,988 rows per component. That is 12 rows per replicate ID rather than the cohort contract's 8, with exactly 4 excess rows per replicate.

The replicate source field is named `tenure_or_contrast`. The R4 executor used a permissive mapper that accepts strings beginning or ending with OWNER/RENTER, so non-cohort contrast labels can be mapped into target cells.

R5R0 changes only the replicate-loop tenure filter: a replicate row is a target cohort row only when the normalized `tenure_or_contrast` value is exactly `OWNER` or exactly `RENTER`.

No numerical replicate value is used to choose this rule.

The 16 transformed K/D point estimates must remain byte-identical to R4. No replicate transform or transformed uncertainty is computed here.

After the exact 8-cell × 999-replicate inventory is frozen, E4C5D may audit the actual K replicate log-domain feasibility.
