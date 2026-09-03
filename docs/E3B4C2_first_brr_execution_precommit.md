# E3B4C2 — First 44-Replicate BRR Execution

## Parent

    324aeb8

## Purpose

Execute the exact E3B4C1 contract for the first time.

This is the first milestone authorized to read:

    WTREP01-WTREP44

and calculate:

    BRR variances
    standard errors
    95% normal-approximation confidence intervals

No outcome-based gate is permitted.

---

# Frozen estimator

Full sample:

    FINLWT21

Replicates:

    WTREP01-WTREP44

Exactly 44 BRR replicates.

Cohorts:

    AGE25_34_OWNER
    AGE25_34_RENTER

Components:

    C_COST
    H_SERVICE

Primary UCCs:

    MTBI = 316
    ITBI = 3
    EXPD = 215

---

# Full-sample identity

The execution code must run the full-sample estimate through the same
45-weight computational path used for BRR.

Index 0:

    FINLWT21

Indices 1..44:

    WTREP01..WTREP44

The resulting FINLWT21 component estimates must reproduce the frozen E3B4A V2
component estimates with:

    absolute tolerance = 1e-8 USD

The recomputed owner/renter difference and ratio must also reproduce the
frozen E3B4A V2 comparison values to the same tolerance.

Failure of this identity invalidates the BRR execution engine.

---

# Missing replicate weights

Official PUMD replicate weights may be missing for CUs excluded from a given
half-sample.

For multiplication and population sums:

    missing WTREP -> 0

Negative survey weights are prohibited.

No missing or non-finite replicate denominator is allowed.

---

# Interview

For every cohort and every weight:

    denominator_I
      = sum(weight * MO_SCOPE / 4)

MTBI:

    numerator = sum(COST * weight)

ITBI:

    numerator = sum(VALUE * weight)

The same cohort, calendar-year, UCC, and reference-month filters used by the
validated point estimator are retained.

---

# Diary

For every cohort and weight:

    denominator_D
      = sum(weight / 4)

EXPD:

    numerator = sum(COST * weight)

UCC estimate:

    numerator / denominator_D * 13 * hierarchy_factor

---

# BRR component inference

For full-sample component estimate theta and 44 replicate values theta_r:

    variance
      = (1/44) * sum((theta_r - theta)^2)

    SE
      = sqrt(variance)

    CI95 lower
      = theta - 1.96 * SE

    CI95 upper
      = theta + 1.96 * SE

No p-value is primary or required.

---

# Direct owner-renter difference

    delta
      = renter - owner

For each replicate:

    delta_r
      = renter_r - owner_r

The BRR SE is calculated directly from delta_r.

The independent-samples shortcut is prohibited.

---

# Direct owner-renter ratio

    rho
      = renter / owner

For each replicate:

    rho_r
      = renter_r / owner_r

The BRR SE is calculated directly from rho_r.

Owner component estimates must be finite and nonzero in every replicate.

---

# Hard gates

Only structural/computational gates:

    full-sample component identity PASS
    full-sample comparison identity PASS

    exactly 44 replicates

    all Interview replicate denominators finite and > 0
    all Diary replicate denominators finite and > 0

    176 component replicate rows
    88 difference replicate rows
    88 ratio replicate rows

    all component replicates finite
    all differences finite
    all ratios finite

    all BRR variances finite and >= 0
    all BRR SEs finite and >= 0

No gate exists on:

    sign
    effect magnitude
    SE magnitude
    CI width
    whether CI includes zero
    whether ratio CI includes one

---

# Interpretation if PASS

A PASS authorizes inferential interpretation of these 2022 cohort component
estimates under the CE BRR sampling design.

It does NOT authorize:

    causal interpretation
    welfare interpretation
    observed expenditure = inflation
    Real Inflation estimate
    five-dimensional scalar

