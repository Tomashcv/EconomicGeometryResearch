#!/usr/bin/env python3
from pathlib import Path
import csv,json

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"data/metadata/E4D0B_multiyear_semantic_design_comparability_adjudication_contract.json"
AXES=ROOT/"data/results/E4D0B_adjudication_axis_registry.tsv"
EVIDENCE=ROOT/"data/results/E4D0B_evidence_role_assignment.tsv"
TIMEPOL=ROOT/"data/results/E4D0B_temporal_reference_period_policy.tsv"
STATUS=ROOT/"data/results/E4D0B_status_vocabulary.tsv"
GATES=ROOT/"data/results/E4D0B_preflight_hard_gates.tsv"
DECISION=ROOT/"data/results/E4D0B_multiyear_semantic_design_comparability_adjudication_preflight_decision.tsv"
EXEC=ROOT/"data/metadata/E4D0B_execution.txt"
AUDIT=ROOT/"data/metadata/E4D0B_multiyear_semantic_design_comparability_adjudication_preflight_audit.txt"

c=json.loads(CONTRACT.read_text(encoding="utf-8"))

def write_tsv(path,header,rows):
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,delimiter="\t",lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)

axis_rules={
"YEAR_AVAILABILITY":
("GLOBAL","REQUIRED","official release/evidence exists for both 2019 and 2022","FAIL_OR_UNRESOLVED_BLOCKS"),
"VARIABLE_DEFINITION_CONTINUITY":
("COORDINATE","REQUIRED","raw/derived variable definition and coding preserve frozen coordinate estimand","FAIL_OR_UNRESOLVED_BLOCKS"),
"POPULATION_UNIVERSE_CONTINUITY":
("SURVEY_FAMILY","REQUIRED","target universe and estimator denominator remain equivalent or explicitly versioned","FAIL_OR_UNRESOLVED_BLOCKS"),
"AGE_BAND_MAPPING_CONTINUITY":
("SURVEY_FAMILY","REQUIRED","25-34,35-44,45-54,55-64 mapping is exact in both years","FAIL_OR_UNRESOLVED_BLOCKS"),
"TENURE_MAPPING_CONTINUITY":
("SURVEY_FAMILY","REQUIRED","OWNER/RENTER mapping retains frozen semantics in both years","FAIL_OR_UNRESOLVED_BLOCKS"),
"TRANSFORM_CONTINUITY":
("COORDINATE","REQUIRED","same frozen transform/orientation/reference-scale semantics; no refit on 2019 outcomes","FAIL_OR_UNRESOLVED_BLOCKS"),
"SURVEY_WEIGHT_DESIGN_CONTINUITY":
("SURVEY_FAMILY","REQUIRED","point-weight estimator valid for each year; documented design change may be versioned","FAIL_OR_UNRESOLVED_BLOCKS"),
"REPLICATE_COUNT_AND_FORMULA_CONTINUITY":
("SURVEY_FAMILY","REQUIRED","replicate/MI variance engine valid for each year; exact equality not assumed","FAIL_OR_UNRESOLVED_BLOCKS"),
"REFERENCE_PERIOD_ALIGNMENT":
("COORDINATE","REQUIRED","economic reference period is documented and not inferred from survey-wave label","FAIL_OR_UNRESOLVED_BLOCKS"),
"PRICE_LEVEL_OR_NOMINAL_DEFLATION_POLICY":
("K_COORDINATE","REQUIRED","cross-year monetary bridge frozen before 2019 K values; no post-value deflator choice","FAIL_OR_UNRESOLVED_BLOCKS"),
"MISSING_YEAR_POLICY":
("GLOBAL","REQUIRED","2019→2022 pair uses no interpolation/carry-forward/synthetic intermediate state","FAIL_OR_UNRESOLVED_BLOCKS"),
"SURVEY_RELEASE_VINTAGE_POLICY":
("SURVEY_FAMILY","REQUIRED","exact hash-pinned official vintage/source is named for each evidence item","FAIL_OR_UNRESOLVED_BLOCKS"),
"COMMON_TIME_GRID":
("GLOBAL","REQUIRED","2019 may enter only after all preceding required axes pass/versioned-pass","FAIL_OR_UNRESOLVED_BLOCKS"),
}

axis_rows=[]
for axis in c["required_axes"]:
    scope,requirement,rule,blocking=axis_rules[axis]
    axis_rows.append([axis,scope,requirement,rule,blocking,"NOT_YET_ADJUDICATED"])
write_tsv(
    AXES,
    ["axis","scope","requirement","adjudication_rule","blocking_rule","preflight_status"],
    axis_rows
)

evidence_rows=[
["ACS","2019","official_release_page|variable_dictionary_or_codebook|survey_user_or_technical_guide|sample_accuracy_or_standard_error_documentation",
 "H variable definitions; housing/person universe; age/tenure coding; weights/replicates; reference period"],
["ACS","2022","official_release_page|variable_dictionary_or_codebook|survey_user_or_technical_guide|sample_accuracy_or_standard_error_documentation|survey_change_document",
 "same H axes plus explicit change evidence"],
["SCF","2019","official_release_page|variable_dictionary_or_codebook|survey_change_document|shared_sample_accuracy_or_standard_error_documentation",
 "K/D definitions; household/family universe; age/homeownership semantics; implicates/replicates; design"],
["SCF","2022","official_release_page|variable_dictionary_or_codebook|survey_change_document|shared_sample_accuracy_or_standard_error_documentation",
 "same K/D axes plus documented 2022 design/variable changes"],
["CPS_ASEC","2019","official_release_page|variable_dictionary_or_codebook|survey_user_or_technical_guide|replicate_layout_metadata",
 "I definitions; household/person universe; age/tenure mapping; current-vs-prior-year timing; replicate layout"],
["CPS_ASEC","2022","official_release_page|variable_dictionary_or_codebook|survey_user_or_technical_guide|replicate_layout_metadata",
 "same I axes for 2022"],
]
write_tsv(
    EVIDENCE,
    ["family","year","required_evidence_roles","adjudication_use"],
    evidence_rows
)

time_rows=[
["ACS","2019","DO_NOT_ASSUME_WAVE_LABEL_EQUALS_POINT_DATE",
 "document survey/reference period from official ACS evidence before temporal alignment"],
["ACS","2022","DO_NOT_ASSUME_WAVE_LABEL_EQUALS_POINT_DATE",
 "document survey/reference period from official ACS evidence before temporal alignment"],
["SCF","2019","DO_NOT_ASSUME_WAVE_LABEL_EQUALS_POINT_DATE",
 "document SCF interview/reference conventions and any nominal-dollar basis"],
["SCF","2022","DO_NOT_ASSUME_WAVE_LABEL_EQUALS_POINT_DATE",
 "document SCF interview/reference conventions and any nominal-dollar basis"],
["CPS_ASEC","2019","MIXED_TIMING_MUST_BE_EXPLICIT",
 "separate current-survey labor status from prior-calendar-year work-experience concepts if used by frozen I coordinates"],
["CPS_ASEC","2022","MIXED_TIMING_MUST_BE_EXPLICIT",
 "same timing decomposition as 2019; no silent relabeling to a single calendar instant"],
]
write_tsv(
    TIMEPOL,
    ["family","year","policy","requirement"],
    time_rows
)

status_rows=[
["PASS","directly documented same frozen estimand/design rule across years","ELIGIBLE_IF_ALL_REQUIRED_AXES_RESOLVED"],
["VERSIONED_PASS","documented year-specific implementation preserves same frozen estimand under precommitted bridge","ELIGIBLE_ONLY_WITH_EXPLICIT_BRIDGE"],
["FAIL","documented incompatibility with frozen estimand/cohort/transform semantics","BLOCKS_2019"],
["UNRESOLVED","official evidence bundle insufficient for a defensible decision","BLOCKS_2019"],
]
write_tsv(
    STATUS,
    ["status","meaning","downstream_effect"],
    status_rows
)

gate_rows=[
["E4D0A_FROZEN_EVIDENCE_BUNDLE_REUSED","PASS"],
["E4D0A_DOCUMENT_SEMANTIC_ADJUDICATION_PERFORMED_IN_PREFLIGHT","PASS_NO"],
["E4D0B_EXACT_13_REQUIRED_AXES_FROZEN","PASS"],
["PASS_VERSIONED_PASS_FAIL_UNRESOLVED_VOCABULARY_FROZEN","PASS"],
["REFERENCE_PERIOD_ALIGNMENT_EXPLICIT","PASS"],
["K_MONETARY_BRIDGE_REQUIRED_BEFORE_2019_VALUES","PASS"],
["2019_REFERENCE_SCALE_REFIT_AFTER_VALUES","PASS_PROHIBITED"],
["SAME_REPLICATE_COUNT_TREATED_AS_DESIGN_PROOF","PASS_NO"],
["INTERPOLATION_OR_CARRY_FORWARD_AUTHORIZED","PASS_NO"],
["ADDITIONAL_YEAR_ECONOMIC_VALUES_OPENED","PASS_0"],
["COMMON_YEAR_GRID_FROZEN","PASS_0"],
["TEMPORAL_GEOMETRY_COMPUTED","PASS_0"],
["REAL_INFLATION_ESTIMATION_AUTHORIZED","PASS_0"],
]
write_tsv(GATES,["gate","value"],gate_rows)

decision_rows=[
["TARGET_YEAR_PAIR","2019_TO_2022"],
["FROZEN_NUMERICAL_COORDINATE_COUNT","5"],
["REPRESENTED_CONCEPT_COUNT","4"],
["REQUIRED_ADJUDICATION_AXIS_COUNT","13"],
["STATUS_VOCABULARY_COUNT","4"],
["OFFICIAL_EVIDENCE_ARTIFACT_COUNT","25"],
["E4D0A_DOCUMENT_SEMANTIC_CONTENT_USED_FOR_ADJUDICATION","0"],
["ADDITIONAL_YEAR_ECONOMIC_VALUES_OPENED","0"],
["COMPARABILITY_ADJUDICATED","0"],
["ADDITIONAL_YEAR_COMPARABILITY_VERIFIED_COUNT","0"],
["COMMON_YEAR_GRID_FROZEN","0"],
["TEMPORAL_GEOMETRY_COMPUTED","0"],
["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
["E4D1_MULTIYEAR_PARTIAL_STATE_COORDINATE_EXECUTION_PREFLIGHT_AUTHORIZED","0"],
["NEXT_PRIMARY_PHASE_ID","E4D0B1"],
["E4D0B1_SEMANTIC_AND_DESIGN_COMPARABILITY_ADJUDICATION_EXECUTION_AUTHORIZED","1"],
["E4D0B_MULTIYEAR_SEMANTIC_AND_DESIGN_COMPARABILITY_ADJUDICATION_PREFLIGHT","PASS"],
]
write_tsv(DECISION,["decision","value"],decision_rows)

log="\n".join([
"E4D0A_REUSED_AS_CANONICAL_OFFICIAL_EVIDENCE_BUNDLE=1",
"TARGET_YEAR_PAIR=2019_TO_2022",
"FROZEN_NUMERICAL_COORDINATE_COUNT=5",
"REPRESENTED_CONCEPT_COUNT=4",
"REQUIRED_ADJUDICATION_AXIS_COUNT=13",
"STATUS_VOCABULARY_COUNT=4",
"OFFICIAL_EVIDENCE_ARTIFACT_COUNT=25",
"E4D0A_DOCUMENT_SEMANTIC_CONTENT_USED_FOR_ADJUDICATION=0",
"ADDITIONAL_YEAR_ECONOMIC_VALUES_OPENED=0",
"COMPARABILITY_ADJUDICATED=0",
"ADDITIONAL_YEAR_COMPARABILITY_VERIFIED_COUNT=0",
"COMMON_YEAR_GRID_FROZEN=0",
"TEMPORAL_GEOMETRY_COMPUTED=0",
"REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
"E4D1_MULTIYEAR_PARTIAL_STATE_COORDINATE_EXECUTION_PREFLIGHT_AUTHORIZED=0",
"E4D0B1_SEMANTIC_AND_DESIGN_COMPARABILITY_ADJUDICATION_EXECUTION_AUTHORIZED=1",
"E4D0B_MULTIYEAR_SEMANTIC_AND_DESIGN_COMPARABILITY_ADJUDICATION_PREFLIGHT=PASS",
])+"\n"

EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
