# E3B4B R3A — Exact 2022 ITBI Schema Forensic

## Trigger

E3B4B R3 attempt 1 stopped before economic execution because the contract
incorrectly assumed that ITBI shared MTBI field names:

    COST
    REF_MO

The actual 2022 ITBI schema rejected this assumption.

This is a schema failure only.

No economic hypothesis failed.

---

## Objective

Inspect headers only for:

    ITBI221
    ITBI222
    ITBI223
    ITBI224
    ITBI231

and freeze the exact field spelling used by the 2022 PUMD.

No ITBI data row may be parsed.

---

## Expected semantic concepts

The required concepts are:

    consumer-unit identifier
    UCC
    monthly reference month
    monthly reference year
    released point value

Candidate historical BLS spellings include:

    NEWID
    UCC
    REFMO
    REFYR
    VALUE

but the local 2022 archive bytes are canonical for exact spelling.

---

## Important distinction

MTBI uses expenditure schema such as:

    COST
    REF_MO
    REF_YR

ITBI must NOT be forced into the MTBI schema.

ITII is not appended to ITBI for the point estimate.

---

## Restrictions

    DATA_ROWS_PARSED = 0
    COST_VALUES_READ = 0
    ITBI_VALUE_VALUES_READ = 0
    NEW_ECONOMIC_VALUES_OPENED = 0

No estimator V2 execution is authorized by R3A alone.

