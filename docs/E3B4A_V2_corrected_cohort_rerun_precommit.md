# E3B4A V2 — Corrected 2022 Cohort Point Estimates

## Parent

    e5d012e

## Upstream validation

E3B4B R4 validated estimator V2 against the unchanged official 2022 BLS
all-consumer-unit benchmark:

    TOTAL APE                        = 0.20055%
    weighted absolute error ratio   = 0.35947%
    categories within 5%            = 14 / 14
    C_COST APE                      = 0.45748%
    H_SERVICE APE                   = 0.23765%

Therefore the corrected cohort rerun is authorized.

---

# Historical preservation

Original E3B4A V1 remains immutable.

It used the defective assumption:

    Interview source -> MTBI only

The V1 values remain historical evidence and are not overwritten.

All corrected outputs use new V2 filenames.

---

# Cohorts

Exactly the same frozen cohorts as original E3B4A:

    AGE25_34_OWNER
        AGE_REF 25..34
        CUTENURE 1,2,3

    AGE25_34_RENTER
        AGE_REF 25..34
        CUTENURE 4

No cohort definition changes are permitted.

---

# Components

Exactly the same frozen primary component map:

    C_COST
    H_SERVICE

Expected primary UCCs:

    total = 534

Estimator-family split:

    MTBI = 316
    ITBI =   3
    EXPD = 215

The three ITBI primary UCCs are factor-4 finance-charge UCCs.

No Pensions/Social Security UCC enters the primary components because
Personal insurance and pensions remains excluded from C_COST.

---

# V2 source schemas

MTBI:

    point value = COST
    month       = REF_MO
    year        = REF_YR

ITBI:

    point value = VALUE
    month       = REFMO
    year        = REFYR
    VALUE_      = topcode diagnostic only

EXPD:

    point value = COST
    weekly-to-quarter multiplier = 13

ITII is not appended.

---

# Calendar-year denominator

Interview calendar-year denominator is unchanged from V1.

Five quarters:

    221
    222
    223
    224
    231

Calendar scope:

    first-year Jan/Feb/Mar = 0, 1/3, 2/3
    first-year Apr-Dec     = 1
    following Jan/Feb/Mar  = 1, 2/3, 1/3

Population contribution:

    FINLWT21 / 4 * scope

Diary denominator remains:

    FINLWT21 / 4

for quarters:

    221
    222
    223
    224

---

# Frozen V1 denominator identity

Because cohort definitions and family weights are unchanged, V2 must reproduce
the original E3B4A source denominators.

Expected source/cohort rows:

    owner Interview = 1486
    renter Interview = 1918
    owner Diary = 775
    renter Diary = 908

V2 denominators must equal V1 denominators within numerical floating-point
tolerance.

This is a structural gate.

---

# Expected mechanical repair identities

H_SERVICE contains no ITBI UCC.

Therefore:

    H_SERVICE_V2 = H_SERVICE_V1

up to floating-point tolerance.

C_COST contains exactly three ITBI UCCs that were omitted by V1.

Therefore:

    C_COST_V2 - C_COST_V1
        = summed corrected ITBI primary contribution

within floating-point tolerance.

These are implementation identities, not outcome-based economic gates.

No sign or magnitude of owner-vs-renter differences is precommitted.

---

# Missing / negative values

Same frozen estimator semantics:

    missing released numerical value -> zero
    negative values -> preserve
    clipping -> prohibited
    winsorization -> prohibited
    positive-spender conditioning -> prohibited

---

# Outputs

New V2 outputs only:

    E3B4A_V2_2022_cohort_denominators.tsv
    E3B4A_V2_2022_primary_ucc_estimates.tsv
    E3B4A_V2_2022_component_point_estimates.tsv
    E3B4A_V2_2022_owner_renter_comparison.tsv
    E3B4A_V2_2022_itbi_primary_ucc_estimates.tsv
    E3B4A_V2_v1_v2_component_delta.tsv

---

# Interpretation

On structural PASS:

    corrected 2022 cohort point estimates may be interpreted descriptively

but:

    no SE
    no CI
    no p-value
    no causal claim
    no welfare claim
    no inflation claim

because the BRR component engine has not yet been frozen.

Even after PASS:

    OBSERVED_EXPENDITURE_CHANGE_EQUALS_INFLATION = 0
    REAL_INFLATION_ESTIMATION_AUTHORIZED = 0
    FINAL_SCALAR_AUTHORIZED = 0

