# E3A3 — Pseudo-Cohort Sample-Support Gate

## Status

Precommitted before any pseudo-cohort sample counts are opened.

No economic values are inspected in E3A3.

---

# Purpose

Prevent pseudo-cohort definitions from being selected because they happen to
produce convenient sample sizes.

Sample support is a design constraint, not an economic result.

---

# Support metrics

For weights w_i, define Kish effective sample size:

    n_eff = (sum_i w_i)^2 / sum_i(w_i^2)

Kish effective sample size is used ONLY as a conservative screening diagnostic.

It is NOT a substitute for survey-specific variance estimation.

Final inference must use the appropriate replicate-weight / complex-survey
methodology for CEX, CPS ASEC and SCF.

---

# Hard 2022 anchor thresholds

## CEX

    minimum unique Consumer Units = 200
    minimum Kish effective sample size = 100

## CPS ASEC

    minimum unique households = 500
    minimum Kish effective sample size = 250

## SCF

    minimum unique families = 100
    minimum Kish effective sample size = 50

A pseudo-cohort passes the cross-survey anchor gate only if all three survey
thresholds pass.

Thresholds may not be lowered after counts are opened.

---

# Statistical-unit rules

## CEX

NEWID must be preserved as a string.

The Consumer Unit identity is derived from the CU-sequence component of NEWID,
excluding the interview-number digit.

Repeated Interview Survey observations of the same CU are NOT independent
families.

For support counting:

    n_unique = number of unique underlying CUs within the cohort.

For the Kish support screen, repeated in-cell quarterly observations for the
same CU are first collapsed to one CU-level weight using the arithmetic mean of
FINLWT21 for that CU within the relevant support period.

Dividing all weights by a common calendar-year QNUM factor would not alter
Kish ESS and is therefore unnecessary for this screening calculation.

This rule is only for sample-support screening.

Final CEX estimation must separately follow the BLS calendar-year weighting and
variance methodology.

---

## CPS ASEC

The support unit is one household.

A household is counted once.

Cohort demographic characteristics must be derived through the designated
householder/reference-person rule after schema/code-mapping validation.

The canonical household weight must be used for the Kish support screen.

Replicate weights remain required for final standard errors.

---

## SCF

The support unit is one unique public SCF family, NOT one implicate record.

Five multiple-imputation implicates must never be counted as five families.

Family identity must use the public family identifier after exact schema
verification.

For cohort-defining variables:

    age band
    tenure/homeownership
    children status

a family is support-eligible only when cohort membership is unambiguous under
the five implicates.

If implicates disagree on a cohort-defining state:

    SUPPORT_MEMBERSHIP=AMBIGUOUS

and the family is excluded from that cohort's support count.

The canonical full-sample family weight is used once per unique family for the
Kish support screen.

Replicate weights and multiple-imputation combination remain mandatory for
final inference.

---

# Candidate age bands

The following age bands are frozen before counts:

    25-34
    35-44
    45-54
    55-64

Ages outside 25-64 are not part of the first canonical working-age household
experiment.

They may be studied later under a separately frozen extension.

---

# Candidate tenure states

Only:

    OWNER
    RENTER

are eligible for first canonical comparisons.

OTHER / UNKNOWN / unresolved tenure is excluded from primary cells.

Exact survey-specific code mappings must be frozen before counts are opened.

---

# Candidate children states

If supported:

    NO_CHILDREN
    CHILDREN_PRESENT

The children split is secondary to age and tenure.

Exact code mappings must be frozen before counts are opened.

---

# Granularity ladder

Counts may be inspected only for the following predeclared hierarchy:

## G1

    AGE_BAND × TENURE

## G2

    AGE_BAND × TENURE × CHILDREN_STATUS

No additional demographic dimension may be introduced after seeing counts.

In particular, E3A3 does NOT authorize count-driven addition of:

    income rank
    education
    race
    geography
    marital status
    occupation

Those require separate precommitments.

---

# First substantive comparison family

The first housing-access comparison is structurally targeted at:

    YOUNG_RENTER = age 25-34, RENTER

versus

    YOUNG_OWNER = age 25-34, OWNER

This keeps age fixed while changing tenure state.

A secondary lifecycle comparison may use:

    ESTABLISHED_OWNER = age 55-64, OWNER

No economic result has been inspected in selecting these targets.

---

# Children refinement rule

G2 may replace G1 only when BOTH:

    NO_CHILDREN
    CHILDREN_PRESENT

subcells required for the intended comparison pass all three survey support
thresholds.

If either required child-status subcell fails:

    use G1

The threshold may not be reduced to rescue G2.

---

# Historical-support rule

After the 2022 anchor audit passes, historical support must be assessed using
the SAME thresholds.

## CEX and CPS annual history

Tier A:

    every required year passes.

Tier B:

    at least 90% of required years pass;
    first required year passes;
    final required year passes;
    no run of more than 2 consecutive failed years.

Below Tier B:

    REJECT historical use at that granularity.

## SCF 1989-2022 waves

There are 12 canonical waves.

Tier A:

    12 / 12 waves pass.

Tier B:

    at least 10 / 12 waves pass;
    1989 passes;
    2022 passes.

Below Tier B:

    REJECT historical use at that granularity.

Primary longitudinal Real Inflation work requires Tier A.

Tier B may be reported only as robustness/exploratory evidence.

---

# Precommitted fallback

If G2 fails:

    fall back to G1.

If G1 age 25-34 × tenure fails for the young comparison:

    broaden BOTH young OWNER and RENTER jointly to age 25-44 × tenure.

Do not broaden only the failing side.

If age 25-44 × tenure still fails:

    the young tenure comparison is NOT CANONICAL.

For the established-owner secondary comparison:

    55-64 × OWNER
    -> fallback 45-64 × OWNER

If that fails:

    established-owner comparison is NOT CANONICAL.

No threshold reduction is authorized.

---

# Forbidden after counts open

After the first sample counts are opened, do NOT:

- lower minimum n;
- lower minimum Kish ESS;
- invent a new age band;
- drop a difficult historical wave;
- merge OWNER and RENTER;
- add an income filter to improve support;
- select a cohort because its economic result is more dramatic;
- treat five SCF implicates as five families.

---

# Next prerequisite

Counts remain closed until exact 2022 schema and code mappings are verified for:

    CPS ASEC
    SCF

and tenure/children/reference-person mappings are frozen for all three surveys.

Only after that mapping audit passes may E3A3 support counts be opened.
