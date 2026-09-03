# E3B0 — Economic Component Architecture

## Status

Frozen after:

    E3A5B R1 2022 pseudo-cohort support PASS

and before opening any household economic values.

This milestone defines roles and admissible constructions.

It does NOT estimate Real Inflation.

---

# 1. Two different mathematical objects

The project must distinguish:

## A. Economic state

Candidate multidimensional state:

    x_g(t) = [C, H, K, D, I]^T

where:

    C = consumption power
    H = housing position/access
    K = capital position/access
    D = debt position
    I = income/employment security

Higher values must eventually mean better economic position.

The five-dimensional structure remains a hypothesis.

The data may later support fewer, more, or differently defined dimensions.

---

## B. Real Inflation cost object

Define:

    R_g(t ; B_g)

as:

    nominal resources required at time t
    to preserve a frozen economic-capability bundle B_g
    for cohort g.

Candidate Real Inflation:

    pi_real_g(t)
        = Delta ln R_g(t ; B_g)

This is a COST-SIDE object.

---

# 2. Critical non-equivalence

The following identity is PROHIBITED:

    Real Inflation
        = weighted average of C,H,K,D,I

unless separately derived and empirically validated later.

In particular:

- higher debt does not automatically mean inflation;
- lower wealth does not automatically mean inflation;
- job insecurity does not automatically mean inflation;
- poorer capital-market participation does not automatically mean inflation.

These can reduce household economic power without being price inflation.

Therefore:

    STATE_CHANGE != COST_INFLATION

by construction.

---

# 3. Candidate economic purchasing power object

The project may later test:

    EP_g(t)
        = Resources_g(t) / R_g(t ; B_g)

which implies algebraically:

    Delta ln EP_g
        = Delta ln Resources_g
          - Delta ln R_g

and therefore, if Real Inflation is defined as above:

    Delta ln EP_g
        = Delta ln Resources_g
          - pi_real_g

This algebra is valid conditional on the definitions.

Its empirical usefulness is NOT yet established.

---

# 4. C — Consumption

Consumption is separated into:

    C_COST
    C_POWER

## C_COST

Cost of a frozen non-housing consumption bundle.

CEX expenditure data may determine cohort-specific base-period expenditure
weights.

Expenditures themselves must NOT be treated as price indices.

Candidate fixed-base construction:

    s_gjr
        = expenditure share for cohort g,
          category j,
          frozen base period r

    p_jt
        = category price index at time t

Then:

    CI_C(g,t|r)
        = SUM_j [
            s_gjr * (p_jt / p_jr)
          ]

with:

    SUM_j s_gjr = 1

Candidate cohort consumption inflation:

    pi_C(g,t)
        = Delta ln CI_C(g,t|r)

This is a Laspeyres-style fixed-base cohort cost index.

The exact category universe, UCC mapping, price-series mapping, treatment of
taxes, transfers and imputed expenditures must be frozen before values open.

---

## Housing exclusion from C_COST

Housing must NOT silently appear both inside C_COST and inside H.

Therefore the primary candidate C_COST excludes housing/shelter expenditure
categories that will be handled by the housing component.

A robustness version including official all-items consumer inflation may be
tested later.

---

## C_POWER

Candidate state-side consumption power:

    C_POWER_g(t)
        = Resources_g(t)
          / ConsumptionCost_g(t)

or equivalent log normalization.

This is distinct from C_COST.

---

# 5. H — Housing

Housing must remain split into two concepts.

## H_SERVICE

The resource cost of obtaining shelter services during a period.

Examples of possible future inputs:

RENTER:
    rent
    required housing operating costs

OWNER:
    recurring owner housing-service costs

The final owner-service formula is unresolved.

Mortgage principal must NOT automatically be treated as consumption because
principal repayment also changes the household balance sheet.

---

## H_ACCESS

Resources required to acquire access to owner-occupied housing.

Candidate future concepts include:

    down-payment burden
    years-to-deposit
    mortgage-payment burden
    purchase-price-to-resources ratio

The exact formula is unresolved.

H_ACCESS must remain distinct from H_SERVICE.

---

## No direct addition yet

H_SERVICE and H_ACCESS are not automatically commensurable.

Therefore:

    H = H_SERVICE + H_ACCESS

is NOT authorized.

They may only be combined after both are converted to a common, explicitly
defined resource-requirement unit.

---

# 6. K — Capital position/access

K is STATE-SIDE at this stage.

Candidate SCF evidence includes concepts such as:

    financial assets
    liquid assets
    stock ownership
    retirement assets
    emergency liquidity
    financial-market participation
    credit/access indicators

Candidate harmonized SCF variables include:

    ASSET
    FIN
    LIQ
    STOCKS
    RETQLIQ
    EQUITY
    HLIQ
    TURNDOWN
    FEARDENIAL

The final K formula is NOT frozen.

No K variable enters Real Inflation merely because its level changes.

---

# 7. D — Debt position

D is STATE-SIDE at this stage.

Candidate SCF concepts include:

    total debt
    debt-to-income
    payment-to-income
    mortgage payment burden
    delinquency
    bankruptcy / payment stress

Candidate harmonized variables include:

    DEBT
    DEBT2INC
    PIRTOTAL
    PIRMORT
    MRTHEL
    LATE60

Raw variables for these concepts may differ by SCF wave.

Because higher debt stress is economically worse, the final D state must be
sign-normalized so that:

    higher D = better debt position

The exact transformation is unresolved.

Changes in debt position are not automatically inflation.

---

# 8. I — Income and employment security

I is STATE-SIDE at this stage.

Canonical income/resource evidence comes from CPS ASEC rather than CEX.

Candidate CPS ASEC concepts include:

    total household/family resources
    weeks worked
    weeks unemployed / looking for work
    full-year / part-year work
    labor-force status
    employment status

Candidate variables include:

    WORKYN
    WKSWORK
    WEWKRS
    WEUEMP
    WEXP
    A_LFSR
    A_WKSTAT

Income-level variables will be mapped separately.

The final I formula is NOT frozen.

Income growth is not inflation.

---

# 9. Canonical source roles

CEX:

    primary role:
        consumption bundle / expenditure weights
        housing-service expenditure evidence

    NOT canonical:
        household income denominator

CPS ASEC:

    primary role:
        household/family resources
        labor-market and income-security evidence

SCF:

    primary role:
        capital
        debt
        balance sheet
        housing balance-sheet evidence

No direct record-level joins across surveys.

Only independently weighted cohort-level estimands may later be combined.

---

# 10. Temporal semantics

Flows and stocks must remain distinct.

CEX:

    expenditure FLOW

CPS ASEC:

    annual income/work-experience FLOW
    typically referring primarily to previous calendar year

SCF:

    balance-sheet STOCK at survey wave
    income FLOW referring primarily to previous calendar year

No variable may be treated as contemporaneous merely because its survey file
has the same nominal year.

Every future estimand must retain:

    survey_year
    reference_period_start
    reference_period_end
    measurement_type

where measurement_type is one of:

    FLOW
    STOCK
    DEMOGRAPHIC_STATE

---

# 11. Real Inflation admissible cost components

At E3B0 the potentially admissible cost-side families are:

    C_NONHOUSING_COST
    H_SERVICE_COST
    H_ACCESS_REQUIREMENT
    DURABLE_SERVICE_COST
    LOW_END_ACCESS_COST

The last two remain future extensions.

K, D and I are NOT directly admissible as inflation components merely because
their state changes.

Financing prices, interest costs or insurance prices may later enter a cost
component only under a separately frozen capability interpretation.

---

# 12. Common-unit gate

A final scalar:

    R_g(t ; B_g)

must NOT be produced until all components included in it have a coherent
common interpretation.

Primary preferred unit:

    nominal annual resource requirement

or a mathematically equivalent normalized cost index derived from such
requirements.

Adding incomparable quantities is prohibited.

For example, the project may not directly sum:

    CPI index
    house price
    debt ratio
    employment probability

into a scalar.

---

# 13. GE index status

The exploratory geometric aggregation:

    GE_g
        = PRODUCT_i q_i^(w_i)

or:

    ln GE_g
        = w^T x_g

is mathematically valid as a weighted geometric index.

However:

    GE_FINAL_INDEX_AUTHORIZED = 0

because:

- K, D and I formulas are unresolved;
- weights w_i are unresolved;
- dimensionality is unresolved;
- aggregation loses multidimensional information.

GE must not be called Real Inflation.

---

# 14. Required next gate

Before any economic values are opened, E3B1 must perform an exact schema and
semantic audit for the candidate variables needed to construct:

    C_COST
    H_SERVICE
    CPS resources / I
    SCF K
    SCF D

E3B1 remains schema/metadata only.

Only after that audit may an economic-value precommit be written.

---

# 15. Disclosure state

At E3B0:

    HOUSEHOLD_ECONOMIC_VALUES_OPENED = 0
    REAL_INFLATION_ESTIMATED = 0
    GE_ESTIMATED = 0
    COMPONENT_WEIGHTS_SELECTED = 0
    DIMENSIONALITY_SELECTED = 0

