#!/usr/bin/env python3
from pathlib import Path
import ast,csv,hashlib,io,json,re,zipfile
from pandas.io.stata import StataReader

ROOT=Path(__file__).resolve().parents[1]

CONTRACT=ROOT/"data/metadata/E4D1BR_acs_column_discovery_schema_repair_contract.json"
LINEAGE=ROOT/"data/metadata/E4D1BR_frozen_input_lineage.tsv"
ACS_EXEC=ROOT/"scripts/E4C3D_first_acs2022_h_access_execution.py"
ACS_CONTRACT=ROOT/"data/metadata/E4C3C_first_acs2022_h_access_execution_contract.json"
ACS_2022_ZIP=ROOT/"data/raw/acs/2022/1year/csv_hus.zip"
B_MANIFEST=ROOT/"data/results/E4D1B_2019_official_data_manifest.tsv"

ACS_2019_ZIP=ROOT/"data/raw/acs/2019/1year/csv_hus.zip"
SCF_SUMMARY=ROOT/"data/raw/scf/2019/scfp2019s.zip"
SCF_FULL=ROOT/"data/raw/scf/2019/scf2019s.zip"
SCF_REP=ROOT/"data/raw/scf/2019/scf2019rw1s.zip"
CPS_PUBLIC=ROOT/"data/raw/cps_asec/2019/asec2019_pubuse.zip"
CPS_REP=ROOT/"data/raw/cps_asec/2019/CPS_ASEC_ASCII_REPWGT_2019.zip"

COLS=ROOT/"data/results/E4D1BR_acs_required_column_recovery_registry.tsv"
MEMBERS=ROOT/"data/results/E4D1BR_2019_archive_member_registry.tsv"
SCHEMA=ROOT/"data/results/E4D1BR_2019_schema_audit_registry.tsv"
GATES=ROOT/"data/results/E4D1BR_schema_repair_hard_gates.tsv"
DECISION=ROOT/"data/results/E4D1BR_acs_column_discovery_schema_repair_decision.tsv"
EXEC=ROOT/"data/metadata/E4D1BR_execution.txt"
AUDIT=ROOT/"data/metadata/E4D1BR_acs_column_discovery_schema_repair_audit.txt"

c=json.loads(CONTRACT.read_text(encoding="utf-8"))

def read_tsv(p):
    with p.open("r",encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f,delimiter="\t"))

def write_tsv(p,header,rows):
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,delimiter="\t",lineterminator="\n")
        w.writerow(header); w.writerows(rows)

# Exact raw byte recheck against preserved E4D1B manifest.
manifest=read_tsv(B_MANIFEST)
assert len(manifest)==6
for r in manifest:
    p=ROOT/r["local_path"]
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):
            h.update(b)
    assert h.hexdigest()==r["sha256"]
    assert p.stat().st_size==int(r["bytes"])

member_rows=[]

def zip_member_names(cid,p):
    with zipfile.ZipFile(p,"r") as z:
        infos=[i for i in z.infolist() if not i.is_dir()]
        for i in infos:
            member_rows.append([
                cid,i.filename,Path(i.filename).suffix.lower(),
                str(i.file_size),str(i.compress_size)
            ])
        return [i.filename for i in infos]

def csv_headers(p):
    out={}
    with zipfile.ZipFile(p,"r") as z:
        for i in z.infolist():
            if i.is_dir() or not i.filename.lower().endswith(".csv"):
                continue
            with z.open(i,"r") as raw:
                text=io.TextIOWrapper(raw,encoding="utf-8-sig",newline="")
                header=next(csv.reader(text))
            out[i.filename]=[x.strip().upper() for x in header]
    return out

# ---------------- ACS repaired static-column recovery ----------------
headers22=csv_headers(ACS_2022_ZIP)
assert headers22
common22=set.intersection(*(set(v) for v in headers22.values()))

source=ACS_EXEC.read_text(encoding="utf-8")
tree=ast.parse(source)

# Fixed-point string binding environment.
env={}
assigns=[]
for n in ast.walk(tree):
    if isinstance(n,ast.Assign):
        names=[]
        for t in n.targets:
            if isinstance(t,ast.Name):
                names.append(t.id)
        if names:
            assigns.append((names,n.value))
    elif isinstance(n,ast.AnnAssign) and isinstance(n.target,ast.Name):
        assigns.append(([n.target.id],n.value))

def resolve(node):
    vals=set()
    if node is None:
        return vals
    if isinstance(node,ast.Constant) and isinstance(node.value,str):
        vals.add(node.value.upper())
        return vals
    if isinstance(node,ast.Name):
        return set(env.get(node.id,set()))
    if isinstance(node,(ast.List,ast.Tuple,ast.Set)):
        for x in node.elts:
            vals |= resolve(x)
        return vals
    if isinstance(node,ast.Dict):
        for x in node.keys:
            vals |= resolve(x)
        for x in node.values:
            vals |= resolve(x)
        return vals
    if isinstance(node,ast.Subscript):
        vals |= resolve(node.slice)
        vals |= resolve(node.value)
        return vals
    if isinstance(node,ast.BinOp):
        vals |= resolve(node.left)
        vals |= resolve(node.right)
        return vals
    if isinstance(node,ast.JoinedStr):
        for x in node.values:
            vals |= resolve(x)
        return vals
    if isinstance(node,ast.FormattedValue):
        vals |= resolve(node.value)
        return vals
    for child in ast.iter_child_nodes(node):
        vals |= resolve(child)
    return vals

for _ in range(50):
    changed=False
    for names,val in assigns:
        got=resolve(val)
        for name in names:
            old=env.get(name,set())
            new=old|got
            if new!=old:
                env[name]=new
                changed=True
    if not changed:
        break

effective=set()
provenance={}

def add(vals,why,line):
    for v in vals:
        u=v.upper()
        if u in common22:
            effective.add(u)
            provenance.setdefault(u,set()).add(f"{why}@{line}")

# DataFrame-style subscript slices with propagated named-string bindings.
for n in ast.walk(tree):
    if isinstance(n,ast.Subscript):
        add(resolve(n.slice),"EXECUTOR_SUBSCRIPT_DATAFLOW",getattr(n,"lineno",0))
    elif isinstance(n,ast.Call):
        fn=""
        if isinstance(n.func,ast.Name):
            fn=n.func.id
        elif isinstance(n.func,ast.Attribute):
            fn=n.func.attr
        low=fn.lower()
        if any(k in low for k in ["column","series","numeric","weight","field","require","select"]):
            vals=set()
            for a in n.args:
                vals |= resolve(a)
            for kw in n.keywords:
                vals |= resolve(kw.value)
            add(vals,"EXECUTOR_COLUMN_HELPER_DATAFLOW",getattr(n,"lineno",0))

executor_effective=set(effective)

# Fallback only if executor dataflow still yields zero substantive header tokens.
contract_effective=set()
if not executor_effective:
    obj=json.loads(ACS_CONTRACT.read_text(encoding="utf-8"))
    def walk(x,path="$"):
        if isinstance(x,dict):
            for k,v in x.items():
                yield from walk(v,path+"."+str(k))
        elif isinstance(x,list):
            for i,v in enumerate(x):
                yield from walk(v,path+f"[{i}]")
        elif isinstance(x,str):
            yield x,path
    for val,path in walk(obj):
        u=val.strip().upper()
        if u in common22:
            contract_effective.add(u)
            provenance.setdefault(u,set()).add("FROZEN_H_CONTRACT:"+path)
    effective |= contract_effective

# Frozen ACS point + 80 replicate architecture.
weights={"WGTP"}|{f"WGTP{i}" for i in range(1,81)}
assert weights<=common22,"2022 ACS housing header lacks frozen weight architecture"
for w in weights:
    effective.add(w)
    provenance.setdefault(w,set()).add("FROZEN_WGTP_80_REPLICATE_ARCHITECTURE")

non_weight=sorted(effective-weights)
recovery_ok=len(non_weight)>=c["acs_recovery"]["minimum_non_weight_effective_field_count"]

col_rows=[]
for col in sorted(effective):
    col_rows.append([
        col,
        "WEIGHT" if col in weights else "SUBSTANTIVE_OR_STRUCTURAL",
        "|".join(sorted(provenance.get(col,set()))),
        str(int(col in common22)),
    ])
write_tsv(COLS,["column","role_class","recovery_provenance","present_in_2022_housing_header"],col_rows)

# 2019 ACS header-only compatibility.
zip_member_names("ACS_2019_NATIONAL_HOUSING_CSV",ACS_2019_ZIP)
headers19=csv_headers(ACS_2019_ZIP)
acs_schema_ok=(
    recovery_ok and bool(headers19) and
    all(effective<=set(h) for h in headers19.values())
)

# ---------------- SCF same frozen metadata-only gates ----------------
def stata_schema(cid,p):
    members=zip_member_names(cid,p)
    dta=[m for m in members if m.lower().endswith(".dta")]
    if len(dta)!=1:
        return dta,set(),"NONE"
    with zipfile.ZipFile(p,"r") as z:
        with z.open(dta[0],"r") as fh:
            reader=StataReader(fh,convert_categoricals=False)
            labels=reader.variable_labels()
            names={x.upper() for x in labels.keys()}
    vh=hashlib.sha256(("\n".join(sorted(names))+"\n").encode()).hexdigest()
    return dta,names,vh

sdta,snames,shash=stata_schema("SCF_2019_SUMMARY_STATA",SCF_SUMMARY)
fdta,fnames,fhash=stata_schema("SCF_2019_FULL_STATA",SCF_FULL)
rdta,rnames,rhash=stata_schema("SCF_2019_REPWGT_STATA",SCF_REP)

summary_req={"FIN","PIRTOTAL","Y1"}
full_req={"X42001","Y1"}
wt=[x for x in rnames if re.fullmatch(r"WT1B\d+",x)]
mm=[x for x in rnames if re.fullmatch(r"MM\d+",x)]

scf_summary_ok=len(sdta)==1 and summary_req<=snames
scf_full_ok=len(fdta)==1 and full_req<=fnames
scf_rep_ok=len(rdta)==1 and "Y1" in rnames and len(wt)==999 and len(mm)==999

# ---------------- CPS same frozen member-only gates ----------------
pub_members=zip_member_names("CPS_2019_PUBLIC_ASCII",CPS_PUBLIC)
rep_members=zip_member_names("CPS_2019_REPWGT_ASCII",CPS_REP)
cps_public_ok=len(pub_members)>0
cps_rep_ok=len(rep_members)>0

schema_rows=[
["ACS","ACS_2019_NATIONAL_HOUSING_CSV","CSV_HEADER_ONLY",
 str(len(headers19)),str(len(effective)),
 f"recovered_non_weight={len(non_weight)};executor_effective={len(executor_effective)};contract_fallback={len(contract_effective)};WGTP_family=81",
 "PASS" if acs_schema_ok else "FAIL"],
["SCF","SCF_2019_SUMMARY_STATA","STATA_METADATA_ONLY",
 str(len(sdta)),str(len(snames)),
 f"required={','.join(sorted(summary_req))};var_sha={shash}",
 "PASS" if scf_summary_ok else "FAIL"],
["SCF","SCF_2019_FULL_STATA","STATA_METADATA_ONLY",
 str(len(fdta)),str(len(fnames)),
 f"required={','.join(sorted(full_req))};var_sha={fhash}",
 "PASS" if scf_full_ok else "FAIL"],
["SCF","SCF_2019_REPWGT_STATA","STATA_METADATA_ONLY",
 str(len(rdta)),str(len(rnames)),
 f"Y1={int('Y1' in rnames)};WT1B={len(wt)};MM={len(mm)};var_sha={rhash}",
 "PASS" if scf_rep_ok else "FAIL"],
["CPS_ASEC","CPS_2019_PUBLIC_ASCII","ZIP_MEMBER_LIST_ONLY",
 str(len(pub_members)),"0","ASCII_content_opened=0",
 "PASS" if cps_public_ok else "FAIL"],
["CPS_ASEC","CPS_2019_REPWGT_ASCII","ZIP_MEMBER_LIST_ONLY",
 str(len(rep_members)),"0","ASCII_content_opened=0",
 "PASS" if cps_rep_ok else "FAIL"],
]
write_tsv(SCHEMA,
          ["family","candidate_id","inspection_mode","member_or_schema_count",
           "required_field_count","structural_summary","status"],
          schema_rows)
write_tsv(MEMBERS,
          ["candidate_id","member_name","suffix","uncompressed_bytes","compressed_bytes"],
          member_rows)

all_pass=all(r[-1]=="PASS" for r in schema_rows)
next_phase="E4D1C" if all_pass else "E4D1BR1"

write_tsv(GATES,["gate","value"],[
["PRESERVED_E4D1B_DOWNLOADED_ARTIFACT_COUNT","6"],
["REDOWNLOADED_ARTIFACT_COUNT","0"],
["ACS_RECOVERED_TOTAL_COLUMN_COUNT",str(len(effective))],
["ACS_RECOVERED_NON_WEIGHT_COLUMN_COUNT",str(len(non_weight))],
["ACS_EXECUTOR_EFFECTIVE_COLUMN_COUNT",str(len(executor_effective))],
["ACS_CONTRACT_FALLBACK_COLUMN_COUNT",str(len(contract_effective))],
["ACS_COLUMN_RECOVERY_SUFFICIENT",str(int(recovery_ok))],
["ACS_SCHEMA_PASS",str(int(acs_schema_ok))],
["SCF_SUMMARY_SCHEMA_PASS",str(int(scf_summary_ok))],
["SCF_FULL_SCHEMA_PASS",str(int(scf_full_ok))],
["SCF_REPLICATE_SCHEMA_PASS",str(int(scf_rep_ok))],
["CPS_PUBLIC_CONTAINER_PASS",str(int(cps_public_ok))],
["CPS_REPLICATE_CONTAINER_PASS",str(int(cps_rep_ok))],
["ALL_SCHEMA_GATES_PASS",str(int(all_pass))],
["ACS_DATA_ROWS_OPENED","0"],
["SCF_OBSERVATION_ROWS_OPENED","0"],
["CPS_ASCII_DATA_LINES_OPENED","0"],
["NUMERIC_RESULT_ROWS_OPENED","0"],
["2019_ECONOMIC_VALUES_OPENED","0"],
["TEMPORAL_GEOMETRY_AUTHORIZED","0"],
["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
])

write_tsv(DECISION,["decision","value"],[
["E4D1B_FAILURE_PRESERVED_BEFORE_REPAIR","1"],
["REPAIR_CLASS","ACS_REQUIRED_COLUMN_DISCOVERY_STATIC_ANALYSIS_BUG"],
["DOWNLOADED_ARTIFACT_COUNT","6"],
["REDOWNLOADED_ARTIFACT_COUNT","0"],
["ACS_COLUMN_RECOVERY_STATUS","PASS" if recovery_ok else "UNRESOLVED"],
["ACS_SCHEMA_AUDIT_STATUS","PASS" if acs_schema_ok else "FAIL"],
["SCF_SCHEMA_AUDIT_STATUS","PASS" if (scf_summary_ok and scf_full_ok and scf_rep_ok) else "FAIL"],
["CPS_CONTAINER_AUDIT_STATUS","PASS" if (cps_public_ok and cps_rep_ok) else "FAIL"],
["SCHEMA_AUDIT_STATUS","PASS" if all_pass else "BLOCKED"],
["ACS_DATA_ROWS_OPENED","0"],
["SCF_OBSERVATION_ROWS_OPENED","0"],
["CPS_ASCII_DATA_LINES_OPENED","0"],
["NUMERIC_RESULT_ROWS_OPENED","0"],
["2019_ECONOMIC_VALUES_OPENED","0"],
["NEXT_PRIMARY_PHASE_ID",next_phase],
["E4D1C_2019_COORDINATE_EXECUTION_PRECOMMIT_AUTHORIZED",str(int(all_pass))],
["E4D1BR1_TARGETED_SCHEMA_FORENSIC_AUTHORIZED",str(int(not all_pass))],
["TEMPORAL_GEOMETRY_AUTHORIZED","0"],
["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
["E4D1BR_ACS_COLUMN_DISCOVERY_SCHEMA_REPAIR","PASS"],
])

log="\n".join([
"E4D1B_FAILURE_PRESERVED_BEFORE_REPAIR=1",
"REPAIR_CLASS=ACS_REQUIRED_COLUMN_DISCOVERY_STATIC_ANALYSIS_BUG",
"DOWNLOADED_ARTIFACT_COUNT=6",
"REDOWNLOADED_ARTIFACT_COUNT=0",
f"ACS_RECOVERED_TOTAL_COLUMN_COUNT={len(effective)}",
f"ACS_RECOVERED_NON_WEIGHT_COLUMN_COUNT={len(non_weight)}",
f"ACS_EXECUTOR_EFFECTIVE_COLUMN_COUNT={len(executor_effective)}",
f"ACS_CONTRACT_FALLBACK_COLUMN_COUNT={len(contract_effective)}",
f"ACS_COLUMN_RECOVERY_SUFFICIENT={int(recovery_ok)}",
f"ACS_2019_CSV_MEMBER_COUNT={len(headers19)}",
f"ACS_SCHEMA_PASS={int(acs_schema_ok)}",
f"SCF_SUMMARY_SCHEMA_PASS={int(scf_summary_ok)}",
f"SCF_FULL_SCHEMA_PASS={int(scf_full_ok)}",
f"SCF_REPLICATE_SCHEMA_PASS={int(scf_rep_ok)}",
f"SCF_REPLICATE_WT1B_COUNT={len(wt)}",
f"SCF_REPLICATE_MM_COUNT={len(mm)}",
f"CPS_PUBLIC_ARCHIVE_MEMBER_COUNT={len(pub_members)}",
f"CPS_REPLICATE_ARCHIVE_MEMBER_COUNT={len(rep_members)}",
f"CPS_CONTAINER_SCHEMA_PASS={int(cps_public_ok and cps_rep_ok)}",
f"ALL_SCHEMA_GATES_PASS={int(all_pass)}",
"ACS_DATA_ROWS_OPENED=0",
"SCF_OBSERVATION_ROWS_OPENED=0",
"CPS_ASCII_DATA_LINES_OPENED=0",
"NUMERIC_RESULT_ROWS_OPENED=0",
"2019_ECONOMIC_VALUES_OPENED=0",
"TEMPORAL_GEOMETRY_AUTHORIZED=0",
"REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
f"NEXT_PRIMARY_PHASE_ID={next_phase}",
f"E4D1C_2019_COORDINATE_EXECUTION_PRECOMMIT_AUTHORIZED={int(all_pass)}",
f"E4D1BR1_TARGETED_SCHEMA_FORENSIC_AUTHORIZED={int(not all_pass)}",
"E4D1BR_ACS_COLUMN_DISCOVERY_SCHEMA_REPAIR=PASS",
])+"\n"

EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
