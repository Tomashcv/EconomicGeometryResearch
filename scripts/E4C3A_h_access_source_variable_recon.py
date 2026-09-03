#!/usr/bin/env python3
from pathlib import Path
import csv, hashlib, json

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "data/metadata/E4C3A_h_access_source_variable_recon_contract.json"
LINEAGE = ROOT / "data/metadata/E4C3A_frozen_input_lineage.tsv"

EXEC = ROOT / "data/metadata/E4C3A_execution.txt"
AUDIT = ROOT / "data/metadata/E4C3A_h_access_source_variable_recon_audit.txt"
VARIABLES = ROOT / "data/results/E4C3A_h_access_variable_registry.tsv"
SOURCE_DECISION = ROOT / "data/results/E4C3A_h_access_source_decision.tsv"
BLOCKERS = ROOT / "data/results/E4C3A_h_access_remaining_blockers.tsv"

def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024), b""):
            h.update(c)
    return h.hexdigest()

def read_tsv(path):
    with path.open("r",encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f,delimiter="\t"))

c=json.loads(CONTRACT.read_text(encoding="utf-8"))
if c["phase"]!="E4C3A":
    raise RuntimeError("wrong phase")
if c["hard_boundaries"]["H_ACCESS_selected"]:
    raise RuntimeError("H_ACCESS selection prohibited")
if c["primary_source_recon"]["H_ACCESS_variable_selected"]:
    raise RuntimeError("source recon may not select H_ACCESS variable")

for r in read_tsv(LINEAGE):
    p=ROOT/r["artifact"]
    if not p.exists() or sha256(p)!=r["sha256"]:
        raise RuntimeError(f"lineage mismatch: {r['artifact']}")

variable_rows = [
    ("ACS_2022","COHORT","HHLDRAGEP","age of householder","PRIMARY_READY","0"),
    ("ACS_2022","COHORT","TEN","tenure","PRIMARY_READY_CODES_PENDING","0"),
    ("ACS_2022","INFERENCE","WGTP","housing unit weight","PRIMARY_READY","0"),
    ("ACS_2022","INFERENCE","WGTP1-WGTP80","80 housing replicate weights","PRIMARY_READY","0"),
    ("ACS_2022","AFFORDABILITY","GRPIP","gross rent percent of household income","CANDIDATE_HARMONIZATION_PENDING","0"),
    ("ACS_2022","AFFORDABILITY","OCPIP","owner costs percent of household income","CANDIDATE_HARMONIZATION_PENDING","0"),
    ("ACS_2022","AFFORDABILITY","HINCP","household income","DENOMINATOR_SEMANTICS_PENDING","0"),
    ("ACS_2022","SPACE","NP","persons in household","CANDIDATE_READY_METADATA_ONLY","0"),
    ("ACS_2022","SPACE","RMSP","number of rooms","CANDIDATE_READY_METADATA_ONLY","0"),
    ("ACS_2022","SPACE","BDSP","number of bedrooms","CANDIDATE_READY_METADATA_ONLY","0"),
    ("ACS_2022","ADEQUACY","PLM","complete plumbing facilities","LIMITED_ADEQUACY_CANDIDATE","0"),
    ("ACS_2022","ADEQUACY","BATH","bathtub or shower","LIMITED_ADEQUACY_CANDIDATE","0"),
    ("ACS_2022","ADEQUACY","KIT","complete kitchen facilities","LIMITED_ADEQUACY_CANDIDATE","0"),
    ("ACS_2022","ADEQUACY","SINK","sink with faucet","LIMITED_ADEQUACY_CANDIDATE","0"),
    ("ACS_2022","ADEQUACY","STOV","stove or range","LIMITED_ADEQUACY_CANDIDATE","0"),
    ("ACS_2022","STABILITY","MV","when moved into dwelling","WEAK_PROXY_NOT_SECURITY","0"),
    ("ACS_2022","STABILITY","MIG","mobility status one year ago","WEAK_PROXY_NOT_SECURITY","0"),
    ("AHS_2023","ADEQUACY","ZADEQ","recoded housing adequacy","SECONDARY_YEAR_MISMATCH","0"),
    ("AHS_2023","INSECURITY","HIAFFORD","difficulty affording housing payments","SECONDARY_YEAR_MISMATCH","0"),
    ("AHS_2023","INSECURITY","HIBEHINDFRQ","months missed housing payments","SECONDARY_YEAR_MISMATCH","0"),
    ("AHS_2023","INSECURITY","HIMOVFRC","worry about forced move","SECONDARY_YEAR_MISMATCH","0"),
    ("AHS_2023","INSECURITY","HIWORRY","current worry about forced move","SECONDARY_YEAR_MISMATCH","0"),
    ("AHS_2023","STABILITY","HINUMOVE","moves in last 12 months","SECONDARY_YEAR_MISMATCH","0"),
]

with VARIABLES.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["source","family","variable","semantic_role","status","values_authorized"])
    w.writerows(variable_rows)

source_rows = [
    ("PRIMARY_NEXT_METADATA_AUDIT_SOURCE","ACS_2022_1YEAR_PUMS"),
    ("PRIMARY_SOURCE_YEAR","2022"),
    ("PRIMARY_SOURCE_SELECTION_IS_H_ACCESS_SELECTION","0"),
    ("AHS_2023_STATUS","SECONDARY_RICH_HOUSING_RECON"),
    ("AHS_2023_PRIMARY_YEAR_ALIGNMENT","0"),
    ("ACS_HOUSEHOLDER_AGE_DIRECT_FIELD","HHLDRAGEP"),
    ("ACS_TENURE_DIRECT_FIELD","TEN"),
    ("PERSON_LEVEL_JOIN_REQUIRED_FOR_ACS_HOUSEHOLDER_COHORT","0"),
    ("ACS_FULL_WEIGHT","WGTP"),
    ("ACS_REPLICATE_WEIGHT_COUNT","80"),
    ("ACS_SDR_VARIANCE_FACTOR","4/80"),
    ("H_ACCESS_SELECTED","0"),
]
with SOURCE_DECISION.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["decision","value"])
    w.writerows(source_rows)

blocker_rows = [
    ("ACS_TEN_CODE_MAPPING","REQUIRES_EXACT_2022_DICTIONARY_FREEZE"),
    ("GRPIP_OCPIP_COMMON_SEMANTIC","HARMONIZATION_CONTRACT_REQUIRED"),
    ("AFFORDABILITY_DENOMINATOR","OVERLAP_AND_ZERO_NEGATIVE_INCOME_POLICY_REQUIRED"),
    ("CROWDING_FORMULA_OR_THRESHOLD","PRECOMMIT_REQUIRED"),
    ("LIMITED_ADEQUACY_COMPOSITE","PRECOMMIT_REQUIRED_IF_RETAINED"),
    ("AHS_2023_YEAR_ALIGNMENT","DECISION_REQUIRED_IF_AHS_RETAINED"),
    ("AHS_VARIANCE_METHOD","REQUIRED_IF_AHS_RETAINED"),
    ("ALL_8_COHORT_CELL_SUPPORT","MUST_BE_CHECKED_ONLY_AFTER_ESTIMAND_FREEZE"),
]
with BLOCKERS.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["blocker","status"])
    w.writerows(blocker_rows)

log="\n".join([
"================================================================================",
"ECONOMIC GEOMETRY RESEARCH — E4C3A",
"H_ACCESS SOURCE + VARIABLE RECON",
"================================================================================",
"RAW_SURVEY_DATA_READ=0",
"NEW_HOUSING_ECONOMIC_VALUES_OPENED=0",
"OWNER_RENTER_OUTCOME_VALUES_OPENED=0",
"H_COORDINATE_VALUES_COMPUTED=0",
"TRANSFORMED_VALUES_COMPUTED=0",
"GEOMETRY_PERFORMED=0",
"OFFICIAL_SOURCE_METADATA_RECON=1",
"PRIMARY_H_ACCESS_RECON_SOURCE=ACS_2022_1YEAR_PUMS",
"PRIMARY_SOURCE_YEAR=2022",
"PRIMARY_SOURCE_SELECTION_IS_H_ACCESS_SELECTION=0",
"ACS_HOUSEHOLDER_AGE_DIRECT_FIELD=HHLDRAGEP",
"ACS_TENURE_DIRECT_FIELD=TEN",
"ACS_PERSON_LEVEL_JOIN_REQUIRED=0",
"ACS_FULL_WEIGHT=WGTP",
"ACS_REPLICATE_WEIGHT_COUNT=80",
"ACS_SDR_VARIANCE_FACTOR=4/80",
"ACS_AFFORDABILITY_VARIABLES_FOUND=GRPIP,OCPIP",
"ACS_CROWDING_VARIABLES_FOUND=NP,RMSP,BDSP",
"ACS_LIMITED_ADEQUACY_VARIABLES_FOUND=PLM,BATH,KIT,SINK,STOV",
"ACS_STABILITY_DIRECT_INVOLUNTARY_SECURITY_MEASURE_FOUND=0",
"AHS_2023_RICH_ADEQUACY_INSECURITY_VARIABLES_FOUND=1",
"AHS_2023_PRIMARY_YEAR_ALIGNMENT=0",
"H_ACCESS_SELECTED=0",
"H_COORDINATE_VALUES_AUTHORIZED=0",
"FIVE_COMPONENT_STATE_VECTOR_AUTHORIZED=0",
"FIVE_COMPONENT_NORMALIZATION_AUTHORIZED=0",
"GEOMETRY_AUTHORIZED=0",
"DIMENSIONALITY_TEST_AUTHORIZED=0",
"REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
"FINAL_SCALAR_AUTHORIZED=0",
"OWNER_RENTER_DIRECTION_USED_AS_SELECTION_GATE=0",
"STATISTICAL_SIGNIFICANCE_USED_AS_SELECTION_GATE=0",
"GEOMETRY_USED_AS_SELECTION_GATE=0",
"E4C3A_H_ACCESS_SOURCE_VARIABLE_RECON=PASS",
"E4C3B_ACS_2022_METADATA_HARMONIZATION_PREFLIGHT_AUTHORIZED=1",
])+"\n"
EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
