# E4A2F — First SCF K-D Inference Execution Precommit

## Parent

    6c074f1

E4A2E is frozen PASS.

This is the first milestone permitted to open the real SCF K/D values and the
999 replicate-weight/multiplicity values.

The source join, raw cohort rules, estimands, MI engine, sampling engine and
all PASS gates are committed before those values are opened.

---

## 1. Sources and exact responsibilities

Full public SCF:

    scf2022s.zip
    member p22i6.dta

Authorized fields:

    Y1
    YY1
    X14
    X508
    X601
    X701
    X7133
    X42001

This file supplies only:

    family / implicate identifiers
    frozen raw cohort classification
    full-sample weight

SCF summary extract:

    scfp2022s.zip
    member rscfp2022.dta

Authorized economic fields:

    FIN
    LIQ
    EQUITY
    RETQLIQ
    PIRTOTAL
    DEBT2INC

The full and summary extracts are joined one-to-one by:

    Y1, YY1

No summary HOUSECL or AGE variable is substituted for the already-frozen raw
E3A4 cohort rules.

---

## 2. Family / implicate structure

Family:

    YY1

Implicate:

    Y1

Implicate number:

    Y1 - 10*YY1

Every family must have exactly:

    {1,2,3,4,5}

The five rows are multiple imputations, not five independent families.

---

## 3. Frozen G1 classification

Age comes from:

    X14

Age bands:

    25-34
    35-44
    45-54
    55-64

OWNER if any:

    X508 in {1,2}

    X601 in {1,2,3}

    X701 in {1,3,4,5,6,8}

    X701 == -7 AND X7133 == 1

RENTER only if OWNER is false and any:

    X508 == 3

    X601 == 4

    X701 == 2

Everything else is OTHER and excluded from the primary G1 comparison.

Classification is recomputed independently in each implicate before its
statistic is estimated.

No cohort rule may change after K/D outcomes open.

---

## 4. Full-sample point estimation

Full weight:

    X42001

Each statistic is estimated separately in each of five implicates.

Reported point:

    mean of the five implicate statistics

The SCF summary extract is already on the frozen 2022-real-dollar basis where
applicable.

Second deflation is prohibited.

---

## 5. Sampling variance

Replicate file:

    scf2022rw1s.zip
    member p22_rw1.dta

Exactly:

    WT1B1 ... WT1B999
    MM1 ... MM999

Each replicate joins to first-implicate outcomes by Y1.

Effective replicate weight:

    MAX(0,WT1B_r) * MAX(0,MM_r)

Sampling uses only:

    implicate 1 outcome
    implicate 1 cohort membership

Every one of the 999 replicate domain denominators must be finite and strictly
positive.

Sampling variance:

    mean_rep = mean(theta_1,...,theta_999)

    V_sampling
      = sum((theta_r - mean_rep)^2) / 998

No replicate is selected or removed based on its result.

---

## 6. Multiple-imputation variance

For implicate statistics theta_1...theta_5:

    mean_imp = mean(theta_1,...,theta_5)

    V_imp
      = sum((theta_m - mean_imp)^2) / 4

Combined variance:

    V_total
      = (6/5)*V_imp + V_sampling

Combined SE:

    sqrt(V_total)

---

## 7. Frozen K statistics

Primary:

    K_FIN_MEAN
      FIN weighted mean
      higher = stronger K

Mandatory robustness:

    K_FIN_MEDIAN
      FIN weighted median
      higher = stronger K

Sensitivities:

    K_LIQ_MEAN
    K_EQUITY_MEAN
    K_RETQLIQ_MEAN

All are descriptive component estimates.

No K scalar combining them is authorized.

---

## 8. Frozen D statistics

Primary raw burden:

    D_PIRTOTAL_MEAN

State orientation:

    state_sign = -1

Secondary burden:

    D_DEBT2INC_MEAN

State orientation:

    state_sign = -1

DEBT dollars remain diagnostic only and are not opened in this execution.

No D scalar is authorized.

---

## 9. Weighted median rule

FIN weighted median is exactly the engine frozen in E4A2E:

    sort by FIN
    compute cumulative normalized weight
    choose first FIN where cumulative share >= 0.5

It is estimated separately:

    in all five implicates
    in all 999 first-implicate sampling replicates

It receives the same MI + sampling variance construction.

---

## 10. Owner-renter contrast

For every age band and statistic:

Raw difference:

    renter - owner

Per implicate:

    delta_m
      = renter_m - owner_m

Point difference:

    mean(delta_1,...,delta_5)

Per sampling replicate:

    delta_r
      = renter_r - owner_r

The combined SE is calculated directly from these differences.

State-oriented difference:

    state_sign * raw_difference

This is only orientation, not a scalar construction.

Independent owner/renter SE combination is prohibited.

---

## 11. Exact output shape

Seven statistics x eight cohorts:

    56 cohort estimates

Five implicates per estimate:

    280 cohort implicate statistics

999 sampling replicates per estimate:

    55,944 cohort replicate statistics

Seven statistics x four age-band contrasts:

    28 renter-minus-owner differences

Five implicates per contrast:

    140 difference implicate statistics

999 replicates per contrast:

    27,972 difference replicate statistics

Totals:

    420 implicate statistics
    83,916 replicate statistics

Support:

    8 cohorts x 5 implicates = 40 rows

---

## 12. Outcome-independent PASS

There is NO gate on:

    K sign
    K magnitude
    D sign
    D magnitude
    renter-owner direction
    SE magnitude
    statistical significance
    agreement with the economic hypothesis
    dimensionality

Whatever K/D values are observed under the frozen estimator must be preserved.

Only source/schema, merge, implicate structure, replicate structure, finite
input, denominator, and exact-shape failures may block PASS.

---

## 13. After PASS

A complete PASS sets:

    K_EMPIRICALLY_TESTED=1
    D_EMPIRICALLY_TESTED=1
    I_EMPIRICALLY_TESTED=1

and authorizes only:

    E4A2G_KDI_COMPONENT_INFERENCE_CLOSEOUT_AUTHORIZED=1

Still false:

    K_SCALAR_AUTHORIZED
    D_SCALAR_AUTHORIZED
    K_D_I_INFERENCE_AUTHORIZED
    FIVE_DIMENSIONALITY_PROVEN
    REAL_INFLATION_ESTIMATION_AUTHORIZED
    FINAL_SCALAR_AUTHORIZED
