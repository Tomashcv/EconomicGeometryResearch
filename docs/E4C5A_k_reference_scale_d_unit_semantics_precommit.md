# E4C5A — K reference scale + D exact unit semantics

## Purpose

E4C5 froze the transform architecture while leaving two parameters unresolved:

1. the common positive `K_REF_FIN_USD`;
2. the exact storage unit of `PIRTOTAL`.

E4C5A resolves these without opening the eight target AGE_BAND × TENURE K/D result cells.

## K reference population

The source is the official 2022 SCF Summary Extract Public Data.

Only three fields are used:

- `Y1` to identify the five implicates;
- `WGT` as the survey weight;
- `FIN` as financial assets.

No AGE field, tenure variable, OWNER/RENTER label, target cohort definition, or target K result is used.

For each implicate independently, E4C5A retains finite `FIN > 0` and finite positive `WGT`, sorts by FIN, and selects the first FIN whose cumulative weight reaches at least one half of eligible weight.

The common reference is the arithmetic mean of the five implicate-specific weighted medians.

This value is a transform scale, not a target outcome and not a replacement K estimand.

## D exact unit semantics

The official Federal Reserve summary-variable SAS macro is the canonical semantic source.

E4C5A requires the macro to show that `PIRTOTAL` is computed as total monthly payments divided by a monthly-income denominator and cross-checks that the `PIR40` indicator compares `PIRTOTAL` with `0.4`.

If both checks pass, `PIRTOTAL` is a fraction, not a percentage-point number:

`D_STATE = -PIRTOTAL`

and the multiplier to fraction is exactly `1.0`.

No empirical target D value is used to infer the unit.

## Source chronology

The official SCF summary ZIP is SHA-256 frozen and its ZIP central directory is committed before any CSV member byte is opened.

The raw ZIP is not Git tracked.

## Boundary

E4C5A freezes parameters only.

It does not open target K/D results, does not compute transformed target coordinates, and does not authorize cross-coordinate metric scaling or geometry.
