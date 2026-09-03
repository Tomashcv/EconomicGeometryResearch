from __future__ import annotations

import hashlib
import json
import math
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np

from E4A2C_cps_replicate_engine import (
    ASEC_VARIANCE_FACTOR,
    REPLICATE_COUNT,
    asec_variance,
    owner_renter_difference_with_replicates,
    weighted_share,
    weighted_share_with_replicates,
)


ROOT = Path(__file__).resolve().parents[1]

CONTRACT = (
    ROOT
    / "data/metadata/E4A2C_cps_replicate_engine_contract.json"
)

E3A4_MAPPING = ROOT / "data/metadata/E3A4_mapping.tsv"

E4A2_CONTRACT = ROOT / "data/metadata/E4A2_kdi_estimator_contract.json"
E4A2_AUDIT = ROOT / "data/metadata/E4A2_kdi_estimator_preflight_audit.txt"

E4A2A_AUDIT = ROOT / "data/metadata/E4A2A_replicate_weight_schema_audit.txt"
E4A2A_SCHEMA = ROOT / "data/metadata/E4A2A_replicate_weight_schema.tsv"

E4A2B_CONTRACT = ROOT / "data/metadata/E4A2B_cps_full_weight_bridge_contract.json"
E4A2B_AUDIT = ROOT / "data/metadata/E4A2B_cps_full_weight_bridge_audit.txt"
E4A2B_SUMMARY = ROOT / "data/metadata/E4A2B_cps_full_weight_bridge_summary.tsv"

INSTRUCTIONS = (
    ROOT
    / "data/raw/cps_asec/2022/2022_ASEC_Replicate_Weight_Usage_Instructions.docx"
)

ENGINE = ROOT / "scripts/E4A2C_cps_replicate_engine.py"

AUDIT = (
    ROOT
    / "data/metadata/E4A2C_cps_replicate_engine_contract_audit.txt"
)

CHECKS = (
    ROOT
    / "data/metadata/E4A2C_synthetic_engine_checks.tsv"
)


EXPECTED_SHA = {
    E3A4_MAPPING:
        "12783a626edf3af3b8dccadfbe3d084c1b2af493a1e51966a963b20226f1c97e",

    E4A2_CONTRACT:
        "40c85c629285e7cf0999250914d7928b9825047682bf41362327060adaef4f0a",

    E4A2_AUDIT:
        "9998c60b281874d15be0c01578abd7a5bb39a05f27b4d2971d7244987fbba24c",

    E4A2A_AUDIT:
        "ebf719755fbe7d0f6c5b0023f3900d435228b2e36d97f1e9a7da3fc4fe76b546",

    E4A2A_SCHEMA:
        "88125ae7eae4edb3ca7a38d37e74eeec99b6a9877aac20865c2b08d2bf25f85e",

    E4A2B_CONTRACT:
        "52fb6ef530fc43c535b51fc74e06d81c3e72b393d03daafc232ac73c5e78ce00",

    E4A2B_AUDIT:
        "962b727559808c389afac33060a4562bead5099be6000b951af796a1ac37be2e",

    E4A2B_SUMMARY:
        "475ba266f163b2e08fff3256567bd563c3cc17c4826240a8429275cdb2fc62bb",

    INSTRUCTIONS:
        "981043658928c925507e376625d313a7d6d7b473298c0468a20a3448a4236f63",
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
    if not path.is_file():
        raise RuntimeError(f"missing required file={path}")

    actual = sha256(path)

    if actual != expected:
        raise RuntimeError(
            f"SHA mismatch {path}: expected={expected} actual={actual}"
        )


upstream_b = E4A2B_AUDIT.read_text(encoding="utf-8")

for token in (
    "E4A2B_WEIGHT_BRIDGE_AUDIT=PASS",
    "E4A2C_CPS_REPLICATE_ENGINE_PREFLIGHT_AUTHORIZED=1",
    "CPS_HOUSEHOLD_FULL_WEIGHT_BRIDGE=PASS",
    "CPS_HSUP_WGT_MARSUPWT_EXACT_IDENTITY=PASS",
    "CPS_PWWGT0_MARSUPWT_PRECISION_BRIDGE=PASS",
):
    if token not in upstream_b:
        raise RuntimeError(
            f"missing E4A2B upstream invariant={token}"
        )


upstream_a = E4A2A_AUDIT.read_text(encoding="utf-8")

for token in (
    "CPS_REPLICATE_COUNT=160",
    "CPS_REPLICATE_WEIGHTS=PWWGT1_PWWGT160",
    "CPS_REPLICATE_MERGE_SCHEMA=PASS",
):
    if token not in upstream_a:
        raise RuntimeError(
            f"missing E4A2A upstream invariant={token}"
        )


# =============================================================================
# Official instruction anchors
# =============================================================================

with zipfile.ZipFile(INSTRUCTIONS) as zf:
    xml = zf.read("word/document.xml")

root = ET.fromstring(xml)

W_NS = {
    "w":
        "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
}

paragraphs = []

for p in root.findall(".//w:p", W_NS):
    text = "".join(
        t.text or ""
        for t in p.findall(".//w:t", W_NS)
    ).strip()

    if text:
        paragraphs.append(text)

instruction_text = re.sub(
    r"\s+",
    " ",
    " ".join(paragraphs),
).strip()


negative_weight_doc_pass = (
    "may result in negative weights for some cases"
    in instruction_text
)

variance_only_doc_pass = (
    "should be used in creating variances only"
    in instruction_text
    and
    "should not be used to create independent estimates"
    in instruction_text
)

merge_doc_pass = all(
    phrase in instruction_text
    for phrase in (
        "A_EXPRRP = 1 or 2",
        "H_HHTYPE = 1",
        "PPPOS = 41",
    )
)

formula_doc_pass = (
    "(4/160) * sdiffsq"
    in instruction_text
)


# =============================================================================
# Machine contract
# =============================================================================

contract = json.loads(
    CONTRACT.read_text(encoding="utf-8")
)

expected_replicates = [
    f"PWWGT{i}"
    for i in range(1, 161)
]

replicate_contract_pass = (
    contract["parent_commit"] == "4235083"
    and
    contract["replicate_design"]["replicate_count"] == 160
    and
    contract["replicate_design"]["replicate_weights"]
    == expected_replicates
    and
    len(
        set(
            contract["replicate_design"]["replicate_weights"]
        )
    ) == 160
    and
    contract["replicate_design"]["variance_formula"]
    == "(4/160)*SUM((THETA_R-THETA_0)^2)"
    and
    contract["replicate_design"][
        "same_replicate_weight_for_numerator_and_denominator"
    ] is True
    and
    contract["replicate_design"][
        "full_sample_denominator_reuse_inside_replicate"
    ] is False
    and
    contract["replicate_design"]["negative_replicate_weights"]
    == "PERMITTED_OFFICIAL_DESIGN"
    and
    contract["replicate_design"]["negative_replicate_weight_clipping"]
    == "PROHIBITED"
)

full_sample_contract_pass = (
    contract["full_sample"]["point_weight"] == "HSUP_WGT"
    and
    contract["full_sample"]["PWWGT0_role"]
    == "MERGE_AND_PRECISION_BRIDGE_VERIFICATION_ONLY"
    and
    contract["full_sample"][
        "replicate_weights_for_independent_point_estimates"
    ] is False
)

estimand_contract_pass = (
    contract["estimands"]
    == {
        "I_FYFT_SHARE": {
            "variable": "WEWKRS",
            "indicator_codes": [1],
            "state_sign": 1,
            "role": "PRIMARY",
        },
        "I_SEARCH_BURDEN_SHARE": {
            "variable": "WEUEMP",
            "indicator_codes": [2, 3, 4, 5, 6, 7],
            "state_sign": -1,
            "role": "PRIMARY",
        },
        "I_LONG_SEARCH_SHARE": {
            "variable": "WEUEMP",
            "indicator_codes": [6, 7],
            "state_sign": -1,
            "role": "SECONDARY",
        },
        "I_ANY_WORK_SHARE": {
            "variable": "WRK_CK",
            "indicator_codes": [1],
            "state_sign": 1,
            "role": "SECONDARY",
        },
    }
)

cohort_contract_pass = (
    contract["cohorts"]["age_bands"]
    == {
        "AGE25_34": [25, 34],
        "AGE35_44": [35, 44],
        "AGE45_54": [45, 54],
        "AGE55_64": [55, 64],
    }
    and
    contract["cohorts"]["tenure"]
    == {
        "OWNER": "H_TENURE_EQ_1",
        "RENTER": "H_TENURE_EQ_2",
    }
    and
    contract["cohorts"]["other_tenure_excluded"] is True
)

execution_shape_pass = (
    contract["first_execution_shape"]
    == {
        "cohort_count": 8,
        "estimand_count": 4,
        "full_sample_cohort_estimand_rows": 32,
        "replicate_cohort_estimand_rows": 5120,
        "age_band_owner_renter_difference_rows": 16,
        "replicate_difference_rows": 2560,
    }
)

no_outcome_gate_pass = (
    contract["first_execution_gates"]["structural_only"] is True
    and
    contract["first_execution_gates"]["sign_gate"] is False
    and
    contract["first_execution_gates"]["magnitude_gate"] is False
    and
    contract["first_execution_gates"][
        "standard_error_magnitude_gate"
    ] is False
    and
    contract["first_execution_gates"]["significance_gate"] is False
    and
    contract["first_execution_gates"]["dimensionality_gate"] is False
)


# =============================================================================
# Synthetic executable tests
# =============================================================================

checks: list[tuple[str, bool]] = []


def record(name: str, passed: bool) -> None:
    checks.append((name, bool(passed)))


# ----- exact constants

record(
    "REPLICATE_COUNT_CONSTANT",
    REPLICATE_COUNT == 160,
)

record(
    "ASEC_VARIANCE_FACTOR_CONSTANT",
    math.isclose(
        ASEC_VARIANCE_FACTOR,
        4.0 / 160.0,
        rel_tol=0.0,
        abs_tol=0.0,
    ),
)


# ----- base fixture

z = np.array(
    [1, 0, 1, 0, 1, 0, 0, 1],
    dtype=float,
)

w0 = np.array(
    [2, 1, 3, 4, 2, 5, 3, 2],
    dtype=float,
)

manual_theta0 = (
    sum(float(a * b) for a, b in zip(z, w0))
    /
    sum(float(x) for x in w0)
)

engine_theta0 = weighted_share(z, w0)

record(
    "FULL_SAMPLE_WEIGHTED_SHARE_ORACLE",
    math.isclose(
        engine_theta0,
        manual_theta0,
        rel_tol=0.0,
        abs_tol=1e-15,
    ),
)


# ----- zero variance when every replicate equals full sample

wr_equal = np.repeat(
    w0[:, None],
    160,
    axis=1,
)

equal_inf = weighted_share_with_replicates(
    z,
    w0,
    wr_equal,
)

record(
    "ZERO_VARIANCE_EQUAL_REPLICATES",
    equal_inf.variance == 0.0
    and
    equal_inf.standard_error == 0.0
    and
    np.array_equal(
        equal_inf.replicate_estimates,
        np.repeat(equal_inf.theta0, 160),
    ),
)


# ----- controlled replicate fixture, including negative replicate weights

wr = wr_equal.copy()

# Replicate 1: one negative case weight, but positive domain total.
wr[:, 0] = np.array(
    [3.0, -0.5, 4.0, 3.0, 1.5, 5.0, 2.0, 2.0]
)

# Replicate 2: change both numerator and denominator structure.
wr[:, 1] = np.array(
    [1.0, 2.0, 5.0, 1.0, 2.0, 6.0, 4.0, 1.0]
)

# Replicate 3: another correlated perturbation.
wr[:, 2] = np.array(
    [4.0, 0.5, 2.0, 5.0, 3.0, 3.0, 2.0, 3.0]
)

controlled = weighted_share_with_replicates(
    z,
    w0,
    wr,
)

manual_reps = []

for r in range(160):
    col = wr[:, r]

    denominator = sum(float(x) for x in col)
    numerator = sum(
        float(a * b)
        for a, b in zip(z, col)
    )

    manual_reps.append(
        numerator / denominator
    )

manual_reps = np.asarray(
    manual_reps,
    dtype=float,
)

record(
    "REPLICATE_SHARE_ORACLE",
    np.allclose(
        controlled.replicate_estimates,
        manual_reps,
        rtol=0.0,
        atol=1e-15,
    ),
)

manual_variance = (
    (4.0 / 160.0)
    * float(
        np.sum(
            (manual_reps - manual_theta0) ** 2
        )
    )
)

record(
    "ASEC_VARIANCE_ORACLE",
    math.isclose(
        controlled.variance,
        manual_variance,
        rel_tol=0.0,
        abs_tol=1e-15,
    ),
)


# ----- negative weights are preserved, not clipped

rep0_manual_with_negative = (
    float(np.dot(z, wr[:, 0]))
    /
    float(np.sum(wr[:, 0]))
)

rep0_clipped_weights = np.maximum(
    wr[:, 0],
    0.0,
)

rep0_if_illegally_clipped = (
    float(np.dot(z, rep0_clipped_weights))
    /
    float(np.sum(rep0_clipped_weights))
)

negative_preserved = (
    math.isclose(
        controlled.replicate_estimates[0],
        rep0_manual_with_negative,
        rel_tol=0.0,
        abs_tol=1e-15,
    )
    and
    not math.isclose(
        controlled.replicate_estimates[0],
        rep0_if_illegally_clipped,
        rel_tol=0.0,
        abs_tol=1e-15,
    )
)

record(
    "NEGATIVE_REPLICATE_WEIGHT_PRESERVED",
    negative_preserved,
)


# ----- share is invariant to common scaling inside one replicate

scaled = wr.copy()
scaled[:, 1] *= 7.25

scaled_inf = weighted_share_with_replicates(
    z,
    w0,
    scaled,
)

record(
    "REPLICATE_COMMON_SCALE_INVARIANCE",
    math.isclose(
        scaled_inf.replicate_estimates[1],
        controlled.replicate_estimates[1],
        rel_tol=0.0,
        abs_tol=1e-15,
    ),
)


# ----- this also catches illegal full-sample denominator reuse

illegal_full_denominator_rep0 = (
    float(np.dot(z, wr[:, 0]))
    /
    float(np.sum(w0))
)

record(
    "REPLICATE_DENOMINATOR_RECOMPUTED",
    not math.isclose(
        controlled.replicate_estimates[0],
        illegal_full_denominator_rep0,
        rel_tol=0.0,
        abs_tol=1e-15,
    ),
)


# ----- direct owner-renter difference

owner = np.array(
    [1, 1, 1, 1, 0, 0, 0, 0],
    dtype=bool,
)

renter = ~owner

difference = owner_renter_difference_with_replicates(
    z,
    owner,
    renter,
    w0,
    wr,
)

owner_manual_0 = weighted_share(
    z[owner],
    w0[owner],
)

renter_manual_0 = weighted_share(
    z[renter],
    w0[renter],
)

manual_delta0 = (
    renter_manual_0
    - owner_manual_0
)

manual_delta_reps = []

for r in range(160):
    owner_r = weighted_share(
        z[owner],
        wr[owner, r],
    )

    renter_r = weighted_share(
        z[renter],
        wr[renter, r],
    )

    manual_delta_reps.append(
        renter_r - owner_r
    )

manual_delta_reps = np.asarray(
    manual_delta_reps,
    dtype=float,
)

record(
    "DIRECT_OWNER_RENTER_DIFFERENCE_ORACLE",
    math.isclose(
        difference.delta0,
        manual_delta0,
        rel_tol=0.0,
        abs_tol=1e-15,
    )
    and
    np.allclose(
        difference.replicate_differences,
        manual_delta_reps,
        rtol=0.0,
        atol=1e-15,
    ),
)

manual_delta_variance = asec_variance(
    manual_delta0,
    manual_delta_reps,
)

record(
    "DIRECT_DIFFERENCE_VARIANCE_ORACLE",
    math.isclose(
        difference.variance,
        manual_delta_variance,
        rel_tol=0.0,
        abs_tol=1e-15,
    ),
)


# ----- direct covariance is not replaced by independent-SE shortcut

owner_inf = weighted_share_with_replicates(
    z[owner],
    w0[owner],
    wr[owner, :],
)

renter_inf = weighted_share_with_replicates(
    z[renter],
    w0[renter],
    wr[renter, :],
)

independent_shortcut_variance = (
    owner_inf.variance
    + renter_inf.variance
)

record(
    "INDEPENDENT_SE_SHORTCUT_DISTINGUISHABLE",
    not math.isclose(
        difference.variance,
        independent_shortcut_variance,
        rel_tol=0.0,
        abs_tol=1e-18,
    ),
)


# ----- failure-closed checks

bad_denominator_rejected = False

bad_wr = wr_equal.copy()
bad_wr[:, 5] = -1.0

try:
    weighted_share_with_replicates(
        z,
        w0,
        bad_wr,
    )
except ValueError:
    bad_denominator_rejected = True

record(
    "NONPOSITIVE_REPLICATE_DENOMINATOR_REJECTED",
    bad_denominator_rejected,
)


nonfinite_rejected = False

bad_finite = wr_equal.copy()
bad_finite[0, 0] = np.nan

try:
    weighted_share_with_replicates(
        z,
        w0,
        bad_finite,
    )
except ValueError:
    nonfinite_rejected = True

record(
    "NONFINITE_REPLICATE_WEIGHT_REJECTED",
    nonfinite_rejected,
)


wrong_rep_count_rejected = False

try:
    weighted_share_with_replicates(
        z,
        w0,
        wr_equal[:, :159],
    )
except ValueError:
    wrong_rep_count_rejected = True

record(
    "WRONG_REPLICATE_COUNT_REJECTED",
    wrong_rep_count_rejected,
)


synthetic_pass = all(
    passed
    for _, passed in checks
)

CHECKS.write_text(
    "check\tgate\n"
    + "\n".join(
        f"{name}\t{'PASS' if passed else 'FAIL'}"
        for name, passed in checks
    )
    + "\n",
    encoding="utf-8",
)


overall = all([
    negative_weight_doc_pass,
    variance_only_doc_pass,
    merge_doc_pass,
    formula_doc_pass,
    replicate_contract_pass,
    full_sample_contract_pass,
    estimand_contract_pass,
    cohort_contract_pass,
    execution_shape_pass,
    no_outcome_gate_pass,
    synthetic_pass,
])


lines = [
    "=" * 100,
    "E4A2C — EXACT CPS ASEC REPLICATE-INFERENCE ENGINE CONTRACT",
    "=" * 100,
    "",
    "CPS_I_VALUES_READ=0",
    "CPS_PWWGT1_160_VALUES_PARSED=0",
    "SCF_K_D_VALUES_READ=0",
    "DIMENSIONALITY_OUTCOMES_OPENED=0",
    "SYNTHETIC_ENGINE_VALUES_ONLY=1",
    "",
    "===== UPSTREAM =====",
    "E4A2B_WEIGHT_BRIDGE_AUDIT=PASS",
    "E4A2C_UPSTREAM_AUTHORIZATION=PASS",
    "",
    "===== OFFICIAL ASEC DESIGN SEMANTICS =====",
    (
        "CPS_NEGATIVE_REPLICATE_WEIGHT_DOCUMENTATION=PASS"
        if negative_weight_doc_pass
        else
        "CPS_NEGATIVE_REPLICATE_WEIGHT_DOCUMENTATION=FAIL"
    ),
    (
        "CPS_REPLICATE_VARIANCE_ONLY_DOCUMENTATION=PASS"
        if variance_only_doc_pass
        else
        "CPS_REPLICATE_VARIANCE_ONLY_DOCUMENTATION=FAIL"
    ),
    (
        "CPS_HOUSEHOLD_REPLICATE_MERGE_DOCUMENTATION=PASS"
        if merge_doc_pass
        else
        "CPS_HOUSEHOLD_REPLICATE_MERGE_DOCUMENTATION=FAIL"
    ),
    (
        "CPS_4_OVER_160_DOCUMENTATION=PASS"
        if formula_doc_pass
        else
        "CPS_4_OVER_160_DOCUMENTATION=FAIL"
    ),
    "",
    "===== EXACT ENGINE CONTRACT =====",
    "CPS_FULL_SAMPLE_POINT_WEIGHT=HSUP_WGT",
    "CPS_PWWGT0_ROLE=MERGE_AND_PRECISION_BRIDGE_VERIFICATION_ONLY",
    "CPS_REPLICATE_FIRST=PWWGT1",
    "CPS_REPLICATE_LAST=PWWGT160",
    "CPS_REPLICATE_COUNT=160",
    (
        "CPS_EXACT_REPLICATE_SET=PASS"
        if replicate_contract_pass
        else
        "CPS_EXACT_REPLICATE_SET=FAIL"
    ),
    "CPS_REPLICATE_NEGATIVE_WEIGHT_CLIPPING=PROHIBITED",
    "CPS_REPLICATE_NUMERATOR_DENOMINATOR_SAME_WEIGHT=REQUIRED",
    "CPS_REPLICATE_FULL_SAMPLE_DENOMINATOR_REUSE=PROHIBITED",
    "CPS_REPLICATE_DOMAIN_DENOMINATOR=RECOMPUTE_FINITE_POSITIVE",
    "CPS_VARIANCE_FORMULA=(4/160)*SUM((THETA_R-THETA_0)^2)",
    "CPS_SE_FORMULA=SQRT(VARIANCE)",
    (
        "CPS_FULL_SAMPLE_WEIGHT_CONTRACT=PASS"
        if full_sample_contract_pass
        else
        "CPS_FULL_SAMPLE_WEIGHT_CONTRACT=FAIL"
    ),
    "",
    "===== I ESTIMANDS =====",
    "I_FYFT_SHARE=WEWKRS_EQ_1",
    "I_SEARCH_BURDEN_SHARE=WEUEMP_IN_2_3_4_5_6_7",
    "I_LONG_SEARCH_SHARE=WEUEMP_IN_6_7",
    "I_ANY_WORK_SHARE=WRK_CK_EQ_1",
    (
        "CPS_I_ESTIMAND_CONTRACT=PASS"
        if estimand_contract_pass
        else
        "CPS_I_ESTIMAND_CONTRACT=FAIL"
    ),
    "",
    "===== COHORTS / CONTRAST =====",
    "CPS_G1_COHORT_COUNT=8",
    (
        "CPS_G1_COHORT_CONTRACT=PASS"
        if cohort_contract_pass
        else
        "CPS_G1_COHORT_CONTRACT=FAIL"
    ),
    "OWNER_RENTER_DIFFERENCE=RENTER_MINUS_OWNER",
    "OWNER_RENTER_DIFFERENCE_REPLICATE=DIRECT",
    "OWNER_RENTER_INDEPENDENT_SE_SHORTCUT=PROHIBITED",
    "",
    "===== FIRST EXECUTION SHAPE =====",
    "EXPECTED_FULL_SAMPLE_COHORT_ESTIMAND_ROWS=32",
    "EXPECTED_REPLICATE_COHORT_ESTIMAND_ROWS=5120",
    "EXPECTED_OWNER_RENTER_DIFFERENCE_ROWS=16",
    "EXPECTED_REPLICATE_DIFFERENCE_ROWS=2560",
    (
        "CPS_FIRST_EXECUTION_SHAPE_CONTRACT=PASS"
        if execution_shape_pass
        else
        "CPS_FIRST_EXECUTION_SHAPE_CONTRACT=FAIL"
    ),
    "",
    "===== SYNTHETIC EXECUTABLE PREFLIGHT =====",
    (
        "CPS_SYNTHETIC_ENGINE_PREFLIGHT=PASS"
        if synthetic_pass
        else
        "CPS_SYNTHETIC_ENGINE_PREFLIGHT=FAIL"
    ),
    "",
    "SIGN_GATE=0",
    "MAGNITUDE_GATE=0",
    "SE_MAGNITUDE_GATE=0",
    "SIGNIFICANCE_GATE=0",
    "DIMENSIONALITY_GATE=0",
    (
        "NO_OUTCOME_BASED_CPS_I_GATE=PASS"
        if no_outcome_gate_pass
        else
        "NO_OUTCOME_BASED_CPS_I_GATE=FAIL"
    ),
    "",
    "K_VALUES_OPEN_AUTHORIZED=0",
    "D_VALUES_OPEN_AUTHORIZED=0",
    "I_VALUES_OPEN_AUTHORIZED=0",
    "K_D_I_INFERENCE_AUTHORIZED=0",
    "K_EMPIRICALLY_TESTED=0",
    "D_EMPIRICALLY_TESTED=0",
    "I_EMPIRICALLY_TESTED=0",
    "FIVE_DIMENSIONALITY_PROVEN=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "",
    (
        "E4A2C_EXACT_CPS_REPLICATE_ENGINE_CONTRACT=PASS"
        if overall
        else
        "E4A2C_EXACT_CPS_REPLICATE_ENGINE_CONTRACT=FAIL"
    ),
    (
        "E4A2D_FIRST_CPS_I_INFERENCE_EXECUTION_AUTHORIZED=1"
        if overall
        else
        "E4A2D_FIRST_CPS_I_INFERENCE_EXECUTION_AUTHORIZED=0"
    ),
]

text = "\n".join(lines) + "\n"

AUDIT.write_text(
    text,
    encoding="utf-8",
)

sys.stdout.write(text)

if not overall:
    raise SystemExit(1)
