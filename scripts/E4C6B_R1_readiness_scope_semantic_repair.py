#!/usr/bin/env python3
from pathlib import Path
import csv, json

ROOT=Path(__file__).resolve().parents[1]

C_REPR=ROOT/"data/results/E4C2E_c_current_operating_decision.tsv"
H_REPR=ROOT/"data/results/E4C3E_h_current_operating_representation.tsv"
I_REPR=ROOT/"data/results/E4C4_i_current_operating_representation.tsv"
I_SUB=ROOT/"data/results/E4C4_i_subcoordinate_registry.tsv"
R0_EXEC=ROOT/"data/metadata/E4C6B_R0_execution.txt"

EXEC=ROOT/"data/metadata/E4C6B_R1_execution.txt"
AUDIT=ROOT/"data/metadata/E4C6B_R1_readiness_scope_semantic_repair_audit.txt"
MATRIX=ROOT/"data/results/E4C6B_R1_component_readiness_matrix.tsv"
DECISION=ROOT/"data/results/E4C6B_R1_state_vector_readiness_decision.tsv"

def d2(path):
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        rows=list(csv.reader(f,delimiter="\t"))
    if not rows or rows[0][:2] != ["decision","value"]:
        raise RuntimeError(f"unexpected decision schema: {path}")
    return {r[0]:r[1] for r in rows[1:] if len(r)>=2}

r0=R0_EXEC.read_text(encoding="utf-8")
for x in [
    "H_READINESS_SCOPE_MISMATCH=1",
    "I_COUNT_SCOPE_MISMATCH=1",
    "STRUCTURAL_REPAIR_CANDIDATE=ROLE_AWARE_I_PRIMARY_COUNT_PLUS_H_COMPONENT_STATE_SCOPE_CLASSIFICATION",
]:
    if x not in r0.splitlines():
        raise RuntimeError(f"missing frozen R0 basis: {x}")

c=d2(C_REPR)
h=d2(H_REPR)
i=d2(I_REPR)
with I_SUB.open("r",encoding="utf-8-sig",newline="") as f:
    isub=list(csv.DictReader(f,delimiter="\t"))

i_primary=[r for r in isub if r.get("role")=="PRIMARY"]
i_sens=[r for r in isub if r.get("role")=="SENSITIVITY"]
other=[r for r in isub if r.get("role") not in {"PRIMARY","SENSITIVITY"}]
if other:
    raise RuntimeError(f"unexpected I roles: {sorted({r.get('role') for r in other})}")

# C.
c_repr_ready=0
c_num_subcoord_ready=0
c_full_scalar=int(
    c.get("C_REAL_STATE_COORDINATE_IDENTIFIED")=="1"
    and c.get("C_COORDINATE_VALUES_AUTHORIZED")=="1"
)
c_common=c_full_scalar

# H.
h_repr_ready=int(
    h.get("H_ACCESS_SPACE_SUBCOORDINATE_IDENTIFIED")=="1"
    and h.get("H_ACCESS_SPACE_CURRENT_OPERATING_NUMERICAL_SUBCOORDINATE")=="1"
)
h_num_subcoord_ready=h_repr_ready
h_full_scalar=int(
    h.get("H_FULL_STATE_COMPLETE")=="1"
    and h.get("H_FULL_ARCHITECTURE_SELECTED")=="1"
    and h.get("H_SERVICE_H_ACCESS_AUTO_SCALAR")=="1"
)
h_common=h_full_scalar

# K/D frozen prior readiness.
k_repr_ready=k_num_subcoord_ready=k_full_scalar=k_common=1
d_repr_ready=d_num_subcoord_ready=d_full_scalar=d_common=1

# I.
frozen_primary_count=int(i.get("I_PRIMARY_SUBCOORDINATE_COUNT","-1"))
i_primary_count=len(i_primary)
i_sens_count=len(i_sens)
if frozen_primary_count != i_primary_count:
    raise RuntimeError(
        f"I primary count mismatch frozen={frozen_primary_count} registry={i_primary_count}"
    )
i_repr_ready=int(
    i_primary_count>0
    and all(r.get("status")=="CURRENT_OPERATING_PRIMARY" for r in i_primary)
)
i_num_subcoord_ready=i_repr_ready
i_scalar_selected=int(i.get("I_SCALAR_SELECTED")=="1")
i_equal_weight_authorized=int(i.get("I_EQUAL_WEIGHT_SCALAR_AUTHORIZED")=="1")
i_full_scalar=int(i_repr_ready and i_scalar_selected and i_equal_weight_authorized)
i_common=i_full_scalar

rows=[
    ["C",1,c_repr_ready,c_num_subcoord_ready,c_full_scalar,c_common,0,0,
     "LINEAGE_RESOLVED_UNRESOLVED_EVIDENCE_ONLY","E4C2E"],
    ["H",1,h_repr_ready,h_num_subcoord_ready,h_full_scalar,h_common,1,0,
     "CURRENT_NUMERICAL_SUBCOORDINATE_READY_FULL_H_SCALAR_NOT_FROZEN","E4C3E"],
    ["K",1,k_repr_ready,k_num_subcoord_ready,k_full_scalar,k_common,1,0,
     "READY_FULL_COMPONENT_SCALAR_COORDINATE","E4C5I"],
    ["D",1,d_repr_ready,d_num_subcoord_ready,d_full_scalar,d_common,1,0,
     "READY_FULL_COMPONENT_SCALAR_COORDINATE","E4C5I"],
    ["I",1,i_repr_ready,i_num_subcoord_ready,i_full_scalar,i_common,i_primary_count,i_sens_count,
     "PRIMARY_MULTI_SUBCOORDINATE_REPRESENTATION_READY_SINGLE_I_SCALAR_NOT_FROZEN","E4C4"],
]

with MATRIX.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow([
        "component",
        "exact_lineage_resolved_for_decision",
        "current_operating_representation_ready",
        "current_numerical_subcoordinate_ready",
        "full_component_scalar_coordinate_ready",
        "ready_for_common_scalar_component_registry",
        "primary_numeric_subcoordinate_count",
        "sensitivity_subcoordinate_count",
        "status",
        "canonical_lineage",
    ])
    w.writerows(rows)

full_five_scalar=int(all([c_common,h_common,k_common,d_common,i_common]))
decisions=[
    ["C_READY_FOR_COMMON_STATE_REGISTRY",str(c_common)],
    ["H_CURRENT_OPERATING_REPRESENTATION_READY",str(h_repr_ready)],
    ["H_ACCESS_NUMERICAL_SUBCOORDINATE_READY",str(h_num_subcoord_ready)],
    ["H_FULL_COMPONENT_SCALAR_COORDINATE_READY",str(h_full_scalar)],
    ["H_READY_FOR_COMMON_STATE_REGISTRY",str(h_common)],
    ["K_READY_FOR_COMMON_STATE_REGISTRY","1"],
    ["D_READY_FOR_COMMON_STATE_REGISTRY","1"],
    ["I_CURRENT_OPERATING_REPRESENTATION_READY",str(i_repr_ready)],
    ["I_PRIMARY_SUBCOORDINATE_COUNT",str(i_primary_count)],
    ["I_SENSITIVITY_SUBCOORDINATE_COUNT",str(i_sens_count)],
    ["I_SINGLE_COMPONENT_SCALAR_COORDINATE_READY",str(i_full_scalar)],
    ["I_READY_FOR_COMMON_STATE_REGISTRY",str(i_common)],
    ["FIVE_COMPONENT_LABELS_DO_NOT_PROVE_FIVE_DIMENSIONS","1"],
    ["FULL_CHKDI_FIVE_SCALAR_COORDINATE_STATE_VECTOR_READY",str(full_five_scalar)],
]
with DECISION.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["decision","value"])
    w.writerows(decisions)

log="\n".join([
    "PRIOR_E4C6B_ATTEMPT_PRESERVED=1",
    "FROZEN_R0_REPAIR_BASIS_REUSED=1",
    "R1_REPAIR_SCOPE=READINESS_SEMANTICS_AND_ROLE_AWARE_COUNT_ONLY",
    f"C_READY_FOR_COMMON_STATE_REGISTRY={c_common}",
    f"H_CURRENT_OPERATING_REPRESENTATION_READY={h_repr_ready}",
    f"H_ACCESS_NUMERICAL_SUBCOORDINATE_READY={h_num_subcoord_ready}",
    f"H_FULL_COMPONENT_SCALAR_COORDINATE_READY={h_full_scalar}",
    f"H_READY_FOR_COMMON_STATE_REGISTRY={h_common}",
    "K_READY_FOR_COMMON_STATE_REGISTRY=1",
    "D_READY_FOR_COMMON_STATE_REGISTRY=1",
    f"I_CURRENT_OPERATING_REPRESENTATION_READY={i_repr_ready}",
    f"I_FROZEN_PRIMARY_SUBCOORDINATE_COUNT={frozen_primary_count}",
    f"I_PRIMARY_SUBCOORDINATE_COUNT={i_primary_count}",
    f"I_SENSITIVITY_SUBCOORDINATE_COUNT={i_sens_count}",
    f"I_SINGLE_COMPONENT_SCALAR_COORDINATE_READY={i_full_scalar}",
    f"I_READY_FOR_COMMON_STATE_REGISTRY={i_common}",
    "H_NUMERICAL_SUBCOORDINATE_PROMOTED_TO_FULL_SCALAR=0",
    "I_SENSITIVITY_ROWS_PROMOTED_TO_PRIMARY=0",
    "COMMON_STATE_REGISTRY_REQUIRES_FULL_COMPONENT_SCALAR_COORDINATE=1",
    "FIVE_COMPONENT_LABELS_DO_NOT_PROVE_FIVE_DIMENSIONS=1",
    f"FULL_CHKDI_FIVE_SCALAR_COORDINATE_STATE_VECTOR_READY={full_five_scalar}",
    "ECONOMIC_RESULT_NUMERIC_ROWS_OPENED=0",
    "NEW_ECONOMIC_VALUES_USED=0",
    "SIGN_USED_AS_READINESS_GATE=0",
    "MAGNITUDE_USED_AS_READINESS_GATE=0",
    "STATISTICAL_SIGNIFICANCE_USED_AS_READINESS_GATE=0",
    "OWNER_RENTER_DIRECTION_USED_AS_READINESS_GATE=0",
    "SCIENTIFIC_ESTIMATOR_MUTATED=0",
    "TRANSFORM_MUTATED=0",
    "COMPONENT_DEFINITION_MUTATED=0",
    "SOURCE_RESULT_VALUES_MUTATED=0",
    "NEW_INFERENCE_COMPUTED=0",
    "CROSS_COORDINATE_COVARIANCE_COMPUTED=0",
    "CROSS_COORDINATE_METRIC_SCALE_FROZEN=0",
    "GEOMETRY_READY=0",
    "GEOMETRY_AUTHORIZED=0",
    "DIMENSIONALITY_TEST_AUTHORIZED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "E4C6B_R1_READINESS_SCOPE_SEMANTIC_REPAIR=PASS",
    "E4C6C_POST_READINESS_DISPOSITION_PREFLIGHT_AUTHORIZED=1",
])+"\n"

EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
print("===== CORRECTED COMPONENT READINESS MATRIX =====")
for r in rows:
    print("\t".join(map(str,r)))
