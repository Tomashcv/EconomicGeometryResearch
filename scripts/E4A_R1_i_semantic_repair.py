from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

UPSTREAM = (
    ROOT
    / "data/metadata/E4A1_scf_cps_kdi_schema_semantic_audit.txt"
)

ORIGINAL_ARCH = (
    ROOT
    / "data/metadata/E4A_kdi_household_state_architecture.json"
)

CPS_META = (
    ROOT
    / "data/metadata/E3B1_cps_2022_variables.json"
)

REPAIR = (
    ROOT
    / "data/metadata/E4A_R1_i_semantic_repair.json"
)

SEMANTIC = (
    ROOT
    / "data/metadata/E4A_R1_i_official_semantic_contract.tsv"
)

AUDIT = (
    ROOT
    / "data/metadata/E4A_R1_i_semantic_repair_audit.txt"
)


EXPECTED_SHA = {
    UPSTREAM:
        "6f223eda2647cb0d46e70dbc7c78ee0dbd55765b085340570d755dda5e2f499c",

    ORIGINAL_ARCH:
        "72f8967f5dd3be78bd5b3cb12e5ee0af249a2bfaae94d0312070f143c181b986",

    CPS_META:
        "9dfa693600835042231120b3e8ed8d14748f05a1a654595aa6870a522a3dc737"
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
# Preserve scientific failure
# =============================================================================

upstream_text = UPSTREAM.read_text(
    encoding="utf-8"
)


required_upstream = [
    "SCF_K_D_SCHEMA=PASS",
    "CPS_OFFICIAL_METADATA_VARIABLES=PASS",
    "E4A_WEWKRS_DIRECTION_SEMANTICS=FAIL",
    "E4A_WEUEMP_DIRECTION_SEMANTICS=FAIL",
    "E4A_I_PRIMARY_SEMANTICS=FAIL",
    "E4A1_SCF_CPS_KDI_SCHEMA_AUDIT=FAIL",
    "E4A_R1_I_SEMANTIC_REPAIR_AUTHORIZED=1",
]


for token in required_upstream:

    if token not in upstream_text:

        raise RuntimeError(
            f"missing upstream invariant={token}"
        )


# =============================================================================
# CPS official metadata availability
# =============================================================================

meta_obj = json.loads(
    CPS_META.read_text(
        encoding="utf-8"
    )
)


variables = meta_obj.get(
    "variables",
    meta_obj,
)


required_variables = {
    "WEWKRS",
    "WEUEMP",
    "WKSWORK",
    "WORKYN",
    "WRK_CK",
    "WTEMP",
    "LKNONE",
    "LKWEEKS",
    "NWLKWK",
    "NWLOOK",
    "PYRSN",
    "RSNNOTW",
    "HRSWK",

    "I_WKSWK",
    "I_LKWEEK",
    "I_NWLKWK",
    "I_NWLOOK",
    "I_WORKYN",
    "I_WTEMP",
}


missing_variables = sorted(
    required_variables
    - set(
        variables
    )
)


metadata_pass = (
    not missing_variables
)


# =============================================================================
# Semantic table
# =============================================================================

sem = pd.read_csv(
    SEMANTIC,
    sep="\t",
    dtype=str,
).fillna("")


expected_positions = {
    "HRSWK": ("296", "2"),
    "LKNONE": ("303", "1"),
    "LKWEEKS": ("305", "2"),
    "NWLKWK": ("309", "2"),
    "NWLOOK": ("311", "1"),
    "PYRSN": ("323", "1"),
    "RSNNOTW": ("324", "1"),
    "WEUEMP": ("333", "1"),
    "WEWKRS": ("334", "1"),
    "WKSWORK": ("338", "2"),
    "WORKYN": ("340", "1"),
    "WRK_CK": ("341", "1"),
    "WTEMP": ("342", "1"),
}


sem_lookup = {
    r["variable"]:
        (
            r["position"],
            r["length"],
        )
    for _, r in sem.iterrows()
}


semantic_position_pass = (
    sem_lookup
    == expected_positions
)


# =============================================================================
# Repaired machine contract
# =============================================================================

r = json.loads(
    REPAIR.read_text(
        encoding="utf-8"
    )
)


i = r["I"]


primary = {
    x["name"]:
        x
    for x in i[
        "primary_observables"
    ]
}


secondary = {
    x["name"]:
        x
    for x in i[
        "secondary_observables"
    ]
}


fyft_pass = (
    primary[
        "I_FYFT_SHARE"
    ][
        "source_variable"
    ] == "WEWKRS"
    and primary[
        "I_FYFT_SHARE"
    ][
        "operator"
    ] == "EQ"
    and primary[
        "I_FYFT_SHARE"
    ][
        "codes"
    ] == [1]
)


search_pass = (
    primary[
        "I_SEARCH_BURDEN_SHARE"
    ][
        "source_variable"
    ] == "WEUEMP"
    and primary[
        "I_SEARCH_BURDEN_SHARE"
    ][
        "operator"
    ] == "IN"
    and primary[
        "I_SEARCH_BURDEN_SHARE"
    ][
        "codes"
    ] == [
        2, 3, 4, 5, 6, 7
    ]
    and primary[
        "I_SEARCH_BURDEN_SHARE"
    ][
        "state_sign"
    ] == -1
)


long_search_pass = (
    secondary[
        "I_LONG_SEARCH_SHARE"
    ][
        "source_variable"
    ] == "WEUEMP"
    and secondary[
        "I_LONG_SEARCH_SHARE"
    ][
        "codes"
    ] == [6, 7]
)


any_work_pass = (
    secondary[
        "I_ANY_WORK_SHARE"
    ][
        "source_variable"
    ] == "WRK_CK"
    and secondary[
        "I_ANY_WORK_SHARE"
    ][
        "codes"
    ] == [1]
)


prohibition_pass = (
    set(
        i[
            "prohibited_numeric_treatments"
        ]
    )
    == {
        "MEAN_WEWKRS",
        "NUMERIC_MONOTONIC_WEWKRS",
        "MEAN_WEUEMP",
        "NUMERIC_MONOTONIC_WEUEMP",
    }
    and i[
        "cardinal_zero_from_niu"
    ] == "PROHIBITED"
)


cardinal_pass = (
    i[
        "cardinal_sensitivity_fields"
    ]
    == [
        "WKSWORK",
        "LKWEEKS",
        "NWLKWK",
    ]
)


reason_pass = (
    i[
        "reason_diagnostics_required"
    ]
    == [
        "PYRSN",
        "RSNNOTW",
    ]
)


scalar_pass = (
    i[
        "scalar_authorized"
    ] is False
)


k_d_unchanged_pass = (
    r["K"] == {
        "unchanged": True,
        "primary": "FIN",
        "sensitivities": [
            "LIQ",
            "EQUITY",
            "RETQLIQ",
        ],
    }
    and r["D"] == {
        "unchanged": True,
        "primary_raw": "PIRTOTAL",
        "primary_sign": -1,
        "secondary_raw": "DEBT2INC",
        "secondary_sign": -1,
    }
)


dim = r["dimensionality"]


dimensionality_pass = (
    dim[
        "K_empirically_tested"
    ] is False
    and dim[
        "D_empirically_tested"
    ] is False
    and dim[
        "I_empirically_tested"
    ] is False
    and dim[
        "five_dimensionality_proven"
    ] is False
)


overall = all([
    metadata_pass,
    semantic_position_pass,
    fyft_pass,
    search_pass,
    long_search_pass,
    any_work_pass,
    prohibition_pass,
    cardinal_pass,
    reason_pass,
    scalar_pass,
    k_d_unchanged_pass,
    dimensionality_pass,
])


lines = [
    "=" * 100,
    "E4A R1 — I SEMANTIC REPAIR",
    "=" * 100,
    "",
    "CPS_DATA_ROWS_PARSED=0",
    "CPS_I_VALUES_READ=0",
    "SCF_DATA_ROWS_PARSED=0",
    "SCF_K_VALUES_READ=0",
    "SCF_D_VALUES_READ=0",
    "",
    "===== ORIGINAL SCIENTIFIC RESULT =====",
    "E4A1_SCF_CPS_KDI_SCHEMA_AUDIT=FAIL",
    "E4A_I_PRIMARY_SEMANTICS=FAIL",
    "ORIGINAL_E4A1_FAIL=PRESERVED",
    "",
    "===== K / D =====",
    "SCF_K_D_SCHEMA=PASS",
    "K_PRIMARY=FIN",
    "D_PRIMARY_RAW=PIRTOTAL",
    "K_D_ARCHITECTURE_CHANGED=0",
    (
        "K_D_PRESERVATION=PASS"
        if k_d_unchanged_pass
        else
        "K_D_PRESERVATION=FAIL"
    ),
    "",
    "===== CPS REPAIRED I =====",
    (
        "REPAIRED_I_REQUIRED_METADATA=PASS"
        if metadata_pass
        else
        "REPAIRED_I_REQUIRED_METADATA=FAIL"
    ),
    (
        "OFFICIAL_FIXED_WIDTH_SEMANTICS=PASS"
        if semantic_position_pass
        else
        "OFFICIAL_FIXED_WIDTH_SEMANTICS=FAIL"
    ),
    "",
    "I_PRIMARY_1=I_FYFT_SHARE",
    "I_FYFT_FORMULA=WEWKRS_EQ_1",
    (
        "I_FYFT_SEMANTICS=PASS"
        if fyft_pass
        else
        "I_FYFT_SEMANTICS=FAIL"
    ),
    "",
    "I_PRIMARY_2=I_SEARCH_BURDEN_SHARE",
    "I_SEARCH_FORMULA=WEUEMP_IN_2_3_4_5_6_7",
    "I_SEARCH_STATE_SIGN=-1",
    (
        "I_SEARCH_SEMANTICS=PASS"
        if search_pass
        else
        "I_SEARCH_SEMANTICS=FAIL"
    ),
    "",
    "I_SECONDARY_LONG_SEARCH=WEUEMP_IN_6_7",
    "I_SECONDARY_ANY_WORK=WRK_CK_EQ_1",
    "",
    "WEWKRS_NUMERIC_MEAN=PROHIBITED",
    "WEUEMP_NUMERIC_MEAN=PROHIBITED",
    "CARDINAL_NIU_EQUALS_ZERO=PROHIBITED",
    "",
    "I_CARDINAL_SENSITIVITY=WKSWORK,LKWEEKS,NWLKWK",
    "I_REASON_DIAGNOSTICS=PYRSN,RSNNOTW",
    "I_HRSWK_PRIMARY=0",
    "",
    "I_SCALAR_AUTHORIZED=0",
    "",
    "===== DIMENSIONALITY =====",
    "K_EMPIRICALLY_TESTED=0",
    "D_EMPIRICALLY_TESTED=0",
    "I_EMPIRICALLY_TESTED=0",
    "FIVE_DIMENSIONALITY_PROVEN=0",
    "",
    "K_D_I_ECONOMIC_VALUES_OPENED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "",
    (
        "E4A_R1_I_SEMANTIC_REPAIR=PASS"
        if overall
        else
        "E4A_R1_I_SEMANTIC_REPAIR=FAIL"
    ),
    (
        "E4A2_KDI_ESTIMATOR_PREFLIGHT_AUTHORIZED=1"
        if overall
        else
        "E4A2_KDI_ESTIMATOR_PREFLIGHT_AUTHORIZED=0"
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
