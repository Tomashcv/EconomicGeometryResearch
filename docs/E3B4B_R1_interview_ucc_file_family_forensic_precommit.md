# E3B4B R1 — Interview UCC File-Family Coverage Forensic

## Trigger

E3B4B benchmark result:

    E3B4B_ALL_CU_OFFICIAL_BENCHMARK = FAIL

while:

    12 / 14 broad categories within 5%
    C_COST APE = 1.3009%
    H_SERVICE APE = 0.2376%

The failure is permanently preserved.

No benchmark criterion is changed.

---

# 1. Key observed residual

2022 published:

    Personal insurance and pensions = 8742.00

Current MTBI/EXPD estimator:

    519.2007500259

Residual:

    8222.7992499741

Published:

    Life and other personal insurance = 519.20
    Pensions and Social Security      = 8222.80

This exact numerical decomposition motivates a source-file coverage forensic.

It does not itself authorize a repair.

---

# 2. Question

The frozen component map identifies survey source:

    I = Interview
    D = Diary

It does NOT necessarily prove that every Interview UCC is physically sourced
from MTBI.

Current estimator implementation assumed:

    Interview source -> MTBI

R1 tests that assumption against the actual 2022 PUMD archives.

---

# 3. Interview candidate file families

Inspect UCC presence in:

    MTBI
    ITBI

for calendar-source quarters:

    221
    222
    223
    224
    231

No COST or income amount is required for this forensic.

Only:

    UCC presence
    file membership
    hierarchy metadata

are needed.

---

# 4. Required classification

Every one of the 398 frozen Interview-sourced UCCs must be classified as:

    MTBI_ONLY
    ITBI_ONLY
    BOTH
    NEITHER

The forensic must separately identify:

    Personal insurance and pensions UCCs
    Pensions and Social Security UCCs
    factor-4 UCCs
    Miscellaneous UCCs

---

# 5. Diary sanity

The 247 Diary-sourced UCCs are checked for EXPD presence.

This is coverage-only.

---

# 6. No retrofit

Regardless of outcome:

    E3B3C4 remains historically frozen
    E3B4A remains historically frozen
    E3B4B remains historically FAIL

If the MTBI-only assumption is disproved, a NEW estimator revision must be
precommitted and rerun.

No historical file or result is overwritten.

---

# 7. Interpretation state

    E3B4A_MAGNITUDES_VALIDATED = 0
    COHORT_POINT_ESTIMATE_INTERPRETATION_AUTHORIZED = 0
    REAL_INFLATION_ESTIMATION_AUTHORIZED = 0
    ESTIMATOR_MUTATION_AUTHORIZED = 0

