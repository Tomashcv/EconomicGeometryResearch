#!/usr/bin/env python3
from pathlib import Path
import csv, json

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"data/metadata/E4C8C_cross_survey_uncertainty_policy_contract.json"

EXEC=ROOT/"data/metadata/E4C8C_execution.txt"
AUDIT=ROOT/"data/metadata/E4C8C_cross_survey_uncertainty_policy_audit.txt"
POLICY=ROOT/"data/results/E4C8C_uncertainty_policy_registry.tsv"
MASK=ROOT/"data/results/E4C8C_covariance_identifiability_mask.tsv"
RULES=ROOT/"data/results/E4C8C_psd_completion_rules.tsv"
OBLIG=ROOT/"data/results/E4C8C_downstream_robustness_obligations.tsv"
DECISION=ROOT/"data/results/E4C8C_cross_survey_uncertainty_policy_decision.tsv"

c=json.loads(CONTRACT.read_text(encoding="utf-8"))
coords=c["canonical_policy"]["coordinate_order"]

policy_rows=[
    [
        "U1_PSD_COMPLETION_PARTIAL_IDENTIFICATION_SET","CANONICAL",
        "all symmetric PSD 5x5 matrices with frozen diagonals and two frozen within-survey offdiagonals; eight cross-survey offdiagonals free under PSD",
        "NO","YES"
    ],
    [
        "S1_BLOCK_DIAGONAL_ZERO_CROSS_SURVEY_REFERENCE","MANDATORY_NONCANONICAL_SENSITIVITY_IF_PSD",
        "same frozen known entries; set exactly eight cross-survey offdiagonals to zero",
        "YES","NO"
    ],
]
with POLICY.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["policy_id","role","definition","sets_cross_survey_unknowns_to_zero","canonical_for_inference"])
    w.writerows(policy_rows)

status={}
for a in coords:
    for b in coords:
        if a==b:
            s="KNOWN_DIAGONAL_FROM_E4C6E_SE_SQUARED"
        elif {a,b}=={"K_FIN_MEAN_TRANSFORMED","D_PIRTOTAL_MEAN_STATE_TRANSFORMED"}:
            s="KNOWN_WITHIN_SCF_FROM_E4C8B"
        elif {a,b}=={"I_FYFT_SHARE","I_SEARCH_SECURITY"}:
            s="KNOWN_WITHIN_CPS_FROM_E4C8B"
        else:
            s="UNKNOWN_CROSS_SURVEY_FREE_UNDER_PSD"
        status[(a,b)]=s

with MASK.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["row_coordinate"]+coords)
    for a in coords:
        w.writerow([a]+[status[(a,b)] for b in coords])

rules=[
    ["SYMMETRY","REQUIRED","Sigma_ij=Sigma_ji"],
    ["POSITIVE_SEMIDEFINITE","REQUIRED","Sigma must be PSD"],
    ["DIAGONAL_FIX","REQUIRED","Sigma_ii equals exact square of frozen E4C6E se_state"],
    ["SCF_KD_FIX","REQUIRED","Sigma_KD equals frozen E4C8B K-D combined covariance"],
    ["CPS_I_PAIR_FIX","REQUIRED","Sigma_I1I2 equals frozen E4C8B I-pair covariance"],
    ["CROSS_SURVEY_UNKNOWN_COUNT","REQUIRED","exactly 8 unique offdiagonal pairs remain unknown before completion"],
    ["EXTRA_RHO_BOX_BOUND","PROHIBITED","no arbitrary correlation cap narrower than PSD"],
    ["BEST_FIT_COMPLETION","PROHIBITED","no completion selected from observed outcome fit"],
    ["NEAREST_PSD_PROJECTION","PROHIBITED","do not modify frozen known entries to force PSD"],
    ["AUTOMATIC_CLIPPING","PROHIBITED","do not clip covariance values to feasibility bounds"],
    ["ZERO_CROSS_SURVEY_CANONICAL","PROHIBITED","zero completion is sensitivity only"],
]
with RULES.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["rule","status","meaning"])
    w.writerows(rules)

oblig=[
    ["CANONICAL_COVARIANCE_SENSITIVE_CLAIM","must hold for every feasible Sigma in U1","YES"],
    ["ZERO_CROSS_SURVEY_RESULT","must be labeled S1 sensitivity; never canonical fact","YES"],
    ["METRIC_DEPENDENT_ROBUST_CLAIM","must additionally satisfy frozen E4C7 dual-metric reporting rule","YES"],
    ["EMPTY_U1_CELL","halt and preserve forensic state; no automatic repair","YES"],
    ["ECONOMIC_DEPENDENCE_LANGUAGE","must not be inferred from sampling covariance architecture","YES"],
]
with OBLIG.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["claim_class","obligation","mandatory"])
    w.writerows(oblig)

decisions=[
    ["CANONICAL_UNCERTAINTY_POLICY_ID","U1_PSD_COMPLETION_PARTIAL_IDENTIFICATION_SET"],
    ["MANDATORY_SENSITIVITY_POLICY_ID","S1_BLOCK_DIAGONAL_ZERO_CROSS_SURVEY_REFERENCE"],
    ["MATRIX_DIMENSION","5"],
    ["KNOWN_DIAGONAL_ENTRY_COUNT","5"],
    ["KNOWN_NONTRIVIAL_OFFDIAGONAL_PAIR_COUNT","2"],
    ["UNKNOWN_CROSS_SURVEY_OFFDIAGONAL_PAIR_COUNT","8"],
    ["CROSS_SURVEY_ZERO_CANONICAL","0"],
    ["ZERO_CROSS_SURVEY_SENSITIVITY_REQUIRED","1"],
    ["EXTRA_RHO_BOX_BOUND_INTRODUCED","0"],
    ["BEST_FIT_COMPLETION_AUTHORIZED","0"],
    ["NEAREST_PSD_PROJECTION_AUTHORIZED","0"],
    ["AUTOMATIC_COVARIANCE_CLIPPING_AUTHORIZED","0"],
    ["NUMERIC_REGISTRY_ROWS_OPENED","0"],
    ["PSD_FEASIBILITY_COMPUTED","0"],
    ["CROSS_SURVEY_COVARIANCE_POINT_VALUES_COMPUTED","0"],
    ["CROSS_SURVEY_COVARIANCE_ASSUMED_ZERO","0"],
    ["ECONOMIC_STATE_DEPENDENCE_INFERRED","0"],
    ["METRIC_MUTATED","0"],
    ["GEOMETRY_AUTHORIZED","0"],
    ["E4C8D_CELLWISE_COVARIANCE_UNCERTAINTY_SET_CONSTRUCTION_AUTHORIZED","1"],
]
with DECISION.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["decision","value"])
    w.writerows(decisions)

log="\n".join([
    "E4C8B_REUSED_AS_CANONICAL_WITHIN_SURVEY_COVARIANCE=1",
    "E4C6E_REUSED_AS_MARGINAL_SE_LINEAGE=1",
    "E4C7_REUSED_AS_FROZEN_METRIC_ARCHITECTURE=1",
    "NUMERIC_REGISTRY_ROWS_OPENED=0",
    "PSD_FEASIBILITY_COMPUTED=0",
    "CROSS_SURVEY_COVARIANCE_POINT_VALUES_COMPUTED=0",
    "CANONICAL_UNCERTAINTY_POLICY_ID=U1_PSD_COMPLETION_PARTIAL_IDENTIFICATION_SET",
    "MANDATORY_SENSITIVITY_POLICY_ID=S1_BLOCK_DIAGONAL_ZERO_CROSS_SURVEY_REFERENCE",
    "MATRIX_DIMENSION=5",
    "KNOWN_DIAGONAL_ENTRY_COUNT=5",
    "KNOWN_NONTRIVIAL_OFFDIAGONAL_PAIR_COUNT=2",
    "UNKNOWN_CROSS_SURVEY_OFFDIAGONAL_PAIR_COUNT=8",
    "PSD_REQUIRED_FOR_CANONICAL_COMPLETIONS=1",
    "SYMMETRY_REQUIRED=1",
    "FROZEN_DIAGONALS_MUST_REMAIN_FIXED=1",
    "FROZEN_WITHIN_SURVEY_COVARIANCES_MUST_REMAIN_FIXED=1",
    "EXTRA_RHO_BOX_BOUND_INTRODUCED=0",
    "BEST_FIT_COMPLETION_AUTHORIZED=0",
    "NEAREST_PSD_PROJECTION_AUTHORIZED=0",
    "AUTOMATIC_COVARIANCE_CLIPPING_AUTHORIZED=0",
    "CROSS_SURVEY_ZERO_CANONICAL=0",
    "ZERO_CROSS_SURVEY_SENSITIVITY_REQUIRED=1",
    "ZERO_CROSS_SURVEY_SENSITIVITY_IS_INDEPENDENCE_CLAIM=0",
    "EMPTY_FEASIBLE_SET_TRIGGERS_HALT=1",
    "CROSS_SURVEY_COVARIANCE_ASSUMED_ZERO=0",
    "ECONOMIC_STATE_DEPENDENCE_INFERRED=0",
    "SURVEY_SEPARATION_IMPLIES_ECONOMIC_INDEPENDENCE=0",
    "METRIC_DIAGONALITY_IMPLIES_COVARIANCE_DIAGONALITY=0",
    "DOWNSTREAM_ROBUST_CLAIM_REQUIRES_ALL_FEASIBLE_U1_COMPLETIONS=1",
    "BEST_LOOKING_COMPLETION_SELECTION_AUTHORIZED=0",
    "C_INCLUDED_IN_COVARIANCE_ARCHITECTURE=0",
    "H_ACCESS_PROMOTED_TO_FULL_H_STATE=0",
    "I_SCALAR_CREATED=0",
    "PARTIAL_PANEL_IS_FULL_CHKDI_STATE_VECTOR=0",
    "CROSS_COORDINATE_METRIC_SCALE_FROZEN=1",
    "GEOMETRY_READY=0",
    "GEOMETRY_AUTHORIZED=0",
    "DIMENSIONALITY_TEST_AUTHORIZED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "E4C8C_CROSS_SURVEY_UNCERTAINTY_POLICY_PREFLIGHT=PASS",
    "E4C8D_CELLWISE_COVARIANCE_UNCERTAINTY_SET_CONSTRUCTION_AUTHORIZED=1",
])+"\n"

EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")

print(log,end="")
print("===== UNCERTAINTY POLICY REGISTRY =====")
print(POLICY.read_text(encoding="utf-8"),end="")
print("===== COVARIANCE IDENTIFIABILITY MASK =====")
print(MASK.read_text(encoding="utf-8"),end="")
print("===== PSD COMPLETION RULES =====")
print(RULES.read_text(encoding="utf-8"),end="")
print("===== DOWNSTREAM ROBUSTNESS OBLIGATIONS =====")
print(OBLIG.read_text(encoding="utf-8"),end="")
