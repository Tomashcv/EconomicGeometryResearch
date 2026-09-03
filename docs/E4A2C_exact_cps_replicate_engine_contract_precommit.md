# E4A2C — Exact CPS ASEC Replicate-Inference Engine Contract

## Parent

    4235083

E4A2B is frozen PASS.

This milestone freezes and tests the exact CPS replicate-inference engine
before any real I outcome or PWWGT1-PWWGT160 value is opened.

---

## 1. Economic-open boundary

E4A2C may read:

    frozen metadata
    frozen contracts
    frozen E4A2B bridge outputs
    official Census replicate-weight usage documentation
    synthetic fixtures created inside the audit

E4A2C may NOT read:

    WEWKRS values
    WEUEMP values
    WRK_CK values

    PWWGT1 ... PWWGT160 values

    FIN or other K outcomes
    PIRTOTAL or other D outcomes

No real estimate, SE, CI, correlation, dimensionality statistic or Real
Inflation result is produced.

---

## 2. Full-sample point weight

The already-frozen CPS household point estimator remains:

    HSUP_WGT

E4A2B empirically established:

    HSUP_WGT == reference-person MARSUPWT
    at the public-use two-decimal representation

and established the precision bridge to PWWGT0.

PWWGT0 is therefore retained as a merge/precision verification field.

It does NOT replace HSUP_WGT as the project's frozen full-sample household
point weight.

Official replicate weights are used to estimate variance, not to create a new
independent point estimate.

---

## 3. Exact replicate set

Exactly:

    PWWGT1
    ...
    PWWGT160

No missing replicate.
No extra replicate.
No silent replicate drop.

---

## 4. Negative replicate weights

Official Census ASEC documentation states that the replicate weighting process
may produce negative replicate weights for some cases.

Therefore the engine must:

    preserve negative replicate weights exactly
    never MAX(0, weight)
    never clip negative weights
    never replace a negative replicate weight with zero

This is intentionally different from the SCF replicate-weight construction.

A replicate domain denominator must nevertheless be finite and strictly
positive for the statistic to be accepted.

---

## 5. Weighted-share estimator

For cohort g and binary indicator z_i:

Full-sample estimate:

    theta_0[g]
      = sum_i HSUP_WGT_i * z_i
        / sum_i HSUP_WGT_i

within the cohort.

For replicate r:

    theta_r[g]
      = sum_i PWWGT_r_i * z_i
        / sum_i PWWGT_r_i

within the exact same cohort.

The numerator and denominator must use the same replicate weight.

Reusing the full-sample denominator inside a replicate is prohibited.

---

## 6. ASEC variance

Exactly:

    Var(theta_0)
      = (4/160)
        * sum_{r=1..160}
          (theta_r - theta_0)^2

    SE(theta_0)
      = sqrt(Var(theta_0))

All 160 replicate estimates are required.

No replicate may be selected or removed based on its result.

---

## 7. I estimands

Primary:

    I_FYFT_SHARE
      variable: WEWKRS
      indicator: WEWKRS == 1
      state sign: +1

    I_SEARCH_BURDEN_SHARE
      variable: WEUEMP
      indicator: WEUEMP in {2,3,4,5,6,7}
      state sign: -1

Secondary:

    I_LONG_SEARCH_SHARE
      variable: WEUEMP
      indicator: WEUEMP in {6,7}
      state sign: -1

    I_ANY_WORK_SHARE
      variable: WRK_CK
      indicator: WRK_CK == 1
      state sign: +1

The denominator for every share is all valid frozen-cohort reference-person
households, not only the numerator universe.

No numeric mean of WEWKRS or WEUEMP is authorized.

---

## 8. Cohorts

Exactly the frozen G1 architecture:

    AGE25_34 OWNER
    AGE25_34 RENTER

    AGE35_44 OWNER
    AGE35_44 RENTER

    AGE45_54 OWNER
    AGE45_54 RENTER

    AGE55_64 OWNER
    AGE55_64 RENTER

CPS mapping remains:

    H_HHTYPE == 1
    A_EXPRRP in {1,2}
    PH_SEQ == H_SEQ

    H_TENURE == 1 -> OWNER
    H_TENURE == 2 -> RENTER

OTHER/no-cash-rent excluded.

The reference-person replicate record remains:

    PPPOS == 41

joined by H_SEQ.

No cohort mutation based on I outcomes is permitted.

---

## 9. Owner-renter difference

For each age band and estimand:

    delta
      = theta_RENTER - theta_OWNER

For replicate r:

    delta_r
      = theta_RENTER,r - theta_OWNER,r

Variance is calculated directly from the 160 delta_r values using the same
ASEC formula.

Primary difference SE:

    direct replicate covariance-preserving SE

Prohibited:

    sqrt(SE_owner^2 + SE_renter^2)

---

## 10. First execution shape

Four estimands x eight cohorts:

    32 full-sample cohort-estimand rows

Exactly 160 replicates per row:

    5120 replicate cohort-estimand rows

Four estimands x four age-band owner-renter contrasts:

    16 full-sample difference rows

Exactly 160 replicates per difference:

    2560 replicate difference rows

No ratio inference is required at this milestone family.

---

## 11. Synthetic engine preflight

E4A2C must pass executable synthetic tests for:

    exact 160-replicate shape
    weighted-share oracle identity
    zero-variance identity
    replicate-specific denominator recomputation
    common-scale invariance of a weighted share
    permitted negative replicate weights without clipping
    exact 4/160 variance formula
    direct owner-renter difference within replicate
    rejection of a nonpositive replicate domain denominator
    rejection of non-finite input

Synthetic values are engineering fixtures only.

They are not economic observations.

---

## 12. No outcome-based gate

E4A2C has no gate on:

    expected I direction
    owner-renter sign
    effect magnitude
    variance magnitude
    SE magnitude
    statistical significance
    dimensionality

Only structural and computational correctness may determine PASS.

---

## 13. Next authorization

Only a complete E4A2C PASS may produce:

    E4A2D_FIRST_CPS_I_INFERENCE_EXECUTION_AUTHORIZED=1

E4A2D will be the first milestone permitted to parse:

    WEWKRS
    WEUEMP
    WRK_CK
    PWWGT1 ... PWWGT160

under this frozen engine.

Even after E4A2C PASS:

    K_VALUES_OPEN_AUTHORIZED=0
    D_VALUES_OPEN_AUTHORIZED=0
    K_D_I_INFERENCE_AUTHORIZED=0
    FIVE_DIMENSIONALITY_PROVEN=0
    REAL_INFLATION_ESTIMATION_AUTHORIZED=0
    FINAL_SCALAR_AUTHORIZED=0
