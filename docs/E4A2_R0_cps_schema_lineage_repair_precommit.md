# E4A2 R0 — CPS Schema-Lineage Validator Repair

## Parent

    6a7fb10

## Original E4A2 result

The first E4A2 audit produced:

    CPS_I_REQUIRED_SCHEMA = FAIL

while simultaneously producing:

    SCF_FULL_REQUIRED_SCHEMA = PASS
    SCF_K_D_REQUIRED_SCHEMA = PASS

    SCF_POINT_ESTIMATOR_CONTRACT = PASS
    K_ESTIMATOR_CONTRACT = PASS
    D_ESTIMATOR_CONTRACT = PASS

    CPS_I_POINT_ESTIMATOR_CONTRACT = PASS
    CPS_INFERENCE_PREFLIGHT = PASS

No K, D or I economic values were opened.

---

# Root cause

The E4A2 validator required WRK_CK to be present in:

    E4A1_local_schema_audit.tsv

However that artifact was generated during E4A1 before the I-semantic repair.

The original E4A1 required CPS metadata set did not include WRK_CK.

Later E4A R1 explicitly audited the repaired I metadata against the frozen
official Census variable metadata and established:

    REPAIRED_I_REQUIRED_METADATA = PASS

and froze:

    I_SECONDARY_ANY_WORK = WRK_CK_EQ_1

Therefore WRK_CK availability is already validated by a newer, stronger
upstream artifact.

The E4A2 failure is a validator lineage mismatch, not a physical CPS schema
failure.

---

# Repair principle

For fields already audited by E4A1:

    A_AGE
    A_EXPRRP
    HSUP_WGT
    H_TENURE
    WEWKRS
    WEUEMP

continue to require exact presence in:

    E4A1_local_schema_audit.tsv

For WRK_CK, require the newer frozen E4A R1 evidence:

    REPAIRED_I_REQUIRED_METADATA = PASS
    I_SECONDARY_ANY_WORK = WRK_CK_EQ_1

This does not weaken the gate.

It routes each variable to the artifact in which it was actually audited.

---

# No scientific contract mutation

The following remain unchanged:

    K primary = FIN
    D primary = -PIRTOTAL

    I_FYFT_SHARE = WEWKRS == 1
    I_SEARCH_BURDEN_SHARE = WEUEMP in {2,3,4,5,6,7}

    SCF implicates = 5
    SCF bootstrap replicates required = 999

    CPS replicate count = 160
    CPS variance = (4/160) * sum((theta_r - theta_0)^2)

No outcome gate is changed.

No estimator definition is changed.

No economic values are opened.

---

# Attempt preservation

The original E4A2 FAIL is retained as:

    E4A2_attempt1_cps_schema_lineage_failure_execution.txt
    E4A2_attempt1_cps_schema_lineage_failure_audit.txt

It must not be deleted or rewritten.
