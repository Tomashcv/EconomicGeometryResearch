# E4B2 — First C/H 8-Cell Coverage Execution

## Parent

    98e58b2

E4B1 froze the extension of the validated 2022 CEX C/H estimator from the
two AGE25_34 tenure cells to the complete four-age-band x two-tenure grid.

E4B2 is the first milestone allowed to open C/H values for ages 35-64.

---

## 1. Chronology

Before any new AGE35_64 C/H economic value is read:

1. the E4B2 execution contract is written;
2. the exact E4B2 executor is written;
3. all upstream hashes are rechecked;
4. the executor is committed;
5. the precommit is pushed.

Only then may the executor read CEX expenditure and WTREP values.

---

## 2. Frozen estimator base

E4B2 is derived from:

    scripts/E3B4C2_first_brr_execution.py

SHA-256:

    f806410e02ec880490614ddb579371c85b2116133a1592290245fd0eabb81763

The estimator semantics stay fixed.

The only scientific mutation is the cohort grid.

No mutation is authorized to:

    source families
    UCC mapping
    annualization factors
    calendar timing
    FINLWT21 weighting
    WTREP weighting
    BRR formula
    C_COST definition
    H_SERVICE definition
    tenure semantics

---

## 3. Exact cohort grid

    AGE25_34 OWNER
    AGE25_34 RENTER

    AGE35_44 OWNER
    AGE35_44 RENTER

    AGE45_54 OWNER
    AGE45_54 RENTER

    AGE55_64 OWNER
    AGE55_64 RENTER

OWNER:

    CUTENURE in {1,2,3}

RENTER:

    CUTENURE == 4

OTHER remains excluded.

---

## 4. AGE25_34 is an invariance control

AGE25_34 is not treated as a new discovery.

The expanded executor must reproduce the frozen existing results at:

    absolute tolerance = 1e-8

Required controls:

    full-sample C_COST and H_SERVICE estimates
    every one of 44 component replicates
    every one of 44 renter-owner difference replicates
    every one of 44 renter/owner ratio replicates

Failure of any control fails E4B2.

No estimator repair is permitted after seeing the new 35-64 values.

---

## 5. Newly opened economic values

The genuinely new C/H cells are exactly:

    AGE35_44 OWNER / RENTER
    AGE45_54 OWNER / RENTER
    AGE55_64 OWNER / RENTER

No new component is introduced.

---

## 6. BRR remains frozen

Replicates:

    WTREP01 ... WTREP44

Variance:

    (1/44) * sum((theta_r - theta_full)^2)

CI:

    theta +/- 1.96 * SE

Owner-renter differences are computed directly inside each replicate.

Ratios are computed directly inside each replicate.

Independent-SE shortcuts and post-hoc source-variance sums remain prohibited.

---

## 7. Exact expected output shape

    16 full-sample component estimates
     8 owner-renter component comparisons
   720 full+replicate source denominators
   704 component replicate estimates
   352 difference replicate estimates
   352 ratio replicate estimates

Inference summary:

    16 COMPONENT
     8 RENTER_MINUS_OWNER
     8 RENTER_TO_OWNER_RATIO

    total = 32

---

## 8. Outcome-independent gates

E4B2 PASS is structural.

PASS does not depend on:

    owner/renter direction
    effect magnitude
    SE magnitude
    CI excluding zero
    ratio excluding one
    agreement with an economic story

The six new cells are accepted whatever their values are, provided the
frozen estimator and inference engine execute correctly.

---

## 9. Geometry remains prohibited

Even after C/H reach 8/8 coverage, E4B2 does not make raw C/H/K/D/I values
commensurable.

Still prohibited:

    H_ACCESS invention
    five-component normalization
    five-component raw vector
    norm or distance
    dimensionality test
    five-dimensionality claim
    Real Inflation estimate
    final scalar

A PASS authorizes only the next frozen-results closeout:

    E4B3_FULL_8_CELL_FIVE_COMPONENT_COVERAGE_CLOSEOUT_AUTHORIZED=1
