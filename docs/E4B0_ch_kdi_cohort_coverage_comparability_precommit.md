# E4B0 — C-H-K-D-I Cohort Coverage + Comparability Preflight

## Parent

    52dac48

E3B4C3 has frozen C/H inference for 2022.

E4A2G has frozen K/D/I component inference for 2022.

E4B0 does not estimate anything new. It asks whether the five component
families currently have enough common cohort coverage and compatible scale
semantics to begin a joint geometry.

---

## 1. Frozen inputs only

C/H evidence is read from the already-frozen CEX result tables.

K/D/I evidence is read from already-frozen CPS/SCF result tables.

No raw CEX, SCF or CPS files are opened.

No point estimate, standard error, replicate estimate, ratio or contrast is
recomputed.

Numeric outcome magnitudes are not PASS gates.

---

## 2. Exact cohort grid

The intended pseudo-cohort grid is:

    AGE25_34 OWNER
    AGE25_34 RENTER

    AGE35_44 OWNER
    AGE35_44 RENTER

    AGE45_54 OWNER
    AGE45_54 RENTER

    AGE55_64 OWNER
    AGE55_64 RENTER

Eight cells in total.

---

## 3. Coverage means primary evidence availability

Coverage is not the same as having a scalar coordinate.

For each cell, the following frozen evidence must exist:

C:

    C_COST

H:

    H_SERVICE

K:

    K_FIN_MEAN

D:

    D_PIRTOTAL_MEAN

I:

    I_FYFT_SHARE
    I_SEARCH_BURDEN_SHARE

I requires both frozen primary estimands.

The result is a component-evidence coverage matrix only.

No I scalar is constructed.

---

## 4. Survey observational units are not identical

CEX:

    consumer unit

SCF:

    family

CPS ASEC:

    household classified through the reference person

Matching AGE_BAND × TENURE labels therefore do not create person-level or
household-level identity across surveys.

The permitted bridge remains:

    pseudo-cohort integration

Person-level joins remain prohibited.

---

## 5. Raw units are not commensurable

C_COST:

    annual dollar flow

H_SERVICE:

    annual dollar housing-service flow

K FIN:

    financial stock in dollars

D PIRTOTAL:

    ratio / debt-service burden

I:

    binary population shares

Therefore the following is prohibited:

    sqrt(C^2 + H^2 + K^2 + D^2 + I^2)

It would be driven by arbitrary measurement units rather than an economic
metric.

Also prohibited before a separate transformation contract:

    raw cross-dimension magnitude ranking
    raw coordinate norms
    raw Euclidean distances
    cross-dimension SE combination

---

## 6. Covariance boundary

K and D are estimated in SCF.

I is estimated in CPS ASEC.

C and H are estimated in CEX.

There is no joint microdata sample spanning C/H/K/D/I and no frozen
cross-survey joint covariance matrix.

Inference from one survey cannot be mechanically combined with inference from
another as if the estimates came from a common sample.

---

## 7. H boundary

The implemented H component is:

    H_SERVICE

E3B4C3 also explicitly records:

    H_ACCESS_IMPLEMENTED=0

Therefore H_SERVICE must not silently be re-labelled as a complete housing
access dimension.

This is an architectural limitation, not a failure of H_SERVICE estimation.

---

## 8. Expected structural finding is precommitted

From the already-frozen result scope, the expected coverage pattern is
declared before this audit executes:

C/H:

    exactly two covered cells
    AGE25_34 OWNER
    AGE25_34 RENTER

K/D/I:

    all eight cells

Therefore:

    full 8-cell five-component coverage = NO

but:

    AGE25_34 OWNER/RENTER five-component evidence coverage = YES

This coverage pattern is descriptive and is not a PASS/fail gate.

The audit must reproduce it exactly or fail as a lineage/schema problem.

---

## 9. Why we do not jump to a focal 5D geometry

Two focal cells are enough to say that all component families have evidence
for AGE25_34 owner and renter.

They are not enough to establish a five-dimensional economic geometry.

With only two common cohort points, a dimensionality claim would be
structurally underidentified.

The next correct milestone is therefore to expand C/H coverage to the other
three frozen age bands before choosing a cross-component scaling rule.

---

## 10. Authorization after PASS

A complete E4B0 PASS may authorize only:

    E4B1_C_H_AGE35_64_COVERAGE_EXTENSION_PREFLIGHT_AUTHORIZED=1

E4B1 must freeze the extension of the already-validated CEX point/BRR
estimator to:

    AGE35_44 OWNER/RENTER
    AGE45_54 OWNER/RENTER
    AGE55_64 OWNER/RENTER

before any new C/H values for those cells are opened.

Still prohibited:

    five-component raw vector
    five-component norm
    five-component distance
    dimensionality test
    five-dimensionality claim
    Real Inflation estimate
    final scalar
