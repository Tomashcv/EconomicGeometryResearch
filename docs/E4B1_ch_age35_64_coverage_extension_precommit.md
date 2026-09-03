# E4B1 — C/H AGE35-64 Coverage Extension Preflight

## Parent

    c40bc11

E4B0 froze:

    C/H common coverage = 2/8 cells
    K/D/I coverage      = 8/8 cells

and authorized a C/H coverage extension preflight.

E4B1 opens no new CEX values.

Its only purpose is to freeze the exact extension before E4B2 is allowed to
estimate C/H for ages 35-64.

---

## 1. Only permitted mutation

The validated CEX estimator currently contains:

    AGE25_34_OWNER
    AGE25_34_RENTER

The only permitted scientific change in E4B2 is to extend that cohort
classifier to:

    AGE25_34 OWNER / RENTER
    AGE35_44 OWNER / RENTER
    AGE45_54 OWNER / RENTER
    AGE55_64 OWNER / RENTER

Everything else remains frozen.

---

## 2. Exact CEX tenure semantics

From the frozen cross-survey mapping:

OWNER:

    CUTENURE in {1,2,3}

RENTER:

    CUTENURE == 4

OTHER:

    CUTENURE in {5,6}
    missing
    unexpected

OTHER is excluded from the primary pseudo-cohort grid.

No alternate tenure mapping may be selected after the new C/H values are
opened.

---

## 3. Exact age bands

Reference age:

    AGE_REF

Bands:

    AGE25_34 = 25..34
    AGE35_44 = 35..44
    AGE45_54 = 45..54
    AGE55_64 = 55..64

The bands are inclusive and disjoint.

There is no data-dependent binning.

---

## 4. Point estimator remains frozen

Components:

    C_COST
    H_SERVICE

The validated E3B4A V2 / E3B3C4 semantics remain unchanged:

Interview quarters:

    221,222,223,224,231

Interview calendar filter:

    REF_YEAR = 2022
    REF_MONTH in 1..12

Interview population weight:

    FINLWT21 / 4 * MO_SCOPE / 3

Diary quarters:

    221,222,223,224

Diary population weight:

    FINLWT21 / 4

Diary weekly periodicity multiplier:

    13

Also unchanged:

    source selection
    hierarchy factor
    primary UCC mapping
    zero-spender inclusion
    missing cost -> zero
    negative cost preserved
    no clipping
    no winsorization
    no interview/diary record join

E4B1 does not authorize changing any of these.

---

## 5. BRR engine remains frozen

Full-sample weight:

    FINLWT21

Replicate set:

    WTREP01 ... WTREP44

Variance:

    V_BRR = (1/44) * sum((theta_r - theta_full)^2)

SE:

    sqrt(V_BRR)

Within every replicate:

    use the same replicate weight in numerator and denominator

    apply hierarchy factor inside the replicate

    sum component source contributions inside the replicate

Direct owner-renter inference:

    renter - owner

Direct ratio:

    renter / owner

Post-hoc source-variance addition remains prohibited.

The independent-SE shortcut for renter-owner differences remains prohibited.

---

## 6. Existing AGE25_34 results become invariance controls

E4B2 must re-estimate the old two cells using the expanded executor.

Those estimates are controls, not new discoveries.

The following must reproduce the frozen E3B4A V2 / E3B4C2 results within
the already-used numerical tolerance of 1e-8:

    AGE25_34 component full-sample estimates

    all AGE25_34 component BRR replicates

    all AGE25_34 renter-owner difference replicates

    all AGE25_34 renter/owner ratio replicates

If the old focal results move, E4B2 fails.

No repair or estimator mutation is permitted inside E4B2.

---

## 7. First genuinely new cells in E4B2

Only these six cells contain newly opened C/H economic values:

    AGE35_44_OWNER
    AGE35_44_RENTER

    AGE45_54_OWNER
    AGE45_54_RENTER

    AGE55_64_OWNER
    AGE55_64_RENTER

The 25-34 cells remain frozen controls.

---

## 8. Exact E4B2 output shape

Eight cohorts x two components:

    16 full-sample component rows

Four age bands x two components:

    8 renter-owner component comparisons

BRR denominator rows:

    8 cohorts
    x 2 sources
    x 45 weights (full + 44 replicates)
    = 720

Component replicate rows:

    8 x 2 x 44 = 704

Difference replicate rows:

    4 x 2 x 44 = 352

Ratio replicate rows:

    4 x 2 x 44 = 352

Inference summary:

    16 COMPONENT
    8 RENTER_MINUS_OWNER
    8 RENTER_TO_OWNER_RATIO

    total = 32 rows

---

## 9. Outcome-independent execution

E4B2 will not require any direction, magnitude or significance.

It may fail only for structural/inference integrity, including:

    source hash failure
    cohort parser failure
    empty cohort
    nonpositive denominator
    nonfinite estimate
    incorrect replicate set
    AGE25_34 invariance failure
    exact output-shape failure

Whatever the new 35-64 C/H estimates are, they must be preserved under the
frozen contract.

---

## 10. Boundary after E4B1

E4B1 PASS authorizes only:

    E4B2_FIRST_C_H_8_CELL_COVERAGE_EXECUTION_AUTHORIZED=1

Still prohibited:

    H_ACCESS invention
    five-component scaling
    five-component vector
    distance / norm
    dimensionality test
    five-dimensionality claim
    Real Inflation estimate
    final scalar
