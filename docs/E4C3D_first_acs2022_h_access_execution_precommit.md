# E4C3D — First ACS 2022 H_ACCESS execution

The estimator is frozen before any ACS 2022 housing microdata value is opened.

Primary record value: `RMSP / NP`.
Primary cohort estimator: WGTP-weighted mean of record-level rooms per person.
Sensitivity: `BDSP / NP`, predeclared and prohibited from replacing the primary because of observed outcomes.

OWNER is `TEN in {1,2}`; RENTER is `TEN == 3`; no-cash-rent is excluded.
Age is direct householder age `HHLDRAGEP`, using 25–34, 35–44, 45–54, 55–64.

Inference uses WGTP1..WGTP80 and SDR variance `(4/80) * sum((theta_r-theta_0)^2)`.
Renter-minus-owner and renter-divided-by-owner are computed directly inside each replicate.

The official national ACS housing ZIP must be SHA-256 hashed and its ZIP central-directory member manifest committed before any CSV member bytes are opened.

Direction, magnitude and statistical significance are not gates.
A successful result identifies a space-access subcoordinate only. It does not complete H or authorize geometry.
