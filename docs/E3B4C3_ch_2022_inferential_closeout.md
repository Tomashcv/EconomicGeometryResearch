# E3B4C3 — C/H 2022 Inferential Closeout

## Scope

This milestone closes the 2022 household CEX C/H workstream for the frozen
25-34 owner-versus-renter comparison.

No new estimates are calculated.

---

# Validated estimator state

The corrected CEX estimator V2 passed the unchanged official BLS 2022
all-consumer-unit benchmark.

The subsequent cohort estimator reproduced the same frozen definitions for:

    C_COST
    H_SERVICE

The 44-replicate BRR engine then passed all structural and numerical gates.

---

# C_COST

Owner 25-34:

    estimate = 38171.091887 USD/year
    BRR SE   = 1241.793694
    CI95     = [35737.176247, 40605.007528]

Renter 25-34:

    estimate = 29384.021741 USD/year
    BRR SE   = 1257.460583
    CI95     = [26919.398999, 31848.644483]

Renter minus owner:

    estimate = -8787.070146 USD/year
    BRR SE   = 1718.116290
    CI95     = [-12154.578075, -5419.562218]

Renter / owner:

    estimate = 0.769797779
    BRR SE   = 0.040067512
    CI95     = [0.691265455, 0.848330102]

The 95% normal-approximation BRR interval for the difference excludes zero,
and the ratio interval excludes one.

Therefore the 2022 C_COST difference between the frozen owner and renter
cohorts is statistically distinguishable under this survey-design inference.

This is a descriptive cohort comparison, not a causal effect of tenure.

---

# H_SERVICE

Owner 25-34:

    estimate = 19141.176266 USD/year
    BRR SE   = 510.272904
    CI95     = [18141.041374, 20141.311158]

Renter 25-34:

    estimate = 19863.973973 USD/year
    BRR SE   = 415.710505
    CI95     = [19049.181384, 20678.766562]

Renter minus owner:

    estimate = 722.797707 USD/year
    BRR SE   = 636.906686
    CI95     = [-525.539398, 1971.134811]

Renter / owner:

    estimate = 1.037761405
    BRR SE   = 0.033642256
    CI95     = [0.971822583, 1.103700227]

The difference interval includes zero and the ratio interval includes one.

Therefore this 2022 sample does not establish a statistically distinguishable
H_SERVICE difference between the frozen owner and renter cohorts.

This does not imply equality of housing circumstances.

---

# What this establishes

The CEX implementation for C_COST and H_SERVICE is now:

    source-family repaired
    official-benchmark validated
    cohort point-estimate validated
    BRR-inference validated

The household evidence is consistent with C and housing-service circumstances
being economically different objects.

Combined with the earlier macro C-versus-H divergence evidence, this
strengthens the case that consumption purchasing power and housing position
should not be collapsed mechanically into one state variable.

---

# What this does NOT establish

This milestone does NOT prove the entire five-dimensional state hypothesis:

    x_g(t) = [C,H,K,D,I]^T

In particular:

    K has not yet been empirically tested
    D has not yet been empirically tested
    I has not yet been empirically tested
    H_ACCESS remains distinct from H_SERVICE and still requires implementation

It also does not establish that exactly five dimensions are necessary or
sufficient.

---

# Real Inflation remains separate

The five-dimensional state vector is not itself Real Inflation.

Still required later:

    frozen capability bundle B_g
    resource-preservation cost R_g(t;B_g)

Candidate definition remains:

    pi_real_g(t) = Delta ln R_g(t;B_g)

Therefore:

    STATE_CHANGE_EQUALS_COST_INFLATION = 0
    GE_EQUALS_REAL_INFLATION = 0
    OBSERVED_EXPENDITURE_CHANGE_EQUALS_INFLATION = 0

---

# Next workstream

Authorized next empirical work:

    E4 — K / D / I household-state architecture

Primary survey roles:

    SCF -> K, D, housing balance-sheet/access state
    CPS ASEC -> income/resources and employment-security I

No direct record linkage between CEX, CPS and SCF is permitted.

Pseudo-cohort estimands remain the integration layer.
