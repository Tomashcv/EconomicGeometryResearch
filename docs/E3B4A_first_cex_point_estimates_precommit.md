# E3B4A — First CEX Cohort Point Estimates

## Parent

    8d1a267

## Authorization

Frozen parent state:

    POINT_ESTIMATOR_CONTRACT_FROZEN = 1
    COST_VALUES_AUTHORIZED = 1
    E3B4A_FIRST_CEX_POINT_ESTIMATES_AUTHORIZED = 1

This is the first milestone permitted to inspect CEX COST observations.

---

# 1. Target year

    calendar year 2022

No other year is estimated.

---

# 2. Frozen cohorts

Primary young comparison:

## AGE25_34_OWNER

    25 <= AGE_REF <= 34
    CUTENURE in {1,2,3}

## AGE25_34_RENTER

    25 <= AGE_REF <= 34
    CUTENURE = 4

Other tenure codes are excluded.

Cohort definitions may not be altered after COST inspection.

---

# 3. Frozen components

Only UCCs already frozen as:

    C_COST_PRIMARY
    H_SERVICE_CORE

are estimated.

Frozen counts:

    C_COST_PRIMARY = 435 UCCs
    H_SERVICE_CORE = 99 UCCs

Total primary UCCs:

    534

No pending or excluded UCC class enters E3B4A.

---

# 4. Interview estimator

Calendar-year source files:

    221
    222
    223
    224
    231

Family denominator:

    popwt_i
      = FINLWT21_i / 4
        * MO_SCOPE_i / 3

MTBI expenditures restricted to:

    REF_YR = 2022
    REF_MO in 1..12

For each cohort g and Interview UCC j:

    numerator_gj
      = sum(COST_r * FINLWT21_i)

    raw_mean_gj
      = numerator_gj / population_g

---

# 5. Diary estimator

Calendar-year source files:

    221
    222
    223
    224

Family denominator:

    popwt_i = FINLWT21_i / 4

For each cohort g and Diary UCC j:

    numerator_gj
      = sum(COST_r * FINLWT21_i)

    raw_mean_gj
      = numerator_gj / population_g

Diary conversion:

    source_mean_gj
      = 13 * raw_mean_gj

---

# 6. Hierarchy factor

For all source-specific UCC means:

    annual_mean_gj
      = factor_j * source_mean_gj

where:

    factor_j in {1,4}

The three frozen factor-4 UCCs remain included.

No post-outcome exclusion is authorized.

---

# 7. Component aggregation

For each cohort:

    C_COST_g
      = sum annual_mean_gj
        over C_COST_PRIMARY

    H_SERVICE_g
      = sum annual_mean_gj
        over H_SERVICE_CORE

No combined scalar:

    C_COST + H_SERVICE

is defined in E3B4A.

---

# 8. Zero / missing / negative observations

Zero spenders remain in source-specific population denominators.

Missing COST:

    -> 0

Negative COST:

    preserved

No:

    clipping
    winsorization
    abs()
    positive-spender conditioning

is permitted.

Missing and negative row counts are diagnostics only.

---

# 9. Diary ALLOC

ALLOC is diagnostic only.

No Diary record is removed because of ALLOC status.

---

# 10. Outputs frozen before execution

E3B4A must produce:

    E3B4A_2022_cohort_denominators.tsv
    E3B4A_2022_primary_ucc_estimates.tsv
    E3B4A_2022_component_point_estimates.tsv
    E3B4A_2022_owner_renter_comparison.tsv
    E3B4A_2022_diary_alloc_counts.tsv
    E3B4A_first_cex_point_estimates_audit.txt

The comparison table reports mechanically:

    owner level
    renter level
    renter - owner
    renter / owner

for:

    C_COST
    H_SERVICE

No outcome-based model or component selection follows from those values.

---

# 11. Meaning of first values

Reported values are:

    nominal 2022 USD
    weighted
    annual-calendar
    average observed expenditure per consumer unit
    within the specified pseudo-cohort

They are NOT:

    price inflation
    Real Inflation
    fixed-capability cost
    welfare
    causality

Therefore:

    OBSERVED_EXPENDITURE_CHANGE_EQUALS_INFLATION = 0
    REAL_INFLATION_ESTIMATED = 0

---

# 12. Validation policy

E3B4A is the first cohort-specific economic opening.

Even if internally valid:

    ECONOMIC_INTERPRETATION_AUTHORIZED = 0

The next milestone must benchmark the estimator against an official
all-consumer-unit BLS target before strong interpretation.

Proposed next milestone:

    E3B4B — All-CU estimator benchmark validation

