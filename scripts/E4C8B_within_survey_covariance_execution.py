#!/usr/bin/env python3
from pathlib import Path
from fractions import Fraction
from decimal import Decimal, localcontext, ROUND_HALF_EVEN
import csv, json

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"data/metadata/E4C8B_within_survey_covariance_execution_contract.json"

SCF_IMP=ROOT/"data/results/E4C5G_transformed_implicate_statistics.tsv"
SCF_REP=ROOT/"data/results/E4C5G_transformed_replicate_statistics.tsv"
CPS_POINT=ROOT/"data/results/E4A2D_2022_cps_i_cohort_inference.tsv"
CPS_REP=ROOT/"data/results/E4A2D_2022_cps_i_replicate_estimates.tsv"

EXEC=ROOT/"data/metadata/E4C8B_execution.txt"
AUDIT=ROOT/"data/metadata/E4C8B_within_survey_covariance_execution_audit.txt"
REG=ROOT/"data/results/E4C8B_within_survey_covariance_registry.tsv"
ALIGN=ROOT/"data/results/E4C8B_pair_alignment_diagnostics.tsv"
GATES=ROOT/"data/results/E4C8B_execution_hard_gates.tsv"
DECISION=ROOT/"data/results/E4C8B_within_survey_covariance_execution_decision.tsv"

c=json.loads(CONTRACT.read_text(encoding="utf-8"))
ages=c["ages"]
tenures=c["tenures"]
age_map=c["age_normalization"]

def age_norm(x):
    if x not in age_map:
        raise RuntimeError(f"unrecognized age token: {x!r}")
    return age_map[x]

def frac(s):
    x=s.strip()
    if not x:
        raise RuntimeError("empty numeric source string")
    d=Decimal(x)
    if not d.is_finite():
        raise RuntimeError(f"nonfinite numeric source string: {x}")
    return Fraction(d)

def mean(xs):
    if not xs:
        raise RuntimeError("empty mean")
    return sum(xs,Fraction(0,1))/len(xs)

def sample_cov(xs,ys):
    if len(xs)!=len(ys):
        raise RuntimeError("paired covariance length mismatch")
    n=len(xs)
    if n<2:
        raise RuntimeError("sample covariance requires n>=2")
    mx,my=mean(xs),mean(ys)
    return sum(((x-mx)*(y-my) for x,y in zip(xs,ys)),Fraction(0,1))/(n-1)

def cps_cov(xs,ys,x0,y0):
    if len(xs)!=160 or len(ys)!=160:
        raise RuntimeError("CPS covariance requires exactly 160 paired replicates")
    return Fraction(1,40)*sum(((x-x0)*(y-y0) for x,y in zip(xs,ys)),Fraction(0,1))

def dec30(q):
    with localcontext() as ctx:
        ctx.prec=100
        d=Decimal(q.numerator)/Decimal(q.denominator)
        quantum=Decimal("1e-30")
        z=d.quantize(quantum,rounding=ROUND_HALF_EVEN)
        if z==0:
            z=abs(z)
        return format(z,"f")

def ftxt(q):
    return f"{q.numerator}/{q.denominator}"

# ---------------- SCF implicates ----------------
scf_imp={}
with SCF_IMP.open("r",encoding="utf-8",newline="") as f:
    for row in csv.DictReader(f,delimiter="\t"):
        if row["year"]!="2022":
            continue
        sid=row["statistic_id"]
        comp=row["component"]
        if (sid,comp) not in {("K_FIN_MEAN","K"),("D_PIRTOTAL_MEAN","D")}:
            continue
        age=age_norm(row["age_band"])
        ten=row["tenure"]
        if age not in ages or ten not in tenures:
            continue
        idx=row["implicate"]
        key=(age,ten,idx,sid)
        if key in scf_imp:
            raise RuntimeError(f"duplicate SCF implicate key {key}")
        scf_imp[key]=frac(row["transformed_state_value"])

# ---------------- SCF replicates ----------------
scf_rep={}
with SCF_REP.open("r",encoding="utf-8",newline="") as f:
    for row in csv.DictReader(f,delimiter="\t"):
        if row["year"]!="2022":
            continue
        sid=row["statistic_id"]
        comp=row["component"]
        if (sid,comp) not in {("K_FIN_MEAN","K"),("D_PIRTOTAL_MEAN","D")}:
            continue
        age=age_norm(row["age_band"])
        ten=row["tenure"]
        if age not in ages or ten not in tenures:
            continue
        idx=row["replicate"]
        key=(age,ten,idx,sid)
        if key in scf_rep:
            raise RuntimeError(f"duplicate SCF replicate key {key}")
        scf_rep[key]=frac(row["transformed_state_value"])

# ---------------- CPS full sample ----------------
cps_point={}
with CPS_POINT.open("r",encoding="utf-8",newline="") as f:
    for row in csv.DictReader(f,delimiter="\t"):
        if row["year"]!="2022" or row["role"]!="PRIMARY":
            continue
        est=row["estimand"]
        if est not in {"I_FYFT_SHARE","I_SEARCH_BURDEN_SHARE"}:
            continue
        age=age_norm(row["age_band"])
        ten=row["tenure"]
        if age not in ages or ten not in tenures:
            continue
        expected_sign="1" if est=="I_FYFT_SHARE" else "-1"
        if row["state_sign"].strip() not in {expected_sign,("+"+expected_sign if expected_sign=="1" else expected_sign)}:
            raise RuntimeError(f"CPS point state_sign mismatch for {est}: {row['state_sign']!r}")
        sign=1 if est=="I_FYFT_SHARE" else -1
        key=(age,ten,est)
        if key in cps_point:
            raise RuntimeError(f"duplicate CPS full-sample key {key}")
        cps_point[key]=sign*frac(row["point_estimate"])

# ---------------- CPS replicates ----------------
cps_rep={}
with CPS_REP.open("r",encoding="utf-8",newline="") as f:
    for row in csv.DictReader(f,delimiter="\t"):
        if row["year"]!="2022":
            continue
        est=row["estimand"]
        if est not in {"I_FYFT_SHARE","I_SEARCH_BURDEN_SHARE"}:
            continue
        age=age_norm(row["age_band"])
        ten=row["tenure_or_contrast"]
        if age not in ages or ten not in tenures:
            continue
        sign=1 if est=="I_FYFT_SHARE" else -1
        idx=row["replicate"]
        key=(age,ten,idx,est)
        if key in cps_rep:
            raise RuntimeError(f"duplicate CPS replicate key {key}")
        cps_rep[key]=sign*frac(row["value"])

registry=[]
alignment=[]

# SCF 8 cells
for age in ages:
    for ten in tenures:
        imp_k={k[2]:v for k,v in scf_imp.items() if k[0]==age and k[1]==ten and k[3]=="K_FIN_MEAN"}
        imp_d={k[2]:v for k,v in scf_imp.items() if k[0]==age and k[1]==ten and k[3]=="D_PIRTOTAL_MEAN"}
        rep_k={k[2]:v for k,v in scf_rep.items() if k[0]==age and k[1]==ten and k[3]=="K_FIN_MEAN"}
        rep_d={k[2]:v for k,v in scf_rep.items() if k[0]==age and k[1]==ten and k[3]=="D_PIRTOTAL_MEAN"}

        if len(imp_k)!=5 or len(imp_d)!=5 or set(imp_k)!=set(imp_d):
            raise RuntimeError(f"SCF implicate pairing failure {age} {ten}: {len(imp_k)} {len(imp_d)}")
        if len(rep_k)!=999 or len(rep_d)!=999 or set(rep_k)!=set(rep_d):
            raise RuntimeError(f"SCF replicate pairing failure {age} {ten}: {len(rep_k)} {len(rep_d)}")

        ikeys=sorted(imp_k,key=lambda x:(len(x),x))
        rkeys=sorted(rep_k,key=lambda x:(len(x),x))
        imp_cov=sample_cov([imp_k[x] for x in ikeys],[imp_d[x] for x in ikeys])
        samp_cov=sample_cov([rep_k[x] for x in rkeys],[rep_d[x] for x in rkeys])
        combined=Fraction(6,5)*imp_cov+samp_cov

        registry.append([
            "2022",age,ten,"SCF_K_D","SCF2022",
            "K_FIN_MEAN_TRANSFORMED","D_PIRTOTAL_MEAN_STATE_TRANSFORMED",
            str(imp_cov.numerator),str(imp_cov.denominator),ftxt(imp_cov),
            str(samp_cov.numerator),str(samp_cov.denominator),ftxt(samp_cov),
            str(combined.numerator),str(combined.denominator),ftxt(combined),dec30(combined),
            "5","999","SCF_COMBINED_MI_REPLICATE_COVARIANCE","E4C8A"
        ])
        alignment.append([
            "SCF_K_D",age,ten,
            "5","5","5","1",
            "999","999","999","1",
            "1","1"
        ])

# CPS 8 cells
for age in ages:
    for ten in tenures:
        kf=(age,ten,"I_FYFT_SHARE")
        ks=(age,ten,"I_SEARCH_BURDEN_SHARE")
        if kf not in cps_point or ks not in cps_point:
            raise RuntimeError(f"CPS full-sample pairing failure {age} {ten}")

        fy={k[2]:v for k,v in cps_rep.items() if k[0]==age and k[1]==ten and k[3]=="I_FYFT_SHARE"}
        se={k[2]:v for k,v in cps_rep.items() if k[0]==age and k[1]==ten and k[3]=="I_SEARCH_BURDEN_SHARE"}

        if len(fy)!=160 or len(se)!=160 or set(fy)!=set(se):
            raise RuntimeError(f"CPS replicate pairing failure {age} {ten}: {len(fy)} {len(se)}")

        rkeys=sorted(fy,key=lambda x:(len(x),x))
        cov=cps_cov([fy[x] for x in rkeys],[se[x] for x in rkeys],cps_point[kf],cps_point[ks])

        registry.append([
            "2022",age,ten,"CPS_I_PAIR","CPS_ASEC_2022",
            "I_FYFT_SHARE","I_SEARCH_SECURITY",
            "","","",
            str(cov.numerator),str(cov.denominator),ftxt(cov),
            str(cov.numerator),str(cov.denominator),ftxt(cov),dec30(cov),
            "0","160","CPS_160_REPLICATE_COVARIANCE_AFTER_FROZEN_STATE_SIGN","E4C8A"
        ])
        alignment.append([
            "CPS_I_PAIR",age,ten,
            "0","0","0","1",
            "160","160","160","1",
            "1","1"
        ])

if len(registry)!=16:
    raise RuntimeError(f"covariance registry row count {len(registry)} != 16")
if len(alignment)!=16:
    raise RuntimeError(f"alignment row count {len(alignment)} != 16")

with REG.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow([
        "year","age_band","tenure","pair_id","survey","coordinate_a","coordinate_b",
        "imputation_covariance_numerator","imputation_covariance_denominator","imputation_covariance_exact",
        "sampling_covariance_numerator","sampling_covariance_denominator","sampling_covariance_exact",
        "combined_covariance_numerator","combined_covariance_denominator","combined_covariance_exact",
        "combined_covariance_decimal_30",
        "implicate_count","replicate_count","estimator","frozen_formula_phase"
    ])
    w.writerows(registry)

with ALIGN.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow([
        "pair_id","age_band","tenure",
        "expected_implicate_count","observed_a_implicate_count","observed_b_implicate_count","implicate_key_sets_equal",
        "expected_replicate_count","observed_a_replicate_count","observed_b_replicate_count","replicate_key_sets_equal",
        "full_sample_pair_complete","numeric_parse_pass"
    ])
    w.writerows(alignment)

gate_rows=[
    ["E4C8A_FROZEN_FORMULAS_REUSED","PASS"],
    ["EXACT_RATIONAL_ARITHMETIC","PASS"],
    ["BINARY_FLOAT_ROUNDTRIP_USED_FOR_COVARIANCE","0"],
    ["SCF_PAIR_ALIGNMENT","PASS"],
    ["CPS_PAIR_ALIGNMENT","PASS"],
    ["EXACT_16_CELL_COVARIANCE_REGISTRY","PASS"],
    ["NO_OUTCOME_GATE","PASS"],
    ["NO_CROSS_SURVEY_ZERO_ASSUMPTION","PASS"],
    ["GEOMETRY_REMAINS_UNAUTHORIZED","PASS"],
]
with GATES.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["gate","value"])
    w.writerows(gate_rows)

decision_rows=[
    ["WITHIN_SURVEY_COVARIANCE_ROW_COUNT","16"],
    ["SCF_K_D_COVARIANCE_ROW_COUNT","8"],
    ["CPS_I_PAIR_COVARIANCE_ROW_COUNT","8"],
    ["SCF_IMPLICATE_PAIRING_COMPLETE","1"],
    ["SCF_REPLICATE_PAIRING_COMPLETE","1"],
    ["CPS_FULL_SAMPLE_PAIRING_COMPLETE","1"],
    ["CPS_REPLICATE_PAIRING_COMPLETE","1"],
    ["EXACT_RATIONAL_ARITHMETIC_USED","1"],
    ["BINARY_FLOAT_ROUNDTRIP_USED","0"],
    ["COVARIANCE_SIGN_USED_AS_GATE","0"],
    ["COVARIANCE_MAGNITUDE_USED_AS_GATE","0"],
    ["STATISTICAL_SIGNIFICANCE_USED_AS_GATE","0"],
    ["OWNER_RENTER_DIRECTION_USED_AS_GATE","0"],
    ["CROSS_SURVEY_COVARIANCE_COMPUTED","0"],
    ["CROSS_SURVEY_COVARIANCE_ASSUMED_ZERO","0"],
    ["ECONOMIC_STATE_DEPENDENCE_INFERRED","0"],
    ["METRIC_MUTATED","0"],
    ["I_SCALAR_CREATED","0"],
    ["GEOMETRY_AUTHORIZED","0"],
    ["E4C8C_CROSS_SURVEY_UNCERTAINTY_POLICY_PREFLIGHT_AUTHORIZED","1"],
]
with DECISION.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["decision","value"])
    w.writerows(decision_rows)

log="\n".join([
    "E4C8A_FROZEN_FORMULAS_REUSED=1",
    "ECONOMIC_SOURCE_ROWS_OPENED_AFTER_E4C8B_PRECOMMIT=1",
    "EXACT_RATIONAL_ARITHMETIC_USED=1",
    "BINARY_FLOAT_ROUNDTRIP_USED_FOR_COVARIANCE=0",
    "SCF_K_D_COVARIANCE_ROW_COUNT=8",
    "CPS_I_PAIR_COVARIANCE_ROW_COUNT=8",
    "WITHIN_SURVEY_COVARIANCE_ROW_COUNT=16",
    "SCF_IMPLICATE_COUNT_PER_CELL=5",
    "SCF_REPLICATE_COUNT_PER_CELL=999",
    "CPS_REPLICATE_COUNT_PER_CELL=160",
    "SCF_IMPLICATE_PAIRING_COMPLETE=1",
    "SCF_REPLICATE_PAIRING_COMPLETE=1",
    "CPS_FULL_SAMPLE_PAIRING_COMPLETE=1",
    "CPS_REPLICATE_PAIRING_COMPLETE=1",
    "PAIRING_KEY_UNIQUENESS_PASS=1",
    "NUMERIC_SOURCE_PARSE_PASS=1",
    "COVARIANCE_SIGN_USED_AS_GATE=0",
    "COVARIANCE_MAGNITUDE_USED_AS_GATE=0",
    "STATISTICAL_SIGNIFICANCE_USED_AS_GATE=0",
    "OWNER_RENTER_DIRECTION_USED_AS_GATE=0",
    "NEW_TRANSFORM_INTRODUCED=0",
    "NEW_VARIANCE_ESTIMATOR_INTRODUCED=0",
    "NEW_COVARIANCE_FORMULA_INTRODUCED_AFTER_PRECOMMIT=0",
    "CROSS_SURVEY_COVARIANCE_COMPUTED=0",
    "CROSS_SURVEY_COVARIANCE_ASSUMED_ZERO=0",
    "UNKNOWN_CROSS_SURVEY_COVARIANCE_REPLACED_BY_ZERO=0",
    "ECONOMIC_STATE_DEPENDENCE_INFERRED=0",
    "METRIC_MUTATED=0",
    "C_INCLUDED_IN_COVARIANCE_REGISTRY=0",
    "H_ACCESS_PROMOTED_TO_FULL_H_STATE=0",
    "I_SCALAR_CREATED=0",
    "PARTIAL_PANEL_IS_FULL_CHKDI_STATE_VECTOR=0",
    "CROSS_COORDINATE_METRIC_SCALE_FROZEN=1",
    "GEOMETRY_READY=0",
    "GEOMETRY_AUTHORIZED=0",
    "DIMENSIONALITY_TEST_AUTHORIZED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "E4C8B_WITHIN_SURVEY_COVARIANCE_EXECUTION=PASS",
    "E4C8C_CROSS_SURVEY_UNCERTAINTY_POLICY_PREFLIGHT_AUTHORIZED=1",
])+"\n"

EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")

print(log,end="")
print("===== WITHIN-SURVEY COVARIANCE REGISTRY — NO OUTCOME GATE =====")
print(REG.read_text(encoding="utf-8"),end="")
print("===== PAIR ALIGNMENT DIAGNOSTICS =====")
print(ALIGN.read_text(encoding="utf-8"),end="")
