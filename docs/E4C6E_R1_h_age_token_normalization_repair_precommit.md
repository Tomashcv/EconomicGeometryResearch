# E4C6E R1 — H age-token normalization repair

The failed E4C6E attempt and E4C6E R0 forensic remain immutable.

R0 established, without interpreting or emitting H estimate/SE/CI values, that the H selector failure is purely categorical: the frozen H source encodes age bands as `AGE25_34`, `AGE35_44`, `AGE45_54`, and `AGE55_64`, while the common registry uses the already frozen canonical labels `25-34`, `35-44`, `45-54`, and `55-64`.

R1 therefore changes only the source-representation bridge for H age labels:

- `AGE25_34` -> `25-34`
- `AGE35_44` -> `35-44`
- `AGE45_54` -> `45-54`
- `AGE55_64` -> `55-64`

No role, estimand, entity, K/D/I selector, estimator, state transform, uncertainty estimator, component definition, or registry schema changes. No numerical outcome, sign, magnitude, significance, or owner/renter result was used to select this repair.

The categorical R0 freezes the expected H source row identities after normalization as source data rows 2, 3, 6, 7, 10, 11, 14, and 15. These are structural row identities only.

After this R1 precommit is committed and pushed, the patched execution may re-open the already frozen value sources and attempt the original 40-row registry construction. Failure is preserved again rather than repaired in-place.
