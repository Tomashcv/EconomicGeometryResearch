# E4A2G — K-D-I Component Inference Closeout

## Parent

    bd7222d

E4A2D and E4A2F are frozen PASS.

This milestone performs no new survey estimation. It reads only the frozen
result tables and creates a common K-D-I evidence ledger.

---

## 1. Why a closeout is needed

K, D and I are now empirically estimated, but they come from two independent
official surveys:

    K, D -> SCF
    I    -> CPS ASEC

The three components cannot be treated as if they were observed jointly on
the same household.

This closeout freezes what is known component-by-component before any later
cross-component geometry design.

---

## 2. Common contrast orientation

Every row starts from:

    raw difference = RENTER - OWNER

Each component already has a frozen state sign.

The common state-oriented contrast is:

    state difference
      = state_sign * raw difference

Interpretation:

    positive -> renters have higher/better component state
    negative -> renters have lower/worse component state

This orientation does not combine components.

---

## 3. Frozen K evidence

Primary:

    FIN weighted mean

Mandatory robustness:

    FIN weighted median

Sensitivities:

    LIQ
    EQUITY
    RETQLIQ

All use the already-frozen SCF combined MI + sampling SE.

No K scalar is produced.

---

## 4. Frozen D evidence

Primary:

    PIRTOTAL weighted mean
    state_sign = -1

Secondary:

    DEBT2INC weighted mean
    state_sign = -1

No D scalar is produced.

---

## 5. Frozen I evidence

Primary:

    I_FYFT_SHARE
    I_SEARCH_BURDEN_SHARE

Secondary:

    I_LONG_SEARCH_SHARE
    I_ANY_WORK_SHARE

All use the already-frozen CPS 160-replicate SE.

No I scalar is produced.

---

## 6. 95% uncertainty intervals

For descriptive reporting only:

    state_ci_low
      = state_difference - 1.96*SE

    state_ci_high
      = state_difference + 1.96*SE

A flag records whether the interval excludes zero.

This flag is never a PASS gate.

No multiplicity-adjusted hypothesis family is introduced here.

---

## 7. Exact expected shape

K:

    5 measures x 4 age bands = 20 contrasts

D:

    2 measures x 4 age bands = 8 contrasts

I:

    4 measures x 4 age bands = 16 contrasts

Total:

    44 frozen component contrasts

Plus exactly one descriptive summary row for each of:

    K
    D
    I

---

## 8. Cross-survey boundary

SCF and CPS are independent samples.

Therefore:

    person-level joins are prohibited

    cross-survey joint covariance is unavailable

    K/D SEs cannot be combined with I SEs as if jointly estimated

    raw magnitudes across K, D and I are not commensurable

    pseudo-cohort integration is the only authorized future bridge

This closeout therefore does not calculate a K-D-I norm, distance, angle,
index or scalar.

---

## 9. Outcome-independent closeout

PASS depends only on:

    upstream frozen hashes
    exact source rows
    valid state signs
    finite frozen estimates and SEs
    exact expected shape
    deterministic closeout serialization

PASS does not depend on:

    direction
    magnitude
    confidence interval excluding zero
    agreement among K, D and I
    an expected economic story

Observed heterogeneity must be preserved.

---

## 10. Authorization boundary

A complete closeout may authorize only:

    E4B0_C_H_K_D_I_COHORT_COVERAGE_AND_COMPARABILITY_PREFLIGHT_AUTHORIZED=1

E4B0 must first determine whether C/H coverage and scale semantics are
sufficient for a defensible five-component geometry design.

Still prohibited:

    K scalar
    D scalar
    I scalar
    KDI scalar
    five-dimensionality claim
    Real Inflation estimate
    final scalar
