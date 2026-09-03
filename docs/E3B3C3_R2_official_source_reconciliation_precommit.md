# E3B3C3 R2 — Official SAS/STATA Source Reconciliation

## Parent

    811b752

## Prior evidence

The official R UCC sample-code forensic established:

    R_SAMPLE_SCOPE=INTERVIEW_FMLI_MTBI_ONLY
    R_SAMPLE_CALENDAR_WEIGHT_FORMULA=PASS
    R_SAMPLE_SELF_CONTAINED_INTERVIEW_DIARY_INTEGRATION=0

The original composite R-only gate remains permanently preserved as FAIL.

---

## Objective

Inspect the official BLS SAS and STATA implementations associated with:

    Aggregates selected UCCs

to determine whether the missing Diary implementation is present.

This milestone does not alter any economic hypothesis or estimator rule.

---

## Required direct source-code evidence

At least one secondary official implementation must contain direct evidence of:

    FMLD and/or EXPD
    FINLWT21
    UCC
    COST or expenditure-value processing
    explicit Diary periodicity conversion involving 13

WTREP and hierarchy-factor appearances are audited but are not required to
appear in the same program because current BLS methodology independently
documents:

    BRR using WTREP01-WTREP44
    hierarchy factor 1 or 4

---

## Reconciliation principle

Evidence is deliberately split:

### Official R source

Direct evidence for:

    Interview FMLI/MTBI processing
    five-quarter calendar weighting
    FINLWT21 / 4
    partial first-quarter scope
    partial fifth-quarter scope
    sum(COST * FINLWT21) / sum(POPWT)

### Official SAS/STATA source

Expected to resolve direct Diary implementation and periodicity.

### Official BLS methodology

Already separately frozen for:

    QNUM
    MO_SCOPE
    independent Interview/Diary samples
    UCC-by-UCC integration
    Diary weekly x13
    BRR WTREP01-WTREP44
    hierarchy factor 1/4

No single source file is required to restate every methodology rule.

---

## Hard restriction

Even if R2 passes:

    EXACT_INTEGRATED_ESTIMATOR_IMPLEMENTATION_FROZEN=0
    COST_VALUES_AUTHORIZED=0

R2 only authorizes an exact estimator contract to be written next.

---

## Disclosure

    MICRODATA_DATA_ROWS_PARSED=0
    COST_VALUES_READ=0
    EXPENDITURE_VALUES_OPENED=0
    HOUSEHOLD_ECONOMIC_VALUES_OPENED=0
    REAL_INFLATION_ESTIMATED=0

