from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

READINESS = (
    ROOT
    / "data/results/E4C0_component_coordinate_readiness.tsv"
)

POLICY = (
    ROOT
    / "data/results/E4C0_transformation_invariance_policy.tsv"
)

BLOCKERS = (
    ROOT
    / "data/results/E4C0_coordinate_blocker_register.tsv"
)

CONTRACT = (
    ROOT
    / "data/metadata/E4C1_chi_coordinate_blocker_resolution_contract.json"
)

OUT_CANDIDATES = (
    ROOT
    / "data/results/E4C1_chi_candidate_resolution_registry.tsv"
)

OUT_RULES = (
    ROOT
    / "data/results/E4C1_chi_resolution_selection_rules.tsv"
)

OUT_WORKSTREAMS = (
    ROOT
    / "data/results/E4C1_authorized_blocker_workstreams.tsv"
)

OUT_BOUNDARIES = (
    ROOT
    / "data/results/E4C1_coordinate_boundary_register.tsv"
)

AUDIT = (
    ROOT
    / "data/metadata/E4C1_chi_coordinate_blocker_resolution_preflight_audit.txt"
)


contract = json.loads(
    CONTRACT.read_text(
        encoding="utf-8"
    )
)

readiness = pd.read_csv(
    READINESS,
    sep="\t",
    dtype=str,
)

policy = pd.read_csv(
    POLICY,
    sep="\t",
    dtype=str,
)

blockers = pd.read_csv(
    BLOCKERS,
    sep="\t",
    dtype=str,
)


# =============================================================================
# E4C0 frozen-state checks.
# =============================================================================

if len(readiness) != 5:
    raise RuntimeError(
        f"expected 5 readiness rows, observed={len(readiness)}"
    )

readiness_map = {
    str(row.component):
        str(row.readiness_status)
    for row in readiness.itertuples(
        index=False
    )
}

expected_readiness = {
    "C":
        "BLOCKED_COORDINATE_SEMANTICS",

    "H":
        "BLOCKED_H_ACCESS_UNIMPLEMENTED",

    "K":
        "SEMANTICS_READY_TRANSFORMATION_NOT_FROZEN",

    "D":
        "SEMANTICS_READY_TRANSFORMATION_NOT_FROZEN",

    "I":
        "BLOCKED_MULTI_ESTIMAND_REPRESENTATION",
}

if readiness_map != expected_readiness:
    raise RuntimeError(
        f"E4C0 readiness mismatch={readiness_map}"
    )


if len(blockers) != 5:
    raise RuntimeError(
        f"expected 5 blockers, observed={len(blockers)}"
    )

blocker_map = {
    str(row.component):
        str(row.blocking_issue)
    for row in blockers.itertuples(
        index=False
    )
}

for component in (
    "C",
    "H",
    "I",
):
    if component not in blocker_map:
        raise RuntimeError(
            f"missing required blocker component={component}"
        )


required_policy = {
    (
        "DIMENSIONLESS_BEFORE_CROSS_COMPONENT_GEOMETRY",
        "REQUIRED",
    ),
    (
        "COMMON_HIGHER_IS_BETTER_ORIENTATION",
        "REQUIRED",
    ),
    (
        "OUTCOME_DIRECTION_DEPENDENT_TRANSFORM",
        "PROHIBITED",
    ),
    (
        "SIGNIFICANCE_DEPENDENT_TRANSFORM",
        "PROHIBITED",
    ),
    (
        "GEOMETRY_RESULT_DEPENDENT_TRANSFORM",
        "PROHIBITED",
    ),
    (
        "TRANSFORMATION_PARAMETERS_FROZEN_BEFORE_GEOMETRY",
        "REQUIRED",
    ),
    (
        "IN_SAMPLE_8_CELL_Z_SCORE",
        "PROHIBITED",
    ),
    (
        "PCA_OR_WHITENING_AS_AUTOMATIC_COORDINATE_CONSTRUCTION",
        "PROHIBITED",
    ),
}

observed_policy = {
    (
        str(row.rule),
        str(row.status),
    )
    for row in policy.itertuples(
        index=False
    )
}

missing_policy = (
    required_policy
    - observed_policy
)

if missing_policy:
    raise RuntimeError(
        f"missing frozen E4C0 policy rules={sorted(missing_policy)}"
    )


# =============================================================================
# Candidate resolution registry.
# No candidate is selected.
# =============================================================================

candidate_rows = [
    {
        "component": "C",
        "candidate_id": "C_A",
        "candidate_family": "REFERENCE_BUNDLE_AFFORDABILITY",
        "semantic_target":
            "ABILITY_TO_COMMAND_A_PREDECLARED_CONSUMPTION_BUNDLE",
        "new_data_or_reference_required": "YES",
        "selected": "NO",
    },
    {
        "component": "C",
        "candidate_id": "C_B",
        "candidate_family": "REAL_CONSUMPTION_COMMAND",
        "semantic_target":
            "REAL_QUANTITY_EQUIVALENT_CONSUMPTION_COMMAND",
        "new_data_or_reference_required": "YES",
        "selected": "NO",
    },
    {
        "component": "C",
        "candidate_id": "C_C",
        "candidate_family":
            "EXPENDITURE_BURDEN_WITH_PREDECLARED_RESOURCE_DENOMINATOR",
        "semantic_target":
            "CONSUMPTION_COST_RELATIVE_TO_A_PREDECLARED_RESOURCE_SCALE",
        "new_data_or_reference_required": "YES",
        "selected": "NO",
    },
    {
        "component": "H",
        "candidate_id": "H_A",
        "candidate_family": "HOUSING_COST_BURDEN",
        "semantic_target":
            "HOUSING_ACCESS_THROUGH_SUSTAINABLE_COST_BURDEN",
        "new_data_or_reference_required": "YES",
        "selected": "NO",
    },
    {
        "component": "H",
        "candidate_id": "H_B",
        "candidate_family": "SPACE_OR_CROWDING_ACCESS",
        "semantic_target":
            "ACCESS_TO_ADEQUATE_HOUSING_SPACE",
        "new_data_or_reference_required": "YES",
        "selected": "NO",
    },
    {
        "component": "H",
        "candidate_id": "H_C",
        "candidate_family": "ADEQUACY_SECURITY_OR_STABILITY_ACCESS",
        "semantic_target":
            "ACCESS_TO_ADEQUATE_STABLE_HOUSING",
        "new_data_or_reference_required": "YES",
        "selected": "NO",
    },
    {
        "component": "I",
        "candidate_id": "I_A",
        "candidate_family": "KEEP_AS_TWO_SUBCOORDINATES",
        "semantic_target":
            "PRESERVE_DISTINCT_FYFT_AND_SEARCH_SECURITY_INFORMATION",
        "new_data_or_reference_required": "NO",
        "selected": "NO",
    },
    {
        "component": "I",
        "candidate_id": "I_B",
        "candidate_family": "PREDECLARED_THEORY_WEIGHTED_SCALAR",
        "semantic_target":
            "ONE_EMPLOYMENT_SECURITY_COORDINATE_WITH_EX_ANTE_WEIGHTS",
        "new_data_or_reference_required": "POSSIBLY",
        "selected": "NO",
    },
    {
        "component": "I",
        "candidate_id": "I_C",
        "candidate_family":
            "LATENT_REPRESENTATION_WITH_INDEPENDENT_REFERENCE_FIT",
        "semantic_target":
            "ONE_OR_MORE_EMPIRICAL_EMPLOYMENT_SECURITY_FACTORS",
        "new_data_or_reference_required": "YES",
        "selected": "NO",
    },
]

candidates = pd.DataFrame(
    candidate_rows
)

if len(candidates) != 9:
    raise RuntimeError(
        "candidate registry shape mismatch"
    )

if (
    candidates[
        "selected"
    ]
    != "NO"
).any():
    raise RuntimeError(
        "E4C1 must not select a candidate"
    )

candidate_counts = (
    candidates[
        "component"
    ]
    .value_counts()
    .to_dict()
)

if candidate_counts != {
    "C": 3,
    "H": 3,
    "I": 3,
}:
    raise RuntimeError(
        f"candidate component counts mismatch={candidate_counts}"
    )


# =============================================================================
# Frozen selection rules.
# =============================================================================

rule_rows = [
    (
        "C",
        "C_STATE_EQUALS_NEGATIVE_C_COST",
        "PROHIBITED",
        "Observed expenditure is not monotone in economic power.",
    ),
    (
        "C",
        "REFERENCE_OR_DENOMINATOR_FROZEN_BEFORE_COORDINATE_VALUES",
        "REQUIRED",
        "Any C affordability/command architecture must predeclare its reference object.",
    ),
    (
        "C",
        "OVERLAP_AUDIT_WITH_K_D_I",
        "REQUIRED",
        "A C denominator must not silently duplicate capital, debt, or employment dimensions.",
    ),
    (
        "H",
        "TENURE_AS_H_ACCESS_MEASURE",
        "PROHIBITED",
        "Tenure already defines the owner/renter cohort split.",
    ),
    (
        "H",
        "H_FULL_STATE_EQUALS_H_SERVICE_ONLY",
        "PROHIBITED",
        "Housing-service spending is not the complete access state.",
    ),
    (
        "H",
        "SAME_YEAR_NON_TAUTOLOGICAL_ACCESS_MEASURE",
        "REQUIRED",
        "Primary H_ACCESS should be calendar-compatible and not mechanically encode tenure.",
    ),
    (
        "I",
        "UNJUSTIFIED_EQUAL_WEIGHT_SCALAR",
        "PROHIBITED",
        "Two estimands do not imply 50/50 weights.",
    ),
    (
        "I",
        "INDEPENDENT_REFERENCE_REQUIRED_FOR_LATENT_FIT",
        "REQUIRED_IF_LATENT",
        "Do not fit and assess a latent I representation on the same eight geometry cells.",
    ),
    (
        "I",
        "COORDINATE_COUNT_IMPLICATION_EXPLICIT",
        "REQUIRED",
        "Keeping two I subcoordinates means the system need not have five coordinates.",
    ),
    (
        "ALL",
        "OWNER_RENTER_DIRECTION_AS_SELECTION_CRITERION",
        "PROHIBITED",
        "Observed direction cannot select semantic architecture.",
    ),
    (
        "ALL",
        "SIGNIFICANCE_AS_SELECTION_CRITERION",
        "PROHIBITED",
        "Confidence intervals cannot select semantic architecture.",
    ),
    (
        "ALL",
        "GEOMETRY_OR_DIMENSIONALITY_RESULT_AS_SELECTION_CRITERION",
        "PROHIBITED",
        "Architecture must be frozen before geometry.",
    ),
]

rules = pd.DataFrame(
    rule_rows,
    columns=[
        "scope",
        "rule",
        "status",
        "interpretation",
    ],
)

if len(rules) != 12:
    raise RuntimeError(
        "selection-rule shape mismatch"
    )


# =============================================================================
# Independent next workstreams.
# =============================================================================

workstream_rows = [
    {
        "workstream": "E4C2",
        "component": "C",
        "name": "C_COORDINATE_ARCHITECTURE_PREFLIGHT",
        "authorized": "YES",
        "may_open_coordinate_values": "NO",
        "purpose":
            "Freeze C semantic target, reference object, denominator policy, and source lineage requirements.",
    },
    {
        "workstream": "E4C3",
        "component": "H",
        "name": "H_ACCESS_SOURCE_ESTIMAND_RECON_PREFLIGHT",
        "authorized": "YES",
        "may_open_coordinate_values": "NO",
        "purpose":
            "Recon official same-year non-tautological H_ACCESS source and estimand candidates.",
    },
    {
        "workstream": "E4C4",
        "component": "I",
        "name": "I_REPRESENTATION_ARCHITECTURE_PREFLIGHT",
        "authorized": "YES",
        "may_open_coordinate_values": "NO",
        "purpose":
            "Freeze whether I remains multi-coordinate or what ex-ante evidence is required for reduction.",
    },
]

workstreams = pd.DataFrame(
    workstream_rows
)

if len(workstreams) != 3:
    raise RuntimeError(
        "workstream shape mismatch"
    )

if not (
    workstreams[
        "authorized"
    ]
    == "YES"
).all():
    raise RuntimeError(
        "all three independent blocker workstreams must be authorized"
    )

if not (
    workstreams[
        "may_open_coordinate_values"
    ]
    == "NO"
).all():
    raise RuntimeError(
        "E4C1 workstreams must remain pre-value"
    )


# =============================================================================
# Boundary register.
# =============================================================================

boundary_rows = [
    (
        "C_COORDINATE_SELECTED",
        "NO",
    ),
    (
        "H_ACCESS_ESTIMAND_SELECTED",
        "NO",
    ),
    (
        "I_REPRESENTATION_SELECTED",
        "NO",
    ),
    (
        "I_SCALAR_AUTHORIZED",
        "NO",
    ),
    (
        "K_D_TRANSFORM_SELECTION_AUTHORIZED",
        "NO",
    ),
    (
        "FIVE_COORDINATES_FROZEN",
        "NO",
    ),
    (
        "FIVE_COMPONENT_STATE_VECTOR_AUTHORIZED",
        "NO",
    ),
    (
        "FIVE_COMPONENT_NORMALIZATION_AUTHORIZED",
        "NO",
    ),
    (
        "DIMENSIONALITY_TEST_AUTHORIZED",
        "NO",
    ),
    (
        "FIVE_DIMENSIONALITY_PROVEN",
        "NO",
    ),
    (
        "REAL_INFLATION_ESTIMATION_AUTHORIZED",
        "NO",
    ),
    (
        "FINAL_SCALAR_AUTHORIZED",
        "NO",
    ),
]

boundaries = pd.DataFrame(
    boundary_rows,
    columns=[
        "boundary",
        "status",
    ],
)

if len(boundaries) != 12:
    raise RuntimeError(
        "boundary-register shape mismatch"
    )


# =============================================================================
# Serialize static outputs.
# =============================================================================

OUT_CANDIDATES.parent.mkdir(
    parents=True,
    exist_ok=True,
)

candidates.to_csv(
    OUT_CANDIDATES,
    sep="\t",
    index=False,
    lineterminator="\n",
)

rules.to_csv(
    OUT_RULES,
    sep="\t",
    index=False,
    lineterminator="\n",
)

workstreams.to_csv(
    OUT_WORKSTREAMS,
    sep="\t",
    index=False,
    lineterminator="\n",
)

boundaries.to_csv(
    OUT_BOUNDARIES,
    sep="\t",
    index=False,
    lineterminator="\n",
)


# =============================================================================
# Audit.
# =============================================================================

audit_lines = [
    "=" * 100,
    "E4C1 — C-H-I COORDINATE BLOCKER RESOLUTION PREFLIGHT",
    "=" * 100,
    "",
    "RAW_SURVEY_DATA_READ=0",
    "NEW_ECONOMIC_VALUES_OPENED=0",
    "NEW_SOURCE_VALUES_OPENED=0",
    "SURVEY_REESTIMATION_PERFORMED=0",
    "REPLICATE_RECALCULATION_PERFORMED=0",
    "COORDINATE_VALUES_COMPUTED=0",
    "TRANSFORMED_VALUES_COMPUTED=0",
    "GEOMETRY_PERFORMED=0",
    "",
    "===== C BLOCKER =====",
    "C_EXISTING_MEASURE=C_COST",
    "C_EXISTING_ROLE=OBSERVED_ANNUAL_CONSUMPTION_EXPENDITURE_FLOW_EVIDENCE",
    "C_STATE_EQUALS_NEGATIVE_C_COST_AUTHORIZED=0",
    "C_CANDIDATE_ARCHITECTURE_COUNT=3",
    "C_COORDINATE_SELECTED=0",
    "",
    "===== H BLOCKER =====",
    "H_EXISTING_MEASURE=H_SERVICE",
    "H_SERVICE_IMPLEMENTED=1",
    "H_ACCESS_IMPLEMENTED=0",
    "TENURE_AS_H_ACCESS_MEASURE_AUTHORIZED=0",
    "H_FULL_STATE_EQUALS_H_SERVICE_ONLY_AUTHORIZED=0",
    "H_ACCESS_CANDIDATE_FAMILY_COUNT=3",
    "H_ACCESS_ESTIMAND_SELECTED=0",
    "",
    "===== I BLOCKER =====",
    "I_PRIMARY_ESTIMAND_COUNT=2",
    "I_PER_ESTIMAND_ORIENTATION_FROZEN=1",
    "I_UNJUSTIFIED_EQUAL_WEIGHT_SCALAR_AUTHORIZED=0",
    "I_REPRESENTATION_CANDIDATE_COUNT=3",
    "I_REPRESENTATION_SELECTED=0",
    "I_SCALAR_AUTHORIZED=0",
    "",
    "===== ANTI-CIRCULAR SELECTION RULES =====",
    "OWNER_RENTER_DIRECTION_AS_SELECTION_CRITERION=PROHIBITED",
    "SIGNIFICANCE_AS_SELECTION_CRITERION=PROHIBITED",
    "GEOMETRY_OR_DIMENSIONALITY_RESULT_AS_SELECTION_CRITERION=PROHIBITED",
    "E4C1_SELECTION_RULE_COUNT=12",
    "E4C1_SELECTION_RULE_SHAPE=PASS",
    "",
    "===== COORDINATE COUNT =====",
    "FIVE_COORDINATES_FROZEN=0",
    "H_MAY_REQUIRE_MORE_THAN_ONE_SUBSTRUCTURE=1",
    "I_MAY_REMAIN_TWO_SUBCOORDINATES=1",
    "FIVE_DIMENSIONALITY_PROVEN=0",
    "",
    "===== K-D HOLD =====",
    "K_STATE_SEMANTICS_FROZEN=1",
    "D_STATE_SEMANTICS_FROZEN=1",
    "K_D_TRANSFORM_SELECTION_AUTHORIZED=0",
    "",
    "===== INDEPENDENT NEXT WORKSTREAMS =====",
    "E4C2_C_COORDINATE_ARCHITECTURE_PREFLIGHT_AUTHORIZED=1",
    "E4C3_H_ACCESS_SOURCE_ESTIMAND_RECON_PREFLIGHT_AUTHORIZED=1",
    "E4C4_I_REPRESENTATION_ARCHITECTURE_PREFLIGHT_AUTHORIZED=1",
    "E4C1_AUTHORIZED_WORKSTREAM_COUNT=3",
    "E4C1_WORKSTREAM_SHAPE=PASS",
    "",
    "===== HARD BOUNDARY =====",
    "FIVE_COMPONENT_STATE_VECTOR_AUTHORIZED=0",
    "FIVE_COMPONENT_NORMALIZATION_AUTHORIZED=0",
    "DIMENSIONALITY_TEST_AUTHORIZED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "",
    "E4C1_C_H_I_COORDINATE_BLOCKER_RESOLUTION_PREFLIGHT=PASS",
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
