#!/usr/bin/env python3
from pathlib import Path
import csv, hashlib, json, os, re, subprocess

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"data/metadata/E4C5E_transformed_inference_method_contract.json"

RAW_POINT=ROOT/"data/results/E4A2F_2022_scf_kd_cohort_inference.tsv"
RAW_IMPL=ROOT/"data/results/E4A2F_2022_scf_kd_implicate_statistics.tsv"
RAW_REP=ROOT/"data/results/E4A2F_2022_scf_kd_replicate_statistics.tsv"

EXEC=ROOT/"data/metadata/E4C5E_execution.txt"
AUDIT=ROOT/"data/metadata/E4C5E_transformed_inference_method_audit.txt"
CAND=ROOT/"data/metadata/E4C5E_E4A2F_inference_engine_candidates.tsv"
HDR=ROOT/"data/metadata/E4C5E_raw_inference_table_headers.tsv"
TOK=ROOT/"data/results/E4C5E_E4A2F_inference_engine_token_inventory.tsv"
DEC=ROOT/"data/results/E4C5E_transformed_inference_method_decision.tsv"

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):
            h.update(b)
    return h.hexdigest()

def first_header(p):
    with p.open("r",encoding="utf-8-sig",newline="") as f:
        line=f.readline().rstrip("\r\n")
    if not line:
        raise RuntimeError(f"empty table: {p}")
    return line.split("\t")

c=json.loads(CONTRACT.read_text(encoding="utf-8"))
assert c["phase"]=="E4C5E"
assert c["engine_forensic"]["target_numeric_result_rows_opened_in_E4C5E"] is False
assert c["engine_forensic"]["transformed_replicate_values_computed"] is False
assert c["engine_forensic"]["transformed_uncertainty_computed"] is False

# Header-only table inventory.
headers={
    "COMBINED":first_header(RAW_POINT),
    "IMPLICATE":first_header(RAW_IMPL),
    "REPLICATE":first_header(RAW_REP),
}

with HDR.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["table_role","path","sha256","column_count","columns"])
    for role,p in [("COMBINED",RAW_POINT),("IMPLICATE",RAW_IMPL),("REPLICATE",RAW_REP)]:
        w.writerow([role,str(p.relative_to(ROOT)),sha(p),len(headers[role]),",".join(headers[role])])

# Discover tracked E4A2F Python scripts only. No result rows are read.
proc=subprocess.run(
    ["git","ls-files","scripts/E4A2F*.py"],
    cwd=ROOT,check=True,text=True,capture_output=True
)
paths=[ROOT/x for x in proc.stdout.splitlines() if x.strip()]
if not paths:
    raise RuntimeError("no tracked scripts/E4A2F*.py candidates")

required_families={
    "IMPUTATION":["IMPUTATION","IMPLICATE"],
    "SAMPLING":["SAMPLING","REPLICATE"],
    "COMBINED":["COMBINED","VARIANCE"],
}

candidate_rows=[]
token_rows=[]
qualified=[]

for p in paths:
    text=p.read_text(encoding="utf-8")
    upper=text.upper()
    has_imp=("IMPUTATION" in upper and "IMPLICATE" in upper)
    has_sampling=("SAMPLING" in upper and "REPLICATE" in upper)
    has_combined=("COMBINED" in upper and "VARIANCE" in upper)
    has_999=("999" in text)
    has_5=("IMPLICATE" in upper and re.search(r"\b5\b",text) is not None)
    score=sum([has_imp,has_sampling,has_combined,has_999,has_5])
    candidate_rows.append([
        str(p.relative_to(ROOT)),sha(p),int(has_imp),int(has_sampling),
        int(has_combined),int(has_999),int(has_5),score
    ])
    if has_imp and has_sampling and has_combined:
        qualified.append(p)

    for lineno,line in enumerate(text.splitlines(),start=1):
        up=line.upper()
        if any(tok in up for tok in [
            "IMPUTATION_VARIANCE","SAMPLING_VARIANCE","COMBINED_VARIANCE",
            "IMPLICATE","REPLICATE","VARIANCE","6/5","6.0/5.0","1.2"
        ]):
            # Source-code text only; never result-table values.
            token_rows.append([str(p.relative_to(ROOT)),lineno,line.strip()])

with CAND.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow([
        "path","sha256","has_imputation_implicate_terms",
        "has_sampling_replicate_terms","has_combined_variance_terms",
        "has_literal_999","has_literal_5_near_engine_source","semantic_score"
    ])
    w.writerows(candidate_rows)

with TOK.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["path","line_number","source_text"])
    w.writerows(token_rows)

# E4C5E is allowed to choose the method family, but not to pretend that a
# variance engine was uniquely frozen if source discovery is ambiguous.
unique_engine=(len(qualified)==1)
engine_path=str(qualified[0].relative_to(ROOT)) if unique_engine else "UNRESOLVED"
engine_sha=sha(qualified[0]) if unique_engine else "UNRESOLVED"

with DEC.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["decision","value"])
    w.writerows([
        ["K_METHOD_FAMILY","DIRECT_TRANSFORM_ATOMIC_IMPLICATES_AND_REPLICATES"],
        ["D_METHOD_FAMILY","DIRECT_TRANSFORM_ATOMIC_IMPLICATES_AND_REPLICATES"],
        ["DELTA_METHOD_SELECTED",0],
        ["E4A2F_TRACKED_PYTHON_CANDIDATE_COUNT",len(paths)],
        ["E4A2F_QUALIFIED_INFERENCE_ENGINE_CANDIDATE_COUNT",len(qualified)],
        ["E4A2F_UNIQUE_INFERENCE_ENGINE_DISCOVERED",int(unique_engine)],
        ["E4A2F_INFERENCE_ENGINE_PATH",engine_path],
        ["E4A2F_INFERENCE_ENGINE_SHA256",engine_sha],
        ["TARGET_NUMERIC_RESULT_ROWS_OPENED_IN_E4C5E",0],
        ["TRANSFORMED_REPLICATE_VALUES_COMPUTED",0],
        ["TRANSFORMED_UNCERTAINTY_COMPUTED",0],
        ["E4C5F_EXACT_ENGINE_FREEZE_PREFLIGHT_AUTHORIZED",1],
        ["E4C5F_TRANSFORMED_INFERENCE_EXECUTION_AUTHORIZED",0],
    ])

log="\n".join([
    "K_DOMAIN_FEASIBILITY_REUSED=1",
    "K_FULL_REPLICATE_TRANSFORM_DOMAIN_FEASIBLE=1",
    "D_FULL_REPLICATE_TRANSFORM_DOMAIN_FEASIBLE=1",
    "K_METHOD_FAMILY=DIRECT_TRANSFORM_ATOMIC_IMPLICATES_AND_REPLICATES",
    "D_METHOD_FAMILY=DIRECT_TRANSFORM_ATOMIC_IMPLICATES_AND_REPLICATES",
    "DELTA_METHOD_SELECTED=0",
    "RAW_E4A2F_VARIANCE_ENGINE_MUST_BE_REUSED_EXACTLY=1",
    "VARIANCE_COEFFICIENT_REDERIVATION_IN_E4C5E=0",
    "RESULT_TABLE_HEADERS_OPENED=1",
    "TARGET_NUMERIC_RESULT_ROWS_OPENED_IN_E4C5E=0",
    f"E4A2F_TRACKED_PYTHON_CANDIDATE_COUNT={len(paths)}",
    f"E4A2F_QUALIFIED_INFERENCE_ENGINE_CANDIDATE_COUNT={len(qualified)}",
    f"E4A2F_UNIQUE_INFERENCE_ENGINE_DISCOVERED={int(unique_engine)}",
    f"E4A2F_INFERENCE_ENGINE_PATH={engine_path}",
    f"E4A2F_INFERENCE_ENGINE_SHA256={engine_sha}",
    "TRANSFORMED_REPLICATE_VALUES_COMPUTED=0",
    "TRANSFORMED_UNCERTAINTY_COMPUTED=0",
    "OWNER_RENTER_DIRECTION_USED_AS_METHOD_GATE=0",
    "STATISTICAL_SIGNIFICANCE_USED_AS_METHOD_GATE=0",
    "MAGNITUDE_USED_AS_METHOD_GATE=0",
    "K_D_COVARIANCE_COMPUTED=0",
    "CROSS_COORDINATE_METRIC_SCALE_FROZEN=0",
    "GEOMETRY_READY=0",
    "GEOMETRY_AUTHORIZED=0",
    "DIMENSIONALITY_TEST_AUTHORIZED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "E4C5E_TRANSFORMED_INFERENCE_METHOD_PREFLIGHT=PASS",
    "E4C5F_EXACT_ENGINE_FREEZE_PREFLIGHT_AUTHORIZED=1",
    "E4C5F_TRANSFORMED_INFERENCE_EXECUTION_AUTHORIZED=0",
])+"\n"

EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
print("===== E4A2F ENGINE CANDIDATES =====")
for r in candidate_rows:
    print("\t".join(map(str,r)))
print("===== RAW TABLE HEADERS =====")
for role in ["COMBINED","IMPLICATE","REPLICATE"]:
    print(role+"\t"+"\t".join(headers[role]))
