# E4A2B — CPS Full-Weight Bridge Audit Precommit

## Parent

    6b8b670

E4A2A is frozen PASS.

The only unresolved CPS inference issue carried forward is:

    CPS_E4A2_POINT_WEIGHT=HSUP_WGT
    CPS_REPLICATE_BASE_WEIGHT=PWWGT0
    CPS_PWWGT0_DOCUMENTED_COUNTERPART=MARSUPWT
    CPS_HOUSEHOLD_FULL_WEIGHT_BRIDGE=PENDING

E4A2B tests that bridge before any I outcome is opened and before any of the
160 replicate-weight columns are parsed.

---

## 1. Scientific boundary

Authorized CPS main-file value fields:

Household records:

    H_SEQ
    HSUP_WGT
    H_HHTYPE

Person records:

    PH_SEQ
    PPPOS
    MARSUPWT
    A_EXPRRP

Authorized replicate-file fields:

    PWWGT0
    H_SEQ
    PPPOS

Explicitly prohibited:

    PWWGT1 ... PWWGT160 values
    WEWKRS
    WEUEMP
    WRK_CK
    every other I outcome
    FIN and every K outcome
    PIRTOTAL and every D outcome
    dimensionality tests
    Real Inflation estimation
    final scalar estimation

Reading raw records is permitted only to slice the predeclared fields above.
No other numeric field may be interpreted.

---

## 2. Official household merge path

The frozen Census usage instructions establish the household workflow:

    keep household records with H_HHTYPE = 1

    create a reference-person person file using
    A_EXPRRP in {1,2}

    merge household H_SEQ to person PH_SEQ

    create the reference-person replicate file using
    PPPOS = 41

    merge the reference-person replicate file to the
    household/reference-person file by H_SEQ

E4A2B therefore requires the observed 2022 data to satisfy that path without
post-hoc key selection.

---

## 3. Weight precision

Official 2022 ASEC data dictionary:

    HSUP_WGT  -> 2 implied decimals
    MARSUPWT  -> 2 implied decimals

Official 2022 replicate instructions/SAS layout:

    PWWGT0 -> 4 implied decimals

Therefore the precommitted comparisons are:

Household to reference person:

    HSUP_WGT == MARSUPWT

exactly at their common 2-decimal representation.

Replicate full weight to person full weight:

    abs(PWWGT0 - MARSUPWT) <= 0.0050

The tolerance is not a fitted parameter. It is fixed before reading values and
exists only because a 4-decimal official weight is being compared with its
documented 2-decimal public-use counterpart.

---

## 4. Parser verification

The official SAS file publishes a PWWGT0 total.

E4A2B parses only the published PWWGT0 total from the SAS documentation and
requires the sum of raw PWWGT0 records to match it exactly at four decimal
places.

This is a hard parser/scaling gate.

No PWWGT1-PWWGT160 total is parsed or tested.

---

## 5. Hard gates

PASS requires all of the following:

    upstream E4A2A PASS and E4A2B authorization

    exact official raw-source hashes

    exact one reference person for every H_HHTYPE=1 household

    every such reference person has PPPOS=41

    exact replicate match for every such reference person

    exact HSUP_WGT == MARSUPWT at 2 decimals

    PWWGT0 / MARSUPWT discrepancy <= 0.0050 for every matched reference person

    exact PWWGT0 published-total verification

Any failure is preserved as forensic output.

No repair or alternate transformation is authorized inside this milestone.

---

## 6. Authorization boundary

Only a complete E4A2B PASS may produce:

    E4A2C_CPS_REPLICATE_ENGINE_PREFLIGHT_AUTHORIZED=1

Even after PASS:

    I_VALUES_OPEN_AUTHORIZED=0
    K_VALUES_OPEN_AUTHORIZED=0
    D_VALUES_OPEN_AUTHORIZED=0
    K_D_I_INFERENCE_AUTHORIZED=0
    FIVE_DIMENSIONALITY_PROVEN=0
    REAL_INFLATION_ESTIMATION_AUTHORIZED=0
    FINAL_SCALAR_AUTHORIZED=0
