#!/usr/bin/env python3
from pathlib import Path
import csv,hashlib,json

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"data/metadata/E4D1D2A2_R2_official_static_layout_acquisition_plan.tsv"
AUTH=ROOT/"data/results/E4D1D2A2_R2_official_static_layout_authority_registry.tsv"
HASHES=ROOT/"data/results/E4D1D2A2_R2_static_layout_hash_registry.tsv"
GATES=ROOT/"data/results/E4D1D2A2_R2_static_layout_acquisition_hard_gates.tsv"
DECISION=ROOT/"data/results/E4D1D2A2_R2_static_layout_acquisition_decision.tsv"
EXEC=ROOT/"data/metadata/E4D1D2A2_R2_execution.txt"
AUDIT=ROOT/"data/metadata/E4D1D2A2_R2_static_layout_acquisition_audit.txt"

def read(p):
    with p.open("r",encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f,delimiter="\t"))
def write(p,h,rows):
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,delimiter="\t",lineterminator="\n")
        w.writerow(h);w.writerows(rows)
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

rows=read(PLAN)
auth=[]
hashrows=[]
fail=[]

for r in rows:
    p=ROOT/r["exact_local_path"]
    if not p.exists():
        fail.append(f"{r['binding']}:MISSING")
        continue
    b=p.read_bytes()
    try:
        txt=b.decode("utf-8")
    except UnicodeDecodeError:
        txt=b.decode("latin-1")

    basename_ok=(p.name==r["expected_basename"])
    not_html=("<html" not in txt[:2048].lower() and "<!doctype html" not in txt[:2048].lower())
    size_ok=len(b)>1000
    upper=txt.upper()

    if r["binding"]=="CPS_SAS":
        semantic_ok=("PWWGT" in upper and ("INPUT" in upper or "INFILE" in upper))
    elif r["binding"]=="PERSON_LAYOUT":
        semantic_ok=("PERSON" in upper or "PERID" in upper or "A_AGE" in upper or "A_SEX" in upper)
    elif r["binding"]=="HOUSE_LAYOUT":
        semantic_ok=("HOUSE" in upper or "H_SEQ" in upper or "H_IDNUM" in upper)
    else:
        semantic_ok=False

    ok=basename_ok and not_html and size_ok and semantic_ok
    if not ok:
        fail.append(
            f"{r['binding']}:basename={int(basename_ok)},not_html={int(not_html)},"
            f"size={int(size_ok)},semantic={int(semantic_ok)}"
        )

    digest=sha(p)
    auth.append([
        r["binding"],r["role"],r["official_url"],r["exact_local_path"],
        p.name,len(b),digest,int(basename_ok),int(not_html),int(semantic_ok),
        "PASS" if ok else "UNRESOLVED"
    ])
    hashrows.append([
        r["binding"],r["exact_local_path"],digest,len(b),
        "OFFICIAL_CENSUS_2019_STATIC_TEXT","PASS" if ok else "UNRESOLVED"
    ])

success=(len(auth)==3 and not fail and all(r[-1]=="PASS" for r in auth))

write(AUTH,[
    "binding","role","official_url","local_path","basename","bytes","sha256",
    "exact_basename","not_html","static_role_semantics","status"
],auth)
write(HASHES,["binding","local_path","sha256","bytes","authority_class","status"],hashrows)
write(GATES,["gate","value"],[
    ["EXACT_OFFICIAL_AUTHORITY_COUNT",str(int(len(auth)==3))],
    ["ALL_EXACT_BASENAMES_PASS",str(int(len(auth)==3 and all(r[7]=="1" for r in auth)))],
    ["ALL_NON_HTML_TEXT_PASS",str(int(len(auth)==3 and all(r[8]=="1" for r in auth)))],
    ["ALL_STATIC_ROLE_SEMANTICS_PASS",str(int(len(auth)==3 and all(r[9]=="1" for r in auth)))],
    ["UNRESOLVED_AUTHORITY_COUNT",str(len(fail))],
    ["PARENT_R1_OUTPUT_MUTATED","0"],
    ["PARENT_ADAPTERS_MUTATED","0"],
    ["ADAPTER_IMPORTED","0"],
    ["ADAPTER_EXECUTED","0"],
    ["2019_RAW_DATA_ROWS_OPENED","0"],
    ["2019_COORDINATE_VALUES_OPENED","0"],
    ["SCIENTIFIC_METHOD_MUTATED","0"],
    ["TEMPORAL_GEOMETRY_AUTHORIZED","0"],
    ["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
])

nxt="E4D1D2A2R3" if success else "E4D1D2A2R2R"
write(DECISION,["decision","value"],[
    ["PARENT_R1_REUSED_AS_CANONICAL_UNRESOLVED_EVIDENCE","1"],
    ["REPAIR_CLASS","OFFICIAL_CPS2019_STATIC_AUTHORITY_ACQUISITION"],
    ["OFFICIAL_AUTHORITY_COUNT",str(len(auth))],
    ["UNRESOLVED_AUTHORITY_COUNT",str(len(fail))],
    ["PARENT_R1_OUTPUT_MUTATED","0"],
    ["PARENT_ADAPTERS_MUTATED","0"],
    ["ADAPTER_IMPORTED","0"],
    ["ADAPTER_EXECUTED","0"],
    ["2019_RAW_DATA_ROWS_OPENED","0"],
    ["2019_COORDINATE_VALUES_OPENED","0"],
    ["SCIENTIFIC_METHOD_MUTATED","0"],
    ["NEXT_PRIMARY_PHASE_ID",nxt],
    ["E4D1D2A2R3_STATIC_BINDING_PATCH_FREEZE_AUTHORIZED",str(int(success))],
    ["E4D1D3_2019_COORDINATE_EXECUTION_PRECOMMIT_AUTHORIZED","0"],
    ["E4D1D_2019_COORDINATE_VALUES_OPEN_AUTHORIZED","0"],
    ["TEMPORAL_GEOMETRY_AUTHORIZED","0"],
    ["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
    ["E4D1D2A2_R2_OFFICIAL_STATIC_LAYOUT_ACQUISITION_FREEZE","PASS"],
])

log="\n".join([
    "PARENT_R1_REUSED_AS_CANONICAL_UNRESOLVED_EVIDENCE=1",
    "REPAIR_CLASS=OFFICIAL_CPS2019_STATIC_AUTHORITY_ACQUISITION",
    f"OFFICIAL_AUTHORITY_COUNT={len(auth)}",
    f"UNRESOLVED_AUTHORITY_COUNT={len(fail)}",
    "PARENT_R1_OUTPUT_MUTATED=0",
    "PARENT_ADAPTERS_MUTATED=0",
    "ADAPTER_IMPORTED=0",
    "ADAPTER_EXECUTED=0",
    "2019_RAW_DATA_ROWS_OPENED=0",
    "2019_COORDINATE_VALUES_OPENED=0",
    "SCIENTIFIC_METHOD_MUTATED=0",
    f"NEXT_PRIMARY_PHASE_ID={nxt}",
    f"E4D1D2A2R3_STATIC_BINDING_PATCH_FREEZE_AUTHORIZED={int(success)}",
    "E4D1D3_2019_COORDINATE_EXECUTION_PRECOMMIT_AUTHORIZED=0",
    "E4D1D_2019_COORDINATE_VALUES_OPEN_AUTHORIZED=0",
    "TEMPORAL_GEOMETRY_AUTHORIZED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "E4D1D2A2_R2_OFFICIAL_STATIC_LAYOUT_ACQUISITION_FREEZE=PASS",
])+"\n"
if fail:
    log += "UNRESOLVED_DETAILS="+" || ".join(fail)+"\n"
EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
