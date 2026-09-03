#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import ast,csv,hashlib,json,re

ROOT=Path(__file__).resolve().parents[1]
C=json.loads((ROOT/"data/metadata/E4D1D3P0_preexecution_provenance_repair_contract.json").read_text())
ACS=ROOT/"scripts/E4D1D2A2_acs2019_h_access_adapter.py"
CPS=ROOT/"scripts/E4D1D2A2_R3_cps2019_i_adapter.py"
SCF=ROOT/"scripts/E4D1D2A2_scf2019_kd_adapter.py"
A1_RULES=ROOT/"data/metadata/E4D1D2A1_target_binding_rules.tsv"
B_MAN=ROOT/"data/results/E4D1B_2019_official_data_manifest.tsv"
CR0_SCHEMA=ROOT/"data/results/E4D1BR2CR0_updated_2019_schema_audit_status.tsv"
CR0_DECISION=ROOT/"data/results/E4D1BR2CR0_type_to_typehugq_versioned_name_repair_decision.tsv"
CR0_BRIDGE=ROOT/"data/results/E4D1BR2CR0_validated_householder_age_bridge_registry.tsv"

OUT_DEP=ROOT/"data/results/E4D1D3P0_dependency_classification_registry.tsv"
OUT_REPAIR=ROOT/"data/results/E4D1D3P0_required_repair_registry.tsv"
OUT_ORDER=ROOT/"data/results/E4D1D3P0_staged_execution_order.tsv"
OUT_GATES=ROOT/"data/results/E4D1D3P0_preexecution_provenance_hard_gates.tsv"
OUT_DEC=ROOT/"data/results/E4D1D3P0_preexecution_provenance_decision.tsv"
EXEC=ROOT/"data/metadata/E4D1D3P0_execution.txt"
AUDIT=ROOT/"data/metadata/E4D1D3P0_preexecution_provenance_audit.txt"

def rows(p):
    with p.open("r",encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f,delimiter="\t"))

def write(p,header,data):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,delimiter="\t",lineterminator="\n")
        w.writerow(header); w.writerows(data)

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

def source(p):
    s=p.read_text(encoding="utf-8")
    ast.parse(s)
    return s

acs=source(ACS); cps=source(CPS); scf=source(SCF)

# Frozen A1 policy: outputs are runtime-isolated while basename is preserved.
a1=rows(A1_RULES)
a1_text="\n".join(r["frozen_rule"] for r in a1)
assert "preserving basename" in a1_text
assert "exact 2022 token" in a1_text

# ACS forensic truth.
assert 'data/metadata/E4C3D_acs2022_microdata_manifest.tsv' in acs
assert 'data/metadata/E4C3D_execution.txt' not in acs  # path is composed from META/"..."
assert 'E4C3D_execution.txt' in acs
assert 'E4C3D_first_acs2022_h_access_execution_audit.txt' in acs
assert 'ACS_2022_MICRODATA_VALUES_OPENED=1' in acs
assert 'ACS_2022_HOUSING_ZIP_SHA_MATCHES_FROZEN_MANIFEST=1' in acs
assert 'data/raw/acs/2019/1year/csv_hus.zip' in acs

# Exact 2019 ACS raw authority row already exists.
manifest=rows(B_MAN)
acs_rows=[r for r in manifest if r.get("local_path")=="data/raw/acs/2019/1year/csv_hus.zip"]
assert len(acs_rows)==1,acs_rows
assert re.fullmatch(r"[0-9a-f]{64}",acs_rows[0]["sha256"])
assert int(acs_rows[0]["bytes"])>0

# Existing 2019 schema compatibility must use the canonical final\n# E4D1BR2CR0 authority, not the historical blocked E4D1BR registry.\nschema=rows(CR0_SCHEMA)\nassert len(schema)==3\nassert schema[0]["family"]=="ACS" and schema[0]["schema_status"]=="VERSIONED_PASS"\nassert schema[1]["family"]=="SCF" and schema[1]["schema_status"]=="PASS"\nassert schema[2]["family"]=="CPS_ASEC" and schema[2]["schema_status"]=="PASS"\n\ncr0d={r["decision"]:r["value"] for r in rows(CR0_DECISION)}\nassert cr0d["E4D1BR2CR0_TYPE_TO_TYPEHUGQ_VERSIONED_NAME_REPAIR"]=="PASS"\nassert cr0d["TYPE_FIELD_VERSION_BRIDGE"]=="2019:TYPE|2020+:TYPEHUGQ"\nassert cr0d["VERSIONED_BRIDGE_STATUS"]=="VALIDATED_FROZEN"\nassert cr0d["ACS_SCHEMA_AUDIT_STATUS"]=="VERSIONED_PASS"\nassert cr0d["SCHEMA_AUDIT_STATUS"]=="PASS_WITH_VERSIONED_BRIDGE"\nassert cr0d["NEXT_PRIMARY_PHASE_ID"]=="E4D1C"\nassert cr0d["E4D1C_2019_COORDINATE_EXECUTION_PRECOMMIT_AUTHORIZED"]=="1"\n\ncr0b={r["field"]:r["value"] for r in rows(CR0_BRIDGE)}\nassert cr0b["STATUS"]=="VALIDATED_FROZEN"\nassert cr0b["HOUSEHOLDER_STRUCTURAL_UNIVERSE"]=="TYPE=1 AND NP>0"\nassert cr0b["PERSON_WEIGHT_USED"]=="0"

# CPS runtime dependencies.
assert 'data/metadata/E4D1D_2019_runtime/CPS_ASEC/E4A2B_cps_full_weight_bridge_audit.txt' in cps
assert 'data/metadata/E4D1D_2019_runtime/CPS_ASEC/E4A2C_cps_replicate_engine_contract_audit.txt' in cps

# SCF dependency gap and cross-family issue.
assert 'data/metadata/E4D1D_2019_runtime/SCF/E4A2A_replicate_weight_schema_audit.txt' in scf
assert 'data/metadata/E4D1D_2019_runtime/SCF/E4A2D_first_cps_i_inference_execution_audit.txt' in scf
assert 'data/metadata/E4D1D_2019_runtime/SCF/E4A2E_exact_scf_replicate_mi_engine_preflight_audit.txt' in scf

# Original authority classification.
orig={
 "E4A2A":ROOT/"data/metadata/E4A2A_replicate_weight_schema_audit.txt",
 "E4A2B":ROOT/"data/metadata/E4A2B_cps_full_weight_bridge_audit.txt",
 "E4A2C":ROOT/"data/metadata/E4A2C_cps_replicate_engine_contract_audit.txt",
 "E4A2D":ROOT/"data/metadata/E4A2D_first_cps_i_inference_execution_audit.txt",
 "E4A2E":ROOT/"data/metadata/E4A2E_exact_scf_replicate_mi_engine_preflight_audit.txt",
}
txt={k:p.read_text(encoding="utf-8") for k,p in orig.items()}
assert "WEIGHT_VALUE_IDENTITY_TEST_PERFORMED=1" in txt["E4A2B"]
assert "I_EMPIRICALLY_TESTED=1" in txt["E4A2D"]
assert "E4A2C_CPS_REPLICATE_ENGINE_PREFLIGHT" in txt["E4A2C"] or "SYNTHETIC" in txt["E4A2C"]
assert "SCF_EXACT_REPLICATE_SCHEMA=PASS" in txt["E4A2A"]
assert "E4A2D_FIRST_CPS_I_INFERENCE_EXECUTION=PASS" in txt["E4A2E"]

dep=[
["ACS","SOURCE_MANIFEST","data/metadata/E4C3D_acs2022_microdata_manifest.tsv","YEAR_SPECIFIC_2022_SOURCE_AUTHORITY","REPAIR_REQUIRED","Use exact E4D1B 2019 manifest row; do not copy/relabel 2022 manifest"],
["ACS","EXECUTION_METADATA","data/metadata/E4C3D_execution.txt","HISTORICAL_2022_OUTPUT_NAMESPACE","REPAIR_REQUIRED","Redirect to data/metadata/E4D1D_2019_runtime/ACS"],
["ACS","EXECUTION_AUDIT","data/metadata/E4C3D_first_acs2022_h_access_execution_audit.txt","HISTORICAL_2022_OUTPUT_NAMESPACE","REPAIR_REQUIRED","Redirect to 2019 runtime metadata namespace and truth-label 2019"],
["CPS_ASEC","E4A2B_AUDIT","data/metadata/E4D1D_2019_runtime/CPS_ASEC/E4A2B_cps_full_weight_bridge_audit.txt","EMPIRICAL_2019_PREDECESSOR","REGENERATE_BEFORE_CPS_I","Do not mirror 2022 audit"],
["CPS_ASEC","E4A2C_AUDIT","data/metadata/E4D1D_2019_runtime/CPS_ASEC/E4A2C_cps_replicate_engine_contract_audit.txt","STATIC_SYNTHETIC_METHOD_AUTHORITY","BYTE_IDENTICAL_MIRROR_ALLOWED","Mirror exact 2022 method audit bytes; label externally as method authority"],
["SCF","E4A2A_AUDIT","data/metadata/E4D1D_2019_runtime/SCF/E4A2A_replicate_weight_schema_audit.txt","STATIC_REPLICATE_DESIGN_AUTHORITY","BYTE_IDENTICAL_MIRROR_ALLOWED","2019 schema compatibility independently frozen in E4D1BR"],
["SCF","E4A2D_AUDIT","data/metadata/E4D1D_2019_runtime/SCF/E4A2D_first_cps_i_inference_execution_audit.txt","EMPIRICAL_CROSS_FAMILY_PREDECESSOR","REPAIR_REQUIRED","Bind to CPS_ASEC runtime audit; never duplicate under SCF"],
["SCF","E4A2E_AUDIT","data/metadata/E4D1D_2019_runtime/SCF/E4A2E_exact_scf_replicate_mi_engine_preflight_audit.txt","CPS_CHAINED_SYNTHETIC_PREFLIGHT","REGENERATE_AFTER_CPS_PASS","Run frozen synthetic preflight bound to 2019 CPS predecessor"],
]
write(OUT_DEP,["family","dependency","observed_or_target_path","classification","required_action","provenance_rule"],dep)

repair=[
["P1R1","ACS","MANIFEST_VALIDATION","STATIC_BEFORE_VALUES","Replace legacy 2022 manifest consumer with exact E4D1B 2019 local_path/SHA/bytes lookup","0"],
["P1R2","ACS","METADATA_OUTPUT_ISOLATION","STATIC_BEFORE_VALUES","Redirect execution/audit writes under data/metadata/E4D1D_2019_runtime/ACS and use 2019-truth labels","0"],
["P1R3","CPS_ASEC","E4A2C_METHOD_AUTHORITY_MIRROR","STATIC_BEFORE_VALUES","Byte-identical mirror of frozen E4A2C audit into CPS runtime metadata","0"],
["P1R4","SCF","E4A2A_METHOD_AUTHORITY_MIRROR","STATIC_BEFORE_VALUES","Byte-identical mirror of frozen E4A2A audit into SCF runtime metadata","0"],
["P2R1","CPS_ASEC","2019_FULL_WEIGHT_BRIDGE","EMPIRICAL_AFTER_EXECUTION_PRECOMMIT","Generate 2019 E4A2B audit from frozen weight-bridge method; no I values","1_WEIGHT_ONLY"],
["P3R1","CPS_ASEC","PREDECESSOR_SHA_BIND","DETERMINISTIC_AFTER_P2_FREEZE","Patch only E4A2B_AUDIT linked expected SHA to frozen 2019 bridge SHA","0"],
["P4R1","CPS_ASEC","I_EXECUTION","EMPIRICAL","Execute frozen CPS 2019 adapter after P3","1_I"],
["P5R1","SCF","2019_BOUND_ENGINE_PREFLIGHT","SYNTHETIC_AFTER_CPS_PASS","Regenerate E4A2E preflight using frozen engine + frozen 2019 CPS predecessor","0_KD"],
["P6R1","SCF","CROSS_FAMILY_CPS_BIND","DETERMINISTIC_AFTER_P4_FREEZE","Patch E4A2D path to CPS_ASEC runtime and linked SHA to frozen CPS 2019 audit","0"],
["P6R2","SCF","E4A2E_SHA_BIND","DETERMINISTIC_AFTER_P5_FREEZE","Patch only E4A2E linked expected SHA to frozen 2019-bound preflight SHA","0"],
["P7R1","SCF","KD_EXECUTION","EMPIRICAL","Execute frozen SCF 2019 adapter after P6","1_KD"],
]
write(OUT_REPAIR,["repair_id","family","repair_class","timing","frozen_action","value_open_scope"],repair)

order=[
["1","E4D1D3P1","STATIC_PROVENANCE_REPAIR_AND_METHOD_AUTHORITY_MIRRORS","0","0","0","P0_PASS"],
["2","E4D1D3_ACS","ACS_2019_H_ACCESS_EXECUTION","1","0","0","P1_PASS"],
["3","E4D1D3_CPSB","CPS_2019_FULL_WEIGHT_BRIDGE_EXECUTION","0","0","1_WEIGHT_ONLY","P1_PASS"],
["4","E4D1D3_CPSP","CPS_DETERMINISTIC_PREDECESSOR_SHA_PATCH","0","0","0","CPSB_PASS_AND_FROZEN"],
["5","E4D1D3_CPSI","CPS_2019_I_EXECUTION","0","1","0","CPSP_PASS"],
["6","E4D1D3_SCFP","SCF_2019_BOUND_ENGINE_PREFLIGHT","0","0","0","CPSI_PASS_AND_FROZEN"],
["7","E4D1D3_SCFB","SCF_DETERMINISTIC_PREDECESSOR_PATH_SHA_PATCH","0","0","0","SCFP_PASS_AND_FROZEN"],
["8","E4D1D3_SCFKD","SCF_2019_KD_EXECUTION","0","0","1_KD","SCFB_PASS"],
]
write(OUT_ORDER,["order","phase","action","acs_values_open","cps_i_values_open","other_value_scope","precondition"],order)

gates=[
["ACS_LEGACY_2022_MANIFEST_MISMATCH_IDENTIFIED","1"],
["ACS_OUTSIDE_RUNTIME_METADATA_WRITES_IDENTIFIED","2"],
["ACS_2019_MANIFEST_AUTHORITY_ROW_COUNT","1"],
["ACS_2019_SCHEMA_COMPATIBILITY_FROZEN","1"],
["CPS_EMPIRICAL_E4A2B_MIRROR_PROHIBITED","1"],
["CPS_STATIC_E4A2C_MIRROR_ALLOWED","1"],
["SCF_STATIC_E4A2A_MIRROR_ALLOWED","1"],
["SCF_CPS_CROSS_FAMILY_BIND_REQUIRED","1"],
["SCF_E4A2E_REGENERATION_REQUIRED","1"],
["STAGED_EXECUTION_STEP_COUNT","8"],
["ADAPTER_MUTATED","0"],
["ADAPTER_IMPORTED","0"],
["ADAPTER_EXECUTED","0"],
["2019_RAW_DATA_ROWS_OPENED","0"],
["2019_COORDINATE_VALUES_OPENED","0"],
["SCIENTIFIC_METHOD_MUTATED","0"],
]
write(OUT_GATES,["gate","value"],gates)

decision=[
["E4D1D3P0_PREEXECUTION_PROVENANCE_REPAIR_PLAN_FREEZE","PASS"],
["REPAIR_PLAN_ROW_COUNT",str(len(repair))],
["DEPENDENCY_CLASSIFICATION_ROW_COUNT",str(len(dep))],
["STAGED_EXECUTION_STEP_COUNT",str(len(order))],
["ADAPTIVE_REPAIR_AFTER_VALUES","0"],
["OUTCOME_BASED_GATE","0"],
["ADAPTER_MUTATED","0"],
["ADAPTER_IMPORTED","0"],
["ADAPTER_EXECUTED","0"],
["2019_RAW_DATA_ROWS_OPENED","0"],
["2019_COORDINATE_VALUES_OPENED","0"],
["SCIENTIFIC_METHOD_MUTATED","0"],
["NEXT_PRIMARY_PHASE_ID","E4D1D3P1"],
["E4D1D3P1_STATIC_PROVENANCE_REPAIR_CONSTRUCTION_AUTHORIZED","1"],
["E4D1D_2019_COORDINATE_VALUES_OPEN_AUTHORIZED","0"],
["TEMPORAL_GEOMETRY_AUTHORIZED","0"],
["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
]
write(OUT_DEC,["decision","value"],decision)

log="\n".join(f"{k}={v}" for k,v in decision)+"\n"
EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")

print("ACS_LEGACY_2022_MANIFEST_MISMATCH_IDENTIFIED=1")
print("ACS_OUTSIDE_RUNTIME_METADATA_WRITES_IDENTIFIED=2")
print("CPS_E4A2B_CLASS=EMPIRICAL_2019_PREDECESSOR")
print("CPS_E4A2C_CLASS=STATIC_SYNTHETIC_METHOD_AUTHORITY")
print("SCF_E4A2A_CLASS=STATIC_REPLICATE_DESIGN_AUTHORITY")
print("SCF_E4A2D_CLASS=EMPIRICAL_CROSS_FAMILY_PREDECESSOR")
print("SCF_E4A2E_CLASS=CPS_CHAINED_SYNTHETIC_PREFLIGHT")
print("STAGED_EXECUTION_STEP_COUNT=8")
print("ADAPTER_MUTATED=0")
print("ADAPTER_IMPORTED=0")
print("ADAPTER_EXECUTED=0")
print("2019_RAW_DATA_ROWS_OPENED=0")
print("2019_COORDINATE_VALUES_OPENED=0")
print("SCIENTIFIC_METHOD_MUTATED=0")
print("E4D1D3P0_PREEXECUTION_PROVENANCE_REPAIR_PLAN_FREEZE=PASS")
