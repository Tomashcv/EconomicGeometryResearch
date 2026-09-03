# E3B3A — Integrated CEX Source and Timing Preflight

## Status

Frozen after E3B2 and before opening any household economic values.

This milestone may inspect:

- ZIP structure;
- source hashes;
- CSV first-record headers only;
- official BLS hierarchical-grouping metadata.

It may NOT inspect expenditure observations.

---

# 1. Calendar-year 2022 source architecture

For Interview Survey calendar-year 2022:

    Q1 2022
        comes from the 2021 Interview release

    Q2 2022
    Q3 2022
    Q4 2022
        come from the 2022 Interview release

Therefore:

    intrvw21.zip
        supplies 2022 Q1

    intrvw22.zip
        supplies 2022 Q2-Q4

The 2022-release Q1-2023 records are NOT part of calendar-year 2022.

---

# 2. Diary Survey

Diary 2022 uses the four Diary calendar quarters:

    Q1 2022
    Q2 2022
    Q3 2022
    Q4 2022

Canonical source:

    diary22.zip

Diary and Interview are independent samples.

Thus:

    RECORD_LEVEL_INTERVIEW_DIARY_JOIN = PROHIBITED

Integrated estimates must be constructed at the UCC / estimand level.

---

# 3. Integrated hierarchy

Canonical metadata:

    BLS Hierarchical Groupings
    CE-HG-Integ-2022

The integrated hierarchy determines which UCCs are sourced from:

    I = Interview
    D = Diary

and provides:

    hierarchy level
    title
    UCC
    survey source
    published-table factor
    data section

No component-specific UCC classification is frozen in E3B3A.

Therefore:

    C_COST_UCC_MAP_FROZEN = 0
    H_SERVICE_UCC_MAP_FROZEN = 0

---

# 4. Required Interview schema

FMLI:

    NEWID
    AGE_REF
    CUTENURE
    FINLWT21

MTBI:

    NEWID
    UCC
    COST
    REF_MO
    REF_YR

Header only.

No COST observation may be read.

---

# 5. Required Diary schema

FMLD:

    NEWID
    AGE_REF
    CUTENURE
    FINLWT21

EXPD:

    NEWID
    UCC
    COST
    ALLOC

Header only.

No COST observation may be read.

---

# 6. Independent-sample rule

The same household does NOT exist in both Interview and Diary samples.

Therefore the project must never attempt:

    Interview_CU_i JOIN Diary_CU_i

Instead, for any integrated component, later estimators must be formed
independently within each survey and combined only after weighting and
periodicity normalization.

---

# 7. Periodicity

Interview MTBI:

    monthly expenditure evidence

Diary EXPD:

    weekly expenditure evidence

No values are opened here.

The exact annualization/integration arithmetic will be frozen in E3B3B,
before economic values are opened.

---

# 8. Transport

Official source URLs:

    https://www.bls.gov/cex/pumd/data/comma/intrvw21.zip
    https://www.bls.gov/cex/pumd/data/comma/diary22.zip
    https://www.bls.gov/cex/pumd/stubs.zip

BLS may reject automated downloads.

If browser-manual transport is required, exact bytes are permitted to be
promoted to the canonical raw path only after ZIP structural validation.

Transport method must not change source semantics.

---

# 9. Disclosure state

    MICRODATA_DATA_ROWS_PARSED = 0
    ECONOMIC_VALUES_OPENED = 0
    EXPENDITURE_VALUES_OPENED = 0
    COHORT_ECONOMIC_ESTIMATES_CALCULATED = 0
    REAL_INFLATION_ESTIMATED = 0

