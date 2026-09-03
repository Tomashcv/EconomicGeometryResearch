from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

SUMMARY = (
    ROOT
    / "data/results/E4B3_five_component_evidence_coverage_summary.tsv"
)

CONSTRAINTS = (
    ROOT
    / "data/results/E4B3_coordinate_readiness_constraints.tsv"
)

COVERAGE = (
    ROOT
    / "data/results/E4B3_2022_five_component_evidence_coverage.tsv"
)

CONTRACT = (
    ROOT
    / "data/metadata/E4C0_component_coordinate_semantics_transformation_contract.json"
)

OUT_READINESS = (
    ROOT
    / "data/results/E4C0_component_coordinate_readiness.tsv"
)

OUT_POLICY = (
    ROOT
    / "data/results/E4C0_transformation_invariance_policy.tsv"
)

OUT_BLOCKERS = (
    ROOT
    / "data/results/E4C0_coordinate_blocker_register.tsv"
)

AUDIT = (
    ROOT
    / "data/metadata/E4C0_component_coordinate_semantics_transformation_preflight_audit.txt"
)


contract = json.loads(
    CONTRACT.read_text(
        encoding="utf-8"
    )
)

summary = pd.read_csv(
    SUMMARY,
    sep="\t",
    dtype=str,
)

constraints = pd.read_csv(
    CONSTRAINTS,
    sep="\t",
    dtype=str,
)

coverage = pd.read_csv(
    COVERAGE,
    sep="\t",
    dtype=str,
)


# =============================================================================
# Frozen input shape checks.
# =============================================================================

if len(summary) != 5:
    raise RuntimeError(
        f"expected 5 component summary rows, observed={len(summary)}"
    )

if set(summary["component"]) != {
    "C",
    "H",
    "K",
    "D",
    "I",
}:
    raise RuntimeError(
        "unexpected E4B3 component set"
    )

if not (
    pd.to_numeric(
        summary["covered_cells_of_8"],
        errors="raise",
    )
    == 8
).all():
    raise RuntimeError(
        "not every component has 8/8 frozen evidence coverage"
    )

if len(coverage) != 8:
    raise RuntimeError(
        f"expected 8 common coverage cells, observed={len(coverage)}"
    )

if not (
    coverage[
        "five_component_evidence_coverage"
    ]
    == "YES"
).all():
    raise RuntimeError(
        "E4B3 full evidence coverage is not complete"
    )


constraint_map = dict(
    zip(
        constraints["constraint"],
        constraints["status"],
        strict=True,
    )
)

required_constraints = {
    "FULL_8_CELL_FIVE_COMPONENT_EVIDENCE_COVERAGE":
        "YES",

    "MICRO_OBSERVATIONAL_UNIT_IDENTICAL":
        "NO",

    "PERSON_LEVEL_CROSS_SURVEY_JOIN_AUTHORIZED":
        "NO",

    "CROSS_SURVEY_JOINT_COVARIANCE_AVAILABLE":
        "NO",

    "PSEUDO_COHORT_INTEGRATION_ONLY":
        "YES",

    "RAW_C_H_K_D_I_UNITS_COMMENSURABLE":
        "NO",

    "C_COORDINATE_SEMANTICS_FROZEN":
        "NO",

    "H_ACCESS_IMPLEMENTED":
        "NO",

    "H_SERVICE_EQUALS_FULL_H_DIMENSION":
        "NO",

    "I_SCALAR_AUTHORIZED":
        "NO",

    "FIVE_COMPONENT_STATE_VECTOR_AUTHORIZED":
        "NO",

    "FIVE_COMPONENT_NORMALIZATION_AUTHORIZED":
        "NO",

    "DIMENSIONALITY_TEST_AUTHORIZED":
        "NO",

    "REAL_INFLATION_ESTIMATION_AUTHORIZED":
        "NO",

    "FINAL_SCALAR_AUTHORIZED":
        "NO",
}

for key, expected in required_constraints.items():

    observed = constraint_map.get(
        key
    )

    if observed != expected:
        raise RuntimeError(
            f"E4B3 constraint mismatch {key}: "
            f"expected={expected} observed={observed}"
        )


# =============================================================================
# Precommitted coordinate-readiness classification.
# No economic outcome values are used.
# =============================================================================

readiness_rows = [
    {
        "component": "C",
        "evidence_coverage_cells": 8,
        "primary_measure": "C_COST",
        "state_orientation_frozen": "NO",
        "scalar_coordinate_frozen": "NO",
        "dimensionless_transform_frozen": "NO",
        "readiness_status": "BLOCKED_COORDINATE_SEMANTICS",
    },
    {
        "component": "H",
        "evidence_coverage_cells": 8,
        "primary_measure": "H_SERVICE",
        "state_orientation_frozen": "NO",
        "scalar_coordinate_frozen": "NO",
        "dimensionless_transform_frozen": "NO",
        "readiness_status": "BLOCKED_H_ACCESS_UNIMPLEMENTED",
    },
    {
        "component": "K",
        "evidence_coverage_cells": 8,
        "primary_measure": "K_FIN_MEAN",
        "state_orientation_frozen": "YES",
        "scalar_coordinate_frozen": "NO",
        "dimensionless_transform_frozen": "NO",
        "readiness_status": "SEMANTICS_READY_TRANSFORMATION_NOT_FROZEN",
    },
    {
        "component": "D",
        "evidence_coverage_cells": 8,
        "primary_measure": "D_PIRTOTAL_MEAN",
        "state_orientation_frozen": "YES",
        "scalar_coordinate_frozen": "NO",
        "dimensionless_transform_frozen": "NO",
        "readiness_status": "SEMANTICS_READY_TRANSFORMATION_NOT_FROZEN",
    },
    {
        "component": "I",
        "evidence_coverage_cells": 8,
        "primary_measure": "I_FYFT_SHARE+I_SEARCH_BURDEN_SHARE",
        "state_orientation_frozen": "YES_PER_ESTIMAND",
        "scalar_coordinate_frozen": "NO",
        "dimensionless_transform_frozen": "NO",
        "readiness_status": "BLOCKED_MULTI_ESTIMAND_REPRESENTATION",
    },
]

readiness = pd.DataFrame(
    readiness_rows
)


# =============================================================================
# Frozen transformation invariance policy.
# =============================================================================

policy_rows = [
    (
        "DIMENSIONLESS_BEFORE_CROSS_COMPONENT_GEOMETRY",
        "REQUIRED",
        "Every coordinate entering cross-component geometry must be dimensionless.",
    ),
    (
        "COMMON_HIGHER_IS_BETTER_ORIENTATION",
        "REQUIRED",
        "State orientation must be explicit before geometry.",
    ),
    (
        "SAME_COMPONENT_FORMULA_ACROSS_COHORTS",
        "REQUIRED",
        "A component transform cannot depend on age/tenure cell identity.",
    ),
    (
        "TENURE_SPECIFIC_SCALING",
        "PROHIBITED",
        "Owner and renter coordinates cannot use different scales.",
    ),
    (
        "COHORT_SPECIFIC_SCALING",
        "PROHIBITED",
        "No cell-specific normalization is allowed.",
    ),
    (
        "OUTCOME_DIRECTION_DEPENDENT_TRANSFORM",
        "PROHIBITED",
        "Transformation choice cannot depend on observed owner-renter direction.",
    ),
    (
        "SIGNIFICANCE_DEPENDENT_TRANSFORM",
        "PROHIBITED",
        "Transformation choice cannot depend on confidence intervals or significance.",
    ),
    (
        "GEOMETRY_RESULT_DEPENDENT_TRANSFORM",
        "PROHIBITED",
        "Transformation cannot be selected after inspecting geometric results.",
    ),
    (
        "TRANSFORMATION_PARAMETERS_FROZEN_BEFORE_GEOMETRY",
        "REQUIRED",
        "All anchors and scales must be frozen before transformed geometry values are opened.",
    ),
    (
        "UNIT_CHANGE_INVARIANCE",
        "REQUIRED",
        "Changing reporting units must not change substantive geometry conclusions.",
    ),
    (
        "MONOTONICITY_WHERE_STATE_ORDER_DEFINED",
        "REQUIRED",
        "Transforms must preserve frozen state ordering unless separately justified in advance.",
    ),
    (
        "IN_SAMPLE_8_CELL_Z_SCORE",
        "PROHIBITED",
        "Do not use the same eight cells to define coordinate scale and then analyze their geometry.",
    ),
    (
        "IN_SAMPLE_8_CELL_MIN_MAX",
        "PROHIBITED",
        "Do not derive endpoints from the same eight cells used for geometry.",
    ),
    (
        "RANK_TRANSFORM_OVER_8_CELLS",
        "PROHIBITED",
        "Ranks discard magnitude and make geometry sample-composition dependent.",
    ),
    (
        "PCA_OR_WHITENING_AS_AUTOMATIC_COORDINATE_CONSTRUCTION",
        "PROHIBITED",
        "No automatic latent geometry before semantic coordinates and valid covariance structure are frozen.",
    ),
]

policy = pd.DataFrame(
    policy_rows,
    columns=[
        "rule",
        "status",
        "interpretation",
    ],
)


# =============================================================================
# Blocker register.
# =============================================================================

blocker_rows = [
    {
        "blocker_id": "C1",
        "component": "C",
        "blocking_issue": "OBSERVED_EXPENDITURE_IS_NOT_AUTOMATICALLY_A_PURCHASING_POWER_STATE",
        "must_resolve_before_five_component_vector": "YES",
        "next_preflight": "E4C1",
    },
    {
        "blocker_id": "H1",
        "component": "H",
        "blocking_issue": "H_ACCESS_UNIMPLEMENTED_AND_H_SERVICE_NOT_FULL_H",
        "must_resolve_before_five_component_vector": "YES",
        "next_preflight": "E4C1",
    },
    {
        "blocker_id": "I1",
        "component": "I",
        "blocking_issue": "TWO_PRIMARY_ESTIMANDS_WITH_NO_FROZEN_SCALAR_OR_LATENT_REPRESENTATION",
        "must_resolve_before_five_component_vector": "YES",
        "next_preflight": "E4C1",
    },
    {
        "blocker_id": "K1",
        "component": "K",
        "blocking_issue": "DIMENSIONLESS_TRANSFORM_NOT_FROZEN",
        "must_resolve_before_five_component_vector": "YES",
        "next_preflight": "POST_E4C1_TRANSFORMATION_CONTRACT",
    },
    {
        "blocker_id": "D1",
        "component": "D",
        "blocking_issue": "GEOMETRY_METRIC_SCALE_NOT_FROZEN",
        "must_resolve_before_five_component_vector": "YES",
        "next_preflight": "POST_E4C1_TRANSFORMATION_CONTRACT",
    },
]

blockers = pd.DataFrame(
    blocker_rows
)


# =============================================================================
# Exact output shapes.
# =============================================================================

if len(readiness) != 5:
    raise RuntimeError(
        "readiness shape mismatch"
    )

if len(policy) != 15:
    raise RuntimeError(
        "policy shape mismatch"
    )

if len(blockers) != 5:
    raise RuntimeError(
        "blocker shape mismatch"
    )

if int(
    (
        blockers[
            "must_resolve_before_five_component_vector"
        ]
        == "YES"
    ).sum()
) != 5:
    raise RuntimeError(
        "all five component paths must remain blocked before vector authorization"
    )


# =============================================================================
# Serialize static preflight outputs.
# =============================================================================

OUT_READINESS.parent.mkdir(
    parents=True,
    exist_ok=True,
)

readiness.to_csv(
    OUT_READINESS,
    sep="\t",
    index=False,
    lineterminator="\n",
)

policy.to_csv(
    OUT_POLICY,
    sep="\t",
    index=False,
    lineterminator="\n",
)

blockers.to_csv(
    OUT_BLOCKERS,
    sep="\t",
    index=False,
    lineterminator="\n",
)


# =============================================================================
# Audit.
# =============================================================================

audit_lines = [
    "=" * 100,
    "E4C0 — COMPONENT COORDINATE SEMANTICS + TRANSFORMATION PREFLIGHT",
    "=" * 100,
    "",
    "RAW_SURVEY_DATA_READ=0",
    "NEW_ECONOMIC_VALUES_OPENED=0",
    "SURVEY_REESTIMATION_PERFORMED=0",
    "REPLICATE_RECALCULATION_PERFORMED=0",
    "TRANSFORMED_VALUES_COMPUTED=0",
    "FROZEN_RESULT_TABLES_ONLY=1",
    "",
    "===== COMPLETE EVIDENCE COVERAGE =====",
    "C_EVIDENCE_COVERAGE=8_OF_8",
    "H_EVIDENCE_COVERAGE=8_OF_8",
    "K_EVIDENCE_COVERAGE=8_OF_8",
    "D_EVIDENCE_COVERAGE=8_OF_8",
    "I_EVIDENCE_COVERAGE=8_OF_8",
    "FULL_FIVE_COMPONENT_EVIDENCE_COVERAGE=PASS",
    "",
    "===== COORDINATE READINESS =====",
    "C_COORDINATE_STATUS=BLOCKED_COORDINATE_SEMANTICS",
    "C_STATE_ORIENTATION_FROZEN=0",
    "H_COORDINATE_STATUS=BLOCKED_H_ACCESS_UNIMPLEMENTED",
    "H_SERVICE_IMPLEMENTED=1",
    "H_ACCESS_IMPLEMENTED=0",
    "H_SERVICE_EQUALS_FULL_H_DIMENSION=0",
    "K_COORDINATE_STATUS=SEMANTICS_READY_TRANSFORMATION_NOT_FROZEN",
    "K_STATE_ORIENTATION_FROZEN=1",
    "D_COORDINATE_STATUS=SEMANTICS_READY_TRANSFORMATION_NOT_FROZEN",
    "D_STATE_ORIENTATION_FROZEN=1",
    "I_COORDINATE_STATUS=BLOCKED_MULTI_ESTIMAND_REPRESENTATION",
    "I_PRIMARY_ESTIMAND_COUNT=2",
    "I_PER_ESTIMAND_ORIENTATION_FROZEN=1",
    "I_SCALAR_AUTHORIZED=0",
    "",
    "===== TRANSFORMATION POLICY =====",
    "DIMENSIONLESS_BEFORE_CROSS_COMPONENT_GEOMETRY=REQUIRED",
    "COMMON_HIGHER_IS_BETTER_ORIENTATION=REQUIRED",
    "SAME_COMPONENT_FORMULA_ACROSS_COHORTS=REQUIRED",
    "TENURE_SPECIFIC_SCALING=PROHIBITED",
    "COHORT_SPECIFIC_SCALING=PROHIBITED",
    "OUTCOME_DIRECTION_DEPENDENT_TRANSFORM=PROHIBITED",
    "SIGNIFICANCE_DEPENDENT_TRANSFORM=PROHIBITED",
    "GEOMETRY_RESULT_DEPENDENT_TRANSFORM=PROHIBITED",
    "TRANSFORMATION_PARAMETERS_FROZEN_BEFORE_GEOMETRY=REQUIRED",
    "UNIT_CHANGE_INVARIANCE=REQUIRED",
    "MONOTONICITY_WHERE_STATE_ORDER_DEFINED=REQUIRED",
    "IN_SAMPLE_8_CELL_Z_SCORE=PROHIBITED",
    "IN_SAMPLE_8_CELL_MIN_MAX=PROHIBITED",
    "RANK_TRANSFORM_OVER_8_CELLS=PROHIBITED",
    "PCA_OR_WHITENING_AS_AUTOMATIC_COORDINATE_CONSTRUCTION=PROHIBITED",
    "E4C0_TRANSFORMATION_POLICY_SHAPE=PASS",
    "",
    "===== COORDINATE COUNT =====",
    "FIVE_COORDINATES_FROZEN=0",
    "I_MAY_REQUIRE_MORE_THAN_ONE_COORDINATE=1",
    "H_MAY_REQUIRE_ACCESS_SUBSTRUCTURE=1",
    "FIVE_DIMENSIONALITY_PROVEN=0",
    "",
    "===== HARD BOUNDARY =====",
    "FIVE_COMPONENT_STATE_VECTOR_AUTHORIZED=0",
    "FIVE_COMPONENT_NORMALIZATION_AUTHORIZED=0",
    "RAW_EUCLIDEAN_DISTANCE_AUTHORIZED=0",
    "DIMENSIONALITY_TEST_AUTHORIZED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "",
    "E4C0_COMPONENT_COORDINATE_SEMANTICS_AND_TRANSFORMATION_PREFLIGHT=PASS",
    "E4C1_C_H_I_COORDINATE_BLOCKER_RESOLUTION_PREFLIGHT_AUTHORIZED=1",
]

audit_text = (
    "\n".join(
        audit_lines
    )
    + "\n"
)

AUDIT.write_text(
    audit_text,
    encoding="utf-8",
)

sys.stdout.write(
    audit_text
)
