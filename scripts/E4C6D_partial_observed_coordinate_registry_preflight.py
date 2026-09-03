#!/usr/bin/env python3
from pathlib import Path
import csv, json

ROOT=Path(__file__).resolve().parents[1]

H_SRC=ROOT/"data/results/E4C3D_h_access_inference_summary.tsv"
KD_SRC=ROOT/"data/results/E4C5I_k_d_component_inference_registry.tsv"
I_SRC=ROOT/"data/results/E4A2D_2022_cps_i_cohort_inference.tsv"
H_REPR=ROOT/"data/results/E4C3E_h_current_operating_representation.tsv"
I_REPR=ROOT/"data/results/E4C4_i_current_operating_representation.tsv"
I_SUB=ROOT/"data/results/E4C4_i_subcoordinate_registry.tsv"

EXEC=ROOT/"data/metadata/E4C6D_execution.txt"
AUDIT=ROOT/"data/metadata/E4C6D_partial_observed_coordinate_registry_preflight_audit.txt"
SOURCE=ROOT/"data/results/E4C6D_coordinate_source_selection_contract.tsv"
SCHEMA=ROOT/"data/results/E4C6D_partial_observed_coordinate_registry_schema.tsv"
PLAN=ROOT/"data/results/E4C6D_partial_registry_execution_plan.tsv"
DECISION=ROOT/"data/results/E4C6D_partial_observed_coordinate_registry_preflight_decision.tsv"

def header(path):
    # Intentionally reads exactly one line only.
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        return f.readline().rstrip("\r\n").split("\t")

expected_headers={
    H_SRC:["entity_type","role","estimand","age_band","entity","estimate","se","ci95_low","ci95_high"],
    KD_SRC:["inference_role","year","component","age_band","tenure","contrast","statistic_id","point_state",
            "imputation_variance_state","sampling_replicate_mean_state","sampling_variance_state",
            "combined_variance_state","combined_se_state","implicate_count","replicate_count","frozen_source_phase"],
    I_SRC:["year","age_band","tenure","estimand","role","state_sign","unweighted_n","point_estimate",
           "replicate_variance","replicate_se","replicate_count"],
}
for p,e in expected_headers.items():
    got=header(p)
    if got!=e:
        raise RuntimeError(f"header mismatch {p}: {got}")

def d2(path):
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        rows=list(csv.reader(f,delimiter="\t"))
    if not rows or rows[0][:2]!=["decision","value"]:
        raise RuntimeError(f"unexpected structural decision schema {path}")
    return {r[0]:r[1] for r in rows[1:] if len(r)>=2}

h=d2(H_REPR)
i=d2(I_REPR)
with I_SUB.open("r",encoding="utf-8-sig",newline="") as f:
    sub=list(csv.DictReader(f,delimiter="\t"))

assert h.get("H_ACCESS_SPACE_SUBCOORDINATE_IDENTIFIED")=="1"
assert h.get("H_ACCESS_SPACE_ESTIMAND")=="H_ACCESS_SPACE_ROOMS_PER_PERSON"
assert h.get("H_ACCESS_SPACE_CURRENT_OPERATING_NUMERICAL_SUBCOORDINATE")=="1"
assert h.get("H_FULL_STATE_COMPLETE")=="0"

assert i.get("I_PRIMARY_SUBCOORDINATE_COUNT")=="2"
assert i.get("I_FYFT_SHARE_CURRENT_PRIMARY")=="1"
assert i.get("I_SEARCH_SECURITY_CURRENT_PRIMARY")=="1"
assert i.get("I_SCALAR_SELECTED")=="0"

prim=[r for r in sub if r.get("role")=="PRIMARY"]
sens=[r for r in sub if r.get("role")=="SENSITIVITY"]
assert {r["name"] for r in prim}=={"I_FYFT_SHARE","I_SEARCH_SECURITY"}
assert len(sens)==2

source_rows=[
    ["H","H_ACCESS_SPACE_ROOMS_PER_PERSON",str(H_SRC.relative_to(ROOT)),
     "role=PRIMARY;estimand=H_ACCESS_SPACE_ROOMS_PER_PERSON;age=frozen4;entity=OWNER|RENTER",
     "estimate","se","IDENTITY","DIMENSIONLESS","HIGHER_IS_BETTER",
     "PRIMARY_OBSERVED_SUBCOORDINATE_NOT_FULL_H_STATE"],
    ["K","K_FIN_MEAN_TRANSFORMED",str(KD_SRC.relative_to(ROOT)),
     "inference_role=CELL;component=K;statistic_id=K_FIN_MEAN;age=frozen4;tenure=OWNER|RENTER",
     "point_state","combined_se_state","ALREADY_FROZEN_E4C5G_LOG1P_REFERENCE_TRANSFORM",
     "DIMENSIONLESS","HIGHER_IS_BETTER","FULL_COMPONENT_SCALAR_COORDINATE"],
    ["D","D_PIRTOTAL_MEAN_STATE_TRANSFORMED",str(KD_SRC.relative_to(ROOT)),
     "inference_role=CELL;component=D;statistic_id=D_PIRTOTAL_MEAN;age=frozen4;tenure=OWNER|RENTER",
     "point_state","combined_se_state","ALREADY_FROZEN_SIGN_NORMALIZATION",
     "DIMENSIONLESS","HIGHER_IS_BETTER","FULL_COMPONENT_SCALAR_COORDINATE"],
    ["I","I_FYFT_SHARE",str(I_SRC.relative_to(ROOT)),
     "role=PRIMARY;estimand=I_FYFT_SHARE;age=frozen4;tenure=OWNER|RENTER;state_sign=+1",
     "point_estimate","replicate_se","MULTIPLY_BY_FROZEN_STATE_SIGN",
     "DIMENSIONLESS","HIGHER_IS_BETTER","PRIMARY_OBSERVED_SUBCOORDINATE"],
    ["I","I_SEARCH_SECURITY",str(I_SRC.relative_to(ROOT)),
     "role=PRIMARY;estimand=I_SEARCH_BURDEN_SHARE;age=frozen4;tenure=OWNER|RENTER;state_sign=-1",
     "point_estimate","replicate_se","MULTIPLY_BY_FROZEN_STATE_SIGN",
     "DIMENSIONLESS","HIGHER_IS_BETTER","PRIMARY_OBSERVED_SUBCOORDINATE"],
]

with SOURCE.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["component","coordinate_id","source_path","frozen_selector","point_field","se_field",
                "state_transform","units","orientation","coordinate_scope"])
    w.writerows(source_rows)

schema=[
    ["year","INTEGER","2022 only"],
    ["age_band","CATEGORICAL","25-34|35-44|45-54|55-64"],
    ["tenure","CATEGORICAL","OWNER|RENTER"],
    ["component","CATEGORICAL","H|K|D|I"],
    ["coordinate_id","STRING","one of five frozen coordinate ids"],
    ["coordinate_scope","CATEGORICAL","full component scalar or observed subcoordinate"],
    ["point_state","FLOAT","state-oriented source point; no metric rescaling"],
    ["se_state","FLOAT","source-standard-error in same coordinate units"],
    ["units","STRING","DIMENSIONLESS"],
    ["orientation","STRING","HIGHER_IS_BETTER"],
    ["source_survey","STRING","ACS2022|SCF2022|CPS_ASEC_2022"],
    ["source_phase","STRING","E4C3D|E4C5I|E4A2D+E4C4"],
]
with SCHEMA.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["field","type","contract"])
    w.writerows(schema)

plan=[
    ["H_ACCESS_SPACE_ROOMS_PER_PERSON","H",8,"ACS2022","IDENTITY","E4C3D"],
    ["K_FIN_MEAN_TRANSFORMED","K",8,"SCF2022","REUSE_FROZEN_TRANSFORMED_STATE","E4C5I"],
    ["D_PIRTOTAL_MEAN_STATE_TRANSFORMED","D",8,"SCF2022","REUSE_FROZEN_TRANSFORMED_STATE","E4C5I"],
    ["I_FYFT_SHARE","I",8,"CPS_ASEC_2022","FROZEN_STATE_SIGN_PLUS1","E4A2D+E4C4"],
    ["I_SEARCH_SECURITY","I",8,"CPS_ASEC_2022","FROZEN_STATE_SIGN_MINUS1","E4A2D+E4C4"],
]
with PLAN.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["coordinate_id","component","expected_cell_rows","source_survey","execution_transform_policy","source_phase"])
    w.writerows(plan)

dec=[
    ["EXACT_VALUE_SOURCE_COUNT","3"],
    ["SOURCE_HEADER_COUNT","3"],
    ["SOURCE_HEADERS_VALIDATED","1"],
    ["PARTIAL_OBSERVED_COORDINATE_COUNT","5"],
    ["EXPECTED_CELL_ROWS_PER_COORDINATE","8"],
    ["EXPECTED_PARTIAL_REGISTRY_ROW_COUNT","40"],
    ["NUMERICALLY_REPRESENTED_CONCEPT_COUNT","4"],
    ["C_INCLUDED_IN_PARTIAL_REGISTRY","0"],
    ["H_ACCESS_PROMOTED_TO_FULL_H_STATE","0"],
    ["I_PRIMARY_COORDINATE_COUNT","2"],
    ["I_SENSITIVITY_ROWS_INCLUDED","0"],
    ["I_SCALAR_FORCED","0"],
    ["PARTIAL_REGISTRY_IS_FULL_CHKDI_STATE_VECTOR","0"],
    ["PARTIAL_REGISTRY_IS_FINAL_MODEL","0"],
    ["SOURCE_STANDARD_ERRORS_REUSED","1"],
    ["CROSS_SURVEY_INDEPENDENCE_ASSUMED","0"],
    ["CROSS_COORDINATE_COVARIANCE_COMPUTED","0"],
    ["CROSS_COORDINATE_METRIC_SCALE_FROZEN","0"],
    ["GEOMETRY_AUTHORIZED","0"],
    ["E4C6E_PARTIAL_OBSERVED_COORDINATE_REGISTRY_EXECUTION_AUTHORIZED","1"],
]
with DECISION.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["decision","value"])
    w.writerows(dec)

log="\n".join([
    "E4C6C_REUSED_AS_CANONICAL_DISPOSITION=1",
    "EXACT_VALUE_SOURCE_COUNT=3",
    "SOURCE_HEADER_COUNT=3",
    "SOURCE_HEADERS_VALIDATED=1",
    "SOURCE_NUMERIC_ROWS_OPENED=0",
    "ECONOMIC_RESULT_NUMERIC_ROWS_OPENED=0",
    "NEW_ECONOMIC_VALUES_OPENED=0",
    "PARTIAL_OBSERVED_COORDINATE_COUNT=5",
    "EXPECTED_CELL_ROWS_PER_COORDINATE=8",
    "EXPECTED_PARTIAL_REGISTRY_ROW_COUNT=40",
    "NUMERICALLY_REPRESENTED_CONCEPT_COUNT=4",
    "C_INCLUDED_IN_PARTIAL_REGISTRY=0",
    "H_ACCESS_PROMOTED_TO_FULL_H_STATE=0",
    "I_PRIMARY_COORDINATE_COUNT=2",
    "I_SENSITIVITY_ROWS_INCLUDED=0",
    "I_SCALAR_FORCED=0",
    "PARTIAL_REGISTRY_IS_FULL_CHKDI_STATE_VECTOR=0",
    "PARTIAL_REGISTRY_IS_FINAL_MODEL=0",
    "ALL_FIVE_COORDINATES_DIMENSIONLESS_BY_FROZEN_SEMANTICS=1",
    "ALL_FIVE_COORDINATES_HIGHER_IS_BETTER_BY_FROZEN_SEMANTICS=1",
    "SOURCE_STANDARD_ERRORS_REUSED_IN_EXECUTION_PLAN=1",
    "NEW_UNCERTAINTY_ESTIMATOR_INTRODUCED=0",
    "CROSS_SURVEY_INDEPENDENCE_ASSUMED=0",
    "CROSS_COORDINATE_COVARIANCE_COMPUTED=0",
    "CROSS_COORDINATE_METRIC_SCALE_FROZEN=0",
    "SIGN_USED_AS_PREFLIGHT_GATE=0",
    "MAGNITUDE_USED_AS_PREFLIGHT_GATE=0",
    "STATISTICAL_SIGNIFICANCE_USED_AS_PREFLIGHT_GATE=0",
    "OWNER_RENTER_DIRECTION_USED_AS_PREFLIGHT_GATE=0",
    "COMPONENT_DEFINITION_MUTATED=0",
    "TRANSFORM_MUTATED=0",
    "NEW_ESTIMATOR_INTRODUCED=0",
    "NEW_INFERENCE_COMPUTED=0",
    "GEOMETRY_READY=0",
    "GEOMETRY_AUTHORIZED=0",
    "DIMENSIONALITY_TEST_AUTHORIZED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "E4C6D_PARTIAL_OBSERVED_COORDINATE_REGISTRY_PREFLIGHT=PASS",
    "E4C6E_PARTIAL_OBSERVED_COORDINATE_REGISTRY_EXECUTION_AUTHORIZED=1",
])+"\n"

EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
print("===== FROZEN COORDINATE SOURCE SELECTION =====")
for r in source_rows:
    print("\t".join(map(str,r)))
print("===== EXECUTION PLAN =====")
for r in plan:
    print("\t".join(map(str,r)))
