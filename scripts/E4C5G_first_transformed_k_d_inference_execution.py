#!/usr/bin/env python3
from pathlib import Path
import csv, collections, hashlib, importlib.util, json, math, re, sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1]

ENGINE=ROOT/"scripts/E4A2E_scf_replicate_mi_engine.py"
ENGINE_CONTRACT=ROOT/"data/metadata/E4A2E_scf_replicate_mi_engine_contract.json"
CONTRACT=ROOT/"data/metadata/E4C5G_first_transformed_k_d_inference_execution_contract.json"

RAW_COMBINED=ROOT/"data/results/E4A2F_2022_scf_kd_cohort_inference.tsv"
RAW_IMPL=ROOT/"data/results/E4A2F_2022_scf_kd_implicate_statistics.tsv"
RAW_REP=ROOT/"data/results/E4A2F_2022_scf_kd_replicate_statistics.tsv"
C_POINTS=ROOT/"data/results/E4C5C_k_d_transformed_point_estimates.tsv"

EXEC=ROOT/"data/metadata/E4C5G_execution.txt"
AUDIT=ROOT/"data/metadata/E4C5G_first_transformed_k_d_inference_execution_audit.txt"
OUT_IMPL=ROOT/"data/results/E4C5G_transformed_implicate_statistics.tsv"
OUT_REP=ROOT/"data/results/E4C5G_transformed_replicate_statistics.tsv"
OUT_INF=ROOT/"data/results/E4C5G_transformed_cohort_inference.tsv"
HARD=ROOT/"data/results/E4C5G_execution_hard_gates.tsv"

ENGINE_SHA="216c4e8bd52104bba0db3d69be17ac54fa8c86893c9f21c6c1b6ec5890d9722a"
ENGINE_CONTRACT_SHA="e535ef36f3829e759fd0563d9eeb06dbb54afb8db4bceca42456bf6d217a3064"
RAW_COMBINED_SHA="4fc37f81af05b32f1769412fca327cb0cee0bc1610b33c6c77eeb5a04669b55c"
RAW_REP_SHA="d7a25d385cab8d3aee0701ca86af19c2525b35fc839d44a01198f5ee6f6d311e"
C_POINTS_SHA="81fd6ec3888164b761e6684967ee56484895ee1d8db5a4d6d317ea9c9a973072"

KREF=38640.0
AGES=["25-34","35-44","45-54","55-64"]
TENS=["OWNER","RENTER"]
CELLS=[(a,t) for a in AGES for t in TENS]
CELL_SET=set(CELLS)
REL_TOL=5e-10
ABS_TOL=5e-12


def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):
            h.update(b)
    return h.hexdigest()


def norm(x):
    return re.sub(r"[^A-Z0-9]+","_",str(x).strip().upper()).strip("_")


def age_exact(x):
    s=str(x).strip().upper().replace("–","-").replace("—","-")
    return s if s in AGES else None


def tenure_exact(x):
    s=norm(x)
    return s if s in {"OWNER","RENTER"} else None


def ffloat(x,label):
    try:v=float(str(x).strip())
    except Exception as e: raise RuntimeError(f"{label}: nonnumeric {x!r}") from e
    if not math.isfinite(v):
        raise RuntimeError(f"{label}: nonfinite {v}")
    return v


def assert_close(label,a,b):
    if not math.isclose(float(a),float(b),rel_tol=REL_TOL,abs_tol=ABS_TOL):
        raise RuntimeError(f"{label}: mismatch calculated={a:.17g} frozen={b:.17g}")


def transform(comp,x):
    if comp=="K":
        if not x > -KREF:
            raise RuntimeError(f"K transform domain failure: {x}")
        return math.log1p(x/KREF)
    if comp=="D":
        return -x
    raise RuntimeError(comp)


c=json.loads(CONTRACT.read_text(encoding="utf-8"))
assert c["phase"]=="E4C5G"
assert c["operational_engine"]["formula_rederivation_allowed"] is False
assert c["scope_boundary"]["owner_renter_transformed_contrast_computed"] is False
assert c["scope_boundary"]["geometry_authorized"] is False

assert sha(ENGINE)==ENGINE_SHA
assert sha(ENGINE_CONTRACT)==ENGINE_CONTRACT_SHA
assert sha(RAW_COMBINED)==RAW_COMBINED_SHA
assert sha(RAW_REP)==RAW_REP_SHA
assert sha(C_POINTS)==C_POINTS_SHA

# Load exact frozen operational engine and validate adapter constants/symbols.
spec=importlib.util.spec_from_file_location("e4a2e_frozen_engine",ENGINE)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load frozen E4A2E engine")
eng=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=eng
spec.loader.exec_module(eng)

if eng.IMPLICATE_COUNT!=5: raise RuntimeError("engine IMPLICATE_COUNT drift")
if eng.REPLICATE_COUNT!=999: raise RuntimeError("engine REPLICATE_COUNT drift")
if eng.IMPUTATION_VARIANCE_DIVISOR!=4: raise RuntimeError("engine imputation divisor drift")
if eng.SAMPLING_VARIANCE_DIVISOR!=998: raise RuntimeError("engine sampling divisor drift")
if not math.isclose(float(eng.MI_MULTIPLIER),1.2,rel_tol=0,abs_tol=0):
    raise RuntimeError("engine MI multiplier drift")
if not callable(getattr(eng,"_sample_variance",None)):
    raise RuntimeError("engine _sample_variance missing")

# Select frozen raw combined primary rows.
combined={}
with RAW_COMBINED.open("r",encoding="utf-8-sig",newline="") as f:
    rd=csv.DictReader(f,delimiter="\t")
    required={
        "year","age_band","tenure","statistic_id","dimension","role",
        "raw_variable","statistic","point_estimate_raw","imputation_variance",
        "sampling_replicate_mean","sampling_variance","combined_variance","combined_se",
        "implicate_count","replicate_count"
    }
    miss=required-set(rd.fieldnames or [])
    if miss: raise RuntimeError(f"combined source missing fields {sorted(miss)}")
    for rownum,row in enumerate(rd,start=2):
        sid=norm(row["statistic_id"])
        if sid=="K_FIN_MEAN": comp="K"
        elif sid=="D_PIRTOTAL_MEAN": comp="D"
        else: continue
        age=age_exact(row["age_band"]); ten=tenure_exact(row["tenure"])
        if age is None or ten is None: continue
        if norm(row["role"])!="PRIMARY": continue
        if comp=="K" and not (norm(row["dimension"])=="K" and norm(row["raw_variable"])=="FIN" and norm(row["statistic"])=="MEAN"): continue
        if comp=="D" and not (norm(row["dimension"])=="D" and norm(row["raw_variable"])=="PIRTOTAL" and norm(row["statistic"])=="MEAN"): continue
        key=(comp,age,ten)
        if key in combined: raise RuntimeError(f"duplicate combined primary {key}")
        combined[key]={
            "year":str(row["year"]).strip(),
            "point":ffloat(row["point_estimate_raw"],f"combined point {key}"),
            "imp_var":ffloat(row["imputation_variance"],f"combined imp_var {key}"),
            "rep_mean":ffloat(row["sampling_replicate_mean"],f"combined rep_mean {key}"),
            "sampling_var":ffloat(row["sampling_variance"],f"combined sampling_var {key}"),
            "combined_var":ffloat(row["combined_variance"],f"combined var {key}"),
            "combined_se":ffloat(row["combined_se"],f"combined se {key}"),
            "implicate_count":int(row["implicate_count"]),
            "replicate_count":int(row["replicate_count"]),
        }

expected={(comp,a,t) for comp in ["K","D"] for a,t in CELLS}
if set(combined)!=expected:
    raise RuntimeError(f"combined primary key mismatch missing={sorted(expected-set(combined))} extra={sorted(set(combined)-expected)}")

# Read exact cohort implicate atomic values. Do not transform until all K domains pass.
impl=collections.defaultdict(dict)
with RAW_IMPL.open("r",encoding="utf-8-sig",newline="") as f:
    rd=csv.DictReader(f,delimiter="\t")
    required={"year","statistic_type","age_band","tenure_or_contrast","statistic_id","implicate","raw_value"}
    miss=required-set(rd.fieldnames or [])
    if miss: raise RuntimeError(f"implicate source missing fields {sorted(miss)}")
    for rownum,row in enumerate(rd,start=2):
        if norm(row["statistic_type"])!="COHORT": continue
        sid=norm(row["statistic_id"])
        if sid=="K_FIN_MEAN": comp="K"
        elif sid=="D_PIRTOTAL_MEAN": comp="D"
        else: continue
        age=age_exact(row["age_band"]); ten=tenure_exact(row["tenure_or_contrast"])
        if age is None or ten is None: continue
        m=int(str(row["implicate"]).strip())
        if m not in {1,2,3,4,5}: raise RuntimeError(f"bad implicate id row {rownum}: {m}")
        key=(comp,age,ten)
        if m in impl[key]: raise RuntimeError(f"duplicate implicate {key} m={m}")
        impl[key][m]=(ffloat(row["raw_value"],f"implicate {key} {m}"),rownum,str(row["year"]).strip())

for key in expected:
    if set(impl[key])!={1,2,3,4,5}:
        raise RuntimeError(f"implicate shape failure {key}: {sorted(impl[key])}")

k_impl_invalid=[]
for key in sorted(k for k in expected if k[0]=="K"):
    for m,(v,rownum,year) in impl[key].items():
        if not v > -KREF:
            k_impl_invalid.append((key,m,v,rownum))
if k_impl_invalid:
    raise RuntimeError(f"K implicate transform domain invalid rows: {k_impl_invalid}")

# Read exact cohort replicate atomic values.
rep=collections.defaultdict(dict)
with RAW_REP.open("r",encoding="utf-8-sig",newline="") as f:
    rd=csv.DictReader(f,delimiter="\t")
    required={"year","statistic_type","age_band","tenure_or_contrast","statistic_id","replicate","raw_value"}
    miss=required-set(rd.fieldnames or [])
    if miss: raise RuntimeError(f"replicate source missing fields {sorted(miss)}")
    for rownum,row in enumerate(rd,start=2):
        if norm(row["statistic_type"])!="COHORT": continue
        sid=norm(row["statistic_id"])
        if sid=="K_FIN_MEAN": comp="K"
        elif sid=="D_PIRTOTAL_MEAN": comp="D"
        else: continue
        age=age_exact(row["age_band"]); ten=tenure_exact(row["tenure_or_contrast"])
        if age is None or ten is None: continue
        rid=str(row["replicate"]).strip()
        if not rid: raise RuntimeError(f"blank replicate id row {rownum}")
        key=(comp,age,ten)
        if rid in rep[key]: raise RuntimeError(f"duplicate replicate {key} rid={rid}")
        rep[key][rid]=(ffloat(row["raw_value"],f"replicate {key} {rid}"),rownum,str(row["year"]).strip())

for key in expected:
    if len(rep[key])!=999:
        raise RuntimeError(f"replicate shape failure {key}: {len(rep[key])}")

# ID sets must align across all cells/components.
base_ids=set(rep[("K","25-34","OWNER")])
for key in expected:
    if set(rep[key])!=base_ids:
        raise RuntimeError(f"replicate id alignment failure {key}")

k_rep_invalid=[]
for key in sorted(k for k in expected if k[0]=="K"):
    for rid,(v,rownum,year) in rep[key].items():
        if not v > -KREF:
            k_rep_invalid.append((key,rid,v,rownum))
if k_rep_invalid:
    raise RuntimeError(f"K replicate domain drift despite E4C5D: {k_rep_invalid[:20]}")

# Raw-engine reproduction gate. This occurs before transformed atomic outputs are written.
raw_repro_rows=[]
for key in sorted(expected):
    iv=np.asarray([impl[key][m][0] for m in range(1,6)],dtype=np.float64)
    # Stable ID ordering affects only mean/sample variance through summation ordering;
    # numeric replicate IDs are sorted numerically if possible.
    def rid_key(x):
        try:return (0,int(x))
        except Exception:return (1,x)
    rids=sorted(rep[key],key=rid_key)
    rv=np.asarray([rep[key][rid][0] for rid in rids],dtype=np.float64)

    raw_point=float(np.mean(iv))
    raw_imp=float(eng._sample_variance(iv,eng.IMPLICATE_COUNT))
    raw_rep_mean=float(np.mean(rv))
    raw_samp=float(eng._sample_variance(rv,eng.REPLICATE_COUNT))
    raw_comb=float(eng.MI_MULTIPLIER*raw_imp+raw_samp)
    raw_se=math.sqrt(raw_comb)

    frozen=combined[key]
    assert frozen["implicate_count"]==5, key
    assert frozen["replicate_count"]==999, key
    assert_close(f"raw point {key}",raw_point,frozen["point"])
    assert_close(f"raw imputation variance {key}",raw_imp,frozen["imp_var"])
    assert_close(f"raw replicate mean {key}",raw_rep_mean,frozen["rep_mean"])
    assert_close(f"raw sampling variance {key}",raw_samp,frozen["sampling_var"])
    assert_close(f"raw combined variance {key}",raw_comb,frozen["combined_var"])
    assert_close(f"raw combined se {key}",raw_se,frozen["combined_se"])
    raw_repro_rows.append(key)

# Only after all structural/domain/raw-reproduction gates pass do we compute transformed atoms.
impl_out=[]
rep_out=[]
inf_out=[]
d_linear_invariance=True

for key in sorted(expected):
    comp,age,ten=key
    year=combined[key]["year"]
    sid="K_FIN_MEAN" if comp=="K" else "D_PIRTOTAL_MEAN"

    raw_impl=np.asarray([impl[key][m][0] for m in range(1,6)],dtype=np.float64)
    tr_impl=np.asarray([transform(comp,float(v)) for v in raw_impl],dtype=np.float64)

    def rid_key(x):
        try:return (0,int(x))
        except Exception:return (1,x)
    rids=sorted(rep[key],key=rid_key)
    raw_rep=np.asarray([rep[key][rid][0] for rid in rids],dtype=np.float64)
    tr_rep=np.asarray([transform(comp,float(v)) for v in raw_rep],dtype=np.float64)

    point_state=transform(comp,combined[key]["point"])
    imp_mean_diag=float(np.mean(tr_impl))
    imp_var=float(eng._sample_variance(tr_impl,eng.IMPLICATE_COUNT))
    rep_mean=float(np.mean(tr_rep))
    sampling_var=float(eng._sample_variance(tr_rep,eng.REPLICATE_COUNT))
    combined_var=float(eng.MI_MULTIPLIER*imp_var+sampling_var)
    if combined_var<0 or not math.isfinite(combined_var):
        raise RuntimeError(f"invalid transformed combined variance {key}: {combined_var}")
    combined_se=math.sqrt(combined_var)

    if comp=="D":
        # Exact linear sign flip must preserve both variance components and SE.
        raw_imp=float(eng._sample_variance(raw_impl,eng.IMPLICATE_COUNT))
        raw_sampling=float(eng._sample_variance(raw_rep,eng.REPLICATE_COUNT))
        raw_comb=float(eng.MI_MULTIPLIER*raw_imp+raw_sampling)
        raw_se=math.sqrt(raw_comb)
        for label,a,b in [
            ("D imp variance",imp_var,raw_imp),
            ("D sampling variance",sampling_var,raw_sampling),
            ("D combined variance",combined_var,raw_comb),
            ("D SE",combined_se,raw_se),
        ]:
            if not math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-14):
                d_linear_invariance=False
                raise RuntimeError(f"{label} invariance failure {key}: {a} vs {b}")
        assert_close(f"D transformed implicate mean equals transformed point {key}",imp_mean_diag,point_state)

    for m,(rv,source_row,src_year) in sorted(impl[key].items()):
        impl_out.append([
            src_year,age,ten,sid,comp,m,
            f"{rv:.12f}",f"{transform(comp,rv):.12f}"
        ])
    for rid in rids:
        rv,source_row,src_year=rep[key][rid]
        rep_out.append([
            src_year,age,ten,sid,comp,rid,
            f"{rv:.12f}",f"{transform(comp,rv):.12f}"
        ])

    inf_out.append([
        year,age,ten,sid,comp,
        "TRANSFORM_OF_FROZEN_RAW_POOLED_POINT",
        f"{combined[key]['point']:.12f}",f"{point_state:.12f}",
        f"{imp_mean_diag:.12f}",f"{imp_var:.12f}",
        f"{rep_mean:.12f}",f"{sampling_var:.12f}",
        f"{combined_var:.12f}",f"{combined_se:.12f}",5,999
    ])

with OUT_IMPL.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["year","age_band","tenure","statistic_id","component","implicate","raw_value","transformed_state_value"])
    w.writerows(impl_out)

with OUT_REP.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["year","age_band","tenure","statistic_id","component","replicate","raw_value","transformed_state_value"])
    w.writerows(rep_out)

with OUT_INF.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow([
        "year","age_band","tenure","statistic_id","component","point_definition",
        "point_estimate_raw","point_estimate_state","transformed_implicate_mean_diagnostic",
        "imputation_variance_state","sampling_replicate_mean_state","sampling_variance_state",
        "combined_variance_state","combined_se_state","implicate_count","replicate_count"
    ])
    w.writerows(inf_out)

hard_rows=[
    ("RAW_ENGINE_REPRODUCTION_CELL_COUNT",len(raw_repro_rows)),
    ("RAW_ENGINE_REPRODUCTION_PASS",1),
    ("K_IMPLICATE_DOMAIN_INVALID_COUNT",len(k_impl_invalid)),
    ("K_IMPLICATE_DOMAIN_VALID_COUNT",40-len(k_impl_invalid)),
    ("K_REPLICATE_DOMAIN_INVALID_COUNT",len(k_rep_invalid)),
    ("K_REPLICATE_DOMAIN_VALID_COUNT",7992-len(k_rep_invalid)),
    ("TRANSFORMED_IMPLICATE_ROW_COUNT",len(impl_out)),
    ("TRANSFORMED_REPLICATE_ROW_COUNT",len(rep_out)),
    ("TRANSFORMED_COHORT_INFERENCE_ROW_COUNT",len(inf_out)),
    ("D_LINEAR_VARIANCE_INVARIANCE_PASS",int(d_linear_invariance)),
    ("OWNER_RENTER_TRANSFORMED_CONTRAST_COMPUTED",0),
    ("K_D_COVARIANCE_COMPUTED",0),
    ("CROSS_COORDINATE_METRIC_SCALE_FROZEN",0),
    ("GEOMETRY_AUTHORIZED",0),
]
with HARD.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["gate","value"])
    w.writerows(hard_rows)

log="\n".join([
    "EXACT_FROZEN_E4A2E_ENGINE_REUSED=1",
    f"E4A2E_ENGINE_SHA256={ENGINE_SHA}",
    "IMPLICATE_COUNT=5",
    "REPLICATE_COUNT=999",
    "IMPUTATION_VARIANCE_DIVISOR=4",
    "SAMPLING_VARIANCE_DIVISOR=998",
    "MI_MULTIPLIER=1.2",
    "RAW_ENGINE_REPRODUCTION_CELL_COUNT=16",
    "RAW_ENGINE_REPRODUCTION_PASS=1",
    "K_IMPLICATE_DOMAIN_INVALID_COUNT=0",
    "K_IMPLICATE_DOMAIN_VALID_COUNT=40",
    "K_REPLICATE_DOMAIN_INVALID_COUNT=0",
    "K_REPLICATE_DOMAIN_VALID_COUNT=7992",
    "D_IMPLICATE_NONFINITE_COUNT=0",
    "D_REPLICATE_NONFINITE_COUNT=0",
    "TRANSFORMED_IMPLICATE_ROW_COUNT=80",
    "TRANSFORMED_REPLICATE_ROW_COUNT=15984",
    "TRANSFORMED_COHORT_INFERENCE_ROW_COUNT=16",
    "TRANSFORMED_REPLICATE_VALUES_COMPUTED=1",
    "TRANSFORMED_UNCERTAINTY_COMPUTED=1",
    "POINT_ESTIMATE_DEFINITION=TRANSFORM_OF_FROZEN_RAW_POOLED_POINT",
    "K_POINT_REDEFINED_AS_MEAN_TRANSFORMED_IMPLICATES=0",
    f"D_LINEAR_VARIANCE_INVARIANCE_PASS={int(d_linear_invariance)}",
    "OWNER_RENTER_DIRECTION_USED_AS_EXECUTION_GATE=0",
    "STATISTICAL_SIGNIFICANCE_USED_AS_EXECUTION_GATE=0",
    "MAGNITUDE_USED_AS_EXECUTION_GATE=0",
    "OWNER_RENTER_TRANSFORMED_CONTRAST_COMPUTED=0",
    "K_D_COVARIANCE_COMPUTED=0",
    "CROSS_COORDINATE_METRIC_SCALE_FROZEN=0",
    "GEOMETRY_READY=0",
    "GEOMETRY_AUTHORIZED=0",
    "DIMENSIONALITY_TEST_AUTHORIZED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "E4C5G_FIRST_TRANSFORMED_K_D_INFERENCE_EXECUTION=PASS",
    "E4C5H_TRANSFORMED_OWNER_RENTER_CONTRAST_PREFLIGHT_AUTHORIZED=1",
])+"\n"

EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")

print(log,end="")
print("===== TRANSFORMED K/D CELL-LEVEL INFERENCE — NO OUTCOME GATE =====")
for r in inf_out:
    print(
        f"{r[4]} {r[1]} {r[2]} "
        f"POINT={r[7]} IMPVAR={r[9]} SAMPVAR={r[11]} COMBVAR={r[12]} SE={r[13]}"
    )
