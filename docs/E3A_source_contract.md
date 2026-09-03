# E3A — Household Microdata Source Contract

## Objective

Build a defensible data architecture for household/cohort-specific
Real Inflation and Economic Purchasing Power.

No scalar Real Inflation estimate is authorized in E3A.

---

## Fundamental statistical rule

CEX, CPS ASEC and SCF do NOT contain the same sampled households.

Individual records must never be directly joined across surveys.

The project will instead construct independently weighted pseudo-cohort
statistics using harmonized economic characteristics.

Forbidden:

    CEX_person_id == CPS_person_id
    CPS_household_id == SCF_family_id
    direct record linkage across surveys

Allowed:

    estimate_CEX(concept | cohort g, year t)
    estimate_CPS(concept | cohort g, year t)
    estimate_SCF(concept | cohort g, wave t)

and combine only the resulting cohort-level estimands after their
definitions have been separately validated.

---

## Canonical development window

Primary rich-window candidate:

    1989 through 2022

Reason:

- SCF harmonized modern series begins in 1989;
- CEX PUMD spans this interval;
- CPS March/ASEC information spans this interval;
- SCF 2022 is the latest currently documented public SCF wave.

SCF waves:

    1989
    1992
    1995
    1998
    2001
    2004
    2007
    2010
    2013
    2016
    2019
    2022

CEX and CPS are higher-frequency/annual sources.
SCF is triennial.

No interpolation of SCF wealth/debt values is authorized in E3A.

---

## Survey roles

### Consumer Expenditure Survey — CEX

Primary role:

    consumption structure C

Candidate concepts:

- expenditure shares;
- detailed expenditure categories;
- household/consumer-unit demographics;
- housing-service expenditures;
- tenure;
- family size;
- children.

Primary files:

    FMLI
    MTBI
    MEMI

CEX income is not the canonical project income spine.

Reason:

income collection/imputation methodology changes over time and CPS ASEC is
better suited to the project's canonical income and labor-market estimates.

---

### Current Population Survey ASEC — CPS ASEC

Primary roles:

    Y = household/family income
    I = income/employment security
    population-demographic anchor

Candidate concepts:

- age;
- family/household size;
- children;
- tenure;
- family income;
- earnings;
- employment/work experience;
- sampling weights.

CPS is not the canonical balance-sheet source for wealth.

---

### Survey of Consumer Finances — SCF

Primary roles:

    K = capital access / financial position
    D = debt position
    H_balance_sheet = owner housing balance sheet

Use the Federal Reserve harmonized summary-variable definitions where
possible.

Candidate harmonized variables include:

    AGE
    AGECL
    MARRIED
    KIDS
    FAMSTRUCT
    HOUSECL
    INCOME
    ASSET
    FIN
    LIQ
    STOCKS
    RETQLIQ
    HOUSES
    DEBT
    MRTHEL
    HOMEEQ
    NETWORTH
    PIRTOTAL
    PIRMORT
    DEBT2INC
    WGT

SCF multiple imputation must be respected.

Five implicates must NOT be interpreted as five independent families.

---

## Housing decomposition

Housing must be separated into:

    H_service

and

    H_access

H_service:

    cost/value of shelter services consumed

H_access:

    resources required to acquire owner-occupied housing

House prices must not simply be added to consumption inflation.

Owner housing wealth must not simultaneously be counted as both a
consumption cost and a positive asset without an explicit accounting rule.

---

## Real Inflation target

Final objective remains:

    pi_real_g(t) = Delta ln R_g(t)

where R_g(t) is the nominal resource requirement for pseudo-cohort g to
preserve a frozen set of economic capabilities.

Economic purchasing-power change is separate:

    Delta ln EP_g(t)
        = Delta ln Resources_g(t)
        - pi_real_g(t)

The construction of R_g(t) is NOT frozen in E3A.

---

## No universal household assumption

Real Inflation may differ across economically different households.

At minimum the architecture must permit contrasts such as:

    young renter / housing entrant

versus

    established homeowner

The national aggregate, if ever produced, will be a secondary aggregation
over household-specific estimates.

---

## Known structural issues requiring explicit audit

CEX:
- PUMD unavailable for 1982 and 1983;
- survey/data-collection protocols change through time;
- income imputation changed materially beginning in 2004;
- weighting/protocol changes must not be silently ignored.

CPS ASEC:
- variable definitions and file layouts change through time;
- ASEC redesign periods must be explicitly audited;
- household, family and person weights are not interchangeable.

SCF:
- triennial rather than annual;
- five multiple-imputation implicates;
- complex survey design and replicate weights;
- public harmonized dollar variables may be inflation-adjusted;
- nominal versus real treatment must be explicitly contracted before
  computing Real Inflation.

---

## Next authorized step

E3A1:

    schema-only one-wave reconnaissance

using modern anchor data/documentation before any 1989-2022 bulk acquisition.

No final cohort definition is authorized until sample support is measured.
