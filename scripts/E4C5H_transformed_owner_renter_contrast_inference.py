#!/usr/bin/env python3
from pathlib import Path
import csv, collections, hashlib, importlib.util, json, math, re, sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1]

ENGINE=ROOT/"scripts/E4A2E_scf_replicate_mi_engine.py"
CONTRACT=ROOT/"data/metadata/E4C5H_transformed_owner_renter_contrast_inference_contract.json"

RAW_COMBINED=ROOT/"data/results/E4A2F_2022_scf_kd_cohort_inference.tsv"
RAW_IMPL=ROOT/"data/results/E4A2F_2022_scf_kd_implicate_statistics.tsv"
RAW_REP=ROOT/"data/results/E4A2F_2022_scf_kd_replicate_statistics.tsv"
G_INF=ROOT/"data/results/E4C5G_transformed_cohort_inference.tsv"

EXEC=ROOT/"data/metadata/E4C5H_execution.txt"
AUDIT=ROOT/"data/metadata/E4C5H_transformed_owner_renter_contrast_inference_audit.txt"
OUT_IMPL=ROOT/"data/results/E4C5H_transformed_owner_renter_implicate_contrasts.tsv"
OUT_REP=ROOT/"data/results/E4C5H_transformed_owner_renter_replicate_contrasts.tsv"
OUT_INF=ROOT/"data/results/E4C5H_transformed_owner_renter_contrast_inference.tsv"
HARD=ROOT/"data/results/E4C5H_execution_hard_gates.tsv"

ENGINE_SHA="216c4e8bd52104bba0db3d69be17ac54fa8c86893c9f21c6c1b6ec5890d9722a"
RAW_COMBINED_SHA="4fc37f81af05b32f1769412fca327cb0cee0bc1610b33c6c77eeb5a04669b55c"
RAW_IMPL_SHA="13b98bf512878722b9ce134c0146e46705b1275cfc97239e7e8fdb1026e1e5df"
RAW_REP_SHA="d7a25d385cab8d3aee0701ca86af19c2525b35fc839d44a01198f5ee6f6d311e"
G_INF_SHA="bfd8521083114846cdb20de440d21b6cf1f904087a14f9c7d4c26cdcf31095ad"

KREF=38640.0
AGES=["25-34","35-44","45-54","55-64"]
COMPONENTS=["K","D"]
REL_TOL=5e-10
ABS_TOL=2e-11

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):
            h.update(b)
    return h.hexdigest()

def norm(x):
    return re.sub(r"[^A-Z0-9]+","_",str(x).strip().upper()).strip("_")

def age_frozen(x):
    s=str(x).strip().upper().replace("–","-").replace("—","-")
    nums=[int(v) for v in re.findall(r"\d+",s)]
    for lo,hi in [(25,34),(35,44),(45,54),(55,64)]:
        if lo in nums and hi in nums:
            return f"{lo}-{hi}"
    return None

def tenure_exact(x):
    s=norm(x)
    return s if s in {"OWNER","RENTER"} else None

def component_from_sid(x):
    s=norm(x)
    if s=="K_FIN_MEAN": return "K"
    if s=="D_PIRTOTAL_MEAN": return "D"
    return None

def ffloat(x,label):
    try:v=float(str(x).strip())
    except Exception as e: raise RuntimeError(f"{label}: nonnumeric {x!r}") from e
    if not math.isfinite(v): raise RuntimeError(f"{label}: nonfinite {v}")
    return v

def transform(comp,x):
    if comp=="K":
        if not x > -KREF:
            raise RuntimeError(f"K transform domain failure: {x}")
        return math.log1p(x/KREF)
    if comp=="D":
        return -x
    raise RuntimeError(comp)

def rid_key(x):
    try:return (0,int(x))
    except Exception:return (1,x)

def assert_close(label,a,b):
    if not math.isclose(float(a),float(b),rel_tol=REL_TOL,abs_tol=ABS_TOL):
        raise RuntimeError(f"{label}: mismatch calculated={a:.17g} frozen={b:.17g}")

c=json.loads(CONTRACT.read_text(encoding="utf-8"))
assert c["phase"]=="E4C5H"
assert c["contrast"]["name"]=="RENTER_MINUS_OWNER_STATE"
assert c["contrast"]["transform_raw_difference_directly"] is False
assert c["scope_boundary"]["K_D_cross_coordinate_covariance_computed"] is False

assert sha(ENGINE)==ENGINE_SHA
assert sha(RAW_COMBINED)==RAW_COMBINED_SHA
assert sha(RAW_IMPL)==RAW_IMPL_SHA
assert sha(RAW_REP)==RAW_REP_SHA
assert sha(G_INF)==G_INF_SHA

spec=importlib.util.spec_from_file_location("e4a2e_h",ENGINE)
if spec is None or spec.loader is None: raise RuntimeError("cannot load engine")
eng=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=eng
spec.loader.exec_module(eng)
if eng.IMPLICATE_COUNT!=5 or eng.REPLICATE_COUNT!=999:
    raise RuntimeError("engine count drift")
if eng.IMPUTATION_VARIANCE_DIVISOR!=4 or eng.SAMPLING_VARIANCE_DIVISOR!=998:
    raise RuntimeError("engine divisor drift")
if float(eng.MI_MULTIPLIER)!=1.2:
    raise RuntimeError("engine multiplier drift")

# Frozen E4C5G serialized cell inference for reproduction validation.
frozen_inf={}
with G_INF.open("r",encoding="utf-8",newline="") as f:
    rd=csv.DictReader(f,delimiter="\t")
    for r in rd:
        key=(r["component"],r["age_band"],r["tenure"])
        frozen_inf[key]={
            "point":ffloat(r["point_estimate_state"],f"G point {key}"),
            "imp_var":ffloat(r["imputation_variance_state"],f"G impvar {key}"),
            "rep_mean":ffloat(r["sampling_replicate_mean_state"],f"G repmean {key}"),
            "samp_var":ffloat(r["sampling_variance_state"],f"G sampvar {key}"),
            "comb_var":ffloat(r["combined_variance_state"],f"G combvar {key}"),
            "se":ffloat(r["combined_se_state"],f"G se {key}"),
        }

expected_cell_keys={(comp,age,ten) for comp in COMPONENTS for age in AGES for ten in ["OWNER","RENTER"]}
if set(frozen_inf)!=expected_cell_keys:
    raise RuntimeError("frozen E4C5G cell key mismatch")

# Full-precision raw combined primary point estimates.
points={}
with RAW_COMBINED.open("r",encoding="utf-8-sig",newline="") as f:
    rd=csv.DictReader(f,delimiter="\t")
    for rownum,r in enumerate(rd,start=2):
        comp=component_from_sid(r["statistic_id"])
        if comp is None: continue
        age=age_frozen(r["age_band"]); ten=tenure_exact(r["tenure"])
        if age is None or ten is None: continue
        if norm(r["role"])!="PRIMARY": continue
        if comp=="K" and not (norm(r["dimension"])=="K" and norm(r["raw_variable"])=="FIN" and norm(r["statistic"])=="MEAN"): continue
        if comp=="D" and not (norm(r["dimension"])=="D" and norm(r["raw_variable"])=="PIRTOTAL" and norm(r["statistic"])=="MEAN"): continue
        key=(comp,age,ten)
        if key in points: raise RuntimeError(f"duplicate point {key}")
        points[key]=(ffloat(r["point_estimate_raw"],f"raw point {key}"),str(r["year"]).strip())

if set(points)!=expected_cell_keys:
    raise RuntimeError("raw point key mismatch")

# Full-precision implicates.
impl=collections.defaultdict(dict)
with RAW_IMPL.open("r",encoding="utf-8-sig",newline="") as f:
    rd=csv.DictReader(f,delimiter="\t")
    for rownum,r in enumerate(rd,start=2):
        if norm(r["statistic_type"])!="COHORT": continue
        comp=component_from_sid(r["statistic_id"])
        if comp is None: continue
        age=age_frozen(r["age_band"]); ten=tenure_exact(r["tenure_or_contrast"])
        if age is None or ten is None: continue
        m=int(str(r["implicate"]).strip())
        if m not in {1,2,3,4,5}: raise RuntimeError(f"bad implicate {m}")
        key=(comp,age,ten)
        if m in impl[key]: raise RuntimeError(f"duplicate implicate {key} {m}")
        impl[key][m]=ffloat(r["raw_value"],f"implicate {key} {m}")

for key in expected_cell_keys:
    if set(impl[key])!={1,2,3,4,5}:
        raise RuntimeError(f"implicate shape {key}")

# Full-precision replicates.
rep=collections.defaultdict(dict)
with RAW_REP.open("r",encoding="utf-8-sig",newline="") as f:
    rd=csv.DictReader(f,delimiter="\t")
    for rownum,r in enumerate(rd,start=2):
        if norm(r["statistic_type"])!="COHORT": continue
        comp=component_from_sid(r["statistic_id"])
        if comp is None: continue
        age=age_frozen(r["age_band"]); ten=tenure_exact(r["tenure_or_contrast"])
        if age is None or ten is None: continue
        rid=str(r["replicate"]).strip()
        if not rid: raise RuntimeError("blank replicate id")
        key=(comp,age,ten)
        if rid in rep[key]: raise RuntimeError(f"duplicate replicate {key} {rid}")
        rep[key][rid]=ffloat(r["raw_value"],f"replicate {key} {rid}")

for key in expected_cell_keys:
    if len(rep[key])!=999:
        raise RuntimeError(f"replicate shape {key}: {len(rep[key])}")

# All owner/renter pairs must use identical replicate-ID sets.
for comp in COMPONENTS:
    for age in AGES:
        if set(rep[(comp,age,"OWNER")]) != set(rep[(comp,age,"RENTER")]):
            raise RuntimeError(f"owner/renter replicate id mismatch {comp} {age}")

# Reproduce frozen E4C5G transformed cell inference from raw atoms before contrast.
reproduced=0
for key in sorted(expected_cell_keys):
    comp,age,ten=key
    iv=np.asarray([transform(comp,impl[key][m]) for m in range(1,6)],dtype=np.float64)
    rids=sorted(rep[key],key=rid_key)
    rv=np.asarray([transform(comp,rep[key][rid]) for rid in rids],dtype=np.float64)
    point=transform(comp,points[key][0])
    imp_var=float(eng._sample_variance(iv,5))
    rep_mean=float(np.mean(rv))
    samp_var=float(eng._sample_variance(rv,999))
    comb_var=float(eng.MI_MULTIPLIER*imp_var+samp_var)
    se=math.sqrt(comb_var)
    fr=frozen_inf[key]
    assert_close(f"point {key}",point,fr["point"])
    assert_close(f"impvar {key}",imp_var,fr["imp_var"])
    assert_close(f"repmean {key}",rep_mean,fr["rep_mean"])
    assert_close(f"sampvar {key}",samp_var,fr["samp_var"])
    assert_close(f"combvar {key}",comb_var,fr["comb_var"])
    assert_close(f"se {key}",se,fr["se"])
    reproduced+=1

impl_out=[]
rep_out=[]
inf_out=[]
d_identity_pass=True

for comp in COMPONENTS:
    sid="K_FIN_MEAN" if comp=="K" else "D_PIRTOTAL_MEAN"
    for age in AGES:
        ok=(comp,age,"OWNER")
        rk=(comp,age,"RENTER")
        year=points[ok][1]
        if points[rk][1]!=year:
            raise RuntimeError(f"year mismatch {comp} {age}")

        owner_point_state=transform(comp,points[ok][0])
        renter_point_state=transform(comp,points[rk][0])
        point_delta=renter_point_state-owner_point_state

        imp_deltas=[]
        for m in range(1,6):
            owner_state=transform(comp,impl[ok][m])
            renter_state=transform(comp,impl[rk][m])
            delta=renter_state-owner_state
            imp_deltas.append(delta)
            impl_out.append([
                year,age,"RENTER_MINUS_OWNER_STATE",sid,comp,m,
                f"{owner_state:.12f}",f"{renter_state:.12f}",f"{delta:.12f}"
            ])

        owner_ids=set(rep[ok]); renter_ids=set(rep[rk])
        if owner_ids!=renter_ids:
            raise RuntimeError(f"replicate ids misaligned {comp} {age}")
        rids=sorted(owner_ids,key=rid_key)

        rep_deltas=[]
        for rid in rids:
            owner_state=transform(comp,rep[ok][rid])
            renter_state=transform(comp,rep[rk][rid])
            delta=renter_state-owner_state
            rep_deltas.append(delta)
            rep_out.append([
                year,age,"RENTER_MINUS_OWNER_STATE",sid,comp,rid,
                f"{owner_state:.12f}",f"{renter_state:.12f}",f"{delta:.12f}"
            ])

        imp_arr=np.asarray(imp_deltas,dtype=np.float64)
        rep_arr=np.asarray(rep_deltas,dtype=np.float64)
        imp_mean=float(np.mean(imp_arr))
        imp_var=float(eng._sample_variance(imp_arr,5))
        rep_mean=float(np.mean(rep_arr))
        samp_var=float(eng._sample_variance(rep_arr,999))
        comb_var=float(eng.MI_MULTIPLIER*imp_var+samp_var)
        if comb_var<0 or not math.isfinite(comb_var):
            raise RuntimeError(f"invalid contrast combined variance {comp} {age}")
        se=math.sqrt(comb_var)

        if comp=="D":
            # Since state=-raw, state renter-owner equals raw owner-renter.
            raw_identity=points[ok][0]-points[rk][0]
            if not math.isclose(point_delta,raw_identity,rel_tol=1e-12,abs_tol=1e-14):
                d_identity_pass=False
                raise RuntimeError(f"D point identity failure {age}")
            for m,delta in zip(range(1,6),imp_deltas):
                expected=impl[ok][m]-impl[rk][m]
                if not math.isclose(delta,expected,rel_tol=1e-12,abs_tol=1e-14):
                    d_identity_pass=False
                    raise RuntimeError(f"D implicate identity failure {age} m={m}")
            for rid,delta in zip(rids,rep_deltas):
                expected=rep[ok][rid]-rep[rk][rid]
                if not math.isclose(delta,expected,rel_tol=1e-12,abs_tol=1e-14):
                    d_identity_pass=False
                    raise RuntimeError(f"D replicate identity failure {age} rid={rid}")

        inf_out.append([
            year,age,"RENTER_MINUS_OWNER_STATE",sid,comp,
            "STATE_RENTER_MINUS_STATE_OWNER",
            f"{owner_point_state:.12f}",f"{renter_point_state:.12f}",
            f"{point_delta:.12f}",f"{imp_mean:.12f}",f"{imp_var:.12f}",
            f"{rep_mean:.12f}",f"{samp_var:.12f}",f"{comb_var:.12f}",
            f"{se:.12f}",5,999
        ])

with OUT_IMPL.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow([
        "year","age_band","contrast","statistic_id","component","implicate",
        "owner_state_value","renter_state_value","renter_minus_owner_state"
    ])
    w.writerows(impl_out)

with OUT_REP.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow([
        "year","age_band","contrast","statistic_id","component","replicate",
        "owner_state_value","renter_state_value","renter_minus_owner_state"
    ])
    w.writerows(rep_out)

with OUT_INF.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow([
        "year","age_band","contrast","statistic_id","component","point_definition",
        "owner_point_state","renter_point_state","renter_minus_owner_point_state",
        "implicate_difference_mean_diagnostic","imputation_variance_state_contrast",
        "sampling_replicate_mean_difference_state","sampling_variance_state_contrast",
        "combined_variance_state_contrast","combined_se_state_contrast",
        "implicate_count","replicate_count"
    ])
    w.writerows(inf_out)

hard_rows=[
    ("E4C5G_CELL_INFERENCE_REPRODUCTION_COUNT",reproduced),
    ("E4C5G_CELL_INFERENCE_REPRODUCTION_PASS",1),
    ("CONTRAST_ORIENTATION","RENTER_MINUS_OWNER_STATE"),
    ("IMPLICATE_CONTRAST_ROW_COUNT",len(impl_out)),
    ("REPLICATE_CONTRAST_ROW_COUNT",len(rep_out)),
    ("CONTRAST_INFERENCE_ROW_COUNT",len(inf_out)),
    ("D_LINEAR_CONTRAST_IDENTITY_PASS",int(d_identity_pass)),
    ("RAW_DIFFERENCE_DIRECTLY_TRANSFORMED",0),
    ("RATIO_COMPUTED",0),
    ("SIGN_USED_AS_GATE",0),
    ("SIGNIFICANCE_USED_AS_GATE",0),
    ("MAGNITUDE_USED_AS_GATE",0),
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
    "CONTRAST_ORIENTATION=RENTER_MINUS_OWNER_STATE",
    "POINT_CONTRAST_DEFINITION=STATE_RENTER_MINUS_STATE_OWNER",
    "K_RAW_DIFFERENCE_DIRECTLY_LOG_TRANSFORMED=0",
    "RATIO_COMPUTED=0",
    "IMPLICATE_PAIRING=SAME_IMPLICATE_ID",
    "REPLICATE_PAIRING=SAME_REPLICATE_ID",
    "IMPLICATE_COUNT=5",
    "REPLICATE_COUNT=999",
    "MI_MULTIPLIER=1.2",
    f"E4C5G_CELL_INFERENCE_REPRODUCTION_COUNT={reproduced}",
    "E4C5G_CELL_INFERENCE_REPRODUCTION_PASS=1",
    f"IMPLICATE_CONTRAST_ROW_COUNT={len(impl_out)}",
    f"REPLICATE_CONTRAST_ROW_COUNT={len(rep_out)}",
    f"CONTRAST_INFERENCE_ROW_COUNT={len(inf_out)}",
    f"D_LINEAR_CONTRAST_IDENTITY_PASS={int(d_identity_pass)}",
    "TRANSFORMED_OWNER_RENTER_CONTRAST_COMPUTED=1",
    "TRANSFORMED_OWNER_RENTER_CONTRAST_UNCERTAINTY_COMPUTED=1",
    "CONTRAST_SIGN_USED_AS_EXECUTION_GATE=0",
    "STATISTICAL_SIGNIFICANCE_USED_AS_EXECUTION_GATE=0",
    "MAGNITUDE_USED_AS_EXECUTION_GATE=0",
    "K_D_COVARIANCE_COMPUTED=0",
    "CROSS_COORDINATE_METRIC_SCALE_FROZEN=0",
    "GEOMETRY_READY=0",
    "GEOMETRY_AUTHORIZED=0",
    "DIMENSIONALITY_TEST_AUTHORIZED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "E4C5H_TRANSFORMED_OWNER_RENTER_CONTRAST_INFERENCE=PASS",
    "E4C5I_K_D_COMPONENT_INFERENCE_CLOSEOUT_PREFLIGHT_AUTHORIZED=1",
])+"\n"

EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")

print(log,end="")
print("===== TRANSFORMED OWNER/RENTER CONTRAST INFERENCE — NO OUTCOME GATE =====")
for r in inf_out:
    print(
        f"{r[4]} {r[1]} {r[2]} "
        f"POINT={r[8]} IMPVAR={r[10]} SAMPVAR={r[12]} COMBVAR={r[13]} SE={r[14]}"
    )
