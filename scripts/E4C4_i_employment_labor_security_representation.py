#!/usr/bin/env python3
from pathlib import Path
import csv, hashlib, json

ROOT=Path(__file__).resolve().parents[1]

CONTRACT=ROOT/"data/metadata/E4C4_i_employment_labor_security_representation_contract.json"
LINEAGE=ROOT/"data/metadata/E4C4_frozen_input_lineage.tsv"
PRIOR=ROOT/"data/metadata/E4C4_prior_i_semantic_lineage.tsv"

EXEC=ROOT/"data/metadata/E4C4_execution.txt"
AUDIT=ROOT/"data/metadata/E4C4_i_employment_labor_security_representation_audit.txt"
REGISTRY=ROOT/"data/results/E4C4_i_subcoordinate_registry.tsv"
DECISION=ROOT/"data/results/E4C4_i_current_operating_representation.tsv"
NEXT=ROOT/"data/results/E4C4_post_i_research_sequence.tsv"

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""): h.update(b)
    return h.hexdigest()

def tsv(p):
    with p.open("r",encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f,delimiter="\t"))

c=json.loads(CONTRACT.read_text(encoding="utf-8"))
assert c["phase"]=="E4C4"
assert c["input_policy"]["prior_numeric_I_results_opened"] is False
assert c["scalarization_policy"]["equal_weight_scalar"] is False
assert c["geometry_policy"]["two_I_subcoordinates_allowed"] is True
assert c["hard_boundaries"]["I_scalar_selected"] is False

for r in tsv(LINEAGE):
    p=ROOT/r["artifact"]
    if not p.exists() or sha(p)!=r["sha256"]:
        raise RuntimeError(f"frozen lineage mismatch: {r['artifact']}")

if len(tsv(PRIOR))<2:
    raise RuntimeError("insufficient prior I semantic lineage")

registry_rows=[
    ("PRIMARY","I_FYFT_SHARE","1[WEWKRS == 1]","HIGHER_IS_BETTER","DIMENSIONLESS","CURRENT_OPERATING_PRIMARY"),
    ("PRIMARY","I_SEARCH_SECURITY","-1[WEUEMP in {2,3,4,5,6,7}]","HIGHER_IS_BETTER","DIMENSIONLESS","CURRENT_OPERATING_PRIMARY"),
    ("SENSITIVITY","I_LONG_SEARCH_BURDEN","1[WEUEMP in {6,7}]","LOWER_IS_BETTER_RAW","DIMENSIONLESS","PRESERVED_SENSITIVITY"),
    ("SENSITIVITY","I_ANY_WORK_SHARE","1[WRK_CK == 1]","HIGHER_IS_BETTER","DIMENSIONLESS","PRESERVED_SENSITIVITY"),
]
with REGISTRY.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["role","name","definition","orientation","units","status"])
    w.writerows(registry_rows)

decision_rows=[
    ("I_CONCEPTUAL_TARGET","EMPLOYMENT_AND_LABOR_MARKET_SECURITY"),
    ("I_PRIMARY_SUBCOORDINATE_COUNT","2"),
    ("I_FYFT_SHARE_CURRENT_PRIMARY","1"),
    ("I_SEARCH_SECURITY_CURRENT_PRIMARY","1"),
    ("I_EQUAL_WEIGHT_SCALAR_AUTHORIZED","0"),
    ("I_TARGET_8_CELL_FITTED_WEIGHTS_AUTHORIZED","0"),
    ("I_TARGET_8_CELL_PCA_AUTHORIZED","0"),
    ("I_CROSS_SURVEY_WHITENING_AUTHORIZED","0"),
    ("I_SCALAR_SELECTED","0"),
    ("I_SCALAR_REQUIRED_BEFORE_PROGRESS","0"),
    ("FIVE_CONCEPT_LABELS_REQUIRE_EXACTLY_FIVE_NUMERICAL_COORDINATES","0"),
    ("EVENTUAL_COORDINATE_COUNT_MAY_EXCEED_FIVE","1"),
    ("I_PRIMARY_VALUES_ALREADY_DIMENSIONLESS_SEMANTICALLY","1"),
    ("I_GEOMETRY_METRIC_SCALE_FROZEN","0"),
    ("E4C5_K_D_DIMENSIONLESS_TRANSFORM_PREFLIGHT_AUTHORIZED","1"),
]
with DECISION.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["decision","value"]); w.writerows(decision_rows)

next_rows=[
    ("1","E4C5","K_D_DIMENSIONLESS_TRANSFORM_PREFLIGHT","AUTHORIZED_NEXT"),
    ("2","POST_E4C5","COORDINATE_METRIC_SCALE_READINESS","PENDING"),
    ("3","POST_READINESS","DIMENSIONALITY_GEOMETRY_PREFLIGHT","NOT_AUTHORIZED_YET"),
    ("FUTURE","I_SCALARIZATION","THEORY_WEIGHTS_OR_INDEPENDENT_REFERENCE_MODEL_ONLY","NONBLOCKING"),
]
with NEXT.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["order","phase","scope","status"]); w.writerows(next_rows)

log="\n".join([
"RAW_CPS_DATA_READ=0",
"PRIOR_NUMERIC_I_RESULT_TABLES_OPENED=0",
"NEW_I_ECONOMIC_VALUES_OPENED=0",
"REESTIMATION_PERFORMED=0",
"NEW_REPLICATES_COMPUTED=0",
"FROZEN_PRIOR_I_SEMANTICS_ONLY=1",
"I_CONCEPTUAL_TARGET=EMPLOYMENT_AND_LABOR_MARKET_SECURITY",
"I_PRIMARY_SUBCOORDINATE_COUNT=2",
"I_FYFT_SHARE_CURRENT_PRIMARY=1",
"I_FYFT_SHARE_ORIENTATION=HIGHER_IS_BETTER",
"I_SEARCH_SECURITY_CURRENT_PRIMARY=1",
"I_SEARCH_SECURITY_RAW_BURDEN_SIGN=-1",
"I_SEARCH_SECURITY_ORIENTATION=HIGHER_IS_BETTER",
"I_LONG_SEARCH_BURDEN=PRESERVED_SENSITIVITY",
"I_ANY_WORK_SHARE=PRESERVED_SENSITIVITY",
"I_EQUAL_WEIGHT_SCALAR_AUTHORIZED=0",
"I_TARGET_8_CELL_FITTED_WEIGHTS_AUTHORIZED=0",
"I_TARGET_8_CELL_PCA_AUTHORIZED=0",
"I_CROSS_SURVEY_WHITENING_AUTHORIZED=0",
"I_SCALAR_SELECTED=0",
"I_SCALAR_REQUIRED_BEFORE_PROGRESS=0",
"FIVE_CONCEPT_LABELS_REQUIRE_EXACTLY_FIVE_NUMERICAL_COORDINATES=0",
"EVENTUAL_COORDINATE_COUNT_MAY_EXCEED_FIVE=1",
"I_PRIMARY_VALUES_ALREADY_DIMENSIONLESS_SEMANTICALLY=1",
"I_GEOMETRY_METRIC_SCALE_FROZEN=0",
"OWNER_RENTER_DIRECTION_USED_AS_SELECTION_GATE=0",
"STATISTICAL_SIGNIFICANCE_USED_AS_SELECTION_GATE=0",
"MAGNITUDE_USED_AS_SELECTION_GATE=0",
"GEOMETRY_USED_AS_SELECTION_GATE=0",
"FIVE_COMPONENT_STATE_VECTOR_AUTHORIZED=0",
"FIVE_COMPONENT_NORMALIZATION_AUTHORIZED=0",
"GEOMETRY_AUTHORIZED=0",
"DIMENSIONALITY_TEST_AUTHORIZED=0",
"REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
"FINAL_SCALAR_AUTHORIZED=0",
"E4C4_I_EMPLOYMENT_LABOR_SECURITY_REPRESENTATION=PASS",
"E4C5_K_D_DIMENSIONLESS_TRANSFORM_PREFLIGHT_AUTHORIZED=1",
])+"\n"

EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
