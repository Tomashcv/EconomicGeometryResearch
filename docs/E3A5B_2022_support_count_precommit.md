# E3A5B — 2022 Pseudo-Cohort Support Count Opening

## Status

Written after:

    E3A3 support thresholds frozen
    E3A4 cohort mappings frozen
    E3A5A source/schema inventory frozen

and before any pseudo-cohort support counts are opened.

---

# Objective

Open only the statistical-support quantities needed to determine whether the
predeclared AGE_BAND × TENURE cohorts are viable.

Authorized outputs:

    unique statistical-unit count
    Kish effective sample size
    threshold PASS/FAIL
    precommitted fallback selection

Unauthorized:

    income
    expenditure
    rent amount
    house value
    assets
    debt
    net worth
    economic means/medians
    Real Inflation

---

# Frozen source hashes

CEX 2022 Interview:

    c99a2f47c0084b7a88812b34c56a1a288be2798ff010b2b59dcf87e072773e17

CPS ASEC 2022:

    61b6b6ba8ae70eb1b37acca8144163bb5c260d742b33152c639bebccc0a1fbb5

SCF 2022 full:

    409e6811df895766d50b2f597c10b1b3c5813e7d3e0e45d910ad26c0cb07f4eb

SCF 2022 summary:

    3bb4d890ae2463ff6039ec7692e375f544dd98a55a37ca2cb2340354b9cc9d80

---

# Frozen design-contract hashes

E3A3 thresholds:

    f0abc60abf21a38c1f1268f1f299f3ceeee18b558b796daa0cbeb943e635ffa4

E3A4 mapping:

    12783a626edf3af3b8dccadfbe3d084c1b2af493a1e51966a963b20226f1c97e

No support count may be opened if any frozen input hash differs.

---

# Thresholds

CEX:

    n >= 200
    Kish ESS >= 100

CPS ASEC:

    n >= 500
    Kish ESS >= 250

SCF:

    n >= 100
    Kish ESS >= 50

---

# Cohorts

Base:

    25-34 OWNER
    25-34 RENTER

    35-44 OWNER
    35-44 RENTER

    45-54 OWNER
    45-54 RENTER

    55-64 OWNER
    55-64 RENTER

Frozen fallbacks:

    25-44 OWNER
    25-44 RENTER
    45-64 OWNER

No other grouping is authorized.

---

# CEX parser

Input:

    FMLI only

Permitted variables:

    NEWID
    AGE_REF
    CUTENURE
    FINLWT21

Underlying CU:

    NEWID without final interview digit

For every underlying CU:

1. derive AGE_BAND × TENURE for every observed interview;
2. require identical membership across observations;
3. otherwise mark CU ambiguous and exclude;
4. use mean positive FINLWT21 across its observations as the support-screen
   weight.

No expenditure field is read.

---

# CPS ASEC parser

Official ASCII positions are interpreted as one-based positions in the Census
dictionary.

Household record:

    record type   position 1, length 1
    H_SEQ         position 29, length 5
    HSUP_WGT      position 34, length 8
    H_HHTYPE      position 61, length 1
    H_TENURE      position 89, length 1

Person record:

    record type   position 1, length 1
    PH_SEQ        position 36, length 5
    A_AGE         position 79, length 2
    A_EXPRRP      position 82, length 2

Eligible household:

    H_HHTYPE == 1

Reference person:

    exactly one person with A_EXPRRP in {1,2}

Person-household join:

    PH_SEQ == H_SEQ

HSUP_WGT has two implied decimal places.

That common scaling does not affect Kish ESS.

No income field is parsed.

---

# SCF parser

Permitted full-file variables:

    Y1
    X14
    X508
    X601
    X701
    X7133
    X42001

Permitted summary-file variables:

    Y1
    YY1

No other SCF field is loaded.

Join:

    full.Y1 == summary.Y1

Statistical family:

    YY1

Exactly five implicates are required.

AGE_BAND and TENURE are derived independently for every implicate.

All five must agree.

Otherwise:

    SUPPORT_MEMBERSHIP=AMBIGUOUS

and the family is excluded.

X42001 must be internally consistent across the family's five implicates.

One weight is used per unique YY1 for Kish support screening.

---

# Tenure mappings

Exactly E3A4.

CEX:

    1,2,3 -> OWNER
    4     -> RENTER
    other -> excluded

CPS:

    1 -> OWNER
    2 -> RENTER
    other -> excluded

SCF OWNER:

    X508 in {1,2}

or:

    X601 in {1,2,3}

or:

    X701 in {1,3,4,5,6,8}

or:

    X701 == -7 and X7133 == 1

SCF strict RENTER, conditional on OWNER=false:

    X508 == 3

or:

    X601 == 4

or:

    X701 == 2

---

# Selection

Young primary:

    25-34 OWNER
    25-34 RENTER

If both pass in all three surveys:

    YOUNG_CANONICAL=25-34

Otherwise test the already-frozen joint fallback:

    25-44 OWNER
    25-44 RENTER

If both pass:

    YOUNG_CANONICAL=25-44_FALLBACK

Otherwise:

    YOUNG_CANONICAL=REJECTED

Established owner:

    55-64 OWNER

Fallback:

    45-64 OWNER

No threshold mutation is permitted after output opening.

