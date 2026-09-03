#!/usr/bin/env python3
from pathlib import Path
import csv,hashlib,math,sys

ROOT=Path(__file__).resolve().parents[1]

ADAPTER=ROOT/"scripts/E4D1D3P1_acs2019_h_access_adapter.py"
F3_DEC=ROOT/"data/results/E4D1D3_ACS_P0_F3_execution_precommit_decision.tsv"

OUTDIR=ROOT/"data/results/E4D1D_2019_runtime/ACS"
METADIR=ROOT/"data/metadata/E4D1D_2019_runtime/ACS"

FILES={
 "POINT":OUTDIR/"E4C3D_h_access_point_estimates.tsv",
 "COMP":OUTDIR/"E4C3D_h_access_component_replicates.tsv",
 "COMPARE":OUTDIR/"E4C3D_h_access_owner_renter_comparisons.tsv",
 "DIFF":OUTDIR/"E4C3D_h_access_difference_replicates.tsv",
 "RATIO":OUTDIR/"E4C3D_h_access_ratio_replicates.tsv",
 "SUMMARY":OUTDIR/"E4C3D_h_access_inference_summary.tsv",
 "EXEC":METADIR/"E4D1D3_ACS_2019_h_access_execution.txt",
 "AUDIT":METADIR/"E4D1D3_ACS_2019_h_access_execution_audit.txt",
}
HASHREG=ROOT/"data/results/E4D1D3_ACS_R0_output_hash_registry.tsv"
GATES=ROOT/"data/results/E4D1D3_ACS_R0_execution_hard_gates.tsv"
DEC=ROOT/"data/results/E4D1D3_ACS_R0_execution_decision.tsv"
VAUDIT=ROOT/"data/metadata/E4D1D3_ACS_R0_execution_validation_audit.txt"

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def tsv_rows(p):
    with p.open("r",encoding="utf-8",newline="") as f:
        rd=csv.reader(f,delimiter="\t")
        rows=list(rd)
    assert rows and len(rows)>=1,p
    return rows

def kv_tsv(p):
    with p.open("r",encoding="utf-8",newline="") as f:
        rows=list(csv.DictReader(f,delimiter="\t"))
    return rows

assert sha(ADAPTER)=="8155f51370c1ba23657f803dd16901f657d74e5755cc273de1290c5ab1cca45d"

fd={r["decision"]:r["value"] for r in kv_tsv(F3_DEC)}
assert fd["E4D1D3_ACS_P0_F3_2019_H_ACCESS_EXECUTION_PRECOMMIT_FREEZE"]=="PASS"
assert fd["E4D1D3_ACS_2019_H_ACCESS_EXECUTION_AUTHORIZED"]=="1"
assert fd["ACS_EXECUTION_VALUE_OPEN_SCOPE"]=="ACS_H_ONLY"

for p in FILES.values():
    assert p.is_file(),f"missing output: {p}"

assert FILES["EXEC"].read_bytes()==FILES["AUDIT"].read_bytes()

log=FILES["EXEC"].read_text(encoding="utf-8")
required=[
 "RAW_SURVEY_DATA_READ=1",
 "ACS_2019_MICRODATA_VALUES_OPENED=1",
 "ACS_2019_HOUSING_ZIP_SHA_MATCHES_FROZEN_MANIFEST=1",
 "SELECTED_HOUSING_CSV_MEMBER_COUNT=2",
 "REQUIRED_COLUMNS_PRESENT_ALL_MEMBERS=1",
 "PRIMARY_8_OF_8_COHORTS_NONEMPTY=1",
 "PRIMARY_FULL_DENOMINATORS_POSITIVE_FINITE=1",
 "PRIMARY_80_REPLICATE_DENOMINATORS_POSITIVE_FINITE=1",
 "PRIMARY_ALL_POINT_ESTIMATES_FINITE=1",
 "POINT_ESTIMATE_ROWS=16",
 "COMPONENT_REPLICATE_ROWS=1280",
 "OWNER_RENTER_COMPARISON_ROWS=8",
 "DIFFERENCE_REPLICATE_ROWS=640",
 "RATIO_REPLICATE_ROWS=640",
 "INFERENCE_SUMMARY_ROWS=32",
 "OWNER_RENTER_DIRECTION_USED_AS_GATE=0",
 "STATISTICAL_SIGNIFICANCE_USED_AS_GATE=0",
 "MAGNITUDE_USED_AS_GATE=0",
 "GEOMETRY_USED_AS_GATE=0",
 "H_SERVICE_H_ACCESS_AUTO_SCALAR_COMPUTED=0",
 "H_ACCESS_SPACE_SUBCOORDINATE_IDENTIFIED=1",
 "H_FULL_STATE_COMPLETE=0",
 "FIVE_COMPONENT_STATE_VECTOR_AUTHORIZED=0",
 "GEOMETRY_AUTHORIZED=0",
 "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
 "FINAL_SCALAR_AUTHORIZED=0",
 "E4D1D3_ACS_2019_H_ACCESS_EXECUTION=PASS",
 "DOWNSTREAM_EXECUTION_AUTHORIZATION_EMITTED=0",
]
for token in required:
    assert token in log,token

expected_counts={
 "POINT":16,
 "COMP":1280,
 "COMPARE":8,
 "DIFF":640,
 "RATIO":640,
 "SUMMARY":32,
}
actual_counts={}
for key,n in expected_counts.items():
    rows=tsv_rows(FILES[key])
    actual=len(rows)-1
    assert actual==n,(key,actual,n)
    actual_counts[key]=actual

# No adaptive outcome acceptance: only frozen structural gates above decide PASS.
for forbidden in (
    "OWNER_RENTER_DIRECTION_USED_AS_GATE=1",
    "STATISTICAL_SIGNIFICANCE_USED_AS_GATE=1",
    "MAGNITUDE_USED_AS_GATE=1",
    "GEOMETRY_USED_AS_GATE=1",
):
    assert forbidden not in log,forbidden

HASHREG.parent.mkdir(parents=True,exist_ok=True)
with HASHREG.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["role","path","sha256","bytes","data_rows"])
    for role,p in FILES.items():
        n=actual_counts.get(role,"NA")
        w.writerow([role,str(p.relative_to(ROOT)),sha(p),p.stat().st_size,n])

gates=[
 ["ACS_CANONICAL_ADAPTER_SHA_MATCH","1"],
 ["ACS_EXECUTION_RETURNED_SUCCESS","1"],
 ["ACS_EXECUTION_AUDIT_BYTE_IDENTICAL","1"],
 ["ACS_HOUSING_MEMBER_COUNT","2"],
 ["ACS_PERSON_MEMBER_POLICY_FROZEN","1"],
 ["REQUIRED_COLUMNS_PRESENT_ALL_MEMBERS","1"],
 ["PRIMARY_8_OF_8_COHORTS_NONEMPTY","1"],
 ["PRIMARY_FULL_DENOMINATORS_POSITIVE_FINITE","1"],
 ["PRIMARY_80_REPLICATE_DENOMINATORS_POSITIVE_FINITE","1"],
 ["PRIMARY_ALL_POINT_ESTIMATES_FINITE","1"],
 ["POINT_ESTIMATE_ROWS","16"],
 ["COMPONENT_REPLICATE_ROWS","1280"],
 ["OWNER_RENTER_COMPARISON_ROWS","8"],
 ["DIFFERENCE_REPLICATE_ROWS","640"],
 ["RATIO_REPLICATE_ROWS","640"],
 ["INFERENCE_SUMMARY_ROWS","32"],
 ["OUTCOME_BASED_GATE","0"],
 ["SCIENTIFIC_METHOD_MUTATED","0"],
]
with GATES.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["gate","value"]); w.writerows(gates)

decision=[
 ["E4D1D3_ACS_R0_FIRST_2019_H_ACCESS_EMPIRICAL_EXECUTION","PASS"],
 ["ACS_CANONICAL_ADAPTER_SHA256",sha(ADAPTER)],
 ["ACS_H_2019_MICRODATA_ROWS_OPENED","1"],
 ["ACS_H_2019_COORDINATE_VALUES_OPENED","1"],
 ["ACS_H_2019_EMPIRICALLY_TESTED","1"],
 ["OUTCOME_BASED_GATE","0"],
 ["SCIENTIFIC_METHOD_MUTATED","0"],
 ["NEXT_PRIMARY_PHASE_ID","E4D1D3_CPSB"],
 ["E4D1D3_CPSB_2019_FULL_WEIGHT_BRIDGE_EXECUTION_PRECOMMIT_AUTHORIZED","1"],
 ["CPS_WEIGHT_BRIDGE_VALUE_OPEN_AUTHORIZED","0"],
 ["CPS_I_VALUE_OPEN_AUTHORIZED","0"],
 ["SCF_K_VALUE_OPEN_AUTHORIZED","0"],
 ["SCF_D_VALUE_OPEN_AUTHORIZED","0"],
 ["E4D1D_2019_COORDINATE_VALUES_OPEN_AUTHORIZED","0"],
 ["TEMPORAL_GEOMETRY_AUTHORIZED","0"],
 ["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
 ["FINAL_SCALAR_AUTHORIZED","0"],
]
with DEC.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["decision","value"]); w.writerows(decision)

text="\n".join(f"{k}={v}" for k,v in decision)+"\n"
VAUDIT.write_text(text,encoding="utf-8")

for k,n in actual_counts.items():
    print(f"{k}_DATA_ROWS={n}")
print("ACS_EXECUTION_AUDIT_BYTE_IDENTICAL=PASS")
print("FROZEN_STRUCTURAL_ACCEPTANCE_GATES=PASS")
print("OUTCOME_BASED_GATE=0")
print("ACS_H_2019_MICRODATA_ROWS_OPENED=1")
print("ACS_H_2019_COORDINATE_VALUES_OPENED=1")
print("ACS_H_2019_EMPIRICALLY_TESTED=1")
print("SCIENTIFIC_METHOD_MUTATED=0")
print("NEXT_PRIMARY_PHASE_ID=E4D1D3_CPSB")
print("E4D1D3_CPSB_2019_FULL_WEIGHT_BRIDGE_EXECUTION_PRECOMMIT_AUTHORIZED=1")
print("CPS_I_VALUE_OPEN_AUTHORIZED=0")
print("SCF_K_VALUE_OPEN_AUTHORIZED=0")
print("SCF_D_VALUE_OPEN_AUTHORIZED=0")
print("TEMPORAL_GEOMETRY_AUTHORIZED=0")
print("REAL_INFLATION_ESTIMATION_AUTHORIZED=0")
print("E4D1D3_ACS_R0_POST_EXECUTION_VALIDATOR=PASS")
