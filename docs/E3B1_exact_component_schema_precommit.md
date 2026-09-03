# E3B1 — Exact Component Schema Audit

## Status

Written after E3B0 and before any household economic values are opened.

This milestone verifies only:

- exact variable existence;
- file/family location;
- official labels where available;
- raw-vs-harmonized variable provenance.

It does NOT select final formulas.

---

# Disclosure prohibition

E3B1 must not calculate or disclose:

- income values;
- expenditure values;
- rent values;
- house values;
- asset values;
- debt values;
- means;
- medians;
- distributions;
- cohort economic estimates;
- Real Inflation.

Allowed operations:

- CEX first-record header only;
- Census metadata API only;
- SCF Stata metadata / variable labels only.

    DATA_ROWS_PARSED = 0
    ECONOMIC_VALUES_OPENED = 0

---

# CEX candidate schema

## FMLI support/context fields

Required:

    NEWID
    AGE_REF
    CUTENURE
    FINLWT21

## MTBI expenditure fields

Required:

    NEWID
    UCC
    COST
    REF_MO
    REF_YR

Interpretation at this gate:

    UCC
        expenditure classification key

    COST
        expenditure amount field

    REF_MO / REF_YR
        expenditure reference month/year

No COST observation may be read in E3B1.

No UCC category is yet classified as housing/nonhousing.

Therefore:

    CEX_UCC_COMPONENT_MAPPING_FROZEN = 0

---

# CPS ASEC candidate schema

## Household resource candidates

Required:

    H_SEQ
    HSUP_WGT
    H_HHTYPE
    H_TENURE
    HTOTVAL

HTOTVAL is only a candidate household-resource concept.

E3B1 does NOT yet declare gross household income to be the final
Resources_g(t) definition.

---

## Reference-person and income-security candidates

Required:

    PH_SEQ
    A_AGE
    A_EXPRRP

Current-status candidates:

    A_LFSR
    A_WKSTAT

Previous-year work-experience candidates:

    WORKYN
    WEWKRS
    WEUEMP
    WEXP
    WTEMP

E3B1 verifies existence only.

Current-status and previous-year variables must not be mixed into one
contemporaneous index without a later timing contract.

---

# SCF harmonized candidate schema

The Federal Reserve summary extract is treated as a harmonized-variable source.

Required identifiers / demographic context:

    Y1
    YY1
    WGT
    AGE
    HOUSECL

## K candidates

    ASSET
    FIN
    LIQ
    STOCKS
    RETQLIQ
    EQUITY
    HLIQ
    TURNDOWN
    FEARDENIAL

## D candidates

    DEBT
    DEBT2INC
    PIRTOTAL
    PIRMORT
    MRTHEL
    LATE60

## H balance-sheet candidates

    HOUSES
    HOMEEQ
    NETWORTH

These are not automatically final component formulas.

No SCF observation may be loaded in E3B1.

---

# Important provenance distinction

SCF variables such as:

    ASSET
    FIN
    DEBT
    PIRTOTAL
    HOMEEQ

are harmonized/constructed variables from the Federal Reserve summary
program/extract.

They are not equivalent to individual raw questionnaire X-fields.

Future historical work should prefer documented harmonized constructions
where cross-wave comparability is required.

---

# Gate consequences

E3B1 PASS means only:

    required candidate fields exist in the 2022 anchor sources.

It does NOT mean:

    candidate semantic interpretation is final;
    component formula is final;
    cross-wave availability is proven;
    Real Inflation can be estimated.

After PASS, E3B2 must freeze:

- exact CEX UCC component mappings;
- housing exclusion rules;
- CPS Resources definition;
- I timing/aggregation rule;
- K formula candidates;
- D sign normalization;
- treatment of SCF harmonized variables;
- cross-wave availability requirements.

