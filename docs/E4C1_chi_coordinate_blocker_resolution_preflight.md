# E4C1 — C/H/I Coordinate Blocker Resolution Preflight

## Parent

    16823d0

E4C0 established complete evidence coverage but blocked C, H, and I from
becoming geometry-ready scalar coordinates.

E4C1 does not resolve those blockers by choosing a convenient formula.

Instead it freezes the candidate resolution families and the rules by which
future work is allowed to choose among them.

No raw survey values, new sources, coordinate values, transformed values, or
geometric results are opened here.

## 1. C — do not equate low spending with high economic power

The existing measure:

    C_COST

is retained as validated observed expenditure-flow evidence.

It is not authorized as a state coordinate by applying:

    C_state = -C_COST

because low spending can arise from very different mechanisms:

    lower prices;
    lower quantities;
    substitution;
    deprivation;
    preferences;
    household composition;
    life-cycle behavior.

Therefore a C state requires an explicit semantic bridge from expenditure to
economic command / affordability.

E4C1 freezes three candidate architecture families:

    REFERENCE_BUNDLE_AFFORDABILITY

    REAL_CONSUMPTION_COMMAND

    EXPENDITURE_BURDEN_WITH_PREDECLARED_RESOURCE_DENOMINATOR

No family is selected here.

Any future C architecture must specify its reference bundle or denominator
before opening resulting coordinate values and must audit conceptual overlap
with K, D, and I.

## 2. H — tenure cannot be the missing H_ACCESS variable

H_SERVICE remains valid housing-service expenditure evidence.

But the missing object is:

    H_ACCESS

A particularly important anti-tautology rule is now frozen:

    TENURE_AS_H_ACCESS_MEASURE=PROHIBITED

OWNER/RENTER already defines the cohort split.

Using tenure itself as the H coordinate would mechanically encode the group
label we are comparing and would not provide independent housing-access
information.

Candidate H_ACCESS families are:

    HOUSING_COST_BURDEN

    SPACE_OR_CROWDING_ACCESS

    ADEQUACY_SECURITY_OR_STABILITY_ACCESS

The actual source and estimand remain unresolved.

A future H workstream must prefer same-calendar-year evidence and must prove
that the selected measure is not merely a disguised tenure indicator.

## 3. I — two estimands do not force one scalar

The frozen primary I estimands are:

    I_FYFT_SHARE
    I_SEARCH_BURDEN_SHARE

Their individual state orientation is already frozen.

What is not frozen is the representation.

E4C1 explicitly prohibits silently defining:

    I = 0.5 * FYFT_state + 0.5 * SEARCH_state

Equal weighting could eventually be justified, but it cannot be assumed just
because two variables exist.

Three representation families remain admissible for separate study:

    KEEP_AS_TWO_SUBCOORDINATES

    PREDECLARED_THEORY_WEIGHTED_SCALAR

    LATENT_REPRESENTATION_WITH_INDEPENDENT_REFERENCE_FIT

If I remains two subcoordinates, the total coordinate count need not be five.

If a latent representation is considered, it cannot be fit and selected on
the same eight geometry cells.

## 4. The five-label hypothesis remains a hypothesis

C/H/K/D/I are conceptual labels.

They do not imply:

    exactly five scalar coordinates

H may contain service and access substructure.

I may remain multi-estimand.

Therefore E4C1 keeps:

    FIVE_COORDINATES_FROZEN=0
    FIVE_DIMENSIONALITY_PROVEN=0

## 5. Selection cannot depend on observed success

For C, H, and I, representation choices are forbidden from depending on:

    owner-renter direction;
    effect magnitude;
    significance;
    CI exclusion;
    visual separation;
    PCA loadings;
    geometric rank;
    dimensionality estimate;
    agreement with a preferred economic narrative.

The architecture must be chosen for semantic and measurement reasons before
geometry values are opened.

## 6. Three independent next workstreams

A PASS authorizes three independent preflights:

### E4C2 — C Coordinate Architecture

Goal:

    determine what economic state C should represent and what reference /
    denominator lineage would be required.

No C coordinate value is authorized merely by E4C2 preflight.

### E4C3 — H Access Source + Estimand Recon

Goal:

    find an official, same-year, non-tautological housing-access measure
    compatible with the frozen pseudo-cohort bridge.

No H_ACCESS value is authorized until its source and estimator are frozen.

### E4C4 — I Representation Architecture

Goal:

    decide whether I remains two subcoordinates or can be reduced by a
    predeclared, independently justified representation.

No I scalar is authorized by E4C1 itself.

## 7. K and D remain parked

K and D already have frozen state semantics.

Their dimensionless metric transformations remain unresolved, but those
choices are intentionally deferred until C/H/I semantic blockers have an
architecture.

This prevents us from optimizing K/D scaling around an incomplete coordinate
system.

## 8. Geometry remains prohibited

Even after E4C1:

    FIVE_COMPONENT_STATE_VECTOR_AUTHORIZED=0
    FIVE_COMPONENT_NORMALIZATION_AUTHORIZED=0
    DIMENSIONALITY_TEST_AUTHORIZED=0
    REAL_INFLATION_ESTIMATION_AUTHORIZED=0
    FINAL_SCALAR_AUTHORIZED=0
