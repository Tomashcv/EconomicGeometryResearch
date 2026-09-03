# E3B3C2 — BLS Estimator Semantics Preflight

## Status

Executed after:

    E3B3C1 component UCC mapping PASS

Canonical parent:

    71e82d2

No CEX COST observation may be opened.

---

# 1. Purpose

Freeze the official weighting, timing and periodicity semantics required for
future CEX point estimates before implementing economic calculations.

This milestone does NOT yet implement the final integrated estimator.

The exact implementation must subsequently be checked against official BLS
integrated-UCC sample code.

---

# 2. Canonical component map

Frozen input:

    data/metadata/E3B3C1_component_ucc_map.tsv

Expected SHA256:

    a6dd2e592d45f0c7c8428a8265d3b857c615cd842e10241fff06d2a3c06c1e1f

Frozen 2022 map:

    C_COST_PRIMARY = 435 UCCs
    H_SERVICE_CORE = 99 UCCs

with:

    C_COST / H_SERVICE overlap = 0
    unmapped UCCs = 0

---

# 3. Representative weight

Official population weight:

    FINLWT21

is available in:

    FMLI
    FMLD

For a calendar-year estimate:

    QNUM = 4

The reason is that each collection quarter is independently weighted to
represent the annual US population.

Therefore population weights must not simply be summed across quarters without
the QNUM adjustment.

---

# 4. Interview MO_SCOPE

Interview uses five collection quarters for calendar-year 2022:

    221
    222
    223
    224
    231

For the first four quarters:

    interview month 1    -> MO_SCOPE = 0
    interview month 2    -> MO_SCOPE = 1
    interview month 3    -> MO_SCOPE = 2
    interview month 4-12 -> MO_SCOPE = 3

For the fifth quarter:

    interview month 1 -> MO_SCOPE = 3
    interview month 2 -> MO_SCOPE = 2
    interview month 3 -> MO_SCOPE = 1

Required fields:

    QINTRVMO
    QINTRVYR

The future population denominator must apply the official:

    FINLWT21 / QNUM
        * MO_SCOPE / 3

logic.

---

# 5. MTBI calendar restriction

Future Interview expenditure observations must satisfy:

    REF_YR = 2022
    REF_MO in 1..12

The collection-quarter filename is not itself the expenditure date.

No REF_MO/REF_YR observations are read here.

---

# 6. Diary scope

Diary calendar-year 2022 uses:

    221
    222
    223
    224

For Diary:

    MO_SCOPE = 3

for all four quarters.

Thus the population-weight scope multiplier is:

    MO_SCOPE / 3 = 1

---

# 7. Survey integration

Interview and Diary are independent samples.

Therefore:

    RECORD_LEVEL_INTERVIEW_DIARY_JOIN = PROHIBITED

For every UCC:

    use only the survey source frozen in E3B3C1

and integrate only after source-specific estimation.

---

# 8. Diary periodicity

EXPD expenditures are weekly.

BLS states that an integrated Diary UCC estimate must be multiplied by:

    13

to convert the weekly result to a quarterly amount comparable with an
Interview estimate.

Therefore:

    DIARY_WEEKLY_TO_QUARTER_MULTIPLIER = 13

This multiplier is frozen before COST values open.

---

# 9. Hierarchy factor

The integrated hierarchy provides:

    factor = 1
    factor = 4

BLS defines this as the factor by which the mean must be multiplied to match
annualized published-table data.

The exact frozen map contains:

    factor 1 = 642 UCCs
    factor 4 = 3 UCCs

The factor is preserved UCC-by-UCC.

E3B3C2 does not guess around these three factor-4 UCCs.

Their identities may be disclosed because this is metadata only.

---

# 10. Point estimate versus inference

FINLWT21 is sufficient to construct representative full-sample point
estimates under the BLS formulas.

However final sampling inference must account for the CE complex design.

Current CE uses:

    WTREP01 ... WTREP44

Balanced Repeated Replication weights.

Therefore:

    FINAL_STANDARD_ERRORS_FROM_NAIVE_IID = PROHIBITED

and:

    BRR_REQUIRED_FOR_FINAL_CEX_INFERENCE = 1

E3B3C2 verifies the 44 replicate-weight fields exist.

It does not calculate replicate estimates.

---

# 11. Exact numerator implementation remains blocked

The documentation establishes the required pieces:

    FINLWT21
    QNUM
    MO_SCOPE
    survey source
    Diary x13
    hierarchy factor

but the project will not infer the exact implementation order or detailed
numerator treatment from memory.

Before COST values open, E3B3C3 must audit the official BLS integrated-UCC
sample code.

Therefore:

    EXACT_INTEGRATED_ESTIMATOR_IMPLEMENTATION_FROZEN = 0

and:

    COST_VALUES_AUTHORIZED = 0

---

# 12. Disclosure state

    COST_VALUES_READ = 0
    EXPENDITURE_VALUES_OPENED = 0
    HOUSEHOLD_ECONOMIC_VALUES_OPENED = 0
    REAL_INFLATION_ESTIMATED = 0

