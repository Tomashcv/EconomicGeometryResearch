# E3B4C1 — Exact BRR Engine Contract

## Parent

    6e2b4a3

## Purpose

Freeze the exact executable architecture for the first 44-replicate BRR run.

This milestone does not read WTREP values and does not calculate any standard
error, confidence interval, or inferential result.

---

# 1. Frozen point-estimator anchor

The BRR engine must reproduce the already validated E3B4A V2 full-sample point
estimates using FINLWT21 before any replicate-based uncertainty is accepted.

Frozen point-estimator outputs:

    E3B4A_V2_2022_component_point_estimates.tsv
    E3B4A_V2_2022_owner_renter_comparison.tsv

The BRR execution engine must recompute those statistics from raw PUMD using
the same code path that will later substitute WTREP01-WTREP44.

Required identity tolerance:

    absolute tolerance = 1e-8 USD

No separate hand-coded point-estimate path is authorized.

---

# 2. Replicate set

Exactly:

    WTREP01
    ...
    WTREP44

No missing replicate.
No extra replicate.
No replicate may be silently dropped.

---

# 3. Cohorts

Exactly:

    AGE25_34_OWNER
    AGE25_34_RENTER

Age:

    AGE_REF 25..34

Owner:

    CUTENURE in {1,2,3}

Renter:

    CUTENURE == 4

The cohort definition is identical for FINLWT21 and all 44 replicates.

---

# 4. Frozen primary UCC estimator map

Primary component UCCs:

    534 total

Estimator families:

    MTBI = 316
    ITBI =   3
    EXPD = 215

No UCC selection may change across replicates.

---

# 5. Interview replicate denominator

For cohort g and replicate r:

    denominator_I[g,r]
      = sum_i WTREP_r[i] / 4 * MO_SCOPE[i]

over the same cohort-filtered FMLI rows used by the point estimator.

MO_SCOPE is exactly the frozen calendar-year rule:

    2022 Jan = 0
    2022 Feb = 1/3
    2022 Mar = 2/3
    2022 Apr-Dec = 1

    2023 Jan = 1
    2023 Feb = 2/3
    2023 Mar = 1/3

No full-sample denominator may be reused for a replicate.

---

# 6. Diary replicate denominator

For cohort g and replicate r:

    denominator_D[g,r]
      = sum_i WTREP_r[i] / 4

over the same cohort-filtered FMLD rows.

No full-sample Diary denominator may be reused for a replicate.

---

# 7. MTBI replicate UCC estimate

For UCC j, cohort g, replicate r:

    numerator[j,g,r]
      = sum_i COST_i * WTREP_r[i]

after the same frozen:

    UCC filter
    REF_YR = 2022
    REF_MO = 1..12
    cohort join
    missing COST -> 0
    negative COST preserved

Then:

    mean[j,g,r]
      = numerator[j,g,r]
        / denominator_I[g,r]
        * hierarchy_factor[j]

---

# 8. ITBI replicate UCC estimate

For the 3 primary ITBI UCCs:

    numerator[j,g,r]
      = sum_i VALUE_i * WTREP_r[i]

after:

    REFYR = 2022
    REFMO = 1..12
    same cohort join

VALUE_ remains a diagnostic flag only.

Then:

    mean[j,g,r]
      = numerator[j,g,r]
        / denominator_I[g,r]
        * hierarchy_factor[j]

ITII is not appended.

---

# 9. EXPD replicate UCC estimate

For Diary UCC j:

    numerator[j,g,r]
      = sum_i COST_i * WTREP_r[i]

Then:

    mean[j,g,r]
      = numerator[j,g,r]
        / denominator_D[g,r]
        * 13
        * hierarchy_factor[j]

The x13 correction occurs inside every replicate.

---

# 10. Component integration

For component k, cohort g, replicate r:

    theta[k,g,r]
      = sum_{j in component k}
        mean[j,g,r]

Therefore component integration occurs before BRR variance calculation.

It is prohibited to compute UCC variances separately and sum them.

It is prohibited to compute Interview and Diary component variances separately
and add them post hoc.

---

# 11. Full-sample statistics

Full-sample component estimate:

    theta[k,g]

is recomputed by the exact same engine using FINLWT21.

It must match the frozen E3B4A V2 point estimate to absolute tolerance 1e-8.

---

# 12. BRR component variance

For each component/cohort statistic:

    Var(theta)
      = (1/44)
        * sum_{r=1}^{44}
          (theta_r - theta)^2

    SE(theta)
      = sqrt(Var(theta))

All 44 replicate values must be finite.

All 44 cohort/source replicate denominators must be finite and strictly
positive.

---

# 13. Owner-renter difference

For component k:

    delta[k]
      = renter[k] - owner[k]

For replicate r:

    delta[k,r]
      = renter[k,r] - owner[k,r]

Variance:

    Var(delta[k])
      = (1/44)
        * sum_r
          (delta[k,r] - delta[k])^2

Direct replicate covariance is preserved.

Prohibited:

    sqrt(SE_owner^2 + SE_renter^2)

as the primary difference SE.

---

# 14. Owner-renter ratio

For component k:

    rho[k]
      = renter[k] / owner[k]

For replicate r:

    rho[k,r]
      = renter[k,r] / owner[k,r]

If ratio inference is produced, its BRR variance is calculated directly from
the 44 ratio replicates.

No delta-method ratio approximation is primary.

---

# 15. First execution hard gates

The first BRR execution may PASS only if all are true:

    FULL_SAMPLE_COMPONENT_IDENTITY = PASS
    FULL_SAMPLE_COMPARISON_IDENTITY = PASS

    REPLICATE_COUNT = 44

    INTERVIEW_REPLICATE_DENOMINATORS_FINITE_POSITIVE = PASS
    DIARY_REPLICATE_DENOMINATORS_FINITE_POSITIVE = PASS

    COMPONENT_REPLICATE_ROWS = 176
        2 cohorts * 2 components * 44 replicates

    DIFFERENCE_REPLICATE_ROWS = 88
        2 components * 44 replicates

    RATIO_REPLICATE_ROWS = 88
        2 components * 44 replicates

    ALL_REPLICATE_COMPONENT_VALUES_FINITE = PASS
    ALL_REPLICATE_DIFFERENCES_FINITE = PASS
    ALL_REPLICATE_RATIOS_FINITE = PASS

    BRR_VARIANCE_NONNEGATIVE = PASS
    BRR_SE_FINITE = PASS

No sign, magnitude, CI width, or statistical significance criterion is a hard
gate.

---

# 16. Interpretation gates

Only after the executable BRR engine passes:

    COHORT_INFERENTIAL_INTERPRETATION_AUTHORIZED = 1

may be considered.

A BRR PASS still does NOT authorize:

    Real Inflation
    final five-dimensional scalar
    causal claims
    welfare claims

Observed expenditure is not itself inflation.

---

# 17. This milestone restrictions

    MICRODATA_DATA_ROWS_PARSED = 0
    COST_VALUES_READ = 0
    ITBI_VALUE_VALUES_READ = 0
    WTREP_VALUES_READ = 0

    STANDARD_ERRORS_COMPUTED = 0
    CONFIDENCE_INTERVALS_COMPUTED = 0
    P_VALUES_COMPUTED = 0

