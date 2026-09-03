#!/usr/bin/env python3
from pathlib import Path
import csv
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "data/metadata/E4C2C_c_identification_architecture_decision_contract.json"
LINEAGE = ROOT / "data/metadata/E4C2C_frozen_input_lineage.tsv"
E4C2B_EXEC = ROOT / "data/metadata/E4C2B_execution.txt"

EXEC = ROOT / "data/metadata/E4C2C_execution.txt"
AUDIT = ROOT / "data/metadata/E4C2C_c_identification_architecture_decision_audit.txt"
LEDGER = ROOT / "data/results/E4C2C_c_architecture_candidate_ledger.tsv"
DECISION = ROOT / "data/results/E4C2C_c_identification_decision.tsv"
REQS = ROOT / "data/results/E4C2C_c_next_evidence_requirements.tsv"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_tsv(path: Path):
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def exact(lines, x):
    if x not in lines:
        raise RuntimeError(f"missing frozen invariant: {x}")


contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
lineage = read_tsv(LINEAGE)

for row in lineage:
    p = ROOT / row["artifact"]
    if not p.exists():
        raise RuntimeError(f"missing frozen input: {row['artifact']}")
    if sha256(p) != row["sha256"]:
        raise RuntimeError(f"frozen input lineage mismatch: {row['artifact']}")

lines = E4C2B_EXEC.read_text(encoding="utf-8").splitlines()

required = [
    "RAW_SURVEY_DATA_READ=0",
    "NEW_CEX_ECONOMIC_VALUES_OPENED=0",
    "CPI_INDEX_VALUES_OPENED=0",
    "CPI_AVERAGE_PRICE_VALUES_OPENED=0",
    "PCE_EXPENDITURE_VALUES_OPENED=0",
    "PCE_PRICE_INDEX_VALUES_OPENED=0",
    "PCE_QUANTITY_INDEX_VALUES_OPENED=0",
    "REGIONAL_PRICE_PARITY_VALUES_OPENED=0",
    "FROZEN_C_COST_UCCS=435",
    "FROZEN_C_COST_UNIQUE_UCCS=435",
    "CPI_2022_ELI_MAPPED_UCCS_OF_435=387",
    "PCE_CONCORDANCE_MAPPED_UCCS_OF_435=435",
    "BOTH_CPI_AND_PCE_MAPPED_UCCS_OF_435=387",
    "C_A_COMPLETE_REFERENCE_PRICE_VECTOR_RESOLVED=0",
    "C_B_REAL_QUANTITY_CROSS_SECTIONAL_IDENTIFICATION_RESOLVED=0",
    "C_C_K_D_I_OVERLAP_RESOLVED=0",
    "EQUIVALENCE_SCALE_PLACEMENT_SELECTED=0",
    "C_ARCHITECTURE_SELECTED=0",
    "E4C2B_C_CONCORDANCE_AND_CATEGORY_COVERAGE_AUDIT=PASS",
    "E4C2C_C_IDENTIFICATION_AND_ARCHITECTURE_DECISION_PREFLIGHT_AUTHORIZED=1",
]
for x in required:
    exact(lines, x)

ledger_rows = [
    {
        "candidate": "NOMINAL_C_COST_AS_REAL_STATE",
        "decision": "NOT_SELECTED",
        "reason": "nominal expenditure mixes price quantity mix and choice; not identified as real consumption quantity",
        "may_compute_values_now": "0",
    },
    {
        "candidate": "AGGREGATE_CPI_DEFLATED_C_COST",
        "decision": "NOT_SELECTED",
        "reason": "aggregate CPI deflation does not identify household cross-sectional quantity or category price levels",
        "may_compute_values_now": "0",
    },
    {
        "candidate": "UCC_ELI_CPI_DEFLATED_REAL_QUANTITY",
        "decision": "NOT_IDENTIFIED",
        "reason": "CPI concordance covers 387 of 435 frozen UCCs and CPI series levels are not cross-category reference prices",
        "may_compute_values_now": "0",
    },
    {
        "candidate": "PCE_CONCORDANCE_BASED_REAL_QUANTITY",
        "decision": "NOT_IDENTIFIED",
        "reason": "435 of 435 concordance coverage is classification coverage; household real quantity is not thereby identified",
        "may_compute_values_now": "0",
    },
    {
        "candidate": "HYBRID_CPI_PCE_REAL_QUANTITY",
        "decision": "NOT_IDENTIFIED",
        "reason": "combining concordances does not create household quantities or a complete comparable reference-price vector",
        "may_compute_values_now": "0",
    },
    {
        "candidate": "FIXED_REFERENCE_BASKET_COST_INDEX",
        "decision": "RETAIN_DISTINCT_COST_SIDE_CANDIDATE",
        "reason": "potential future temporal cost-side architecture; not interchangeable with the C real-quantity state",
        "may_compute_values_now": "0",
    },
    {
        "candidate": "REAL_CONSUMPTION_QUANTITY_STATE",
        "decision": "TARGET_SEMANTIC_UNRESOLVED",
        "reason": "requires identified reference-price or quantity construction plus comparability and equivalence-scale placement",
        "may_compute_values_now": "0",
    },
]

decision_rows = [
    ("C_REAL_STATE_COORDINATE_IDENTIFIED", "0"),
    ("C_ARCHITECTURE_SELECTED", "0"),
    ("NOMINAL_C_COST_EQUALS_REAL_CONSUMPTION_QUANTITY", "0"),
    ("CPI_SERIES_INDEX_LEVELS_CROSS_CATEGORY_PRICE_LEVEL_AUTHORIZED", "0"),
    ("CONCORDANCE_MAPPING_ALONE_IDENTIFIES_REAL_QUANTITY", "0"),
    ("PCE_CONCORDANCE_ALONE_IDENTIFIES_HOUSEHOLD_REAL_QUANTITY", "0"),
    ("SILENT_IMPUTATION_OF_48_NON_CPI_MAPPED_UCCS_AUTHORIZED", "0"),
    ("COST_SIDE_REFERENCE_BASKET_TRACK_SEPARATED_FROM_C_STATE", "1"),
    ("EQUIVALENCE_SCALE_PLACEMENT_SELECTED", "0"),
    ("C_COORDINATE_VALUES_AUTHORIZED", "0"),
    ("FIVE_COMPONENT_STATE_VECTOR_AUTHORIZED", "0"),
    ("FIVE_COMPONENT_NORMALIZATION_AUTHORIZED", "0"),
    ("GEOMETRY_AUTHORIZED", "0"),
    ("DIMENSIONALITY_TEST_AUTHORIZED", "0"),
    ("REAL_INFLATION_ESTIMATION_AUTHORIZED", "0"),
    ("FINAL_SCALAR_AUTHORIZED", "0"),
    ("E4C2D_TARGETED_C_IDENTIFICATION_EVIDENCE_AUDIT_AUTHORIZED", "1"),
]

requirements = [
    (
        "REFERENCE_PRICE_SEMANTICS",
        "determine whether any official source supplies economically meaningful comparable reference-price information for the frozen C categories; CPI temporal index levels alone do not satisfy this",
        "REQUIRED_BEFORE_REAL_C_STATE",
    ),
    (
        "CPI_COVERAGE_GAP",
        "adjudicate the 48 of 435 frozen C_COST UCCs without CPI-ELI mapping; no silent dropping or imputation",
        "REQUIRED_IF_CPI_PATH_RETAINED",
    ),
    (
        "HOUSEHOLD_REAL_QUANTITY",
        "determine whether household/category real quantity can be identified from CEX fields or a defensible official bridge",
        "REQUIRED_BEFORE_REAL_C_STATE",
    ),
    (
        "PCE_BRIDGE_SEMANTICS",
        "determine whether PCE concepts can contribute only temporal/category information or can support a valid household bridge; concordance alone is insufficient",
        "REQUIRED_IF_PCE_PATH_RETAINED",
    ),
    (
        "KDI_COMPARABILITY",
        "precommit how C would coexist with K D and I without pretending raw units are commensurable",
        "REQUIRED_BEFORE_FIVE_COMPONENT_VECTOR",
    ),
    (
        "EQUIVALENCE_SCALE",
        "select placement and semantics of household-size/composition adjustment before C state normalization",
        "REQUIRED_BEFORE_C_NORMALIZATION",
    ),
]

for p in (EXEC, AUDIT, LEDGER, DECISION, REQS):
    p.parent.mkdir(parents=True, exist_ok=True)

with LEDGER.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(
        f,
        fieldnames=["candidate", "decision", "reason", "may_compute_values_now"],
        delimiter="\t",
        lineterminator="\n",
    )
    w.writeheader()
    w.writerows(ledger_rows)

with DECISION.open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t", lineterminator="\n")
    w.writerow(["decision", "value"])
    w.writerows(decision_rows)

with REQS.open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t", lineterminator="\n")
    w.writerow(["requirement", "description", "status"])
    w.writerows(requirements)

log = "\n".join([
    "================================================================================",
    "ECONOMIC GEOMETRY RESEARCH — E4C2C",
    "C IDENTIFICATION + ARCHITECTURE DECISION",
    "================================================================================",
    "RAW_SURVEY_DATA_READ=0",
    "NEW_CEX_ECONOMIC_VALUES_OPENED=0",
    "CPI_INDEX_VALUES_OPENED=0",
    "CPI_AVERAGE_PRICE_VALUES_OPENED=0",
    "PCE_EXPENDITURE_VALUES_OPENED=0",
    "PCE_PRICE_INDEX_VALUES_OPENED=0",
    "PCE_QUANTITY_INDEX_VALUES_OPENED=0",
    "REGIONAL_PRICE_PARITY_VALUES_OPENED=0",
    "NEW_EXTERNAL_METADATA_DOWNLOADED=0",
    "HTTP_REQUESTS_PERFORMED=0",
    "FROZEN_E4C2B_RESULTS_ONLY=1",
    "FROZEN_C_COST_UCCS=435",
    "CPI_2022_ELI_MAPPED_UCCS_OF_435=387",
    "PCE_CONCORDANCE_MAPPED_UCCS_OF_435=435",
    "BOTH_CPI_AND_PCE_MAPPED_UCCS_OF_435=387",
    "NOMINAL_C_COST_EQUALS_REAL_CONSUMPTION_QUANTITY=0",
    "CPI_SERIES_INDEX_LEVELS_CROSS_CATEGORY_PRICE_LEVEL_AUTHORIZED=0",
    "CONCORDANCE_MAPPING_ALONE_IDENTIFIES_REAL_QUANTITY=0",
    "PCE_CONCORDANCE_ALONE_IDENTIFIES_HOUSEHOLD_REAL_QUANTITY=0",
    "SILENT_IMPUTATION_OF_48_NON_CPI_MAPPED_UCCS_AUTHORIZED=0",
    "C_A_COMPLETE_REFERENCE_PRICE_VECTOR_RESOLVED=0",
    "C_B_REAL_QUANTITY_CROSS_SECTIONAL_IDENTIFICATION_RESOLVED=0",
    "C_C_K_D_I_OVERLAP_RESOLVED=0",
    "EQUIVALENCE_SCALE_PLACEMENT_SELECTED=0",
    "C_REAL_STATE_COORDINATE_IDENTIFIED=0",
    "C_ARCHITECTURE_SELECTED=0",
    "COST_SIDE_REFERENCE_BASKET_TRACK_SEPARATED_FROM_C_STATE=1",
    "C_COORDINATE_VALUES_COMPUTED=0",
    "TRANSFORMED_VALUES_COMPUTED=0",
    "GEOMETRY_PERFORMED=0",
    "C_COORDINATE_VALUES_AUTHORIZED=0",
    "FIVE_COMPONENT_STATE_VECTOR_AUTHORIZED=0",
    "FIVE_COMPONENT_NORMALIZATION_AUTHORIZED=0",
    "GEOMETRY_AUTHORIZED=0",
    "DIMENSIONALITY_TEST_AUTHORIZED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "E4C2C_NEGATIVE_IDENTIFICATION_DECISION_IS_VALID=1",
    "E4C2C_C_IDENTIFICATION_AND_ARCHITECTURE_DECISION=PASS",
    "E4C2D_TARGETED_C_IDENTIFICATION_EVIDENCE_AUDIT_AUTHORIZED=1",
]) + "\n"

EXEC.write_text(log, encoding="utf-8")
AUDIT.write_text(log, encoding="utf-8")

print(log, end="")
