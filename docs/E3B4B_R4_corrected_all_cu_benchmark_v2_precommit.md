# E3B4B R4 — Corrected 2022 All-CU Official Benchmark V2

## Parent

    e7ecd50

## Purpose

Test the repaired CEX point estimator against the exact same official 2022
all-consumer-unit benchmark used by the original E3B4B.

No benchmark target or tolerance is changed.

---

# Historical result preserved

Original E3B4B:

    STRUCTURAL_BENCHMARK_GATE = PASS
    TOTAL_APE_PCT             = 11.8697151538
    TOTAL_APE_LE_3PCT         = FAIL

    WEIGHTED_ABSOLUTE_ERROR_RATIO_PCT = 12.0274607725
    WEIGHTED_ERROR_LE_3PCT             = FAIL

    CATEGORIES_WITHIN_5PCT = 12 / 14
    AT_LEAST_10_OF_14_WITHIN_5PCT = PASS

    C_COST_APE_PCT    = 1.3009027038
    H_SERVICE_APE_PCT = 0.2376483752

    COMPONENT_APE_LE_5PCT = PASS

    E3B4B_ALL_CU_OFFICIAL_BENCHMARK = FAIL

That FAIL remains immutable.

---

# Proven implementation defect

Estimator V1 treated every Interview UCC as MTBI.

Subsequent frozen forensics established:

    MTBI = 390 UCCs
    ITBI =   8 UCCs
    EXPD = 247 UCCs

ITBI contains:

    5 Pensions and Social Security UCCs
    3 factor-4 finance-charge UCCs

Exact ITBI schema:

    value = VALUE
    month = REFMO
    year  = REFYR

VALUE_ is a topcode flag and is not the numerical point value.

---

# Corrected estimator V2

## MTBI

    value = COST
    REF_YR = 2022
    REF_MO = 1..12

## ITBI

    value = VALUE
    REFYR = 2022
    REFMO = 1..12

ITBI VALUE is normalized internally to the common point-value concept.

ITII is NOT appended.

## EXPD

Unchanged:

    value = COST
    weekly-to-quarter multiplier = 13

## Hierarchy factor

Applied UCC-by-UCC after source-specific mean estimation.

Frozen factor counts:

    factor 1 = 642
    factor 4 = 3

---

# Original official benchmark targets

The exact existing target file is reused.

Official total:

    72,967 USD

Derived project-component targets:

    C_COST    = 37,172 USD
    H_SERVICE = 19,056 USD

---

# Original gates — unchanged

## Structural

    exactly 14 major categories
    exactly 645 integrated UCCs
    zero unmatched source/family joins
    all category estimates finite
    all category estimates positive

## Total

    APE(total vs 72,967) <= 3.0%

## Weighted category replication

    sum_j |estimate_j - official_j|
    -------------------------------- <= 3.0%
          sum_j official_j

## Category count

At least:

    10 of 14 categories

must satisfy:

    APE <= 5%

## Project components

    C_COST APE    <= 5%
    H_SERVICE APE <= 5%

No outcome-based category exclusion is allowed.

No tolerance is modified after observing V2 values.

---

# Falsifiable repair predictions

These predictions are qualitative and mechanically implied by the diagnosed
missing ITBI source family.

Relative to V1:

    Personal insurance and pensions must increase materially.

    Finance-charge contributions to Education and Miscellaneous must no longer
    be omitted.

If the unchanged benchmark gates still fail:

    R4 = FAIL

and no cohort V2 interpretation is authorized.

---

# Interpretation restrictions

Even on PASS:

    observed expenditure != price inflation

and:

    REAL_INFLATION_ESTIMATED = 0
    REAL_INFLATION_ESTIMATION_AUTHORIZED = 0
    FINAL_SCALAR_AUTHORIZED = 0

A PASS only validates the corrected 2022 CEX point-estimator implementation.

Only then may corrected cohort point estimates be rerun.

