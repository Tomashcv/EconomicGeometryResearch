# E4A2A — Official Replicate-Weight Acquisition + Schema Audit

## Parent

    5cea6e1

## Purpose

Acquire only the official 2022 SCF and CPS ASEC replicate-weight assets and
freeze their cryptographic provenance and physical schemas.

No K, D or I economic values are opened.

No replicate-weight values are parsed into numerical arrays.

---

# Official SCF acquisition

Replicate-weight archive:

    https://www.federalreserve.gov/econres/files/scf2022rw1s.zip

2022 codebook:

    https://www.federalreserve.gov/econres/files/codebk2022.txt

Expected Stata replicate schema from the official 2022 codebook:

    Y1

    WT1B1
    ...
    WT1B999

    MM1
    ...
    MM999

Exactly:

    999 replicate-weight variables
    999 multiplicity variables

Effective bootstrap weight r is later:

    WGT_r = max(0, WT1B_r) * max(0, MM_r)

The replicate file is merged to the main SCF data using:

    Y1

Replicate weights exist for sampling-variance estimation on the first
implicate.

No replicate values are read at E4A2A.

---

# Official CPS acquisition

Replicate archive:

    https://www2.census.gov/programs-surveys/cps/datasets/2022/march/CPS_ASEC_ASCII_REPWGT_2022.ZIP

Official layout:

    https://www2.census.gov/programs-surveys/cps/datasets/2022/march/CPS_ASEC_ASCII_REPWGT_2022.SAS

Official usage instructions:

    https://www2.census.gov/programs-surveys/cps/datasets/2022/march/2022_ASEC_Replicate_Weight_Usage_Instructions.docx

Official person layout:

    https://www2.census.gov/programs-surveys/cps/datasets/2022/march/persfmt.txt

Official household layout:

    https://www2.census.gov/programs-surveys/cps/datasets/2022/march/hhldfmt.txt

---

# CPS expected replicate-file schema

Official SAS layout specifies:

    LRECL = 1456

    PWWGT0
        position 1
        width 9
        format F9.4

    PWWGT1 ... PWWGT160
        160 replicate weights
        each width 9
        format F9.4

    H_SEQ
        position 1450
        width 5

    PPPOS
        position 1455
        width 2

Therefore:

    full/base weight fields = 1
    replicate fields = 160
    total weight fields = 161

No weight values are parsed at E4A2A.

---

# CPS merge architecture

Official person layout:

    PH_SEQ
        position 36
        width 5

    PPPOS
        position 43
        width 2

    MARSUPWT
        position 71
        width 8

    A_EXPRRP
        position 82
        width 2

Official household layout:

    H_SEQ
        position 29
        width 5

    HSUP_WGT
        position 34
        width 8

    H_HHTYPE
        position 61
        width 1

    H_TENURE
        position 89
        width 1

Replicate-person merge key:

    replicate H_SEQ  <-> person PH_SEQ
    replicate PPPOS  <-> person PPPOS

Household-reference-person merge:

    household H_SEQ <-> reference-person PH_SEQ

Reference person remains:

    A_EXPRRP in {1,2}

---

# Important full-weight bridge gate

E4A2 froze the household point-estimator weight as:

    HSUP_WGT

The CPS replicate file contains:

    PWWGT0

and official replicate documentation identifies PWWGT0 as the full-sample
ASEC replicate-file weight corresponding to the person supplement weight:

    MARSUPWT

Therefore the following identity/equivalence must NOT be assumed silently:

    HSUP_WGT
      vs
    reference-person MARSUPWT / PWWGT0

E4A2A freezes:

    CPS_HOUSEHOLD_FULL_WEIGHT_BRIDGE = PENDING

A dedicated values-only weight audit must verify the bridge before CPS
replicate inference is authorized.

That audit may open weights and identifiers only.

It may not open I outcomes.

---

# E4A2A hard gates

SCF:

    official ZIP valid
    exactly one Stata member
    Y1 present
    exactly WT1B1-WT1B999
    exactly MM1-MM999

CPS:

    official ZIP valid
    expected ASCII DAT member present
    official SAS layout retrieved
    record length = 1456
    PWWGT0-PWWGT160 exact
    H_SEQ exact
    PPPOS exact

Documentation:

    official usage instruction DOCX valid
    person layout exact merge fields present
    household layout exact merge fields present

---

# Scientific boundary

Still prohibited:

    reading FIN
    reading LIQ/EQUITY/RETQLIQ
    reading PIRTOTAL/DEBT2INC
    reading WEWKRS/WEUEMP outcomes

    calculating K
    calculating D
    calculating I

    dimensionality analysis

    Real Inflation

If E4A2A passes:

    E4A2B_WEIGHT_BRIDGE_AUDIT_AUTHORIZED = 1

