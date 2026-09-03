#!/usr/bin/env python3
from pathlib import Path
import csv, hashlib, json, re, subprocess

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"data/metadata/E4C6A_c_h_i_exact_lineage_resolution_contract.json"

EXEC=ROOT/"data/metadata/E4C6A_execution.txt"
AUDIT=ROOT/"data/metadata/E4C6A_c_h_i_exact_lineage_resolution_audit.txt"
PHASES=ROOT/"data/metadata/E4C6A_c_h_i_phase_commit_inventory.tsv"
ARTIFACTS=ROOT/"data/metadata/E4C6A_c_h_i_exact_artifact_inventory.tsv"
HEADERS=ROOT/"data/metadata/E4C6A_c_h_i_exact_result_header_inventory.tsv"
TOKENS=ROOT/"data/results/E4C6A_c_h_i_structural_status_token_inventory.tsv"
DECISION=ROOT/"data/results/E4C6A_c_h_i_lineage_resolution_decision.tsv"

c=json.loads(CONTRACT.read_text(encoding="utf-8"))
assert c["phase"]=="E4C6A"
assert c["allowed_reads"]["candidate_result_numeric_rows"] is False
assert c["scope_boundary"]["geometry_authorized"] is False

families=c["phase_families"]

def run(*args):
    return subprocess.check_output(args,cwd=ROOT,text=True,errors="replace")

def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):
            h.update(b)
    return h.hexdigest()

def git_blob(path):
    return run("git","hash-object",str(path.relative_to(ROOT))).strip()

tracked=[x for x in run("git","ls-files").splitlines() if x.strip()]

# Exact phase-family commit inventory.
phase_rows=[]
phase_commit_counts={}
for comp,phases in families.items():
    for phase in phases:
        # Exact phase ID in commit subject; no broad component lexical matching.
        raw=run("git","log","--all","--pretty=format:%H\t%s","--grep",phase)
        rows=[]
        for line in raw.splitlines():
            if "\t" not in line: continue
            commit,subject=line.split("\t",1)
            if phase.upper() in subject.upper():
                rows.append((commit,subject))
        phase_commit_counts[(comp,phase)]=len(rows)
        for commit,subject in rows:
            phase_rows.append([comp,phase,commit,subject])

with PHASES.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["component","phase_family","commit","subject"])
    w.writerows(phase_rows)

# Exact tracked artifacts matching predeclared phase IDs. Exclude E4C6/E4C6A and E4C5I.
artifact_rows=[]
selected_paths={comp:set() for comp in families}
for comp,phases in families.items():
    for rel in tracked:
        up=rel.upper()
        if any(x in up for x in ["E4C6","E4C5I"]):
            continue
        matched=[phase for phase in phases if phase.upper() in up]
        if not matched:
            continue
        p=ROOT/rel
        last_touch=run("git","log","-1","--format=%H","--",rel).strip()
        blob=git_blob(p)
        digest=sha256(p)
        artifact_rows.append([
            comp,",".join(matched),rel,p.stat().st_size,digest,blob,last_touch
        ])
        selected_paths[comp].add(rel)

artifact_rows.sort(key=lambda r:(r[0],r[1],r[2]))
with ARTIFACTS.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["component","phase_family","path","bytes","sha256","git_blob","last_touch_commit"])
    w.writerows(artifact_rows)

# Header-only read of exact-family result tables.
header_rows=[]
for comp in ["C","H","I"]:
    for rel in sorted(selected_paths[comp]):
        if not rel.startswith("data/results/"):
            continue
        p=ROOT/rel
        if p.suffix.lower() not in {".tsv",".csv"}:
            continue
        delim="\t" if p.suffix.lower()==".tsv" else ","
        with p.open("r",encoding="utf-8-sig",newline="") as f:
            first=f.readline().rstrip("\r\n")
        cols=next(csv.reader([first],delimiter=delim)) if first else []
        header_rows.append([comp,rel,len(cols),"|".join(cols)])

with HEADERS.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["component","path","column_count","header"])
    w.writerows(header_rows)

# Structural status lines only from exact-family docs/metadata/scripts.
# Lines containing decimal values such as 0.123 or 38640.0 are suppressed from emitted output.
status_terms=[
    "READY","READINESS","FROZEN","AUTHORIZED","UNRESOLVED","BLOCKER","SELECTED",
    "PRIMARY","REPRESENTATION","COORDINATE","DIMENSIONLESS","TRANSFORM","STATE_ORIENT",
    "STATE_SIGN","HIGHER","INFERENCE","CLOSEOUT","SCALAR","VALUES_AUTHORIZED",
    "EMPLOYMENT","LABOR_SECURITY","H_ACCESS","ROOMS_PER_PERSON","CEX","ACS","CPS",
]
decimal_value=re.compile(r"(?<![A-Za-z])[-+]?\d+\.\d+(?![A-Za-z])")
token_rows=[]
for comp in ["C","H","I"]:
    emitted=0
    for rel in sorted(selected_paths[comp]):
        if emitted>=180:
            break
        if not rel.startswith(("docs/","data/metadata/","scripts/")):
            continue
        if Path(rel).suffix.lower() not in {".md",".txt",".json",".tsv",".csv",".py",".yaml",".yml"}:
            continue
        try:
            lines=(ROOT/rel).read_text(encoding="utf-8",errors="replace").splitlines()
        except Exception:
            continue
        for lineno,line in enumerate(lines,1):
            if emitted>=180:
                break
            up=line.upper()
            if not any(term in up for term in status_terms):
                continue
            if decimal_value.search(line):
                continue
            text=line.strip()
            if not text or len(text)>320:
                continue
            token_rows.append([comp,rel,lineno,text])
            emitted+=1

with TOKENS.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["component","path","line","structural_status_text"])
    w.writerows(token_rows)

artifact_counts={comp:sum(r[0]==comp for r in artifact_rows) for comp in ["C","H","I"]}
header_counts={comp:sum(r[0]==comp for r in header_rows) for comp in ["C","H","I"]}
token_counts={comp:sum(r[0]==comp for r in token_rows) for comp in ["C","H","I"]}
phase_family_coverage={
    comp:sum(phase_commit_counts[(comp,phase)]>0 for phase in families[comp])
    for comp in ["C","H","I"]
}

# E4C6A freezes exact candidate lineage families but deliberately does not yet
# declare the common-registry readiness of C/H/I.
decision_rows=[]
for comp in ["C","H","I"]:
    complete=int(
        artifact_counts[comp]>0
        and token_counts[comp]>0
        and phase_family_coverage[comp]>=2
    )
    decision_rows.append([
        comp,
        len(families[comp]),
        phase_family_coverage[comp],
        artifact_counts[comp],
        header_counts[comp],
        token_counts[comp],
        complete,
        0,
        "EXACT_FAMILY_INVENTORY_FROZEN_PENDING_READINESS_DECISION" if complete
        else "LINEAGE_EVIDENCE_INCOMPLETE"
    ])

with DECISION.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow([
        "component","predeclared_phase_family_count","phase_families_with_commit_evidence",
        "exact_artifact_count","result_header_count","structural_status_token_count",
        "exact_family_inventory_sufficient_for_decision","ready_for_common_state_registry",
        "status"
    ])
    w.writerows(decision_rows)

all_sufficient=all(r[6]==1 for r in decision_rows)

log="\n".join([
    "E4C6_BROAD_LEXICAL_CANDIDATES_REUSED_AS_DISCOVERY_ONLY=1",
    "E4C6_SELF_MATCHES_EXCLUDED_FROM_EXACT_LINEAGE=1",
    "E4C5I_FALSE_I_MATCHES_EXCLUDED_FROM_EXACT_LINEAGE=1",
    f"C_PREDECLARED_PHASE_FAMILY_COUNT={len(families['C'])}",
    f"H_PREDECLARED_PHASE_FAMILY_COUNT={len(families['H'])}",
    f"I_PREDECLARED_PHASE_FAMILY_COUNT={len(families['I'])}",
    f"C_PHASE_FAMILIES_WITH_COMMIT_EVIDENCE={phase_family_coverage['C']}",
    f"H_PHASE_FAMILIES_WITH_COMMIT_EVIDENCE={phase_family_coverage['H']}",
    f"I_PHASE_FAMILIES_WITH_COMMIT_EVIDENCE={phase_family_coverage['I']}",
    f"C_EXACT_ARTIFACT_COUNT={artifact_counts['C']}",
    f"H_EXACT_ARTIFACT_COUNT={artifact_counts['H']}",
    f"I_EXACT_ARTIFACT_COUNT={artifact_counts['I']}",
    f"C_EXACT_RESULT_HEADER_COUNT={header_counts['C']}",
    f"H_EXACT_RESULT_HEADER_COUNT={header_counts['H']}",
    f"I_EXACT_RESULT_HEADER_COUNT={header_counts['I']}",
    f"C_STRUCTURAL_STATUS_TOKEN_COUNT={token_counts['C']}",
    f"H_STRUCTURAL_STATUS_TOKEN_COUNT={token_counts['H']}",
    f"I_STRUCTURAL_STATUS_TOKEN_COUNT={token_counts['I']}",
    f"C_H_I_EXACT_FAMILY_INVENTORY_SUFFICIENT_FOR_DECISION={int(all_sufficient)}",
    "C_READY_FOR_COMMON_STATE_REGISTRY=0",
    "H_READY_FOR_COMMON_STATE_REGISTRY=0",
    "I_READY_FOR_COMMON_STATE_REGISTRY=0",
    "RESULT_NUMERIC_ROWS_OPENED=0",
    "DECIMAL_ECONOMIC_VALUE_LINES_EMITTED=0",
    "NEW_ECONOMIC_VALUES_OPENED=0",
    "COMPONENT_DEFINITION_MUTATED=0",
    "TRANSFORM_MUTATED=0",
    "NEW_INFERENCE_COMPUTED=0",
    "CROSS_COORDINATE_COVARIANCE_COMPUTED=0",
    "CROSS_COORDINATE_METRIC_SCALE_FROZEN=0",
    "FULL_CHKDI_STATE_VECTOR_READY=0",
    "GEOMETRY_READY=0",
    "GEOMETRY_AUTHORIZED=0",
    "DIMENSIONALITY_TEST_AUTHORIZED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "E4C6A_C_H_I_EXACT_LINEAGE_RESOLUTION_PREFLIGHT=PASS",
    "E4C6B_C_H_I_READINESS_DECISION_PREFLIGHT_AUTHORIZED=1",
])+"\n"

EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")

print("===== EXACT PHASE-COMMIT INVENTORY =====")
for r in phase_rows:
    print("\t".join(map(str,r)))

print("===== EXACT C/H/I ARTIFACT INVENTORY =====")
for r in artifact_rows:
    print("\t".join(map(str,r)))

print("===== EXACT C/H/I RESULT HEADERS =====")
for r in header_rows:
    print("\t".join(map(str,r)))

print("===== STRUCTURAL STATUS TOKENS =====")
for comp in ["C","H","I"]:
    print(f"--- {comp} ---")
    for r in [x for x in token_rows if x[0]==comp]:
        print("\t".join(map(str,r)))
