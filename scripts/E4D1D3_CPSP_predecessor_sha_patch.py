#!/usr/bin/env python3
from pathlib import Path
import ast,csv,hashlib

ROOT=Path(__file__).resolve().parents[1]
PARENT=ROOT/"scripts/E4D1D2A2_R3_cps2019_i_adapter.py"
BRIDGE_AUDIT=ROOT/"data/metadata/E4D1D_2019_runtime/CPS_ASEC/E4A2B_cps_full_weight_bridge_audit.txt"
OUT=ROOT/"scripts/E4D1D3_CPSP_cps2019_i_adapter.py"
REG=ROOT/"data/results/E4D1D3_CPSP_predecessor_sha_patch_registry.tsv"
DEC=ROOT/"data/results/E4D1D3_CPSP_predecessor_sha_patch_decision.tsv"
AUDIT=ROOT/"data/metadata/E4D1D3_CPSP_predecessor_sha_patch_audit.txt"

PARENT_SHA="c8c864cf0cbccdb5508d0216c53c771bf07a99936e7810077e65f62725e3f94d"
OLD="962b727559808c389afac33060a4562bead5099be6000b951af796a1ac37be2e"
SUMMARY_SHA="475ba266f163b2e08fff3256567bd563c3cc17c4826240a8429275cdb2fc62bb"
RUNTIME_PATH="data/metadata/E4D1D_2019_runtime/CPS_ASEC/E4A2B_cps_full_weight_bridge_audit.txt"
SUMMARY_PATH="data/metadata/E4A2B_cps_full_weight_bridge_summary.tsv"

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

assert sha(PARENT)==PARENT_SHA
assert BRIDGE_AUDIT.is_file()
t=BRIDGE_AUDIT.read_text(encoding="utf-8")
for token in (
 "E4A2B_WEIGHT_BRIDGE_AUDIT=PASS",
 "CPS_HOUSEHOLD_FULL_WEIGHT_BRIDGE=PASS",
 "CPS_PWWGT0_VALUES_PARSED=1",
 "CPS_PWWGT1_160_VALUES_PARSED=0",
 "CPS_I_VALUES_READ=0",
 "E4D1D3_CPSP_PREDECESSOR_SHA_PATCH_AUTHORIZED=1",
):
    assert token in t,token

new=sha(BRIDGE_AUDIT)
src=PARENT.read_text(encoding="utf-8")
assert src.count(RUNTIME_PATH)==1
assert src.count(OLD)==1
assert src.count(SUMMARY_PATH)==1
assert src.count(SUMMARY_SHA)==1

patched=src.replace(OLD,new,1)

def fmap(text):
    tree=ast.parse(text)
    d={}
    for n in tree.body:
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
            seg=ast.get_source_segment(text,n) or ""
            d[n.name]=hashlib.sha256(seg.encode()).hexdigest()
    return d

assert fmap(src)==fmap(patched)
assert patched.count(RUNTIME_PATH)==1
assert patched.count(new)==1
assert patched.count(SUMMARY_PATH)==1
assert patched.count(SUMMARY_SHA)==1
assert OLD not in patched

for p in (OUT,REG,DEC,AUDIT):
    assert not p.exists(),p

OUT.write_text(patched,encoding="utf-8")

REG.parent.mkdir(parents=True,exist_ok=True)
with REG.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["binding","patch_class","old_sha256","new_sha256","occurrence_count","scientific_functions_mutated","status"])
    w.writerow(["E4A2B_AUDIT","EXPECTED_SHA_ONLY",OLD,new,"1","0","PASS"])

with DEC.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["decision","value"])
    for row in [
        ("E4D1D3_CPSP_PREDECESSOR_SHA_PATCH","PASS"),
        ("E4A2B_AUDIT_EXPECTED_SHA_PATCH_COUNT","1"),
        ("E4A2B_SUMMARY_BINDING_MUTATED","0"),
        ("SCIENTIFIC_METHOD_MUTATED","0"),
        ("CPS_VALUES_OPENED_DURING_PATCH","0"),
        ("NEXT_PRIMARY_PHASE_ID","E4D1D3_CPSI"),
        ("E4D1D3_CPSI_2019_I_EXECUTION_PRECOMMIT_AUTHORIZED","1"),
        ("CPS_I_VALUE_OPEN_AUTHORIZED","0"),
        ("SCF_K_VALUE_OPEN_AUTHORIZED","0"),
        ("SCF_D_VALUE_OPEN_AUTHORIZED","0"),
        ("TEMPORAL_GEOMETRY_AUTHORIZED","0"),
        ("REAL_INFLATION_ESTIMATION_AUTHORIZED","0"),
    ]:
        w.writerow(row)

audit_lines=[
 "E4D1D3_CPSP_PREDECESSOR_SHA_PATCH=PASS",
 f"PARENT_ADAPTER_SHA256={PARENT_SHA}",
 f"BRIDGE_AUDIT_SHA256={new}",
 f"OUTPUT_ADAPTER_SHA256={sha(OUT)}",
 "E4A2B_AUDIT_EXPECTED_SHA_PATCH_COUNT=1",
 "E4A2B_SUMMARY_BINDING_MUTATED=0",
 "SCIENTIFIC_METHOD_MUTATED=0",
 "CPS_VALUES_OPENED_DURING_PATCH=0",
 "NEXT_PRIMARY_PHASE_ID=E4D1D3_CPSI",
 "E4D1D3_CPSI_2019_I_EXECUTION_PRECOMMIT_AUTHORIZED=1",
 "CPS_I_VALUE_OPEN_AUTHORIZED=0",
]
AUDIT.write_text("\n".join(audit_lines)+"\n",encoding="utf-8")
print(AUDIT.read_text(encoding="utf-8"),end="")
