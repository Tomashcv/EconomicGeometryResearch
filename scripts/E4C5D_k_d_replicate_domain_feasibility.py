#!/usr/bin/env python3
from pathlib import Path
import csv, collections, hashlib, json, math, re

ROOT=Path(__file__).resolve().parents[1]

REP=ROOT/"data/results/E4A2F_2022_scf_kd_replicate_statistics.tsv"
POINTS=ROOT/"data/results/E4C5C_k_d_transformed_point_estimates.tsv"
CONTRACT=ROOT/"data/metadata/E4C5D_k_d_replicate_domain_feasibility_contract.json"

EXEC=ROOT/"data/metadata/E4C5D_execution.txt"
AUDIT=ROOT/"data/metadata/E4C5D_k_d_replicate_domain_feasibility_audit.txt"
K_SUM=ROOT/"data/results/E4C5D_k_replicate_domain_summary.tsv"
K_INVALID=ROOT/"data/results/E4C5D_k_replicate_domain_invalid_rows.tsv"
D_SUM=ROOT/"data/results/E4C5D_d_replicate_domain_summary.tsv"
ALIGN=ROOT/"data/results/E4C5D_replicate_alignment_summary.tsv"
BRANCH=ROOT/"data/results/E4C5D_method_branch_decision.tsv"

REP_SHA="d7a25d385cab8d3aee0701ca86af19c2525b35fc839d44a01198f5ee6f6d311e"
KREF=38640.0
AGES=["25-34","35-44","45-54","55-64"]
TENS=["OWNER","RENTER"]
EXPECTED_CELLS={(a,t) for a in AGES for t in TENS}

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):
            h.update(b)
    return h.hexdigest()

def norm(x):
    return re.sub(r"[^A-Z0-9]+","_",str(x).strip().upper()).strip("_")

def map_age(x):
    s=str(x).strip().upper().replace("–","-").replace("—","-")
    nums=[int(v) for v in re.findall(r"\d+",s)]
    for lo,hi in [(25,34),(35,44),(45,54),(55,64)]:
        if lo in nums and hi in nums:
            return f"{lo}-{hi}"
    return None

def exact_tenure(x):
    s=norm(x)
    return s if s in {"OWNER","RENTER"} else None

def finite_float(x):
    try:v=float(str(x).strip())
    except Exception:return None
    return v if math.isfinite(v) else None

c=json.loads(CONTRACT.read_text(encoding="utf-8"))
assert c["phase"]=="E4C5D"
assert c["important_boundary"]["direct_transformed_replicate_inference_authorized_in_E4C5D"] is False
assert c["important_boundary"]["delta_method_authorized_in_E4C5D"] is False
assert c["important_boundary"]["transformed_replicate_values_computed"] is False
assert sha(REP)==REP_SHA

selected={"K":[],"D":[]}

with REP.open("r",encoding="utf-8-sig",newline="") as f:
    rd=csv.DictReader(f,delimiter="\t")
    required={"age_band","tenure_or_contrast","statistic_id","replicate","raw_value"}
    missing=required-set(rd.fieldnames or [])
    if missing:
        raise RuntimeError(f"missing replicate fields: {sorted(missing)}")

    for rownum,row in enumerate(rd,start=2):
        sid=norm(row["statistic_id"])
        comp="K" if sid=="K_FIN_MEAN" else ("D" if sid=="D_PIRTOTAL_MEAN" else None)
        if comp is None:
            continue

        age=map_age(row["age_band"])
        ten=exact_tenure(row["tenure_or_contrast"])
        if age is None or ten is None:
            continue

        value=finite_float(row["raw_value"])
        if value is None:
            raise RuntimeError(f"nonfinite selected {comp} replicate row {rownum}")

        rid=str(row["replicate"]).strip()
        if not rid:
            raise RuntimeError(f"blank replicate id row {rownum}")

        selected[comp].append((age,ten,rid,value,rownum))

for comp in ["K","D"]:
    if len(selected[comp])!=7992:
        raise RuntimeError(f"{comp}: selected rows={len(selected[comp])}, expected 7992")
    cells={(a,t) for a,t,_,_,_ in selected[comp]}
    if cells!=EXPECTED_CELLS:
        raise RuntimeError(f"{comp}: target-cell mismatch")

# Every cell must have exactly the same 999-id set.
ids_by_cell={"K":collections.defaultdict(set),"D":collections.defaultdict(set)}
for comp in ["K","D"]:
    counts=collections.Counter()
    for age,ten,rid,value,rownum in selected[comp]:
        counts[(age,ten)]+=1
        ids_by_cell[comp][(age,ten)].add(rid)
    for cell in sorted(EXPECTED_CELLS):
        if counts[cell]!=999 or len(ids_by_cell[comp][cell])!=999:
            raise RuntimeError(f"{comp} cell {cell}: rows={counts[cell]} ids={len(ids_by_cell[comp][cell])}")

    base=ids_by_cell[comp][("25-34","OWNER")]
    if any(ids_by_cell[comp][cell]!=base for cell in EXPECTED_CELLS):
        raise RuntimeError(f"{comp}: replicate-id set differs across cells")

K_IDS=ids_by_cell["K"][("25-34","OWNER")]
D_IDS=ids_by_cell["D"][("25-34","OWNER")]
KD_IDS_EQUAL=(K_IDS==D_IDS)

# K domain audit.
k_stats={}
invalid=[]
for cell in sorted(EXPECTED_CELLS):
    vals=[(rid,v,rownum) for a,t,rid,v,rownum in selected["K"] if (a,t)==cell]
    n_invalid=sum(v<=-KREF for _,v,_ in vals)
    n_valid_neg=sum((-KREF<v<0) for _,v,_ in vals)
    n_nonneg=sum(v>=0 for _,v,_ in vals)
    if n_invalid+n_valid_neg+n_nonneg!=999:
        raise RuntimeError(f"K bin partition failure: {cell}")

    # This margin is diagnostic only; it is not used in the method branch.
    valid_args=[1.0+v/KREF for _,v,_ in vals if v>-KREF]
    min_valid_arg=min(valid_args) if valid_args else math.nan

    k_stats[cell]=(n_invalid,n_valid_neg,n_nonneg,min_valid_arg)
    for rid,v,rownum in vals:
        if v<=-KREF:
            invalid.append((cell[0],cell[1],rid,rownum,v,1.0+v/KREF))

total_invalid=sum(x[0] for x in k_stats.values())
total_valid_negative=sum(x[1] for x in k_stats.values())
total_nonnegative=sum(x[2] for x in k_stats.values())
full_k_domain=(total_invalid==0)

with K_SUM.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow([
        "age_band","tenure","replicate_count",
        "invalid_raw_le_negative_Kref_count",
        "valid_negative_count","valid_nonnegative_count",
        "min_positive_transform_argument_among_valid",
        "full_cell_transform_domain_feasible"
    ])
    for cell in sorted(EXPECTED_CELLS):
        ni,nv,nn,arg=k_stats[cell]
        w.writerow([
            cell[0],cell[1],999,ni,nv,nn,
            "NA" if not math.isfinite(arg) else f"{arg:.12f}",
            int(ni==0)
        ])

with K_INVALID.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["age_band","tenure","replicate","source_row","raw_K_FIN_MEAN","transform_argument_1_plus_raw_over_Kref"])
    for age,ten,rid,rownum,v,arg in sorted(invalid):
        w.writerow([age,ten,rid,rownum,f"{v:.12f}",f"{arg:.12f}"])

# D has only finite-domain requirement.
with D_SUM.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["age_band","tenure","replicate_count","finite_count","nonfinite_count","full_cell_transform_domain_feasible"])
    for cell in sorted(EXPECTED_CELLS):
        n=sum(1 for a,t,_,_,_ in selected["D"] if (a,t)==cell)
        w.writerow([cell[0],cell[1],n,n,0,1])

with ALIGN.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["diagnostic","value"])
    w.writerows([
        ["K_ROWS",len(selected["K"])],
        ["D_ROWS",len(selected["D"])],
        ["K_REPLICATE_IDS_PER_CELL",999],
        ["D_REPLICATE_IDS_PER_CELL",999],
        ["K_IDS_ALIGNED_ACROSS_8_CELLS",1],
        ["D_IDS_ALIGNED_ACROSS_8_CELLS",1],
        ["K_D_REPLICATE_ID_SETS_EQUAL",int(KD_IDS_EQUAL)],
        ["K_D_COVARIANCE_COMPUTED",0],
    ])

branch = (
    "DIRECT_REPLICATE_TRANSFORM_DOMAIN_CANDIDATE"
    if full_k_domain
    else "DIRECT_FULL_REPLICATE_TRANSFORM_DOMAIN_BLOCKED_EVALUATE_ANALYTIC_INFERENCE"
)

with BRANCH.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["decision","value"])
    w.writerows([
        ["K_TOTAL_REPLICATE_ROWS",7992],
        ["K_INVALID_DOMAIN_COUNT",total_invalid],
        ["K_VALID_NEGATIVE_COUNT",total_valid_negative],
        ["K_VALID_NONNEGATIVE_COUNT",total_nonnegative],
        ["K_FULL_REPLICATE_TRANSFORM_DOMAIN_FEASIBLE",int(full_k_domain)],
        ["D_FULL_REPLICATE_TRANSFORM_DOMAIN_FEASIBLE",1],
        ["PRECOMMITTED_METHOD_BRANCH",branch],
        ["DIRECT_TRANSFORMED_REPLICATE_INFERENCE_AUTHORIZED",0],
        ["DELTA_METHOD_AUTHORIZED",0],
        ["POINT_TRANSFORM_MUTATION_AUTHORIZED",0],
        ["E4C5E_METHOD_PREFLIGHT_AUTHORIZED",1],
    ])

log="\n".join([
    "EXACT_E4C5C_COHORT_REPLICATE_FILTER_REUSED=1",
    "K_PRIMARY_STATISTIC_ID=K_FIN_MEAN",
    "D_PRIMARY_STATISTIC_ID=D_PIRTOTAL_MEAN",
    "K_REF_FIN_USD=38640.000000000000",
    "K_REPLICATE_ROWS_AUDITED=7992",
    "D_REPLICATE_ROWS_AUDITED=7992",
    "K_DISTINCT_REPLICATE_ID_COUNT=999",
    "D_DISTINCT_REPLICATE_ID_COUNT=999",
    "K_IDS_ALIGNED_ACROSS_8_CELLS=1",
    "D_IDS_ALIGNED_ACROSS_8_CELLS=1",
    f"K_D_REPLICATE_ID_SETS_EQUAL={int(KD_IDS_EQUAL)}",
    f"K_INVALID_DOMAIN_COUNT={total_invalid}",
    f"K_VALID_NEGATIVE_COUNT={total_valid_negative}",
    f"K_VALID_NONNEGATIVE_COUNT={total_nonnegative}",
    f"K_FULL_REPLICATE_TRANSFORM_DOMAIN_FEASIBLE={int(full_k_domain)}",
    "D_NONFINITE_REPLICATE_COUNT=0",
    "D_FULL_REPLICATE_TRANSFORM_DOMAIN_FEASIBLE=1",
    f"PRECOMMITTED_METHOD_BRANCH={branch}",
    "TRANSFORMED_REPLICATE_VALUES_COMPUTED=0",
    "TRANSFORMED_UNCERTAINTY_COMPUTED=0",
    "DIRECT_TRANSFORMED_REPLICATE_INFERENCE_AUTHORIZED=0",
    "DELTA_METHOD_AUTHORIZED=0",
    "POINT_TRANSFORM_MUTATION_AUTHORIZED=0",
    "K_D_COVARIANCE_COMPUTED=0",
    "CROSS_COORDINATE_METRIC_SCALE_FROZEN=0",
    "GEOMETRY_READY=0",
    "GEOMETRY_AUTHORIZED=0",
    "DIMENSIONALITY_TEST_AUTHORIZED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "E4C5D_K_D_REPLICATE_DOMAIN_FEASIBILITY_AUDIT=PASS",
    "E4C5E_K_D_TRANSFORMED_INFERENCE_METHOD_PREFLIGHT_AUTHORIZED=1",
])+"\n"

EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")

print(log,end="")
print("===== K DOMAIN COUNTS BY TARGET CELL =====")
for cell in sorted(EXPECTED_CELLS):
    ni,nv,nn,arg=k_stats[cell]
    print(f"{cell[0]} {cell[1]} INVALID={ni} VALID_NEGATIVE={nv} NONNEGATIVE={nn}")
print(f"TOTAL_INVALID={total_invalid}")
print(f"TOTAL_VALID_NEGATIVE={total_valid_negative}")
print(f"TOTAL_NONNEGATIVE={total_nonnegative}")
print(f"METHOD_BRANCH={branch}")
