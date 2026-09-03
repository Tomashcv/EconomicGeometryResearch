from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

CONTRACT = (
    ROOT
    / "data/metadata/E3B4C1_exact_brr_engine_contract.json"
)

E3B4C_AUDIT = (
    ROOT
    / "data/metadata/E3B4C_brr_preflight_audit.txt"
)

HEADER_AUDIT = (
    ROOT
    / "data/metadata/E3B4C_brr_weight_header_audit.tsv"
)

CODE_CONTEXT = (
    ROOT
    / "data/metadata/E3B4C_official_brr_code_context.tsv"
)

V2_UCC_CONTRACT = (
    ROOT
    / "data/metadata/E3B4B_R3_R1_estimator_v2_ucc_source_contract.tsv"
)

V2_COMPONENTS = (
    ROOT
    / "data/results/E3B4A_V2_2022_component_point_estimates.tsv"
)

V2_COMPARISON = (
    ROOT
    / "data/results/E3B4A_V2_2022_owner_renter_comparison.tsv"
)

AUDIT_OUT = (
    ROOT
    / "data/metadata/E3B4C1_exact_brr_engine_contract_audit.txt"
)


EXPECTED_SHA = {
    E3B4C_AUDIT:
        "bf669dedc7b7e46830b92108ab27b0e2dcc7713d7479e03a368d7635c5b81f54",

    HEADER_AUDIT:
        "7e3e53741a0618e12a2fa3218499885926c354259d23794104021ee15665422d",

    CODE_CONTEXT:
        "a9d37f27a0ffb15f8046ec6489ee35381e22455c65b91f2ca0086fb75806816d",

    V2_UCC_CONTRACT:
        "72c253f9295aad902c39636277b7cf23aa5f651206eb8ff416d58a45e7bbf047",

    V2_COMPONENTS:
        "7fc2513c82b78a3c1ced549192ab45b2fe849361d296a57743cd1846b01ef366",

    V2_COMPARISON:
        "46a7ee46e845a866d1a06b629c412d6ce7dfd80b80f2af99836e10516faee682",
}


def sha256(path: Path) -> str:

    h = hashlib.sha256()

    with path.open("rb") as f:
        for block in iter(
            lambda: f.read(1024 * 1024),
            b"",
        ):
            h.update(block)

    return h.hexdigest()


for path, expected in EXPECTED_SHA.items():

    actual = sha256(path)

    if actual != expected:
        raise RuntimeError(
            f"SHA mismatch {path}: {actual}"
        )


# =============================================================================
# Upstream BRR authorization
# =============================================================================

text = E3B4C_AUDIT.read_text(
    encoding="utf-8",
)

required_tokens = [
    "E3B4C_BRR_PREFLIGHT=PASS",
    "E3B4C1_EXACT_BRR_ENGINE_CONTRACT_AUTHORIZED=1",
    "BRR_REPLICATE_COUNT=44",
    "ALL_REQUIRED_WEIGHT_HEADERS=PASS",
    "REPLICATE_NUMERATOR_USES_WTREPr=1",
    "REPLICATE_DENOMINATOR_USES_SAME_WTREPr=1",
    "INTEGRATED_UCC_SUM_WITHIN_REPLICATE=1",
    "BRR_VARIANCE_COMPUTED_AFTER_COMPONENT_INTEGRATION=1",
    "OWNER_RENTER_DIFFERENCE_REPLICATE_DIRECT=1",
]

for token in required_tokens:

    if token not in text:
        raise RuntimeError(
            f"missing upstream invariant={token}"
        )


# =============================================================================
# Header invariants
# =============================================================================

headers = pd.read_csv(
    HEADER_AUDIT,
    sep="\t",
    dtype=str,
).fillna("")


header_pass = (
    len(headers) == 9
    and headers["header_gate"].eq("PASS").all()
    and headers["replicate_count"].eq("44").all()
    and headers["finlwt21_present"].eq("1").all()
)


# =============================================================================
# Frozen estimator-family map
# =============================================================================

ucc = pd.read_csv(
    V2_UCC_CONTRACT,
    sep="\t",
    dtype=str,
).fillna("")


primary = ucc[
    ucc["primary_component"].isin(
        ["C_COST", "H_SERVICE"]
    )
]


family_counts = (
    primary[
        "estimator_family"
    ]
    .value_counts()
    .to_dict()
)


family_pass = (
    len(primary) == 534
    and family_counts.get("MTBI", 0) == 316
    and family_counts.get("ITBI", 0) == 3
    and family_counts.get("EXPD", 0) == 215
)


# =============================================================================
# Frozen full-sample outputs exist and have expected structure
# =============================================================================

components = pd.read_csv(
    V2_COMPONENTS,
    sep="\t",
)

comparison = pd.read_csv(
    V2_COMPARISON,
    sep="\t",
)


anchor_pass = (
    len(components) == 4
    and len(comparison) == 2
    and set(
        components["cohort"]
    ) == {
        "AGE25_34_OWNER",
        "AGE25_34_RENTER",
    }
    and set(
        components["component"]
    ) == {
        "C_COST",
        "H_SERVICE",
    }
    and set(
        comparison["component"]
    ) == {
        "C_COST",
        "H_SERVICE",
    }
)


# =============================================================================
# Machine contract
# =============================================================================

contract = json.loads(
    CONTRACT.read_text(
        encoding="utf-8"
    )
)


expected_reps = [
    f"WTREP{i:02d}"
    for i in range(1, 45)
]


replicate_pass = (
    contract[
        "replicate_count"
    ] == 44
    and contract[
        "replicate_weights"
    ] == expected_reps
    and len(
        set(
            contract[
                "replicate_weights"
            ]
        )
    ) == 44
)


cohort_pass = (
    contract["cohorts"]
    == {
        "AGE25_34_OWNER": {
            "age_min": 25,
            "age_max": 34,
            "cutensure": [1, 2, 3],
        },
        "AGE25_34_RENTER": {
            "age_min": 25,
            "age_max": 34,
            "cutensure": [4],
        },
    }
)


estimator_pass = (
    contract[
        "primary_ucc_count"
    ] == 534
    and contract[
        "primary_family_counts"
    ] == {
        "MTBI": 316,
        "ITBI": 3,
        "EXPD": 215,
    }
    and contract[
        "interview"
    ][
        "replicate_denominator_uses_same_replicate_weight"
    ] is True
    and contract[
        "diary"
    ][
        "replicate_denominator_uses_same_replicate_weight"
    ] is True
    and contract[
        "interview"
    ][
        "calendar_scope_applied_to_replicate_denominator"
    ] is True
    and contract[
        "diary"
    ][
        "weekly_to_quarter_multiplier"
    ] == 13.0
    and contract[
        "hierarchy_factor_applied_inside_replicate"
    ] is True
    and contract[
        "component_sum_inside_replicate"
    ] is True
    and contract[
        "source_variance_posthoc_sum_prohibited"
    ] is True
)


variance_pass = (
    contract[
        "brr_variance"
    ]
    == "(1/44)*SUM((THETA_R-THETA)^2)"
    and contract[
        "brr_se"
    ]
    == "SQRT(BRR_VARIANCE)"
    and contract[
        "difference_replication"
    ]
    == "DIRECT_RENTER_MINUS_OWNER"
    and contract[
        "difference_independence_shortcut_prohibited"
    ] is True
    and contract[
        "ratio_replication"
    ]
    == "DIRECT_RENTER_DIV_OWNER"
)


execution_shape_pass = (
    contract[
        "expected_component_replicate_rows"
    ] == 176
    and contract[
        "expected_difference_replicate_rows"
    ] == 88
    and contract[
        "expected_ratio_replicate_rows"
    ] == 88
)


no_outcome_gate_pass = (
    contract[
        "inference_sign_gate"
    ] is False
    and contract[
        "inference_magnitude_gate"
    ] is False
    and contract[
        "inference_significance_gate"
    ] is False
)


overall = all([
    header_pass,
    family_pass,
    anchor_pass,
    replicate_pass,
    cohort_pass,
    estimator_pass,
    variance_pass,
    execution_shape_pass,
    no_outcome_gate_pass,
])


lines = [
    "=" * 100,
    "E3B4C1 — EXACT EXECUTABLE BRR ENGINE CONTRACT",
    "=" * 100,
    "",
    "MICRODATA_DATA_ROWS_PARSED=0",
    "COST_VALUES_READ=0",
    "ITBI_VALUE_VALUES_READ=0",
    "WTREP_VALUES_READ=0",
    "STANDARD_ERRORS_COMPUTED=0",
    "CONFIDENCE_INTERVALS_COMPUTED=0",
    "P_VALUES_COMPUTED=0",
    "",
    "===== UPSTREAM =====",
    "E3B4C_BRR_PREFLIGHT=PASS",
    (
        "FROZEN_BRR_HEADER_CONTRACT=PASS"
        if header_pass
        else
        "FROZEN_BRR_HEADER_CONTRACT=FAIL"
    ),
    "",
    "===== FULL-SAMPLE ANCHOR =====",
    f"FROZEN_COMPONENT_ROWS={len(components)}",
    f"FROZEN_COMPARISON_ROWS={len(comparison)}",
    (
        "FULL_SAMPLE_POINT_ESTIMATE_ANCHOR=PASS"
        if anchor_pass
        else
        "FULL_SAMPLE_POINT_ESTIMATE_ANCHOR=FAIL"
    ),
    "FULL_SAMPLE_RECOMPUTATION_REQUIRED_BEFORE_BRR_INFERENCE=1",
    "FULL_SAMPLE_IDENTITY_ATOL_USD=1e-8",
    "",
    "===== ESTIMATOR MAP =====",
    f"PRIMARY_UCCS={len(primary)}",
    f"PRIMARY_MTBI_UCCS={family_counts.get('MTBI', 0)}",
    f"PRIMARY_ITBI_UCCS={family_counts.get('ITBI', 0)}",
    f"PRIMARY_EXPD_UCCS={family_counts.get('EXPD', 0)}",
    (
        "FROZEN_PRIMARY_ESTIMATOR_MAP=PASS"
        if family_pass
        else
        "FROZEN_PRIMARY_ESTIMATOR_MAP=FAIL"
    ),
    "",
    "===== REPLICATE SET =====",
    "REPLICATE_FIRST=WTREP01",
    "REPLICATE_LAST=WTREP44",
    "REPLICATE_COUNT=44",
    (
        "EXACT_REPLICATE_SET=PASS"
        if replicate_pass
        else
        "EXACT_REPLICATE_SET=FAIL"
    ),
    "",
    "===== EXECUTABLE SEMANTICS =====",
    "REPLICATE_NUMERATOR_AND_DENOMINATOR_WEIGHT_MATCH=REQUIRED",
    "FULL_SAMPLE_DENOMINATOR_REUSE=PROHIBITED",
    "INTERVIEW_MO_SCOPE_INSIDE_REPLICATE=REQUIRED",
    "DIARY_X13_INSIDE_REPLICATE=REQUIRED",
    "HIERARCHY_FACTOR_INSIDE_REPLICATE=REQUIRED",
    "COMPONENT_INTEGRATION_INSIDE_REPLICATE=REQUIRED",
    "SOURCE_VARIANCE_POSTHOC_SUM=PROHIBITED",
    "",
    "===== DIFFERENCE / RATIO =====",
    "OWNER_RENTER_DIFFERENCE_REPLICATE=DIRECT",
    "OWNER_RENTER_DIFFERENCE_INDEPENDENCE_SHORTCUT=PROHIBITED",
    "OWNER_RENTER_RATIO_REPLICATE=DIRECT",
    "",
    "===== BRR =====",
    "BRR_VARIANCE_FORMULA=(1/44)*SUM((THETA_R-THETA)^2)",
    "BRR_SE_FORMULA=SQRT(BRR_VARIANCE)",
    (
        "BRR_VARIANCE_CONTRACT=PASS"
        if variance_pass
        else
        "BRR_VARIANCE_CONTRACT=FAIL"
    ),
    "",
    "===== FIRST EXECUTION SHAPE =====",
    "EXPECTED_COMPONENT_REPLICATE_ROWS=176",
    "EXPECTED_DIFFERENCE_REPLICATE_ROWS=88",
    "EXPECTED_RATIO_REPLICATE_ROWS=88",
    (
        "EXECUTION_SHAPE_CONTRACT=PASS"
        if execution_shape_pass
        else
        "EXECUTION_SHAPE_CONTRACT=FAIL"
    ),
    "",
    "SIGN_GATE=0",
    "MAGNITUDE_GATE=0",
    "SIGNIFICANCE_GATE=0",
    (
        "NO_OUTCOME_BASED_BRR_GATE=PASS"
        if no_outcome_gate_pass
        else
        "NO_OUTCOME_BASED_BRR_GATE=FAIL"
    ),
    "",
    "COHORT_INFERENTIAL_INTERPRETATION_AUTHORIZED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "",
    (
        "E3B4C1_EXACT_BRR_ENGINE_CONTRACT=PASS"
        if overall
        else
        "E3B4C1_EXACT_BRR_ENGINE_CONTRACT=FAIL"
    ),
    (
        "E3B4C2_FIRST_BRR_EXECUTION_AUTHORIZED=1"
        if overall
        else
        "E3B4C2_FIRST_BRR_EXECUTION_AUTHORIZED=0"
    ),
    "",
]


AUDIT_OUT.write_text(
    "\n".join(lines),
    encoding="utf-8",
)


print(
    "\n".join(lines)
)


if not overall:
    raise SystemExit(1)
