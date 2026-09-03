# E4C8 — cross-survey dependence and covariance feasibility precommit

E4C7 froze two diagonal economic metrics for the five-coordinate partial panel. Metric diagonality is a geometric design choice and is not a statement that estimator errors are statistically independent.

E4C8 freezes only the identifiability architecture for covariance. It does not open the numeric registry, compute any covariance, or fit dependence from the eight 2022 age×tenure cells.

The five coordinates occupy three survey blocks:

- ACS2022: H_ACCESS_SPACE_ROOMS_PER_PERSON
- SCF2022: K_FIN_MEAN_TRANSFORMED, D_PIRTOTAL_MEAN_STATE_TRANSFORMED
- CPS_ASEC_2022: I_FYFT_SHARE, I_SEARCH_SECURITY

This yields exactly two nontrivial same-survey pairs:
- K with D within SCF;
- I_FYFT with I_SEARCH_SECURITY within CPS.

Those two pairs are potentially identifiable because a dedicated joint replicate estimator can, in principle, preserve paired replicate information from the same survey design. E4C8 does not freeze either covariance formula yet.

The remaining eight coordinate pairs are cross-survey. Under the current unlinked architecture their sampling covariance is not identified by the available marginal point/SE registry. E4C8 does not replace those unknown covariances with zero and does not assert independent sampling designs merely because the surveys have different names.

Sampling-estimator covariance and economic-state dependence are distinct objects. Separation of survey samples cannot prove that the underlying economic concepts are independent.

The full 5×5 sampling covariance matrix is therefore not identified at E4C8. A partial block covariance architecture is potentially recoverable, but geometry remains unauthorized until the within-survey covariance estimators and a cross-survey uncertainty policy are separately precommitted.
