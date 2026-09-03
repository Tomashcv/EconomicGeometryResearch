# E3B4A V2 R1 — ITBI Topcode Diagnostic Repair

## Parent

    efdea97

E3B4A V2 point estimates PASS and remain frozen.

Observed audit:

    ITBI_SELECTED_ROWS  = 2196
    ITBI_TOPCODED_ROWS = 29499

The second number cannot describe the selected primary-ITBI rows because it is
larger than the selected-row count.

Code inspection shows that VALUE_=="T" was counted before filtering ITBI to:

    the 3 primary ITBI UCCs
    REFYR = 2022
    REFMO = 1..12

This affects diagnostic metadata only.

The following remain unchanged:

    cohort definitions
    estimator-family contract
    COST values
    ITBI VALUE values
    weights
    denominators
    UCC estimates
    component estimates
    owner/renter comparisons
    R4 benchmark result

R1 recomputes only topcode-flag counts using:

    NEWID
    UCC
    REFMO
    REFYR
    VALUE_

and cohort metadata from FMLI.

It does NOT read:

    VALUE
    COST

Expected identity:

    PRIMARY_ITBI_SELECTED_ROWS = 2196

Corrected topcode count must satisfy:

    0 <= PRIMARY_ITBI_TOPCODED_ROWS <= 2196

The original 29499 value is preserved as historical evidence and explicitly
classified as a pre-filter diagnostic count.

No scientific result is changed.
