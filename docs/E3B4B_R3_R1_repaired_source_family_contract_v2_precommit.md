# E3B4B R3 R1 — Repaired Exact Source-Family Contract V2

## Historical chain

The following historical results remain immutable:

- E3B4B original all-CU benchmark: FAIL
- E3B4B R1: MTBI-only Interview assumption disproved
- E3B4B R2: complete file-family inventory attempt FAIL
- E3B4B R3 attempt 1: ITBI schema mismatch
- E3B4B R3A: exact ITBI 2022 schema PASS
- E3B4B R3B: overly strong sample-code semantic gate FAIL
- E3B4B R3B R1: official-documentation reconciliation PASS

No prior result is overwritten.

## Exact V2 source-family rule

Frozen integrated UCC survey source:

    I = Interview Survey
    D = Diary Survey

For Interview UCCs:

    if physical 2022 family contains ITBI:
        estimator_family = ITBI
    else:
        estimator_family = MTBI

For Diary UCCs:

    estimator_family = EXPD

ITII and DTID are not appended to point-estimate data.

## Exact field normalization

MTBI:

    value field = COST
    month field = REF_MO
    year field  = REF_YR

ITBI:

    value field = VALUE
    month field = REFMO
    year field  = REFYR
    VALUE_      = topcode flag only

EXPD:

    value field = COST

## Expected 645-UCC contract

    MTBI = 390
    ITBI =   8
    EXPD = 247

Total:

    645

## Expected primary 534-UCC contract

    MTBI = 316
    ITBI =   3
    EXPD = 215

Total:

    534

The three primary ITBI UCCs are the factor-4 finance-charge UCCs.

## Zero released records

Expected valid hierarchy UCCs with no released 2022 record:

    all integrated UCCs = 20
    primary UCCs        = 19

Expected by estimator family:

    MTBI zero-record = 16
    EXPD zero-record = 4
    ITBI zero-record = 0

For the released-PUMD estimator:

    empty released record set -> numerator 0

This is not a claim that latent population expenditure was literally zero.

## Restrictions

This milestone reads metadata only.

    COST_VALUES_READ = 0
    ITBI_VALUE_VALUES_READ = 0
    NEW_ECONOMIC_VALUES_OPENED = 0

No corrected benchmark is executed here.

If this contract passes:

    ESTIMATOR_V2_SOURCE_FAMILY_CONTRACT_FROZEN = 1
    E3B4B_R4_CORRECTED_ALL_CU_BENCHMARK_V2_AUTHORIZED = 1

The original E3B4B targets and tolerances remain unchanged.
