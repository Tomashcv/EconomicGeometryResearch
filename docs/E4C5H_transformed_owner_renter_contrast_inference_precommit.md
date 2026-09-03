# E4C5H — transformed owner/renter contrast inference

E4C5G R1 froze transformed K/D cell-level point estimates and uncertainty for all eight owner/renter cohort cells per component.

E4C5H freezes and executes the within-age tenure contrast on the already-frozen state coordinates:

`RENTER_MINUS_OWNER_STATE`.

For K, the contrast is the difference of the two separately transformed state coordinates:

`ln(1 + K_renter/38640) - ln(1 + K_owner/38640)`.

It is **not** `ln(1 + (K_renter-K_owner)/38640)` and no raw difference is transformed directly.

For D, the state contrast is:

`(-D_renter) - (-D_owner)`.

Uncertainty is paired. Each of the five renter implicates is differenced with the owner implicate having the same implicate id. Each of the 999 renter sampling replicates is differenced with the owner replicate having the same replicate id. The exact frozen E4A2E sample-variance and MI-combination engine is then applied to those paired transformed differences.

Before contrast output is written, E4C5H recomputes the frozen E4C5G cell-level inference from the full-precision raw atomic sources and requires agreement with the serialized E4C5G outputs. This prevents a silent selector or engine drift.

No sign, magnitude, or significance criterion is a gate. No p-value or ratio is required for authorization. K-D cross-coordinate covariance, cross-coordinate scaling, geometry, dimensionality testing, Real Inflation estimation, and a final scalar remain unauthorized.
