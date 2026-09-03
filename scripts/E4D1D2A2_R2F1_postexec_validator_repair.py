#!/usr/bin/env python3
from pathlib import Path
import csv,hashlib,json

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"data/metadata/E4D1D2A2_R2F1_postexec_validator_repair_contract.json"

R2_AUTH=ROOT/"data/results/E4D1D2A2_R2_official_static_layout_authority_registry.tsv"
R2_DEC=ROOT/"data/results/E4D1D2A2_R2_static_layout_acquisition_decision.tsv"
R2_GATES=ROOT/"data/results/E4D1D2A2_R2_static_layout_acquisition_hard_gates.tsv"
R2_HASH=ROOT/"data/results/E4D1D2A2_R2_static_layout_hash_registry.tsv"

FILES={
 "CPS_SAS":ROOT/"data/raw/cps_asec/2019/CPS_ASEC_ASCII_REPWGT_2019.SAS",
 "PERSON_LAYOUT":ROOT/"data/raw/cps_asec/2019/persfmt.txt",
 "HOUSE_LAYOUT":ROOT/"data/raw/cps_asec/2019/hhldfmt.txt",
}
EXPECTED_SHA={
 "CPS_SAS":"97e60a9fb698c72a343e0e9c346c3439987560461bbfcde42704cc3937b4c2e7",
 "PERSON_LAYOUT":"be9b7912f64ac574b78b8d455660c2bece8605c080c5771e496446de869eb1da",
 "HOUSE_LAYOUT":"eb3102622f5b9445e5ded16919dbb6de7b20eede0156fbbb4693bbb5124eaa31",
}

OUT_GATES=ROOT/"data/results/E4D1D2A2_R2F1_postexec_validator_repair_hard_gates.tsv"
OUT_DEC=ROOT/"data/results/E4D1D2A2_R2F1_postexec_validator_repair_decision.tsv"
OUT_AUDIT=ROOT/"data/metadata/E4D1D2A2_R2F1_postexec_validator_repair_audit.txt"

c=json.loads(CONTRACT.read_text(encoding="utf-8"))

def read(p):
    with p.open("r",encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f,delimiter="\t"))

def write(p,h,rows):
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,delimiter="\t",lineterminator="\n")
        w.writerow(h); w.writerows(rows)

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):
            h.update(b)
    return h.hexdigest()

auth=read(R2_AUTH)
dec_rows=read(R2_DEC)
gate_rows=read(R2_GATES)

assert len(auth)==3, len(auth)
bindings={r["binding"] for r in auth}
assert bindings==set(c["success_criteria"]["bindings"]), bindings

by={r["binding"]:r for r in auth}
for binding in c["success_criteria"]["bindings"]:
    r=by[binding]
    assert r["status"]=="PASS"
    assert r["exact_basename"]=="1"
    assert r["not_html"]=="1"
    assert r["static_role_semantics"]=="1"
    actual=sha(FILES[binding])
    assert actual==EXPECTED_SHA[binding]
    assert r["sha256"]==actual

hash_text=R2_HASH.read_text(encoding="utf-8")
for v in EXPECTED_SHA.values():
    assert v in hash_text

d={r["decision"]:r["value"] for r in dec_rows}
expected={
 "PARENT_R1_REUSED_AS_CANONICAL_UNRESOLVED_EVIDENCE":"1",
 "REPAIR_CLASS":"OFFICIAL_CPS2019_STATIC_AUTHORITY_ACQUISITION",
 "OFFICIAL_AUTHORITY_COUNT":"3",
 "UNRESOLVED_AUTHORITY_COUNT":"0",
 "PARENT_R1_OUTPUT_MUTATED":"0",
 "PARENT_ADAPTERS_MUTATED":"0",
 "ADAPTER_IMPORTED":"0",
 "ADAPTER_EXECUTED":"0",
 "2019_RAW_DATA_ROWS_OPENED":"0",
 "2019_COORDINATE_VALUES_OPENED":"0",
 "SCIENTIFIC_METHOD_MUTATED":"0",
 "NEXT_PRIMARY_PHASE_ID":"E4D1D2A2R3",
 "E4D1D2A2R3_STATIC_BINDING_PATCH_FREEZE_AUTHORIZED":"1",
 "E4D1D3_2019_COORDINATE_EXECUTION_PRECOMMIT_AUTHORIZED":"0",
 "E4D1D_2019_COORDINATE_VALUES_OPEN_AUTHORIZED":"0",
 "TEMPORAL_GEOMETRY_AUTHORIZED":"0",
 "REAL_INFLATION_ESTIMATION_AUTHORIZED":"0",
 "E4D1D2A2_R2_OFFICIAL_STATIC_LAYOUT_ACQUISITION_FREEZE":"PASS",
}
for k,v in expected.items():
    assert d[k]==v,(k,d.get(k),v)

for row in gate_rows:
    vals=[str(v).upper() for v in row.values()]
    assert "FAIL" not in vals, row

gates=[
 ["EXACT_3_OFFICIAL_AUTHORITY_ROWS_PASS","1"],
 ["EXACT_AUTHORITY_BINDING_SET_PASS","1"],
 ["EXACT_LOCAL_AUTHORITY_SHA_IDENTITIES_PASS","1"],
 ["R2_DECISION_OFFICIAL_AUTHORITY_COUNT_3","1"],
 ["R2_DECISION_UNRESOLVED_AUTHORITY_COUNT_0","1"],
 ["R2_SUCCESS_ROUTE_TO_R3_PASS","1"],
 ["PARENT_R2_OUTPUT_MUTATED","0"],
 ["PARENT_ADAPTERS_MUTATED","0"],
 ["R2_VERIFIER_REEXECUTED","0"],
 ["REDOWNLOAD_PERFORMED","0"],
 ["ADAPTER_IMPORTED","0"],
 ["ADAPTER_EXECUTED","0"],
 ["2019_RAW_DATA_ROWS_OPENED","0"],
 ["2019_COORDINATE_VALUES_OPENED","0"],
 ["SCIENTIFIC_METHOD_MUTATED","0"],
]
write(OUT_GATES,["gate","value"],gates)

decision=[
 ["PARENT_R2_POSTEXEC_OUTPUT_REUSED_IMMUTABLY","1"],
 ["PARENT_R2F0_FAILURE_PRESERVED","1"],
 ["R2_VERIFIER_REEXECUTED","0"],
 ["REDOWNLOAD_PERFORMED","0"],
 ["OFFICIAL_AUTHORITY_COUNT","3"],
 ["UNRESOLVED_AUTHORITY_COUNT","0"],
 ["CORRECTED_POSTEXEC_VALIDATION","PASS"],
 ["PARENT_R2_OUTPUT_MUTATED","0"],
 ["PARENT_ADAPTERS_MUTATED","0"],
 ["ADAPTER_IMPORTED","0"],
 ["ADAPTER_EXECUTED","0"],
 ["2019_RAW_DATA_ROWS_OPENED","0"],
 ["2019_COORDINATE_VALUES_OPENED","0"],
 ["SCIENTIFIC_METHOD_MUTATED","0"],
 ["NEXT_PRIMARY_PHASE_ID","E4D1D2A2R3"],
 ["E4D1D2A2R3_STATIC_BINDING_PATCH_FREEZE_AUTHORIZED","1"],
 ["E4D1D3_2019_COORDINATE_EXECUTION_PRECOMMIT_AUTHORIZED","0"],
 ["E4D1D_2019_COORDINATE_VALUES_OPEN_AUTHORIZED","0"],
 ["TEMPORAL_GEOMETRY_AUTHORIZED","0"],
 ["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
 ["E4D1D2A2_R2F1_POSTEXEC_VALIDATOR_REPAIR","PASS"],
]
write(OUT_DEC,["decision","value"],decision)

log="\n".join(f"{k}={v}" for k,v in decision)+"\n"
OUT_AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
