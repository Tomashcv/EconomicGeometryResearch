# E3B4B R3B — ITBI Point-Value Semantics

## Parent

    b070223

## Trigger

R3A froze the exact 2022 ITBI schema:

    NEWID
    REFMO
    REFYR
    UCC
    PUBFLAG
    VALUE
    VALUE_

with:

    ITBI_REFERENCE_MONTH_FIELD = REFMO
    ITBI_REFERENCE_YEAR_FIELD  = REFYR
    ITBI_POINT_VALUE_FIELD     = VALUE

No data rows were parsed.

---

# 1. Official BLS semantic evidence

Official BLS PUMD documentation describes ITBI as:

    detailed income
    monthly
    classified by UCC

and shows ITBI records with:

    NEWID
    UCC
    REFMO / REFYR
    VALUE
    VALUE_

The BLS documentation states that:

    VALUE  = released numerical point value
    VALUE_ = indicator showing whether VALUE was topcoded

VALUE_ is not an alternative numerical estimate.

Sources reviewed 2026-08-29:

    https://www.bls.gov/cex/pumd-getting-started-guide.htm
    https://www.bls.gov/cex/introduction-to-microdata.pdf
    https://www.bls.gov/cex/pumd_novice_guide.pdf
    https://www.bls.gov/cex/pumd_disclosure.htm

---

# 2. ITII distinction

Official BLS documentation identifies ITII as:

    imputed income iterations

with:

    five imputes per income item
    IMPNUM identifying the iteration

ITII is needed for variance / standard-error treatment of imputed income.

Therefore for the ordinary point estimator:

    ITBI VALUE = point-value source
    ITII append = PROHIBITED

Appending all ITII rows to ITBI would duplicate multiple imputations and is
not a valid point estimator.

---

# 3. V2 normalization

Estimator V2 may normalize different physical schemas internally:

## MTBI

    point_value = COST
    reference_month = REF_MO
    reference_year = REF_YR

## ITBI

    point_value = VALUE
    reference_month = REFMO
    reference_year = REFYR

## EXPD

    point_value = COST

This normalization is an implementation abstraction only.

The source columns remain distinct and auditable.

---

# 4. Topcoding

VALUE_ is retained as diagnostic metadata.

Primary ITBI point estimation does NOT:

    replace VALUE with VALUE_
    drop rows solely because VALUE_ indicates topcoding
    reconstruct confidential pre-topcode values

The released VALUE is used as supplied by BLS.

---

# 5. Restrictions

R3B is source/schema forensic only:

    DATA_ROWS_PARSED = 0
    COST_VALUES_READ = 0
    ITBI_VALUE_VALUES_READ = 0
    NEW_ECONOMIC_VALUES_OPENED = 0

If R3B passes, it authorizes repair of the already-precommitted R3 contract.

It does NOT authorize corrected benchmark execution directly.

