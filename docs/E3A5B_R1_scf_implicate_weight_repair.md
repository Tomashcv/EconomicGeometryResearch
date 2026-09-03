# E3A5B R1 — SCF Implicate-Weight Repair

## Trigger

E3A5B attempt 1 aborted before producing a support table.

Observed failure:

    SCF X42001 inconsistent across implicates

The original implementation incorrectly required X42001 to be identical
within all five implicates of one YY1 family.

No pseudo-cohort counts or Kish ESS values were disclosed.

No economic variables were loaded.

---

## Official SCF semantics

The 2022 SCF codebook states that the record IDs satisfy:

    implicate = Y1 - 10 * YY1

with implicate in:

    {1,2,3,4,5}

The SCF analysis weight X42001 applies within each implicate.

The Federal Reserve methodology treats the five implicates separately when
forming exact multiply-imputed estimates.

Therefore exact equality of X42001 across implicates is NOT a valid structural
requirement.

---

## Repair

The following remain unchanged:

- unique family = YY1;
- exactly five implicates required;
- AGE_BAND × TENURE is derived independently in every implicate;
- all five memberships must agree;
- ambiguous families are excluded;
- E3A3 thresholds remain unchanged;
- E3A4 tenure mappings remain unchanged.

For SCF support screening:

    n_unique

is the number of unique eligible YY1 families.

Kish ESS is computed separately within each implicate:

    ESS_j = (sum_i w_ij)^2 / sum_i(w_ij^2)

for:

    j = 1,...,5

The canonical SCF support-screen ESS is:

    ESS_SCF = min(ESS_1, ESS_2, ESS_3, ESS_4, ESS_5)

This minimum rule is deliberately conservative and is frozen before any
implicate-specific ESS values are opened.

It is a project support-screen rule, not an official SCF variance estimator.

Final SCF inference will still require the Federal Reserve replicate-weight
and multiple-imputation methodology.

---

## Disclosure state

At the E3A5B attempt-1 failure:

    SUPPORT_TABLE_CREATED = 0
    SUPPORT_COUNTS_DISCLOSED = 0
    KISH_ESS_DISCLOSED = 0
    ECONOMIC_VALUES_OPENED = 0

The failed attempt is preserved and is not relabeled PASS.
