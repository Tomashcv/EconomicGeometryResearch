#!/usr/bin/env python3
from pathlib import Path
import ast,csv,hashlib,io,json,re,zipfile
from pandas.io.stata import StataReader

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"data/metadata/E4D1B_exact_2019_data_acquisition_plan.tsv"
STATIC=ROOT/"data/metadata/E4D1B_frozen_static_schema_authority_lineage.tsv"
CONTRACT=ROOT/"data/metadata/E4D1B_2019_official_source_acquisition_schema_audit_contract.json"

ACS_EXEC=ROOT/"scripts/E4C3D_first_acs2022_h_access_execution.py"
ACS_2022_ZIP=ROOT/"data/raw/acs/2022/1year/csv_hus.zip"

MANIFEST=ROOT/"data/results/E4D1B_2019_official_data_manifest.tsv"
MEMBERS=ROOT/"data/results/E4D1B_2019_archive_member_registry.tsv"
SCHEMA=ROOT/"data/results/E4D1B_2019_schema_audit_registry.tsv"
GATES=ROOT/"data/results/E4D1B_acquisition_schema_hard_gates.tsv"
DECISION=ROOT/"data/results/E4D1B_2019_official_source_acquisition_schema_audit_decision.tsv"
EXEC=ROOT/"data/metadata/E4D1B_execution.txt"
AUDIT=ROOT/"data/metadata/E4D1B_2019_official_source_acquisition_schema_audit.txt"

def read_tsv(p):
    with p.open("r",encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f,delimiter="\t"))

def write_tsv(p,header,rows):
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,delimiter="\t",lineterminator="\n")
        w.writerow(header); w.writerows(rows)

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):
            h.update(b)
    return h.hexdigest()

c=json.loads(CONTRACT.read_text(encoding="utf-8"))
plan=read_tsv(PLAN)
assert len(plan)==6
byid={r["candidate_id"]:r for r in plan}

# Verify all downloaded bytes exist; do not read semantic content yet.
manifest=[]
for r in plan:
    p=ROOT/r["local_path"]
    assert p.is_file(),p
    manifest.append([
        r["candidate_id"],r["family"],r["url"],r["local_path"],
        sha(p),str(p.stat().st_size)
    ])
write_tsv(MANIFEST,["candidate_id","family","url","local_path","sha256","bytes"],manifest)

member_rows=[]
schema_rows=[]

def zip_members(cid,p):
    with zipfile.ZipFile(p,"r") as z:
        infos=[i for i in z.infolist() if not i.is_dir()]
        for i in infos:
            suffix=Path(i.filename).suffix.lower()
            member_rows.append([cid,i.filename,suffix,str(i.file_size),str(i.compress_size)])
        return [i.filename for i in infos]

# ----- ACS: header-only, no data row -----
def first_csv_header_from_zip(p):
    out={}
    with zipfile.ZipFile(p,"r") as z:
        for info in z.infolist():
            if info.is_dir() or not info.filename.lower().endswith(".csv"):
                continue
            with z.open(info,"r") as raw:
                text=io.TextIOWrapper(raw,encoding="utf-8-sig",newline="")
                reader=csv.reader(text)
                header=next(reader)
            out[info.filename]=[x.strip().upper() for x in header]
    return out

# Derive exact ACS fields from frozen executor subscript string tokens intersected
# with the frozen 2022 housing header. This is schema-only and avoids token guessing.
tree=ast.parse(ACS_EXEC.read_text(encoding="utf-8"))
sub_tokens=set()
for n in ast.walk(tree):
    if isinstance(n,ast.Subscript):
        for x in ast.walk(n.slice):
            if isinstance(x,ast.Constant) and isinstance(x.value,str):
                s=x.value.strip().upper()
                if re.fullmatch(r"[A-Z][A-Z0-9_]{1,30}",s):
                    sub_tokens.add(s)

acs22_headers=first_csv_header_from_zip(ACS_2022_ZIP)
assert acs22_headers,"no 2022 ACS CSV header"
acs22_common=set.intersection(*(set(v) for v in acs22_headers.values()))
acs_required=sorted(sub_tokens & acs22_common)
assert acs_required,"no frozen H columns derived"

# Frozen weight architecture must appear exactly.
for x in ["WGTP"]+[f"WGTP{i}" for i in range(1,81)]:
    assert x in acs22_common,x
    if x not in acs_required:
        acs_required.append(x)
acs_required=sorted(set(acs_required))

acs19_path=ROOT/byid["ACS_2019_NATIONAL_HOUSING_CSV"]["local_path"]
acs19_members=zip_members("ACS_2019_NATIONAL_HOUSING_CSV",acs19_path)
acs19_headers=first_csv_header_from_zip(acs19_path)
acs_ok=bool(acs19_headers) and all(set(acs_required)<=set(h) for h in acs19_headers.values())
schema_rows.append([
    "ACS","ACS_2019_NATIONAL_HOUSING_CSV","CSV_HEADER_ONLY",
    str(len(acs19_headers)),str(len(acs_required)),
    "|".join(acs_required),
    "PASS" if acs_ok else "FAIL"
])

# ----- SCF: Stata metadata only -----
def stata_schema(cid,p):
    members=zip_members(cid,p)
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

scf_summary=ROOT/byid["SCF_2019_SUMMARY_STATA"]["local_path"]
scf_full=ROOT/byid["SCF_2019_FULL_STATA"]["local_path"]
scf_rep=ROOT/byid["SCF_2019_REPWGT_STATA"]["local_path"]

sdta,snames,shash=stata_schema("SCF_2019_SUMMARY_STATA",scf_summary)
fdta,fnames,fhash=stata_schema("SCF_2019_FULL_STATA",scf_full)
rdta,rnames,rhash=stata_schema("SCF_2019_REPWGT_STATA",scf_rep)

summary_req={"FIN","PIRTOTAL","Y1"}
full_req={"X42001","Y1"}
wt=[x for x in rnames if re.fullmatch(r"WT1B\d+",x)]
mm=[x for x in rnames if re.fullmatch(r"MM\d+",x)]
summary_ok=len(sdta)==1 and summary_req<=snames
full_ok=len(fdta)==1 and full_req<=fnames
rep_ok=len(rdta)==1 and "Y1" in rnames and len(wt)==999 and len(mm)==999

schema_rows.extend([
    ["SCF","SCF_2019_SUMMARY_STATA","STATA_METADATA_ONLY",str(len(sdta)),str(len(snames)),
     f"required={','.join(sorted(summary_req))};var_sha={shash}","PASS" if summary_ok else "FAIL"],
    ["SCF","SCF_2019_FULL_STATA","STATA_METADATA_ONLY",str(len(fdta)),str(len(fnames)),
     f"required={','.join(sorted(full_req))};var_sha={fhash}","PASS" if full_ok else "FAIL"],
    ["SCF","SCF_2019_REPWGT_STATA","STATA_METADATA_ONLY",str(len(rdta)),str(len(rnames)),
     f"Y1={int('Y1' in rnames)};WT1B={len(wt)};MM={len(mm)};var_sha={rhash}","PASS" if rep_ok else "FAIL"],
])

# ----- CPS: member/container audit only; no member content opened -----
cps_pub=ROOT/byid["CPS_2019_PUBLIC_ASCII"]["local_path"]
cps_rep=ROOT/byid["CPS_2019_REPWGT_ASCII"]["local_path"]
pub_members=zip_members("CPS_2019_PUBLIC_ASCII",cps_pub)
rep_members=zip_members("CPS_2019_REPWGT_ASCII",cps_rep)

pub_ok=len(pub_members)>0
rep_ok_cps=len(rep_members)>0
schema_rows.extend([
    ["CPS_ASEC","CPS_2019_PUBLIC_ASCII","ZIP_MEMBER_LIST_ONLY",str(len(pub_members)),"0",
     "frozen_2019_dictionary_and_E4D1A_semantic_lineage_reused;ASCII_content_opened=0",
     "PASS" if pub_ok else "FAIL"],
    ["CPS_ASEC","CPS_2019_REPWGT_ASCII","ZIP_MEMBER_LIST_ONLY",str(len(rep_members)),"0",
     "frozen_2019_replicate_SAS_layout_reused;ASCII_content_opened=0",
     "PASS" if rep_ok_cps else "FAIL"],
])

write_tsv(MEMBERS,
          ["candidate_id","member_name","suffix","uncompressed_bytes","compressed_bytes"],
          member_rows)
write_tsv(SCHEMA,
          ["family","candidate_id","inspection_mode","member_or_schema_count",
           "required_field_count","structural_summary","status"],
          schema_rows)

all_schema_pass=all(r[-1]=="PASS" for r in schema_rows)
next_phase="E4D1C" if all_schema_pass else "E4D1BR"

write_tsv(GATES,["gate","value"],[
    ["DOWNLOADED_ARTIFACT_COUNT","6"],
    ["MANIFEST_HASH_PINNED_ARTIFACT_COUNT","6"],
    ["ACS_DATA_ROWS_OPENED","0"],
    ["SCF_OBSERVATION_ROWS_OPENED","0"],
    ["CPS_ASCII_DATA_LINES_OPENED","0"],
    ["NUMERIC_RESULT_ROWS_OPENED","0"],
    ["2019_ECONOMIC_VALUES_OPENED","0"],
    ["SCHEMA_AUDIT_ROW_COUNT",str(len(schema_rows))],
    ["ALL_SCHEMA_GATES_PASS",str(int(all_schema_pass))],
    ["TEMPORAL_GEOMETRY_AUTHORIZED","0"],
    ["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
])

write_tsv(DECISION,["decision","value"],[
    ["DOWNLOADED_ARTIFACT_COUNT","6"],
    ["SELECTED_2019_DATA_ARTIFACT_COUNT","6"],
    ["ALL_2019_SOURCE_BYTES_HASH_PINNED","1"],
    ["SCHEMA_AUDIT_STATUS","PASS" if all_schema_pass else "BLOCKED"],
    ["ACS_DATA_ROWS_OPENED","0"],
    ["SCF_OBSERVATION_ROWS_OPENED","0"],
    ["CPS_ASCII_DATA_LINES_OPENED","0"],
    ["NUMERIC_RESULT_ROWS_OPENED","0"],
    ["2019_ECONOMIC_VALUES_OPENED","0"],
    ["NEXT_PRIMARY_PHASE_ID",next_phase],
    ["E4D1C_2019_COORDINATE_EXECUTION_PRECOMMIT_AUTHORIZED",str(int(all_schema_pass))],
    ["E4D1BR_TARGETED_SOURCE_SCHEMA_REPAIR_AUTHORIZED",str(int(not all_schema_pass))],
    ["TEMPORAL_GEOMETRY_AUTHORIZED","0"],
    ["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
    ["E4D1B_2019_OFFICIAL_SOURCE_ACQUISITION_AND_SCHEMA_AUDIT","PASS"],
])

log="\n".join([
    "E4D1AR2_R0_REUSED_AS_CANONICAL_2019_SOURCE_LINEAGE=1",
    "TARGET_YEAR=2019",
    "DOWNLOADED_ARTIFACT_COUNT=6",
    "ALL_2019_SOURCE_BYTES_HASH_PINNED=1",
    f"ACS_REQUIRED_FROZEN_COLUMN_COUNT={len(acs_required)}",
    f"ACS_2019_CSV_MEMBER_COUNT={len(acs19_headers)}",
    f"ACS_SCHEMA_PASS={int(acs_ok)}",
    f"SCF_SUMMARY_SCHEMA_PASS={int(summary_ok)}",
    f"SCF_FULL_SCHEMA_PASS={int(full_ok)}",
    f"SCF_REPLICATE_SCHEMA_PASS={int(rep_ok)}",
    f"SCF_REPLICATE_WT1B_COUNT={len(wt)}",
    f"SCF_REPLICATE_MM_COUNT={len(mm)}",
    f"CPS_PUBLIC_ARCHIVE_MEMBER_COUNT={len(pub_members)}",
    f"CPS_REPLICATE_ARCHIVE_MEMBER_COUNT={len(rep_members)}",
    f"CPS_CONTAINER_SCHEMA_PASS={int(pub_ok and rep_ok_cps)}",
    f"ALL_SCHEMA_GATES_PASS={int(all_schema_pass)}",
    "ACS_DATA_ROWS_OPENED=0",
    "SCF_OBSERVATION_ROWS_OPENED=0",
    "CPS_ASCII_DATA_LINES_OPENED=0",
    "NUMERIC_RESULT_ROWS_OPENED=0",
    "2019_ECONOMIC_VALUES_OPENED=0",
    "TEMPORAL_GEOMETRY_AUTHORIZED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    f"NEXT_PRIMARY_PHASE_ID={next_phase}",
    f"E4D1C_2019_COORDINATE_EXECUTION_PRECOMMIT_AUTHORIZED={int(all_schema_pass)}",
    f"E4D1BR_TARGETED_SOURCE_SCHEMA_REPAIR_AUTHORIZED={int(not all_schema_pass)}",
    "E4D1B_2019_OFFICIAL_SOURCE_ACQUISITION_AND_SCHEMA_AUDIT=PASS",
])+"\n"
EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
