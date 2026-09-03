#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import ast,csv,hashlib,os

ROOT=Path(__file__).resolve().parents[1]

PARENT=ROOT/"scripts/E4D1D2A2_acs2019_h_access_adapter.py"
OUT=ROOT/"scripts/E4D1D3P1_acs2019_h_access_adapter.py"
OLD_MAN=ROOT/"data/metadata/E4C3D_acs2022_microdata_manifest.tsv"
NEW_MAN=ROOT/"data/results/E4D1B_2019_official_data_manifest.tsv"

CPS_ADAPTER=ROOT/"scripts/E4D1D2A2_R3_cps2019_i_adapter.py"
SCF_ADAPTER=ROOT/"scripts/E4D1D2A2_scf2019_kd_adapter.py"

CPS_SRC=ROOT/"data/metadata/E4A2C_cps_replicate_engine_contract_audit.txt"
SCF_SRC=ROOT/"data/metadata/E4A2A_replicate_weight_schema_audit.txt"
CPS_DST=ROOT/"data/metadata/E4D1D_2019_runtime/CPS_ASEC/E4A2C_cps_replicate_engine_contract_audit.txt"
SCF_DST=ROOT/"data/metadata/E4D1D_2019_runtime/SCF/E4A2A_replicate_weight_schema_audit.txt"

PATCHREG=ROOT/"data/results/E4D1D3P1_static_provenance_patch_registry.tsv"
MIRRORREG=ROOT/"data/results/E4D1D3P1_method_authority_mirror_registry.tsv"
CANONREG=ROOT/"data/results/E4D1D3P1_canonical_adapter_source_registry.tsv"
FUNCREG=ROOT/"data/results/E4D1D3P1_function_provenance_registry.tsv"
GATES=ROOT/"data/results/E4D1D3P1_static_provenance_repair_hard_gates.tsv"
DECISION=ROOT/"data/results/E4D1D3P1_static_provenance_repair_decision.tsv"
EXEC=ROOT/"data/metadata/E4D1D3P1_execution.txt"
AUDIT=ROOT/"data/metadata/E4D1D3P1_static_provenance_repair_audit.txt"

EXPECTED={
 PARENT:"453425409ba727fc61ff82bd22fe7bf363b37c2a5d8d5aeb4fed2d0aff30d208",
 CPS_ADAPTER:"c8c864cf0cbccdb5508d0216c53c771bf07a99936e7810077e65f62725e3f94d",
 SCF_ADAPTER:"a62fd58144d6cb13e15f1d4b7eee442156e98f7be1213158d6424150a6c981ed",
 CPS_SRC:"a4fff0ecc7663338a0e3b68c1531a1f7f9015aa3c73c8a90006f90580cf08294",
 SCF_SRC:"ebf719755fbe7d0f6c5b0023f3900d435228b2e36d97f1e9a7da3fc4fe76b546",
}

def sha_bytes(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def sha(p:Path)->str:
    return sha_bytes(p.read_bytes())

def rows(p:Path):
    with p.open("r",encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f,delimiter="\t"))

def write_tsv(path:Path, header, data):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+".tmp-e4d1d3p1")
    with tmp.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,delimiter="\t",lineterminator="\n")
        w.writerow(header); w.writerows(data)
    os.replace(tmp,path)

for p,h in EXPECTED.items():
    assert p.is_file(),p
    assert sha(p)==h,(p,sha(p),h)

for p in (OUT,CPS_DST,SCF_DST,PATCHREG,MIRRORREG,CANONREG,FUNCREG,GATES,DECISION,EXEC,AUDIT):
    assert not p.exists(),f"output exists: {p}"

old=rows(OLD_MAN)
selected=[r["member_name"] for r in old if r.get("row_type")=="MEMBER" and r.get("selected")=="1"]
assert selected==["psam_husa.csv","psam_husb.csv"],selected

new=rows(NEW_MAN)
auth=[r for r in new if r.get("local_path")=="data/raw/acs/2019/1year/csv_hus.zip"]
assert len(auth)==1,auth
a=auth[0]
assert a["candidate_id"]=="ACS_2019_NATIONAL_HOUSING_CSV"
assert a["family"]=="ACS"
assert a["sha256"]=="82b1b11747a1259698db0254af0a8ca3064f83c22b028377d0f93e46f01c27e7"
assert a["bytes"]=="236656453"

parent_text=PARENT.read_text(encoding="utf-8")
patched=parent_text

repls=[
(
 "ACS_MANIFEST_PATH",
 'MAN=ROOT/"data/metadata/E4C3D_acs2022_microdata_manifest.tsv"',
 'MAN=ROOT/"data/results/E4D1B_2019_official_data_manifest.tsv"'
),
(
 "ACS_METADATA_NAMESPACE",
 'META=ROOT/"data/metadata"',
 'META=ROOT/"data/metadata/E4D1D_2019_runtime/ACS"'
),
(
 "ACS_MANIFEST_AND_MEMBER_BINDING",
 'with MAN.open(encoding="utf-8",newline="") as f: mr=list(csv.DictReader(f,delimiter="\\t"))\nar=[r for r in mr if r["row_type"]=="ARCHIVE"]\nmem=[r["member_name"] for r in mr if r["row_type"]=="MEMBER" and r["selected"]=="1"]\nif len(ar)!=1 or sha(RAW)!=ar[0]["sha256"] or not mem: raise RuntimeError("frozen source manifest mismatch")',
 'with MAN.open(encoding="utf-8",newline="") as f: mr=list(csv.DictReader(f,delimiter="\\t"))\nar=[r for r in mr if r.get("candidate_id")=="ACS_2019_NATIONAL_HOUSING_CSV" and r.get("family")=="ACS" and r.get("local_path")=="data/raw/acs/2019/1year/csv_hus.zip"]\nmem=["psam_husa.csv","psam_husb.csv"]\nif len(ar)!=1 or ar[0].get("sha256")!="82b1b11747a1259698db0254af0a8ca3064f83c22b028377d0f93e46f01c27e7" or ar[0].get("bytes")!="236656453" or sha(RAW)!=ar[0]["sha256"] or RAW.stat().st_size!=int(ar[0]["bytes"]): raise RuntimeError("frozen 2019 source manifest mismatch")'
),
(
 "ACS_2019_VALUE_OPEN_LABELS",
 '"RAW_SURVEY_DATA_READ=1","ACS_2022_MICRODATA_VALUES_OPENED=1","ACS_2022_HOUSING_ZIP_SHA_MATCHES_FROZEN_MANIFEST=1",',
 '"RAW_SURVEY_DATA_READ=1","ACS_2019_MICRODATA_VALUES_OPENED=1","ACS_2019_HOUSING_ZIP_SHA_MATCHES_FROZEN_MANIFEST=1",'
),
(
 "ACS_2019_EXECUTION_LABEL",
 '"E4C3D_FIRST_ACS_2022_H_ACCESS_EXECUTION=PASS","E4C3E_H_HOUSING_EVIDENCE_CLOSEOUT_PREFLIGHT_AUTHORIZED=1"',
 '"E4D1D3_ACS_2019_H_ACCESS_EXECUTION=PASS","DOWNSTREAM_EXECUTION_AUTHORIZATION_EMITTED=0"'
),
(
 "ACS_2019_EXECUTION_METADATA_FILE",
 '(META/"E4C3D_execution.txt").write_text(log,encoding="utf-8")',
 '(META/"E4D1D3_ACS_2019_h_access_execution.txt").write_text(log,encoding="utf-8")'
),
(
 "ACS_2019_AUDIT_METADATA_FILE",
 '(META/"E4C3D_first_acs2022_h_access_execution_audit.txt").write_text(log,encoding="utf-8")',
 '(META/"E4D1D3_ACS_2019_h_access_execution_audit.txt").write_text(log,encoding="utf-8")'
),
]

patch_rows=[]
for rid,old_s,new_s in repls:
    count=patched.count(old_s)
    assert count==1,(rid,count)
    patched=patched.replace(old_s,new_s,1)
    patch_rows.append([rid,sha_bytes(old_s.encode()),sha_bytes(new_s.encode()),"PASS"])

for forbidden in (
    "E4C3D_acs2022_microdata_manifest.tsv",
    "ACS_2022_MICRODATA_VALUES_OPENED=1",
    "ACS_2022_HOUSING_ZIP_SHA_MATCHES_FROZEN_MANIFEST=1",
    "E4C3D_FIRST_ACS_2022_H_ACCESS_EXECUTION=PASS",
    "E4C3E_H_HOUSING_EVIDENCE_CLOSEOUT_PREFLIGHT_AUTHORIZED=1",
    'META=ROOT/"data/metadata"',
):
    assert forbidden not in patched,forbidden

for token in (
 "E4C3D_h_access_point_estimates.tsv",
 "E4C3D_h_access_component_replicates.tsv",
 "E4C3D_h_access_owner_renter_comparisons.tsv",
 "E4C3D_h_access_difference_replicates.tsv",
 "E4C3D_h_access_ratio_replicates.tsv",
 "E4C3D_h_access_inference_summary.tsv",
):
    assert token in parent_text and token in patched

parent_tree=ast.parse(parent_text,filename=str(PARENT))
patched_tree=ast.parse(patched,filename=str(OUT))

def function_map(tree,src):
    out={}
    for n in tree.body:
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
            seg=ast.get_source_segment(src,n)
            assert seg is not None
            out[n.name]=seg
    return out

pf=function_map(parent_tree,parent_text)
rf=function_map(patched_tree,patched)
assert pf.keys()==rf.keys()
func_rows=[]
for name in pf:
    ph=sha_bytes(pf[name].encode("utf-8"))
    rh=sha_bytes(rf[name].encode("utf-8"))
    assert ph==rh,(name,ph,rh)
    func_rows.append([name,ph,rh,"IDENTICAL"])

cps_bytes=CPS_SRC.read_bytes()
scf_bytes=SCF_SRC.read_bytes()
assert sha_bytes(cps_bytes)==EXPECTED[CPS_SRC]
assert sha_bytes(scf_bytes)==EXPECTED[SCF_SRC]

OUT.parent.mkdir(parents=True,exist_ok=True)
tmp=OUT.with_name(OUT.name+".tmp-e4d1d3p1")
tmp.write_text(patched,encoding="utf-8")
os.replace(tmp,OUT)

for dst,b in ((CPS_DST,cps_bytes),(SCF_DST,scf_bytes)):
    dst.parent.mkdir(parents=True,exist_ok=True)
    tmp=dst.with_name(dst.name+".tmp-e4d1d3p1")
    tmp.write_bytes(b)
    os.replace(tmp,dst)

assert sha(CPS_DST)==sha(CPS_SRC)
assert sha(SCF_DST)==sha(SCF_SRC)
assert sha(PARENT)==EXPECTED[PARENT]
assert sha(CPS_ADAPTER)==EXPECTED[CPS_ADAPTER]
assert sha(SCF_ADAPTER)==EXPECTED[SCF_ADAPTER]

write_tsv(PATCHREG,["repair_id","old_span_sha256","new_span_sha256","status"],patch_rows)

mirror_rows=[
 ["CPS_ASEC",str(CPS_SRC.relative_to(ROOT)),sha(CPS_SRC),str(CPS_DST.relative_to(ROOT)),sha(CPS_DST),"BYTE_IDENTICAL_METHOD_AUTHORITY_MIRROR","PASS"],
 ["SCF",str(SCF_SRC.relative_to(ROOT)),sha(SCF_SRC),str(SCF_DST.relative_to(ROOT)),sha(SCF_DST),"BYTE_IDENTICAL_REPLICATE_DESIGN_AUTHORITY_MIRROR","PASS"],
]
write_tsv(MIRRORREG,["family","source","source_sha256","target","target_sha256","semantics","status"],mirror_rows)

canon=[
 ["ACS",str(OUT.relative_to(ROOT)),sha(OUT),"P1_REPAIRED_STATIC_PROVENANCE"],
 ["CPS_ASEC",str(CPS_ADAPTER.relative_to(ROOT)),sha(CPS_ADAPTER),"R3_FROZEN"],
 ["SCF",str(SCF_ADAPTER.relative_to(ROOT)),sha(SCF_ADAPTER),"A2_FROZEN"],
]
write_tsv(CANONREG,["family","adapter_path","sha256","source_status"],canon)
write_tsv(FUNCREG,["function","parent_source_sha256","repaired_source_sha256","status"],func_rows)

gates=[
 ["EXACT_STATIC_SOURCE_PATCH_SPAN_COUNT",str(len(repls))],
 ["ACS_FROZEN_SELECTED_MEMBER_COUNT","2"],
 ["ACS_FROZEN_SELECTED_MEMBER_SET","PASS"],
 ["ACS_2019_MANIFEST_AUTHORITY","PASS"],
 ["ACS_METADATA_RUNTIME_ISOLATION","PASS"],
 ["ACS_2019_TRUTH_LABELS","PASS"],
 ["ALL_ACS_FUNCTIONS_SOURCE_IDENTICAL","1"],
 ["CPS_METHOD_AUTHORITY_MIRROR_BYTE_IDENTICAL","1"],
 ["SCF_METHOD_AUTHORITY_MIRROR_BYTE_IDENTICAL","1"],
 ["EMPIRICAL_AUDIT_COPIED","0"],
 ["PARENT_ACS_ADAPTER_MUTATED","0"],
 ["CPS_ADAPTER_MUTATED","0"],
 ["SCF_ADAPTER_MUTATED","0"],
 ["ADAPTER_IMPORTED","0"],
 ["ADAPTER_EXECUTED","0"],
 ["2019_RAW_DATA_ROWS_OPENED","0"],
 ["2019_COORDINATE_VALUES_OPENED","0"],
 ["SCIENTIFIC_METHOD_MUTATED","0"],
]
write_tsv(GATES,["gate","value"],gates)

decision=[
 ["E4D1D3P1_STATIC_PROVENANCE_REPAIR_FREEZE","PASS"],
 ["ACS_CANONICAL_ADAPTER_SHA256",sha(OUT)],
 ["ACS_FROZEN_SELECTED_MEMBERS","psam_husa.csv|psam_husb.csv"],
 ["CPS_METHOD_AUTHORITY_MIRROR_SHA256",sha(CPS_DST)],
 ["SCF_METHOD_AUTHORITY_MIRROR_SHA256",sha(SCF_DST)],
 ["EMPIRICAL_AUDIT_COPIED","0"],
 ["PARENT_ACS_ADAPTER_MUTATED","0"],
 ["CPS_ADAPTER_MUTATED","0"],
 ["SCF_ADAPTER_MUTATED","0"],
 ["ADAPTER_IMPORTED","0"],
 ["ADAPTER_EXECUTED","0"],
 ["2019_RAW_DATA_ROWS_OPENED","0"],
 ["2019_COORDINATE_VALUES_OPENED","0"],
 ["SCIENTIFIC_METHOD_MUTATED","0"],
 ["NEXT_PRIMARY_PHASE_ID","E4D1D3_ACS"],
 ["E4D1D3_ACS_2019_H_ACCESS_EXECUTION_PRECOMMIT_AUTHORIZED","1"],
 ["E4D1D_2019_COORDINATE_VALUES_OPEN_AUTHORIZED","0"],
 ["TEMPORAL_GEOMETRY_AUTHORIZED","0"],
 ["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
]
write_tsv(DECISION,["decision","value"],decision)

log="\n".join(f"{k}={v}" for k,v in decision)+"\n"
EXEC.parent.mkdir(parents=True,exist_ok=True)
for p in (EXEC,AUDIT):
    tmp=p.with_name(p.name+".tmp-e4d1d3p1")
    tmp.write_text(log,encoding="utf-8")
    os.replace(tmp,p)

print("PARENT_ACS_ADAPTER_REUSED_IMMUTABLY=1")
print("EXACT_STATIC_SOURCE_PATCH_SPAN_COUNT="+str(len(repls)))
print("ACS_FROZEN_SELECTED_MEMBER_COUNT=2")
print("ACS_FROZEN_SELECTED_MEMBERS=psam_husa.csv|psam_husb.csv")
print("ACS_2019_MANIFEST_AUTHORITY=PASS")
print("ACS_METADATA_RUNTIME_ISOLATION=PASS")
print("ACS_2019_TRUTH_LABELS=PASS")
print("ALL_ACS_FUNCTIONS_SOURCE_IDENTICAL=1")
print("CPS_METHOD_AUTHORITY_MIRROR_BYTE_IDENTICAL=1")
print("SCF_METHOD_AUTHORITY_MIRROR_BYTE_IDENTICAL=1")
print("EMPIRICAL_AUDIT_COPIED=0")
print("ADAPTER_IMPORTED=0")
print("ADAPTER_EXECUTED=0")
print("2019_RAW_DATA_ROWS_OPENED=0")
print("2019_COORDINATE_VALUES_OPENED=0")
print("SCIENTIFIC_METHOD_MUTATED=0")
print("NEXT_PRIMARY_PHASE_ID=E4D1D3_ACS")
print("E4D1D3_ACS_2019_H_ACCESS_EXECUTION_PRECOMMIT_AUTHORIZED=1")
print("E4D1D_2019_COORDINATE_VALUES_OPEN_AUTHORIZED=0")
print("E4D1D3P1_STATIC_PROVENANCE_REPAIR_FREEZE=PASS")
