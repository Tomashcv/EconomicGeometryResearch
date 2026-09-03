# E3B4B R3B R1 — Official Documentation Reconciliation

## Trigger

The original R3B precommit required the official integrated SAS/STATA UCC
sample-code bundle itself to contain direct literal evidence for:

    ITBI
    VALUE

Observed result:

    ITBI_OR_ITAB_CODE_EVIDENCE = 1
    VALUE_CODE_EVIDENCE = 0
    OFFICIAL_ITBI_CODE_CONTEXT = FAIL

This failure is permanently preserved.

The failure does NOT establish that VALUE is semantically unresolved.
It establishes that the integrated sample-code artifact is not the correct
source for ITBI variable-level documentation.

---

# 1. Frozen local-byte evidence

E3B4B R3A directly inspected the five 2022 ITBI CSV headers and established:

    NEWID
    REFMO
    REFYR
    UCC
    PUBFLAG
    VALUE
    VALUE_

with identical schema across:

    221
    222
    223
    224
    231

and:

    ITBI_POINT_VALUE_FIELD = VALUE

No data rows were parsed.

---

# 2. Official BLS variable documentation evidence

Official BLS Consumer Expenditure PUMD documentation identifies:

    VALUE
        Value of UCC
        numeric

    VALUE_
        Value flag
        T     = Topcoded
        blank = Not topcoded

Therefore:

    VALUE is the numerical released UCC value.

    VALUE_ is NOT an alternative numerical estimate.

Source:

    https://www.bls.gov/cex/csxintvw.pdf

The official BLS Microdata Overview also states:

    Value_ only indicates whether value is topcoded

Source:

    https://www.bls.gov/cex/introduction-to-microdata.pdf

---

# 3. Current BLS file-type documentation

Current BLS PUMD Getting Started Guide identifies:

    ITBI
        Detailed income
        Monthly
        primary key includes NEWID, UCC, REF_MO, REFYR

    ITII
        Imputed income iterations
        Monthly
        primary key additionally includes IMPNUM

Source:

    https://www.bls.gov/cex/pumd-getting-started-guide.htm

The official novice guide states that ITII contains:

    five imputes per income item

with:

    IMPNUM

identifying the imputation iteration.

Therefore ITII must not be naïvely appended to ITBI for an ordinary point
estimate.

---

# 4. Evidence-provenance rule

Different official artifacts answer different questions:

    Integrated SAS/STATA sample code:
        integration architecture / file-family use

    2022 local CSV headers:
        exact released field spelling

    BLS variable documentation:
        VALUE / VALUE_ field semantics

    Current BLS PUMD guide:
        ITBI / ITII file roles and periodicity

No single artifact is required to restate all layers.

The original R3B FAIL remains valid as a failure of its overly strong
single-artifact gate.

---

# 5. V2 semantic contract

    MTBI point value = COST
    MTBI month       = REF_MO
    MTBI year        = REF_YR

    ITBI point value = VALUE
    ITBI month       = REFMO
    ITBI year        = REFYR
    ITBI topcode flag = VALUE_

    EXPD point value = COST

    ITII point-estimate append = PROHIBITED

Released negative VALUE observations are preserved.

No:

    abs()
    clipping
    winsorization
    positive-only filtering

is authorized.

---

# 6. Restrictions

    DATA_ROWS_PARSED = 0
    COST_VALUES_READ = 0
    ITBI_VALUE_VALUES_READ = 0
    NEW_ECONOMIC_VALUES_OPENED = 0

If this reconciliation passes:

    ITBI_POINT_VALUE_SEMANTICS_FROZEN = 1
    E3B4B_R3_REPAIR_AUTHORIZED = 1

Corrected economic execution remains unauthorized until repaired R3 passes.

