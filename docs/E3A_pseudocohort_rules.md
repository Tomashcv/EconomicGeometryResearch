# E3A — Pseudo-Cohort Design Rules

## Core idea

Pseudo-cohort g is a set of independently sampled statistical units from each
survey that share a harmonized economic definition.

Example form only:

    g = (
        reference_age_band,
        tenure,
        children_status
    )

This is NOT yet the final cohort definition.

---

## Candidate core dimensions

Priority 1:

    reference-person age
    housing tenure
    children presence

Priority 2, only after harmonization audit:

    marital/partner status
    family size
    income rank

---

## Why income rank is not automatically part of cohort identity

If cohort membership is defined using contemporaneous nominal income, inflation
and income movements can mechanically move households between cells.

Income-based cohort definitions therefore require a frozen rank or real-income
protocol before use.

No such protocol is authorized in E3A.

---

## Sample-support gate

No pseudo-cohort becomes canonical merely because it is economically
interesting.

Before E3B freezes cohort definitions, each candidate must pass a sample-support
audit separately in CEX, CPS and every required SCF wave.

The minimum effective sample-size rule will be frozen before candidate cell
counts are opened.

---

## Reference person

Use the survey reference-person concept as the default age anchor.

Do not average spouse/reference-person ages unless explicitly justified in a
future contract.

---

## Tenure

Target harmonized high-level states:

    OWNER
    RENTER
    OTHER_OR_UNRESOLVED

Mortgage/no-mortgage may later refine OWNER, but only where cross-time
availability is sufficient.

---

## Children

Target first-pass harmonization:

    NO_CHILDREN
    CHILDREN_PRESENT

Detailed child counts or ages may be added only after availability audit.

---

## Direct cross-survey joins

PROHIBITED.
