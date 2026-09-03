#!/usr/bin/env python3
from pathlib import Path
import csv, hashlib, json, re, subprocess

ROOT=Path(__file__).resolve().parents[1]

CONTRACT=ROOT/"data/metadata/E4C5B_first_k_d_transform_execution_contract.json"
LINEAGE=ROOT/"data/metadata/E4C5B_frozen_input_lineage.tsv"
PRIOR_KD=ROOT/"data/metadata/E4C5_prior_k_d_semantic_lineage.tsv"

EXEC=ROOT/"data/metadata/E4C5B_execution.txt"
AUDIT=ROOT/"data/metadata/E4C5B_first_k_d_transform_execution_preflight_audit.txt"
POOL=ROOT/"data/metadata/E4C5B_target_k_d_source_pool.tsv"
SCHEMA=ROOT/"data/results/E4C5B_expected_transform_execution_schema.tsv"
GATES=ROOT/"data/results/E4C5B_first_transform_hard_gates.tsv"

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):
            h.update(b)
    return h.hexdigest()

def tracked():
    return set(filter(None,subprocess.check_output(["git","ls-files"],cwd=ROOT,text=True).splitlines()))

def read_tsv(p):
    with p.open("r",encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f,delimiter="\t"))

c=json.loads(CONTRACT.read_text(encoding="utf-8"))
assert c["phase"]=="E4C5B"
assert c["input_policy"]["target_numeric_K_D_values_opened"] is False
assert c["frozen_parameters"]["K_REF_FIN_USD"]==38640.0
assert c["frozen_parameters"]["D_multiplier_to_fraction"]==1.0
assert c["hard_boundaries"]["transformed_K_D_values_computed"] is False

for r in read_tsv(LINEAGE):
    p=ROOT/r["artifact"]
    if not p.exists() or sha(p)!=r["sha256"]:
        raise RuntimeError(f"lineage mismatch: {r['artifact']}")

all_tracked=tracked()

# Discovery is path/reference only. Candidate result files are never text-parsed here.
direct={
    p for p in all_tracked
    if p.startswith("data/results/E4A")
    and Path(p).suffix.lower() in {".tsv",".csv",".txt"}
}

# Build a non-result text set from frozen K/D semantic lineage and nearby semantic phases.
semantic_text=set()
for r in read_tsv(PRIOR_KD):
    p=r["artifact"]
    if p in all_tracked and not p.startswith("data/results/"):
        semantic_text.add(p)

for p in all_tracked:
    if p.startswith(("docs/E4A","docs/E4B3","docs/E4C0","docs/E4C1",
                     "scripts/E4A","scripts/E4B3","scripts/E4C0","scripts/E4C1",
                     "data/metadata/E4A","data/metadata/E4B3","data/metadata/E4C0","data/metadata/E4C1")):
        semantic_text.add(p)

ref_pat=re.compile(r"data/results/[A-Za-z0-9_.\-/]+\.(?:tsv|csv|txt)")
refs={}
for p in sorted(semantic_text):
    fp=ROOT/p
    try:
        text=fp.read_text(encoding="utf-8")
    except Exception:
        continue
    for m in ref_pat.finditer(text):
        rp=m.group(0)
        if rp not in all_tracked:
            continue
        # Context is used only for a nonnumeric role hint.
        lo=max(0,m.start()-280); hi=min(len(text),m.end()+280)
        ctx=text[lo:hi].upper()
        hint=set()
        if any(k in ctx for k in ["PIRTOTAL","DEBT2INC","DEBT BURDEN","DEBT_SERVICE","DEBT SERVICE"]):
            hint.add("D")
        if any(k in ctx for k in ["K_FIN","FIN_MEAN","FINANCIAL CAPITAL","CAPITAL POSITION"]):
            hint.add("K")
        refs.setdefault(rp,{"origins":set(),"hints":set()})
        refs[rp]["origins"].add(p)
        refs[rp]["hints"].update(hint)

pool=set(direct) | set(refs)

# Keep source pool bounded to the intended research stages.
pool={
    p for p in pool
    if p.startswith("data/results/")
    and (
        "/E4A" in p or "/E4B3" in p or Path(p).name.startswith(("E4A","E4B3"))
    )
}

if len(pool)<2:
    raise RuntimeError(f"insufficient frozen K/D target source pool: {sorted(pool)}")
if len(pool)>80:
    raise RuntimeError(f"unexpectedly broad K/D target source pool: {len(pool)} files")

rows=[]
k_hint=0
d_hint=0
for p in sorted(pool):
    hint=refs.get(p,{}).get("hints",set())
    if "K" in hint:k_hint+=1
    if "D" in hint:d_hint+=1
    role="BOTH" if hint=={"K","D"} else ("K" if hint=={"K"} else ("D" if hint=={"D"} else "UNRESOLVED"))
    origins=sorted(refs.get(p,{}).get("origins",set()))
    rows.append([
        p,sha(ROOT/p),role,
        str(int(p in direct)),
        str(len(origins)),
        ";".join(origins) if origins else "NA"
    ])

with POOL.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["artifact","sha256","semantic_role_hint","direct_E4A_result_path","reference_origin_count","reference_origins"])
    w.writerows(rows)

schema_rows=[
    ("data/results/E4C5C_k_d_transformed_point_estimates.tsv","16","8 K + 8 D primary target cells"),
    ("data/metadata/E4C5C_target_source_selection.tsv","SOURCE_DEFINED","exact source rows/files selected by frozen parser"),
    ("data/metadata/E4C5C_execution.txt","1","execution audit"),
    ("data/metadata/E4C5C_first_k_d_transform_execution_audit.txt","1","byte-identical audit"),
]
with SCHEMA.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["artifact","expected_rows","meaning"])
    w.writerows(schema_rows)

gate_rows=[
    ("SOURCE_POOL_SHA256_FROZEN","1"),
    ("TARGET_NUMERIC_VALUES_OPENED_IN_E4C5B","0"),
    ("PRIMARY_K_CELL_COUNT_REQUIRED","8"),
    ("PRIMARY_D_CELL_COUNT_REQUIRED","8"),
    ("K_DOMAIN_FINITE_NONNEGATIVE_REQUIRED","1"),
    ("D_DOMAIN_FINITE_REQUIRED","1"),
    ("OWNER_RENTER_DIRECTION_GATE","0"),
    ("STATISTICAL_SIGNIFICANCE_GATE","0"),
    ("CROSS_COORDINATE_METRIC_SCALE_FROZEN","0"),
    ("GEOMETRY_AUTHORIZED","0"),
]
with GATES.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["gate","value"])
    w.writerows(gate_rows)

log="\n".join([
"RAW_SCF_DATA_READ=0",
"TARGET_RESULT_FILES_SHA256_READ=1",
"TARGET_RESULT_FILE_CONTENT_PARSED=0",
"TARGET_NUMERIC_K_D_VALUES_OPENED=0",
"TARGET_K_D_VALUES_TRANSFORMED=0",
"REESTIMATION_PERFORMED=0",
"NEW_REPLICATES_COMPUTED=0",
"FROZEN_E4C5A_PARAMETERS_ONLY=1",
"K_REF_FIN_USD=38640.000000000000",
"D_PIRTOTAL_UNIT=FRACTION",
"D_EXACT_UNIT_MULTIPLIER=1.0",
f"TARGET_SOURCE_POOL_FILE_COUNT={len(rows)}",
f"TARGET_SOURCE_POOL_K_HINT_FILE_COUNT={k_hint}",
f"TARGET_SOURCE_POOL_D_HINT_FILE_COUNT={d_hint}",
"TARGET_SOURCE_POOL_SHA256_FROZEN=1",
"PRIMARY_K_EXPECTED_CELL_COUNT=8",
"PRIMARY_D_EXPECTED_CELL_COUNT=8",
"PRIMARY_TRANSFORMED_POINT_EXPECTED_ROW_COUNT=16",
"K_TRANSFORM=LN1P_K_FIN_MEAN_OVER_38640",
"D_TRANSFORM=NEGATIVE_PIRTOTAL_FRACTION",
"K_DOMAIN_GATE=FINITE_AND_NONNEGATIVE",
"D_DOMAIN_GATE=FINITE",
"OWNER_RENTER_DIRECTION_USED_AS_TRANSFORM_GATE=0",
"STATISTICAL_SIGNIFICANCE_USED_AS_TRANSFORM_GATE=0",
"MAGNITUDE_USED_AS_TRANSFORM_GATE=0",
"GEOMETRY_USED_AS_TRANSFORM_GATE=0",
"REPLICATE_ARCHITECTURE_MUST_BE_INVENTORIED_BEFORE_TRANSFORMED_UNCERTAINTY=1",
"CROSS_COORDINATE_METRIC_SCALE_FROZEN=0",
"GEOMETRY_READY=0",
"GEOMETRY_AUTHORIZED=0",
"DIMENSIONALITY_TEST_AUTHORIZED=0",
"REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
"FINAL_SCALAR_AUTHORIZED=0",
"E4C5B_FIRST_K_D_TRANSFORM_EXECUTION_PREFLIGHT=PASS",
"E4C5C_FIRST_K_D_TRANSFORM_EXECUTION_AUTHORIZED=1",
])+"\n"

EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")

print(log,end="")
print("===== FROZEN TARGET K/D SOURCE POOL — PATHS + ROLE HINTS ONLY =====")
for r in rows:
    print(f"{r[2]}\t{r[0]}\tSHA256={r[1]}")
