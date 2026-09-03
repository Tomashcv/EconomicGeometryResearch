# E4C2A — C Reference / Price / Quantity Source Recon Preflight

## Parent

    85720af

E4C2 froze the semantic target:

    C_SEMANTIC_TARGET=CONSUMPTION_ECONOMIC_COMMAND

and deliberately selected no architecture.

E4C2A freezes only official/public source lineage discovered from BLS, BEA,
and Census documentation.

No numeric CPI, average-price, PCE, RPP, or new survey values are opened.

## 1. BLS CE UCC -> CPI ELI concordance

The BLS CPI Handbook publishes an official Consumer Expenditure UCC to CPI
Entry Level Item concordance.

The documentation also exposes an archived concordance associated with the
January 2022 CPI weight update.

This is the strongest direct lineage bridge for asking whether frozen CEX
UCC expenditure categories can be matched to CPI price categories.

Status:

    STRONG_LINEAGE

No CPI index levels are opened in E4C2A.

## 2. CPI public item structure

BLS documents the CPI aggregation hierarchy and identifies item strata as the
most granular complete and mutually exclusive item breakdown for which public
CPI indexes are available.

This supports a future metadata-level coverage audit after UCC -> ELI mapping.

It does not yet authorize category deflation.

## 3. CPI average prices

BLS publishes physical-unit average prices for selected products.

The official publication list is only a subset.

Therefore:

    CPI_AVERAGE_PRICES_COMPLETE_C_BUNDLE=NO

Average-price data may later be useful for diagnostics or narrowly defined
reference bundles, but cannot by itself support the complete frozen C
consumption universe.

## 4. BLS CE -> PCE concordance

BLS also publishes a concordance mapping CE UCC categories to detailed BEA
PCE product categories.

This provides a second official classification bridge independent of the
CE -> CPI ELI concordance.

No PCE numeric values are opened here.

## 5. BEA PCE price and quantity methodology

BEA documents that PCE prices and quantities are prepared at detailed levels,
using detailed deflation and, for some components, quantity extrapolation or
direct valuation.

This is a strong methodological reference for C_B:

    REAL_CONSUMPTION_COMMAND

but does not mean arbitrary category CPI index levels can simply be divided
into CE expenditures and summed.

A future contract must freeze the mapping, reference period, aggregation
rule, index normalization and any nonadditivity treatment before values.

## 6. BEA Regional Price Parities

RPPs are official same-year spatial price-level measures.

Our frozen bridge is:

    AGE_BAND x TENURE

not geography.

RPP therefore does not directly identify owner/renter-age C differences
without an additional frozen geographic integration layer.

Status:

    SPATIAL_SENSITIVITY_ONLY

No RPP values are opened here.

## 7. Household equivalence scales

Household composition can materially affect expenditure comparisons.

Census publishes an official three-parameter equivalence adjustment used in
income-distribution work.

Neither that scale nor any other scale is automatically selected for C.

E4C2A freezes:

    EQUIVALENCE_SCALE_REQUIRED_TO_BE_EXPLICIT=1
    C_PRIMARY_EQUIVALENCE_SCALE_SELECTED=0

## 8. Architecture implications

### C_A

    C_A_SOURCE_LINEAGE_FEASIBLE=1
    C_A_CROSS_SECTIONAL_IDENTIFICATION_RESOLVED=0

### C_B

    C_B_SOURCE_LINEAGE_FEASIBLE=1
    C_B_DEFLATION_ARCHITECTURE_RESOLVED=0

### C_C

    C_C_RESOURCE_LINEAGE_FEASIBLE=1
    C_C_K_D_I_OVERLAP_RESOLVED=0

No architecture wins E4C2A.

## 9. Next milestone

A PASS authorizes only:

    E4C2B_C_CONCORDANCE_AND_CATEGORY_COVERAGE_AUDIT_PREFLIGHT

E4C2B should inspect frozen mapping metadata and official concordance schemas
without opening CPI/PCE numeric values.

Only after that should numeric price-series acquisition be considered.

## 10. Hard boundary

    C_ARCHITECTURE_SELECTED=0
    C_COORDINATE_VALUES_AUTHORIZED=0
    PRICE_INDEX_VALUES_OPENED=0
    PCE_VALUES_OPENED=0
    FIVE_COMPONENT_STATE_VECTOR_AUTHORIZED=0
    DIMENSIONALITY_TEST_AUTHORIZED=0
    REAL_INFLATION_ESTIMATION_AUTHORIZED=0
    FINAL_SCALAR_AUTHORIZED=0
