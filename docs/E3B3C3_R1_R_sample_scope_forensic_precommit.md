# E3B3C3 R1 — Official R UCC Sample-Code Scope Forensic

## Trigger

The original E3B3C3 precommit required one official R sample-code archive to
contain direct evidence of:

    FINLWT21
    WTREP
    MO_SCOPE
    UCC
    COST
    Diary x13
    hierarchy factor

The downloaded official BLS archive passed transport but failed that composite
gate.

This failure is preserved.

No COST values were opened.

---

## Frozen official source

Archive:

    data/raw/cex/sample_code/r-ucc.zip

SHA256:

    c2d8021f52b0118e8e73ce743de63cf872a2b8c668314f0977193ca54fc46a85

Archive member:

    R UCC/calendar_year_estimate_ucc.R

Member SHA256:

    633e70db439a55a7910684a39e7c0609d59768d61e1db929b756c0e13c59b92e

---

## R1 question

Determine what the downloaded R file itself actually implements.

This is a source-scope forensic, not a relaxed PASS criterion.

The forensic must distinguish:

    direct code evidence

from:

    external BLS methodology evidence.

---

## Direct-code evidence to test

Audit the R source for:

    FMLI
    MTBI
    FMLD
    EXPD

and for the calendar-year weighting operations:

    QINTRVMO
    QINTRVYR
    FINLWT21 / 4
    first-quarter partial scope
    fifth-quarter partial scope
    sum(COST * FINLWT21) / sum(POPWT)

Also audit direct appearances of:

    WTREP
    FACTOR
    Diary x13

---

## Interpretation rule

If the code contains FMLI + MTBI but not FMLD + EXPD, it must NOT be called a
self-contained Interview+Diary implementation merely because the BLS web page
describes the sample-code family as integrated.

The downloaded source bytes control the classification of the downloaded file.

---

## External methodology

Current BLS PUMD documentation separately specifies:

    Interview and Diary are independent samples;
    integration is performed UCC-by-UCC;
    Diary weekly estimates require x13 for quarterly comparability;
    annual population denominator uses QNUM and MO_SCOPE;
    BRR uses WTREP01-WTREP44;
    hierarchy factor is x1 or x4.

These external rules are not required to appear literally inside the R file.

---

## Consequence

Even if this R1 forensic passes:

    EXACT_INTEGRATED_ESTIMATOR_IMPLEMENTATION_FROZEN = 0
    COST_VALUES_AUTHORIZED = 0

A later source-reconciliation milestone must determine the exact integrated
implementation from all relevant official evidence.

---

## Disclosure

    MICRODATA_DATA_ROWS_PARSED = 0
    COST_VALUES_READ = 0
    ECONOMIC_VALUES_OPENED = 0
    REAL_INFLATION_ESTIMATED = 0

