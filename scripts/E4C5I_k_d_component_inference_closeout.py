#!/usr/bin/env python3
from pathlib import Path
import csv, collections, json, math

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"data/metadata/E4C5I_k_d_component_inference_closeout_contract.json"

G_INF=ROOT/"data/results/E4C5G_transformed_cohort_inference.tsv"
H_INF=ROOT/"data/results/E4C5H_transformed_owner_renter_contrast_inference.tsv"

EXEC=ROOT/"data/metadata/E4C5I_execution.txt"
AUDIT=ROOT/"data/metadata/E4C5I_k_d_component_inference_closeout_audit.txt"
REGISTRY=ROOT/"data/results/E4C5I_k_d_component_inference_registry.tsv"
HARD=ROOT/"data/results/E4C5I_k_d_component_inference_closeout_hard_gates.tsv"
DECISION=ROOT/"data/results/E4C5I_k_d_component_inference_closeout_decision.tsv"

AGES=["25-34","35-44","45-54","55-64"]
COMPS=["K","D"]
REL=2e-10
ABS=2e-11

def f(x):
    v=float(x)
    if not math.isfinite(v):
        raise RuntimeError(f"nonfinite {x}")
    return v

def close(a,b):
    return math.isclose(float(a),float(b),rel_tol=REL,abs_tol=ABS)

c=json.loads(CONTRACT.read_text(encoding="utf-8"))
assert c["phase"]=="E4C5I"
assert c["new_estimator_introduced"] is False
assert c["new_transform_introduced"] is False
assert c["new_numeric_inference_introduced"] is False

cells={}
with G_INF.open("r",encoding="utf-8",newline="") as fh:
    rd=csv.DictReader(fh,delimiter="\t")
    for r in rd:
        key=(r["component"],r["age_band"],r["tenure"])
        if key in cells:
            raise RuntimeError(f"duplicate cell {key}")
        row={
            "year":r["year"],
            "statistic_id":r["statistic_id"],
            "point":f(r["point_estimate_state"]),
            "imp_var":f(r["imputation_variance_state"]),
            "rep_mean":f(r["sampling_replicate_mean_state"]),
            "samp_var":f(r["sampling_variance_state"]),
            "comb_var":f(r["combined_variance_state"]),
            "se":f(r["combined_se_state"]),
            "implicate_count":int(r["implicate_count"]),
            "replicate_count":int(r["replicate_count"]),
        }
        if row["implicate_count"]!=5 or row["replicate_count"]!=999:
            raise RuntimeError(f"cell counts {key}")
        expected_comb=1.2*row["imp_var"]+row["samp_var"]
        if not close(expected_comb,row["comb_var"]):
            raise RuntimeError(f"cell combined variance algebra {key}: {expected_comb} vs {row['comb_var']}")
        if not close(math.sqrt(row["comb_var"]),row["se"]):
            raise RuntimeError(f"cell SE algebra {key}")
        if row["imp_var"]<0 or row["samp_var"]<0 or row["comb_var"]<0 or row["se"]<0:
            raise RuntimeError(f"negative uncertainty {key}")
        cells[key]=row

expected_cells={(comp,age,ten) for comp in COMPS for age in AGES for ten in ["OWNER","RENTER"]}
if set(cells)!=expected_cells:
    raise RuntimeError(f"cell key mismatch missing={expected_cells-set(cells)} extra={set(cells)-expected_cells}")

contrasts={}
with H_INF.open("r",encoding="utf-8",newline="") as fh:
    rd=csv.DictReader(fh,delimiter="\t")
    for r in rd:
        if r["contrast"]!="RENTER_MINUS_OWNER_STATE":
            raise RuntimeError(f"contrast orientation drift {r['contrast']}")
        key=(r["component"],r["age_band"])
        if key in contrasts:
            raise RuntimeError(f"duplicate contrast {key}")
        row={
            "year":r["year"],
            "statistic_id":r["statistic_id"],
            "point":f(r["renter_minus_owner_point_state"]),
            "imp_var":f(r["imputation_variance_state_contrast"]),
            "rep_mean":f(r["sampling_replicate_mean_difference_state"]),
            "samp_var":f(r["sampling_variance_state_contrast"]),
            "comb_var":f(r["combined_variance_state_contrast"]),
            "se":f(r["combined_se_state_contrast"]),
            "implicate_count":int(r["implicate_count"]),
            "replicate_count":int(r["replicate_count"]),
        }
        if row["implicate_count"]!=5 or row["replicate_count"]!=999:
            raise RuntimeError(f"contrast counts {key}")
        expected_comb=1.2*row["imp_var"]+row["samp_var"]
        if not close(expected_comb,row["comb_var"]):
            raise RuntimeError(f"contrast combined variance algebra {key}")
        if not close(math.sqrt(row["comb_var"]),row["se"]):
            raise RuntimeError(f"contrast SE algebra {key}")
        expected_point=cells[(key[0],key[1],"RENTER")]["point"]-cells[(key[0],key[1],"OWNER")]["point"]
        if not close(expected_point,row["point"]):
            raise RuntimeError(f"contrast point arithmetic {key}: {expected_point} vs {row['point']}")
        if row["imp_var"]<0 or row["samp_var"]<0 or row["comb_var"]<0 or row["se"]<0:
            raise RuntimeError(f"negative contrast uncertainty {key}")
        contrasts[key]=row

expected_contrasts={(comp,age) for comp in COMPS for age in AGES}
if set(contrasts)!=expected_contrasts:
    raise RuntimeError("contrast key mismatch")

registry=[]
for comp in COMPS:
    for age in AGES:
        for ten in ["OWNER","RENTER"]:
            r=cells[(comp,age,ten)]
            registry.append([
                "CELL",r["year"],comp,age,ten,"NA",r["statistic_id"],
                f"{r['point']:.12f}",f"{r['imp_var']:.12f}",f"{r['rep_mean']:.12f}",
                f"{r['samp_var']:.12f}",f"{r['comb_var']:.12f}",f"{r['se']:.12f}",5,999,
                "E4C5G"
            ])
        r=contrasts[(comp,age)]
        registry.append([
            "CONTRAST",r["year"],comp,age,"NA","RENTER_MINUS_OWNER_STATE",r["statistic_id"],
            f"{r['point']:.12f}",f"{r['imp_var']:.12f}",f"{r['rep_mean']:.12f}",
            f"{r['samp_var']:.12f}",f"{r['comb_var']:.12f}",f"{r['se']:.12f}",5,999,
            "E4C5H"
        ])

with REGISTRY.open("w",encoding="utf-8",newline="") as fh:
    w=csv.writer(fh,delimiter="\t",lineterminator="\n")
    w.writerow([
        "inference_role","year","component","age_band","tenure","contrast","statistic_id",
        "point_state","imputation_variance_state","sampling_replicate_mean_state",
        "sampling_variance_state","combined_variance_state","combined_se_state",
        "implicate_count","replicate_count","frozen_source_phase"
    ])
    w.writerows(registry)

hard=[
    ("CELL_INFERENCE_ROW_COUNT",len(cells)),
    ("CONTRAST_INFERENCE_ROW_COUNT",len(contrasts)),
    ("CLOSEOUT_REGISTRY_ROW_COUNT",len(registry)),
    ("CELL_VARIANCE_ALGEBRA_PASS",1),
    ("CELL_SE_ALGEBRA_PASS",1),
    ("CONTRAST_VARIANCE_ALGEBRA_PASS",1),
    ("CONTRAST_SE_ALGEBRA_PASS",1),
    ("CONTRAST_POINT_ARITHMETIC_PASS",1),
    ("SIGN_USED_AS_CLOSEOUT_GATE",0),
    ("STATISTICAL_SIGNIFICANCE_USED_AS_CLOSEOUT_GATE",0),
    ("MAGNITUDE_USED_AS_CLOSEOUT_GATE",0),
    ("OWNER_RENTER_DIRECTION_USED_AS_CLOSEOUT_GATE",0),
    ("K_D_COVARIANCE_COMPUTED",0),
    ("CROSS_COORDINATE_METRIC_SCALE_FROZEN",0),
    ("GEOMETRY_AUTHORIZED",0),
]
with HARD.open("w",encoding="utf-8",newline="") as fh:
    w=csv.writer(fh,delimiter="\t",lineterminator="\n")
    w.writerow(["gate","value"])
    w.writerows(hard)

decision=[
    ("K_COMPONENT_TRANSFORMED_CELL_INFERENCE_FROZEN",1),
    ("D_COMPONENT_TRANSFORMED_CELL_INFERENCE_FROZEN",1),
    ("K_COMPONENT_PAIRED_TENURE_CONTRAST_INFERENCE_FROZEN",1),
    ("D_COMPONENT_PAIRED_TENURE_CONTRAST_INFERENCE_FROZEN",1),
    ("K_D_COMPONENT_INFERENCE_CLOSED",1),
    ("K_D_READY_FOR_LATER_STATE_REGISTRY",1),
    ("K_D_CROSS_COORDINATE_COVARIANCE_COMPUTED",0),
    ("CROSS_COORDINATE_METRIC_SCALE_FROZEN",0),
    ("GEOMETRY_AUTHORIZED",0),
    ("E4C6_FULL_STATE_VECTOR_READINESS_PREFLIGHT_AUTHORIZED",1),
]
with DECISION.open("w",encoding="utf-8",newline="") as fh:
    w=csv.writer(fh,delimiter="\t",lineterminator="\n")
    w.writerow(["decision","value"])
    w.writerows(decision)

log="\n".join([
    "CELL_INFERENCE_ROW_COUNT=16",
    "CONTRAST_INFERENCE_ROW_COUNT=8",
    "CLOSEOUT_REGISTRY_ROW_COUNT=24",
    "CELL_VARIANCE_ALGEBRA_PASS=1",
    "CELL_SE_ALGEBRA_PASS=1",
    "CONTRAST_VARIANCE_ALGEBRA_PASS=1",
    "CONTRAST_SE_ALGEBRA_PASS=1",
    "CONTRAST_POINT_ARITHMETIC_PASS=1",
    "NEW_ESTIMATOR_INTRODUCED=0",
    "NEW_TRANSFORM_INTRODUCED=0",
    "NEW_NUMERIC_INFERENCE_INTRODUCED=0",
    "SIGN_USED_AS_CLOSEOUT_GATE=0",
    "STATISTICAL_SIGNIFICANCE_USED_AS_CLOSEOUT_GATE=0",
    "MAGNITUDE_USED_AS_CLOSEOUT_GATE=0",
    "OWNER_RENTER_DIRECTION_USED_AS_CLOSEOUT_GATE=0",
    "K_D_COMPONENT_INFERENCE_CLOSED=1",
    "K_D_READY_FOR_LATER_STATE_REGISTRY=1",
    "K_D_COVARIANCE_COMPUTED=0",
    "CROSS_COORDINATE_METRIC_SCALE_FROZEN=0",
    "GEOMETRY_READY=0",
    "GEOMETRY_AUTHORIZED=0",
    "DIMENSIONALITY_TEST_AUTHORIZED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "E4C5I_K_D_COMPONENT_INFERENCE_CLOSEOUT=PASS",
    "E4C6_FULL_STATE_VECTOR_READINESS_PREFLIGHT_AUTHORIZED=1",
])+"\n"

EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
print("===== K/D CLOSEOUT REGISTRY =====")
for r in registry:
    print("\t".join(map(str,r)))
