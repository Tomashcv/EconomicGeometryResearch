# E4D1BR2C R0 — static validator and selective row-projection repair

The first E4D1BR2C attempt failed before its precommit commit and before any 2019 microdata row was opened.

The immediate failure was a static-validator false positive. The validator used a global source substring assertion, `RMSP not in source`, even though the executor legitimately contained the diagnostic label `HOUSING_RMSP_OPENED=0`. AST inspection of the failed executor proves that the actual `idx[...]` field accesses were only `SERIALNO`, `NP`, `RELSHIPP`, and `AGEP`.

R0 also fixes a second static implementation issue discovered before any row was opened: `csv.DictReader` materializes all columns in each CSV row even when only a few keys are subsequently used. That implementation was broader than the frozen row-projection boundary.

The scientific design does not change. R0 preserves the same bridge, fields, role code, occupancy rule, one-to-one linkage gates, success/failure routing, and prohibitions on H estimation and weights.

Implementation changes only:
1. field-access validation is AST/projection based rather than global substring based;
2. row parsing uses a selective RFC4180-compatible record scanner that retains only the precommitted columns and discards all other field contents while scanning the record.

The hashes of all five failed uncommitted precommit artifacts are preserved before replacement.
