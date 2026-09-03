# E3B3C1 — 2022 Component UCC Mapping

## Status

Executed after:

    E3B3A R2 calendar-year timing PASS
    E3B3B hierarchy reconstruction PASS

and before reading any CEX COST observation.

This milestone maps official 2022 integrated expenditure UCCs into economic
component roles.

---

# 1. Frozen input

Canonical hierarchy tree:

    data/metadata/E3B3B_ucc_hierarchy_tree.tsv

Expected SHA256:

    136dca44d16777650ac0c8901f3b23187fd9f64bb7bf3208b8c10e16d3960a4c

Frozen expenditure universe:

    FOOD + EXPEND

    645 occurrences
    645 unique UCCs

No duplicate expenditure UCC exists in the frozen 2022 hierarchy.

---

# 2. Classification principle

Classification must use official hierarchy ancestry.

Keyword-only leaf-title classification is prohibited.

Primary broad-category identity is taken from:

    FOOD:
        level_2_title = Food

    EXPEND:
        level_2_title = official CE broad expenditure category

---

# 3. Primary C_COST

The primary non-housing consumption component includes all UCCs under:

    Food
    Alcoholic beverages
    Apparel and services
    Transportation
    Healthcare
    Entertainment
    Personal care products and services
    Reading
    Education
    Tobacco products and smoking supplies
    Miscellaneous

This preserves the broad-category rule frozen in E3B2.

Therefore vehicle purchases remain in the primary candidate under the standard
CE expenditure convention.

A future durable-service robustness specification may replace acquisition
cost treatment.

Miscellaneous also remains included in the primary mapping because it was
explicitly frozen in E3B2.

Possible financing-sensitive subitems may later receive a separately
precommitted robustness test.

---

# 4. Housing split

The official broad Housing category is NOT treated as one homogeneous
economic concept.

## H_SERVICE_CORE

Primary shelter-service cost includes:

    Housing > Shelter

    Housing > Utilities, fuels, and public services

These are the primary H_SERVICE UCC branches.

Under the standard CE expenditure concept, mortgage principal is not part of
owned-housing expenditure.

---

## H_NONCORE_PENDING

The following are NOT silently inserted into H_SERVICE_CORE:

    Housing > Household operations
    Housing > Housekeeping supplies

They are retained explicitly as:

    H_NONCORE_PENDING

Their final role will require a later capability interpretation.

---

## DURABLE_SERVICE_PENDING

The branch:

    Housing > Household furnishings and equipment

is retained explicitly as:

    DURABLE_SERVICE_PENDING

because acquisition expenditure is not automatically identical to annual
service cost from a durable good.

---

# 5. Explicit primary exclusions

The following official CE broad categories do not enter primary C_COST:

    Cash contributions
    Personal insurance and pensions

Classification:

    Cash contributions
        -> EXCLUDED_TRANSFER

    Personal insurance and pensions
        -> EXCLUDED_INSURANCE_PENSION

This preserves E3B2.

---

# 6. H_ACCESS remains separate

H_ACCESS is not constructed from this CEX expenditure map.

It remains a separate acquisition/access capability involving future housing
market and financing inputs.

Therefore:

    H_ACCESS_UCC_MAP = NOT_APPLICABLE

---

# 7. Complete partition requirement

Every one of the 645 FOOD/EXPEND UCCs must receive exactly one class:

    C_COST_PRIMARY
    H_SERVICE_CORE
    H_NONCORE_PENDING
    DURABLE_SERVICE_PENDING
    EXCLUDED_TRANSFER
    EXCLUDED_INSURANCE_PENSION

No UCC may:

    remain unmapped
    appear in two classes

---

# 8. Survey source

Each UCC retains the official integrated hierarchy source:

    I = Interview
    D = Diary

The component mapping must not override source selection.

---

# 9. Factor preservation

Each UCC retains its official hierarchy factor:

    1
    4

E3B3C1 does NOT yet decide exactly where that factor enters the estimator.

That arithmetic is delegated to:

    E3B3C2 — BLS estimator / annualization preflight

because factor, QNUM, MO_SCOPE and Diary periodicity must be reconciled with
official BLS sample-code logic before COST values are opened.

---

# 10. Disclosure state

    COST_VALUES_READ = 0
    EXPENDITURE_VALUES_OPENED = 0
    HOUSEHOLD_ECONOMIC_VALUES_OPENED = 0
    REAL_INFLATION_ESTIMATED = 0

    INTEGRATION_ARITHMETIC_FROZEN = 0
    HOUSEHOLD_ECONOMIC_VALUES_AUTHORIZED = 0

