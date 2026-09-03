# E3B3B — 2022 Integrated CEX Hierarchy Tree Reconstruction

## Status

Executed only after:

    E3B3A R1 integrated CEX source preflight PASS

Canonical parent:

    c5dc95e

This milestone is METADATA ONLY.

No CEX expenditure values may be opened.

---

# 1. Purpose

Before classifying UCCs into:

    C_COST
    H_SERVICE

the project must reconstruct the official 2022 BLS integrated hierarchy.

Classification by ad-hoc keyword matching is prohibited.

The hierarchy itself must determine the ancestry and broad expenditure
categories associated with each UCC.

---

# 2. Frozen source

Canonical archive:

    data/raw/cex/stubs/stubs.zip

Canonical member:

    CE-HG-Integ-2022.txt

Frozen SHA256:

    58098e493f0e99239b1f306555e3c1ff2cda57e5cb0287517b22a1b789166d33

Year-specific 2022 fixed-width layout already proven in E3B3A R1:

    type    position 1
    level   position 4
    title   position 7
    UCC     position 70
    source  position 80
    factor  position 83
    section position 86

No further layout mutation is authorized here.

---

# 3. BLS hierarchy semantics

Levels:

    1 through 9

where lower numeric level means broader aggregation.

Source values may include:

    I = Interview
    D = Diary
    G/T = hierarchy/title records
    S = statistical records

For component construction, economic expenditure candidates must originate
only from the expenditure sections:

    FOOD
    EXPEND

Other sections:

    CUCHARS
    INCOME
    ASSETS
    ADDENDA

are not direct consumption-expenditure UCC candidates.

---

# 4. Type-2 continuation lines

BLS permits:

    type 1 = first line of name
    type 2 = second line of name

E3B3B must join type-2 title text to the preceding logical record.

No economic values are involved.

---

# 5. UCC occurrences versus unique UCCs

A UCC may appear more than once in the hierarchy.

Therefore:

    HIERARCHY_ROW != UNIQUE_UCC

E3B3B must report separately:

    hierarchy occurrences
    unique UCCs
    duplicate UCC groups

Duplicates must NOT be silently removed.

---

# 6. Conflict gates

Within FOOD + EXPEND, repeated occurrences of one UCC must be audited for:

    conflicting source
    conflicting factor

If one expenditure UCC has inconsistent source or factor semantics,
component mapping must remain blocked until resolved.

Different hierarchy paths alone are not automatically an error.

---

# 7. Tree reconstruction

For every I/D UCC occurrence, reconstruct:

    level_1_title
    ...
    level_9_title
    leaf title
    full hierarchy path
    source
    factor
    section

using only preceding official hierarchy records.

---

# 8. No component classification yet

E3B3B does NOT decide:

    which FOOD/EXPEND UCCs enter C_COST;
    which EXPEND UCCs enter H_SERVICE;
    treatment of vehicles/durables;
    mortgage-principal treatment by UCC;
    component weights.

Therefore:

    C_COST_UCC_MAP_FROZEN = 0
    H_SERVICE_UCC_MAP_FROZEN = 0

---

# 9. Next authorization

If hierarchy reconstruction passes, E3B3C may freeze:

    exact C_COST UCC rules
    exact H_SERVICE UCC rules
    exclusions
    treatment of duplicate hierarchy occurrences
    integration arithmetic
    first economic estimands

before any COST observations are opened.

---

# 10. Disclosure

    MICRODATA_DATA_ROWS_PARSED = 0
    COST_VALUES_READ = 0
    EXPENDITURE_VALUES_OPENED = 0
    HOUSEHOLD_ECONOMIC_VALUES_OPENED = 0
    REAL_INFLATION_ESTIMATED = 0

