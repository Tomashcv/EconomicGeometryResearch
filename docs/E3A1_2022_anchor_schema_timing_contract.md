# E3A1 — 2022 Anchor Schema and Timing Reconnaissance

## Objective

Verify the schema and temporal semantics required to construct harmonized
pseudo-cohort estimands from CEX, CPS ASEC and SCF.

No economic values are opened or estimated.

No pseudo-cohort sample counts are opened.

No Real Inflation estimate is authorized.

---

# Fundamental timing rule

Survey/release year is NOT automatically the economic reference year.

Every future estimand must carry at least:

    survey_year
    reference_period_start
    reference_period_end
    measurement_type

Possible measurement types include:

    FLOW
    STOCK
    DEMOGRAPHIC_STATE

---

# CEX

Official source:

    BLS Consumer Expenditure Survey PUMD

Beginning with the 2020 release, the Interview package labelled year Y contains:

    Q2(Y)
    Q3(Y)
    Q4(Y)
    Q1(Y+1)

Therefore a calendar-year consumption estimate for year Y must NOT simply
use the package labelled Y.

For calendar year 2022:

    2022Q1 <- 2021 release
    2022Q2 <- 2022 release
    2022Q3 <- 2022 release
    2022Q4 <- 2022 release

No expenditure value is opened in E3A1.

Important Interview files:

    FMLI
    MTBI
    MEMI

Expected candidate variables include:

    NEWID
    AGE_REF
    FAM_SIZE
    PERSLT18
    CUTENURE
    FINLWT21

Exact 2022 microdata-header verification remains pending until the first
microdata package is acquired.

---

# CPS ASEC

Survey:

    CPS ASEC 2022

Demographic state:

    approximately survey/interview period in 2022

Income reference period:

    calendar year 2021

Therefore:

    CPS_ASEC_SURVEY_YEAR=2022
    CPS_ASEC_INCOME_REFERENCE_YEAR=2021

Candidate variables include:

Household:
    H_TENURE
    H_NUMPER
    HSUP_WGT

Person:
    A_AGE
    A_MARITL
    A_FAMNUM
    A_WKSTAT
    MARSUPWT

Income:
    HTOTVAL
    HEARNVAL
    family/person income components as separately audited later

No CPS dollar value is opened in E3A1.

---

# SCF

Survey wave:

    SCF 2022

Balance-sheet variables are interpreted as survey-wave stock measurements
subject to their exact codebook definitions.

The harmonized INCOME variable refers primarily to the previous calendar year:

    SCF_SURVEY_YEAR=2022
    SCF_INCOME_REFERENCE_YEAR=2021

Candidate harmonized variables include:

    AGE
    AGECL
    KIDS
    MARRIED
    FAMSTRUCT
    HOUSECL
    INCOME
    FIN
    LIQ
    STOCKS
    RETQLIQ
    HOUSES
    ASSET
    DEBT
    MRTHEL
    HOMEEQ
    NETWORTH
    DEBT2INC
    PIRTOTAL
    PIRMORT
    WGT

The SCF summary extract dollar variables must NOT be used for nominal
Real Inflation construction without explicit adjustment because the official
summary extract is distributed in inflation-adjusted 2022 dollars.

---

# Cross-survey temporal alignment

The eventual object:

    X_g(t)

must NOT be created by matching survey labels alone.

Every component must first be assigned to an economic reference period.

Example:

    CPS ASEC 2022 income -> 2021 flow
    SCF 2022 INCOME     -> previous-year flow
    SCF 2022 ASSET      -> 2022 stock
    CEX expenditures    -> actual expenditure reference quarter/month

Flows and stocks must remain explicitly distinguished.

---

# E3A1 authorization

Allowed:

    documentation acquisition
    schema inspection
    variable-name verification
    reference-period verification
    hashes

Forbidden:

    economic means
    medians
    weighted estimates
    cohort counts
    income distributions
    wealth distributions
    expenditure distributions
    Real Inflation values

Next gate after E3A1:

    precommit minimum sample-support criteria

before opening pseudo-cohort cell counts.
