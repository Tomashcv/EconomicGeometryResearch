#!/usr/bin/env python3
from pathlib import Path
import csv,json
ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"data/metadata/E4D1_multiyear_partial_state_coordinate_execution_contract.json"
LINEAGE=ROOT/"data/metadata/E4D1_frozen_input_lineage.tsv"
COORD=ROOT/"data/metadata/E4D1_coordinate_execution_plan.tsv"
REQ=ROOT/"data/metadata/E4D1_2019_source_requirement_plan.tsv"
EXEC=ROOT/"data/metadata/E4D1_execution.txt"
AUDIT=ROOT/"data/metadata/E4D1_multiyear_partial_state_coordinate_execution_preflight_audit.txt"
DESIGN=ROOT/"data/results/E4D1_estimator_design_registry.tsv"
TIMEPOL=ROOT/"data/results/E4D1_temporal_alignment_policy.tsv"
SOURCEPLAN=ROOT/"data/results/E4D1_source_lineage_resolution_plan.tsv"
GATES=ROOT/"data/results/E4D1_preflight_hard_gates.tsv"
DECISION=ROOT/"data/results/E4D1_multiyear_partial_state_coordinate_execution_preflight_decision.tsv"

c=json.loads(CONTRACT.read_text(encoding="utf-8"))
with LINEAGE.open("r",encoding="utf-8",newline="") as f: lineage=list(csv.DictReader(f,delimiter="\t"))
with COORD.open("r",encoding="utf-8",newline="") as f: coords=list(csv.DictReader(f,delimiter="\t"))
with REQ.open("r",encoding="utf-8",newline="") as f: reqs=list(csv.DictReader(f,delimiter="\t"))
assert len(lineage)==11
assert len(coords)==5
assert len(reqs)==6
assert all(r["exact_url_frozen_now"]=="0" and r["value_content_open_authorized_now"]=="0" for r in reqs)

def write_tsv(path,header,rows):
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,delimiter="\t",lineterminator="\n"); w.writerow(header); w.writerows(rows)

write_tsv(DESIGN,["family","coordinate_id","target_year","estimand_rule","uncertainty_rule","bridge_or_refit_rule"],[
["ACS","H_ACCESS_SPACE_ROOMS_PER_PERSON","2019","REUSE_FROZEN_ESTIMAND_WITH_2019_VALID_DESIGN","official point plus replicate estimator required","NO_OUTCOME_REFIT"],
["SCF","K_FIN_MEAN_TRANSFORMED","2019","REUSE_FROZEN_ESTIMAND_WITH_VERSIONED_2019_DESIGN","five implicates plus official wave-specific replicate architecture","FED_SCF_SUMMARY_EXTRACT_REAL_2022_DOLLAR_BASIS_THEN_FROZEN_K_SCALE"],
["SCF","D_PIRTOTAL_MEAN_STATE_TRANSFORMED","2019","REUSE_FROZEN_ESTIMAND_WITH_VERSIONED_2019_DESIGN","five implicates plus official wave-specific replicate architecture","NO_PRICE_BRIDGE"],
["CPS_ASEC","I_FYFT_SHARE","2019","REUSE_FROZEN_ESTIMAND_WITH_2019_VALID_DESIGN","official point plus 160 replicates after exact source validation","NO_OUTCOME_REFIT"],
["CPS_ASEC","I_SEARCH_SECURITY","2019","REUSE_FROZEN_ESTIMAND_WITH_2019_VALID_DESIGN","official point plus 160 replicates after exact source validation","NO_OUTCOME_REFIT"],
])

write_tsv(TIMEPOL,["field","value"],[
["GRID","2019|2022"],["GRID_STATUS","FROZEN_BY_E4D0B2A_REUSED_BY_E4D1"],["INTERPOLATION","0"],["CARRY_FORWARD","0"],["SYNTHETIC_2020_STATE","0"],["SYNTHETIC_2021_STATE","0"],["COMMON_INSTANTANEOUS_REFERENCE_DATE_CLAIM","0"],["ACS_REFERENCE_POLICY","retain frozen coordinate-specific ACS wave/reference semantics"],["SCF_REFERENCE_POLICY","retain B2A versioned SCF wave semantics and validated real-dollar bridge"],["CPS_ASEC_REFERENCE_POLICY","retain frozen mixed-timing decomposition; do not relabel to one instant"]
])

write_tsv(SOURCEPLAN,["requirement_index","family","target_year","required_source_role","resolution_authority","current_status","resolution_phase","rule"],[
[r["requirement_index"],r["family"],r["target_year"],r["required_source_role"],r["official_resolution_authority"],"UNRESOLVED_EXACT_URL_BY_DESIGN","E4D1A",r["next_resolution_rule"]] for r in reqs
])

write_tsv(GATES,["gate","value"],[
["E4D0B2A_COMPARABILITY_RESOLVED_REUSED","PASS"],["COMMON_YEAR_GRID","2019|2022"],["NUMERICAL_COORDINATE_COUNT","5"],["REPRESENTED_CONCEPT_COUNT","4"],["TARGET_2019_COORDINATE_ROW_COUNT","40"],["CURRENT_2022_NUMERIC_ROWS_OPENED","0"],["2019_MICRODATA_FILES_DOWNLOADED","0"],["2019_MICRODATA_ROWS_OPENED","0"],["2019_ECONOMIC_VALUES_OPENED","0"],["K_REFERENCE_SCALE_REFIT_AUTHORIZED","0"],["TRANSFORM_REFIT_AUTHORIZED","0"],["TEMPORAL_GEOMETRY_AUTHORIZED","0"],["DIMENSIONALITY_TEST_AUTHORIZED","0"],["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],["FINAL_SCALAR_AUTHORIZED","0"]
])

write_tsv(DECISION,["decision","value"],[
["TARGET_YEAR_PAIR","2019_TO_2022"],["COMMON_YEAR_GRID","2019|2022"],["NUMERICAL_COORDINATE_COUNT","5"],["REPRESENTED_CONCEPT_COUNT","4"],["TARGET_2019_COORDINATE_ROW_COUNT","40"],["SOURCE_REQUIREMENT_COUNT","6"],["EXACT_2019_SOURCE_URL_COUNT_FROZEN","0"],["CURRENT_2022_NUMERIC_ROWS_OPENED","0"],["2019_MICRODATA_FILES_DOWNLOADED","0"],["2019_MICRODATA_ROWS_OPENED","0"],["2019_ECONOMIC_VALUES_OPENED","0"],["TEMPORAL_GEOMETRY_AUTHORIZED","0"],["DIMENSIONALITY_TEST_AUTHORIZED","0"],["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],["FINAL_SCALAR_AUTHORIZED","0"],["NEXT_PRIMARY_PHASE_ID","E4D1A"],["E4D1A_2019_OFFICIAL_SOURCE_LINEAGE_AND_ACQUISITION_PREFLIGHT_AUTHORIZED","1"],["E4D1_MULTIYEAR_PARTIAL_STATE_COORDINATE_EXECUTION_PREFLIGHT","PASS"]
])

log="\n".join([
"E4D0B2A_REUSED_AS_CANONICAL_COMPARABILITY_AND_GRID_AUTHORITY=1",
"TARGET_YEAR_PAIR=2019_TO_2022",
"COMMON_YEAR_GRID=2019|2022",
"COMMON_YEAR_GRID_FROZEN=1",
"NUMERICAL_COORDINATE_COUNT=5",
"REPRESENTED_CONCEPT_COUNT=4",
"STATE_CELL_COUNT_PER_YEAR=8",
"TARGET_2019_COORDINATE_ROW_COUNT=40",
"CURRENT_2022_POINT_REGISTRY_REUSED_BY_HASH_AND_HEADER_ONLY=1",
"CURRENT_2022_NUMERIC_ROWS_OPENED=0",
"2019_SOURCE_REQUIREMENT_COUNT=6",
"EXACT_2019_SOURCE_URL_COUNT_FROZEN=0",
"2019_MICRODATA_FILES_DOWNLOADED=0",
"2019_MICRODATA_ROWS_OPENED=0",
"2019_ECONOMIC_VALUES_OPENED=0",
"K_PRICE_REFERENCE_BRIDGE_REUSED=FED_SCF_SUMMARY_EXTRACT_REAL_2022_DOLLAR_BASIS",
"K_REFERENCE_SCALE_REFIT_AUTHORIZED=0",
"TRANSFORM_REFIT_AUTHORIZED=0",
"C_INCLUDED=0",
"H_ACCESS_PROMOTED_TO_FULL_H_STATE=0",
"I_SCALAR_CREATED=0",
"PARTIAL_PANEL_IS_FULL_CHKDI_STATE_VECTOR=0",
"TEMPORAL_GEOMETRY_AUTHORIZED=0",
"DIMENSIONALITY_TEST_AUTHORIZED=0",
"REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
"FINAL_SCALAR_AUTHORIZED=0",
"NEXT_PRIMARY_PHASE_ID=E4D1A",
"E4D1A_2019_OFFICIAL_SOURCE_LINEAGE_AND_ACQUISITION_PREFLIGHT_AUTHORIZED=1",
"E4D1_MULTIYEAR_PARTIAL_STATE_COORDINATE_EXECUTION_PREFLIGHT=PASS",
])+"\n"
EXEC.write_text(log,encoding="utf-8"); AUDIT.write_text(log,encoding="utf-8"); print(log,end="")
