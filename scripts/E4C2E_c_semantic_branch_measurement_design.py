#!/usr/bin/env python3
from pathlib import Path
import csv
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]

CONTRACT = ROOT / "data/metadata/E4C2E_c_semantic_branch_measurement_design_contract.json"
LINEAGE = ROOT / "data/metadata/E4C2E_frozen_input_lineage.tsv"
E4C2D_EXEC = ROOT / "data/metadata/E4C2D_execution.txt"

EXEC = ROOT / "data/metadata/E4C2E_execution.txt"
AUDIT = ROOT / "data/metadata/E4C2E_c_semantic_branch_measurement_design_audit.txt"
BRANCHES = ROOT / "data/results/E4C2E_c_semantic_branch_registry.tsv"
DECISION = ROOT / "data/results/E4C2E_c_current_operating_decision.tsv"
SEQUENCE = ROOT / "data/results/E4C2E_post_c_coordinate_research_sequence.tsv"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_tsv(path: Path):
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def exact(lines, item):
    if item not in lines:
        raise RuntimeError(f"missing frozen invariant: {item}")


contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
if contract["phase"] != "E4C2E":
    raise RuntimeError("wrong contract phase")
if contract["operating_decision"]["selected_branch"] != 3:
    raise RuntimeError("branch 3 was not frozen as current operating decision")
if contract["semantic_branches"]["3_UNRESOLVED_EVIDENCE_ONLY"]["current_numeric_coordinate"]:
    raise RuntimeError("branch 3 must not create a numeric coordinate")

for row in read_tsv(LINEAGE):
    p = ROOT / row["artifact"]
    if not p.exists() or sha256(p) != row["sha256"]:
        raise RuntimeError(f"frozen lineage mismatch: {row['artifact']}")

lines = E4C2D_EXEC.read_text(encoding="utf-8").splitlines()
for item in [
    "E4C2D_TARGETED_C_IDENTIFICATION_EVIDENCE_AUDIT=PASS",
    "DIRECT_435_UCC_REAL_QUANTITY_IDENTIFIED=0",
    "COMPLETE_C_REFERENCE_PRICE_VECTOR_IDENTIFIED=0",
    "HOUSEHOLD_REAL_QUANTITY_IDENTIFICATION_RESOLVED=0",
    "C_REAL_STATE_COORDINATE_IDENTIFIED=0",
    "C_ARCHITECTURE_SELECTED=0",
    "E4C2E_C_SEMANTIC_BRANCH_AND_MEASUREMENT_DESIGN_PREFLIGHT_AUTHORIZED=1",
]:
    exact(lines, item)

branch_rows = [
    {
        "branch_id": "1",
        "branch_name": "REALIZED_REAL_CONSUMPTION",
        "status": "PRESERVED_NOT_IDENTIFIED",
        "numeric_coordinate_authorized": "0",
        "reopen_condition": "PRECOMMITTED_NEW_IDENTIFICATION_EVIDENCE",
    },
    {
        "branch_id": "2",
        "branch_name": "CONSUMPTION_ECONOMIC_COMMAND",
        "status": "PRESERVED_FUTURE_RESEARCH",
        "numeric_coordinate_authorized": "0",
        "reopen_condition": "RESOURCE_DENOMINATOR_KDI_OVERLAP_EQUIVALENCE_SCALE_RESOLVED",
    },
    {
        "branch_id": "3",
        "branch_name": "UNRESOLVED_EVIDENCE_ONLY",
        "status": "SELECTED_CURRENT_OPERATING_DECISION",
        "numeric_coordinate_authorized": "0",
        "reopen_condition": "FUTURE_PRECOMMITTED_IDENTIFICATION_EVIDENCE_ONLY",
    },
]

decision_rows = [
    ("C_CURRENT_OPERATING_BRANCH", "3_UNRESOLVED_EVIDENCE_ONLY"),
    ("C_CURRENT_OPERATING_BRANCH_SELECTED", "1"),
    ("C_BRANCH_1_REALIZED_REAL_CONSUMPTION_PRESERVED", "1"),
    ("C_BRANCH_1_CURRENTLY_IDENTIFIED", "0"),
    ("C_BRANCH_2_CONSUMPTION_ECONOMIC_COMMAND_PRESERVED", "1"),
    ("C_BRANCH_2_CURRENTLY_SELECTED", "0"),
    ("C_BRANCH_3_UNRESOLVED_EVIDENCE_ONLY_SELECTED", "1"),
    ("C_CURRENT_BRANCH_IS_PERMANENT_DEFINITION", "0"),
    ("C_CONCEPT_DROPPED_FROM_MODEL", "0"),
    ("C_COST_REMAINS_VALID_DESCRIPTIVE_EVIDENCE", "1"),
    ("C_COST_IS_C_STATE_COORDINATE", "0"),
    ("NEGATIVE_C_COST_IS_C_STATE_COORDINATE", "0"),
    ("CPI_DEFLATED_C_COST_AUTOMATIC_REAL_QUANTITY", "0"),
    ("PCE_MAPPED_C_COST_AUTOMATIC_REAL_QUANTITY", "0"),
    ("COST_SIDE_REFERENCE_BASKET_IS_C_STATE_COORDINATE", "0"),
    ("C_FORCED_NUMERICAL_COORDINATE", "0"),
    ("C_REAL_STATE_COORDINATE_IDENTIFIED", "0"),
    ("C_ARCHITECTURE_SELECTED", "0"),
    ("C_COORDINATE_VALUES_AUTHORIZED", "0"),
    ("FIVE_COMPONENT_LABELS_REQUIRE_FIVE_NUMERICAL_COORDINATES", "0"),
    ("UNRESOLVED_COMPONENT_MAY_REMAIN_EVIDENCE_ONLY", "1"),
    ("C_UNRESOLVED_BLOCKS_OTHER_COMPONENT_SEMANTIC_RESEARCH", "0"),
    ("FIVE_COMPONENT_STATE_VECTOR_AUTHORIZED", "0"),
    ("FIVE_COMPONENT_NORMALIZATION_AUTHORIZED", "0"),
    ("GEOMETRY_AUTHORIZED", "0"),
    ("DIMENSIONALITY_TEST_AUTHORIZED", "0"),
    ("REAL_INFLATION_ESTIMATION_AUTHORIZED", "0"),
    ("FINAL_SCALAR_AUTHORIZED", "0"),
    ("C_BRANCH_REOPENING_MAY_DEPEND_ON_OWNER_RENTER_RESULTS", "0"),
    ("C_BRANCH_REOPENING_MAY_DEPEND_ON_GEOMETRY_RESULTS", "0"),
    ("E4C3_H_HOUSING_SEMANTICS_AND_ACCESS_PREFLIGHT_AUTHORIZED", "1"),
]

sequence_rows = [
    ("1", "E4C3", "H_HOUSING_SEMANTICS_AND_ACCESS", "AUTHORIZED_NEXT"),
    ("2", "E4C4", "I_EMPLOYMENT_LABOR_SECURITY_REPRESENTATION", "AFTER_E4C3"),
    ("3", "POST_E4C4", "K_D_DIMENSIONLESS_TRANSFORM_FREEZE", "AFTER_H_I"),
    ("4", "POST_TRANSFORMS", "COORDINATE_READINESS_CLOSEOUT", "BEFORE_ANY_GEOMETRY"),
]

for p in (EXEC, AUDIT, BRANCHES, DECISION, SEQUENCE):
    p.parent.mkdir(parents=True, exist_ok=True)

with BRANCHES.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(
        f,
        fieldnames=[
            "branch_id",
            "branch_name",
            "status",
            "numeric_coordinate_authorized",
            "reopen_condition",
        ],
        delimiter="\t",
        lineterminator="\n",
    )
    w.writeheader()
    w.writerows(branch_rows)

with DECISION.open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t", lineterminator="\n")
    w.writerow(["decision", "value"])
    w.writerows(decision_rows)

with SEQUENCE.open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t", lineterminator="\n")
    w.writerow(["order", "phase", "scope", "status"])
    w.writerows(sequence_rows)

log = "\n".join([
    "================================================================================",
    "ECONOMIC GEOMETRY RESEARCH — E4C2E",
    "C SEMANTIC-BRANCH + MEASUREMENT-DESIGN FREEZE",
    "================================================================================",
    "RAW_SURVEY_DATA_READ=0",
    "NEW_ECONOMIC_VALUES_OPENED=0",
    "NEW_EXTERNAL_METADATA_DOWNLOADED=0",
    "HTTP_REQUESTS_PERFORMED=0",
    "FROZEN_E4C2D_RESULTS_ONLY=1",
    "C_BRANCH_1_REALIZED_REAL_CONSUMPTION=PRESERVED_NOT_IDENTIFIED",
    "C_BRANCH_2_CONSUMPTION_ECONOMIC_COMMAND=PRESERVED_FUTURE_RESEARCH",
    "C_BRANCH_3_UNRESOLVED_EVIDENCE_ONLY=SELECTED_CURRENT_OPERATING_DECISION",
    "C_CURRENT_OPERATING_BRANCH=3_UNRESOLVED_EVIDENCE_ONLY",
    "C_CURRENT_OPERATING_BRANCH_SELECTED=1",
    "C_CURRENT_BRANCH_IS_PERMANENT_DEFINITION=0",
    "C_CONCEPT_DROPPED_FROM_MODEL=0",
    "C_COST_REMAINS_VALID_DESCRIPTIVE_EVIDENCE=1",
    "C_COST_IS_C_STATE_COORDINATE=0",
    "NEGATIVE_C_COST_IS_C_STATE_COORDINATE=0",
    "CPI_DEFLATED_C_COST_AUTOMATIC_REAL_QUANTITY=0",
    "PCE_MAPPED_C_COST_AUTOMATIC_REAL_QUANTITY=0",
    "COST_SIDE_REFERENCE_BASKET_IS_C_STATE_COORDINATE=0",
    "C_FORCED_NUMERICAL_COORDINATE=0",
    "C_REAL_STATE_COORDINATE_IDENTIFIED=0",
    "C_ARCHITECTURE_SELECTED=0",
    "C_COORDINATE_VALUES_COMPUTED=0",
    "TRANSFORMED_VALUES_COMPUTED=0",
    "GEOMETRY_PERFORMED=0",
    "C_COORDINATE_VALUES_AUTHORIZED=0",
    "FIVE_COMPONENT_LABELS_REQUIRE_FIVE_NUMERICAL_COORDINATES=0",
    "UNRESOLVED_COMPONENT_MAY_REMAIN_EVIDENCE_ONLY=1",
    "C_UNRESOLVED_BLOCKS_OTHER_COMPONENT_SEMANTIC_RESEARCH=0",
    "FIVE_COMPONENT_STATE_VECTOR_AUTHORIZED=0",
    "FIVE_COMPONENT_NORMALIZATION_AUTHORIZED=0",
    "GEOMETRY_AUTHORIZED=0",
    "DIMENSIONALITY_TEST_AUTHORIZED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "C_BRANCH_REOPENING_MAY_DEPEND_ON_OWNER_RENTER_RESULTS=0",
    "C_BRANCH_REOPENING_MAY_DEPEND_ON_GEOMETRY_RESULTS=0",
    "E4C2E_C_SEMANTIC_BRANCH_AND_MEASUREMENT_DESIGN=PASS",
    "E4C3_H_HOUSING_SEMANTICS_AND_ACCESS_PREFLIGHT_AUTHORIZED=1",
]) + "\n"

EXEC.write_text(log, encoding="utf-8")
AUDIT.write_text(log, encoding="utf-8")
print(log, end="")
