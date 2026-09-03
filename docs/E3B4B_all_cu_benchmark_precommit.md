# E3B4B — 2022 All-CU Official BLS Benchmark

## Parent

    1834c93

E3B4A produced the first cohort-specific CEX expenditure estimates.

Those magnitudes remain interpretation-blocked until the estimator is
benchmarked against official BLS published 2022 expenditure means.

---

# 1. Benchmark universe

Estimate:

    ALL CONSUMER UNITS

with no:

    age restriction
    tenure restriction
    income restriction
    positive-spender restriction

using the exact estimator frozen in E3B3C4.

---

# 2. Official 2022 targets

The official BLS 2022 all-consumer-unit means are frozen before execution.

Major categories:

    Food                                      9,343
    Alcoholic beverages                        583
    Housing                                  24,298
    Apparel and services                      1,945
    Transportation                           12,295
    Healthcare                                5,850
    Entertainment                             3,458
    Personal care products and services         866
    Reading                                     117
    Education                                 1,335
    Tobacco products and smoking supplies       371
    Miscellaneous                             1,009
    Cash contributions                        2,755
    Personal insurance and pensions           8,742

Sum:

    72,967

which equals the published Average annual expenditures value.

---

# 3. Derived project-component targets

The frozen primary C_COST definition contains:

    Food
    Alcoholic beverages
    Apparel and services
    Transportation
    Healthcare
    Entertainment
    Personal care products and services
    Reading
    Education
    Tobacco products and smoking supplies
    Miscellaneous

Published-target sum:

    C_COST_OFFICIAL_TARGET = 37,172 USD

Frozen H_SERVICE_CORE contains:

    Shelter
    Utilities, fuels, and public services

Published targets:

    Shelter                                    14,507
    Utilities, fuels, and public services       4,549

Therefore:

    H_SERVICE_OFFICIAL_TARGET = 19,056 USD

---

# 4. Why exact equality is NOT required

Published BLS tables and PUMD estimates may differ because:

    published tables use weighted integrated calendar-year estimates;
    PUMD apply respondent-confidentiality / non-disclosure adjustments;
    published tables are produced from confidential internal data.

Therefore exact equality is not a scientifically valid hard gate.

---

# 5. Frozen benchmark gates

These tolerances are frozen BEFORE executing the all-CU estimator.

## Structural

    exactly 14 major categories
    all 645 integrated UCCs represented
    zero source/family join failures
    all category estimates finite
    all 14 category estimates positive

## Total expenditure

    APE(total 72,967) <= 3.0%

## Weighted category error

Define:

    WEIGHTED_ABSOLUTE_ERROR_RATIO
      = sum_j |estimate_j - official_j|
        / sum_j official_j

Hard gate:

    <= 3.0%

## Category replication

At least:

    10 of 14

major categories must have:

    APE <= 5%

No outcome-based category exclusion is permitted.

## Project components

    APE(C_COST vs 37,172) <= 5%
    APE(H_SERVICE vs 19,056) <= 5%

---

# 6. Interpretation

E3B4B evaluates whether the estimator implementation is numerically credible.

It does NOT test:

    Real Inflation
    owner-vs-renter causal differences
    welfare
    capability preservation
    price inflation

If E3B4B passes:

    E3B4A_MAGNITUDES_VALIDATED = 1
    COHORT_POINT_ESTIMATE_INTERPRETATION_AUTHORIZED = 1

But:

    OBSERVED_EXPENDITURE_CHANGE_EQUALS_INFLATION = 0
    REAL_INFLATION_ESTIMATION_AUTHORIZED = 0
    FINAL_SCALAR_AUTHORIZED = 0

