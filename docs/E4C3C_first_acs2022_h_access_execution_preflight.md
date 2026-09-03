# E4C3C — First ACS 2022 H_ACCESS execution preflight

## Purpose

E4C3C is the final values-closed checkpoint before the first ACS H_ACCESS execution.

It freezes the exact official microdata source, the record-level estimands, cohort eligibility, replicate inference, contrast definitions, output schema, and failure gates.

**No ACS microdata is downloaded, listed, opened, or parsed in E4C3C.**

## Official input

The first execution will use the U.S. Census Bureau national 2022 ACS 1-Year PUMS **housing** CSV archive:

`https://www2.census.gov/programs-surveys/acs/data/pums/2022/1-Year/csv_hus.zip`

The raw ZIP is not committed to Git because the national archive is large. The execution must freeze its SHA-256 and ZIP-member manifest before parsing any row values.

All matching housing CSV members are processed. Person files and Puerto Rico files are prohibited for the primary national execution.

## Primary estimator

For each eligible housing record:

`q_i = RMSP_i / NP_i`

For cohort `g`:

`theta_g = sum(WGTP_i * q_i) / sum(WGTP_i)`

The eight primary cells are the four frozen age bands crossed with OWNER / RENTER.

OWNER: `TEN in {1,2}`.

RENTER: `TEN == 3`.

`TEN == 4` and missing tenure are excluded.

No person-level join is needed because the housing record contains `HHLDRAGEP`.

## Sensitivity

`BDSP / NP` is frozen as a sensitivity estimand only.

It cannot replace the rooms-per-person primary because of the observed owner/renter result.

## Replicate inference

For each of `WGTP1..WGTP80`, the point estimator is recomputed with the same record-level outcome and the same eligibility universe.

Replicate weights are preserved as released and are not clipped.

Variance:

`V(theta) = (4/80) * sum_r (theta_r - theta_0)^2`

Renter-minus-owner differences and renter-divided-by-owner ratios are calculated directly inside every replicate before their variance is calculated.

No sign, magnitude, CI-exclusion, or significance result can pass or fail the scientific architecture.

## Cross-survey boundary

`H_SERVICE` remains CEX evidence.

`H_ACCESS` is ACS evidence.

There is no person-level join and no joint covariance between the two surveys. E4C3D therefore cannot combine H_SERVICE and H_ACCESS into an automatic H scalar.

Even if rooms-per-person executes successfully, it identifies a **space-access subcoordinate**, not the entire Housing Economic Security and Access concept.

## First-execution failure gates

The first value-opening execution must fail rather than mutate the estimator if:

- the downloaded ZIP cannot be hash-frozen;
- no valid housing CSV members are present;
- required columns are missing;
- any of the eight primary cohort cells is empty;
- a full or replicate denominator is nonpositive/nonfinite;
- a primary full or replicate estimate is nonfinite.

A failure after values open must be preserved and classified before any repair.

## Authorization

A PASS authorizes E4C3D to acquire the exact national ACS housing ZIP, freeze its byte hash and member manifest, and only then open the first H_ACCESS values.
