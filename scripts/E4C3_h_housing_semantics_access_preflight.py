#!/usr/bin/env python3
from pathlib import Path
import csv
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]

CONTRACT = ROOT / "data/metadata/E4C3_h_housing_semantics_access_contract.json"
LINEAGE = ROOT / "data/metadata/E4C3_frozen_input_lineage.tsv"
PRIOR_H = ROOT / "data/metadata/E4C3_prior_h_semantics_lineage.tsv"

EXEC = ROOT / "data/metadata/E4C3_execution.txt"
AUDIT = ROOT / "data/metadata/E4C3_h_housing_semantics_access_audit.txt"
BRANCHES = ROOT / "data/results/E4C3_h_access_candidate_registry.tsv"
REQUIREMENTS = ROOT / "data/results/E4C3_h_access_source_requirements.tsv"
DECISION = ROOT / "data/results/E4C3_h_current_semantic_decision.tsv"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_tsv(path: Path):
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
if contract["phase"] != "E4C3":
    raise RuntimeError("wrong E4C3 contract phase")
if contract["housing_semantic_target"]["tenure_is_H_ACCESS"]:
    raise RuntimeError("tenure may not be H_ACCESS")
if contract["housing_semantic_target"]["H_SERVICE_is_complete_H_state"]:
    raise RuntimeError("H_SERVICE may not be promoted to complete H state")
if contract["hard_boundaries"]["H_ACCESS_selected"]:
    raise RuntimeError("H_ACCESS selection not authorized in preflight")

for row in read_tsv(LINEAGE):
    p = ROOT / row["artifact"]
    if not p.exists() or sha256(p) != row["sha256"]:
        raise RuntimeError(f"frozen input lineage mismatch: {row['artifact']}")

prior = read_tsv(PRIOR_H)
if len(prior) < 2:
    raise RuntimeError("insufficient prior H semantic lineage")

candidate_rows = [
    {
        "candidate": "AFFORDABILITY_BURDEN",
        "semantic_target": "ability to sustain housing costs from predeclared resources",
        "current_status": "SOURCE_AND_DENOMINATOR_RECON_PENDING",
        "tenure_tautology": "0",
        "selected": "0",
        "values_authorized": "0",
    },
    {
        "candidate": "SPACE_CROWDING_ADEQUACY",
        "semantic_target": "adequate usable housing space relative to household occupancy",
        "current_status": "SOURCE_AND_VARIABLE_RECON_PENDING",
        "tenure_tautology": "0",
        "selected": "0",
        "values_authorized": "0",
    },
    {
        "candidate": "PHYSICAL_ADEQUACY_QUALITY",
        "semantic_target": "absence of material housing deficiencies and basic-quality failures",
        "current_status": "SOURCE_AND_VARIABLE_RECON_PENDING",
        "tenure_tautology": "0",
        "selected": "0",
        "values_authorized": "0",
    },
    {
        "candidate": "STABILITY_DISPLACEMENT_SECURITY",
        "semantic_target": "security against involuntary housing loss displacement or instability",
        "current_status": "SOURCE_AND_VARIABLE_RECON_PENDING",
        "tenure_tautology": "0",
        "selected": "0",
        "values_authorized": "0",
    },
]

requirement_rows = [
    ("PUBLIC_REPRODUCIBLE_SOURCE", "REQUIRED"),
    ("PRIMARY_YEAR_2022_OR_JUSTIFIED_ALIGNMENT", "REQUIRED"),
    ("AGE_BAND_COMPATIBLE", "REQUIRED"),
    ("OWNER_RENTER_COHORT_COMPATIBLE_WITHOUT_USING_TENURE_AS_OUTCOME", "REQUIRED"),
    ("ALL_EIGHT_COHORT_CELLS_MEASURABLE", "REQUIRED"),
    ("SURVEY_WEIGHT_IDENTIFIED", "REQUIRED"),
    ("VARIANCE_METHOD_IDENTIFIED", "REQUIRED"),
    ("HIGHER_IS_BETTER_ORIENTATION_PREDECLARED", "REQUIRED"),
    ("NO_OWNER_RENTER_OUTCOME_DEPENDENT_SELECTION", "REQUIRED"),
    ("NO_SIGNIFICANCE_DEPENDENT_SELECTION", "REQUIRED"),
    ("NO_GEOMETRY_DEPENDENT_SELECTION", "REQUIRED"),
    ("NO_PERSON_LEVEL_CROSS_SURVEY_JOIN", "REQUIRED"),
    ("NO_UNSUPPORTED_JOINT_COVARIANCE", "REQUIRED"),
]

decision_rows = [
    ("H_CONCEPTUAL_TARGET", "HOUSING_ECONOMIC_SECURITY_AND_ACCESS"),
    ("H_SERVICE_REMAINS_VALID_DESCRIPTIVE_EVIDENCE", "1"),
    ("H_SERVICE_IS_COMPLETE_H_STATE", "0"),
    ("NEGATIVE_H_SERVICE_IS_H_STATE", "0"),
    ("TENURE_IS_H_ACCESS", "0"),
    ("TENURE_DEFINES_OWNER_RENTER_COHORT", "1"),
    ("H_ACCESS_REQUIRED_BEFORE_FULL_H_STATE", "1"),
    ("H_ACCESS_SELECTED", "0"),
    ("H_ACCESS_MAY_REQUIRE_MULTIPLE_SUBCOORDINATES", "1"),
    ("H_LABEL_REQUIRES_SINGLE_NUMERICAL_COORDINATE", "0"),
    ("H_COORDINATE_VALUES_AUTHORIZED", "0"),
    ("FIVE_COMPONENT_STATE_VECTOR_AUTHORIZED", "0"),
    ("FIVE_COMPONENT_NORMALIZATION_AUTHORIZED", "0"),
    ("GEOMETRY_AUTHORIZED", "0"),
    ("DIMENSIONALITY_TEST_AUTHORIZED", "0"),
    ("REAL_INFLATION_ESTIMATION_AUTHORIZED", "0"),
    ("FINAL_SCALAR_AUTHORIZED", "0"),
    ("E4C3A_H_ACCESS_SOURCE_VARIABLE_RECON_PREFLIGHT_AUTHORIZED", "1"),
]

for p in (EXEC, AUDIT, BRANCHES, REQUIREMENTS, DECISION):
    p.parent.mkdir(parents=True, exist_ok=True)

with BRANCHES.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(
        f,
        fieldnames=[
            "candidate",
            "semantic_target",
            "current_status",
            "tenure_tautology",
            "selected",
            "values_authorized",
        ],
        delimiter="\t",
        lineterminator="\n",
    )
    w.writeheader()
    w.writerows(candidate_rows)

with REQUIREMENTS.open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t", lineterminator="\n")
    w.writerow(["requirement", "status"])
    w.writerows(requirement_rows)

with DECISION.open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t", lineterminator="\n")
    w.writerow(["decision", "value"])
    w.writerows(decision_rows)

log = "\n".join([
    "================================================================================",
    "ECONOMIC GEOMETRY RESEARCH — E4C3",
    "H HOUSING SEMANTICS + H_ACCESS PREFLIGHT",
    "================================================================================",
    "RAW_SURVEY_DATA_READ=0",
    "NEW_HOUSING_ECONOMIC_VALUES_OPENED=0",
    "NEW_EXTERNAL_METADATA_DOWNLOADED=0",
    "HTTP_REQUESTS_PERFORMED=0",
    "FROZEN_PRIOR_EVIDENCE_ONLY=1",
    "H_CONCEPTUAL_TARGET=HOUSING_ECONOMIC_SECURITY_AND_ACCESS",
    "H_SERVICE_REMAINS_VALID_DESCRIPTIVE_EVIDENCE=1",
    "H_SERVICE_IS_COMPLETE_H_STATE=0",
    "NEGATIVE_H_SERVICE_IS_H_STATE=0",
    "TENURE_IS_H_ACCESS=0",
    "TENURE_DEFINES_OWNER_RENTER_COHORT=1",
    "H_ACCESS_REQUIRED_BEFORE_FULL_H_STATE=1",
    "H_ACCESS_CANDIDATE_COUNT=4",
    "H_ACCESS_SELECTED=0",
    "H_ACCESS_MAY_REQUIRE_MULTIPLE_SUBCOORDINATES=1",
    "H_LABEL_REQUIRES_SINGLE_NUMERICAL_COORDINATE=0",
    "OWNER_RENTER_DIRECTION_USED_AS_SELECTION_GATE=0",
    "STATISTICAL_SIGNIFICANCE_USED_AS_SELECTION_GATE=0",
    "GEOMETRY_USED_AS_SELECTION_GATE=0",
    "PERSON_LEVEL_CROSS_SURVEY_JOIN_AUTHORIZED=0",
    "UNSUPPORTED_JOINT_COVARIANCE_AUTHORIZED=0",
    "H_COORDINATE_VALUES_COMPUTED=0",
    "TRANSFORMED_VALUES_COMPUTED=0",
    "GEOMETRY_PERFORMED=0",
    "H_COORDINATE_VALUES_AUTHORIZED=0",
    "FIVE_COMPONENT_STATE_VECTOR_AUTHORIZED=0",
    "FIVE_COMPONENT_NORMALIZATION_AUTHORIZED=0",
    "GEOMETRY_AUTHORIZED=0",
    "DIMENSIONALITY_TEST_AUTHORIZED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "E4C3_H_HOUSING_SEMANTICS_AND_ACCESS_PREFLIGHT=PASS",
    "E4C3A_H_ACCESS_SOURCE_VARIABLE_RECON_PREFLIGHT_AUTHORIZED=1",
]) + "\n"

EXEC.write_text(log, encoding="utf-8")
AUDIT.write_text(log, encoding="utf-8")
print(log, end="")
