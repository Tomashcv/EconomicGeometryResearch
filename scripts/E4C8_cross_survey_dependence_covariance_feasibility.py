#!/usr/bin/env python3
from pathlib import Path
import csv, json
from itertools import combinations

ROOT=Path(__file__).resolve().parents[1]

E7_CONTRACT=ROOT/"data/metadata/E4C7_cross_coordinate_metric_scale_architecture_contract.json"
E7_EXEC=ROOT/"data/metadata/E4C7_execution.txt"
E6_CONTRACT=ROOT/"data/metadata/E4C6E_partial_observed_coordinate_registry_execution_contract.json"
CONTRACT=ROOT/"data/metadata/E4C8_cross_survey_dependence_covariance_feasibility_contract.json"

EXEC=ROOT/"data/metadata/E4C8_execution.txt"
AUDIT=ROOT/"data/metadata/E4C8_cross_survey_dependence_covariance_feasibility_audit.txt"
BLOCKS=ROOT/"data/results/E4C8_coordinate_survey_block_registry.tsv"
PAIRS=ROOT/"data/results/E4C8_pairwise_covariance_feasibility.tsv"
PATTERN=ROOT/"data/results/E4C8_covariance_identifiability_pattern.tsv"
SEMANTICS=ROOT/"data/results/E4C8_dependence_semantics.tsv"
SEQUENCE=ROOT/"data/results/E4C8_post_feasibility_research_sequence.tsv"
DECISION=ROOT/"data/results/E4C8_cross_survey_dependence_covariance_feasibility_decision.tsv"

# Structural contract reads only. The numeric registry file is intentionally not opened.
e7=json.loads(E7_CONTRACT.read_text(encoding="utf-8"))
e6=json.loads(E6_CONTRACT.read_text(encoding="utf-8"))
c=json.loads(CONTRACT.read_text(encoding="utf-8"))

coords=e6["frozen_coordinate_order"]
expected=[
    "H_ACCESS_SPACE_ROOMS_PER_PERSON",
    "K_FIN_MEAN_TRANSFORMED",
    "D_PIRTOTAL_MEAN_STATE_TRANSFORMED",
    "I_FYFT_SHARE",
    "I_SEARCH_SECURITY",
]
assert coords==expected
assert e7["coordinate_order"]==expected

blocks=c["coordinate_survey_blocks"]
assert list(blocks.keys())==expected
assert len(set(blocks.values()))==3

scope={
    "H_ACCESS_SPACE_ROOMS_PER_PERSON":"H_SUBCOORDINATE_NOT_FULL_H",
    "K_FIN_MEAN_TRANSFORMED":"K_FULL_COMPONENT_SCALAR",
    "D_PIRTOTAL_MEAN_STATE_TRANSFORMED":"D_FULL_COMPONENT_SCALAR",
    "I_FYFT_SHARE":"I_PRIMARY_SUBCOORDINATE",
    "I_SEARCH_SECURITY":"I_PRIMARY_SUBCOORDINATE",
}

with BLOCKS.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["coordinate_id","survey_block","coordinate_scope"])
    for x in coords:
        w.writerow([x,blocks[x],scope[x]])

pair_rows=[]
same_pairs=[]
cross_pairs=[]
for a,b in combinations(coords,2):
    same=blocks[a]==blocks[b]
    if same:
        status="POTENTIALLY_IDENTIFIABLE_WITH_DEDICATED_PRECOMMITTED_JOINT_REPLICATE_ESTIMATOR"
        zero_policy="NOT_APPLICABLE"
        next_req=("PAIRED_SCF_MI_REPLICATE_COVARIANCE_ESTIMATOR_PREFLIGHT"
                  if blocks[a]=="SCF2022"
                  else "PAIRED_CPS_REPLICATE_COVARIANCE_ESTIMATOR_PREFLIGHT")
        same_pairs.append((a,b))
    else:
        status="NOT_IDENTIFIED_FROM_CURRENT_UNLINKED_SURVEY_ARCHITECTURE"
        zero_policy="UNKNOWN_NOT_ASSUMED_ZERO"
        next_req="CROSS_SURVEY_UNCERTAINTY_POLICY_REQUIRED"
        cross_pairs.append((a,b))
    pair_rows.append([
        a,b,blocks[a],blocks[b],
        "SAME_SURVEY" if same else "CROSS_SURVEY",
        status,zero_policy,next_req
    ])

assert len(pair_rows)==10
assert len(same_pairs)==2
assert len(cross_pairs)==8
assert set(same_pairs)=={
    ("K_FIN_MEAN_TRANSFORMED","D_PIRTOTAL_MEAN_STATE_TRANSFORMED"),
    ("I_FYFT_SHARE","I_SEARCH_SECURITY"),
}

with PAIRS.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow([
        "coordinate_a","coordinate_b","survey_a","survey_b","pair_type",
        "sampling_covariance_status","zero_covariance_policy","next_requirement"
    ])
    w.writerows(pair_rows)

# Symbolic identifiability pattern, not a covariance estimate.
# VAR = marginal variance already represented through source SE;
# EST = same-survey off-diagonal potentially estimable later;
# UNK = cross-survey off-diagonal unknown and not assumed zero.
with PATTERN.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["row_coordinate"]+coords)
    for r in coords:
        row=[r]
        for col in coords:
            if r==col:
                token="VAR_MARGINAL_SE_AVAILABLE"
            elif blocks[r]==blocks[col]:
                token="OFFDIAG_POTENTIALLY_IDENTIFIABLE"
            else:
                token="OFFDIAG_UNKNOWN_NOT_ZERO"
            row.append(token)
        w.writerow(row)

semantic_rows=[
    [
        "SAMPLING_ESTIMATOR_COVARIANCE",
        "uncertainty dependence between estimated coordinate statistics",
        "PARTIALLY_IDENTIFIABLE_BY_SURVEY_BLOCK",
        "NOT_EQUAL_TO_ECONOMIC_STATE_DEPENDENCE"
    ],
    [
        "ECONOMIC_STATE_DEPENDENCE",
        "association or co-movement among underlying economic concepts",
        "NOT_IDENTIFIED_BY_SURVEY_SAMPLE_SEPARATION",
        "MUST_NOT_BE_INFERRED_FROM_SAMPLING_ARCHITECTURE"
    ],
    [
        "METRIC_DIAGONALITY",
        "chosen geometry has no off-diagonal metric coupling",
        "FROZEN_IN_E4C7",
        "DOES_NOT_IMPLY_COVARIANCE_DIAGONALITY"
    ],
]
with SEMANTICS.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["object","meaning","E4C8_status","non_equivalence"])
    w.writerows(semantic_rows)

sequence=[
    [1,"E4C8A","WITHIN_SURVEY_COVARIANCE_ESTIMATOR_PREFLIGHT",
     "freeze exact SCF K-D MI/replicate and CPS I-pair replicate covariance lineage + formulas before covariance values"],
    [2,"E4C8B","WITHIN_SURVEY_COVARIANCE_EXECUTION",
     "compute only the two precommitted same-survey covariance families after E4C8A"],
    [3,"E4C8C","CROSS_SURVEY_UNCERTAINTY_POLICY_PREFLIGHT",
     "freeze treatment of eight unknown cross-survey covariances; zero may appear only as explicit sensitivity, never silent fact"],
    [4,"E4C9","PARTIAL_STATE_GEOMETRY_OR_DIMENSIONALITY_PREFLIGHT",
     "only after covariance/uncertainty policy; still not full CHKDI and not real inflation"],
]
with SEQUENCE.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["order","phase","title","rule"])
    w.writerows(sequence)

decisions=[
    ["COORDINATE_COUNT","5"],
    ["SURVEY_BLOCK_COUNT","3"],
    ["SAME_SURVEY_NONTRIVIAL_PAIR_COUNT","2"],
    ["CROSS_SURVEY_PAIR_COUNT","8"],
    ["K_D_COVARIANCE_POTENTIALLY_IDENTIFIABLE","1"],
    ["I_PRIMARY_PAIR_COVARIANCE_POTENTIALLY_IDENTIFIABLE","1"],
    ["SCF_COVARIANCE_FORMULA_FROZEN","0"],
    ["CPS_COVARIANCE_FORMULA_FROZEN","0"],
    ["CROSS_SURVEY_SAMPLING_COVARIANCE_IDENTIFIED","0"],
    ["CROSS_SURVEY_COVARIANCE_ASSUMED_ZERO","0"],
    ["INDEPENDENT_SAMPLING_DESIGN_ESTABLISHED","0"],
    ["FULL_5X5_SAMPLING_COVARIANCE_IDENTIFIED","0"],
    ["PARTIAL_BLOCK_COVARIANCE_POTENTIALLY_IDENTIFIABLE","1"],
    ["EIGHT_CELL_EMPIRICAL_COVARIANCE_AUTHORIZED","0"],
    ["ECONOMIC_STATE_DEPENDENCE_IDENTIFIED","0"],
    ["METRIC_DIAGONALITY_IMPLIES_STATISTICAL_INDEPENDENCE","0"],
    ["COVARIANCE_VALUES_COMPUTED","0"],
    ["REGISTRY_NUMERIC_ROWS_READ","0"],
    ["GEOMETRY_AUTHORIZED","0"],
    ["E4C8A_WITHIN_SURVEY_COVARIANCE_ESTIMATOR_PREFLIGHT_AUTHORIZED","1"],
]
with DECISION.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["decision","value"])
    w.writerows(decisions)

log="\n".join([
    "E4C7_REUSED_AS_CANONICAL_METRIC_ARCHITECTURE=1",
    "E4C6E_PROVENANCE_REUSED_STRUCTURALLY=1",
    "REGISTRY_NUMERIC_ROWS_READ=0",
    "COVARIANCE_VALUES_COMPUTED=0",
    "COORDINATE_COUNT=5",
    "SURVEY_BLOCK_COUNT=3",
    "ACS_BLOCK_COORDINATE_COUNT=1",
    "SCF_BLOCK_COORDINATE_COUNT=2",
    "CPS_BLOCK_COORDINATE_COUNT=2",
    "PAIRWISE_OFFDIAGONAL_PAIR_COUNT=10",
    "SAME_SURVEY_NONTRIVIAL_PAIR_COUNT=2",
    "CROSS_SURVEY_PAIR_COUNT=8",
    "K_D_COVARIANCE_POTENTIALLY_IDENTIFIABLE=1",
    "I_PRIMARY_PAIR_COVARIANCE_POTENTIALLY_IDENTIFIABLE=1",
    "SCF_COVARIANCE_FORMULA_FROZEN=0",
    "CPS_COVARIANCE_FORMULA_FROZEN=0",
    "CROSS_SURVEY_SAMPLING_COVARIANCE_IDENTIFIED=0",
    "CROSS_SURVEY_COVARIANCE_ASSUMED_ZERO=0",
    "INDEPENDENT_SAMPLING_DESIGN_ESTABLISHED=0",
    "UNKNOWN_CROSS_SURVEY_COVARIANCE_REPLACED_BY_ZERO=0",
    "FULL_5X5_SAMPLING_COVARIANCE_IDENTIFIED=0",
    "PARTIAL_BLOCK_COVARIANCE_POTENTIALLY_IDENTIFIABLE=1",
    "EIGHT_CELL_EMPIRICAL_COVARIANCE_AUTHORIZED=0",
    "PCA_WHITENING_AUTHORIZED=0",
    "SOURCE_SE_PRODUCT_USED_AS_OFFDIAGONAL_COVARIANCE=0",
    "ECONOMIC_STATE_DEPENDENCE_IDENTIFIED=0",
    "SURVEY_SAMPLE_SEPARATION_IMPLIES_ECONOMIC_INDEPENDENCE=0",
    "METRIC_DIAGONALITY_IMPLIES_STATISTICAL_INDEPENDENCE=0",
    "SAMPLING_COVARIANCE_EQUALS_ECONOMIC_STATE_DEPENDENCE=0",
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
    "E4C8_CROSS_SURVEY_DEPENDENCE_AND_COVARIANCE_FEASIBILITY_PREFLIGHT=PASS",
    "E4C8A_WITHIN_SURVEY_COVARIANCE_ESTIMATOR_PREFLIGHT_AUTHORIZED=1",
])+"\n"

EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")

print(log,end="")
print("===== COORDINATE SURVEY BLOCKS =====")
print(BLOCKS.read_text(encoding="utf-8"),end="")
print("===== PAIRWISE COVARIANCE FEASIBILITY =====")
print(PAIRS.read_text(encoding="utf-8"),end="")
print("===== COVARIANCE IDENTIFIABILITY PATTERN =====")
print(PATTERN.read_text(encoding="utf-8"),end="")
print("===== DEPENDENCE SEMANTICS =====")
print(SEMANTICS.read_text(encoding="utf-8"),end="")
print("===== POST-FEASIBILITY RESEARCH SEQUENCE =====")
print(SEQUENCE.read_text(encoding="utf-8"),end="")
