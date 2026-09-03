from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

CANDIDATES = (
    ROOT
    / "data/results/E4C1_chi_candidate_resolution_registry.tsv"
)

RULES = (
    ROOT
    / "data/results/E4C1_chi_resolution_selection_rules.tsv"
)

WORKSTREAMS = (
    ROOT
    / "data/results/E4C1_authorized_blocker_workstreams.tsv"
)

CONTRACT = (
    ROOT
    / "data/metadata/E4C2_c_coordinate_architecture_contract.json"
)

OUT_MATRIX = (
    ROOT
    / "data/results/E4C2_c_architecture_evaluation_matrix.tsv"
)

OUT_CRITERIA = (
    ROOT
    / "data/results/E4C2_c_architecture_selection_criteria.tsv"
)

OUT_RECON = (
    ROOT
    / "data/results/E4C2_c_required_source_recon_register.tsv"
)

AUDIT = (
    ROOT
    / "data/metadata/E4C2_c_coordinate_architecture_preflight_audit.txt"
)


contract = json.loads(
    CONTRACT.read_text(
        encoding="utf-8"
    )
)

candidates = pd.read_csv(
    CANDIDATES,
    sep="\t",
    dtype=str,
)

rules = pd.read_csv(
    RULES,
    sep="\t",
    dtype=str,
)

workstreams = pd.read_csv(
    WORKSTREAMS,
    sep="\t",
    dtype=str,
)


# =============================================================================
# E4C1 authorization state.
# =============================================================================

c_rows = candidates[
    candidates[
        "component"
    ]
    == "C"
].copy()

if len(c_rows) != 3:
    raise RuntimeError(
        f"expected 3 C candidates, observed={len(c_rows)}"
    )

expected_families = {
    "REFERENCE_BUNDLE_AFFORDABILITY",
    "REAL_CONSUMPTION_COMMAND",
    "EXPENDITURE_BURDEN_WITH_PREDECLARED_RESOURCE_DENOMINATOR",
}

if set(
    c_rows[
        "candidate_family"
    ]
) != expected_families:
    raise RuntimeError(
        "unexpected frozen C candidate family set"
    )

if (
    c_rows[
        "selected"
    ]
    != "NO"
).any():
    raise RuntimeError(
        "E4C1 unexpectedly selected a C architecture"
    )


ws = workstreams[
    workstreams[
        "workstream"
    ]
    == "E4C2"
]

if len(ws) != 1:
    raise RuntimeError(
        "missing unique E4C2 workstream authorization"
    )

if str(
    ws.iloc[
        0
    ][
        "authorized"
    ]
) != "YES":
    raise RuntimeError(
        "E4C2 workstream not authorized"
    )

if str(
    ws.iloc[
        0
    ][
        "may_open_coordinate_values"
    ]
) != "NO":
    raise RuntimeError(
        "E4C2 must remain pre-coordinate-value"
    )


required_rules = {
    (
        "C",
        "C_STATE_EQUALS_NEGATIVE_C_COST",
        "PROHIBITED",
    ),
    (
        "C",
        "REFERENCE_OR_DENOMINATOR_FROZEN_BEFORE_COORDINATE_VALUES",
        "REQUIRED",
    ),
    (
        "C",
        "OVERLAP_AUDIT_WITH_K_D_I",
        "REQUIRED",
    ),
    (
        "ALL",
        "OWNER_RENTER_DIRECTION_AS_SELECTION_CRITERION",
        "PROHIBITED",
    ),
    (
        "ALL",
        "SIGNIFICANCE_AS_SELECTION_CRITERION",
        "PROHIBITED",
    ),
    (
        "ALL",
        "GEOMETRY_OR_DIMENSIONALITY_RESULT_AS_SELECTION_CRITERION",
        "PROHIBITED",
    ),
}

observed_rules = {
    (
        str(row.scope),
        str(row.rule),
        str(row.status),
    )
    for row in rules.itertuples(
        index=False
    )
}

missing = (
    required_rules
    - observed_rules
)

if missing:
    raise RuntimeError(
        f"missing E4C1 C selection rules={sorted(missing)}"
    )


# =============================================================================
# Architecture evaluation matrix — static, no numeric outcomes.
# =============================================================================

matrix_rows = [
    {
        "candidate_id": "C_A",
        "candidate_family": "REFERENCE_BUNDLE_AFFORDABILITY",
        "semantic_monotonicity": "PLAUSIBLE_PENDING_REFERENCE_DEFINITION",
        "same_year_cross_sectional_identifiability":
            "UNRESOLVED_REQUIRES_COHORT_REFERENCE_OR_VALID_NUMERAIRE",
        "longitudinal_extensibility": "PLAUSIBLE",
        "unit_invariance": "PLAUSIBLE_IF_RATIO_OR_LOG_INDEX",
        "distinctness_from_K_D_I": "HIGH_IF_NO_RESOURCE_DENOMINATOR",
        "source_feasibility": "RECON_REQUIRED",
        "status": "VIABLE_RECON_PENDING",
        "selected": "NO",
    },
    {
        "candidate_id": "C_B",
        "candidate_family": "REAL_CONSUMPTION_COMMAND",
        "semantic_monotonicity": "PLAUSIBLE_HIGHER_REAL_COMMAND_IS_BETTER",
        "same_year_cross_sectional_identifiability":
            "PLAUSIBLE_IF_REAL_QUANTITY_EQUIVALENT_ESTIMATOR_EXISTS",
        "longitudinal_extensibility": "PLAUSIBLE",
        "unit_invariance": "PLAUSIBLE_IF_REFERENCE_NORMALIZED",
        "distinctness_from_K_D_I":
            "HIGH_IF_NO_RESOURCE_DENOMINATOR",
        "source_feasibility": "RECON_REQUIRED",
        "status": "VIABLE_RECON_PENDING",
        "selected": "NO",
    },
    {
        "candidate_id": "C_C",
        "candidate_family":
            "EXPENDITURE_BURDEN_WITH_PREDECLARED_RESOURCE_DENOMINATOR",
        "semantic_monotonicity":
            "PLAUSIBLE_LOWER_BURDEN_IS_BETTER_AFTER_SIGN_ORIENTATION",
        "same_year_cross_sectional_identifiability": "PLAUSIBLE",
        "longitudinal_extensibility": "PLAUSIBLE",
        "unit_invariance": "STRONG_IF_RATIO",
        "distinctness_from_K_D_I":
            "UNRESOLVED_HIGH_OVERLAP_RISK",
        "source_feasibility": "RECON_REQUIRED",
        "status": "CONDITIONAL_RECON_PENDING_OVERLAP_AUDIT",
        "selected": "NO",
    },
]

matrix = pd.DataFrame(
    matrix_rows
)

if len(matrix) != 3:
    raise RuntimeError(
        "C architecture matrix shape mismatch"
    )

if (
    matrix[
        "selected"
    ]
    != "NO"
).any():
    raise RuntimeError(
        "E4C2 must not select a C architecture"
    )


criteria_rows = [
    (
        "MONOTONE_ECONOMIC_STATE_INTERPRETATION",
        "REQUIRED",
    ),
    (
        "SAME_YEAR_CROSS_SECTIONAL_IDENTIFIABILITY",
        "REQUIRED",
    ),
    (
        "LONGITUDINAL_EXTENSIBILITY",
        "REQUIRED",
    ),
    (
        "UNIT_INVARIANCE",
        "REQUIRED",
    ),
    (
        "NON_CIRCULARITY_WITH_8_GEOMETRY_CELLS",
        "REQUIRED",
    ),
    (
        "DISTINCTNESS_FROM_K_D_I",
        "REQUIRED",
    ),
    (
        "OFFICIAL_PUBLIC_SOURCE_FEASIBILITY",
        "REQUIRED",
    ),
    (
        "REFERENCE_OBJECT_FROZEN_BEFORE_VALUES",
        "REQUIRED",
    ),
    (
        "OWNER_RENTER_DIRECTION_GATE",
        "PROHIBITED",
    ),
    (
        "SIGNIFICANCE_GATE",
        "PROHIBITED",
    ),
    (
        "GEOMETRY_RESULT_GATE",
        "PROHIBITED",
    ),
    (
        "EXISTING_C_COST_ORDERING_GATE",
        "PROHIBITED",
    ),
]

criteria = pd.DataFrame(
    criteria_rows,
    columns=[
        "criterion",
        "status",
    ],
)

if len(criteria) != 12:
    raise RuntimeError(
        "C criteria shape mismatch"
    )


recon_rows = [
    {
        "recon_item": "PRICE_SOURCE",
        "required": "YES",
        "purpose":
            "Identify official/public prices or indexes capable of supporting C_A or C_B.",
    },
    {
        "recon_item": "REFERENCE_BUNDLE_OR_QUANTITY_STRUCTURE",
        "required": "YES",
        "purpose":
            "Determine whether a predeclared consumption bundle or quantity-equivalent structure is feasible.",
    },
    {
        "recon_item": "EQUIVALENCE_SCALE_POLICY",
        "required": "YES",
        "purpose":
            "Determine whether household-size/composition adjustment is required and how it can be frozen.",
    },
    {
        "recon_item": "RESOURCE_DENOMINATOR_OPTIONS",
        "required": "YES_FOR_C_C",
        "purpose":
            "Identify possible denominator sources without silently selecting one.",
    },
    {
        "recon_item": "K_D_I_OVERLAP_AUDIT",
        "required": "YES",
        "purpose":
            "Reject architectures that mechanically duplicate capital, debt, or employment-security information.",
    },
    {
        "recon_item": "SAME_YEAR_CROSS_SECTIONAL_IDENTIFICATION",
        "required": "YES",
        "purpose":
            "Prove the architecture can vary meaningfully across the eight 2022 pseudo-cohort cells.",
    },
    {
        "recon_item": "LONGITUDINAL_EXTENSION_PATH",
        "required": "YES",
        "purpose":
            "Ensure the architecture can later support time variation rather than a one-year-only construction.",
    },
]

recon = pd.DataFrame(
    recon_rows
)

if len(recon) != 7:
    raise RuntimeError(
        "C source-recon register shape mismatch"
    )


OUT_MATRIX.parent.mkdir(
    parents=True,
    exist_ok=True,
)

matrix.to_csv(
    OUT_MATRIX,
    sep="\t",
    index=False,
    lineterminator="\n",
)

criteria.to_csv(
    OUT_CRITERIA,
    sep="\t",
    index=False,
    lineterminator="\n",
)

recon.to_csv(
    OUT_RECON,
    sep="\t",
    index=False,
    lineterminator="\n",
)


audit_lines = [
    "=" * 100,
    "E4C2 — C COORDINATE ARCHITECTURE PREFLIGHT",
    "=" * 100,
    "",
    "RAW_SURVEY_DATA_READ=0",
    "NEW_ECONOMIC_VALUES_OPENED=0",
    "NEW_REFERENCE_VALUES_OPENED=0",
    "COORDINATE_VALUES_COMPUTED=0",
    "TRANSFORMED_VALUES_COMPUTED=0",
    "GEOMETRY_PERFORMED=0",
    "",
    "===== EXISTING C EVIDENCE =====",
    "C_EXISTING_MEASURE=C_COST",
    "C_EXISTING_ROLE=OBSERVED_ANNUAL_CONSUMPTION_EXPENDITURE_FLOW_EVIDENCE",
    "C_EVIDENCE_COVERAGE=8_OF_8",
    "C_STATE_EQUALS_NEGATIVE_C_COST_AUTHORIZED=0",
    "",
    "===== C SEMANTIC TARGET =====",
    "C_SEMANTIC_TARGET=CONSUMPTION_ECONOMIC_COMMAND",
    "C_HIGHER_STATE_EQUALS_BETTER=1",
    "NOMINAL_EXPENDITURE_ALONE_SUFFICIENT=0",
    "",
    "===== CANDIDATE ARCHITECTURES =====",
    "C_A_STATUS=VIABLE_RECON_PENDING",
    "C_B_STATUS=VIABLE_RECON_PENDING",
    "C_C_STATUS=CONDITIONAL_RECON_PENDING_OVERLAP_AUDIT",
    "C_ARCHITECTURE_CANDIDATE_COUNT=3",
    "C_ARCHITECTURE_SELECTED=0",
    "",
    "===== IDENTIFICATION BLOCKERS =====",
    "C_A_SAME_YEAR_CROSS_SECTIONAL_IDENTIFICATION_RESOLVED=0",
    "C_B_PRICE_QUANTITY_ARCHITECTURE_RESOLVED=0",
    "C_C_K_D_I_OVERLAP_RESOLVED=0",
    "C_SOURCE_LINEAGE_RESOLVED=0",
    "",
    "===== OUTCOME-INDEPENDENT SELECTION =====",
    "DIRECTION_GATE=0",
    "MAGNITUDE_GATE=0",
    "SIGNIFICANCE_GATE=0",
    "OWNER_RENTER_SEPARATION_GATE=0",
    "GEOMETRY_GATE=0",
    "DIMENSIONALITY_GATE=0",
    "EXISTING_C_COST_ORDERING_GATE=0",
    "E4C2_SELECTION_CRITERIA_COUNT=12",
    "E4C2_SELECTION_CRITERIA_SHAPE=PASS",
    "",
    "===== NEXT RECON =====",
    "E4C2_C_SOURCE_RECON_ITEM_COUNT=7",
    "E4C2_C_SOURCE_RECON_SHAPE=PASS",
    "E4C2A_C_REFERENCE_PRICE_QUANTITY_SOURCE_RECON_PREFLIGHT_AUTHORIZED=1",
    "",
    "===== HARD BOUNDARY =====",
    "C_COORDINATE_VALUES_AUTHORIZED=0",
    "FIVE_COMPONENT_STATE_VECTOR_AUTHORIZED=0",
    "FIVE_COMPONENT_NORMALIZATION_AUTHORIZED=0",
    "DIMENSIONALITY_TEST_AUTHORIZED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "",
    "E4C2_C_COORDINATE_ARCHITECTURE_PREFLIGHT=PASS",
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
