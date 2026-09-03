# E4C8B — within-survey covariance execution precommit

E4C8B executes only the two covariance families frozen in E4C8A:

- SCF K-D, eight age×tenure cells;
- CPS I_FYFT-I_SEARCH_SECURITY, eight age×tenure cells.

All arithmetic is exact rational arithmetic using finite decimal source strings converted directly to `Fraction`; no binary floating-point roundtrip is allowed for covariance values. The canonical outputs store exact numerator and denominator. A 30-decimal representation is emitted for inspection only and is not the canonical numeric representation.

For SCF, K and D must pair exactly by implicate (5 per cell) and replicate (999 per cell). The frozen formulas are:

`Cov_imp = sum((K_m-Kbar)(D_m-Dbar))/4`

`Cov_rep = sum((K_r-Kbar_r)(D_r-Dbar_r))/998`

`Cov_combined = (6/5)Cov_imp + Cov_rep`.

For CPS, the full-sample and 160 replicate values are state-oriented using +1 for FYFT and -1 for source I_SEARCH_BURDEN_SHARE, then:

`Cov = (1/40) sum((FYFT_r-FYFT_full)(SEARCH_SECURITY_r-SEARCH_SECURITY_full))`.

E4C8B gates only structural pairing completeness, uniqueness, exact expected counts, and numeric parsability. Covariance sign, magnitude, statistical significance, and owner-renter direction are not gates.

No cross-survey covariance is computed or set to zero. The resulting covariances describe sampling-estimator uncertainty, not economic-state dependence. Geometry remains unauthorized.
