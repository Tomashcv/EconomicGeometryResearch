# E4C3B — ACS 2022 exact metadata + H_ACCESS harmonization preflight

## Purpose

E4C3A selected the 2022 ACS 1-year PUMS as the primary H_ACCESS reconnaissance source without choosing an H_ACCESS variable.

E4C3B freezes the exact 2022 cohort mapping and chooses a measurement architecture **before any ACS microdata values are opened**.

## Cohort mapping

The housing record directly contains `HHLDRAGEP`, so the frozen age bands are applied to the age of the householder without a person-level join.

`TEN` is mapped:

- `1`: owned with mortgage/loan → OWNER
- `2`: owned free and clear → OWNER
- `3`: rented → RENTER
- `4`: occupied without payment of rent → excluded from primary OWNER/RENTER comparison
- missing/GQ/vacant → excluded

This preserves the project's conceptual OWNER/RENTER split without using tenure as the H_ACCESS outcome.

## Primary H_ACCESS architecture

E4C3B selects, before opening outcomes:

`H_ACCESS_SPACE_ROOMS_PER_PERSON = RMSP / NP`

at the household/housing-unit record, aggregated as a `WGTP`-weighted mean within each AGE_BAND × TENURE cohort.

Higher values mean more rooms available per household member and are therefore higher-is-better.

Reasons for primary selection:

- identical formula for OWNER and RENTER;
- direct observed housing characteristics;
- no household-income denominator;
- no mortgage/debt-service term;
- no arbitrary 1.0-person-per-room crowding threshold;
- naturally dimensionless;
- no person-level cross-survey join;
- same-year 2022 source.

`BDSP / NP` is frozen only as a sensitivity measure.

## Why affordability is not primary

`GRPIP` and `OCPIP` are both housing-cost percentages of household income, but their numerator concepts are tenure-specific.

Gross rent includes rent and renter-paid utilities/fuels. Selected monthly owner costs include mortgage and other housing debt payments, real-estate taxes, property insurance, utilities/fuels, and applicable condominium/mobile-home costs.

That makes owner affordability partly duplicate the already-separate `D` debt-service concept while renter affordability does not. Both ACS percentage variables are also unavailable when household income is absent/nonpositive.

Affordability therefore remains useful evidence but is not the primary H_ACCESS coordinate in this architecture.

## Physical adequacy and stability

Basic-facility variables remain secondary. No ad hoc composite is authorized.

ACS move-timing/mobility variables are not re-labelled as involuntary housing-security measures.

## Inference

Housing-unit inference uses:

- `WGTP`
- `WGTP1..WGTP80`
- SDR variance `(4/80) * Σ(theta_r - theta_0)^2`

Released replicate weights are used as released; clipping is prohibited.

## Hard boundary

This phase opens only official metadata. It does not open ACS microdata values and does not compute H_ACCESS.

If metadata confirms the precommitted architecture, E4C3C may precommit the first ACS 2022 H_ACCESS execution.
