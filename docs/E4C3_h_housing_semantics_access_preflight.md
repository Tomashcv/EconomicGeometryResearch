# E4C3 — H housing semantics + H_ACCESS preflight

## Scope

E4C3 is a semantic preflight. It opens no new housing values and downloads no new sources.

The purpose is to prevent `H_SERVICE` or tenure status from being promoted mechanically into a housing-state coordinate.

## Current evidence status

`H_SERVICE` is retained as valid descriptive housing-service-flow evidence.

It is not a complete housing-state coordinate. Higher housing-service expenditure may reflect more housing quantity, higher quality, higher local prices, or greater burden. Therefore neither `H_SERVICE` nor `-H_SERVICE` receives a higher-is-better state interpretation here.

`H_ACCESS` remains required before a full housing state can be considered.

## Tautology prohibition

OWNER versus RENTER is part of the frozen cohort definition.

Therefore tenure status itself cannot be used as `H_ACCESS`. Doing so would mechanically encode the group label inside the outcome.

Variables derived solely from the fact of being owner or renter are likewise prohibited as access measures.

## Housing semantic target

The working conceptual target is:

`HOUSING_ECONOMIC_SECURITY_AND_ACCESS`

This may eventually require more than one numerical subcoordinate. The conceptual label `H` does not force a single scalar.

## Candidate H_ACCESS families

### 1. Affordability burden

Housing costs relative to a predeclared resource denominator.

Potentially strong economic meaning, but denominator choice must avoid hidden duplication with C, K, D, or I.

### 2. Space / crowding adequacy

Direct measures such as persons per room, bedrooms, or related occupancy adequacy.

This is conceptually distinct from tenure and from housing expenditure.

### 3. Physical adequacy / quality

Structural deficiencies, plumbing/heating problems, or established housing-adequacy measures.

This may require a dedicated housing survey and must preserve cross-survey independence.

### 4. Stability / displacement security

Involuntary moves, displacement, eviction-related risk, or other directly measured housing instability.

Simple tenure duration is not automatically equivalent to security and must not be selected without semantic justification.

## Selection discipline

No candidate may be chosen because it makes OWNER/RENTER differences larger, statistically significant, directionally convenient, or geometrically useful.

A candidate must instead satisfy predeclared identification criteria:

- public and reproducible source;
- preferably same-year 2022 primary measurement;
- compatible AGE_BAND × TENURE cohort construction;
- all eight cohort cells measurable;
- correct survey weights and variance method identifiable;
- definition invariant across age and tenure;
- no person-level cross-survey joins;
- no unsupported joint covariance;
- higher-is-better orientation defensible before values are inspected.

## Next step

E4C3 may authorize only a source-and-variable reconnaissance for H_ACCESS.

No H_ACCESS variable is selected and no new H coordinate is computed here.
