# E3B4B R3 — Exact UCC Source-Family Contract V2

## Parent

    65162a4

## Historical state preserved

The following remain immutable historical results:

    E3B3C4 estimator V1 contract
    E3B4A first cohort estimates
    E3B4B official benchmark FAIL
    E3B4B R1 MTBI-vs-ITBI forensic
    E3B4B R2 complete source-family inventory FAIL

Nothing is retroactively overwritten.

---

# 1. Proven defect in estimator V1

The frozen integrated hierarchy identifies survey source:

    I = Interview
    D = Diary

Estimator V1 incorrectly treated:

    source I -> MTBI

as universal.

E3B4B R1 disproved this:

    374 Interview UCCs observed only in MTBI
    8 Interview UCCs observed in ITBI
    16 Interview UCCs had no released 2022 records

The eight ITBI UCCs consist of:

    five Pensions and Social Security UCCs
    three finance-charge UCCs

The three finance-charge UCCs are all factor-4 UCCs and are primary C_COST.

---

# 2. Official PUMD file semantics

For the Interview Survey:

    MTBI = monthly expenditures
    ITBI = detailed income, monthly
    ITII = imputed-income iterations, monthly

For the Diary Survey:

    EXPD = detailed expenditure/non-expenditure, weekly
    DTBD = detailed income, annual
    DTID = income-imputation iterations, annual

The official UCC estimation sample code uses the expenditure/income point
files, not the multiple-imputation iteration files, for its point estimates.

Therefore:

    ITII is NOT a point-estimate source family.
    DTID is NOT a point-estimate source family.

---

# 3. Estimator V2 physical-family rule

For every frozen integrated UCC j:

## Interview source

If the released 2022 UCC occurs in ITBI:

    estimator_family_j = ITBI

Otherwise:

    estimator_family_j = MTBI

This includes Interview UCCs with zero released records in 2022. Their economic
domain is expenditure rather than income and therefore remains MTBI-domain.

## Diary source

For every Diary expenditure UCC:

    estimator_family_j = EXPD

Diary UCCs with zero released EXPD records in 2022 remain EXPD-domain.

---

# 4. Zero released records

The integrated hierarchy may contain a valid UCC for which the public-use
microdata contain no released record in a particular calendar year.

This does NOT mean:

    unknown survey source
    unknown estimator family
    underlying population expenditure literally equals zero

For the PUMD point estimator it means:

    numerator_j = sum over released records = 0

while the complete source-specific population denominator remains unchanged.

Thus:

    EMPTY_RELEASED_RECORD_SET_NUMERATOR = 0

This rule is mathematical treatment of the released PUMD, not an economic
claim about latent expenditure.

---

# 5. ITBI point estimator

ITBI is monthly.

Calendar-year 2022 ITBI uses the same five Interview collection quarters:

    221
    222
    223
    224
    231

and calendar filter:

    reference year = 2022
    reference month = 1..12

The exact released year-field spelling may be:

    REFYR
or
    REF_YR

and is frozen from header inspection before V2 execution.

For ITBI UCC j:

    numerator_gj
      = sum(COST_r * FINLWT21_i)

using the Interview family weight attached by quarter + NEWID.

The denominator is the same Interview calendar-year population denominator
already frozen in E3B3C4.

Hierarchy factor is then applied UCC-by-UCC.

---

# 6. MTBI point estimator

Unchanged from estimator V1:

    REF_YR = 2022
    REF_MO = 1..12
    numerator = sum(COST * FINLWT21)
    denominator = Interview calendar population

---

# 7. Diary point estimator

Unchanged from estimator V1:

    family = EXPD
    numerator = sum(COST * FINLWT21)
    denominator = Diary calendar population
    source periodicity multiplier = 13

---

# 8. Multiple-imputation files

    ITII point-estimate source = PROHIBITED
    DTID point-estimate source = PROHIBITED

ITII/DTID may later be relevant to income multiple-imputation inference, but
they may not be naïvely appended to ITBI/DTBD because this would duplicate
imputation iterations.

---

# 9. Expected V2 family counts

Frozen 645-UCC map:

    Interview = 398
    Diary     = 247

Expected V2:

    ITBI = 8
    MTBI = 390
    EXPD = 247

Primary 534-UCC map:

    ITBI = 3
    MTBI = 316
    EXPD = 215

Expected zero-released-record UCCs in 2022:

    all frozen map = 20
    primary map    = 19

Those zero-record UCCs remain part of the map with zero released-record
numerator.

---

# 10. Required next validation

R3 itself reads no COST.

If R3 passes:

    ESTIMATOR_V2_SOURCE_FAMILY_CONTRACT_FROZEN = 1

The next milestone is:

    E3B4B R4 — Corrected all-CU benchmark V2

R4 MUST reuse the original E3B4B targets and original precommitted tolerances.

No benchmark gate may be loosened.

Only if R4 passes may corrected cohort estimates be rerun.

---

# 11. Interpretation state

    COST_VALUES_READ = 0
    NEW_ECONOMIC_VALUES_OPENED = 0

    E3B4A_V1_MAGNITUDES_VALIDATED = 0
    COHORT_POINT_ESTIMATE_INTERPRETATION_AUTHORIZED = 0

    REAL_INFLATION_ESTIMATED = 0
    REAL_INFLATION_ESTIMATION_AUTHORIZED = 0
    FINAL_SCALAR_AUTHORIZED = 0

