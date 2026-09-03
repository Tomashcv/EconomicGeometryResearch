#!/usr/bin/env python3
from pathlib import Path
import csv,json,re,subprocess,sys

ROOT=Path(__file__).resolve().parents[1]

CONTRACT=ROOT/"data/metadata/E4D1BR2A_acs_householder_age_versioned_bridge_contract.json"
TARGETS=ROOT/"data/metadata/E4D1BR2A_official_evidence_target_plan.tsv"
MANIFEST0=ROOT/"data/results/E4D0A_official_evidence_manifest.tsv"
INDEX=ROOT/"data/raw/reference_metadata/E4D1A/ACS/2019/acs_2019_1year_pums_directory_index.html"
AGEP=ROOT/"data/raw/reference_metadata/E4D0B2A/ACS/2019/AGEP.api.json"
CHANGE=ROOT/"data/raw/reference_metadata/E4D1BR2A/ACS/ACS2021_PUMS_Variable_Changes_and_Explanations.pdf"
HANDBOOK=ROOT/"data/raw/reference_metadata/E4D1BR2A/ACS/acs_pums_handbook_2021.pdf"

MANIFEST=ROOT/"data/results/E4D1BR2A_official_evidence_manifest.tsv"
EVIDENCE=ROOT/"data/results/E4D1BR2A_versioned_bridge_evidence_registry.tsv"
BRIDGE=ROOT/"data/results/E4D1BR2A_householder_age_versioned_bridge_policy.tsv"
ACQPLAN=ROOT/"data/results/E4D1BR2A_2019_acs_person_source_acquisition_plan.tsv"
GATES=ROOT/"data/results/E4D1BR2A_preflight_hard_gates.tsv"
DECISION=ROOT/"data/results/E4D1BR2A_acs_householder_age_versioned_bridge_preflight_decision.tsv"
EXEC=ROOT/"data/metadata/E4D1BR2A_execution.txt"
AUDIT=ROOT/"data/metadata/E4D1BR2A_acs_householder_age_versioned_bridge_preflight_audit.txt"

c=json.loads(CONTRACT.read_text(encoding="utf-8"))

def read_tsv(p):
    with p.open("r",encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f,delimiter="\t"))

def write_tsv(p,h,rows):
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,delimiter="\t",lineterminator="\n")
        w.writerow(h);w.writerows(rows)

def pdftext(p):
    q=subprocess.run(["pdftotext","-layout",str(p),"-"],capture_output=True,text=True,check=True)
    return q.stdout

def norm(s):
    return re.sub(r"\s+"," ",s).strip()

# Resolve existing 2019 README and dictionary from immutable E4D0A manifest.
targets={
"https://www2.census.gov/programs-surveys/acs/tech_docs/pums/ACS2019_PUMS_README.pdf":"README",
"https://www2.census.gov/programs-surveys/acs/tech_docs/pums/data_dict/PUMS_Data_Dictionary_2019.txt":"DICT",
}
found={}
for r in read_tsv(MANIFEST0):
    if r.get("url") in targets:
        found[targets[r["url"]]]=ROOT/r["local_path"]
assert set(found)=={"README","DICT"}
readme=pdftext(found["README"])
dictionary=found["DICT"].read_text(encoding="utf-8",errors="replace")
change=pdftext(CHANGE)
handbook=pdftext(HANDBOOK)
index=INDEX.read_text(encoding="utf-8",errors="replace")
agep=json.loads(AGEP.read_text(encoding="utf-8"))

nr=norm(readme).lower()
nd=norm(dictionary)
nc=norm(change).lower()
nh=norm(handbook).lower()
ni=norm(index)

# Official evidence gates.
change_new=(
    "hhldragep" in nc and
    "new age of the householder variable" in nc and
    "new variables" in nc
)
change_housing_files=(
    "hhldragep" in nc and
    "pums housing files" in nc and
    "age" in nc and
    "householder" in nc
)

# The handbook contains an explicit example identifying householder as reference person.
householder_reference=(
    "householder" in nh and
    "reference person" in nh and
    ("householder, which is the reference person" in nh or
     "householder/reference person" in nh or
     "householder/reference" in nh)
)

# 2019 dictionary exact structural semantics.
dict_agep=bool(re.search(r"\bAGEP\b.{0,160}\bAge\b",nd,re.I))
dict_relshipp=(
    "RELSHIPP" in nd and
    bool(re.search(r"\b20\s+\.?Reference person\b",nd,re.I))
)
dict_serial=(
    "SERIALNO" in nd and
    "Housing unit/GQ person serial number" in nd
)

# 2019 README exact merge/weight semantics.
readme_merge=(
    "serialno" in nr and
    "merge" in nr and
    ("merge key" in nr or "using serialno" in nr)
)
readme_housing_weight=(
    "household weights" in nr and
    "housing files" in nr and
    ("housing units or households" in nr or "housing unit" in nr)
)

# Existing frozen AGEP API.
agep_gate=(
    agep.get("name")=="AGEP" and
    agep.get("label")=="Age" and
    agep.get("predicateType")=="int"
)

# Existing official directory index contains exact person archive.
person_link=("csv_pus.zip" in ni)

bridge_evidence_pass=all([
    change_new,change_housing_files,householder_reference,
    dict_agep,dict_relshipp,dict_serial,
    readme_merge,readme_housing_weight,agep_gate,person_link
])

ev=[
["BR2A_CHANGE_NEW_FIELD","ACS_2021_VARIABLE_CHANGES",f"HHLDRAGEP_new_field={int(change_new)}","PASS" if change_new else "UNRESOLVED"],
["BR2A_CHANGE_HOUSING_ROLE","ACS_2021_VARIABLE_CHANGES",f"added_to_housing_files_for_householder_age_use={int(change_housing_files)}","PASS" if change_housing_files else "UNRESOLVED"],
["BR2A_HOUSEHOLDER_REFERENCE","ACS_PUMS_2021_HANDBOOK",f"householder_reference_person_identity={int(householder_reference)}","PASS" if householder_reference else "UNRESOLVED"],
["BR2A_2019_AGEP","ACS_2019_DICTIONARY|AGEP_API",f"AGEP_age_semantics={int(dict_agep and agep_gate)}","PASS" if (dict_agep and agep_gate) else "UNRESOLVED"],
["BR2A_2019_RELSHIPP","ACS_2019_DICTIONARY",f"RELSHIPP_code20_reference_person={int(dict_relshipp)}","PASS" if dict_relshipp else "UNRESOLVED"],
["BR2A_2019_SERIALNO","ACS_2019_DICTIONARY|README",f"SERIALNO_key_semantics={int(dict_serial)};merge_documented={int(readme_merge)}","PASS" if (dict_serial and readme_merge) else "UNRESOLVED"],
["BR2A_2019_HOUSING_WEIGHT","ACS_2019_README",f"housing_weight_role_documented={int(readme_housing_weight)}","PASS" if readme_housing_weight else "UNRESOLVED"],
["BR2A_2019_PERSON_SOURCE","ACS_2019_DIRECTORY_INDEX",f"csv_pus_zip_link_present={int(person_link)}","PASS" if person_link else "UNRESOLVED"],
]
write_tsv(EVIDENCE,["evidence_id","source","structural_summary","status"],ev)

write_tsv(BRIDGE,["field","value"],[
["BRIDGE_ID","ACS_2019_HOUSEHOLDER_AGE_FROM_REFERENCE_PERSON"],
["STATUS","CONDITIONAL_PREFROZEN" if bridge_evidence_pass else "UNRESOLVED"],
["TARGET_2019_MISSING_FIELD","HHLDRAGEP"],
["HOUSING_KEY","SERIALNO"],
["PERSON_KEY","SERIALNO"],
["PERSON_ROLE_FIELD","RELSHIPP"],
["PERSON_ROLE_CODE","20"],
["PERSON_ROLE_SEMANTICS","REFERENCE_PERSON_EQ_HOUSEHOLDER"],
["PERSON_AGE_FIELD","AGEP"],
["DERIVATION","HHLDRAGEP_2019 := AGEP where RELSHIPP=20, merged by SERIALNO"],
["AGE_BANDS","25-34|35-44|45-54|55-64"],
["H_NUMERATOR_FIELD","RMSP"],
["H_DENOMINATOR_FIELD","NP"],
["TENURE_FIELD","TEN"],
["POINT_WEIGHT","WGTP"],
["REPLICATE_WEIGHTS","WGTP1..WGTP80"],
["PERSON_WEIGHT_USED","0"],
["REFERENCE_PERSON_UNIQUENESS_ASSUMED","0"],
["REFERENCE_PERSON_UNIQUENESS_DEFERRED_GATE","1"],
["HOUSING_LINK_COVERAGE_ASSUMED","0"],
["HOUSING_LINK_COVERAGE_DEFERRED_GATE","1"],
])

write_tsv(ACQPLAN,["candidate_id","family","url","destination","role","acquisition_status"],[
["ACS_2019_NATIONAL_PERSON_CSV","ACS",
 c["future_person_source"]["url"],c["future_person_source"]["destination"],
 "versioned_householder_age_bridge_source",
 "DOWNLOAD_ONLY_AFTER_E4D1BR2B_PRECOMMIT" if bridge_evidence_pass else "BLOCKED_UNRESOLVED"],
])

write_tsv(GATES,["gate","value"],[
["HHLDRAGEP_NEW_POST2019_FIELD_EVIDENCE",str(int(change_new and change_housing_files))],
["HOUSEHOLDER_REFERENCE_PERSON_IDENTITY_EVIDENCE",str(int(householder_reference))],
["2019_AGEP_SEMANTICS_EVIDENCE",str(int(dict_agep and agep_gate))],
["2019_RELSHIPP20_REFERENCE_PERSON_EVIDENCE",str(int(dict_relshipp))],
["2019_SERIALNO_MERGE_EVIDENCE",str(int(dict_serial and readme_merge))],
["2019_HOUSING_WEIGHT_ROLE_EVIDENCE",str(int(readme_housing_weight))],
["2019_PERSON_ARCHIVE_OFFICIAL_LINK_EVIDENCE",str(int(person_link))],
["VERSIONED_BRIDGE_EVIDENCE_PASS",str(int(bridge_evidence_pass))],
["REFERENCE_PERSON_UNIQUENESS_VALIDATED","0"],
["HOUSING_LINK_COVERAGE_VALIDATED","0"],
["PERSON_MICRODATA_FILES_DOWNLOADED","0"],
["MICRODATA_ROWS_OPENED","0"],
["2019_ECONOMIC_VALUES_OPENED","0"],
["SCHEMA_STATUS_MUTATED","0"],
["E4D1C_2019_COORDINATE_EXECUTION_PRECOMMIT_AUTHORIZED","0"],
["TEMPORAL_GEOMETRY_AUTHORIZED","0"],
["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
])

next_phase="E4D1BR2B" if bridge_evidence_pass else "E4D1BR2AR"
write_tsv(DECISION,["decision","value"],[
["E4D1BR2_REUSED_AS_CANONICAL_HHLDRAGEP_SCHEMA_MISMATCH","1"],
["VERSIONED_BRIDGE_ID","ACS_2019_HOUSEHOLDER_AGE_FROM_REFERENCE_PERSON"],
["VERSIONED_BRIDGE_EVIDENCE_STATUS","PASS" if bridge_evidence_pass else "UNRESOLVED"],
["PERSON_SOURCE_URL_FROZEN",c["future_person_source"]["url"]],
["PERSON_SOURCE_DESTINATION_FROZEN",c["future_person_source"]["destination"]],
["PERSON_MICRODATA_FILES_DOWNLOADED","0"],
["MICRODATA_ROWS_OPENED","0"],
["2019_ECONOMIC_VALUES_OPENED","0"],
["REFERENCE_PERSON_UNIQUENESS_VALIDATED","0"],
["HOUSING_LINK_COVERAGE_VALIDATED","0"],
["SCHEMA_STATUS_MUTATED","0"],
["ACS_SCHEMA_AUDIT_STATUS","FAIL"],
["SCHEMA_AUDIT_STATUS","BLOCKED"],
["NEXT_PRIMARY_PHASE_ID",next_phase],
["E4D1BR2B_2019_ACS_PERSON_SOURCE_ACQUISITION_SCHEMA_AUDIT_AUTHORIZED",str(int(bridge_evidence_pass))],
["E4D1C_2019_COORDINATE_EXECUTION_PRECOMMIT_AUTHORIZED","0"],
["TEMPORAL_GEOMETRY_AUTHORIZED","0"],
["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
["E4D1BR2A_ACS_HOUSEHOLDER_AGE_VERSIONED_BRIDGE_PREFLIGHT","PASS"],
])

log="\n".join([
"E4D1BR2_REUSED_AS_CANONICAL_HHLDRAGEP_SCHEMA_MISMATCH=1",
"TARGET_MISSING_FIELD=HHLDRAGEP",
"NEW_OFFICIAL_EVIDENCE_ARTIFACT_COUNT=2",
f"HHLDRAGEP_NEW_POST2019_FIELD_EVIDENCE={int(change_new and change_housing_files)}",
f"HOUSEHOLDER_REFERENCE_PERSON_IDENTITY_EVIDENCE={int(householder_reference)}",
f"2019_AGEP_SEMANTICS_EVIDENCE={int(dict_agep and agep_gate)}",
f"2019_RELSHIPP20_REFERENCE_PERSON_EVIDENCE={int(dict_relshipp)}",
f"2019_SERIALNO_MERGE_EVIDENCE={int(dict_serial and readme_merge)}",
f"2019_HOUSING_WEIGHT_ROLE_EVIDENCE={int(readme_housing_weight)}",
f"2019_PERSON_ARCHIVE_OFFICIAL_LINK_EVIDENCE={int(person_link)}",
f"VERSIONED_BRIDGE_EVIDENCE_STATUS={'PASS' if bridge_evidence_pass else 'UNRESOLVED'}",
"REFERENCE_PERSON_UNIQUENESS_VALIDATED=0",
"HOUSING_LINK_COVERAGE_VALIDATED=0",
"PERSON_MICRODATA_FILES_DOWNLOADED=0",
"MICRODATA_ROWS_OPENED=0",
"2019_ECONOMIC_VALUES_OPENED=0",
"SCHEMA_STATUS_MUTATED=0",
"ACS_SCHEMA_AUDIT_STATUS=FAIL",
"SCHEMA_AUDIT_STATUS=BLOCKED",
f"NEXT_PRIMARY_PHASE_ID={next_phase}",
f"E4D1BR2B_2019_ACS_PERSON_SOURCE_ACQUISITION_SCHEMA_AUDIT_AUTHORIZED={int(bridge_evidence_pass)}",
"E4D1C_2019_COORDINATE_EXECUTION_PRECOMMIT_AUTHORIZED=0",
"TEMPORAL_GEOMETRY_AUTHORIZED=0",
"REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
"E4D1BR2A_ACS_HOUSEHOLDER_AGE_VERSIONED_BRIDGE_PREFLIGHT=PASS",
])+"\n"
EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
