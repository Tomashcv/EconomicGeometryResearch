# E3B4B R2 — Complete UCC Source-Family Inventory

## Parent

    bcbea24

## Trigger

E3B4B R1 proved:

    MTBI_ONLY_UCCS = 374
    ITBI_ONLY_UCCS = 8
    BOTH_UCCS = 0
    NEITHER_UCCS = 16

and:

    PENSIONS_SOCIAL_SECURITY_UCCS = 5
    PENSIONS_LOCATIONS = ITBI_ONLY

    FACTOR4_UCCS = 3
    FACTOR4_LOCATIONS = ITBI_ONLY

Therefore the assumption:

    Interview source I -> MTBI

is false.

The original E3B4B benchmark remains FAIL.

---

# 1. Purpose

Before creating an estimator V2, determine the physical source-family coverage
of every frozen integrated UCC across all relevant 2022 PUMD files containing
a UCC field.

This milestone must resolve whether the previously:

    16 Interview NEITHER UCCs
    4 Diary UCCs absent from EXPD

occur in other PUMD file families.

---

# 2. Scope

Interview calendar-year source quarters:

    221
    222
    223
    224
    231

Diary calendar-year source quarters:

    221
    222
    223
    224

Scan every CSV member from those quarters.

For each member:

    inspect header
    determine whether UCC exists
    if UCC exists, read ONLY the UCC column

No expenditure/income amount field may be read.

---

# 3. Output classification

For every one of the frozen 645 UCCs record:

    survey source I/D
    component class
    primary component
    broad category
    factor
    physical file families in which the UCC occurs

Examples may include:

    MTBI
    ITBI
    ITII
    EXPD
    DTBD
    DTID
    detailed Interview file families

No assumption is made in advance about which families will appear.

---

# 4. Primary-map question

The main repair question is whether all:

    534 primary UCCs

have a physically identified source family.

If some primary UCC is absent from every UCC-bearing file in 2022, it must
remain unresolved until separately explained.

No zero-value assumption may be introduced merely because an observed record
is absent in 2022.

---

# 5. Header semantics

For each UCC-bearing file family preserve the header fields that may determine:

    value variable
    reference period
    allocation/imputation state
    record identity

This is header metadata only.

No values from these fields are opened.

---

# 6. Official sample-code forensic

The already downloaded official SAS/STATA UCC sample code may be inspected for
references to:

    MTBI / MTAB
    ITBI / ITAB
    EXPD / EXPN
    DTBD / DTAB
    ITII
    DTID

This is source-code evidence only.

---

# 7. No estimator mutation

Regardless of findings:

    E3B3C4 original estimator remains historically frozen
    E3B4A original cohort outputs remain historically frozen
    E3B4B original benchmark remains historically FAIL

and:

    ESTIMATOR_V2_FROZEN = 0
    ESTIMATOR_V2_EXECUTION_AUTHORIZED = 0

A new exact source-family contract is required before rerunning COST values.

---

# 8. Disclosure

    COST_VALUES_READ = 0
    NEW_ECONOMIC_VALUES_OPENED = 0
    REAL_INFLATION_ESTIMATED = 0

