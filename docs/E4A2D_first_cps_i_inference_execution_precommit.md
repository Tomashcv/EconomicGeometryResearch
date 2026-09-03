# E4A2D — First CPS I Inference Execution Precommit

## Parent

    3ab40ce

E4A2C is frozen PASS.

This is the first milestone permitted to open real CPS I outcome values and
the real PWWGT1-PWWGT160 replicate weights.

The execution contract, parser, estimands, cohorts and structural gates are
committed before those values are read.

---

## 1. Scoped authorization

E4A2C produced:

    E4A2D_FIRST_CPS_I_INFERENCE_EXECUTION_AUTHORIZED=1

That is a scoped authorization for this frozen execution.

It does not authorize K or D values.

---

## 2. Real fields opened

Household:

    H_SEQ
    HSUP_WGT
    H_HHTYPE
    H_TENURE

Reference person:

    PH_SEQ
    PPPOS
    A_AGE
    A_EXPRRP
    WEUEMP
    WEWKRS
    WRK_CK

Replicate file:

    H_SEQ
    PPPOS
    PWWGT1 ... PWWGT160

No SCF K or D outcome is read.

---

## 3. Frozen population

Households:

    H_HHTYPE == 1

Reference person:

    A_EXPRRP in {1,2}
    PPPOS == 41

Join:

    PH_SEQ == H_SEQ

Tenure:

    H_TENURE == 1 -> OWNER
    H_TENURE == 2 -> RENTER

Other/no-cash-rent excluded.

Age:

    25-34
    35-44
    45-54
    55-64

Exactly eight age-band x tenure cohorts.

---

## 4. Frozen I estimands

Primary:

    I_FYFT_SHARE
      indicator = (WEWKRS == 1)

    I_SEARCH_BURDEN_SHARE
      indicator = (WEUEMP in {2,3,4,5,6,7})

Secondary:

    I_LONG_SEARCH_SHARE
      indicator = (WEUEMP in {6,7})

    I_ANY_WORK_SHARE
      indicator = (WRK_CK == 1)

The denominator is every valid household in the frozen cohort.

Zero/NIU is therefore not treated as a cardinal zero. It is simply not in a
binary numerator code set.

Numeric means of WEWKRS or WEUEMP remain prohibited.

---

## 5. Exact inference

Full sample:

    HSUP_WGT

Replicates:

    PWWGT1 ... PWWGT160

For every cohort and estimand:

    theta_0
      = sum(HSUP_WGT * indicator)
        / sum(HSUP_WGT)

    theta_r
      = sum(PWWGT_r * indicator)
        / sum(PWWGT_r)

    Var(theta_0)
      = (4/160)
        * sum_r((theta_r - theta_0)^2)

    SE
      = sqrt(Var)

Negative replicate weights are preserved.

No clipping is permitted.

Every replicate domain denominator must nevertheless be finite and strictly
positive.

---

## 6. Owner-renter contrast

For each age band and estimand:

    delta_0
      = theta_RENTER - theta_OWNER

    delta_r
      = theta_RENTER,r - theta_OWNER,r

The SE is obtained directly from the 160 delta_r values.

The independent-SE shortcut remains prohibited.

---

## 7. Replicate parser sentinels

Before inference can PASS, the raw replicate parser must reproduce the
published official SAS totals, exactly at four decimals, for the fixed
precommitted sentinel set:

    PWWGT0
    PWWGT1
    PWWGT80
    PWWGT160

The sentinel set is frozen before value access and cannot be changed based on
results.

E4A2A already froze the exact PWWGT1-PWWGT160 schema; these totals are an
independent values-side parser/scaling check.

---

## 8. Output shape

Exactly:

    32 cohort-estimand estimates
    5120 cohort-estimand replicate estimates

    16 renter-minus-owner estimates
    2560 renter-minus-owner replicate estimates

No I scalar is computed.

No K/D estimate is computed.

No dimensionality statistic is computed.

---

## 9. Outcome-independent PASS

There is NO gate on:

    sign
    magnitude
    expected owner-renter direction
    SE magnitude
    significance
    economic interpretation

Observed I values must be frozen even if they disagree with the economic
hypothesis.

Only parser, merge, domain, finite-value and exact-shape failures may block
PASS.

---

## 10. After PASS

A complete PASS sets:

    I_EMPIRICALLY_TESTED=1
    I_VALUES_REUSABLE_UNDER_FROZEN_PROVENANCE=1

and authorizes only:

    E4A2E_EXACT_SCF_REPLICATE_ENGINE_PREFLIGHT_AUTHORIZED=1

Still false:

    K_EMPIRICALLY_TESTED
    D_EMPIRICALLY_TESTED
    FIVE_DIMENSIONALITY_PROVEN
    REAL_INFLATION_ESTIMATION_AUTHORIZED
    FINAL_SCALAR_AUTHORIZED
