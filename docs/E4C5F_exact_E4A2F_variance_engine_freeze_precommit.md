# E4C5F — exact E4A2F variance-engine freeze

E4C5E found one and only one tracked E4A2F inference-engine candidate:

`scripts/E4A2F_first_scf_kd_inference_execution.py`

with SHA-256:

`1bba062e5db501ed1dd61435e7bcaafc0310338ac40fcc767b7cd8143ada4292`.

The transformed inference method family is already frozen: transform the atomic primary implicate and replicate estimates and then reuse the exact raw E4A2F variance engine.

E4C5F does **not** execute transformed inference. It freezes the engine itself.

The engine source code is the authority. E4C5F therefore inventories:

- all function definitions;
- assignment and return expressions involving imputation, implicates, sampling, replicates, variance, combined variance, SE, and related terms;
- numeric literals appearing inside those formula-bearing expressions;
- exact source line spans and source snippets;
- the complete engine SHA.

No variance coefficient may be re-derived from memory or survey convention when the source already encodes the operational estimator.

No target result-table data row is opened in E4C5F. No transformed replicate, transformed variance, CI, owner/renter contrast, K-D covariance, metric scale, geometry, or Real Inflation scalar is computed.

If the frozen source contains one coherent operational variance path for the E4A2F primary cohort estimator, E4C5G may precommit an execution that ports those exact formulas to transformed atomic estimates.
