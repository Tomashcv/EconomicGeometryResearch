# E4C2 — C Coordinate Architecture Preflight

## Parent

    54c264e

E4C1 authorized an independent C architecture workstream.

E4C2 does not select a C formula.

It freezes what the C state is supposed to mean, how the three candidate
architecture families must be evaluated, and what evidence must be gathered
before a selection can be justified.

No raw survey data, new reference data, coordinate values, transformed
values, or geometry are opened.

## 1. Existing C evidence remains evidence, not a state coordinate

The validated measure is:

    C_COST

Its frozen role remains:

    OBSERVED_ANNUAL_CONSUMPTION_EXPENDITURE_FLOW_EVIDENCE

It is not authorized to define:

    C_state = -C_COST

or any monotone rescaling of that formula.

Low expenditure can mean lower prices, lower quantities, substitution,
deprivation, preferences, or household composition.

## 2. Semantic target for C

E4C2 freezes the intended semantic object as:

    CONSUMPTION_ECONOMIC_COMMAND

Meaning:

    a monotone state representation of the real consumption goods/services
    command available or realized by a pseudo-cohort, distinct from nominal
    spending alone.

Required orientation:

    higher C state = better

This is semantic only.

No numerical coordinate is created.

## 3. Candidate C_A — Reference Bundle Affordability

Family:

    REFERENCE_BUNDLE_AFFORDABILITY

Strength:

    most directly connects C to the cost or affordability of a specified
    consumption bundle.

Unresolved issue:

    in one calendar year, a single common national bundle-price index can be
    identical across age/tenure cells and therefore provide no cross-sectional
    pseudo-cohort variation.

Cross-sectional identification would require a predeclared and defensible
cohort reference structure or a valid common resource numeraire.

That choice cannot be made from the observed owner-renter results.

Status:

    VIABLE_RECON_PENDING

## 4. Candidate C_B — Real Consumption Command

Family:

    REAL_CONSUMPTION_COMMAND

Strength:

    naturally interpretable as higher-is-better and capable, in principle,
    of distinguishing pseudo-cohort consumption levels in the same year.

Unresolved issue:

    requires a defensible price/quantity or deflation architecture.

It must also state explicitly what variation in composition, quality,
preferences, and household size means for the coordinate.

Status:

    VIABLE_RECON_PENDING

## 5. Candidate C_C — Expenditure Burden

Family:

    EXPENDITURE_BURDEN_WITH_PREDECLARED_RESOURCE_DENOMINATOR

Strength:

    yields a clear affordability burden concept.

Major risk:

    the denominator may duplicate other conceptual dimensions.

For example:

    income/employment resources can overlap I;
    financial resources can overlap K;
    debt-adjusted resources can overlap D.

Therefore C_C remains conditional on a formal overlap audit.

Status:

    CONDITIONAL_RECON_PENDING_OVERLAP_AUDIT

## 6. Evaluation criteria frozen before source values

Every candidate must be assessed against the same criteria:

    monotone economic-state interpretation;

    same-year cross-sectional identifiability;

    longitudinal extensibility;

    unit invariance;

    non-circularity with the eight geometry cells;

    distinctness from K/D/I;

    official/public source feasibility;

    reference object frozen before resulting values.

No criterion is outcome based.

## 7. No winner in E4C2

E4C2 explicitly freezes:

    C_ARCHITECTURE_SELECTED=0

A family cannot win because it:

    produces larger owner-renter separation;
    has smaller SEs;
    excludes zero;
    agrees with K or I;
    creates prettier geometry;
    gives five dimensions;
    produces a preferred Real Inflation story.

## 8. Next milestone

A PASS authorizes:

    E4C2A_C_REFERENCE_PRICE_QUANTITY_SOURCE_RECON_PREFLIGHT

That recon must identify what official/public price, quantity, reference
bundle, equivalence-scale, or resource-denominator sources could actually
support C_A, C_B, or C_C.

Source values must remain unopened until the recon contract is frozen.

## 9. Geometry remains prohibited

    C_COORDINATE_SELECTED=0
    C_COORDINATE_VALUES_AUTHORIZED=0
    FIVE_COMPONENT_STATE_VECTOR_AUTHORIZED=0
    FIVE_COMPONENT_NORMALIZATION_AUTHORIZED=0
    DIMENSIONALITY_TEST_AUTHORIZED=0
    REAL_INFLATION_ESTIMATION_AUTHORIZED=0
    FINAL_SCALAR_AUTHORIZED=0
