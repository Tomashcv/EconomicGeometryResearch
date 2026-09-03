#!/usr/bin/env python3
from pathlib import Path
import csv,hashlib,json,math

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"data/metadata/E4C3E_h_housing_evidence_closeout_contract.json"
LINEAGE=ROOT/"data/metadata/E4C3E_frozen_input_lineage.tsv"
COMPS=ROOT/"data/results/E4C3D_h_access_owner_renter_comparisons.tsv"

EXEC=ROOT/"data/metadata/E4C3E_execution.txt"
AUDIT=ROOT/"data/metadata/E4C3E_h_housing_evidence_closeout_audit.txt"
INTERP=ROOT/"data/results/E4C3E_h_access_primary_interpretation.tsv"
DECISION=ROOT/"data/results/E4C3E_h_current_operating_representation.tsv"
NEXT=ROOT/"data/results/E4C3E_post_h_research_sequence.tsv"

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""): h.update(b)
    return h.hexdigest()
def rows(p):
    with p.open("r",encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f,delimiter="\t"))
def f(x):
    v=float(x)
    if not math.isfinite(v): raise RuntimeError("nonfinite frozen result")
    return v

c=json.loads(CONTRACT.read_text())
assert c["phase"]=="E4C3E"
assert c["interpretation_rules"]["direction_gate"] is False
assert c["operating_representation"]["H_full_state_complete"] is False

for r in rows(LINEAGE):
    p=ROOT/r["artifact"]
    if not p.exists() or sha(p)!=r["sha256"]:
        raise RuntimeError(f"lineage mismatch {r['artifact']}")

src=[r for r in rows(COMPS) if r["role"]=="PRIMARY" and r["estimand"]=="H_ACCESS_SPACE_ROOMS_PER_PERSON"]
if len(src)!=4:
    raise RuntimeError(f"expected 4 primary comparison rows, got {len(src)}")

out=[]
negative=0
diff_excl=0
ratio_below1=0
ratio_excl1=0
for r in src:
    owner=f(r["owner"]); renter=f(r["renter"])
    diff=f(r["diff"]); dlo=f(r["diff_lo"]); dhi=f(r["diff_hi"])
    ratio=f(r["ratio"]); rlo=f(r["ratio_lo"]); rhi=f(r["ratio_hi"])
    sign="RENTER_LOWER" if diff<0 else ("RENTER_HIGHER" if diff>0 else "EQUAL_POINT")
    d_excl=int(dlo>0 or dhi<0)
    r_excl=int(rlo>1 or rhi<1)
    negative += int(diff<0)
    diff_excl += d_excl
    ratio_below1 += int(ratio<1)
    ratio_excl1 += r_excl
    out.append([
        r["age_band"],f"{owner:.12f}",f"{renter:.12f}",f"{diff:.12f}",
        f"{dlo:.12f}",f"{dhi:.12f}",str(d_excl),sign,
        f"{ratio:.12f}",f"{rlo:.12f}",f"{rhi:.12f}",str(r_excl)
    ])

with INTERP.open("w",encoding="utf-8",newline="") as f0:
    w=csv.writer(f0,delimiter="\t",lineterminator="\n")
    w.writerow(["age_band","owner","renter","renter_minus_owner","diff_ci95_low","diff_ci95_high","diff_ci_excludes_zero","point_direction","renter_div_owner","ratio_ci95_low","ratio_ci95_high","ratio_ci_excludes_one"])
    w.writerows(out)

decision=[
("H_CONCEPTUAL_TARGET","HOUSING_ECONOMIC_SECURITY_AND_ACCESS"),
("H_SERVICE_REMAINS_VALID_DESCRIPTIVE_EVIDENCE","1"),
("H_SERVICE_IS_STATE_COORDINATE","0"),
("H_ACCESS_SPACE_SUBCOORDINATE_IDENTIFIED","1"),
("H_ACCESS_SPACE_ESTIMAND","H_ACCESS_SPACE_ROOMS_PER_PERSON"),
("H_ACCESS_SPACE_CURRENT_OPERATING_NUMERICAL_SUBCOORDINATE","1"),
("H_FULL_STATE_COMPLETE","0"),
("H_FULL_ARCHITECTURE_SELECTED","0"),
("H_CURRENT_REPRESENTATION_IS_PERMANENT_DEFINITION","0"),
("AHS_ADEQUACY_SECURITY_ROUTE","PRESERVED_FUTURE_RESEARCH"),
("H_SERVICE_H_ACCESS_AUTO_SCALAR","0"),
("H_UNRESOLVED_FULL_CONCEPT_BLOCKS_I_RESEARCH","0"),
("E4C4_I_EMPLOYMENT_LABOR_SECURITY_REPRESENTATION_PREFLIGHT_AUTHORIZED","1"),
]
with DECISION.open("w",encoding="utf-8",newline="") as f0:
    w=csv.writer(f0,delimiter="\t",lineterminator="\n")
    w.writerow(["decision","value"]);w.writerows(decision)

seq=[
("1","E4C4","I_EMPLOYMENT_LABOR_SECURITY_REPRESENTATION","AUTHORIZED_NEXT"),
("2","POST_E4C4","K_D_DIMENSIONLESS_TRANSFORM_FREEZE","AFTER_I"),
("3","POST_TRANSFORMS","COORDINATE_READINESS_CLOSEOUT","BEFORE_GEOMETRY"),
("FUTURE","H_EXTENSION","AHS_ADEQUACY_SECURITY_SENSITIVITY","NONBLOCKING"),
]
with NEXT.open("w",encoding="utf-8",newline="") as f0:
    w=csv.writer(f0,delimiter="\t",lineterminator="\n")
    w.writerow(["order","phase","scope","status"]);w.writerows(seq)

log="\n".join([
"RAW_SURVEY_DATA_READ=0",
"NEW_HOUSING_VALUES_OPENED=0",
"REESTIMATION_PERFORMED=0",
"NEW_REPLICATES_COMPUTED=0",
"FROZEN_E4C3D_RESULTS_ONLY=1",
"H_ACCESS_PRIMARY_AGE_BANDS=4",
f"H_ACCESS_PRIMARY_RENTER_LOWER_POINT_COUNT={negative}",
f"H_ACCESS_PRIMARY_DIFF_CI_EXCLUDES_ZERO_COUNT={diff_excl}",
f"H_ACCESS_PRIMARY_RENTER_OWNER_RATIO_BELOW_ONE_COUNT={ratio_below1}",
f"H_ACCESS_PRIMARY_RATIO_CI_EXCLUDES_ONE_COUNT={ratio_excl1}",
"OUTCOME_DIRECTION_USED_AS_ARCHITECTURE_GATE=0",
"STATISTICAL_SIGNIFICANCE_USED_AS_ARCHITECTURE_GATE=0",
"MAGNITUDE_USED_AS_ARCHITECTURE_GATE=0",
"H_SERVICE_REMAINS_VALID_DESCRIPTIVE_EVIDENCE=1",
"H_SERVICE_IS_STATE_COORDINATE=0",
"H_ACCESS_SPACE_SUBCOORDINATE_IDENTIFIED=1",
"H_ACCESS_SPACE_CURRENT_OPERATING_NUMERICAL_SUBCOORDINATE=1",
"H_FULL_STATE_COMPLETE=0",
"H_FULL_ARCHITECTURE_SELECTED=0",
"H_CURRENT_REPRESENTATION_IS_PERMANENT_DEFINITION=0",
"AHS_ADEQUACY_SECURITY_ROUTE=PRESERVED_FUTURE_RESEARCH",
"H_SERVICE_H_ACCESS_PERSON_LEVEL_JOIN=0",
"H_SERVICE_H_ACCESS_JOINT_COVARIANCE=0",
"H_SERVICE_H_ACCESS_AUTO_SCALAR=0",
"H_UNRESOLVED_FULL_CONCEPT_BLOCKS_I_RESEARCH=0",
"FIVE_COMPONENT_STATE_VECTOR_AUTHORIZED=0",
"FIVE_COMPONENT_NORMALIZATION_AUTHORIZED=0",
"GEOMETRY_AUTHORIZED=0",
"DIMENSIONALITY_TEST_AUTHORIZED=0",
"REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
"FINAL_SCALAR_AUTHORIZED=0",
"E4C3E_H_HOUSING_EVIDENCE_CLOSEOUT=PASS",
"E4C4_I_EMPLOYMENT_LABOR_SECURITY_REPRESENTATION_PREFLIGHT_AUTHORIZED=1",
])+"\n"

EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
print("===== PRIMARY H_ACCESS CLOSEOUT — DESCRIPTIVE / NO OUTCOME GATE =====")
for x in out:
    print(f"{x[0]}: OWNER={float(x[1]):.6f} RENTER={float(x[2]):.6f} DIFF={float(x[3]):.6f} CI=[{float(x[4]):.6f},{float(x[5]):.6f}]")
