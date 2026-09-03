# E4C6E — partial observed-coordinate registry execution precommit

E4C6D froze the source tables, selectors, state orientation, point/SE fields, and exact 40-row registry schema before economic source rows were opened.

After this E4C6E precommit is committed and pushed, execution may open only those frozen source rows and construct the five-coordinate partial observed registry:

- H_ACCESS_SPACE_ROOMS_PER_PERSON
- K_FIN_MEAN_TRANSFORMED
- D_PIRTOTAL_MEAN_STATE_TRANSFORMED
- I_FYFT_SHARE
- I_SEARCH_SECURITY

There are exactly four age bands × two tenures for each coordinate, for 40 rows total.

Numerical handling is deliberately non-adaptive. Decimal source strings are parsed with Python Decimal. H, K, and D point-state values are reused as already frozen. I point-state values are the source point estimate multiplied by the already frozen state_sign (+1 for FYFT, -1 for SEARCH_BURDEN → SEARCH_SECURITY). Standard errors are reused from their frozen source fields and are never combined across coordinates here.

The execution gates only source identity, selector identity, exact shape, unique cells, finite decimal representation, and the definitional requirement that a standard error is nonnegative. Sign, magnitude, statistical significance, and owner/renter direction cannot affect success.

This registry remains partial: C is absent, H_ACCESS is not promoted to full H, I remains two primary subcoordinates, and no cross-coordinate covariance, metric, geometry, dimensionality test, real-inflation estimate, or final scalar is authorized.
