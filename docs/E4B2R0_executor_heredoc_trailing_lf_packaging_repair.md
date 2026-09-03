# E4B2 R0 — Executor Heredoc Trailing-LF Packaging Repair

## Parent

    98e58b2

The first E4B2 wrapper stopped before its precommit and before any CEX
economic values were opened.

Observed:

    EXPECTED executor SHA:
    0677d13ba7c688da8e2a68e260f4e85eef340c5be5393e5ecd91452b5584f0dd

    GENERATED executor SHA:
    eab6e7bd87c3286cf727a90c68ad3bf6fe17e7f80d1746f440f8cef919ae67a0

## Classification

This is a packaging failure.

The shell heredoc inserted one additional final LF after an executor that
already ended with LF.

Byte-level forensic proves:

    failed bytes    = 58167
    canonical bytes = 58166

and removing exactly one final LF from the failed generated executor yields
the exact precomputed canonical SHA:

    0677d13ba7c688da8e2a68e260f4e85eef340c5be5393e5ecd91452b5584f0dd

No Python statement or scientific token changes.

## Outcome boundary

At failure:

    RAW_CEX_DATA_READ=0
    NEW_AGE35_64_C_H_VALUES_OPENED=0
    CEX_WTREP_VALUES_READ=0
    SCIENTIFIC_EXECUTION_STARTED=0

Therefore the pre-outcome design chronology remains intact.

## Exact repair

Apply one operation only:

    remove exactly one final LF byte

from the untracked generated executor.

Do not regenerate the economic code.

Do not alter:

    source families
    UCC mapping
    age bands
    tenure mapping
    point estimator
    weighting
    BRR engine
    invariance controls
    output shapes
    outcome-independent gates

The canonical E4B2 executor is then committed and pushed before any new C/H
value is opened.

## Attempt-1 provenance

Failed wrapper SHA-256:

    a0bbdda99b69b04c27d51da7956d6f126b2869aee840b782943666914a159563

Failed generated executor SHA-256:

    eab6e7bd87c3286cf727a90c68ad3bf6fe17e7f80d1746f440f8cef919ae67a0

The hashes and exact byte relation preserve the failed packaging attempt
without duplicating a 58 KB executor whose only difference is one final LF.
