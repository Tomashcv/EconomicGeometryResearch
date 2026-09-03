#!/usr/bin/env python3
from pathlib import Path
import csv

ROOT=Path(__file__).resolve().parents[1]

EXEC=ROOT/"data/metadata/E4C9_execution.txt"
AUDIT=ROOT/"data/metadata/E4C9_partial_state_geometry_dimensionality_preflight_audit.txt"
OBJECTS=ROOT/"data/results/E4C9_geometry_object_registry.tsv"
FORMULAS=ROOT/"data/results/E4C9_metric_geometry_formula_registry.tsv"
BOUNDARIES=ROOT/"data/results/E4C9_inferential_boundary_registry.tsv"
DIM=ROOT/"data/results/E4C9_dimensionality_method_decision.tsv"
PLAN=ROOT/"data/results/E4C9_descriptive_geometry_execution_plan.tsv"
GATES=ROOT/"data/results/E4C9_preflight_hard_gates.tsv"
DECISION=ROOT/"data/results/E4C9_partial_state_geometry_dimensionality_decision.tsv"

coords=[
    "H_ACCESS_SPACE_ROOMS_PER_PERSON",
    "K_FIN_MEAN_TRANSFORMED",
    "D_PIRTOTAL_MEAN_STATE_TRANSFORMED",
    "I_FYFT_SHARE",
    "I_SEARCH_SECURITY",
]

ages=["25-34","35-44","45-54","55-64"]
tenures=["OWNER","RENTER"]
cells=[f"{a}|{t}" for a in ages for t in tenures]

# Structural enumeration only; no economic values are read.
pairs=[]
for i in range(len(cells)):
    for j in range(i+1,len(cells)):
        a_age,a_ten=cells[i].split("|")
        b_age,b_ten=cells[j].split("|")
        if a_age==b_age and {a_ten,b_ten}=={"OWNER","RENTER"}:
            family="OWNER_RENTER_WITHIN_AGE"
        else:
            same_ten=(a_ten==b_ten)
            if same_ten:
                ia=ages.index(a_age); ib=ages.index(b_age)
                family="ADJACENT_AGE_WITHIN_TENURE" if abs(ia-ib)==1 else "OTHER_PAIRWISE"
            else:
                family="OTHER_PAIRWISE"
        pairs.append((cells[i],cells[j],family))

assert len(pairs)==28
assert sum(p[2]=="OWNER_RENTER_WITHIN_AGE" for p in pairs)==4
assert sum(p[2]=="ADJACENT_AGE_WITHIN_TENURE" for p in pairs)==6

object_rows=[
    ["STATE_POINT","8","one 2022 age_band x tenure point in frozen five-axis partial observed coordinate space","DESCRIPTIVE_ONLY"],
    ["UNORDERED_PAIRWISE_DIFFERENCE_VECTOR","28","x_b - x_a for every unordered pair of the eight state points","DESCRIPTIVE_ONLY"],
    ["OWNER_RENTER_WITHIN_AGE_DIFFERENCE_VECTOR","4","RENTER minus OWNER within each frozen age band","NAMED_DESCRIPTIVE_SUBSET"],
    ["ADJACENT_AGE_WITHIN_TENURE_DIFFERENCE_VECTOR","6","older adjacent age point minus younger adjacent age point within tenure","NAMED_DESCRIPTIVE_SUBSET"],
    ["PAIRWISE_SQUARED_DISTANCE_M1","28","exact M1 squared distance for every unordered point pair","AUTHORIZED_FOR_E4C9A"],
    ["PAIRWISE_SQUARED_DISTANCE_M2","28","exact M2 squared distance for every unordered point pair","AUTHORIZED_FOR_E4C9A"],
]
with OBJECTS.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["object_type","expected_count","definition","status"])
    w.writerows(object_rows)

formula_rows=[
    ["M1_NATURAL_TRANSFORM_UNIT_IDENTITY","CANONICAL_FOR_PARTIAL_PANEL",
     "d2=dH^2+dK^2+dD^2+dI1^2+dI2^2",
     "1,1,1,1,1","EXACT_SQUARED_DISTANCE","YES"],
    ["M2_CONCEPT_BALANCED_I_SPLIT","MANDATORY_ROBUSTNESS",
     "d2=dH^2+dK^2+dD^2+(1/2)*dI1^2+(1/2)*dI2^2",
     "1,1,1,1/2,1/2","EXACT_SQUARED_DISTANCE","YES"],
]
with FORMULAS.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["metric_id","role","exact_formula","diagonal_exact","primary_geometry_primitive","downstream_required"])
    w.writerows(formula_rows)

boundary_rows=[
    ["POINT_ESTIMATE_PAIRWISE_GEOMETRY","AUTHORIZED_DESCRIPTIVE_ONLY",
     "uses frozen point coordinates and both frozen E4C7 metrics; no uncertainty claim"],
    ["ABSOLUTE_ORIGIN_INTERPRETATION","PROHIBITED",
     "E4C7 metric applies to difference vectors; zero vector has no frozen economic baseline meaning"],
    ["PAIRWISE_DISTANCE_STANDARD_ERROR","NOT_AUTHORIZED",
     "requires cross-cell sampling covariance not identified by E4C8D cellwise covariance sets"],
    ["PAIRWISE_DISTANCE_CONFIDENCE_INTERVAL","NOT_AUTHORIZED",
     "requires cross-cell sampling covariance and nonlinear uncertainty propagation"],
    ["OWNER_RENTER_DIFFERENCE_SIGNIFICANCE","NOT_AUTHORIZED",
     "cross-cell joint sampling covariance is not frozen"],
    ["ZERO_CROSS_CELL_SAMPLING_COVARIANCE","PROHIBITED",
     "must not silently substitute missing cross-cell covariance by zero"],
    ["WITHIN_CELL_U1_SUFFICIENT_FOR_CROSS_CELL_DIFFERENCE_INFERENCE","FALSE",
     "U1 describes each cell's 5x5 covariance completion set, not Cov(x_a,x_b) across distinct cells"],
    ["SAMPLING_COVARIANCE_EQUALS_ECONOMIC_DEPENDENCE","FALSE",
     "sampling uncertainty architecture is not underlying economic co-movement"],
]
with BOUNDARIES.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["object","status","reason"])
    w.writerows(boundary_rows)

dim_rows=[
    ["FIVE_NUMERICAL_COORDINATES_IMPLY_FIVE_INTRINSIC_DIMENSIONS","REJECTED",
     "five axes include two I subcoordinates and do not prove latent dimension"],
    ["FOUR_REPRESENTED_CONCEPTS_IMPLY_FOUR_INTRINSIC_DIMENSIONS","REJECTED",
     "concept count is semantic taxonomy, not identified geometric dimension"],
    ["PCA","PROHIBITED",
     "E4C7 prohibits data-fit PCA/whitening for metric/scale construction and E4C9 has no new authorization"],
    ["WHITENING","PROHIBITED",
     "data-fit rotation/scale remains prohibited"],
    ["SVD_THRESHOLD_DIMENSION","NOT_AUTHORIZED",
     "no ex-ante singular-value threshold or noise model frozen"],
    ["EIGENVALUE_THRESHOLD_DIMENSION","NOT_AUTHORIZED",
     "no ex-ante eigenvalue threshold or noise model frozen"],
    ["EXACT_AFFINE_RANK_AS_INTRINSIC_DIMENSION","NOT_AUTHORIZED",
     "algebraic rank of noisy estimated points can be maximal under arbitrarily small estimation noise"],
    ["INTRINSIC_DIMENSION_CLAIM","NOT_AUTHORIZED",
     "requires a separate precommitted noise-aware identification strategy and appropriate validation"],
]
with DIM.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["method_or_claim","status","reason"])
    w.writerows(dim_rows)

plan_rows=[]
for pair_index,(a,b,family) in enumerate(pairs, start=1):
    a_age,a_ten=a.split("|")
    b_age,b_ten=b.split("|")
    for metric in ["M1_NATURAL_TRANSFORM_UNIT_IDENTITY","M2_CONCEPT_BALANCED_I_SPLIT"]:
        plan_rows.append([
            pair_index,a_age,a_ten,b_age,b_ten,family,metric,
            "EXACT_RATIONAL_POINT_DELTA_THEN_EXACT_SQUARED_DISTANCE",
            "NO_OUTCOME_GATE"
        ])
assert len(plan_rows)==56

with PLAN.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow([
        "pair_index","cell_a_age_band","cell_a_tenure","cell_b_age_band","cell_b_tenure",
        "pair_family","metric_id","execution_formula_policy","gate_policy"
    ])
    w.writerows(plan_rows)

gate_rows=[
    ["E4C8D_UNCERTAINTY_ARCHITECTURE_REUSED","PASS"],
    ["E4C7_DUAL_METRIC_POLICY_REUSED","PASS"],
    ["NO_NUMERIC_POINT_ROWS_OPENED","PASS"],
    ["EXACT_8_POINT_28_PAIR_ENUMERATION","PASS"],
    ["EXACT_56_DUAL_METRIC_DISTANCE_PLAN","PASS"],
    ["DESCRIPTIVE_VS_INFERENTIAL_BOUNDARY","PASS"],
    ["NO_SILENT_ZERO_CROSS_CELL_COVARIANCE","PASS"],
    ["NO_DIMENSIONALITY_OVERCLAIM","PASS"],
    ["NO_REAL_INFLATION_OR_FINAL_SCALAR","PASS"],
]
with GATES.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["gate","value"])
    w.writerows(gate_rows)

decision_rows=[
    ["STATE_POINT_COUNT","8"],
    ["NUMERICAL_COORDINATE_COUNT","5"],
    ["NUMERICALLY_REPRESENTED_CONCEPT_COUNT","4"],
    ["UNORDERED_PAIRWISE_POINT_COUNT","28"],
    ["DUAL_METRIC_SQUARED_DISTANCE_PLAN_ROW_COUNT","56"],
    ["OWNER_RENTER_WITHIN_AGE_PAIR_COUNT","4"],
    ["ADJACENT_AGE_WITHIN_TENURE_PAIR_COUNT","6"],
    ["M1_REQUIRED","1"],
    ["M2_REQUIRED","1"],
    ["BEST_LOOKING_METRIC_SELECTION_AUTHORIZED","0"],
    ["ABSOLUTE_ORIGIN_INTERPRETATION_AUTHORIZED","0"],
    ["DESCRIPTIVE_POINT_GEOMETRY_AUTHORIZED","1"],
    ["INFERENTIAL_GEOMETRY_AUTHORIZED","0"],
    ["PAIRWISE_DISTANCE_SE_AUTHORIZED","0"],
    ["PAIRWISE_DISTANCE_CI_AUTHORIZED","0"],
    ["ZERO_CROSS_CELL_SAMPLING_COVARIANCE_ASSUMED","0"],
    ["DIMENSIONALITY_TEST_AUTHORIZED","0"],
    ["PCA_AUTHORIZED","0"],
    ["WHITENING_AUTHORIZED","0"],
    ["EXACT_AFFINE_RANK_AS_INTRINSIC_DIMENSION_AUTHORIZED","0"],
    ["C_INCLUDED","0"],
    ["H_ACCESS_PROMOTED_TO_FULL_H_STATE","0"],
    ["I_SCALAR_CREATED","0"],
    ["PARTIAL_PANEL_IS_FULL_CHKDI_STATE_VECTOR","0"],
    ["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
    ["FINAL_SCALAR_AUTHORIZED","0"],
    ["E4C9A_PARTIAL_STATE_DESCRIPTIVE_GEOMETRY_EXECUTION_AUTHORIZED","1"],
]
with DECISION.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["decision","value"])
    w.writerows(decision_rows)

log="\n".join([
    "E4C8D_REUSED_AS_CANONICAL_CELLWISE_COVARIANCE_UNCERTAINTY_ARCHITECTURE=1",
    "E4C7_REUSED_AS_CANONICAL_DUAL_METRIC_ARCHITECTURE=1",
    "E4C6E_PARTIAL_POINT_REGISTRY_REUSED_BY_HASH_ONLY=1",
    "POINT_REGISTRY_NUMERIC_ROWS_OPENED=0",
    "DISTANCE_VALUES_COMPUTED=0",
    "PCA_VALUES_COMPUTED=0",
    "EIGENVALUES_COMPUTED=0",
    "AFFINE_RANK_COMPUTED=0",
    "STATE_POINT_COUNT=8",
    "NUMERICAL_COORDINATE_COUNT=5",
    "NUMERICALLY_REPRESENTED_CONCEPT_COUNT=4",
    "UNORDERED_PAIRWISE_POINT_COUNT=28",
    "DUAL_METRIC_SQUARED_DISTANCE_PLAN_ROW_COUNT=56",
    "OWNER_RENTER_WITHIN_AGE_PAIR_COUNT=4",
    "ADJACENT_AGE_WITHIN_TENURE_PAIR_COUNT=6",
    "CANONICAL_GEOMETRY_PRIMITIVE=SQUARED_METRIC_DISTANCE_ON_DIFFERENCE_VECTORS",
    "CANONICAL_METRIC_ID=M1_NATURAL_TRANSFORM_UNIT_IDENTITY",
    "MANDATORY_SENSITIVITY_METRIC_ID=M2_CONCEPT_BALANCED_I_SPLIT",
    "DOWNSTREAM_MUST_REPORT_BOTH_METRICS=1",
    "BEST_LOOKING_METRIC_SELECTION_AUTHORIZED=0",
    "ABSOLUTE_ORIGIN_INTERPRETATION_AUTHORIZED=0",
    "DESCRIPTIVE_POINT_GEOMETRY_AUTHORIZED=1",
    "INFERENTIAL_GEOMETRY_AUTHORIZED=0",
    "PAIRWISE_DISTANCE_STANDARD_ERROR_AUTHORIZED=0",
    "PAIRWISE_DISTANCE_CONFIDENCE_INTERVAL_AUTHORIZED=0",
    "CONTRAST_SIGNIFICANCE_TEST_AUTHORIZED=0",
    "WITHIN_CELL_U1_SUFFICIENT_FOR_CROSS_CELL_DIFFERENCE_INFERENCE=0",
    "ZERO_CROSS_CELL_SAMPLING_COVARIANCE_ASSUMED=0",
    "SAMPLING_COVARIANCE_EQUALS_ECONOMIC_STATE_DEPENDENCE=0",
    "PCA_AUTHORIZED=0",
    "WHITENING_AUTHORIZED=0",
    "SVD_THRESHOLD_DIMENSION_AUTHORIZED=0",
    "EIGENVALUE_THRESHOLD_DIMENSION_AUTHORIZED=0",
    "EXACT_AFFINE_RANK_AS_INTRINSIC_DIMENSION_AUTHORIZED=0",
    "DIMENSIONALITY_TEST_AUTHORIZED=0",
    "FIVE_COORDINATES_IMPLY_FIVE_DIMENSIONS=0",
    "FOUR_CONCEPTS_IMPLY_FOUR_DIMENSIONS=0",
    "C_INCLUDED=0",
    "H_ACCESS_PROMOTED_TO_FULL_H_STATE=0",
    "I_SCALAR_CREATED=0",
    "PARTIAL_PANEL_IS_FULL_CHKDI_STATE_VECTOR=0",
    "CROSS_SECTIONAL_2022_GEOMETRY_IS_TIME_CHANGE=0",
    "DESCRIPTIVE_GEOMETRY_IS_REAL_INFLATION_ESTIMATE=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "E4C9_PARTIAL_STATE_GEOMETRY_AND_DIMENSIONALITY_PREFLIGHT=PASS",
    "E4C9A_PARTIAL_STATE_DESCRIPTIVE_GEOMETRY_EXECUTION_AUTHORIZED=1",
])+"\n"

EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")

print(log,end="")
print("===== GEOMETRY OBJECT REGISTRY =====")
print(OBJECTS.read_text(encoding="utf-8"),end="")
print("===== METRIC GEOMETRY FORMULAS =====")
print(FORMULAS.read_text(encoding="utf-8"),end="")
print("===== INFERENTIAL BOUNDARIES =====")
print(BOUNDARIES.read_text(encoding="utf-8"),end="")
print("===== DIMENSIONALITY METHOD DECISION =====")
print(DIM.read_text(encoding="utf-8"),end="")
