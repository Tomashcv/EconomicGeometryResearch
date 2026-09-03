# E4B1 R0 — BRR Audit-Lineage Validator Repair

## Parent precommit

    af563da

The first E4B1 execution stopped before opening CEX values.

Observed failure:

    RuntimeError:
    missing BRR audit invariant=BRR_REPLICATE_COUNT=44

This is a validator-lineage error, not a scientific or estimator failure.

## Why the requirement was wrong

E4B1 already validates the exact BRR design from:

    data/metadata/E3B4C1_exact_brr_engine_contract.json

That contract is the frozen source for:

    replicate_count = 44
    replicate set = WTREP01 ... WTREP44
    BRR variance formula
    direct renter-owner difference replication
    direct renter/owner ratio replication

The E3B4C2 execution audit has a different role:

    attest that the first frozen BRR execution passed.

It is not required to duplicate every engine-contract field.

Therefore requiring the literal line:

    BRR_REPLICATE_COUNT=44

inside the E3B4C2 execution audit was an unnecessary and incorrect
lineage validator.

## Exact repair

Keep:

    E3B4C2_FIRST_BRR_EXECUTION=PASS

as the execution-audit requirement.

Keep:

    E3B4C1 replicate_count == 44

as the exact design requirement.

Add the repaired E4B1 audit line:

    E3B4C1_BRR_REPLICATE_COUNT=44

No scientific code, CEX estimator, cohort definition, UCC mapping,
calendar rule, weighting rule, BRR formula, or outcome gate is changed.

## Attempt 1

The original execution output is preserved byte-for-byte as:

    data/metadata/E4B1_attempt1_execution.txt

with SHA-256:

    858988aca4d9dd8367ba705fed054ee23c7c3b8e09f770edb7cb9b854e3d1b92

## Boundary

During E4B1 R0:

    RAW_CEX_DATA_READ=0
    NEW_C_H_VALUES_OPENED=0
    BRR_REPLICATE_VALUES_OPENED=0

E4B2 remains unauthorized until the repaired E4B1 completes successfully.
