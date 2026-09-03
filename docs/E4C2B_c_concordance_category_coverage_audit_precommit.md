# E4C2B — C Concordance + Category Coverage Audit Precommit

## Purpose

E4C2B audits classification lineage for the already-frozen 2022 `C_COST`
UCC universe. It does **not** create a consumption coordinate.

The frozen C universe is the exact set of rows whose `primary_component` is
`C_COST` in the previously frozen CE component map. The expected cardinality is
435 unique UCCs. E4C2B must not mutate this universe.

## Chronology

The E4C2B code, contract, and exact hash of the frozen C map are committed
**before** any external workbook bytes are downloaded. Only after that precommit
may the execution download the three predeclared official BLS metadata files.

## Authorized source content

1. January-2022 CE UCC → CPI ELI concordance archive.
2. Current CPI item publication-level metadata, used only as current metadata;
   it is explicitly **not** treated as a 2022 publication archive.
3. Current CE UCC → PCE product concordance, used only as classification
   lineage and not as a PCE value table.

## Hard information boundary

The audit may read strings, codes, sheet names, headers, and metadata flags. It
may count mappings. It may not read or analyze CPI index levels, average-price
values, PCE expenditure levels, PCE price/quantity values, or RPP values.

The audit also freezes the methodological boundary that CPI index numbers are
not cross-category price levels. A category CPI index level cannot be divided
into another category's index level and interpreted as a relative price merely
because both are index numbers.

## Coverage outputs

For each frozen C UCC the audit records:

- whether the January-2022 CE→CPI concordance contains it;
- the mapped ELI codes, if any;
- whether an ELI-derived item-stratum code appears in the **current** CPI
  publication metadata;
- whether the current CE→PCE concordance contains the UCC.

Coverage is diagnostic. Missing mappings do not retroactively mutate C_COST and
do not cause architecture selection by outcome.

## Architecture boundary

E4C2B does not select among C_A, C_B, or C_C. In particular:

- C_A still requires a complete defensible reference-price/bundle mechanism;
- C_B still requires a defensible real-consumption identification rule rather
  than treating CPI index levels as physical prices;
- C_C still requires a separate resource-denominator and K/D/I overlap audit.

No C coordinate, five-component state vector, normalization, dimensionality
analysis, Real Inflation estimate, or final scalar is authorized here.
