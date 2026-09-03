# E3B3C4 — Exact CEX Integrated Point-Estimator Contract

## Parent

    7686233

## Status

This is the final zero-economic-value contract before opening CEX COST.

No COST observations may be read while this contract is being frozen.

---

# 1. Frozen evidence

The contract is based on:

    E3B3A R2
        calendar-year Interview window

    E3B3B
        integrated hierarchy reconstruction

    E3B3C1
        component UCC mapping

    E3B3C2
        BLS estimator semantics

    E3B3C3 R1
        official R Interview estimator forensic

    E3B3C3 R2
        official SAS/STATA Interview+Diary reconciliation

and current official BLS methodology.

---

# 2. Cohort-specific source estimators

Let:

    g = pseudo-cohort
    j = UCC
    s_j = official integrated survey source for UCC j
    f_j = official hierarchy annualization factor in {1,4}

The source selection and factor are frozen UCC-by-UCC in E3B3C1.

Interview and Diary use independent samples.

No record-level cross-survey join is permitted.

---

# 3. Interview population denominator

Calendar-year 2022 Interview uses:

    221
    222
    223
    224
    231

For each Interview NEWID i:

    p_i^I
      = FINLWT21_i / 4
        * MO_SCOPE_i / 3

where MO_SCOPE is:

First four collection quarters:

    interview month 1     -> 0
    interview month 2     -> 1
    interview month 3     -> 2
    interview month 4-12  -> 3

Fifth collection quarter:

    interview month 1 -> 3
    interview month 2 -> 2
    interview month 3 -> 1

For cohort g:

    P_g^I = sum_{i in cohort g} p_i^I

The denominator contains all in-scope cohort CUs, including zero spenders.

---

# 4. Interview UCC numerator

MTBI records are restricted to:

    REF_YR = 2022
    REF_MO in 1..12

For Interview-sourced UCC j:

    A_gj^I
      = sum_r COST_r * FINLWT21_NEWID(r)

over records:

    UCC = j
    NEWID belongs to cohort g
    expenditure reference period is calendar 2022

The collection-quarter filename is not used as the expenditure date.

The point mean is:

    mu_gj^I = A_gj^I / P_g^I

MO_SCOPE is applied to the population denominator, not again to COST.

---

# 5. Diary population denominator

Calendar-year 2022 Diary uses:

    221
    222
    223
    224

Diary has:

    MO_SCOPE = 3

Therefore for Diary NEWID i:

    p_i^D = FINLWT21_i / 4

and:

    P_g^D = sum_{i in cohort g} p_i^D

Again, zero-spending cohort CUs remain in the denominator.

---

# 6. Diary UCC numerator and periodicity

For Diary-sourced UCC j:

    A_gj^D
      = sum_r COST_r * FINLWT21_NEWID(r)

over EXPD records with:

    UCC = j
    NEWID belongs to cohort g

The raw Diary estimate is weekly.

The official integrated annual-calendar estimator requires:

    mu_gj^D
      = 13 * A_gj^D / P_g^D

The multiplier 13 is source-periodicity conversion.

It is not the hierarchy factor.

---

# 7. Hierarchy annualization factor

For every UCC:

    f_j in {1,4}

from the frozen integrated hierarchy.

The final annualized UCC point estimate is:

    m_gj = f_j * mu_gj^(s_j)

where:

    mu_gj^(s_j) = mu_gj^I   if source I
                  mu_gj^D   if source D

The factor is applied UCC-by-UCC before component aggregation.

The 2022 frozen map contains exactly:

    factor 1 -> 642 UCCs
    factor 4 -> 3 UCCs

The three factor-4 UCCs remain in the already-frozen primary C_COST map.

No post-hoc exclusion is permitted in the primary estimator.

A separately precommitted robustness specification may later exclude
financing-sensitive UCCs without mutating the primary estimate.

---

# 8. Component point estimators

Primary non-housing observed expenditure:

    C_COST_g
      = sum_{j in C_COST_PRIMARY} m_gj

Primary recurring housing-service observed expenditure:

    H_SERVICE_g
      = sum_{j in H_SERVICE_CORE} m_gj

Frozen counts:

    C_COST_PRIMARY = 435 UCCs
    H_SERVICE_CORE = 99 UCCs

No UCC appears in both components.

---

# 9. Missing, zero and negative COST

Official sample-code behavior is preserved.

## Zero spenders

A cohort CU with no expenditure record for a selected UCC contributes:

    COST = 0

to the numerator while remaining in the population denominator.

Thus:

    POSITIVE_SPENDER_CONDITIONING = PROHIBITED

## Missing COST after expenditure join

Missing COST after joining the family/sample universe to expenditure records:

    -> 0

The first economic execution must report how many missing values were filled.

## Negative COST

Negative released COST observations are preserved.

No:

    abs()
    clipping
    winsorization
    max(COST,0)

is authorized.

Negative values must be separately counted diagnostically.

---

# 10. Diary allocation flags

Released Diary COST is used as supplied by BLS.

ALLOC is diagnostic metadata.

Primary estimation does not drop:

    allocated
    topcoded
    topcoded-and-allocated

records merely because of ALLOC status.

The first execution must report ALLOC counts.

---

# 11. BRR inference

Final CEX inferential uncertainty requires:

    WTREP01 ... WTREP44

For replicate k the same complete estimator is rerun with the appropriate
replicate weights instead of FINLWT21.

The BLS standard-error formula is:

    SE(theta)
      = sqrt(
          sum_{k=1}^{44} (theta_k - theta)^2
          / 44
        )

However E3B3C4 authorizes the opening of descriptive point estimates before
the project implements its final component-level BRR engine.

Therefore:

    BRR_REQUIRED_FOR_FINAL_INFERENCE = 1
    BRR_COMPONENT_ENGINE_FROZEN = 0

No naive IID standard error may be reported.

---

# 12. What the first values mean

The first CEX values are:

    cohort-specific
    weighted
    annual-calendar
    average observed expenditure levels

They are NOT:

    price indices
    fixed-capability costs
    Real Inflation
    welfare measures
    causal estimates

Observed expenditure may change because of:

    prices
    quantities
    substitution
    preferences
    constraints
    composition

Therefore:

    OBSERVED_EXPENDITURE_CHANGE_EQUALS_INFLATION = 0

CEX expenditure levels will later help define frozen base-period expenditure
weights and household economic components.

---

# 13. Authorization

If the evidence audit passes:

    POINT_ESTIMATOR_CONTRACT_FROZEN = 1
    COST_VALUES_AUTHORIZED = 1
    E3B4A_FIRST_CEX_POINT_ESTIMATES_AUTHORIZED = 1

But:

    REAL_INFLATION_ESTIMATION_AUTHORIZED = 0
    FINAL_SCALAR_AUTHORIZED = 0

