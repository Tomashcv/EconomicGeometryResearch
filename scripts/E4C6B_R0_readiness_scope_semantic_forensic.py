#!/usr/bin/env python3
from pathlib import Path
import csv, json

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"data/metadata/E4C6B_R0_readiness_scope_semantic_forensic_contract.json"

B_EXEC=ROOT/"data/metadata/E4C6B_execution.txt"
B_MATRIX=ROOT/"data/results/E4C6B_component_readiness_matrix.tsv"
C_REPR=ROOT/"data/results/E4C2E_c_current_operating_decision.tsv"
H_REPR=ROOT/"data/results/E4C3E_h_current_operating_representation.tsv"
I_REPR=ROOT/"data/results/E4C4_i_current_operating_representation.tsv"
I_SUB=ROOT/"data/results/E4C4_i_subcoordinate_registry.tsv"

EXEC=ROOT/"data/metadata/E4C6B_R0_execution.txt"
AUDIT=ROOT/"data/metadata/E4C6B_R0_readiness_scope_semantic_forensic_audit.txt"
DIAG=ROOT/"data/results/E4C6B_R0_readiness_scope_diagnostics.tsv"
DECISION=ROOT/"data/results/E4C6B_R0_readiness_scope_semantic_forensic_decision.tsv"

c=json.loads(CONTRACT.read_text(encoding="utf-8"))
assert c["phase"]=="E4C6B_R0"
assert c["allowed_reads"]["economic estimate rows"] is False
assert c["repair_authorized"] is False
assert c["E4C6C_authorized"] is False

def dict2(path):
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        rows=list(csv.reader(f,delimiter="\t"))
    if not rows or rows[0][:2] != ["decision","value"]:
        raise RuntimeError(f"unexpected decision schema: {path}")
    return {r[0]:r[1] for r in rows[1:] if len(r)>=2}

def matrix(path):
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        return {r["component"]:r for r in csv.DictReader(f,delimiter="\t")}

btxt=B_EXEC.read_text(encoding="utf-8")
bm=matrix(B_MATRIX)
cr=dict2(C_REPR)
hr=dict2(H_REPR)
ir=dict2(I_REPR)

with I_SUB.open("r",encoding="utf-8-sig",newline="") as f:
    sub=list(csv.DictReader(f,delimiter="\t"))

primary=[r for r in sub if r.get("role")=="PRIMARY"]
sensitivity=[r for r in sub if r.get("role")=="SENSITIVITY"]

# C coherence control.
c_source_ready = int(
    cr.get("C_REAL_STATE_COORDINATE_IDENTIFIED")=="1"
    and cr.get("C_COORDINATE_VALUES_AUTHORIZED")=="1"
)
c_e4c6b_ready = int(bm["C"]["single_scalar_coordinate_ready"])
c_coherent = int(c_source_ready == c_e4c6b_ready)

# H scope forensic.
h_subcoord = int(hr.get("H_ACCESS_SPACE_SUBCOORDINATE_IDENTIFIED")=="1")
h_numeric_subcoord = int(hr.get("H_ACCESS_SPACE_CURRENT_OPERATING_NUMERICAL_SUBCOORDINATE")=="1")
h_full_state_complete = int(hr.get("H_FULL_STATE_COMPLETE")=="1")
h_full_arch_selected = int(hr.get("H_FULL_ARCHITECTURE_SELECTED")=="1")
h_auto_scalar = int(hr.get("H_SERVICE_H_ACCESS_AUTO_SCALAR")=="1")
h_e4c6b_scalar_ready = int(bm["H"]["single_scalar_coordinate_ready"])
h_scope_mismatch = int(
    h_subcoord==1
    and h_numeric_subcoord==1
    and h_full_state_complete==0
    and h_full_arch_selected==0
    and h_auto_scalar==0
    and h_e4c6b_scalar_ready==1
)

# I scope/count forensic.
i_frozen_primary_count=int(ir.get("I_PRIMARY_SUBCOORDINATE_COUNT","-1"))
i_registry_primary_count=len(primary)
i_registry_sensitivity_count=len(sensitivity)
i_registry_all_count=len(sub)
i_e4c6b_count=int(bm["I"]["subcoordinate_count"])
i_primary_count_coherent=int(i_frozen_primary_count==i_registry_primary_count)
i_e4c6b_count_is_all_rows=int(i_e4c6b_count==i_registry_all_count)
i_count_scope_mismatch=int(
    i_frozen_primary_count==2
    and i_registry_primary_count==2
    and i_registry_sensitivity_count==2
    and i_e4c6b_count==4
)

diag=[
    ["C","SOURCE_COMPONENT_SCALAR_READY",c_source_ready,"E4C2E current operating decision"],
    ["C","E4C6B_SINGLE_SCALAR_READY",c_e4c6b_ready,"E4C6B matrix"],
    ["C","CLASSIFICATION_COHERENT",c_coherent,"control"],
    ["H","H_ACCESS_SPACE_SUBCOORDINATE_IDENTIFIED",h_subcoord,"E4C3E"],
    ["H","H_ACCESS_SPACE_CURRENT_OPERATING_NUMERICAL_SUBCOORDINATE",h_numeric_subcoord,"E4C3E"],
    ["H","H_FULL_STATE_COMPLETE",h_full_state_complete,"E4C3E"],
    ["H","H_FULL_ARCHITECTURE_SELECTED",h_full_arch_selected,"E4C3E"],
    ["H","H_SERVICE_H_ACCESS_AUTO_SCALAR",h_auto_scalar,"E4C3E"],
    ["H","E4C6B_SINGLE_SCALAR_READY",h_e4c6b_scalar_ready,"E4C6B matrix"],
    ["H","READINESS_SCOPE_MISMATCH",h_scope_mismatch,"subcoordinate vs component scalar"],
    ["I","FROZEN_PRIMARY_SUBCOORDINATE_COUNT",i_frozen_primary_count,"E4C4 current representation"],
    ["I","REGISTRY_PRIMARY_COUNT",i_registry_primary_count,"E4C4 subcoordinate registry"],
    ["I","REGISTRY_SENSITIVITY_COUNT",i_registry_sensitivity_count,"E4C4 subcoordinate registry"],
    ["I","REGISTRY_ALL_DATA_ROW_COUNT",i_registry_all_count,"E4C4 subcoordinate registry"],
    ["I","E4C6B_REPORTED_SUBCOORDINATE_COUNT",i_e4c6b_count,"E4C6B matrix"],
    ["I","PRIMARY_COUNT_COHERENT_WITH_E4C4",i_primary_count_coherent,"role-aware control"],
    ["I","E4C6B_COUNT_EQUALS_ALL_REGISTRY_ROWS",i_e4c6b_count_is_all_rows,"scope diagnostic"],
    ["I","COUNT_SCOPE_MISMATCH",i_count_scope_mismatch,"primary vs sensitivity"],
]

with DIAG.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["component","diagnostic","value","basis"])
    w.writerows(diag)

failure_class=[]
if h_scope_mismatch:
    failure_class.append("H_NUMERICAL_SUBCOORDINATE_CONFLATED_WITH_COMPLETE_COMPONENT_SCALAR_COORDINATE")
if i_count_scope_mismatch:
    failure_class.append("I_PRIMARY_AND_SENSITIVITY_ROWS_CONFLATED_IN_SUBCOORDINATE_COUNT")
if not failure_class:
    failure_class=["NO_SCOPE_MISMATCH_DETECTED"]

repair_candidate = (
    "ROLE_AWARE_I_PRIMARY_COUNT_PLUS_H_COMPONENT_STATE_SCOPE_CLASSIFICATION"
    if any(x!="NO_SCOPE_MISMATCH_DETECTED" for x in failure_class)
    else "NONE"
)

decision_rows=[
    ["POST_E4C6B_FORENSIC","1"],
    ["PRIOR_E4C6B_FROZEN_AND_PRESERVED","1"],
    ["C_CLASSIFICATION_COHERENT",str(c_coherent)],
    ["H_READINESS_SCOPE_MISMATCH",str(h_scope_mismatch)],
    ["I_COUNT_SCOPE_MISMATCH",str(i_count_scope_mismatch)],
    ["FAILURE_CAUSE_CLASS",";".join(failure_class)],
    ["STRUCTURAL_REPAIR_CANDIDATE",repair_candidate],
    ["ECONOMIC_RESULT_NUMERIC_ROWS_OPENED","0"],
    ["NEW_ECONOMIC_VALUES_USED","0"],
    ["SCIENTIFIC_ESTIMATOR_MUTATED","0"],
    ["TRANSFORM_MUTATED","0"],
    ["COMPONENT_DEFINITION_MUTATED","0"],
    ["REPAIR_AUTHORIZED","0"],
    ["E4C6C_AUTHORIZED","0"],
    ["GEOMETRY_AUTHORIZED","0"],
]
with DECISION.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["decision","value"])
    w.writerows(decision_rows)

log="\n".join([
    "POST_E4C6B_FORENSIC=1",
    "PRIOR_E4C6B_FROZEN_AND_PRESERVED=1",
    f"C_CLASSIFICATION_COHERENT={c_coherent}",
    f"H_ACCESS_SPACE_SUBCOORDINATE_IDENTIFIED={h_subcoord}",
    f"H_ACCESS_SPACE_CURRENT_OPERATING_NUMERICAL_SUBCOORDINATE={h_numeric_subcoord}",
    f"H_FULL_STATE_COMPLETE={h_full_state_complete}",
    f"H_FULL_ARCHITECTURE_SELECTED={h_full_arch_selected}",
    f"H_SERVICE_H_ACCESS_AUTO_SCALAR={h_auto_scalar}",
    f"E4C6B_H_SINGLE_SCALAR_COORDINATE_READY={h_e4c6b_scalar_ready}",
    f"H_READINESS_SCOPE_MISMATCH={h_scope_mismatch}",
    f"I_FROZEN_PRIMARY_SUBCOORDINATE_COUNT={i_frozen_primary_count}",
    f"I_REGISTRY_PRIMARY_COUNT={i_registry_primary_count}",
    f"I_REGISTRY_SENSITIVITY_COUNT={i_registry_sensitivity_count}",
    f"I_REGISTRY_ALL_DATA_ROW_COUNT={i_registry_all_count}",
    f"E4C6B_I_REPORTED_SUBCOORDINATE_COUNT={i_e4c6b_count}",
    f"I_PRIMARY_COUNT_COHERENT_WITH_E4C4={i_primary_count_coherent}",
    f"I_COUNT_SCOPE_MISMATCH={i_count_scope_mismatch}",
    f"FAILURE_CAUSE_CLASS={';'.join(failure_class)}",
    f"STRUCTURAL_REPAIR_CANDIDATE={repair_candidate}",
    "ECONOMIC_RESULT_NUMERIC_ROWS_OPENED=0",
    "NEW_ECONOMIC_VALUES_USED=0",
    "SCIENTIFIC_ESTIMATOR_MUTATED=0",
    "TRANSFORM_MUTATED=0",
    "COMPONENT_DEFINITION_MUTATED=0",
    "REPAIR_AUTHORIZED=0",
    "E4C6C_AUTHORIZED=0",
    "CROSS_COORDINATE_METRIC_SCALE_FROZEN=0",
    "GEOMETRY_AUTHORIZED=0",
    "E4C6B_R0_READINESS_SCOPE_SEMANTIC_FORENSIC=PASS",
])+"\n"

EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
print("===== READINESS SCOPE DIAGNOSTICS =====")
for row in diag:
    print("\t".join(map(str,row)))
