#!/usr/bin/env python3
from pathlib import Path
import csv, hashlib, json, re

ROOT=Path(__file__).resolve().parents[1]

CONTRACT=ROOT/"data/metadata/E4C3C_first_acs2022_h_access_execution_contract.json"
LINEAGE=ROOT/"data/metadata/E4C3C_frozen_input_lineage.tsv"
ACQ=ROOT/"data/metadata/E4C3C_acs2022_microdata_acquisition_contract.tsv"
EST=ROOT/"data/metadata/E4C3C_h_access_estimator_contract.tsv"

EXEC=ROOT/"data/metadata/E4C3C_execution.txt"
AUDIT=ROOT/"data/metadata/E4C3C_first_acs2022_h_access_execution_preflight_audit.txt"
SCHEMA=ROOT/"data/results/E4C3C_expected_execution_schema.tsv"
GATES=ROOT/"data/results/E4C3C_first_execution_hard_gates.tsv"

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for x in iter(lambda:f.read(1024*1024),b""):
            h.update(x)
    return h.hexdigest()

def tsv(p):
    with p.open("r",encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f,delimiter="\t"))

c=json.loads(CONTRACT.read_text(encoding="utf-8"))
if c["phase"]!="E4C3C":
    raise RuntimeError("wrong phase")
if c["microdata_state_during_E4C3C"]["download_authorized"]:
    raise RuntimeError("E4C3C must remain before microdata download")
if c["hard_boundaries"]["ACS_values_opened_in_E4C3C"]:
    raise RuntimeError("ACS values may not be opened")
if c["primary_estimand"]["name"]!="H_ACCESS_SPACE_ROOMS_PER_PERSON":
    raise RuntimeError("primary architecture mismatch")
if c["sensitivity_estimand"]["may_replace_primary_after_outcomes"]:
    raise RuntimeError("outcome-dependent primary switch prohibited")

for r in tsv(LINEAGE):
    p=ROOT/r["artifact"]
    if not p.exists() or sha(p)!=r["sha256"]:
        raise RuntimeError(f"frozen lineage mismatch: {r['artifact']}")

a={r["field"]:r["value"] for r in tsv(ACQ)}
e={r["field"]:r["value"] for r in tsv(EST)}

if a["OFFICIAL_ZIP_URL"]!="https://www2.census.gov/programs-surveys/acs/data/pums/2022/1-Year/csv_hus.zip":
    raise RuntimeError("wrong ACS official ZIP URL")
if a["GIT_TRACK_RAW_ZIP"]!="0":
    raise RuntimeError("national raw ZIP must not be forced into git")
if a["SHA256_FREEZE_AFTER_DOWNLOAD_BEFORE_ROW_PARSE"]!="1":
    raise RuntimeError("ZIP hash must freeze before row parse")
if e["PRIMARY_RECORD_FORMULA"]!="RMSP/NP":
    raise RuntimeError("primary formula mutation")
if e["REPLICATE_COUNT"]!="80":
    raise RuntimeError("replicate count mismatch")
if e["OUTCOME_GATE"]!="0":
    raise RuntimeError("outcome gate prohibited")

schema_rows=[
("microdata_manifest","data/metadata/E4C3D_acs2022_microdata_manifest.tsv","source hash + ZIP members before row parse"),
("point_estimates","data/results/E4C3D_h_access_point_estimates.tsv","8 primary + 8 sensitivity cohort estimates"),
("component_replicates","data/results/E4C3D_h_access_component_replicates.tsv","80 replicates per cohort/estimand"),
("comparisons","data/results/E4C3D_h_access_owner_renter_comparisons.tsv","4 age bands x primary/sensitivity"),
("difference_replicates","data/results/E4C3D_h_access_difference_replicates.tsv","direct renter-minus-owner replicates"),
("ratio_replicates","data/results/E4C3D_h_access_ratio_replicates.tsv","direct renter-divided-by-owner replicates"),
("inference_summary","data/results/E4C3D_h_access_inference_summary.tsv","point, SE, CI for components/differences/ratios"),
("execution_audit","data/metadata/E4C3D_execution.txt","hard-gate audit"),
]
with SCHEMA.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["artifact_type","path","role"])
    w.writerows(schema_rows)

gate_rows=[
("SOURCE_SHA_FROZEN_BEFORE_ROW_PARSE","REQUIRED"),
("ZIP_MEMBER_MANIFEST_FROZEN_BEFORE_ROW_PARSE","REQUIRED"),
("REQUIRED_COLUMNS_PRESENT_ALL_MEMBERS","REQUIRED"),
("PRIMARY_8_OF_8_COHORTS_NONEMPTY","REQUIRED"),
("PRIMARY_FULL_DENOMINATORS_POSITIVE_FINITE","REQUIRED"),
("PRIMARY_80_REPLICATE_DENOMINATORS_POSITIVE_FINITE","REQUIRED"),
("PRIMARY_POINTS_AND_REPLICATES_FINITE","REQUIRED"),
("PRIMARY_ESTIMAND_MUTATION_AFTER_VALUES","PROHIBITED"),
("OUTCOME_BASED_SAMPLE_MUTATION","PROHIBITED"),
("OWNER_RENTER_DIRECTION_GATE","PROHIBITED"),
("SIGNIFICANCE_GATE","PROHIBITED"),
("GEOMETRY_GATE","PROHIBITED"),
("H_SERVICE_H_ACCESS_AUTO_SCALAR","PROHIBITED"),
]
with GATES.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["gate","status"])
    w.writerows(gate_rows)

log="\n".join([
"================================================================================",
"ECONOMIC GEOMETRY RESEARCH — E4C3C",
"FIRST ACS 2022 H_ACCESS EXECUTION PREFLIGHT",
"================================================================================",
"RAW_SURVEY_DATA_READ=0",
"ACS_2022_MICRODATA_DOWNLOADED=0",
"ACS_2022_ZIP_MEMBERS_LISTED=0",
"ACS_2022_CSV_HEADERS_OPENED=0",
"ACS_2022_MICRODATA_VALUES_OPENED=0",
"NEW_HOUSING_ECONOMIC_VALUES_OPENED=0",
"OWNER_RENTER_OUTCOME_VALUES_OPENED=0",
"H_ACCESS_VALUES_COMPUTED=0",
"TRANSFORMED_VALUES_COMPUTED=0",
"GEOMETRY_PERFORMED=0",
"FROZEN_E4C3B_RESULTS_ONLY=1",
"ACS_2022_OFFICIAL_HOUSING_ZIP_URL_FROZEN=1",
"ACS_2022_RAW_ZIP_GIT_TRACKING=0",
"ZIP_SHA256_MUST_FREEZE_BEFORE_ROW_PARSE=1",
"ZIP_MEMBER_MANIFEST_MUST_FREEZE_BEFORE_ROW_PARSE=1",
"PRIMARY_H_ACCESS_ESTIMAND=H_ACCESS_SPACE_ROOMS_PER_PERSON",
"PRIMARY_H_ACCESS_FORMULA=RMSP_DIV_NP",
"PRIMARY_H_ACCESS_AGGREGATION=WGTP_WEIGHTED_MEAN_HOUSEHOLD_RATIO",
"PRIMARY_H_ACCESS_ORIENTATION=HIGHER_IS_BETTER",
"SENSITIVITY_H_ACCESS_ESTIMAND=H_ACCESS_SPACE_BEDROOMS_PER_PERSON",
"SENSITIVITY_MAY_REPLACE_PRIMARY_AFTER_OUTCOMES=0",
"PRIMARY_COHORT_COUNT_EXPECTED=8",
"ACS_OWNER_CODES=1,2",
"ACS_RENTER_CODE=3",
"ACS_NO_RENT_CODE_EXCLUDED=4",
"PERSON_LEVEL_JOIN_REQUIRED=0",
"ACS_FULL_WEIGHT=WGTP",
"ACS_REPLICATE_WEIGHTS=WGTP1-WGTP80",
"ACS_REPLICATE_COUNT=80",
"ACS_SDR_VARIANCE_FACTOR=4/80",
"REPLICATE_ELIGIBILITY_CHANGES_WITH_WEIGHT=0",
"REPLICATE_WEIGHT_CLIPPING_AUTHORIZED=0",
"WINSORIZATION_AUTHORIZED=0",
"OUTCOME_BASED_FILTERING_AUTHORIZED=0",
"RENTER_OWNER_DIFFERENCE=DIRECT_RENTER_MINUS_OWNER",
"RENTER_OWNER_RATIO=DIRECT_RENTER_DIV_OWNER",
"OWNER_RENTER_DIRECTION_USED_AS_SELECTION_GATE=0",
"STATISTICAL_SIGNIFICANCE_USED_AS_SELECTION_GATE=0",
"MAGNITUDE_USED_AS_SELECTION_GATE=0",
"GEOMETRY_USED_AS_SELECTION_GATE=0",
"H_SERVICE_H_ACCESS_PERSON_LEVEL_JOIN_AUTHORIZED=0",
"H_SERVICE_H_ACCESS_JOINT_COVARIANCE_AUTHORIZED=0",
"H_SERVICE_H_ACCESS_AUTO_SCALAR_AUTHORIZED=0",
"H_FULL_STATE_COMPLETE=0",
"FIVE_COMPONENT_STATE_VECTOR_AUTHORIZED=0",
"FIVE_COMPONENT_NORMALIZATION_AUTHORIZED=0",
"GEOMETRY_AUTHORIZED=0",
"DIMENSIONALITY_TEST_AUTHORIZED=0",
"REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
"FINAL_SCALAR_AUTHORIZED=0",
"E4C3C_FIRST_ACS_2022_H_ACCESS_EXECUTION_PREFLIGHT=PASS",
"E4C3D_FIRST_ACS_2022_H_ACCESS_EXECUTION_AUTHORIZED=1",
])+"\n"

EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
