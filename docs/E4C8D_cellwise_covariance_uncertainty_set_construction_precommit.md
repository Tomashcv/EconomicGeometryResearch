# E4C8D — cellwise covariance uncertainty-set construction precommit

E4C8D opens only the already frozen E4C6E marginal standard errors and E4C8B within-survey covariances after this precommit.

All numeric consistency checks use exact rational arithmetic. Each finite decimal `se_state` is squared exactly to form a marginal sampling variance. The E4C8B exact numerator/denominator covariance is reused directly.

For each of the eight age×tenure cells, the specified covariance graph is the disjoint union of:

- one H singleton;
- one SCF 2×2 block containing K and D;
- one CPS 2×2 block containing I_FYFT and I_SEARCH_SECURITY.

The eight cross-survey off-diagonal pairs are unspecified.

Under this graph, a PSD completion exists exactly when each specified block is PSD. A constructive certificate is the frozen S1 block-diagonal zero-cross-survey completion. Therefore no SDP solver, nearest-PSD projection, optimization, correlation cap, or fitted completion is required to establish non-emptiness of U1.

The exact checks are:

- H variance >= 0;
- `var_K * var_D - cov_KD^2 >= 0`;
- `var_I1 * var_I2 - cov_I1I2^2 >= 0`.

S1 is a noncanonical sensitivity and an existence certificate only. Its zero cross-survey entries are not evidence of statistical or economic independence.

If any exact block-PSD check fails, E4C8D halts and preserves the failure. It must not clip or project frozen entries.

Geometry remains unauthorized. A pass authorizes only E4C9 preflight.
