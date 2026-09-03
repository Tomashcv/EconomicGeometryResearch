# E4C5 — K + D dimensionless transform preflight

## Scope

E4C5 is values-closed.

It reads no SCF microdata and no prior numerical K/D target-result table. Its purpose is to freeze the transform architecture before any transform parameter or transformed target value is opened.

## Common rules

Every state coordinate used later in geometry must be:

- dimensionless;
- higher-is-better;
- generated with the same formula across all age × tenure cells;
- independent of owner/renter direction, statistical significance, and later geometry.

The following are prohibited for semantic construction:

- z-scoring the eight target cells;
- min-max scaling the eight target cells;
- target-cell rank transforms;
- target-cell PCA or whitening;
- cohort-specific scale parameters.

## K — financial capital position

The frozen primary K evidence is the cohort-level `K_FIN_MEAN`, based on SCF `FIN`.

E4C5 preserves that estimand. It does **not** redefine K as the mean of record-level logged financial assets.

The proposed state transform is:

`K_STATE_g = ln(1 + K_FIN_MEAN_g / K_REF_FIN_USD)`

where `K_REF_FIN_USD` is a single reference scale common to every cohort.

### K reference scale

`K_REF_FIN_USD` is not chosen from the eight target cohort estimates.

It must be computed from the broad 2022 SCF reference population without AGE_BAND or OWNER/RENTER labels:

1. in each SCF implicate, retain valid positive survey weight and finite `FIN > 0`;
2. compute the weighted median of FIN;
3. average the five implicate-specific weighted medians arithmetically;
4. require the resulting reference scale to be positive and finite.

This makes the ratio `K_FIN_MEAN / K_REF_FIN_USD` dimensionless and unit-invariant when both the raw value and reference unit are converted together.

`ln(1+x)` is monotone and maps zero financial capital to zero.

## D — debt-service / leverage security

The frozen primary D evidence is `D_PIRTOTAL_MEAN`.

The state transform is:

`D_STATE_g = - PIRTOTAL_FRACTION_g`

The sign is already conceptually frozen: greater debt-service burden is worse, so the state coordinate is higher-is-better after negation.

Before any transformed D values are opened, E4C5A must verify the exact documented unit of `PIRTOTAL`.

- if the official variable is already a fraction, multiplier = `1`;
- if the official variable is documented in percent units, multiplier = `0.01`.

No target-sample fitted scale parameter is permitted.

`DEBT2INC` remains a secondary sensitivity and does not replace PIRTOTAL.

## Inference boundary

E4C5 computes no transformed values and no new standard errors.

When transformation is later authorized, the same frozen parameter must be applied to the full-sample cohort estimate and every corresponding frozen replicate estimate.

Any transformed contrasts or uncertainty must be derived from transformed replicate coordinates under a separately frozen inference contract.

## Geometry boundary

Dimensionless does not mean metric-ready.

After K reference-scale and D unit semantics are frozen, a separate step must decide how cross-coordinate metric scale is handled across K, D, H_ACCESS, and the two I subcoordinates.

Geometry, dimensionality testing, Real Inflation, and the final scalar remain unauthorized.
