# E4C5I R0 — serialized-precision algebra forensic

E4C5I attempt 1 was precommitted and failed on the first cell-level `SE = sqrt(combined_variance)` closeout check.

The E4C5G and E4C5H result tables serialize inferential scalars to 12 decimal places. E4C5I attempt 1 parsed those rounded strings back to binary floats and then imposed an absolute tolerance of `2e-11`. A nonlinear square-root identity can legitimately differ by slightly more than that after the variance and SE have each been rounded independently.

R0 does not loosen the threshold based on the observed residual. Instead it freezes a serialization model from the file format itself: a 12-decimal value represents its pre-serialization value within half of one `1e-12` quantization unit.

The forensic checks whether the frozen outputs are algebraically compatible with the original identities under those deterministic quantization intervals. It also records how many rows fail the old fixed tolerance.

If all frozen rows are interval-consistent while the old tolerance rejects at least one row, the failure is classified as a closeout serialization-validation bug rather than an estimator, transform, or uncertainty failure.

R0 does not modify E4C5I and does not authorize a repair. Any R1 repair must be based on the predeclared interval arithmetic, not on the largest residual observed here.
