# E3B2 — Component Semantic Mapping

## Status

Frozen after E3B1 exact-schema PASS and before any household economic values
are opened.

E3B2 freezes semantic roles and source requirements.

It does NOT:

- calculate economic values;
- select final component weights;
- select final dimensionality;
- estimate Real Inflation;
- construct the final GE index.

---

# 1. Core separation

Economic state:

    x_g(t) = [C,H,K,D,I]^T

remains a hypothesis.

Real Inflation remains a separate cost-side candidate:

    pi_real_g(t)
        = Delta ln R_g(t ; B_g)

Therefore:

    STATE_CHANGE != COST_INFLATION

and:

    GE != REAL_INFLATION

unless a future derivation and empirical test explicitly establish otherwise.

---

# 2. Consumption cost — C_COST

## 2.1 Integrated CEX required

The canonical cohort consumption basket must NOT be estimated from the
Interview Survey MTBI alone.

BLS Consumer Expenditure published expenditure concepts integrate information
from:

    Interview Survey
    Diary Survey

depending on the UCC.

Therefore:

    INTERVIEW_ONLY_C_COST_AUTHORIZED = 0
    INTEGRATED_CEX_REQUIRED = 1

The official annual Integrated Hierarchical Grouping must determine:

- each UCC description;
- hierarchy;
- source survey;
- expenditure category.

No economic values may be opened until the applicable grouping file and Diary
source requirements have been audited.

---

## 2.2 Candidate non-housing consumption universe

The initial C_COST candidate is conventional non-housing household
consumption expenditure.

At broad-category level, the primary candidate includes:

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

The following broad categories are NOT part of primary C_COST:

    Housing
    Cash contributions
    Personal insurance and pensions

Reason:

Housing is treated separately in H.

Cash contributions are transfers rather than direct consumption of the CU.

Life insurance/pension contributions are not treated as current consumption
cost in the primary candidate.

This broad-category rule is frozen before values.

Exact UCC membership remains unopened and must be generated from official
BLS hierarchical mappings.

---

## 2.3 Durable-goods warning

Vehicle purchases and other durable acquisitions may behave differently from
current service consumption.

The primary simple C_COST candidate may initially follow conventional CE
expenditure treatment.

A later DURABLE_SERVICE_COST robustness extension may replace acquisition
outlay with service-capacity/TCO treatment.

The durability extension must not be retrofitted after seeing Real Inflation
results.

---

# 3. Housing — H

Housing remains split:

    H_SERVICE
    H_ACCESS

They are not automatically additive.

---

## 3.1 H_SERVICE

H_SERVICE is the recurring resource cost of obtaining shelter services.

RENTER candidate family includes:

    rent
    utilities
    recurring renter shelter costs

OWNER candidate family may include:

    mortgage interest
    property taxes
    insurance
    maintenance / repairs
    utilities
    other recurring owner costs

Mortgage principal is NOT primary consumption/service cost.

Principal repayment changes household balance-sheet position and must not be
silently counted as both consumption cost and asset accumulation.

The exact UCC list remains to be frozen from official BLS hierarchy.

---

## 3.2 H_ACCESS

H_ACCESS measures ability/resources required to acquire owner-occupied
housing.

Candidate future inputs include:

    house-price level/index
    mortgage interest rate
    required down-payment
    cohort Resources
    mortgage-payment requirement

H_ACCESS must remain separate from H_SERVICE.

No final H_ACCESS formula is frozen in E3B2.

No final Real Inflation scalar is authorized until H_ACCESS is either:

A. converted to the same resource-requirement interpretation as the other
   components;

or

B. explicitly excluded from a separately named restricted scalar and reported
   independently.

The project may not silently drop H_ACCESS from the broader research question.

---

# 4. Resources — CPS ASEC

Primary 2022 candidate:

    HTOTVAL

Official concept:

    household income amount

This is a candidate nominal household-resource FLOW.

It is NOT automatically equivalent to:

    disposable income
    after-tax income
    permanent income

Therefore:

    RESOURCES_PRIMARY_CANDIDATE = HTOTVAL
    RESOURCES_FINAL_DEFINITION_FROZEN = 0

The project must not call HTOTVAL "disposable income" unless taxes/transfers
are explicitly incorporated by a later contract.

Timing:

For ASEC survey year Y, the income flow primarily refers to calendar year
Y-1.

Thus:

    CPS_2022_HTOTVAL_REFERENCE_YEAR = 2021

for economic-flow alignment.

---

# 5. Income/employment security — I

I is STATE-SIDE.

Two timing families exist and must remain distinct.

## Previous-calendar-year work experience

Candidate variables:

    WORKYN
    WEWKRS
    WEUEMP
    WEXP
    WTEMP

These can be aligned conceptually with ASEC previous-year income.

Primary long-run I construction must come from this previous-year family
unless separately justified.

## Current-status diagnostics

Candidate variables:

    A_LFSR
    A_WKSTAT

These describe status around the survey date.

They must NOT be combined mechanically with previous-calendar-year HTOTVAL
into one contemporaneous scalar.

Therefore:

    I_PREVIOUS_YEAR_PRIMARY = 1
    I_CURRENT_STATUS_PRIMARY = 0

Current-status variables may later be used as separate diagnostics or under a
separately aligned timing contract.

E3B2 does not yet select a scalar I formula.

---

# 6. Capital position/access — K

K is STATE-SIDE.

Principal-residence housing must not dominate the capital dimension merely
because home values are large.

Therefore:

    ASSET_PRIMARY_K_AUTHORIZED = 0

because ASSET includes financial and nonfinancial assets, including housing.

Primary long-run K candidate family:

    FIN
    LIQ
    EQUITY
    RETQLIQ

Interpretations:

    FIN
        financial assets

    LIQ
        transaction/liquid assets

    EQUITY
        stock-equity exposure

    RETQLIQ
        quasi-liquid retirement assets

These are candidate subdimensions.

E3B2 does NOT collapse them into one K scalar.

---

## 6.1 Liquidity participation

HLIQ may be used as a participation/access diagnostic.

It is not itself equivalent to amount of liquid resources.

---

## 6.2 Credit-access indicators

    TURNDOWN
    FEARDENIAL

are potentially informative capital/credit-access indicators.

However Federal Reserve construction changed the relevant application/lookback
horizon in 2016.

Therefore:

    TURNDOWN_LONGRUN_PRIMARY = 0
    FEARDENIAL_LONGRUN_PRIMARY = 0

They may be used only in:

    MODERN_2016_PLUS

analysis unless a separate historical harmonization contract establishes
comparability.

No post-result reinterpretation is allowed.

---

# 7. Debt position — D

D is STATE-SIDE and must be sign-normalized so:

    higher D = better debt position

Primary burden candidate:

    PIRTOTAL

Federal Reserve construction:

    monthly total debt payments / monthly income

Secondary leverage candidate:

    DEBT2INC

Federal Reserve construction:

    total debt / income

Stress diagnostic:

    LATE60

meaning household had a payment more than 60 days past due in the previous
year.

Therefore candidate hierarchy:

    D_PRIMARY_BURDEN = PIRTOTAL
    D_SECONDARY_LEVERAGE = DEBT2INC
    D_STRESS_DIAGNOSTIC = LATE60

---

## 7.1 Candidate sign-normalization

A future primary log-state candidate is predeclared:

    q_D(t) = 1 / (1 + PIRTOTAL(t))

so:

    higher burden -> lower q_D

and relative debt-position state may be:

    x_D(t)
        = ln(q_D(t) / q_D(r))

        = ln[
            (1 + PIRTOTAL(r))
            /
            (1 + PIRTOTAL(t))
          ]

This formula is only a CANDIDATE.

No PIRTOTAL values have yet been opened under this component analysis.

DEBT2INC may be subjected to the analogous robustness transform.

---

# 8. Housing balance-sheet variables

SCF:

    HOUSES
    HOMEEQ
    NETWORTH

are STATE/BALANCE-SHEET evidence.

Federal Reserve defines:

    HOMEEQ = HOUSES - MRTHEL

These variables are not direct housing-price inflation measures.

They must not be inserted directly into Real Inflation.

They may later explain how the same house-price movement affects owners and
renters differently.

---

# 9. Cross-survey combination

No direct record join is authorized.

For survey S:

    theta_hat_S(g,t)

is estimated independently.

Only cohort-level estimands may subsequently be combined.

Thus:

    CEX_i JOIN CPS_i JOIN SCF_i

remains prohibited.

---

# 10. Timing alignment

Primary alignment target:

CEX:
    expenditure FLOW for the expenditure reference period

CPS ASEC:
    Resources / work-experience FLOW primarily referring to previous year

SCF:
    balance-sheet STOCK at survey date
    plus harmonized state variables

A STOCK and FLOW may coexist in x_g(t), but they must retain explicit
measurement semantics.

They may not be represented as if observed at the same instant without an
alignment rule.

---

# 11. What E3B2 authorizes next

Before the first component economic values can open, E3B3 must:

1. acquire/audit the official CEX integrated hierarchical grouping for the
   anchor year;

2. acquire/audit the 2022 Diary PUMD required for integrated expenditure
   construction;

3. generate the exact UCC classification mechanically from official hierarchy;

4. verify exact CPS code semantics for the I candidate family;

5. freeze the first numerical estimands to be opened for C/H/K/D/I;

6. freeze missing/zero/negative-value treatment before inspecting those
   distributions.

Until E3B3 passes:

    HOUSEHOLD_ECONOMIC_VALUES_AUTHORIZED = 0

---

# 12. Frozen status

    STATE_VECTOR_5D = HYPOTHESIS

    REAL_INFLATION_ESTIMATED = 0

    HOUSEHOLD_ECONOMIC_VALUES_OPENED = 0

    COMPONENT_WEIGHTS_SELECTED = 0

    DIMENSIONALITY_SELECTED = 0

    GE_FINAL_INDEX_AUTHORIZED = 0

    INTERVIEW_ONLY_C_COST_AUTHORIZED = 0

    INTEGRATED_CEX_REQUIRED = 1

