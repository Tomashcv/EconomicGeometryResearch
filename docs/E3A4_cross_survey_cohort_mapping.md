# E3A4 — Cross-Survey Cohort Mapping

## Status

Written after E3A3 support thresholds were frozen and before any pseudo-cohort
support counts are opened.

No economic result is inspected in E3A4.

---

# Scope

This contract freezes the 2022 anchor mapping for the first canonical
pseudo-cohort experiment.

It does NOT assert that every variable/code has identical semantics throughout
1989-2022.

Historical harmonization must be audited separately before historical support
counts or longitudinal Real Inflation estimation.

---

# Canonical first-pass cohort

The canonical first-pass cohort granularity is:

    G1 = AGE_BAND × TENURE

Age bands:

    25-34
    35-44
    45-54
    55-64

Tenure:

    OWNER
    RENTER

OTHER / unresolved tenure is excluded.

---

# G2 children split

E3A3 allowed a possible:

    G2 = AGE_BAND × TENURE × CHILDREN_STATUS

only if semantically and statistically supported.

E3A4 finds that the available off-the-shelf children constructs are not
identical:

CEX:
    PERSLT18
    persons/children under 18 in the Consumer Unit

CPS:
    HUNDER18
    persons under age 18 in the household

SCF harmonized variable:
    KIDS
    natural/step/foster children of the reference person/spouse/partner

These do not represent the same statistical construct.

Therefore:

    G2_CANONICAL_AUTHORIZED = 0

This decision occurs BEFORE cohort counts are opened.

A later separately frozen extension may reconstruct a more closely harmonized
children/family-composition measure from lower-level survey variables.

---

# CEX 2022 anchor

Statistical unit:

    Consumer Unit

Underlying CU identifier:

    remove the final interview-number digit from NEWID

NEWID must remain a string so leading zeroes are preserved.

Reference age:

    AGE_REF

Weight:

    FINLWT21

Tenure mapping:

    CUTENURE in {1,2,3} -> OWNER

        1 = owned with mortgage
        2 = owned without mortgage
        3 = owned, mortgage status not reported

    CUTENURE == 4 -> RENTER

    CUTENURE in {5,6} -> OTHER

        5 = occupied without payment of cash rent
        6 = student housing

Missing/unexpected values:

    OTHER_OR_INVALID

E3A4 may inspect only the distinct CUTENURE category codes present in the
2022 FMLI files.

It may NOT report category frequencies or cohort counts.

---

# CPS ASEC 2022 anchor

Statistical unit:

    household

Household ID for within-file analysis:

    H_SEQ

Person-to-household join:

    PH_SEQ == H_SEQ

Reference person:

    A_EXPRRP in {1,2}

        1 = reference person with relatives
        2 = reference person without relatives

Exactly one eligible reference person is required for an analyzable household.

Reference age:

    A_AGE of that reference person

Weight:

    HSUP_WGT

The documented two implied decimal places are a scale factor and therefore do
not affect Kish effective sample size, but final estimators must interpret the
weight correctly.

Eligible household universe:

    H_HHTYPE == 1

Tenure mapping:

    H_TENURE == 1 -> OWNER
    H_TENURE == 2 -> RENTER
    H_TENURE in {0,3} -> OTHER_OR_INVALID

where:

    0 = not in universe
    3 = no cash rent

---

# SCF 2022 anchor

Statistical unit:

    unique family / Primary Economic Unit

Public family ID:

    YY1

Implicate-specific ID:

    Y1

Five implicates belonging to the same YY1 are NOT five families.

Reference age:

    X14

Weight:

    X42001

For joint use of all five implicates the Federal Reserve harmonized program
defines:

    WGT = X42001 / 5

For one-row-per-family Kish support screening, multiplication/division of all
weights by a common factor is irrelevant.

---

## SCF OWNER

Use the exact ownership logic from the Federal Reserve harmonized HOUSECL
definition.

OWNER if ANY of:

    X508 in {1,2}

or:

    X601 in {1,2,3}

or:

    X701 in {1,3,4,5,6,8}

or:

    X701 == -7 AND X7133 == 1

This corresponds to ownership of all or part of the principal residence,
including farm/ranch, mobile-home arrangements, house, condo, co-op, etc.

---

## SCF RENTER

A strict categorical renter definition is used.

RENTER if OWNER is false and ANY of:

    X508 == 3
        farm/ranch: rents/leases all

    X601 == 4
        mobile-home branch: rents both home and site

    X701 == 2
        conventional housing branch: pays rent

No dollar rent amount is used to define cohort membership.

---

## SCF OTHER

Any family that is neither OWNER nor strict RENTER is:

    OTHER

Examples include some:

    sharecropper
    business-owned housing
    neither-own-nor-rent arrangements
    unresolved/nonstandard tenure

OTHER is excluded from the canonical OWNER-vs-RENTER comparison.

---

# SCF implicate agreement gate

For each YY1, derive age band and tenure independently in all five implicates.

A family is support-eligible only if all available implicates agree on:

    AGE_BAND
    TENURE

If not:

    SUPPORT_MEMBERSHIP = AMBIGUOUS

and the family is excluded from G1 support counting.

The five implicates are never counted separately.

---

# Canonical comparisons

Primary:

    YOUNG_RENTER
        age 25-34
        RENTER

versus:

    YOUNG_OWNER
        age 25-34
        OWNER

Secondary:

    ESTABLISHED_OWNER
        age 55-64
        OWNER

Fallbacks remain exactly those frozen in E3A3.

---

# Forbidden

Before the E3A5 support-count opening:

- no cohort counts;
- no category frequencies;
- no economic means or medians;
- no expenditure statistics;
- no income statistics;
- no wealth/debt statistics;
- no threshold changes;
- no new demographic dimensions.

---

# E3A4 pass consequence

If this mapping audit passes:

    E3A5_2022_SUPPORT_COUNTS_AUTHORIZED = 1

Only the already-frozen G1 cells and fallbacks may then be counted.
