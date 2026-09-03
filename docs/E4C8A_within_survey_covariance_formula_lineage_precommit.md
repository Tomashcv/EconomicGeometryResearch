# E4C8A — within-survey covariance formula + lineage precommit

E4C8 established that only two nontrivial off-diagonal sampling-covariance families are potentially identifiable under the current partial-panel survey architecture: K-D in SCF and I_FYFT-I_SEARCH_SECURITY in CPS. E4C8A0 recovered exact pre-existing replicate/implicate lineage without opening economic numeric rows.

E4C8A freezes the joint estimators before any covariance value is computed.

## SCF K-D

Use the already-frozen transformed-state tables from E4C5G. For each of the eight age×tenure cells, pair K and D by implicate and separately by replicate.

With M=5 implicates:

`Cov_imp(K,D) = sum_m[(K_m-Kbar_imp)(D_m-Dbar_imp)] / (M-1)`

With R=999 sampling replicate statistics:

`Cov_rep(K,D) = sum_r[(K_r-Kbar_rep)(D_r-Dbar_rep)] / (R-1)`

The combined covariance is the bilinear analogue of the frozen SCF combined-variance engine:

`Cov_combined(K,D) = (1 + 1/M) Cov_imp(K,D) + Cov_rep(K,D)`
`= (6/5) Cov_imp(K,D) + Cov_rep(K,D)`.

All K and D inputs are the already-frozen transformed state values. No new transformation is introduced.

## CPS I pair

Use E4A2D full-sample points and replicate estimates. Preserve the frozen state signs:

- FYFT: `+1`;
- SEARCH_SECURITY: `-1 × I_SEARCH_BURDEN_SHARE`.

Apply the state sign to both full-sample and replicate values before covariance. With R=160 CPS replicate estimates, freeze the bilinear analogue of the frozen replicate-variance engine:

`Cov(FYFT, SEARCH_SECURITY) = (4/160) sum_r[(FYFT_r-FYFT_full)(SEARCH_r-SEARCH_full)]`
`= (1/40) sum_r[...]`.

## Boundaries

E4C8A freezes formulas and pairing keys only. It computes no covariance value, does not use covariance sign or magnitude as a gate, does not infer economic-state dependence, and does not assume any of the eight cross-survey covariances are zero.

E4C8B may execute exactly 16 within-survey covariance cells: 8 SCF K-D and 8 CPS I-pair. Geometry remains unauthorized.
