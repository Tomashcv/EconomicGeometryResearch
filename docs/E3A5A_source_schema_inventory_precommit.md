# E3A5A — Source Acquisition and Schema Inventory

## Purpose

Acquire the official 2022 CPS ASEC and SCF source archives and determine
their exact physical file structure before writing the E3A5 support-count
parser.

No support counts are authorized in E3A5A.

No data rows may be parsed.

No economic values may be inspected.

---

## Sources

CPS ASEC 2022:

    asec2022_pubuse.zip

SCF 2022 full public file:

    scf2022s.zip

SCF 2022 summary extract:

    scfp2022s.zip

---

## Authorized inspection

CPS:

- ZIP validity;
- archive SHA256;
- archive member names;
- archive member byte sizes;
- file extensions;
- names of documentation/layout files.

SCF:

- ZIP validity;
- archive SHA256;
- archive member names;
- Stata metadata / column names only.

No Stata observation rows may be loaded.

---

## Required SCF full schema

The full public file must expose:

    Y1
    X14
    X508
    X601
    X701
    X7133
    X42001

These are the fields frozen in E3A4.

---

## Required SCF summary schema

The summary extract must expose:

    Y1
    YY1

No other summary variable is required for E3A5 support counting.

---

## CPS parser status

The E3A5 CPS parser is intentionally NOT frozen before this inventory.

E3A5A must first determine the actual member/file format distributed in the
official 2022 public-use archive.

After E3A5A is frozen, a separate parser precommit may use only the fields
already frozen in E3A4:

Household:

    H_SEQ
    HSUP_WGT
    H_HHTYPE
    H_TENURE

Person:

    PH_SEQ
    A_AGE
    A_EXPRRP

---

## Disclosure state

    DATA_ROWS_PARSED = 0
    PSEUDOCOHORT_COUNTS_OPENED = 0
    SUPPORT_COUNTS_CALCULATED = 0
    ECONOMIC_VALUES_OPENED = 0
    REAL_INFLATION_ESTIMATION_AUTHORIZED = 0

