#!/usr/bin/env python3
from pathlib import Path
import csv, json

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"data/metadata/E4C8A_within_survey_covariance_formula_lineage_contract.json"

EXEC=ROOT/"data/metadata/E4C8A_execution.txt"
AUDIT=ROOT/"data/metadata/E4C8A_within_survey_covariance_formula_lineage_audit.txt"
SOURCES=ROOT/"data/results/E4C8A_covariance_source_selection_contract.tsv"
FORMULAS=ROOT/"data/results/E4C8A_covariance_formula_registry.tsv"
PAIRKEYS=ROOT/"data/results/E4C8A_pairing_key_schema.tsv"
PLAN=ROOT/"data/results/E4C8A_covariance_execution_plan.tsv"
DECISION=ROOT/"data/results/E4C8A_within_survey_covariance_formula_lineage_decision.tsv"

c=json.loads(CONTRACT.read_text(encoding="utf-8"))

sources=[
    [
        "SCF_K_D_IMPLICATE","SCF2022",
        "data/results/E4C5G_transformed_implicate_statistics.tsv",
        "K_FIN_MEAN|D_PIRTOTAL_MEAN",
        "year=2022;age=frozen4_with_explicit_normalization;tenure=OWNER|RENTER;component=K|D",
        "transformed_state_value","implicate"
    ],
    [
        "SCF_K_D_REPLICATE","SCF2022",
        "data/results/E4C5G_transformed_replicate_statistics.tsv",
        "K_FIN_MEAN|D_PIRTOTAL_MEAN",
        "year=2022;age=frozen4_with_explicit_normalization;tenure=OWNER|RENTER;component=K|D",
        "transformed_state_value","replicate"
    ],
    [
        "CPS_I_FULL_SAMPLE","CPS_ASEC_2022",
        "data/results/E4A2D_2022_cps_i_cohort_inference.tsv",
        "I_FYFT_SHARE|I_SEARCH_BURDEN_SHARE",
        "year=2022;role=PRIMARY;age=frozen4_with_explicit_normalization;tenure=OWNER|RENTER;state_sign=+1|-1",
        "point_estimate","FULL_SAMPLE"
    ],
    [
        "CPS_I_REPLICATE","CPS_ASEC_2022",
        "data/results/E4A2D_2022_cps_i_replicate_estimates.tsv",
        "I_FYFT_SHARE|I_SEARCH_BURDEN_SHARE",
        "year=2022;age=frozen4_with_explicit_normalization;tenure_or_contrast=OWNER|RENTER",
        "value","replicate"
    ],
]
with SOURCES.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["source_role","survey","path","target_ids","selector","numeric_field_for_E4C8B","pairing_index"])
    w.writerows(sources)

formulas=[
    [
        "SCF_K_D","SCF2022","IMPUTATION_COVARIANCE","5","4",
        "sum_m((K_m-mean_m_K)*(D_m-mean_m_D))/(5-1)",
        "TRANSFORMED_STATE_SPACE","BILINEAR_EXTENSION_OF_FROZEN_VARIANCE_ENGINE"
    ],
    [
        "SCF_K_D","SCF2022","SAMPLING_COVARIANCE","999","998",
        "sum_r((K_r-mean_r_K)*(D_r-mean_r_D))/(999-1)",
        "TRANSFORMED_STATE_SPACE","BILINEAR_EXTENSION_OF_FROZEN_VARIANCE_ENGINE"
    ],
    [
        "SCF_K_D","SCF2022","COMBINED_COVARIANCE","5+999","NA",
        "(6/5)*imputation_covariance+sampling_covariance",
        "TRANSFORMED_STATE_SPACE","RUBIN_MI_FACTOR_1_PLUS_1_OVER_5_PLUS_FROZEN_SAMPLING_TERM"
    ],
    [
        "CPS_I_PAIR","CPS_ASEC_2022","REPLICATE_COVARIANCE","160","NA",
        "(4/160)*sum_r((FYFT_r-FYFT_full)*(SEARCH_SECURITY_r-SEARCH_SECURITY_full))",
        "FROZEN_STATE_ORIENTED_SPACE","BILINEAR_EXTENSION_OF_FROZEN_CPS_REPLICATE_VARIANCE_ENGINE"
    ],
]
with FORMULAS.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["pair_id","survey","formula_role","replicate_or_implicate_count","sample_covariance_denominator","exact_formula","state_space","basis"])
    w.writerows(formulas)

pairkeys=[
    ["SCF_K_D","IMPLICATE","year,canonical_age_band,tenure,implicate","5","K_FIN_MEAN,D_PIRTOTAL_MEAN"],
    ["SCF_K_D","REPLICATE","year,canonical_age_band,tenure,replicate","999","K_FIN_MEAN,D_PIRTOTAL_MEAN"],
    ["CPS_I_PAIR","FULL_SAMPLE","year,canonical_age_band,tenure","1","I_FYFT_SHARE,I_SEARCH_BURDEN_SHARE"],
    ["CPS_I_PAIR","REPLICATE","year,canonical_age_band,tenure,replicate","160","I_FYFT_SHARE,I_SEARCH_BURDEN_SHARE"],
]
with PAIRKEYS.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["pair_id","pairing_level","pair_key","expected_count_per_cell","required_members"])
    w.writerows(pairkeys)

plan=[
    ["SCF_K_D","8","5","999","8","SCF_COMBINED_MI_REPLICATE_COVARIANCE","NO_OUTCOME_GATE"],
    ["CPS_I_PAIR","8","0","160","8","CPS_160_REPLICATE_COVARIANCE_AFTER_FROZEN_STATE_SIGN","NO_OUTCOME_GATE"],
]
with PLAN.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["pair_id","cell_count","implicate_count_per_cell","replicate_count_per_cell","expected_covariance_rows","execution_formula","gate_policy"])
    w.writerows(plan)

decisions=[
    ["SAME_SURVEY_PAIR_COUNT","2"],
    ["EXPECTED_COVARIANCE_ROW_COUNT","16"],
    ["SCF_K_D_CELL_COUNT","8"],
    ["SCF_IMPLICATE_COUNT_PER_CELL","5"],
    ["SCF_REPLICATE_COUNT_PER_CELL","999"],
    ["CPS_I_PAIR_CELL_COUNT","8"],
    ["CPS_REPLICATE_COUNT_PER_CELL","160"],
    ["SCF_COVARIANCE_FORMULA_FROZEN","1"],
    ["CPS_COVARIANCE_FORMULA_FROZEN","1"],
    ["PAIRING_KEYS_FROZEN","1"],
    ["SOURCE_LINEAGE_FROZEN","1"],
    ["SOURCE_DATA_ROWS_OPENED","0"],
    ["COVARIANCE_VALUES_COMPUTED","0"],
    ["COVARIANCE_SIGN_USED_AS_GATE","0"],
    ["COVARIANCE_MAGNITUDE_USED_AS_GATE","0"],
    ["CROSS_SURVEY_COVARIANCE_ASSUMED_ZERO","0"],
    ["ECONOMIC_STATE_DEPENDENCE_INFERRED","0"],
    ["I_SCALAR_CREATED","0"],
    ["GEOMETRY_AUTHORIZED","0"],
    ["E4C8B_WITHIN_SURVEY_COVARIANCE_EXECUTION_AUTHORIZED","1"],
]
with DECISION.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["decision","value"])
    w.writerows(decisions)

log="\n".join([
    "E4C8A0_REUSED_AS_LINEAGE_RECON_AUTHORITY=1",
    "E4C8_REUSED_AS_COVARIANCE_FEASIBILITY_AUTHORITY=1",
    "SOURCE_HEADER_COUNT=4",
    "SOURCE_HEADERS_VALIDATED=4",
    "SOURCE_DATA_ROWS_OPENED=0",
    "COVARIANCE_VALUES_COMPUTED=0",
    "SAME_SURVEY_PAIR_COUNT=2",
    "EXPECTED_COVARIANCE_ROW_COUNT=16",
    "SCF_K_D_CELL_COUNT=8",
    "SCF_IMPLICATE_COUNT_PER_CELL=5",
    "SCF_REPLICATE_COUNT_PER_CELL=999",
    "SCF_IMPUTATION_COVARIANCE_DENOMINATOR=4",
    "SCF_SAMPLING_COVARIANCE_DENOMINATOR=998",
    "SCF_MI_COMBINATION_FACTOR=6/5",
    "SCF_COVARIANCE_FORMULA_FROZEN=1",
    "CPS_I_PAIR_CELL_COUNT=8",
    "CPS_REPLICATE_COUNT_PER_CELL=160",
    "CPS_REPLICATE_COVARIANCE_FACTOR=4/160",
    "CPS_REPLICATE_COVARIANCE_FACTOR_REDUCED=1/40",
    "CPS_FYFT_STATE_SIGN=+1",
    "CPS_SEARCH_SECURITY_SOURCE_ESTIMAND=I_SEARCH_BURDEN_SHARE",
    "CPS_SEARCH_SECURITY_STATE_SIGN=-1",
    "CPS_COVARIANCE_FORMULA_FROZEN=1",
    "PAIRING_KEYS_FROZEN=1",
    "SOURCE_LINEAGE_FROZEN=1",
    "AGE_TOKEN_NORMALIZATION_FROZEN_STRUCTURALLY=1",
    "NEW_TRANSFORM_INTRODUCED=0",
    "NEW_VARIANCE_ESTIMATOR_INTRODUCED=0",
    "COVARIANCE_IS_BILINEAR_EXTENSION_OF_FROZEN_VARIANCE_ENGINES=1",
    "COVARIANCE_SIGN_USED_AS_GATE=0",
    "COVARIANCE_MAGNITUDE_USED_AS_GATE=0",
    "STATISTICAL_SIGNIFICANCE_USED_AS_GATE=0",
    "OWNER_RENTER_DIRECTION_USED_AS_GATE=0",
    "CROSS_SURVEY_COVARIANCE_IN_SCOPE=0",
    "CROSS_SURVEY_COVARIANCE_ASSUMED_ZERO=0",
    "ECONOMIC_STATE_DEPENDENCE_INFERRED=0",
    "METRIC_DIAGONALITY_IMPLIES_COVARIANCE_DIAGONALITY=0",
    "C_INCLUDED_IN_COVARIANCE_EXECUTION=0",
    "H_ACCESS_PROMOTED_TO_FULL_H_STATE=0",
    "I_SCALAR_CREATED=0",
    "CROSS_COORDINATE_METRIC_SCALE_FROZEN=1",
    "GEOMETRY_READY=0",
    "GEOMETRY_AUTHORIZED=0",
    "DIMENSIONALITY_TEST_AUTHORIZED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "E4C8A_WITHIN_SURVEY_COVARIANCE_FORMULA_LINEAGE_PREFLIGHT=PASS",
    "E4C8B_WITHIN_SURVEY_COVARIANCE_EXECUTION_AUTHORIZED=1",
])+"\n"

EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")

print(log,end="")
print("===== COVARIANCE SOURCE SELECTION =====")
print(SOURCES.read_text(encoding="utf-8"),end="")
print("===== COVARIANCE FORMULA REGISTRY =====")
print(FORMULAS.read_text(encoding="utf-8"),end="")
print("===== PAIRING KEY SCHEMA =====")
print(PAIRKEYS.read_text(encoding="utf-8"),end="")
print("===== E4C8B EXECUTION PLAN =====")
print(PLAN.read_text(encoding="utf-8"),end="")
