# E4C9 — partial-state geometry + dimensionality preflight

E4C9 is structural only. It does not open the 40 numeric point rows and computes no distances, ranks, PCA objects, eigenvalues, or significance results.

## What geometry is allowed next

The current object is an eight-point 2022 cross-sectional cloud, each point represented by five frozen numerical coordinates:

1. H_ACCESS_SPACE_ROOMS_PER_PERSON;
2. K_FIN_MEAN_TRANSFORMED;
3. D_PIRTOTAL_MEAN_STATE_TRANSFORMED;
4. I_FYFT_SHARE;
5. I_SEARCH_SECURITY.

This is five numerical axes but only four represented concepts. C is absent, H is still a subcoordinate rather than a full H scalar, and I remains two primary axes. Therefore this is not a full CHKDI state vector.

E4C7 already froze two mandatory diagonal metrics. E4C9 preserves both and authorizes descriptive geometry only on difference vectors. Absolute-origin interpretation remains prohibited.

For two cells a and b, define delta = x_b - x_a. The primary geometry primitive is exact squared distance:

- M1: delta_H^2 + delta_K^2 + delta_D^2 + delta_I1^2 + delta_I2^2;
- M2: delta_H^2 + delta_K^2 + delta_D^2 + 1/2 delta_I1^2 + 1/2 delta_I2^2.

All 28 unordered cell pairs must be reported under both metrics. Four within-age owner/renter pairs and six adjacent-age within-tenure pairs receive named labels but are not selected using outcomes.

## Why inferential geometry is not yet allowed

E4C8D establishes a valid 5x5 sampling-covariance uncertainty set inside each cell. It does not establish the joint sampling covariance between two distinct age×tenure cells.

For an estimated difference x_b - x_a, uncertainty depends on:

Var(x_b - x_a) = Var(x_b) + Var(x_a) - Cov(x_b,x_a) - Cov(x_a,x_b).

The cross-cell covariance terms are not frozen or identified by E4C8D. E4C9 therefore prohibits distance SEs, distance confidence intervals, significance tests, and silent zero cross-cell covariance assumptions.

## Why intrinsic dimensionality is not yet allowed

Five numerical coordinates do not prove five economic dimensions, and four represented concepts do not prove four dimensions.

Exact affine rank of eight noisy estimated points is not a noise-aware intrinsic-dimension estimator: arbitrarily small estimation noise can make an algebraic rank maximal. E4C7 also prohibits PCA/whitening and data-fitted scale/rotation. No ex-ante singular-value/eigenvalue threshold or cross-cell inferential covariance architecture is frozen.

Accordingly, E4C9 does not authorize PCA, SVD-threshold dimension, eigenvalue-threshold dimension, or exact affine rank as an intrinsic-dimension claim.

A pass authorizes E4C9A descriptive point geometry only. It does not authorize real-inflation estimation or a final scalar.
