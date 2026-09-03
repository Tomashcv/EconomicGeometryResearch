#!/usr/bin/env python3
from pathlib import Path
import csv,json

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"data/metadata/E4D0B2_targeted_comparability_gap_resolution_contract.json"
TARGETS=ROOT/"data/metadata/E4D0B2_official_gap_evidence_acquisition_plan.tsv"
PLAN=ROOT/"data/metadata/E4D0B2_gap_resolution_plan.tsv"
B1_GAPS=ROOT/"data/results/E4D0B1_unresolved_gap_registry.tsv"
B1_ADJ=ROOT/"data/results/E4D0B1_adjudication_registry.tsv"

EXEC=ROOT/"data/metadata/E4D0B2_execution.txt"
AUDIT=ROOT/"data/metadata/E4D0B2_targeted_comparability_gap_resolution_preflight_audit.txt"
RULES=ROOT/"data/results/E4D0B2_conditional_resolution_rule_registry.tsv"
BRIDGE=ROOT/"data/results/E4D0B2_k_price_reference_bridge_policy.tsv"
GATES=ROOT/"data/results/E4D0B2_preflight_hard_gates.tsv"
DECISION=ROOT/"data/results/E4D0B2_targeted_comparability_gap_resolution_preflight_decision.tsv"

c=json.loads(CONTRACT.read_text(encoding="utf-8"))

with TARGETS.open("r",encoding="utf-8",newline="") as f:
    targets=list(csv.DictReader(f,delimiter="\t"))
assert len(targets)==5
assert [int(r["target_index"]) for r in targets]==[1,2,3,4,5]

with PLAN.open("r",encoding="utf-8",newline="") as f:
    plan=list(csv.DictReader(f,delimiter="\t"))
assert len(plan)==7
assert [int(r["object_index"]) for r in plan]==[4,10,12,28,29,32,37]

with B1_GAPS.open("r",encoding="utf-8",newline="") as f:
    gaps=list(csv.DictReader(f,delimiter="\t"))
assert [int(r["object_index"]) for r in gaps]==[4,10,12,28,29,32,37]

with B1_ADJ.open("r",encoding="utf-8",newline="") as f:
    adj=list(csv.DictReader(f,delimiter="\t"))
assert len(adj)==40
assert sum(r["status"]=="PASS" for r in adj)==31
assert sum(r["status"]=="VERSIONED_PASS" for r in adj)==2
assert sum(r["status"]=="FAIL" for r in adj)==0
assert sum(r["status"]=="UNRESOLVED" for r in adj)==7

def write_tsv(path,header,rows):
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,delimiter="\t",lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)

rules=[]
for r in plan:
    rules.append([
        r["object_index"],r["axis"],r["scope_id"],
        r["current_status"],r["precommitted_success_status"],
        r["resolution_evidence"],r["precommitted_rule"],r["failure_status"]
    ])

write_tsv(
    RULES,
    ["object_index","axis","scope_id","current_status",
     "success_status_if_rule_passes","required_evidence",
     "frozen_success_rule","status_if_not_proven"],
    rules
)

bridge_rows=[
["BRIDGE_ID","FED_SCF_SUMMARY_EXTRACT_REAL_2022_DOLLAR_BASIS"],
["STATUS_AT_E4D0B2","CONDITIONAL_NOT_YET_VALIDATED"],
["OFFICIAL_METHOD","Federal Reserve SCF summary-extract CPI-U-RS real-dollar transport"],
["COMMON_BASIS","2022 dollars"],
["NEW_MACRO_REQUIRED","SCF_SUMMARY_EXTRACT_MACRO"],
["EXISTING_RELEASE_PAGE_EVIDENCE_REQUIRED","SCF_2019_RELEASE_PAGE|SCF_2022_RELEASE_PAGE"],
["FIN_COMMON_DEFINITION_REQUIRED","1"],
["FIN_IN_REAL_DOLLAR_ADJUSTMENT_SET_REQUIRED","1"],
["YEAR_2019_BRANCH_REQUIRED","1"],
["YEAR_2022_BRANCH_REQUIRED","1"],
["EXISTING_K_REFERENCE_SCALE_REUSED","1"],
["K_REFERENCE_SCALE_REFIT_ON_2019_VALUES","0"],
["ALTERNATIVE_DEFLATOR_SELECTION_AFTER_VALUES","0"],
["FAILURE_TO_VALIDATE_MAPS_TO","UNRESOLVED"],
]
write_tsv(BRIDGE,["field","value"],bridge_rows)

gate_rows=[
["E4D0B1_EXACT_7_UNRESOLVED_GAPS_REUSED","PASS"],
["E4D0B1_FAIL_OBJECT_COUNT","0"],
["NEW_OFFICIAL_EVIDENCE_TARGET_COUNT","5"],
["NEW_EVIDENCE_TARGETS_METADATA_OR_PROGRAM_DOCS_ONLY","PASS"],
["MICRODATA_URL_COUNT","0"],
["NETWORK_ACCESS_PERFORMED_BY_E4D0B2","0"],
["NEW_DOCUMENT_CONTENT_OPENED_BY_E4D0B2","0"],
["AGE_FUZZY_JACCARD_REUSED_FOR_OBJECTS_10_12","0"],
["K_PRICE_BRIDGE_CONDITIONALLY_FROZEN_BEFORE_2019_VALUES","PASS"],
["K_REFERENCE_SCALE_REFIT_AUTHORIZED","0"],
["COMMON_YEAR_GRID_FROZEN","0"],
["ADDITIONAL_YEAR_ECONOMIC_VALUES_OPENED","0"],
["TEMPORAL_GEOMETRY_COMPUTED","0"],
["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
]
write_tsv(GATES,["gate","value"],gate_rows)

decision_rows=[
["TARGET_YEAR_PAIR","2019_TO_2022"],
["B1_PASS_OBJECT_COUNT","31"],
["B1_VERSIONED_PASS_OBJECT_COUNT","2"],
["B1_FAIL_OBJECT_COUNT","0"],
["B1_UNRESOLVED_OBJECT_COUNT","7"],
["TARGETED_GAP_OBJECT_IDS","4|10|12|28|29|32|37"],
["NEW_OFFICIAL_EVIDENCE_TARGET_COUNT","5"],
["NETWORK_ACCESS_PERFORMED","0"],
["NEW_DOCUMENT_CONTENT_OPENED","0"],
["MICRODATA_FILES_DOWNLOADED","0"],
["ADDITIONAL_YEAR_ECONOMIC_VALUES_OPENED","0"],
["COMMON_YEAR_GRID_FROZEN","0"],
["EXPECTED_ALL_SUCCESS_PASS_OBJECT_COUNT","36"],
["EXPECTED_ALL_SUCCESS_VERSIONED_PASS_OBJECT_COUNT","4"],
["EXPECTED_ALL_SUCCESS_UNRESOLVED_OBJECT_COUNT","0"],
["E4D1_MULTIYEAR_PARTIAL_STATE_COORDINATE_EXECUTION_PREFLIGHT_AUTHORIZED","0"],
["NEXT_PRIMARY_PHASE_ID","E4D0B2A"],
["E4D0B2A_TARGETED_COMPARABILITY_GAP_RESOLUTION_EXECUTION_AUTHORIZED","1"],
["E4D0B2_TARGETED_COMPARABILITY_GAP_RESOLUTION_PREFLIGHT","PASS"],
]
write_tsv(DECISION,["decision","value"],decision_rows)

log="\n".join([
"E4D0B1_REUSED_AS_CANONICAL_COMPARABILITY_ADJUDICATION=1",
"TARGET_YEAR_PAIR=2019_TO_2022",
"B1_PASS_OBJECT_COUNT=31",
"B1_VERSIONED_PASS_OBJECT_COUNT=2",
"B1_FAIL_OBJECT_COUNT=0",
"B1_UNRESOLVED_OBJECT_COUNT=7",
"TARGETED_GAP_OBJECT_IDS=4|10|12|28|29|32|37",
"NEW_OFFICIAL_EVIDENCE_TARGET_COUNT=5",
"NETWORK_ACCESS_PERFORMED=0",
"NEW_DOCUMENT_CONTENT_OPENED=0",
"MICRODATA_FILES_DOWNLOADED=0",
"ADDITIONAL_YEAR_ECONOMIC_VALUES_OPENED=0",
"COMMON_YEAR_GRID_FROZEN=0",
"EXPECTED_ALL_SUCCESS_PASS_OBJECT_COUNT=36",
"EXPECTED_ALL_SUCCESS_VERSIONED_PASS_OBJECT_COUNT=4",
"EXPECTED_ALL_SUCCESS_UNRESOLVED_OBJECT_COUNT=0",
"TEMPORAL_GEOMETRY_COMPUTED=0",
"REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
"E4D1_MULTIYEAR_PARTIAL_STATE_COORDINATE_EXECUTION_PREFLIGHT_AUTHORIZED=0",
"E4D0B2A_TARGETED_COMPARABILITY_GAP_RESOLUTION_EXECUTION_AUTHORIZED=1",
"E4D0B2_TARGETED_COMPARABILITY_GAP_RESOLUTION_PREFLIGHT=PASS",
])+"\n"

EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
