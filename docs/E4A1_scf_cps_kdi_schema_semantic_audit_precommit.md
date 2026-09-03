# E4A1 — SCF / CPS K-D-I Schema + Semantic Audit

## Parent

    ff5130b

## Purpose

Audit actual local 2022 SCF/CPS sources and reconcile the frozen E4A
architecture with official variable semantics.

No K/D/I economic values are opened.

This milestone is permitted to falsify E4A assumptions.

A semantic mismatch is a valid scientific FAIL and must not be repaired
silently.

---

# Local canonical files

CPS ASEC:

    data/raw/cps_asec/2022/asec2022_pubuse.zip
        member: asec2022_pubuse.dat

SCF full:

    data/raw/scf/2022/scf2022s.zip
        member: p22i6.dta

SCF summary:

    data/raw/scf/2022/scfp2022s.zip
        member: rscfp2022.dta

---

# SCF schema expectations

Full public file must expose:

    Y1
    X42001
    X14
    X508
    X601
    X701
    X7133

Summary extract must expose:

    Y1
    YY1
    WGT

    FIN
    LIQ
    EQUITY
    RETQLIQ

    PIRTOTAL
    DEBT2INC
    DEBT

    HOUSES
    HOMEEQ

No values are read.

Stata headers/metadata only.

---

# SCF structure

Frozen identity from prior validated support work:

    family = YY1
    implicate = Y1 - 10*YY1

Expected implicates:

    1..5

X42001 remains implicate-specific.

The five implicates are not independent families.

Federal Reserve public documentation states that the 2022 public file has five
imputations per underlying family and that failure to account for multiple
imputation and complex survey design produces incorrect standard errors.

Summary-extract dollar values are already expressed in 2022 dollars.

---

# CPS physical format

Local canonical file is official fixed-width ASCII, not CSV.

Official household record fields:

    H_SEQ
        position 29
        length 5

    HSUP_WGT
        position 34
        length 8
        two implied decimals

    H_TENURE
        position 89
        length 1

        1 = owned / being bought
        2 = rented
        3 = no cash rent

    HTOTVAL
        position 106
        length 8

No economic values are read at E4A1.

---

# CPS person anchor

Official person fields:

    A_AGE
        position 79
        length 2

    A_EXPRRP
        position 82
        length 2

Reference-person codes:

    1 = reference person with relatives
    2 = reference person without relatives

Therefore the frozen CPS reference-person anchor is supported.

---

# Critical I semantic audit

E4A froze:

    WEWKRS
        direction = HIGHER_BETTER

    WEUEMP
        direction = HIGHER_WORSE

Official 2022 ASEC data dictionary must decide whether those variables are
cardinal counts or categorical recodes.

Official schema:

    WEUEMP
        position 333
        length 1
        categorical recode 0..9

        1 = none
        2 = 1-4 weeks
        3 = 5-10
        4 = 11-14
        5 = 15-26
        6 = 27-39
        7 = 40+
        8 = full-year worker
        9 = nonworker

    WEWKRS
        position 334
        length 1
        categorical recode 0..5

        1 = full-year full-time
        2 = full-year part-time
        3 = part-year full-time
        4 = part-year part-time
        5 = nonworker

Therefore neither field is a cardinal number of weeks.

In particular:

    numeric WEWKRS higher = better

is invalid.

And:

    numeric WEUEMP higher = worse

is not globally monotonic because codes 8 and 9 are structural categories.

If those facts are confirmed:

    E4A_I_PRIMARY_CARDINAL_SEMANTICS = FAIL

must be preserved.

---

# Candidate raw I fields for repair

Official CPS provides:

    WKSWORK
        position 338
        length 2
        0..52 actual weeks worked

    LKWEEKS
        position 305
        length 2
        0..51 actual weeks looking / on layoff
        universe: workers with WKSWORK 1..51

    NWLKWK
        position 309
        length 2
        0..52 actual weeks looking / on layoff
        universe: nonworkers who looked / were on layoff

    WORKYN
        position 340
        length 1
        1 yes / 2 no

    HRSWK
        position 296
        length 2
        usual weekly hours

These are repair candidates only.

E4A1 does NOT yet freeze the repaired I formula.

---

# Outcome restrictions

    CPS_DATA_ROWS_PARSED = 0
    CPS_I_VALUES_READ = 0
    SCF_DATA_ROWS_PARSED = 0
    SCF_K_VALUES_READ = 0
    SCF_D_VALUES_READ = 0

    K_EMPIRICALLY_TESTED = 0
    D_EMPIRICALLY_TESTED = 0
    I_EMPIRICALLY_TESTED = 0

    FIVE_DIMENSIONALITY_PROVEN = 0

No K/D/I economic open is authorized by this audit if the I semantic contract
fails.

Instead:

    E4A_R1_I_SEMANTIC_REPAIR_AUTHORIZED = 1

