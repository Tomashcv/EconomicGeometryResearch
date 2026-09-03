#!/usr/bin/env python3
from pathlib import Path
import csv, json, re, subprocess

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"data/metadata/E4C6_full_state_vector_readiness_contract.json"
I_DECISION=ROOT/"data/results/E4C5I_k_d_component_inference_closeout_decision.tsv"

EXEC=ROOT/"data/metadata/E4C6_execution.txt"
AUDIT=ROOT/"data/metadata/E4C6_full_state_vector_readiness_audit.txt"
CANDIDATES=ROOT/"data/metadata/E4C6_component_lineage_candidates.tsv"
HEADERS=ROOT/"data/metadata/E4C6_candidate_result_headers.tsv"
HISTORY=ROOT/"data/metadata/E4C6_component_git_history_candidates.tsv"
DECISION=ROOT/"data/results/E4C6_full_state_vector_readiness_decision.tsv"

c=json.loads(CONTRACT.read_text())
assert c["phase"]=="E4C6"
assert c["discovery_sources"]["result_table_headers_only"] is True
assert c["discovery_sources"]["result_numeric_rows"] is False
assert c["scope_boundary"]["geometry_authorized"] is False

with I_DECISION.open("r",encoding="utf-8",newline="") as f:
    kd={r["decision"]:r["value"] for r in csv.DictReader(f,delimiter="\t")}
assert kd["K_D_COMPONENT_INFERENCE_CLOSED"]=="1"
assert kd["K_D_READY_FOR_LATER_STATE_REGISTRY"]=="1"
assert kd["K_D_CROSS_COORDINATE_COVARIANCE_COMPUTED"]=="0"

def run(*args):
    return subprocess.check_output(args,cwd=ROOT,text=True,errors="replace")

tracked=[x for x in run("git","ls-files").splitlines() if x.strip()]
subjects=run("git","log","--all","--pretty=format:%H\t%s").splitlines()

profiles={
    "C":{
        "path":["cex","consum","component_c","c_access","purchas"],
        "content":["CEX","CONSUMPT","COMPONENT C","C COMPONENT","PURCHAS"],
        "source":["CEX"]
    },
    "H":{
        "path":["acs","housing","component_h","h_access","rooms"],
        "content":["ACS","HOUSING","H_ACCESS","ROOMS","COMPONENT H","H COMPONENT"],
        "source":["ACS"]
    },
    "I":{
        "path":["cps","employment","labor","labour","component_i","fyft","search"],
        "content":["CPS","EMPLOY","LABOR","LABOUR","FYFT","COMPONENT I","I COMPONENT"],
        "source":["CPS"]
    }
}
content_roots=("docs/","data/metadata/","scripts/")
text_ext={".md",".txt",".json",".tsv",".csv",".py",".yaml",".yml"}

def norm(s):
    return re.sub(r"[^A-Z0-9]+","_",str(s).upper()).strip("_")

candidate_rows=[]
header_paths=set()

for comp,p in profiles.items():
    for rel in tracked:
        low=rel.lower()
        path_hits=sum(term in low for term in p["path"])
        content_hits=source_hit=state_hit=cohort_hit=uncert_hit=0
        if rel.startswith(content_roots) and Path(rel).suffix.lower() in text_ext:
            try:
                up=(ROOT/rel).read_text(encoding="utf-8",errors="replace").upper()
            except Exception:
                up=""
            content_hits=sum(term in up for term in p["content"])
            source_hit=int(any(term in up for term in p["source"]))
            state_hit=int(any(term in up for term in ["TRANSFORM","DIMENSIONLESS","STATE_ORIENT","STATE SIGN","HIGHER BETTER"]))
            cohort_hit=int(any(term in up for term in ["AGE_BAND","TENURE","OWNER","RENTER","COHORT"]))
            uncert_hit=int(any(term in up for term in ["VARIANCE","STANDARD_ERROR","COMBINED_SE","REPLICATE","UNCERTAINT","MOE"]))
        result_path=int(rel.startswith("data/results/") and Path(rel).suffix.lower() in {".tsv",".csv"})
        if result_path and path_hits:
            header_paths.add(rel)
        score=3*path_hits + 2*content_hits + 2*source_hit + state_hit + cohort_hit + uncert_hit
        if score:
            candidate_rows.append([comp,score,path_hits,content_hits,source_hit,state_hit,cohort_hit,uncert_hit,result_path,rel])

candidate_rows.sort(key=lambda r:(r[0],-int(r[1]),r[-1]))
with CANDIDATES.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["component","score","path_term_hits","content_term_hits","source_evidence","state_or_transform_evidence","cohort_schema_evidence","uncertainty_term_evidence","result_path","path"])
    w.writerows(candidate_rows)

header_rows=[]
for rel in sorted(header_paths):
    p=ROOT/rel
    delim="\t" if p.suffix.lower()==".tsv" else ","
    try:
        with p.open("r",encoding="utf-8-sig",newline="") as f:
            first=f.readline().rstrip("\r\n")
        cols=next(csv.reader([first],delimiter=delim)) if first else []
    except Exception:
        cols=[]
    for comp,prof in profiles.items():
        if not any(term in rel.lower() for term in prof["path"]):
            continue
        ncols=[norm(x) for x in cols]
        point=int(any(any(k in x for k in ["POINT","ESTIMATE","STATE","VALUE"]) for x in ncols))
        cohort=int(any("AGE" in x or "TENURE" in x or x in {"OWNER","RENTER","COHORT"} for x in ncols))
        uncert=int(any(any(k in x for k in ["VARIANCE","SE","STDERR","STANDARD_ERROR","MOE","REPLICATE","UNCERTAINT"]) for x in ncols))
        header_rows.append([comp,rel,len(cols),"|".join(cols),point,cohort,uncert])

with HEADERS.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["component","path","column_count","header","point_schema_evidence","cohort_schema_evidence","uncertainty_schema_evidence"])
    w.writerows(header_rows)

history_terms={
    "C":["CEX","CONSUM","COMPONENT C"],
    "H":["ACS","HOUS","H_ACCESS","COMPONENT H"],
    "I":["CPS","EMPLOY","LABOR","FYFT","COMPONENT I"],
}
history_rows=[]
for line in subjects:
    if "\t" not in line: continue
    commit,subject=line.split("\t",1)
    up=subject.upper()
    for comp,terms in history_terms.items():
        if any(t in up for t in terms):
            history_rows.append([comp,commit,subject])

with HISTORY.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["component","commit","subject"])
    w.writerows(history_rows)

counts={x:sum(r[0]==x for r in candidate_rows) for x in ["C","H","I"]}
hcounts={x:sum(r[0]==x for r in header_rows) for x in ["C","H","I"]}
gcounts={x:sum(r[0]==x for r in history_rows) for x in ["C","H","I"]}

decision_rows=[
    ["C","CANDIDATE_LINEAGE_DISCOVERED" if counts["C"] else "NO_CANDIDATE_LINEAGE_DISCOVERED",counts["C"],hcounts["C"],gcounts["C"],0,0],
    ["H","CANDIDATE_LINEAGE_DISCOVERED" if counts["H"] else "NO_CANDIDATE_LINEAGE_DISCOVERED",counts["H"],hcounts["H"],gcounts["H"],0,0],
    ["K","COMPONENT_INFERENCE_CLOSED",0,0,0,1,1],
    ["D","COMPONENT_INFERENCE_CLOSED",0,0,0,1,1],
    ["I","CANDIDATE_LINEAGE_DISCOVERED" if counts["I"] else "NO_CANDIDATE_LINEAGE_DISCOVERED",counts["I"],hcounts["I"],gcounts["I"],0,0],
]
with DECISION.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["component","status","candidate_artifact_count","candidate_result_header_count","git_history_candidate_count","exact_lineage_resolved","ready_for_common_state_registry"])
    w.writerows(decision_rows)

all_candidates=all(counts[x]>0 for x in ["C","H","I"])

log="\n".join([
    "K_COMPONENT_INFERENCE_CLOSED=1",
    "D_COMPONENT_INFERENCE_CLOSED=1",
    "K_READY_FOR_COMMON_STATE_REGISTRY=1",
    "D_READY_FOR_COMMON_STATE_REGISTRY=1",
    f"C_LINEAGE_CANDIDATE_COUNT={counts['C']}",
    f"H_LINEAGE_CANDIDATE_COUNT={counts['H']}",
    f"I_LINEAGE_CANDIDATE_COUNT={counts['I']}",
    f"C_CANDIDATE_RESULT_HEADER_COUNT={hcounts['C']}",
    f"H_CANDIDATE_RESULT_HEADER_COUNT={hcounts['H']}",
    f"I_CANDIDATE_RESULT_HEADER_COUNT={hcounts['I']}",
    f"C_GIT_HISTORY_CANDIDATE_COUNT={gcounts['C']}",
    f"H_GIT_HISTORY_CANDIDATE_COUNT={gcounts['H']}",
    f"I_GIT_HISTORY_CANDIDATE_COUNT={gcounts['I']}",
    "C_EXACT_LINEAGE_RESOLVED=0",
    "H_EXACT_LINEAGE_RESOLVED=0",
    "I_EXACT_LINEAGE_RESOLVED=0",
    f"C_H_I_ALL_HAVE_STRUCTURAL_CANDIDATES={int(all_candidates)}",
    "RESULT_NUMERIC_ROWS_OPENED=0",
    "NEW_ECONOMIC_VALUES_OPENED=0",
    "SIGN_USED_AS_READINESS_GATE=0",
    "MAGNITUDE_USED_AS_READINESS_GATE=0",
    "STATISTICAL_SIGNIFICANCE_USED_AS_READINESS_GATE=0",
    "FULL_CHKDI_STATE_VECTOR_READY=0",
    "K_D_COVARIANCE_COMPUTED=0",
    "CROSS_COORDINATE_METRIC_SCALE_FROZEN=0",
    "GEOMETRY_READY=0",
    "GEOMETRY_AUTHORIZED=0",
    "DIMENSIONALITY_TEST_AUTHORIZED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "E4C6_FULL_STATE_VECTOR_READINESS_PREFLIGHT=PASS",
    "E4C6A_C_H_I_EXACT_LINEAGE_RESOLUTION_PREFLIGHT_AUTHORIZED=1",
])+"\n"
EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")

print("===== TOP C/H/I LINEAGE CANDIDATES =====")
for comp in ["C","H","I"]:
    print(f"--- {comp} ---")
    for r in [x for x in candidate_rows if x[0]==comp][:20]:
        print("\t".join(map(str,r)))

print("===== C/H/I CANDIDATE RESULT HEADERS =====")
for r in header_rows:
    print("\t".join(map(str,r)))

print("===== C/H/I GIT HISTORY CANDIDATES =====")
for r in history_rows[:80]:
    print("\t".join(map(str,r)))
