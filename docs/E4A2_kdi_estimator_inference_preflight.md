# E4A2 — K / D / I Exact Estimator + Inference Preflight

## Parent

    887e512

No K, D or I economic values are opened in this milestone.

No replicate-weight values are opened.

---

# 1. SCF point-estimate architecture

Official Federal Reserve guidance requires statistics to be calculated
separately for each of the five implicates using X42001.

For statistic theta and implicate m:

    theta_m = weighted statistic using X42001 within implicate m

Final point estimate:

    theta = (1/5) * sum_{m=1..5}(theta_m)

The five implicates must never be treated as five independent families.

Using X42001/5 over the pooled five-implicate file is allowed by Federal
Reserve guidance for means and frequencies, but the project primary
implementation will use the explicit per-implicate method because it keeps
multiple-imputation structure visible and supports later uncertainty
decomposition.

---

# 2. Frozen SCF cohorts

Family identity:

    YY1

Implicate identity:

    IMPLIC = Y1 - 10*YY1

Required implicates:

    1,2,3,4,5

Age:

    X14

Tenure classification remains the previously frozen SCF raw logic.

No cohort definition may change based on K or D outcomes.

---

# 3. K estimator

Primary raw variable:

    FIN

Primary cohort statistic:

    weighted mean FIN

For each implicate:

    K_FIN_MEAN_m
      = sum(X42001 * FIN) / sum(X42001)

Final:

    K_FIN_MEAN
      = mean(K_FIN_MEAN_1 .. K_FIN_MEAN_5)

Direction:

    higher = better capital position

Sensitivity variables:

    LIQ
    EQUITY
    RETQLIQ

using the same weighted-mean estimator.

Because financial assets are highly skewed:

    weighted median FIN

must later be produced as a robustness statistic before any strong
dimensionality claim based on K.

The weighted mean remains primary.

NETWORTH and ASSET remain prohibited as primary K.

---

# 4. D estimator

Primary raw variable:

    PIRTOTAL

For each implicate:

    PIRTOTAL_MEAN_m
      = sum(X42001 * PIRTOTAL) / sum(X42001)

Final raw cohort burden:

    PIRTOTAL_MEAN
      = mean(PIRTOTAL_MEAN_1 .. PIRTOTAL_MEAN_5)

State orientation:

    D_PRIMARY = -PIRTOTAL_MEAN

Therefore:

    higher D = better debt-service position

Secondary:

    DEBT2INC

using the same estimator and sign:

    D_SECONDARY = -weighted_mean(DEBT2INC)

DEBT dollars remain diagnostic only.

---

# 5. SCF owner-renter contrasts

For each implicate m, contrasts are constructed within implicate:

    delta_m
      = statistic_RENTER_m - statistic_OWNER_m

The full-sample contrast is:

    delta
      = mean(delta_1 .. delta_5)

Do not subtract independently pooled five-implicate samples using a method
that discards the implicate pairing.

---

# 6. SCF sampling + imputation inference

Correct SCF inference requires BOTH:

    multiple-imputation uncertainty
    sampling uncertainty

Sampling uncertainty requires the separate official replicate-weight file.

Official 2022 architecture:

    999 bootstrap replicates
    sampling variability evaluated on first implicate
    multiple-imputation variability evaluated across all five implicates

The current local project does not yet contain the official SCF replicate
weight archive.

Therefore:

    SCF_STANDARD_ERRORS_AUTHORIZED = 0

until the official file is acquired and its schema/current 2022 codebook
implementation is audited.

No ad-hoc simplified sampling variance denominator is frozen at E4A2.

The exact 2022 implementation will be frozen after inspecting the official
replicate-weight schema and standard-error code/documentation.

---

# 7. CPS I point estimator

Unit:

    household pseudo-cohort represented by CPS reference person

Reference person:

    A_EXPRRP in {1,2}

Weight:

    HSUP_WGT

Denominator:

    all valid frozen-cohort reference-person households

This denominator is NOT restricted only to workers.

---

# 8. I_FYFT_SHARE

Numerator indicator:

    1[WEWKRS == 1]

Point estimate:

    sum(HSUP_WGT * 1[WEWKRS == 1])
    --------------------------------
              sum(HSUP_WGT)

within the frozen cohort.

Direction:

    higher = stronger realized annual employment attachment

WEWKRS numeric means remain prohibited.

---

# 9. I_SEARCH_BURDEN_SHARE

Numerator indicator:

    1[WEUEMP in {2,3,4,5,6,7}]

Point estimate:

    sum(HSUP_WGT * indicator)
    ---------------------------
           sum(HSUP_WGT)

within the frozen cohort.

Direction:

    higher raw share = worse

State orientation:

    sign = -1

WEUEMP numeric means remain prohibited.

---

# 10. Secondary I estimands

Long search:

    I_LONG_SEARCH_SHARE
      = weighted share WEUEMP in {6,7}

Any work:

    I_ANY_WORK_SHARE
      = weighted share WRK_CK == 1

Cardinal fields:

    WKSWORK
    LKWEEKS
    NWLKWK

remain sensitivity-only until their universes are explicitly reconstructed.

NIU must not be silently converted to zero.

---

# 11. CPS replicate inference

Official CPS ASEC 2022 methodology uses:

    160 replicate weights

For any statistic theta:

    theta_0 = full-sample estimate
    theta_r = same statistic recomputed using replicate r

Variance:

    Var(theta_0)
      = (4/160)
        * sum_{r=1..160}
          (theta_r - theta_0)^2

SE:

    sqrt(Var)

For proportions, both numerator AND denominator must be recomputed with the
same replicate weight.

Owner-renter differences must be computed directly inside each replicate:

    delta_r
      = renter_r - owner_r

and variance calculated from the 160 delta_r values.

Independent-SE shortcuts are prohibited.

The exact household replicate field names and merge keys will be frozen only
after the official replicate-weight archive/instructions are locally audited.

---

# 12. Local inference dependency

Current canonical main data:

    CPS:
      data/raw/cps_asec/2022/asec2022_pubuse.zip

    SCF full:
      data/raw/scf/2022/scf2022s.zip

    SCF summary:
      data/raw/scf/2022/scfp2022s.zip

Required additional inference assets:

    data/raw/scf/2022/scf2022rw1s.zip

    data/raw/cps_asec/2022/CPS_ASEC_ASCII_REPWGT_2022.ZIP

They must come only from official Federal Reserve / Census sources.

---

# 13. Economic-open boundary

Even if this preflight passes:

    K_VALUES_OPEN_AUTHORIZED = 0
    D_VALUES_OPEN_AUTHORIZED = 0
    I_VALUES_OPEN_AUTHORIZED = 0

First required:

    official replicate-weight acquisition
    hash freeze
    schema audit
    merge-key audit
    exact inference engine contract

---

# 14. Dimensionality boundary

No dimensionality outcome has been opened.

Still:

    K_EMPIRICALLY_TESTED = 0
    D_EMPIRICALLY_TESTED = 0
    I_EMPIRICALLY_TESTED = 0
    FIVE_DIMENSIONALITY_PROVEN = 0

No correlation / PCA / rank / redundancy result is authorized yet.

