# E4C5I R1 — 12-decimal quantization-interval closeout repair

E4C5I attempt 1 failed on a serialized `SE = sqrt(combined_variance)` consistency check. R0 proved that exactly one SE row fails the fixed tolerance while every frozen identity is consistent with the independent 12-decimal serialization intervals.

R1 does not choose a larger tolerance from the observed residual. It replaces generic `math.isclose` validation with deterministic interval arithmetic derived from the file format itself.

Each serialized scalar must contain exactly 12 decimal places and represents its pre-serialization value within `±0.5e-12`.

Variance combination propagates the imputation- and sampling-variance intervals through `1.2 * imp_var + sampling_var`. SE maps the combined-variance interval through `sqrt`. OWNER/RENTER point arithmetic propagates renter and owner intervals through subtraction.

No source value, estimator, transform, variance engine, contrast definition, registry schema, or scientific authorization boundary changes.
