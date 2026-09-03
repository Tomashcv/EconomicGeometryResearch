#!/usr/bin/env python3
from pathlib import Path
import ast, csv, hashlib, os, re

ROOT=Path(__file__).resolve().parents[1]
SCRIPTDIR=ROOT/"scripts"
RESULTDIR=ROOT/"data/results"
METADIR=ROOT/"data/metadata"
DOCDIR=ROOT/"docs"

EXEC=ROOT/"data/metadata/E4C8A0_execution.txt"
AUDIT=ROOT/"data/metadata/E4C8A0_within_survey_covariance_lineage_recon_audit.txt"
SCRIPTS=ROOT/"data/results/E4C8A0_static_script_candidate_inventory.tsv"
DATA=ROOT/"data/results/E4C8A0_data_header_candidate_inventory.tsv"
REFS=ROOT/"data/results/E4C8A0_static_path_reference_inventory.tsv"
DECISION=ROOT/"data/results/E4C8A0_within_survey_covariance_lineage_recon_decision.tsv"

def sha256(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def rel(p):
    return str(p.relative_to(ROOT))

def text(p):
    return p.read_text(encoding="utf-8",errors="replace")

# Strong static tokens; no numeric data content involved.
scf_tokens=[
    "K_FIN_MEAN","D_PIRTOTAL_MEAN","replicate","implicate"
]
cps_tokens=[
    "I_FYFT_SHARE","I_SEARCH_BURDEN_SHARE","replicate"
]

script_rows=[]
relevant_scripts=[]

for p in sorted(SCRIPTDIR.glob("*.py")):
    s=text(p)
    low=s.lower()
    scf_hits=sum(1 for t in scf_tokens if t.lower() in low)
    cps_hits=sum(1 for t in cps_tokens if t.lower() in low)
    if scf_hits>=2 or cps_hits>=2:
        relevant_scripts.append(p)
        script_rows.append([
            rel(p),sha256(p),str(p.stat().st_size),
            str(scf_hits),str(cps_hits),
            "1" if "replicate" in low else "0",
            "1" if "implicate" in low else "0",
            "1" if ("K_FIN_MEAN" in s and "D_PIRTOTAL_MEAN" in s) else "0",
            "1" if ("I_FYFT_SHARE" in s and "I_SEARCH_BURDEN_SHARE" in s) else "0",
        ])

with SCRIPTS.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow([
        "script_path","sha256","size_bytes","scf_static_token_hits","cps_static_token_hits",
        "contains_replicate_token","contains_implicate_token",
        "contains_both_K_D_tokens","contains_both_I_primary_source_tokens"
    ])
    w.writerows(script_rows)

# Extract path-like string literals from relevant scripts.
path_refs=set()
suffixes=(".tsv",".csv",".txt",".json",".parquet",".dta",".dat",".DAT")
for p in relevant_scripts:
    s=text(p)
    try:
        tree=ast.parse(s)
        literals=[n.value for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str)]
    except SyntaxError:
        literals=[]
    for v in literals:
        vv=v.strip()
        if any(x in vv for x in ["data/","results/","metadata/","raw/"]) and vv.endswith(suffixes):
            path_refs.add((rel(p),vv))
        elif vv.endswith(suffixes) and ("/" in vv or "\\" in vv):
            path_refs.add((rel(p),vv))

with REFS.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["referencing_script","static_path_literal","resolved_repo_path_exists","resolved_path"])
    for sp,v in sorted(path_refs):
        q=Path(v)
        if q.is_absolute():
            resolved=q
        else:
            # Resolve common repo-relative and script-relative forms without opening content.
            cand1=ROOT/q
            cand2=(ROOT/"scripts"/q).resolve()
            resolved=cand1 if cand1.exists() else cand2
        exists=resolved.exists()
        try:
            rr=str(resolved.relative_to(ROOT))
        except Exception:
            rr=str(resolved)
        w.writerow([sp,v,"1" if exists else "0",rr])

# Candidate data inventory. Open HEADER ONLY for text table candidates.
# Candidate set comes from relevant filename tokens plus existing statically referenced paths.
candidate_paths=set()
name_tokens=[
    "E4A2E","E4C5G","E4C5H","E4C5I","scf","SCF","replicate","implicate",
    "E4A2D","cps","CPS","cohort_inference"
]
for p in RESULTDIR.iterdir():
    if p.is_file() and any(t in p.name for t in name_tokens):
        candidate_paths.add(p)

for _,v in path_refs:
    q=Path(v)
    if not q.is_absolute():
        q1=ROOT/q
        if q1.exists() and q1.is_file():
            candidate_paths.add(q1)
    elif q.exists() and q.is_file():
        try:
            q.relative_to(ROOT)
            candidate_paths.add(q)
        except Exception:
            pass

data_rows=[]
headers_opened=0
numeric_rows_opened=0

for p in sorted(candidate_paths):
    if not p.exists() or not p.is_file():
        continue
    suffix=p.suffix.lower()
    header=""
    header_opened="0"
    if suffix in {".tsv",".csv"}:
        with p.open("r",encoding="utf-8",errors="replace",newline="") as f:
            header=f.readline().rstrip("\r\n")
        headers_opened+=1
        header_opened="1"
    low=(p.name+" "+header).lower()
    scf_relevance=sum(1 for t in ["k_fin","d_pirtotal","scf","implicate","replicate"] if t in low)
    cps_relevance=sum(1 for t in ["i_fyft","i_search","cps","replicate"] if t in low)
    data_rows.append([
        rel(p),sha256(p),str(p.stat().st_size),suffix or "NONE",
        header_opened,header,
        str(scf_relevance),str(cps_relevance)
    ])

with DATA.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow([
        "path","sha256","size_bytes","suffix","header_opened","header",
        "scf_schema_relevance_score","cps_schema_relevance_score"
    ])
    w.writerows(data_rows)

# Structural summaries only.
scf_script_candidates=sum(1 for r in script_rows if r[7]=="1")
cps_script_candidates=sum(1 for r in script_rows if r[8]=="1")
scf_data_candidates=sum(1 for r in data_rows if int(r[6])>=2)
cps_data_candidates=sum(1 for r in data_rows if int(r[7])>=2)

decision_rows=[
    ["STATIC_SCRIPT_CANDIDATE_COUNT",str(len(script_rows))],
    ["SCF_BOTH_K_D_SCRIPT_CANDIDATE_COUNT",str(scf_script_candidates)],
    ["CPS_BOTH_I_SCRIPT_CANDIDATE_COUNT",str(cps_script_candidates)],
    ["STATIC_PATH_REFERENCE_COUNT",str(len(path_refs))],
    ["DATA_CANDIDATE_COUNT",str(len(data_rows))],
    ["DATA_HEADERS_OPENED",str(headers_opened)],
    ["NUMERIC_DATA_ROWS_OPENED",str(numeric_rows_opened)],
    ["SCF_SCHEMA_RELEVANT_DATA_CANDIDATE_COUNT",str(scf_data_candidates)],
    ["CPS_SCHEMA_RELEVANT_DATA_CANDIDATE_COUNT",str(cps_data_candidates)],
    ["COVARIANCE_VALUES_COMPUTED","0"],
    ["E4C8A_FORMULA_FROZEN","0"],
    ["E4C8B_COVARIANCE_EXECUTION_AUTHORIZED","0"],
    ["CROSS_SURVEY_COVARIANCE_ASSUMED_ZERO","0"],
    ["GEOMETRY_AUTHORIZED","0"],
]
with DECISION.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["decision","value"])
    w.writerows(decision_rows)

log="\n".join([
    "E4C8_REUSED_AS_CANONICAL_COVARIANCE_FEASIBILITY=1",
    "RECON_SCOPE=STATIC_CODE_REFERENCES_PLUS_DATA_HEADERS_ONLY",
    f"STATIC_SCRIPT_CANDIDATE_COUNT={len(script_rows)}",
    f"SCF_BOTH_K_D_SCRIPT_CANDIDATE_COUNT={scf_script_candidates}",
    f"CPS_BOTH_I_SCRIPT_CANDIDATE_COUNT={cps_script_candidates}",
    f"STATIC_PATH_REFERENCE_COUNT={len(path_refs)}",
    f"DATA_CANDIDATE_COUNT={len(data_rows)}",
    f"DATA_HEADERS_OPENED={headers_opened}",
    "NUMERIC_DATA_ROWS_OPENED=0",
    "REGISTRY_NUMERIC_ROWS_OPENED=0",
    "REPLICATE_NUMERIC_ROWS_OPENED=0",
    "IMPLICATE_NUMERIC_ROWS_OPENED=0",
    "COVARIANCE_VALUES_COMPUTED=0",
    "COVARIANCE_SIGN_USED_AS_GATE=0",
    "COVARIANCE_MAGNITUDE_USED_AS_GATE=0",
    "E4C8A_FORMULA_FROZEN=0",
    "E4C8B_COVARIANCE_EXECUTION_AUTHORIZED=0",
    "CROSS_SURVEY_COVARIANCE_ASSUMED_ZERO=0",
    "GEOMETRY_AUTHORIZED=0",
    "E4C8A0_WITHIN_SURVEY_COVARIANCE_LINEAGE_RECON=PASS",
    "E4C8A_FORMULA_AND_LINEAGE_PREFLIGHT_PENDING_REVIEW=1",
])+"\n"

EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")

print(log,end="")
print("===== STATIC SCRIPT CANDIDATES =====")
print(SCRIPTS.read_text(encoding="utf-8"),end="")
print("===== STATIC PATH REFERENCES =====")
print(REFS.read_text(encoding="utf-8"),end="")
print("===== DATA HEADER CANDIDATES — HEADERS ONLY =====")
print(DATA.read_text(encoding="utf-8"),end="")
