from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

R1 = ROOT / "data/metadata/E4A_R1_i_semantic_repair_audit.txt"
R1_CONTRACT = ROOT / "data/metadata/E4A_R1_i_semantic_repair.json"

E4A1_SCHEMA = ROOT / "data/metadata/E4A1_local_schema_audit.tsv"
E4A1_HASHES = ROOT / "data/metadata/E4A1_local_source_hashes.tsv"

CONTRACT = ROOT / "data/metadata/E4A2_kdi_estimator_contract.json"
SOURCES = ROOT / "data/metadata/E4A2_official_inference_source_manifest.tsv"

SCF_MAIN = ROOT / "data/raw/scf/2022/scf2022s.zip"
SCF_SUM = ROOT / "data/raw/scf/2022/scfp2022s.zip"
CPS_MAIN = ROOT / "data/raw/cps_asec/2022/asec2022_pubuse.zip"

SCF_REP = ROOT / "data/raw/scf/2022/scf2022rw1s.zip"
CPS_REP = ROOT / "data/raw/cps_asec/2022/CPS_ASEC_ASCII_REPWGT_2022.ZIP"

AUDIT = ROOT / "data/metadata/E4A2_kdi_estimator_preflight_audit.txt"


EXPECTED_SHA = {
    R1:
        "b6f66e473979b6f3ff55e3a9a853d62a89396e3fbbfe90344b3a9c7f236ecb1f",

    R1_CONTRACT:
        "26cd1ccdc183cbb02df6fb63f598c01df5c3a1ed7d34a918bf4e4f6fb5b00e03",

    E4A1_SCHEMA:
        "7e6b62f0b0cce046c9f56a17020106659ab1eaefc091c7de25caab1f1457b97f",

    E4A1_HASHES:
        "65823dbd0a2d4e86f3aad3a10e4da5aef9f8c2af523cdd3ea7721df93bc754e2",

    CPS_MAIN:
        "61b6b6ba8ae70eb1b37acca8144163bb5c260d742b33152c639bebccc0a1fbb5",

    SCF_MAIN:
        "409e6811df895766d50b2f597c10b1b3c5813e7d3e0e45d910ad26c0cb07f4eb",

    SCF_SUM:
        "3bb4d890ae2463ff6039ec7692e375f544dd98a55a37ca2cb2340354b9cc9d80",
}


def sha256(path: Path) -> str:

    h = hashlib.sha256()

    with path.open("rb") as f:

        for block in iter(
            lambda: f.read(1024 * 1024),
            b"",
        ):
            h.update(block)

    return h.hexdigest()


for path, expected in EXPECTED_SHA.items():

    actual = sha256(path)

    if actual != expected:

        raise RuntimeError(
            f"SHA mismatch {path}: {actual}"
        )


# =============================================================================
# Upstream repaired I semantics
# =============================================================================

r1_text = R1.read_text(
    encoding="utf-8"
)

for token in (
    "E4A_R1_I_SEMANTIC_REPAIR=PASS",
    "E4A2_KDI_ESTIMATOR_PREFLIGHT_AUTHORIZED=1",
    "SCF_K_D_SCHEMA=PASS",
    "K_D_PRESERVATION=PASS",
    "I_FYFT_SEMANTICS=PASS",
    "I_SEARCH_SEMANTICS=PASS",
    "I_SCALAR_AUTHORIZED=0",
    "FIVE_DIMENSIONALITY_PROVEN=0",
):

    if token not in r1_text:

        raise RuntimeError(
            f"missing upstream invariant={token}"
        )


# =============================================================================
# Existing schema must still contain required fields
# =============================================================================

schema = pd.read_csv(
    E4A1_SCHEMA,
    sep="\t",
    dtype=str,
).fillna("")


def present(source: str, variable: str) -> bool:

    x = schema[
        (schema["source"] == source)
        & (schema["variable"] == variable)
    ]

    return (
        len(x) == 1
        and x.iloc[0]["present"] == "1"
        and x.iloc[0]["economic_value_read"] == "0"
    )


scf_schema_pass = all(
    present(
        "SCF_SUMMARY",
        v,
    )
    for v in (
        "FIN",
        "LIQ",
        "EQUITY",
        "RETQLIQ",
        "PIRTOTAL",
        "DEBT2INC",
        "DEBT",
        "Y1",
        "YY1",
    )
)


scf_full_pass = all(
    present(
        "SCF_FULL",
        v,
    )
    for v in (
        "Y1",
        "X42001",
        "X14",
        "X508",
        "X601",
        "X701",
        "X7133",
    )
)


cps_e4a1_schema_pass = all(
    present(
        "CPS_ASEC_METADATA",
        v,
    )
    for v in (
        "A_AGE",
        "A_EXPRRP",
        "HSUP_WGT",
        "H_TENURE",
        "WEWKRS",
        "WEUEMP",
    )
)


# WRK_CK was added to the repaired I architecture after E4A1.
# Its metadata availability was explicitly validated in E4A R1
# against the frozen official CPS metadata file.
cps_r1_wrk_ck_pass = (
    "REPAIRED_I_REQUIRED_METADATA=PASS"
    in r1_text
    and
    "I_SECONDARY_ANY_WORK=WRK_CK_EQ_1"
    in r1_text
)


cps_schema_pass = (
    cps_e4a1_schema_pass
    and cps_r1_wrk_ck_pass
)


# =============================================================================
# Contract
# =============================================================================

c = json.loads(
    CONTRACT.read_text(
        encoding="utf-8"
    )
)


scf = c["SCF"]
cps = c["CPS_ASEC"]


scf_point_pass = (
    scf["point_estimation"]["implicates"]
    == [1, 2, 3, 4, 5]
    and scf["point_estimation"]["weight"]
    == "X42001"
    and scf["point_estimation"]["method"]
    == "ESTIMATE_SEPARATELY_PER_IMPLICATE_THEN_MEAN_5"
)


k_pass = (
    scf["K"]["primary_variable"]
    == "FIN"
    and scf["K"]["primary_statistic"]
    == "WEIGHTED_MEAN"
    and scf["K"]["sensitivities"]
    == [
        "LIQ",
        "EQUITY",
        "RETQLIQ",
    ]
    and scf["K"][
        "median_FIN_robustness_required_before_dimensionality_claim"
    ] is True
)


d_pass = (
    scf["D"]["primary_variable"]
    == "PIRTOTAL"
    and scf["D"]["primary_statistic"]
    == "WEIGHTED_MEAN"
    and scf["D"]["primary_state_sign"]
    == -1
    and scf["D"]["secondary_variable"]
    == "DEBT2INC"
    and scf["D"]["secondary_state_sign"]
    == -1
    and scf["D"]["DEBT_dollars_primary"]
    is False
)


scf_contrast_pass = (
    scf["contrast"]["owner_renter_difference"]
    == "DIRECT_WITHIN_EACH_IMPLICATE_THEN_MEAN_5"
)


scf_inference_pass = (
    scf["inference"]["bootstrap_replicates_required"]
    == 999
    and scf["inference"]["sampling_variance_first_implicate"]
    is True
    and scf["inference"]["imputation_variance_all_five_implicates"]
    is True
    and scf["inference"]["both_sampling_and_imputation_required"]
    is True
    and scf["inference"][
        "exact_sampling_formula_pending_official_2022_repweight_schema_audit"
    ] is True
)


cps_point_pass = (
    cps["unit"]
    == "REFERENCE_PERSON_HOUSEHOLD"
    and cps["reference_person_codes"]
    == [1, 2]
    and cps["point_weight"]
    == "HSUP_WGT"
    and cps["denominator"]
    == "ALL_VALID_FROZEN_COHORT_REFERENCE_PERSON_HOUSEHOLDS"
)


fyft = cps["I_FYFT_SHARE"]

fyft_pass = (
    fyft["variable"]
    == "WEWKRS"
    and fyft["codes"]
    == [1]
    and fyft["statistic"]
    == "WEIGHTED_SHARE"
)


search = cps["I_SEARCH_BURDEN_SHARE"]

search_pass = (
    search["variable"]
    == "WEUEMP"
    and search["codes"]
    == [2, 3, 4, 5, 6, 7]
    and search["statistic"]
    == "WEIGHTED_SHARE"
    and search["state_sign"]
    == -1
)


rep = cps["replicate_inference"]

cps_inference_pass = (
    rep["replicate_count"]
    == 160
    and rep["variance_formula"]
    == "(4/160)*SUM((THETA_R-THETA_0)^2)"
    and rep[
        "numerator_and_denominator_same_replicate_weight"
    ] is True
    and rep[
        "owner_renter_difference_direct_within_replicate"
    ] is True
    and rep[
        "independent_standard_error_shortcut"
    ] == "PROHIBITED"
    and rep[
        "exact_repweight_field_names_pending_schema_audit"
    ] is True
    and rep[
        "exact_merge_keys_pending_official_instruction_audit"
    ] is True
)


# =============================================================================
# Official-source manifest
# =============================================================================

source_df = pd.read_csv(
    SOURCES,
    sep="\t",
    dtype=str,
).fillna("")


required_source_ids = {
    "SCF_FAQ",
    "SCF_2022",
    "SCF_SE_DOC",
    "SCF_REPWEIGHT",
    "CPS_2022",
    "CPS_TECH",
    "CPS_REPWEIGHT",
    "CPS_REP_INSTRUCTIONS",
}


source_pass = (
    set(source_df["source_id"])
    == required_source_ids
)


# =============================================================================
# Local replicate asset availability — existence only
# =============================================================================

scf_rep_local = SCF_REP.is_file()
cps_rep_local = CPS_REP.is_file()


# This is not a failure of estimator architecture.
# It determines the next workstream.
replicate_acquisition_required = (
    not scf_rep_local
    or not cps_rep_local
)


# =============================================================================
# Scientific boundary
# =============================================================================

dim = c["dimensionality"]

dimensionality_pass = (
    dim["K_empirically_tested"] is False
    and dim["D_empirically_tested"] is False
    and dim["I_empirically_tested"] is False
    and dim["five_dimensionality_proven"] is False
)


overall = all([
    scf_schema_pass,
    scf_full_pass,
    cps_schema_pass,
    scf_point_pass,
    k_pass,
    d_pass,
    scf_contrast_pass,
    scf_inference_pass,
    cps_point_pass,
    fyft_pass,
    search_pass,
    cps_inference_pass,
    source_pass,
    dimensionality_pass,
])


lines = [
    "=" * 100,
    "E4A2 — K / D / I EXACT ESTIMATOR + INFERENCE PREFLIGHT",
    "=" * 100,
    "",
    "SCF_DATA_ROWS_PARSED=0",
    "SCF_K_D_VALUES_READ=0",
    "SCF_REPLICATE_VALUES_READ=0",
    "CPS_DATA_ROWS_PARSED=0",
    "CPS_I_VALUES_READ=0",
    "CPS_REPLICATE_VALUES_READ=0",
    "",
    "===== SOURCE SCHEMA =====",
    (
        "SCF_FULL_REQUIRED_SCHEMA=PASS"
        if scf_full_pass
        else
        "SCF_FULL_REQUIRED_SCHEMA=FAIL"
    ),
    (
        "SCF_K_D_REQUIRED_SCHEMA=PASS"
        if scf_schema_pass
        else
        "SCF_K_D_REQUIRED_SCHEMA=FAIL"
    ),
    (
        "CPS_I_REQUIRED_SCHEMA=PASS"
        if cps_schema_pass
        else
        "CPS_I_REQUIRED_SCHEMA=FAIL"
    ),
    "",
    "===== SCF POINT ESTIMATION =====",
    "SCF_IMPLICATES=1,2,3,4,5",
    "SCF_POINT_WEIGHT=X42001",
    "SCF_POINT_METHOD=PER_IMPLICATE_THEN_MEAN_5",
    (
        "SCF_POINT_ESTIMATOR_CONTRACT=PASS"
        if scf_point_pass
        else
        "SCF_POINT_ESTIMATOR_CONTRACT=FAIL"
    ),
    "",
    "K_PRIMARY_VARIABLE=FIN",
    "K_PRIMARY_STATISTIC=WEIGHTED_MEAN",
    "K_FIN_WEIGHTED_MEDIAN_ROBUSTNESS_REQUIRED=1",
    "K_SENSITIVITY=LIQ,EQUITY,RETQLIQ",
    (
        "K_ESTIMATOR_CONTRACT=PASS"
        if k_pass
        else
        "K_ESTIMATOR_CONTRACT=FAIL"
    ),
    "",
    "D_PRIMARY_VARIABLE=PIRTOTAL",
    "D_PRIMARY_STATISTIC=WEIGHTED_MEAN",
    "D_PRIMARY_STATE_SIGN=-1",
    "D_SECONDARY_VARIABLE=DEBT2INC",
    "D_SECONDARY_STATE_SIGN=-1",
    (
        "D_ESTIMATOR_CONTRACT=PASS"
        if d_pass
        else
        "D_ESTIMATOR_CONTRACT=FAIL"
    ),
    "",
    "SCF_OWNER_RENTER_DIFFERENCE=DIRECT_WITHIN_IMPLICATE",
    (
        "SCF_CONTRAST_CONTRACT=PASS"
        if scf_contrast_pass
        else
        "SCF_CONTRAST_CONTRACT=FAIL"
    ),
    "",
    "===== SCF INFERENCE =====",
    "SCF_BOOTSTRAP_REPLICATES_REQUIRED=999",
    "SCF_SAMPLING_VARIANCE_FIRST_IMPLICATE=1",
    "SCF_IMPUTATION_VARIANCE_FIVE_IMPLICATES=1",
    "SCF_SAMPLING_AND_IMPUTATION_BOTH_REQUIRED=1",
    "SCF_EXACT_VARIANCE_FORMULA_PENDING_2022_REPWEIGHT_AUDIT=1",
    (
        "SCF_INFERENCE_PREFLIGHT=PASS"
        if scf_inference_pass
        else
        "SCF_INFERENCE_PREFLIGHT=FAIL"
    ),
    "",
    "===== CPS I POINT ESTIMATION =====",
    "CPS_POINT_WEIGHT=HSUP_WGT",
    "CPS_I_DENOMINATOR=ALL_FROZEN_COHORT_REFERENCE_PERSON_HOUSEHOLDS",
    "I_FYFT_SHARE=WEWKRS_EQ_1",
    "I_SEARCH_BURDEN_SHARE=WEUEMP_IN_2_3_4_5_6_7",
    "I_SEARCH_STATE_SIGN=-1",
    (
        "CPS_I_POINT_ESTIMATOR_CONTRACT=PASS"
        if all([
            cps_point_pass,
            fyft_pass,
            search_pass,
        ])
        else
        "CPS_I_POINT_ESTIMATOR_CONTRACT=FAIL"
    ),
    "",
    "===== CPS INFERENCE =====",
    "CPS_REPLICATE_COUNT=160",
    "CPS_VARIANCE_FORMULA=(4/160)*SUM((THETA_R-THETA_0)^2)",
    "CPS_REPLICATE_NUMERATOR_DENOMINATOR_WEIGHT_MATCH=REQUIRED",
    "CPS_OWNER_RENTER_DIFFERENCE_REPLICATE=DIRECT",
    "CPS_INDEPENDENT_SE_SHORTCUT=PROHIBITED",
    (
        "CPS_INFERENCE_PREFLIGHT=PASS"
        if cps_inference_pass
        else
        "CPS_INFERENCE_PREFLIGHT=FAIL"
    ),
    "",
    "===== LOCAL REPLICATE ASSETS =====",
    f"SCF_REPLICATE_WEIGHT_FILE_LOCAL={int(scf_rep_local)}",
    f"CPS_REPLICATE_WEIGHT_FILE_LOCAL={int(cps_rep_local)}",
    (
        "REPLICATE_WEIGHT_ACQUISITION_REQUIRED=1"
        if replicate_acquisition_required
        else
        "REPLICATE_WEIGHT_ACQUISITION_REQUIRED=0"
    ),
    "",
    "K_VALUES_OPEN_AUTHORIZED=0",
    "D_VALUES_OPEN_AUTHORIZED=0",
    "I_VALUES_OPEN_AUTHORIZED=0",
    "K_D_I_INFERENCE_AUTHORIZED=0",
    "",
    "K_EMPIRICALLY_TESTED=0",
    "D_EMPIRICALLY_TESTED=0",
    "I_EMPIRICALLY_TESTED=0",
    "FIVE_DIMENSIONALITY_PROVEN=0",
    "",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "",
    (
        "OFFICIAL_INFERENCE_SOURCE_MANIFEST=PASS"
        if source_pass
        else
        "OFFICIAL_INFERENCE_SOURCE_MANIFEST=FAIL"
    ),
    "",
    (
        "E4A2_KDI_ESTIMATOR_PREFLIGHT=PASS"
        if overall
        else
        "E4A2_KDI_ESTIMATOR_PREFLIGHT=FAIL"
    ),
    (
        "E4A2A_REPLICATE_WEIGHT_ACQUISITION_SCHEMA_AUDIT_AUTHORIZED=1"
        if overall
        else
        "E4A2A_REPLICATE_WEIGHT_ACQUISITION_SCHEMA_AUDIT_AUTHORIZED=0"
    ),
    "",
]


AUDIT.write_text(
    "\n".join(lines),
    encoding="utf-8",
)


print(
    "\n".join(lines)
)


if not overall:
    raise SystemExit(1)
