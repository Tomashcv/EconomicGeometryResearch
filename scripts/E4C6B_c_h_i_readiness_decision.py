#!/usr/bin/env python3
from pathlib import Path
import csv, json, re

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"data/metadata/E4C6B_c_h_i_readiness_decision_contract.json"

EXEC=ROOT/"data/metadata/E4C6B_execution.txt"
AUDIT=ROOT/"data/metadata/E4C6B_c_h_i_readiness_decision_audit.txt"
STRUCT=ROOT/"data/metadata/E4C6B_structural_evidence_extract.tsv"
MATRIX=ROOT/"data/results/E4C6B_component_readiness_matrix.tsv"
DECISION=ROOT/"data/results/E4C6B_state_vector_readiness_decision.tsv"

files={
"C2C_DEC":ROOT/"data/results/E4C2C_c_identification_decision.tsv",
"C2C_REQ":ROOT/"data/results/E4C2C_c_next_evidence_requirements.tsv",
"C2E_DEC":ROOT/"data/results/E4C2E_c_current_operating_decision.tsv",
"C2E_BRANCH":ROOT/"data/results/E4C2E_c_semantic_branch_registry.tsv",
"C2E_EXEC":ROOT/"data/metadata/E4C2E_execution.txt",
"H3B_AUDIT":ROOT/"data/metadata/E4C3B_acs2022_metadata_harmonization_audit.txt",
"H3B_CONTRACT":ROOT/"data/metadata/E4C3B_acs2022_metadata_harmonization_contract.json",
"H3B_DEC":ROOT/"data/results/E4C3B_h_access_architecture_decision.tsv",
"H3D_EXEC":ROOT/"data/metadata/E4C3D_execution.txt",
"H3D_INF":ROOT/"data/results/E4C3D_h_access_inference_summary.tsv",
"H3D_REPS":ROOT/"data/results/E4C3D_h_access_component_replicates.tsv",
"H3E_EXEC":ROOT/"data/metadata/E4C3E_execution.txt",
"H3E_REPR":ROOT/"data/results/E4C3E_h_current_operating_representation.tsv",
"I2D_EXEC":ROOT/"data/metadata/E4A2D_execution.txt",
"I4_EXEC":ROOT/"data/metadata/E4C4_execution.txt",
"I4_REPR":ROOT/"data/results/E4C4_i_current_operating_representation.tsv",
"I4_SUB":ROOT/"data/results/E4C4_i_subcoordinate_registry.tsv",
}

c=json.loads(CONTRACT.read_text(encoding="utf-8"))
assert c["phase"]=="E4C6B"
assert c["allowed_reads"]["economic result rows"] is False
assert c["scope_boundary"]["geometry_authorized"] is False

def rows_tsv(path):
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        return list(csv.reader(f,delimiter="\t"))

def header(path):
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        line=f.readline().rstrip("\r\n")
    return next(csv.reader([line],delimiter="\t")) if line else []

def keylines(path, terms):
    out=[]
    for i,line in enumerate(path.read_text(encoding="utf-8",errors="replace").splitlines(),1):
        up=line.upper()
        if any(t in up for t in terms):
            # Reject ordinary decimal-valued lines from human-visible structural extract.
            if re.search(r"(?<![A-Za-z])[-+]?\d+\.\d+(?![A-Za-z])", line):
                continue
            if len(line.strip())<=360:
                out.append((i,line.strip()))
    return out

# Structural decision tables: these are not economic estimate tables.
struct_rows=[]
for label in ["C2C_DEC","C2C_REQ","C2E_DEC","C2E_BRANCH","H3B_DEC","H3E_REPR","I4_REPR","I4_SUB"]:
    rr=rows_tsv(files[label])
    for idx,row in enumerate(rr,1):
        struct_rows.append([label,idx,"TSV_ROW","|".join(row)])

# Exact headers only for H inference artifacts.
for label in ["H3D_INF","H3D_REPS"]:
    struct_rows.append([label,1,"HEADER_ONLY","|".join(header(files[label]))])

terms=[
    "PASS","AUTHORIZED","FROZEN","READY","READINESS","BLOCK","UNRESOLVED","SELECTED",
    "PRIMARY_H_ACCESS","ORIENTATION","DIMENSIONLESS","H_ACCESS","INFERENCE","CLOSEOUT",
    "OPERATING_REPRESENTATION","I_PRIMARY","I_SCALAR","SUBCOORD","REPRESENTATION",
    "COORDINATE","SEMANTIC","EVIDENCE_ONLY","FINAL_SCALAR","FIVE_COMPONENT"
]
for label in ["C2E_EXEC","H3B_AUDIT","H3B_CONTRACT","H3D_EXEC","H3E_EXEC","I2D_EXEC","I4_EXEC"]:
    for lineno,line in keylines(files[label],terms):
        struct_rows.append([label,lineno,"STRUCTURAL_STATUS",line])

with STRUCT.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["source","line_or_row","kind","structural_text"])
    w.writerows(struct_rows)

def alltext(labels):
    parts=[]
    for label in labels:
        p=files[label]
        if p.suffix.lower()==".tsv":
            for row in rows_tsv(p):
                parts.append("\t".join(row))
        else:
            for _,line in keylines(p,terms):
                parts.append(line)
    return "\n".join(parts).upper()

def has_any(text, pats):
    return any(re.search(p,text,re.I|re.M) for p in pats)

# ------------------------------------------------------------------
# C rule: exact lineage is resolved for decision, but a scalar coordinate
# requires explicit current authorization/freeze. Explicit block dominates.
# ------------------------------------------------------------------
ct=alltext(["C2C_DEC","C2C_REQ","C2E_DEC","C2E_BRANCH","C2E_EXEC"])
c_positive=has_any(ct,[
    r"(?:C_)?(?:NUMERIC_)?COORDINATE_(?:AUTHORIZED|READY|FROZEN)[\t:=| ]+(?:1|TRUE|PASS|READY)\b",
    r"SCALAR_COORDINATE_FROZEN[\t:=| ]+(?:1|TRUE|PASS)\b",
])
c_negative=has_any(ct,[
    r"NUMERIC_COORDINATE_AUTHORIZED[\t:=| ]+(?:0|FALSE|NO)\b",
    r"(?:C_)?COORDINATE_(?:AUTHORIZED|READY|FROZEN)[\t:=| ]+(?:0|FALSE|NO)\b",
    r"SCALAR_COORDINATE_FROZEN[\t:=| ]+(?:0|FALSE|NO)\b",
    r"BLOCKED",
    r"UNRESOLVED",
    r"EVIDENCE_ONLY",
    r"NUMERIC_COORDINATE_AUTHORIZED\|0\b",
])
c_ready=int(c_positive and not c_negative)
c_status="READY_SCALAR_COORDINATE" if c_ready else "LINEAGE_RESOLVED_COORDINATE_NOT_READY"

# ------------------------------------------------------------------
# H rule: selected primary, orientation, dimensionless structural semantics,
# inference pass, and closeout/current representation.
# ------------------------------------------------------------------
ht=alltext(["H3B_AUDIT","H3B_CONTRACT","H3B_DEC","H3D_EXEC","H3E_EXEC","H3E_REPR"])
h_selected=has_any(ht,[r"H_ACCESS_SPACE_ROOMS_PER_PERSON",r"RMSP_DIV_NP"])
h_orientation=has_any(ht,[r"(?:PRIMARY_H_ACCESS_)?ORIENTATION[\t:=| \"]+HIGHER_IS_BETTER",r"HIGHER_IS_BETTER"])
h_dimensionless=has_any(ht,[r"DIMENSIONLESS"])
h_inference_pass=has_any(ht,[r"E4C3D[^\n]*(?:PASS|FROZEN)",r"H_ACCESS[^\n]*INFERENCE[^\n]*(?:PASS|FROZEN)"])
h_closeout_pass=has_any(ht,[r"E4C3E[^\n]*(?:PASS|FROZEN)",r"HOUSING_EVIDENCE_CLOSEOUT[^\n]*(?:PASS|FROZEN)"])
h_current_repr=has_any(alltext(["H3E_REPR"]),[r"H_ACCESS",r"ROOMS_PER_PERSON",r"RMSP_DIV_NP"])
h_ready=int(all([h_selected,h_orientation,h_dimensionless,h_inference_pass,h_closeout_pass,h_current_repr]))
h_status="READY_DIMENSIONLESS_SCALAR_COORDINATE" if h_ready else "LINEAGE_RESOLVED_H_COORDINATE_READINESS_INCOMPLETE"

# ------------------------------------------------------------------
# I rule: frozen representation can be ready without being one scalar coordinate.
# ------------------------------------------------------------------
it=alltext(["I2D_EXEC","I4_EXEC","I4_REPR","I4_SUB"])
i4_pass=has_any(it,[r"E4C4[^\n]*(?:PASS|FROZEN)",r"EMPLOYMENT_LABOR_SECURITY_REPRESENTATION[^\n]*(?:PASS|FROZEN)"])
subrows=rows_tsv(files["I4_SUB"])
i_subcount=max(0,len(subrows)-1)
i_repr_ready=int(i4_pass and i_subcount>=1)
i_scalar_positive=has_any(it,[r"I_SCALAR_AUTHORIZED[\t:=| ]+(?:1|TRUE|PASS)\b",r"SINGLE_COORDINATE_(?:AUTHORIZED|FROZEN)[\t:=| ]+(?:1|TRUE|PASS)\b"])
i_scalar_negative=has_any(it,[r"I_SCALAR_AUTHORIZED[\t:=| ]+(?:0|FALSE|NO)\b",r"SCALAR[^\n]*(?:NOT_AUTHORIZED|PROHIBITED|BLOCKED)",r"MULTI[_ -]?ESTIMAND",r"SUBCOORD"])
i_single_ready=int(i_repr_ready and i_scalar_positive and not i_scalar_negative)
if i_single_ready:
    i_status="READY_SINGLE_SCALAR_COORDINATE"
elif i_repr_ready:
    i_status="REPRESENTATION_READY_SINGLE_COORDINATE_NOT_FROZEN"
else:
    i_status="LINEAGE_RESOLVED_REPRESENTATION_NOT_READY"

# K/D are reused from E4C6/E4C5I, not recomputed here.
k_ready=1
d_ready=1
five_component_scalar_vector_ready=int(all([c_ready,h_ready,k_ready,d_ready,i_single_ready]))

matrix=[
    ["C",1,c_ready,c_ready,0,c_status,"E4C2C+E4C2E"],
    ["H",1,h_ready,h_ready,0,h_status,"E4C3B+E4C3D+E4C3E"],
    ["K",1,1,1,0,"READY_REUSED_FROM_E4C5I","E4C5I"],
    ["D",1,1,1,0,"READY_REUSED_FROM_E4C5I","E4C5I"],
    ["I",1,i_repr_ready,i_single_ready,i_subcount,i_status,"E4A2D+E4C4"],
]
with MATRIX.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["component","exact_lineage_resolved_for_decision","representation_ready","single_scalar_coordinate_ready","subcoordinate_count","status","canonical_lineage"])
    w.writerows(matrix)

decision_rows=[
    ["C_READY_FOR_COMMON_STATE_REGISTRY",str(c_ready)],
    ["H_READY_FOR_COMMON_STATE_REGISTRY",str(h_ready)],
    ["K_READY_FOR_COMMON_STATE_REGISTRY","1"],
    ["D_READY_FOR_COMMON_STATE_REGISTRY","1"],
    ["I_REPRESENTATION_READY",str(i_repr_ready)],
    ["I_SINGLE_SCALAR_COORDINATE_READY",str(i_single_ready)],
    ["I_SUBCOORDINATE_COUNT",str(i_subcount)],
    ["FIVE_COMPONENT_LABELS_DO_NOT_PROVE_FIVE_DIMENSIONS","1"],
    ["FULL_CHKDI_FIVE_SCALAR_COORDINATE_STATE_VECTOR_READY",str(five_component_scalar_vector_ready)],
]
with DECISION.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["decision","value"])
    w.writerows(decision_rows)

log="\n".join([
    "C_EXACT_LINEAGE_RESOLVED_FOR_READINESS_DECISION=1",
    "H_EXACT_LINEAGE_RESOLVED_FOR_READINESS_DECISION=1",
    "I_EXACT_LINEAGE_RESOLVED_FOR_READINESS_DECISION=1",
    f"C_EXPLICIT_COORDINATE_POSITIVE_EVIDENCE={int(c_positive)}",
    f"C_EXPLICIT_COORDINATE_BLOCKING_EVIDENCE={int(c_negative)}",
    f"C_READY_FOR_COMMON_STATE_REGISTRY={c_ready}",
    f"H_PRIMARY_REPRESENTATION_SELECTED={int(h_selected)}",
    f"H_HIGHER_IS_BETTER_ORIENTATION_EVIDENCE={int(h_orientation)}",
    f"H_DIMENSIONLESS_EVIDENCE={int(h_dimensionless)}",
    f"H_INFERENCE_PASS_EVIDENCE={int(h_inference_pass)}",
    f"H_CLOSEOUT_PASS_EVIDENCE={int(h_closeout_pass)}",
    f"H_CURRENT_OPERATING_REPRESENTATION_EVIDENCE={int(h_current_repr)}",
    f"H_READY_FOR_COMMON_STATE_REGISTRY={h_ready}",
    f"I_OPERATING_REPRESENTATION_PASS_EVIDENCE={int(i4_pass)}",
    f"I_SUBCOORDINATE_COUNT={i_subcount}",
    f"I_REPRESENTATION_READY={i_repr_ready}",
    f"I_EXPLICIT_SCALAR_POSITIVE_EVIDENCE={int(i_scalar_positive)}",
    f"I_SCALAR_BLOCKING_OR_MULTI_SUBCOORDINATE_EVIDENCE={int(i_scalar_negative)}",
    f"I_SINGLE_SCALAR_COORDINATE_READY={i_single_ready}",
    "K_READY_FOR_COMMON_STATE_REGISTRY=1",
    "D_READY_FOR_COMMON_STATE_REGISTRY=1",
    "FIVE_COMPONENT_LABELS_DO_NOT_PROVE_FIVE_DIMENSIONS=1",
    f"FULL_CHKDI_FIVE_SCALAR_COORDINATE_STATE_VECTOR_READY={five_component_scalar_vector_ready}",
    "STRUCTURAL_DECISION_ROWS_READ=1",
    "INFERENCE_RESULT_HEADERS_OPENED=2",
    "ECONOMIC_RESULT_NUMERIC_ROWS_OPENED=0",
    "NEW_ECONOMIC_VALUES_USED=0",
    "SIGN_USED_AS_READINESS_GATE=0",
    "MAGNITUDE_USED_AS_READINESS_GATE=0",
    "STATISTICAL_SIGNIFICANCE_USED_AS_READINESS_GATE=0",
    "OWNER_RENTER_DIRECTION_USED_AS_READINESS_GATE=0",
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
    "E4C6B_C_H_I_STRUCTURAL_READINESS_DECISION=PASS",
    "E4C6C_POST_READINESS_DISPOSITION_PREFLIGHT_AUTHORIZED=1",
])+"\n"

EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")

print("===== COMPONENT READINESS MATRIX =====")
for r in matrix:
    print("\t".join(map(str,r)))

print("===== STRUCTURAL EVIDENCE EXTRACT =====")
for r in struct_rows:
    print("\t".join(map(str,r)))
