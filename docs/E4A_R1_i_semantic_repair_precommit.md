# E4A R1 — I Semantic Repair

## Parent

    4cc1071

## Trigger

E4A1 produced a genuine scientific semantic FAIL:

    E4A_WEWKRS_DIRECTION_SEMANTICS = FAIL
    E4A_WEUEMP_DIRECTION_SEMANTICS = FAIL
    E4A_I_PRIMARY_SEMANTICS = FAIL

while:

    SCF_K_D_SCHEMA = PASS
    CPS_OFFICIAL_METADATA_VARIABLES = PASS

No K, D or I economic values were opened.

The original FAIL remains immutable.

---

# Why E4A failed

E4A treated:

    WEWKRS numeric higher = better
    WEUEMP numeric higher = worse

Official Census documentation shows both are categorical recodes.

WEWKRS:

    0 = NIU

    1 = full-year full-time
    2 = full-year part-time
    3 = part-year full-time
    4 = part-year part-time
    5 = nonworker

Therefore:

    mean(WEWKRS)
    monotonic numeric WEWKRS

are prohibited as primary economic statistics.

WEUEMP:

    0 = NIU
    1 = none
    2 = 1-4 weeks
    3 = 5-10 weeks
    4 = 11-14 weeks
    5 = 15-26 weeks
    6 = 27-39 weeks
    7 = 40+ weeks
    8 = full-year worker
    9 = nonworker

Codes 8 and 9 are structural categories, not points on an unemployment
severity scale.

Therefore:

    mean(WEUEMP)
    monotonic numeric WEUEMP

are prohibited.

---

# Repaired I architecture

I remains a multidimensional sub-construct at this stage.

No scalar I is authorized.

## Primary I observable 1 — full-year/full-time attachment

For each frozen CPS pseudo-cohort:

    I_FYFT_SHARE
      = weighted share of reference-person households
        with WEWKRS == 1

Interpretation:

    share whose reference person is classified as
    full-year / full-time worker

Direction:

    higher = stronger realized annual employment attachment

This is NOT automatically a welfare measure.

---

# Primary I observable 2 — search / layoff burden

For each frozen CPS pseudo-cohort:

    I_SEARCH_BURDEN_SHARE
      = weighted share with
        WEUEMP in {2,3,4,5,6,7}

These codes indicate a positive interval of weeks looking for work or on
layoff.

Codes:

    1 = none
    8 = full-year worker
    9 = nonworker

are excluded from the positive-search numerator.

Direction:

    higher = greater realized search/layoff burden

For state-vector sign normalization later:

    sign = -1

No scalar combination with I_FYFT_SHARE is authorized.

---

# Secondary robustness observable — long search

    I_LONG_SEARCH_SHARE
      = weighted share with
        WEUEMP in {6,7}

corresponding to:

    27-39 weeks
    40+ weeks

Direction:

    higher = worse labor-market search burden

This is secondary robustness only.

---

# Secondary robustness observable — any work

Official recode:

    WRK_CK

indicates whether the person worked last year including temporary and
part-time employment.

Secondary:

    I_ANY_WORK_SHARE
      = weighted share with WRK_CK == 1

This protects against relying exclusively on full-year/full-time status.

---

# Cardinal sensitivity fields

Official cardinal fields remain available:

    WKSWORK
        actual weeks worked
        1..52
        universe WORKYN == 1

    LKWEEKS
        actual weeks looking / on layoff
        1..51
        universe WKSWORK 1..51

    NWLKWK
        actual weeks looking / on layoff
        1..52
        universe NWLOOK == 1

These fields are not yet promoted to the primary I estimator.

Reason:

their survey universes require explicit reconstruction rules and temporary-work
cases must not be silently converted to zero.

Therefore:

    CARDINAL_NIU_EQUALS_ZERO = PROHIBITED

until a dedicated universe-consistency audit is run.

---

# Universe-control variables

Required for later cardinal sensitivity implementation:

    WORKYN
    WRK_CK
    WTEMP
    LKNONE
    NWLOOK
    PYRSN
    RSNNOTW

Important:

A person with no weeks of work is not automatically classified as
economically insecure.

Reasons for nonwork / remaining nonwork include:

    illness/disability
    caregiving
    school
    retirement
    no work available
    other

PYRSN and RSNNOTW therefore remain mandatory interpretation diagnostics.

---

# Hours

    HRSWK

is secondary only.

Part-time hours can be voluntary or involuntary.

No monotonic welfare interpretation of HRSWK is authorized.

---

# Allocation flags

Later execution must retain diagnostics where available for:

    I_WKSWK
    I_LKWEEK
    I_NWLKWK
    I_NWLOOK
    I_WORKYN
    I_WTEMP

Allocation status may be reported but does not automatically invalidate a
record.

---

# Frozen CPS cohort estimator unit

The project continues to estimate household pseudo-cohort statistics using the
reference person.

Reference-person anchor:

    A_EXPRRP in {1,2}

Cohort:

    AGE_BAND x TENURE

Weight architecture remains pending exact estimator/inference contract before
economic values are opened.

No weight choice is changed by this semantic repair.

---

# K and D

E4A1 already established:

    SCF_K_D_SCHEMA = PASS

Therefore the K and D architecture is not modified by E4A R1.

Still frozen:

K primary:

    FIN

K sensitivities:

    LIQ
    EQUITY
    RETQLIQ

D primary:

    -PIRTOTAL

D sensitivity:

    -DEBT2INC

No K/D economic values are opened here.

---

# Dimensionality

This repair does not constitute evidence that I is an independent dimension.

Still:

    K_EMPIRICALLY_TESTED = 0
    D_EMPIRICALLY_TESTED = 0
    I_EMPIRICALLY_TESTED = 0

    FIVE_DIMENSIONALITY_PROVEN = 0

Later dimensionality gates must be frozen before longitudinal K/D/I outcomes
are inspected.

---

# Restrictions

    CPS_DATA_ROWS_PARSED = 0
    CPS_I_VALUES_READ = 0

    SCF_DATA_ROWS_PARSED = 0
    SCF_K_VALUES_READ = 0
    SCF_D_VALUES_READ = 0

    REAL_INFLATION_ESTIMATION_AUTHORIZED = 0
    FINAL_SCALAR_AUTHORIZED = 0

If this semantic repair passes:

    E4A2_KDI_ESTIMATOR_PREFLIGHT_AUTHORIZED = 1

