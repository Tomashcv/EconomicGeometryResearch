#!/usr/bin/env python3
from pathlib import Path
import csv, json
from fractions import Fraction

ROOT=Path(__file__).resolve().parents[1]

E6_CONTRACT=ROOT/"data/metadata/E4C6E_partial_observed_coordinate_registry_execution_contract.json"
E6_EXEC=ROOT/"data/metadata/E4C6E_execution.txt"
E6_DEC=ROOT/"data/results/E4C6E_partial_observed_coordinate_registry_decision.tsv"
CONTRACT=ROOT/"data/metadata/E4C7_cross_coordinate_metric_scale_architecture_contract.json"

EXEC=ROOT/"data/metadata/E4C7_execution.txt"
AUDIT=ROOT/"data/metadata/E4C7_cross_coordinate_metric_scale_architecture_audit.txt"
CAND=ROOT/"data/results/E4C7_metric_candidate_registry.tsv"
MATRIX=ROOT/"data/results/E4C7_metric_diagonal_coefficients.tsv"
PROHIB=ROOT/"data/results/E4C7_metric_scale_prohibitions.tsv"
DECISION=ROOT/"data/results/E4C7_metric_scale_architecture_decision.tsv"

# Structural reads only. The frozen numeric registry content is intentionally not opened here.
e6c=json.loads(E6_CONTRACT.read_text(encoding="utf-8"))
c=json.loads(CONTRACT.read_text(encoding="utf-8"))

expected_order=[
    "H_ACCESS_SPACE_ROOMS_PER_PERSON",
    "K_FIN_MEAN_TRANSFORMED",
    "D_PIRTOTAL_MEAN_STATE_TRANSFORMED",
    "I_FYFT_SHARE",
    "I_SEARCH_SECURITY",
]
assert e6c["frozen_coordinate_order"]==expected_order
assert c["coordinate_order"]==expected_order

e6_lines=set(E6_EXEC.read_text(encoding="utf-8").splitlines())
for line in [
    "PARTIAL_OBSERVED_COORDINATE_COUNT=5",
    "PARTIAL_OBSERVED_COORDINATE_REGISTRY_ROW_COUNT=40",
    "NUMERICALLY_REPRESENTED_CONCEPT_COUNT=4",
    "C_INCLUDED_IN_PARTIAL_REGISTRY=0",
    "H_ACCESS_PROMOTED_TO_FULL_H_STATE=0",
    "I_PRIMARY_COORDINATE_COUNT=2",
    "I_SENSITIVITY_ROWS_INCLUDED=0",
    "I_SCALAR_FORCED=0",
    "PARTIAL_REGISTRY_IS_FULL_CHKDI_STATE_VECTOR=0",
    "CROSS_SURVEY_INDEPENDENCE_ASSUMED=0",
    "CROSS_COORDINATE_COVARIANCE_COMPUTED=0",
    "CROSS_COORDINATE_METRIC_SCALE_FROZEN=0",
    "GEOMETRY_AUTHORIZED=0",
    "E4C7_CROSS_COORDINATE_METRIC_SCALE_ARCHITECTURE_PREFLIGHT_AUTHORIZED=1",
]:
    assert line in e6_lines, line

metrics=[
    {
        "metric_id":"M1_NATURAL_TRANSFORM_UNIT_IDENTITY",
        "role":"CANONICAL_FOR_PARTIAL_PANEL",
        "description":"one metric unit per one unit of each frozen transformed dimensionless coordinate",
        "downstream_required":"YES",
    },
    {
        "metric_id":"M2_CONCEPT_BALANCED_I_SPLIT",
        "role":"MANDATORY_ROBUSTNESS",
        "description":"same as M1 except total diagonal mass of the two-coordinate I conceptual block is one",
        "downstream_required":"YES",
    },
]

with CAND.open("w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["metric_id","role","description","downstream_required"],
                     delimiter="\t",lineterminator="\n")
    w.writeheader()
    w.writerows(metrics)

weights={
    "M1_NATURAL_TRANSFORM_UNIT_IDENTITY":{
        "H_ACCESS_SPACE_ROOMS_PER_PERSON":"1",
        "K_FIN_MEAN_TRANSFORMED":"1",
        "D_PIRTOTAL_MEAN_STATE_TRANSFORMED":"1",
        "I_FYFT_SHARE":"1",
        "I_SEARCH_SECURITY":"1",
    },
    "M2_CONCEPT_BALANCED_I_SPLIT":{
        "H_ACCESS_SPACE_ROOMS_PER_PERSON":"1",
        "K_FIN_MEAN_TRANSFORMED":"1",
        "D_PIRTOTAL_MEAN_STATE_TRANSFORMED":"1",
        "I_FYFT_SHARE":"1/2",
        "I_SEARCH_SECURITY":"1/2",
    },
}

matrix_rows=[]
for metric_id in [m["metric_id"] for m in metrics]:
    for coord in expected_order:
        raw=weights[metric_id][coord]
        q=Fraction(raw)
        assert q>0
        matrix_rows.append([
            metric_id,coord,raw,str(q.numerator),str(q.denominator),
            "DIAGONAL","NO_OFF_DIAGONAL_COUPLING"
        ])

with MATRIX.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow([
        "metric_id","coordinate_id","G_diagonal_exact",
        "numerator","denominator","matrix_role","off_diagonal_policy"
    ])
    w.writerows(matrix_rows)

prohibited=c["prohibited_scale_methods"]
with PROHIB.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["method","status","reason_class"])
    for x in prohibited:
        if "standard_error" in x:
            reason="SAMPLING_PRECISION_IS_NOT_ECONOMIC_METRIC_SCALE"
        elif x in {"PCA","whitening"}:
            reason="DATA_FIT_ROTATION_OR_SCALE_PROHIBITED"
        elif "cohort_specific" in x:
            reason="SAME_FORMULA_ACROSS_COHORTS_REQUIRED"
        else:
            reason="IN_SAMPLE_2022_DATA_FIT_SCALE_PROHIBITED"
        w.writerow([x,"PROHIBITED",reason])

decision_rows=[
    ["REGISTRY_VALUES_ALREADY_OPENED_BEFORE_E4C7","1"],
    ["E4C7_REGISTRY_NUMERIC_ROWS_READ","0"],
    ["OUTCOME_SIGN_USED_TO_CHOOSE_METRIC","0"],
    ["OUTCOME_MAGNITUDE_USED_TO_CHOOSE_METRIC","0"],
    ["OUTCOME_DISPERSION_USED_TO_CHOOSE_METRIC","0"],
    ["STATISTICAL_SIGNIFICANCE_USED_TO_CHOOSE_METRIC","0"],
    ["SOURCE_STANDARD_ERRORS_USED_TO_CHOOSE_METRIC","0"],
    ["CANONICAL_METRIC_ID","M1_NATURAL_TRANSFORM_UNIT_IDENTITY"],
    ["MANDATORY_SENSITIVITY_METRIC_ID","M2_CONCEPT_BALANCED_I_SPLIT"],
    ["METRIC_CANDIDATE_COUNT","2"],
    ["METRIC_MATRIX_DIMENSION","5"],
    ["METRIC_OFF_DIAGONAL_TERMS_AUTHORIZED","0"],
    ["METRIC_DIAGONALITY_IMPLIES_STATISTICAL_INDEPENDENCE","0"],
    ["DOWNSTREAM_MUST_REPORT_BOTH_METRICS","1"],
    ["BEST_LOOKING_METRIC_SELECTION_AUTHORIZED","0"],
    ["ABSOLUTE_ORIGIN_INTERPRETATION_AUTHORIZED","0"],
    ["C_INCLUDED_IN_METRIC","0"],
    ["H_ACCESS_PROMOTED_TO_FULL_H_STATE","0"],
    ["I_PRIMARY_AXES_REMAIN_SEPARATE","1"],
    ["I_SCALAR_CREATED","0"],
    ["PARTIAL_PANEL_IS_FULL_CHKDI_STATE_VECTOR","0"],
    ["METRIC_WEIGHTS_ARE_WELFARE_WEIGHTS","0"],
    ["CROSS_SURVEY_INDEPENDENCE_ASSUMED","0"],
    ["CROSS_COORDINATE_COVARIANCE_COMPUTED","0"],
    ["CROSS_COORDINATE_METRIC_SCALE_FROZEN","1"],
    ["GEOMETRY_AUTHORIZED","0"],
    ["E4C8_CROSS_SURVEY_DEPENDENCE_AND_COVARIANCE_FEASIBILITY_PREFLIGHT_AUTHORIZED","1"],
]
with DECISION.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["decision","value"])
    w.writerows(decision_rows)

log="\n".join([
    "E4C7_R0_STATIC_VALIDATOR_SELF_REFERENCE_REPAIR=1",
    "PRIOR_E4C7_UNCOMMITTED_ATTEMPT_COMMITTED=0",
    "REPO_HISTORY_MUTATED_BY_FAILED_ATTEMPT=0",
    "E4C6E_R2_REUSED_AS_CANONICAL_PARTIAL_REGISTRY=1",
    "REGISTRY_VALUES_ALREADY_OPENED_BEFORE_E4C7=1",
    "E4C7_REGISTRY_NUMERIC_ROWS_READ=0",
    "E4C7_REGISTRY_FILE_CONTENT_OPENED=0",
    "E4C7_REGISTRY_HASH_VERIFIED_EXTERNALLY_BY_WRAPPER=1",
    "POST_VALUE_OPEN_STRUCTURAL_METRIC_POLICY=1",
    "OUTCOME_SIGN_USED_TO_CHOOSE_METRIC=0",
    "OUTCOME_MAGNITUDE_USED_TO_CHOOSE_METRIC=0",
    "OUTCOME_DISPERSION_USED_TO_CHOOSE_METRIC=0",
    "STATISTICAL_SIGNIFICANCE_USED_TO_CHOOSE_METRIC=0",
    "OWNER_RENTER_DIRECTION_USED_TO_CHOOSE_METRIC=0",
    "SOURCE_STANDARD_ERRORS_USED_TO_CHOOSE_METRIC=0",
    "CANONICAL_METRIC_ID=M1_NATURAL_TRANSFORM_UNIT_IDENTITY",
    "MANDATORY_SENSITIVITY_METRIC_ID=M2_CONCEPT_BALANCED_I_SPLIT",
    "METRIC_CANDIDATE_COUNT=2",
    "METRIC_MATRIX_DIMENSION=5",
    "M1_DIAGONAL=1,1,1,1,1",
    "M2_DIAGONAL=1,1,1,1/2,1/2",
    "METRIC_OFF_DIAGONAL_TERMS_AUTHORIZED=0",
    "METRIC_DIAGONALITY_IMPLIES_STATISTICAL_INDEPENDENCE=0",
    "DOWNSTREAM_MUST_REPORT_BOTH_METRICS=1",
    "METRIC_ROBUST_CLAIM_REQUIRES_SAME_QUALITATIVE_CONCLUSION_UNDER_BOTH=1",
    "BEST_LOOKING_METRIC_SELECTION_AUTHORIZED=0",
    "ABSOLUTE_ORIGIN_INTERPRETATION_AUTHORIZED=0",
    "METRIC_APPLIES_TO_DIFFERENCE_VECTORS=1",
    "C_INCLUDED_IN_METRIC=0",
    "H_ACCESS_PROMOTED_TO_FULL_H_STATE=0",
    "I_PRIMARY_AXES_REMAIN_SEPARATE=1",
    "I_SCALAR_CREATED=0",
    "PARTIAL_PANEL_IS_FULL_CHKDI_STATE_VECTOR=0",
    "METRIC_WEIGHTS_ARE_WELFARE_WEIGHTS=0",
    "IN_SAMPLE_2022_SD_SCALE_AUTHORIZED=0",
    "IN_SAMPLE_2022_RANGE_SCALE_AUTHORIZED=0",
    "IN_SAMPLE_2022_RANK_SCALE_AUTHORIZED=0",
    "PCA_WHITENING_AUTHORIZED=0",
    "INVERSE_SE_METRIC_WEIGHTING_AUTHORIZED=0",
    "COHORT_SPECIFIC_SCALE_PARAMETERS_AUTHORIZED=0",
    "CROSS_SURVEY_INDEPENDENCE_ASSUMED=0",
    "CROSS_COORDINATE_COVARIANCE_COMPUTED=0",
    "CROSS_COORDINATE_METRIC_SCALE_FROZEN=1",
    "GEOMETRY_READY=0",
    "GEOMETRY_AUTHORIZED=0",
    "DIMENSIONALITY_TEST_AUTHORIZED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "E4C7_CROSS_COORDINATE_METRIC_SCALE_ARCHITECTURE_PREFLIGHT=PASS",
    "E4C8_CROSS_SURVEY_DEPENDENCE_AND_COVARIANCE_FEASIBILITY_PREFLIGHT_AUTHORIZED=1",
])+"\n"

EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")

print(log,end="")
print("===== METRIC CANDIDATES =====")
print(CAND.read_text(encoding="utf-8"),end="")
print("===== METRIC DIAGONAL COEFFICIENTS =====")
print(MATRIX.read_text(encoding="utf-8"),end="")
print("===== PROHIBITED SCALE METHODS =====")
print(PROHIB.read_text(encoding="utf-8"),end="")
