#!/usr/bin/env python3
from pathlib import Path
import csv, json

ROOT=Path(__file__).resolve().parents[1]

R1_MATRIX=ROOT/"data/results/E4C6B_R1_component_readiness_matrix.tsv"
C_REPR=ROOT/"data/results/E4C2E_c_current_operating_decision.tsv"
H_REPR=ROOT/"data/results/E4C3E_h_current_operating_representation.tsv"
I_REPR=ROOT/"data/results/E4C4_i_current_operating_representation.tsv"
I_SUB=ROOT/"data/results/E4C4_i_subcoordinate_registry.tsv"

EXEC=ROOT/"data/metadata/E4C6C_execution.txt"
AUDIT=ROOT/"data/metadata/E4C6C_post_readiness_disposition_audit.txt"
DISP=ROOT/"data/results/E4C6C_component_disposition.tsv"
COORD=ROOT/"data/results/E4C6C_operational_coordinate_eligibility.tsv"
SEQ=ROOT/"data/results/E4C6C_post_readiness_research_sequence.tsv"
DECISION=ROOT/"data/results/E4C6C_post_readiness_disposition_decision.tsv"

def d2(path):
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        rows=list(csv.reader(f,delimiter="\t"))
    if not rows or rows[0][:2] != ["decision","value"]:
        raise RuntimeError(f"unexpected decision schema: {path}")
    return {r[0]:r[1] for r in rows[1:] if len(r)>=2}

with R1_MATRIX.open("r",encoding="utf-8-sig",newline="") as f:
    m={r["component"]:r for r in csv.DictReader(f,delimiter="\t")}
if set(m)!={"C","H","K","D","I"}:
    raise RuntimeError("R1 component set mismatch")

c=d2(C_REPR)
h=d2(H_REPR)
i=d2(I_REPR)
with I_SUB.open("r",encoding="utf-8-sig",newline="") as f:
    sub=list(csv.DictReader(f,delimiter="\t"))

primary=[r for r in sub if r.get("role")=="PRIMARY"]
sens=[r for r in sub if r.get("role")=="SENSITIVITY"]

# Frozen structural gates only.
assert m["C"]["ready_for_common_scalar_component_registry"]=="0"
assert c.get("C_CONCEPT_DROPPED_FROM_MODEL")=="0"
assert c.get("C_CURRENT_OPERATING_BRANCH")=="3_UNRESOLVED_EVIDENCE_ONLY"

assert m["H"]["current_numerical_subcoordinate_ready"]=="1"
assert m["H"]["full_component_scalar_coordinate_ready"]=="0"
assert h.get("H_ACCESS_SPACE_CURRENT_OPERATING_NUMERICAL_SUBCOORDINATE")=="1"
assert h.get("H_FULL_STATE_COMPLETE")=="0"

assert m["K"]["full_component_scalar_coordinate_ready"]=="1"
assert m["D"]["full_component_scalar_coordinate_ready"]=="1"

assert m["I"]["current_numerical_subcoordinate_ready"]=="1"
assert m["I"]["full_component_scalar_coordinate_ready"]=="0"
assert i.get("I_PRIMARY_SUBCOORDINATE_COUNT")=="2"
assert len(primary)==2
assert len(sens)==2
assert i.get("I_SCALAR_SELECTED")=="0"

# Dispositions.
disp=[
    ["C","UNRESOLVED_EVIDENCE_ONLY",0,0,0,0,"NOT_DROPPED_FUTURE_PRECOMMITTED_REOPEN_ONLY"],
    ["H","CURRENT_NUMERICAL_SUBCOORDINATE_AVAILABLE",1,1,0,0,"H_ACCESS_NOT_PROMOTED_TO_FULL_H_STATE"],
    ["K","FULL_COMPONENT_SCALAR_COORDINATE_AVAILABLE",1,1,1,1,"FULL_COMPONENT_SCALAR"],
    ["D","FULL_COMPONENT_SCALAR_COORDINATE_AVAILABLE",1,1,1,1,"FULL_COMPONENT_SCALAR"],
    ["I","TWO_PRIMARY_NUMERICAL_SUBCOORDINATES_AVAILABLE",1,1,0,0,"PRIMARYS_SEPARATE_NO_FORCED_I_SCALAR"],
]
with DISP.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow([
        "component","disposition","current_representation_ready",
        "numeric_coordinate_or_subcoordinate_available",
        "full_component_scalar_coordinate_ready",
        "common_scalar_component_registry_ready","restriction"
    ])
    w.writerows(disp)

# Only semantic coordinate eligibility; no economic values.
coord=[
    ["H","H_ACCESS_SPACE_ROOMS_PER_PERSON","PRIMARY_OBSERVED_SUBCOORDINATE","DIMENSIONLESS","HIGHER_IS_BETTER",1,0],
    ["K","K_FIN_MEAN_TRANSFORMED","FULL_COMPONENT_SCALAR_COORDINATE","DIMENSIONLESS","HIGHER_IS_BETTER",1,1],
    ["D","D_PIRTOTAL_MEAN_STATE_TRANSFORMED","FULL_COMPONENT_SCALAR_COORDINATE","DIMENSIONLESS","HIGHER_IS_BETTER",1,1],
]
for r in primary:
    coord.append([
        "I",r["name"],"PRIMARY_OBSERVED_SUBCOORDINATE",
        r["units"],r["orientation"],1,0
    ])

if len(coord)!=5:
    raise RuntimeError(f"unexpected current coordinate count {len(coord)}")

with COORD.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow([
        "component","coordinate_id","semantic_role","units","orientation",
        "eligible_for_partial_observed_coordinate_registry",
        "is_full_component_scalar_coordinate"
    ])
    w.writerows(coord)

seq=[
    [1,"E4C6D","PARTIAL_OBSERVED_COORDINATE_REGISTRY_PREFLIGHT",
     "freeze exact value lineage/schema for H,K,D and two PRIMARY I subcoordinates; no metric or geometry"],
    [2,"E4C7","CROSS_COORDINATE_METRIC_SCALE_ARCHITECTURE_PREFLIGHT",
     "only after E4C6D; freeze admissible scale policy without outcome fitting"],
    [3,"E4C8","CROSS_SURVEY_DEPENDENCE_AND_COVARIANCE_FEASIBILITY",
     "determine what covariance is identifiable across independent surveys before multivariate uncertainty"],
    [4,"E4C9","PARTIAL_STATE_GEOMETRY_OR_DIMENSIONALITY_PREFLIGHT",
     "only if metric and dependence policies pass; cannot be labeled full CHKDI or real inflation"],
    [5,"PARALLEL","C_H_I_COMPLETENESS_RESEARCH",
     "C identification and fuller H/I architecture remain open and may supersede the partial panel only via precommitted evidence"],
]
with SEQ.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["order","phase","scope","constraint"])
    w.writerows(seq)

dec=[
    ["C_DISPOSITION","UNRESOLVED_EVIDENCE_ONLY_NOT_DROPPED"],
    ["H_DISPOSITION","CURRENT_NUMERICAL_SUBCOORDINATE_AVAILABLE_NOT_FULL_H_SCALAR"],
    ["K_DISPOSITION","FULL_COMPONENT_SCALAR_COORDINATE_AVAILABLE"],
    ["D_DISPOSITION","FULL_COMPONENT_SCALAR_COORDINATE_AVAILABLE"],
    ["I_DISPOSITION","TWO_PRIMARY_SUBCOORDINATES_AVAILABLE_NO_SINGLE_I_SCALAR"],
    ["NUMERICALLY_REPRESENTED_CONCEPT_COUNT","4"],
    ["PARTIAL_OBSERVED_NUMERICAL_COORDINATE_COUNT","5"],
    ["PARTIAL_COORDINATE_PANEL_IS_FULL_CHKDI_STATE_VECTOR","0"],
    ["PARTIAL_COORDINATE_PANEL_IS_FINAL_MODEL","0"],
    ["FIVE_COORDINATES_DO_NOT_IMPLY_FIVE_COMPONENTS","1"],
    ["C_DROPPED_FROM_MODEL","0"],
    ["H_ACCESS_PROMOTED_TO_FULL_H_STATE","0"],
    ["I_SCALAR_FORCED","0"],
    ["I_SENSITIVITY_ROWS_INCLUDED_IN_PRIMARY_COORDINATE_SET","0"],
    ["E4C6D_PARTIAL_OBSERVED_COORDINATE_REGISTRY_PREFLIGHT_AUTHORIZED","1"],
]
with DECISION.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["decision","value"])
    w.writerows(dec)

log="\n".join([
    "E4C6B_R1_REUSED_AS_CANONICAL_READINESS=1",
    "C_DISPOSITION=UNRESOLVED_EVIDENCE_ONLY_NOT_DROPPED",
    "H_DISPOSITION=CURRENT_NUMERICAL_SUBCOORDINATE_AVAILABLE_NOT_FULL_H_SCALAR",
    "K_DISPOSITION=FULL_COMPONENT_SCALAR_COORDINATE_AVAILABLE",
    "D_DISPOSITION=FULL_COMPONENT_SCALAR_COORDINATE_AVAILABLE",
    "I_DISPOSITION=TWO_PRIMARY_SUBCOORDINATES_AVAILABLE_NO_SINGLE_I_SCALAR",
    "NUMERICALLY_REPRESENTED_CONCEPT_COUNT=4",
    "PARTIAL_OBSERVED_NUMERICAL_COORDINATE_COUNT=5",
    "PARTIAL_COORDINATE_PANEL_IS_FULL_CHKDI_STATE_VECTOR=0",
    "PARTIAL_COORDINATE_PANEL_IS_FINAL_MODEL=0",
    "FIVE_COORDINATES_DO_NOT_IMPLY_FIVE_COMPONENTS=1",
    "C_DROPPED_FROM_MODEL=0",
    "H_ACCESS_PROMOTED_TO_FULL_H_STATE=0",
    "I_PRIMARY_SUBCOORDINATE_COUNT=2",
    "I_SENSITIVITY_SUBCOORDINATE_COUNT=2",
    "I_SCALAR_FORCED=0",
    "I_SENSITIVITY_ROWS_INCLUDED_IN_PRIMARY_COORDINATE_SET=0",
    "ECONOMIC_RESULT_NUMERIC_ROWS_OPENED=0",
    "NEW_ECONOMIC_VALUES_USED=0",
    "SIGN_USED_AS_DISPOSITION_GATE=0",
    "MAGNITUDE_USED_AS_DISPOSITION_GATE=0",
    "STATISTICAL_SIGNIFICANCE_USED_AS_DISPOSITION_GATE=0",
    "OWNER_RENTER_DIRECTION_USED_AS_DISPOSITION_GATE=0",
    "COMPONENT_DEFINITION_MUTATED=0",
    "TRANSFORM_MUTATED=0",
    "NEW_ESTIMATOR_INTRODUCED=0",
    "NEW_INFERENCE_COMPUTED=0",
    "CROSS_COORDINATE_COVARIANCE_COMPUTED=0",
    "CROSS_COORDINATE_METRIC_SCALE_FROZEN=0",
    "GEOMETRY_READY=0",
    "GEOMETRY_AUTHORIZED=0",
    "DIMENSIONALITY_TEST_AUTHORIZED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "E4C6C_POST_READINESS_DISPOSITION_PREFLIGHT=PASS",
    "E4C6D_PARTIAL_OBSERVED_COORDINATE_REGISTRY_PREFLIGHT_AUTHORIZED=1",
])+"\n"

EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
print("===== COMPONENT DISPOSITION =====")
for r in disp:
    print("\t".join(map(str,r)))
print("===== OPERATIONAL COORDINATE ELIGIBILITY — STRUCTURAL ONLY =====")
for r in coord:
    print("\t".join(map(str,r)))
print("===== POST-READINESS RESEARCH SEQUENCE =====")
for r in seq:
    print("\t".join(map(str,r)))
