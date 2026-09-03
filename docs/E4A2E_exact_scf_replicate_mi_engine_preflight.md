# E4A2E — Exact SCF Replicate + Multiple-Imputation Engine Preflight

## Parent

    017d0ec

E4A2D is frozen PASS and I is now empirically tested.

E4A2E does **not** open K, D or SCF replicate-weight values.  It freezes and
synthetically tests the exact SCF 2022 inference engine before the first K/D
execution.

---

## 1. Official SCF design

The frozen 2022 Federal Reserve codebook establishes:

    five implicates per family

    X42001 as the full-sample weight

    999 sampling replicates

    replicate raw weights WT1B1 ... WT1B999

    multiplicities MM1 ... MM999

    replicate weights computed only for first implicate

    effective replicate weight:
      MAX(0, WT1B_r) * MAX(0, MM_r)

The replicate file is joined by Y1.

The implicate number is:

    Y1 - 10*YY1

---

## 2. Point statistic

For a statistic theta and implicate m:

    theta_m
      = statistic computed with X42001
        inside that implicate's exact frozen cohort

The reported full-sample statistic is:

    theta_0
      = mean(theta_1,...,theta_5)

Cohort membership is evaluated per implicate.

It is not permissible to stack five implicates and treat them as five
independent households.

---

## 3. Imputation variance

Exactly the codebook/SAS macro rule:

    V_imp
      = sum_m((theta_m - mean(theta_1..theta_5))^2)
        / 4

This is the sample variance of the five implicate statistics.

---

## 4. Sampling variance

Sampling uncertainty uses only first-implicate outcomes and cohort membership.

For replicate r:

    w_ir
      = MAX(0, WT1B_ir) * MAX(0, MM_ir)

and:

    theta_r
      = statistic under w_r
        using first-implicate values/domain

Every replicate-domain denominator must be finite and strictly positive.

All 999 replicates are required.

The official macro centers sampling variance on the mean of the 999 replicate
statistics:

    theta_rep_bar
      = mean(theta_1,...,theta_999)

    V_sampling
      = sum_r((theta_r - theta_rep_bar)^2)
        / 998

It is **not** centered on the five-implicate pooled point estimate.

---

## 5. Combined variance

Exactly:

    V_total
      = (6/5)*V_imp + V_sampling

    SE_total
      = sqrt(V_total)

No sign, magnitude or significance gate exists.

---

## 6. Weighted mean

For a domain g:

    mean
      = sum(w_i*x_i) / sum(w_i)

The denominator is recomputed separately:

    per implicate
    per sampling replicate
    per cohort

---

## 7. Weighted median FIN robustness

E4A2 already froze weighted median FIN as mandatory robustness before a strong
K dimensionality claim.

The weighted median is therefore part of the exact engine.

Within a domain:

    sort observations by value

    compute cumulative normalized weight

    select the first value where cumulative weight share >= 0.5

The same rule is used:

    separately in all five implicates
    separately in all 999 first-implicate sampling replicates

Imputation, sampling and combined variance then use the same formulas as above.

The weighted mean FIN remains primary.

---

## 8. K estimands for the next execution

Primary:

    FIN weighted mean

Robustness:

    FIN weighted median

Sensitivity means:

    LIQ
    EQUITY
    RETQLIQ

No K scalar combining these variables is authorized.

---

## 9. D estimands for the next execution

Primary raw burden:

    PIRTOTAL weighted mean

State orientation:

    -PIRTOTAL

Secondary:

    DEBT2INC weighted mean
    state orientation = negative

No D scalar combining PIRTOTAL and DEBT2INC is authorized.

---

## 10. Frozen cohorts

Exactly eight G1 cohorts:

    AGE25_34 OWNER
    AGE25_34 RENTER
    AGE35_44 OWNER
    AGE35_44 RENTER
    AGE45_54 OWNER
    AGE45_54 RENTER
    AGE55_64 OWNER
    AGE55_64 RENTER

SCF age and tenure classification remain the previously frozen raw
per-implicate logic.

No cohort definition may change based on K or D values.

---

## 11. Owner-renter contrast

For every statistic and implicate m:

    delta_m
      = statistic_RENTER,m - statistic_OWNER,m

Point contrast:

    delta_0
      = mean(delta_1,...,delta_5)

Imputation variance is the sample variance of these five direct differences.

For each first-implicate sampling replicate r:

    delta_r
      = statistic_RENTER,r - statistic_OWNER,r

Sampling variance is the sample variance of the 999 direct replicate
differences.

The independent-SE shortcut is prohibited.

---

## 12. Synthetic-only preflight

Executable tests must prove:

    exactly 5 implicates required
    exactly 999 replicates required
    MAX(0,MM)*MAX(0,WT1B) semantics
    missing replicate selection entries map to zero weight
    weighted-mean oracle identity
    weighted-median oracle identity
    per-implicate domain recomputation
    sampling uses first implicate only
    imputation variance divisor 4
    sampling variance divisor 998
    sampling variance centered on replicate mean
    6/5 imputation multiplier
    combined variance identity
    direct renter-minus-owner covariance-preserving inference
    nonpositive replicate denominator rejection
    non-finite input rejection

Only synthetic engineering fixtures are used.

---

## 13. Authorization boundary

Only a complete E4A2E PASS may produce:

    E4A2F_FIRST_SCF_KD_INFERENCE_EXECUTION_AUTHORIZED=1

E4A2F will be the first milestone permitted to read:

    FIN
    LIQ
    EQUITY
    RETQLIQ
    PIRTOTAL
    DEBT2INC
    WT1B1..WT1B999
    MM1..MM999

Even after E4A2E PASS:

    K_VALUES_OPEN_AUTHORIZED=0
    D_VALUES_OPEN_AUTHORIZED=0
    K_D_I_INFERENCE_AUTHORIZED=0
    FIVE_DIMENSIONALITY_PROVEN=0
    REAL_INFLATION_ESTIMATION_AUTHORIZED=0
    FINAL_SCALAR_AUTHORIZED=0
