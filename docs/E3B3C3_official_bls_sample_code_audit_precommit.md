# E3B3C3 — Official BLS Integrated-UCC Sample-Code Audit

## Status

Executed after:

    E3B3C2 BLS estimator semantics PASS

Canonical parent:

    0faddf7

No CEX COST observations may be opened.

---

# 1. Purpose

The BLS publishes official sample code for:

    Aggregates selected UCCs

in SAS, R and STATA.

The code integrates Interview and Diary estimates on a UCC basis.

E3B3C3 audits the official R implementation before this project freezes its
own exact integrated estimator.

---

# 2. Canonical source

Official BLS resource:

    https://www.bls.gov/cex/pumd/r-ucc.zip

Canonical local path:

    data/raw/cex/sample_code/r-ucc.zip

The raw archive is source evidence only.

---

# 3. Allowed disclosure

E3B3C3 may inspect:

    archive member names
    source-code text
    code-variable names
    formulas / operations in source code

It may NOT inspect:

    CEX COST observations
    household expenditures
    income values
    cohort economic values

Therefore:

    MICRODATA_DATA_ROWS_PARSED = 0
    COST_VALUES_READ = 0
    ECONOMIC_VALUES_OPENED = 0

---

# 4. Required semantic evidence

The official code must be audited for evidence relating to:

    FINLWT21
    replicate weights
    MO_SCOPE
    UCC
    COST
    Interview / Diary source selection
    Diary periodicity adjustment
    hierarchy factor

The audit records source-code context around these concepts.

---

# 5. No implementation mutation

E3B3C3 does not change:

    C_COST map
    H_SERVICE map
    cohort definitions
    timing rules
    QNUM
    Diary x13 rule
    BRR requirement
    Real Inflation definition

---

# 6. Exact estimator remains blocked during source inspection

Until the source-code evidence has been inspected:

    EXACT_INTEGRATED_ESTIMATOR_IMPLEMENTATION_FROZEN = 0
    COST_VALUES_AUTHORIZED = 0

A subsequent estimator-contract freeze may only use semantics established
before COST values open.

