#!/usr/bin/env python3
from pathlib import Path
import csv,json,math,re

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"data/metadata/E4C5I_R0_serialized_precision_forensic_contract.json"
G=ROOT/"data/results/E4C5G_transformed_cohort_inference.tsv"
H=ROOT/"data/results/E4C5H_transformed_owner_renter_contrast_inference.tsv"
EXEC=ROOT/"data/metadata/E4C5I_R0_execution.txt"
AUDIT=ROOT/"data/metadata/E4C5I_R0_serialized_precision_forensic_audit.txt"
DETAIL=ROOT/"data/results/E4C5I_R0_serialization_interval_diagnostics.tsv"
DEC=ROOT/"data/results/E4C5I_R0_serialized_precision_forensic_decision.tsv"

Q=1e-12
HQ=0.5e-12
OLD_REL=2e-10
OLD_ABS=2e-11

def old_close(a,b):
    return math.isclose(a,b,rel_tol=OLD_REL,abs_tol=OLD_ABS)

def interval(x):
    return (x-HQ,x+HQ)

def overlap(a,b):
    return max(a[0],b[0]) <= min(a[1],b[1])

def linear_comb_interval(imp,samp):
    il,ih=interval(imp); sl,sh=interval(samp)
    return (1.2*il+sl,1.2*ih+sh)

def sqrt_interval(var):
    lo,hi=interval(var)
    if lo<0: lo=0.0
    return (math.sqrt(lo),math.sqrt(hi))

def diff_interval(renter,owner):
    rl,rh=interval(renter); ol,oh=interval(owner)
    return (rl-oh,rh-ol)

def decimals12(s):
    return re.fullmatch(r"-?\d+\.\d{12}",str(s).strip()) is not None

c=json.loads(CONTRACT.read_text())
assert c["serialization_model"]["expected_decimal_places"]==12
assert c["serialization_model"]["quantization_step"]==1e-12
assert c["repair_policy"]["do_not_choose_new_tolerance_from_observed_max_residual"] is True
assert c["repair_policy"]["repair_authorized_in_R0"] is False

details=[]
old_fail_se=0
old_fail_comb=0
old_fail_point=0
interval_fail_se=0
interval_fail_comb=0
interval_fail_point=0
format_fail=0
max_se_resid=0.0
max_comb_resid=0.0
max_point_resid=0.0

with G.open("r",encoding="utf-8",newline="") as f:
    rows=list(csv.DictReader(f,delimiter="\t"))
if len(rows)!=16: raise RuntimeError(f"G rows={len(rows)}")
for r in rows:
    key=f"CELL:{r['component']}:{r['age_band']}:{r['tenure']}"
    fields=["imputation_variance_state","sampling_variance_state","combined_variance_state","combined_se_state"]
    format_ok=all(decimals12(r[x]) for x in fields)
    format_fail += int(not format_ok)
    imp=float(r[fields[0]]); samp=float(r[fields[1]]); comb=float(r[fields[2]]); se=float(r[fields[3]])

    comb_calc=1.2*imp+samp
    comb_res=abs(comb_calc-comb); max_comb_resid=max(max_comb_resid,comb_res)
    old_comb=old_close(comb_calc,comb); old_fail_comb += int(not old_comb)
    int_comb=overlap(linear_comb_interval(imp,samp),interval(comb)); interval_fail_comb += int(not int_comb)

    se_calc=math.sqrt(comb)
    se_res=abs(se_calc-se); max_se_resid=max(max_se_resid,se_res)
    old_se=old_close(se_calc,se); old_fail_se += int(not old_se)
    int_se=overlap(sqrt_interval(comb),interval(se)); interval_fail_se += int(not int_se)

    details.append([key,"COMBINED_VARIANCE",f"{comb_res:.18e}",int(old_comb),int(int_comb),int(format_ok)])
    details.append([key,"SE_SQRT_VARIANCE",f"{se_res:.18e}",int(old_se),int(int_se),int(format_ok)])

with H.open("r",encoding="utf-8",newline="") as f:
    rows=list(csv.DictReader(f,delimiter="\t"))
if len(rows)!=8: raise RuntimeError(f"H rows={len(rows)}")
for r in rows:
    key=f"CONTRAST:{r['component']}:{r['age_band']}"
    fields=["owner_point_state","renter_point_state","renter_minus_owner_point_state","imputation_variance_state_contrast","sampling_variance_state_contrast","combined_variance_state_contrast","combined_se_state_contrast"]
    format_ok=all(decimals12(r[x]) for x in fields)
    format_fail += int(not format_ok)

    owner=float(r[fields[0]]); renter=float(r[fields[1]]); point=float(r[fields[2]])
    imp=float(r[fields[3]]); samp=float(r[fields[4]]); comb=float(r[fields[5]]); se=float(r[fields[6]])

    pcalc=renter-owner; pres=abs(pcalc-point); max_point_resid=max(max_point_resid,pres)
    old_p=old_close(pcalc,point); old_fail_point += int(not old_p)
    int_p=overlap(diff_interval(renter,owner),interval(point)); interval_fail_point += int(not int_p)

    ccalc=1.2*imp+samp; cres=abs(ccalc-comb); max_comb_resid=max(max_comb_resid,cres)
    old_c=old_close(ccalc,comb); old_fail_comb += int(not old_c)
    int_c=overlap(linear_comb_interval(imp,samp),interval(comb)); interval_fail_comb += int(not int_c)

    scalc=math.sqrt(comb); sres=abs(scalc-se); max_se_resid=max(max_se_resid,sres)
    old_s=old_close(scalc,se); old_fail_se += int(not old_s)
    int_s=overlap(sqrt_interval(comb),interval(se)); interval_fail_se += int(not int_s)

    details.append([key,"POINT_RENTER_MINUS_OWNER",f"{pres:.18e}",int(old_p),int(int_p),int(format_ok)])
    details.append([key,"COMBINED_VARIANCE",f"{cres:.18e}",int(old_c),int(int_c),int(format_ok)])
    details.append([key,"SE_SQRT_VARIANCE",f"{sres:.18e}",int(old_s),int(int_s),int(format_ok)])

with DETAIL.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["object","identity","absolute_residual_from_serialized_values","attempt1_fixed_tolerance_pass","quantization_interval_pass","all_relevant_fields_exactly_12dp"])
    w.writerows(details)

all_interval_pass=(interval_fail_se==0 and interval_fail_comb==0 and interval_fail_point==0 and format_fail==0)
old_rejects=(old_fail_se+old_fail_comb+old_fail_point)>0
cause=("FIXED_TOLERANCE_INCOMPATIBLE_WITH_INDEPENDENT_12DP_SERIALIZATION" if all_interval_pass and old_rejects else "UNRESOLVED_ALGEBRA_OR_SERIALIZATION_INCONSISTENCY")
candidate=("REPLACE_FIXED_SERIALIZED_ALGEBRA_TOLERANCE_WITH_12DP_QUANTIZATION_INTERVAL_CHECK" if all_interval_pass and old_rejects else "NO_REPAIR_CANDIDATE")

with DEC.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["diagnostic","value"])
    w.writerows([
        ["SERIALIZATION_DECIMAL_PLACES",12],
        ["SERIALIZATION_QUANTIZATION_STEP","1e-12"],
        ["ATTEMPT1_ABSOLUTE_TOLERANCE","2e-11"],
        ["ATTEMPT1_SE_FAILURE_COUNT",old_fail_se],
        ["ATTEMPT1_COMBINED_VARIANCE_FAILURE_COUNT",old_fail_comb],
        ["ATTEMPT1_CONTRAST_POINT_FAILURE_COUNT",old_fail_point],
        ["QUANTIZATION_INTERVAL_SE_FAILURE_COUNT",interval_fail_se],
        ["QUANTIZATION_INTERVAL_COMBINED_VARIANCE_FAILURE_COUNT",interval_fail_comb],
        ["QUANTIZATION_INTERVAL_CONTRAST_POINT_FAILURE_COUNT",interval_fail_point],
        ["TWELVE_DECIMAL_FORMAT_FAILURE_COUNT",format_fail],
        ["MAX_SE_RESIDUAL_DIAGNOSTIC",f"{max_se_resid:.18e}"],
        ["MAX_COMBINED_VARIANCE_RESIDUAL_DIAGNOSTIC",f"{max_comb_resid:.18e}"],
        ["MAX_CONTRAST_POINT_RESIDUAL_DIAGNOSTIC",f"{max_point_resid:.18e}"],
        ["FAILURE_CAUSE_CLASS",cause],
        ["STRUCTURAL_REPAIR_CANDIDATE",candidate],
        ["OBSERVED_MAX_RESIDUAL_USED_TO_CHOOSE_REPAIR",0],
        ["SCIENTIFIC_ESTIMATOR_MUTATED",0],
        ["REPAIR_AUTHORIZED",0],
    ])

log="\n".join([
    "POST_E4C5I_FAILURE_FORENSIC=1",
    "PRIOR_FAILURE_PRESERVED=1",
    "SERIALIZATION_DECIMAL_PLACES=12",
    "SERIALIZATION_QUANTIZATION_STEP=1e-12",
    "ATTEMPT1_ABSOLUTE_TOLERANCE=2e-11",
    f"ATTEMPT1_SE_FAILURE_COUNT={old_fail_se}",
    f"ATTEMPT1_COMBINED_VARIANCE_FAILURE_COUNT={old_fail_comb}",
    f"ATTEMPT1_CONTRAST_POINT_FAILURE_COUNT={old_fail_point}",
    f"QUANTIZATION_INTERVAL_SE_FAILURE_COUNT={interval_fail_se}",
    f"QUANTIZATION_INTERVAL_COMBINED_VARIANCE_FAILURE_COUNT={interval_fail_comb}",
    f"QUANTIZATION_INTERVAL_CONTRAST_POINT_FAILURE_COUNT={interval_fail_point}",
    f"TWELVE_DECIMAL_FORMAT_FAILURE_COUNT={format_fail}",
    f"MAX_SE_RESIDUAL_DIAGNOSTIC={max_se_resid:.18e}",
    f"MAX_COMBINED_VARIANCE_RESIDUAL_DIAGNOSTIC={max_comb_resid:.18e}",
    f"MAX_CONTRAST_POINT_RESIDUAL_DIAGNOSTIC={max_point_resid:.18e}",
    f"FAILURE_CAUSE_CLASS={cause}",
    f"STRUCTURAL_REPAIR_CANDIDATE={candidate}",
    "OBSERVED_MAX_RESIDUAL_USED_TO_CHOOSE_REPAIR=0",
    "SCIENTIFIC_ESTIMATOR_MUTATED=0",
    "TRANSFORM_MUTATED=0",
    "VARIANCE_ENGINE_MUTATED=0",
    "CLOSEOUT_SEMANTICS_MUTATED=0",
    "REPAIR_AUTHORIZED=0",
    "GEOMETRY_AUTHORIZED=0",
    "E4C5I_R0_SERIALIZED_PRECISION_FORENSIC=PASS",
])+"\n"
EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
