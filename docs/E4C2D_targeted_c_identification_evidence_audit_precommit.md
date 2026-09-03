# E4C2D — Targeted C identification-evidence audit precommit

## Scope

E4C2D is a documentation-and-methodology audit authorized by frozen E4C2C.

It may acquire and freeze official BLS HTML documentation after the precommit. It must not open CPI index observations, CPI average-price observations, PCE expenditures, PCE price/quantity indexes, new CE expenditure values, or survey microdata records.

## Questions frozen before acquisition

### Q1 — CE quantity / unit-value support

Does CE PUMD generally observe quantity or unit value at the expenditure-record level strongly enough to identify a broad real-consumption-quantity state for the frozen C universe?

A few special-item quantity fields do not satisfy a general 435-UCC identification requirement.

### Q2 — CPI reference-price support

Do official CPI data provide broadly available cross-category **price levels** suitable as a complete reference-price vector?

CPI index numbers and average-price levels are conceptually distinct. A temporal price index is not automatically a cross-category price level.

### Q3 — CE-PCE bridge semantics

Does a CE-to-PCE concordance or distributional PCE procedure directly observe household quantities?

Mapping, allocation, imputation, and proportional scaling are evidence about statistical construction, not direct observation of household physical quantities.

### Q4 — Equivalence scale

If BLS documents an equivalence-scale convention in an experimental distributional-PCE procedure, E4C2D records it as evidence only. It does not adopt that scale for Economic Geometry Research.

## Outcome-independent decision rule

A direct quantity path remains unresolved if broad CE quantities/unit values are unavailable.

A reference-price path remains unresolved if price-level coverage is narrow or incomplete.

A PCE concordance path remains unresolved as a direct household-quantity measure if household PCE is allocated/scaled from CE rather than directly observed.

No result in this phase may authorize a C coordinate, normalization, geometry, dimensionality, Real Inflation, or a final scalar.

## Intended follow-on

If E4C2D passes, it may authorize E4C2E: a semantic-branch and measurement-design preflight that explicitly chooses what `C` is allowed to mean given the identification boundary. That is a design phase, not a value-computation phase.
