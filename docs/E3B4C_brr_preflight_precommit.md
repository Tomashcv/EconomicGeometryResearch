# E3B4C — BRR 44-Replicate Preflight

## Parent

    f6482ce

## Purpose

Freeze the exact Balanced Repeated Replication architecture required for final
CEX inference before calculating any standard errors.

This milestone does NOT read replicate-weight values and does NOT calculate
replicate estimates.

---

# Official BLS methodology

The Consumer Expenditure Surveys use Balanced Repeated Replication.

Current BLS PUMD methodology states:

    44 balanced half-samples
    replicate weights WTREP01-WTREP44
    estimate the statistic separately for every replicate
    compare every replicate estimate with the full-sample estimate

Variance:

    Var(theta_hat)
      = (1 / 44)
        * sum_{r=1}^{44}
          (theta_hat_r - theta_hat)^2

Standard error:

    SE(theta_hat)
      = sqrt(Var(theta_hat))

Official sources:

    https://www.bls.gov/cex/pumd-getting-started-guide.htm
    https://www.bls.gov/opub/hom/cex/calculation.htm
    https://www.bls.gov/cex/research_papers/pdf/consumer-expenditure-survey-anthology-2003.pdf

---

# Replicate estimator principle

A replicate mean is NOT:

    full-sample numerator / replicate denominator

and NOT:

    replicate numerator / full-sample denominator

For replicate r, both numerator and population denominator are recomputed using
the same WTREPr weight.

Therefore:

    numerator_r   = weighted numerator using WTREPr
    denominator_r = weighted population denominator using WTREPr

    mean_r = numerator_r / denominator_r

For Interview calendar-year estimates, the same frozen MO_SCOPE calendar
fraction used in the full-sample denominator is applied to WTREPr.

For Diary estimates, the same replicate weight is used in numerator and
denominator, and the x13 weekly-to-quarter periodicity correction remains
inside every replicate estimate.

---

# Integrated components

Official BLS methodology first estimates each UCC and then sums UCC estimates
to form an integrated estimate.

Therefore for component k and replicate r:

    theta_{k,r}
       = sum_j theta_{j,r}

across the frozen Interview/Diary source-selected UCCs.

The BRR variance is then calculated on the 44 integrated component replicate
estimates:

    Var(theta_k)
      = 1/44 * sum_r (theta_{k,r} - theta_k)^2

It is prohibited to estimate separate Interview and Diary variances and simply
add those variances after the fact.

Integration occurs inside each replicate.

---

# Full-sample versus replicate weights

    full-sample point estimate: FINLWT21

    replicate 01: WTREP01
    ...
    replicate 44: WTREP44

All 44 replicate fields must exist in every required FMLI and FMLD family
header.

---

# Cohort inference

The cohort definition itself is frozen and held constant across all
replicates.

For every replicate:

    same AGE_REF filter
    same CUTENURE mapping
    same UCC map
    same estimator-family map
    same hierarchy factors
    same calendar timing rules
    same periodicity rules

Only the survey weight changes from FINLWT21 to WTREPr.

---

# Difference estimator

For owner-versus-renter component difference:

    delta
      = renter_mean - owner_mean

replicate r:

    delta_r
      = renter_mean_r - owner_mean_r

Variance must be computed directly from the 44 replicate differences:

    Var(delta)
      = 1/44 * sum_r (delta_r - delta)^2

It is prohibited to calculate:

    SE(delta)
      = sqrt(SE_owner^2 + SE_renter^2)

because BRR replicate covariance must be retained.

---

# Ratio estimator

For descriptive renter/owner ratio:

    rho = renter_mean / owner_mean

If inferential ratio uncertainty is later produced:

    rho_r = renter_mean_r / owner_mean_r

and BRR variance is calculated directly from rho_r.

No delta-method shortcut is primary.

---

# Confidence intervals

After BRR engine validation:

    CI95 = estimate +/- 1.96 * SE

may be reported as a conventional normal-approximation interval.

The project must report SE and CI before using language such as statistically
distinguishable.

P-values are not required for the primary analysis.

---

# Restrictions

    MICRODATA_DATA_ROWS_PARSED = 0
    COST_VALUES_READ = 0
    ITBI_VALUE_VALUES_READ = 0
    WTREP_VALUES_READ = 0

    STANDARD_ERRORS_COMPUTED = 0
    CONFIDENCE_INTERVALS_COMPUTED = 0

    NAIVE_IID_STANDARD_ERRORS = PROHIBITED
    SOURCE_VARIANCE_POSTHOC_SUM = PROHIBITED

If this preflight passes, the next milestone may freeze the exact executable
BRR engine contract.

