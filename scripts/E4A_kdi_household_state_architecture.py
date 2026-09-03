from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

UPSTREAM = (
    ROOT
    / "data/metadata/E3B4C3_ch_2022_inferential_closeout_audit.txt"
)

CONTRACT = (
    ROOT
    / "data/metadata/E4A_kdi_household_state_architecture.json"
)

SOURCE_MANIFEST = (
    ROOT
    / "data/metadata/E4A_official_source_manifest.tsv"
)

OUT = (
    ROOT
    / "data/metadata/E4A_kdi_household_state_architecture_audit.txt"
)


# =============================================================================
# Upstream state
# =============================================================================

text = UPSTREAM.read_text(
    encoding="utf-8",
)

for token in (
    "E3B4C3_CH_2022_INFERENTIAL_CLOSEOUT=PASS",
    "E4_K_D_I_ARCHITECTURE_AUTHORIZED=1",
    "FIVE_DIMENSIONALITY_PROVEN=0",
    "K_EMPIRICALLY_TESTED=0",
    "D_EMPIRICALLY_TESTED=0",
    "I_EMPIRICALLY_TESTED=0",
):

    if token not in text:

        raise RuntimeError(
            f"missing upstream invariant={token}"
        )


# =============================================================================
# Contract
# =============================================================================

c = json.loads(
    CONTRACT.read_text(
        encoding="utf-8"
    )
)


state_pass = (
    c["state_vector_candidate"]
    == ["C", "H", "K", "D", "I"]
    and c[
        "five_dimensionality_proven"
    ] is False
)


cohort_pass = (
    c[
        "primary_pseudo_cohort"
    ][
        "age_bands"
    ]
    == [
        "25-34",
        "35-44",
        "45-54",
        "55-64",
    ]
    and c[
        "primary_pseudo_cohort"
    ][
        "tenure"
    ]
    == [
        "OWNER",
        "RENTER",
    ]
)


k = c["K"]

k_pass = (
    k[
        "primary_raw_variable"
    ] == "FIN"
    and k[
        "sensitivity_variables"
    ]
    == [
        "LIQ",
        "EQUITY",
        "RETQLIQ",
    ]
    and set(
        k[
            "primary_prohibited_variables"
        ]
    )
    == {
        "NETWORTH",
        "ASSET",
        "HOMEEQ",
        "HOUSES",
    }
    and k[
        "scalar_authorized"
    ] is False
)


d = c["D"]

d_pass = (
    d[
        "primary"
    ][
        "raw_variable"
    ] == "PIRTOTAL"
    and d[
        "primary"
    ][
        "sign"
    ] == -1
    and d[
        "secondary"
    ][
        "raw_variable"
    ] == "DEBT2INC"
    and d[
        "secondary"
    ][
        "sign"
    ] == -1
    and d[
        "minus_debt_dollars_as_sole_primary"
    ] == "PROHIBITED"
    and d[
        "scalar_authorized"
    ] is False
)


i = c["I"]

i_pass = (
    i[
        "temporal_basis"
    ] == "PREVIOUS_YEAR_PRIMARY"
    and i[
        "primary_observables"
    ][0][
        "variable"
    ] == "WEWKRS"
    and i[
        "primary_observables"
    ][0][
        "direction"
    ] == "HIGHER_BETTER"
    and i[
        "primary_observables"
    ][1][
        "variable"
    ] == "WEUEMP"
    and i[
        "primary_observables"
    ][1][
        "direction"
    ] == "HIGHER_WORSE"
    and i[
        "current_week_labor_status_primary"
    ] is False
    and i[
        "scalar_authorized"
    ] is False
)


resource_pass = (
    c[
        "resources"
    ][
        "candidate_variable"
    ] == "HTOTVAL"
    and c[
        "resources"
    ][
        "is_I_variable"
    ] is False
)


cps = c[
    "cps_anchor"
]

cps_pass = (
    cps[
        "household_id"
    ] == "H_SEQ"
    and cps[
        "reference_person_variable"
    ] == "A_EXPRRP"
    and cps[
        "reference_person_codes"
    ] == [1, 2]
    and cps[
        "age_variable"
    ] == "A_AGE"
    and cps[
        "tenure_variable"
    ] == "H_TENURE"
    and cps[
        "owner_code"
    ] == 1
    and cps[
        "renter_code"
    ] == 2
    and cps[
        "no_cash_rent_primary"
    ] is False
    and cps[
        "household_weight"
    ] == "HSUP_WGT"
)


scf = c["scf"]

scf_pass = (
    scf[
        "five_implicates_required"
    ] is True
    and scf[
        "treat_implicates_as_independent_families"
    ] is False
    and scf[
        "summary_extract_dollar_basis"
    ] == "2022_REAL_DOLLARS"
    and scf[
        "second_deflation"
    ] == "PROHIBITED"
    and scf[
        "multiple_imputation_inference_required"
    ] is True
)


dim = c[
    "dimensionality"
]

dimensionality_pass = (
    dim[
        "variable_name_difference_is_proof"
    ] is False
    and dim[
        "owner_renter_significance_is_proof"
    ] is False
    and dim[
        "construct_validity_required"
    ] is True
    and dim[
        "survey_estimation_validity_required"
    ] is True
    and dim[
        "nondegenerate_variation_required"
    ] is True
    and dim[
        "nonredundant_movement_required"
    ] is True
    and dim[
        "alternate_proxy_robustness_required_where_available"
    ] is True
    and dim[
        "numerical_gates_frozen_at_E4A"
    ] is False
    and dim[
        "numerical_gates_must_be_frozen_before_outcome_open"
    ] is True
)


ri = c[
    "real_inflation"
]

ri_pass = (
    ri[
        "state_change_equals_cost_inflation"
    ] is False
    and ri[
        "observed_expenditure_change_equals_inflation"
    ] is False
    and ri[
        "ge_equals_real_inflation"
    ] is False
    and ri[
        "real_inflation_estimation_authorized"
    ] is False
    and ri[
        "final_scalar_authorized"
    ] is False
)


# =============================================================================
# Source manifest structure
# =============================================================================

manifest_lines = [
    x
    for x in SOURCE_MANIFEST.read_text(
        encoding="utf-8"
    ).splitlines()
    if x.strip()
]


source_pass = (
    len(
        manifest_lines
    ) == 7
    and manifest_lines[0]
    == "source_id\tauthority\turl\trole"
    and sum(
        "\tFederal Reserve Board\t"
        in x
        for x in manifest_lines[1:]
    ) == 3
    and sum(
        "\tCensus Bureau\t"
        in x
        for x in manifest_lines[1:]
    ) == 3
)


overall = all([
    state_pass,
    cohort_pass,
    k_pass,
    d_pass,
    i_pass,
    resource_pass,
    cps_pass,
    scf_pass,
    dimensionality_pass,
    ri_pass,
    source_pass,
])


lines = [
    "=" * 100,
    "E4A — K / D / I HOUSEHOLD-STATE ARCHITECTURE",
    "=" * 100,
    "",
    "SCF_ECONOMIC_VALUES_READ=0",
    "CPS_KDI_ECONOMIC_VALUES_READ=0",
    "K_EMPIRICALLY_TESTED=0",
    "D_EMPIRICALLY_TESTED=0",
    "I_EMPIRICALLY_TESTED=0",
    "FIVE_DIMENSIONALITY_PROVEN=0",
    "",
    "===== STATE =====",
    (
        "FIVE_DIMENSION_CANDIDATE_STATE=PASS"
        if state_pass
        else
        "FIVE_DIMENSION_CANDIDATE_STATE=FAIL"
    ),
    (
        "PSEUDO_COHORT_ARCHITECTURE=PASS"
        if cohort_pass
        else
        "PSEUDO_COHORT_ARCHITECTURE=FAIL"
    ),
    "DIRECT_CEX_SCF_CPS_RECORD_LINKAGE=PROHIBITED",
    "",
    "===== K =====",
    "K_PRIMARY=FIN",
    "K_SENSITIVITY=LIQ,EQUITY,RETQLIQ",
    "K_NETWORTH_PRIMARY=PROHIBITED",
    "K_ASSET_PRIMARY=PROHIBITED",
    (
        "K_ARCHITECTURE=PASS"
        if k_pass
        else
        "K_ARCHITECTURE=FAIL"
    ),
    "",
    "===== D =====",
    "D_PRIMARY_RAW=PIRTOTAL",
    "D_PRIMARY_SIGN=-1",
    "D_SECONDARY_RAW=DEBT2INC",
    "D_SECONDARY_SIGN=-1",
    "D_MINUS_DEBT_DOLLARS_SOLE_PRIMARY=PROHIBITED",
    (
        "D_ARCHITECTURE=PASS"
        if d_pass
        else
        "D_ARCHITECTURE=FAIL"
    ),
    "",
    "===== I =====",
    "I_TEMPORAL_BASIS=PREVIOUS_YEAR_PRIMARY",
    "I_PRIMARY_WORK_ATTACHMENT=WEWKRS",
    "I_PRIMARY_SEARCH_BURDEN=WEUEMP",
    "I_CURRENT_WEEK_STATUS_PRIMARY=0",
    "I_SECONDARY_CODE_AUDIT_PENDING=WORKYN,WTEMP,WEXP,HRSWK",
    (
        "I_ARCHITECTURE=PASS"
        if i_pass
        else
        "I_ARCHITECTURE=FAIL"
    ),
    "",
    "===== RESOURCES =====",
    "RESOURCE_CANDIDATE=HTOTVAL",
    "HTOTVAL_IS_I=0",
    (
        "RESOURCE_VS_I_SEPARATION=PASS"
        if resource_pass
        else
        "RESOURCE_VS_I_SEPARATION=FAIL"
    ),
    "",
    "===== CPS ANCHOR =====",
    "CPS_REFERENCE_PERSON=A_EXPRRP_IN_1_2",
    "CPS_OWNER=H_TENURE_1",
    "CPS_RENTER=H_TENURE_2",
    "CPS_NO_CASH_RENT_PRIMARY=0",
    "CPS_WEIGHT=HSUP_WGT",
    (
        "CPS_PSEUDO_COHORT_ANCHOR=PASS"
        if cps_pass
        else
        "CPS_PSEUDO_COHORT_ANCHOR=FAIL"
    ),
    "",
    "===== SCF =====",
    "SCF_FIVE_IMPLICATES_REQUIRED=1",
    "SCF_IMPLICATES_AS_INDEPENDENT_FAMILIES=PROHIBITED",
    "SCF_SUMMARY_DOLLAR_BASIS=2022_REAL_DOLLARS",
    "SCF_SECOND_DEFLATION=PROHIBITED",
    (
        "SCF_INFERENCE_ARCHITECTURE=PASS"
        if scf_pass
        else
        "SCF_INFERENCE_ARCHITECTURE=FAIL"
    ),
    "",
    "===== DIMENSIONALITY =====",
    "DIFFERENT_VARIABLE_NAME_EQUALS_NEW_DIMENSION=0",
    "OWNER_RENTER_SIGNIFICANCE_EQUALS_NEW_DIMENSION=0",
    "CONSTRUCT_VALIDITY_REQUIRED=1",
    "NONDEGENERATE_VARIATION_REQUIRED=1",
    "NONREDUNDANT_MOVEMENT_REQUIRED=1",
    "ALTERNATE_PROXY_ROBUSTNESS_REQUIRED_WHERE_AVAILABLE=1",
    "DISTINCTNESS_NUMERICAL_GATES_OPENED=0",
    "DISTINCTNESS_GATES_MUST_PRECEDE_OUTCOME_OPEN=1",
    (
        "DIMENSIONALITY_FALSIFICATION_PRINCIPLE=PASS"
        if dimensionality_pass
        else
        "DIMENSIONALITY_FALSIFICATION_PRINCIPLE=FAIL"
    ),
    "",
    "===== H_ACCESS =====",
    "H_ACCESS_IMPLEMENTED=0",
    "HOUSES_RESERVED_FROM_K_PRIMARY=1",
    "HOMEEQ_RESERVED_FROM_K_PRIMARY=1",
    "",
    "===== REAL INFLATION =====",
    "STATE_CHANGE_EQUALS_COST_INFLATION=0",
    "OBSERVED_EXPENDITURE_CHANGE_EQUALS_INFLATION=0",
    "GE_EQUALS_REAL_INFLATION=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "",
    (
        "OFFICIAL_SOURCE_MANIFEST=PASS"
        if source_pass
        else
        "OFFICIAL_SOURCE_MANIFEST=FAIL"
    ),
    "",
    (
        "E4A_KDI_HOUSEHOLD_STATE_ARCHITECTURE=PASS"
        if overall
        else
        "E4A_KDI_HOUSEHOLD_STATE_ARCHITECTURE=FAIL"
    ),
    (
        "E4A1_SCF_CPS_KDI_SCHEMA_AUDIT_AUTHORIZED=1"
        if overall
        else
        "E4A1_SCF_CPS_KDI_SCHEMA_AUDIT_AUTHORIZED=0"
    ),
    "",
]


OUT.write_text(
    "\n".join(lines),
    encoding="utf-8",
)


print(
    "\n".join(lines)
)


if not overall:
    raise SystemExit(1)
