# E4C2C — C identification + architecture decision precommit

## Scope

E4C2C is a frozen-evidence decision step. It reads only already-frozen E4C2B outputs.

It does **not** read raw CEX records, CPI index values, CPI average-price values, PCE expenditure/price/quantity values, regional price parities, or any new economic values.

## Problem being decided

The project requires a scientifically interpretable consumption component `C`.

A nominal expenditure total is not automatically a real-consumption quantity measure because expenditure combines prices, quantities, mix, and household choice. A CPI series index is a temporal relative and its numerical index level is not automatically a cross-category price level. Concordance coverage identifies classification links, not prices or quantities.

Therefore E4C2C must decide whether the frozen evidence already identifies a defensible `C` state coordinate.

## Frozen prior evidence

E4C2B established:

- frozen primary `C_COST` universe: 435 unique UCCs;
- 387/435 map to the 2022 CPI ELI concordance;
- 435/435 appear in the PCE concordance;
- 387/435 are covered by both concordances;
- complete reference-price vector unresolved;
- cross-sectional real-quantity identification unresolved;
- C-to-K/D/I overlap/comparability unresolved;
- equivalence-scale placement unresolved;
- C architecture not selected.

These are decision inputs, not retroactive E4C2B outcome gates.

## Candidate architecture rules

1. `NOMINAL_C_COST_AS_REAL_STATE`
   - cannot be selected as a real-consumption state merely because expenditure is observed.

2. `AGGREGATE_CPI_DEFLATED_C_COST`
   - cannot solve household cross-sectional quantity identification or category price-level comparability.

3. `UCC_ELI_CPI_DEFLATED_REAL_QUANTITY`
   - cannot be selected unless reference-price semantics and coverage are adequate; no silent imputation of the 48 non-CPI-mapped UCCs is allowed.

4. `PCE_CONCORDANCE_BASED_REAL_QUANTITY`
   - concordance coverage alone cannot turn macro PCE concepts into household real quantities.

5. `HYBRID_CPI_PCE_REAL_QUANTITY`
   - combining concordances does not itself identify cross-category price levels or household quantities.

6. `FIXED_REFERENCE_BASKET_COST_INDEX`
   - retained as a distinct future **cost-side** candidate for temporal purchasing-power erosion;
   - it is not interchangeable with a real-consumption quantity state coordinate.

7. `REAL_CONSUMPTION_QUANTITY_STATE`
   - remains the target semantic for a positive consumption-capacity state only if reference prices/quantities and comparability are identified.

## Valid negative decision

E4C2C is successful if it rigorously concludes that no current real `C` state architecture is identified. A negative identification decision is not a project failure.

## Hard boundaries

E4C2C must not compute:

- C coordinate values;
- transformed/normalized five-component values;
- geometry;
- dimensionality;
- Real Inflation;
- any final scalar.

If current evidence is insufficient, the only permissible authorization is a targeted follow-on identification-evidence audit.
