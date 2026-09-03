from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from pathlib import Path

import numpy as np

from E4A2E_scf_replicate_mi_engine import (
    IMPLICATE_COUNT,
    MI_MULTIPLIER,
    REPLICATE_COUNT,
    effective_replicate_weights,
    scf_owner_renter_difference_inference,
    scf_statistic_inference,
    weighted_mean,
    weighted_median,
)


ROOT = Path(__file__).resolve().parents[1]

CONTRACT = (
    ROOT
    / "data/metadata/E4A2E_scf_replicate_mi_engine_contract.json"
)

CODEBOOK = (
    ROOT
    / "data/raw/scf/2022/codebk2022.txt"
)

E4A2_CONTRACT = (
    ROOT
    / "data/metadata/E4A2_kdi_estimator_contract.json"
)

E4A2A_AUDIT = (
    ROOT
    / "data/metadata/E4A2A_replicate_weight_schema_audit.txt"
)

E4A2D_AUDIT = (
    ROOT
    / "data/metadata/E4A2D_first_cps_i_inference_execution_audit.txt"
)

ENGINE = (
    ROOT
    / "scripts/E4A2E_scf_replicate_mi_engine.py"
)

AUDIT = (
    ROOT
    / "data/metadata/E4A2E_exact_scf_replicate_mi_engine_preflight_audit.txt"
)

CHECKS = (
    ROOT
    / "data/metadata/E4A2E_synthetic_scf_engine_checks.tsv"
)


EXPECTED_SHA = {
    CODEBOOK:
        "f0011275e744071a53c038238328156868442174b46e2a8507c6dc62e0245bf9",

    E4A2_CONTRACT:
        "40c85c629285e7cf0999250914d7928b9825047682bf41362327060adaef4f0a",

    E4A2A_AUDIT:
        "ebf719755fbe7d0f6c5b0023f3900d435228b2e36d97f1e9a7da3fc4fe76b546",

    E4A2D_AUDIT:
        "3a11c270856fb82bd96506befe7317bf33b5e07bf85a2d981b5490007328442a",
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


upstream_d = E4A2D_AUDIT.read_text(encoding="utf-8")

for token in (
    "E4A2D_FIRST_CPS_I_INFERENCE_EXECUTION=PASS",
    "I_EMPIRICALLY_TESTED=1",
    "E4A2E_EXACT_SCF_REPLICATE_ENGINE_PREFLIGHT_AUTHORIZED=1",
    "K_EMPIRICALLY_TESTED=0",
    "D_EMPIRICALLY_TESTED=0",
):
    if token not in upstream_d:
        raise RuntimeError(f"missing E4A2D invariant={token}")


upstream_a = E4A2A_AUDIT.read_text(encoding="utf-8")

for token in (
    "SCF_REPLICATE_VARIABLE_COUNT=2000",
    "SCF_WT1B_COUNT=999",
    "SCF_MM_COUNT=999",
    "SCF_EXACT_REPLICATE_SCHEMA=PASS",
    "SCF_EFFECTIVE_REPLICATE_WEIGHT=MAX_0_WT1B_R_X_MAX_0_MM_R",
    "SCF_REPLICATE_MERGE_KEY=Y1",
):
    if token not in upstream_a:
        raise RuntimeError(f"missing E4A2A SCF invariant={token}")


contract = json.loads(
    CONTRACT.read_text(encoding="utf-8")
)

if contract["parent_commit"] != "017d0ec":
    raise RuntimeError("unexpected E4A2E parent commit")


# =============================================================================
# Official codebook anchors
# =============================================================================

codebook = CODEBOOK.read_text(
    encoding="utf-8",
    errors="strict",
)

normalized = re.sub(
    r"\s+",
    " ",
    codebook,
)

replicate_first_implicate_doc = (
    "Replicate weights were computed only for the first implicate of each case."
    in normalized
)

combined_formula_doc = (
    "SQRT((6/5)*imputation variance + sampling variance)"
    in codebook
)

effective_weight_doc = (
    "WGTS{I}=MAX(0,MULT{I})*MAX(0,RWGT{I});"
    in codebook
)

implicate_formula_doc = all(
    token in codebook
    for token in (
        "IVM=(IM-IM[,+]/5)##2;",
        "IVM=IVM[,+]/4;",
    )
)

sampling_formula_doc = all(
    token in codebook
    for token in (
        "RVM=(RM-RM[,+]/999)##2;",
        "RVM=RVM[,+]/998;",
    )
)

weight_and_implicate_doc = all(
    token in codebook
    for token in (
        "WGT0=X42001;",
        "IMPLIC=Y1-10*YY1;",
    )
)

median_doc = all(
    token in codebook
    for token in (
        "IMP[,2]=CUSUM(IMP[,2])/POP;",
        "ID[1,I]=IMP[MIN(LOC(IMP[,2]>=.5)),1];",
    )
)


# =============================================================================
# Contract checks
# =============================================================================

contract_pass = all([
    contract["multiple_imputation"]["implicate_count"] == 5,
    contract["multiple_imputation"]["imputation_variance_divisor"] == 4,
    contract["sampling_replicates"]["replicate_count"] == 999,
    contract["sampling_replicates"]["sampling_variance_divisor"] == 998,
    contract["sampling_replicates"]["outcome_and_domain_implicate"] == 1,
    contract["sampling_replicates"]["center"]
        == "MEAN_OF_999_REPLICATE_STATISTICS",
    contract["combined_inference"]["variance"]
        == "(6/5)*IMPUTATION_VARIANCE+SAMPLING_VARIANCE",
    contract["full_sample"]["weight"] == "X42001",
    contract["K"]["primary"]["variable"] == "FIN",
    contract["K"]["robustness"]["statistic"] == "WEIGHTED_MEDIAN",
    contract["D"]["primary"]["variable"] == "PIRTOTAL",
    contract["D"]["primary"]["state_sign"] == -1,
    contract["owner_renter_contrast"]["definition"]
        == "RENTER_MINUS_OWNER",
    contract["owner_renter_contrast"]["independent_standard_error_shortcut"]
        == "PROHIBITED",
])


# =============================================================================
# Synthetic executable tests
# =============================================================================

checks: list[tuple[str, bool]] = []


def record(name: str, passed: bool) -> None:
    checks.append((name, bool(passed)))


record(
    "IMPLICATE_COUNT_CONSTANT",
    IMPLICATE_COUNT == 5,
)

record(
    "REPLICATE_COUNT_CONSTANT",
    REPLICATE_COUNT == 999,
)

record(
    "MI_MULTIPLIER_CONSTANT",
    math.isclose(
        MI_MULTIPLIER,
        6.0 / 5.0,
        rel_tol=0.0,
        abs_tol=0.0,
    ),
)


# ----- MAX(0, raw weight) * MAX(0, multiplicity), including missing -> zero

raw = np.ones((4, 999), dtype=float)
mm = np.ones((4, 999), dtype=float)

raw[:, 0] = [2.0, -3.0, np.nan, 4.0]
mm[:, 0] = [3.0, 5.0, 7.0, -2.0]

raw[:, 1] = [1.5, 2.0, 3.0, 4.0]
mm[:, 1] = [2.0, np.nan, 0.0, 1.5]

eff = effective_replicate_weights(raw, mm)

record(
    "MAX0_MULTIPLICITY_WEIGHT_ORACLE",
    np.array_equal(
        eff[:, 0],
        np.array([6.0, 0.0, 0.0, 0.0]),
    )
    and
    np.array_equal(
        eff[:, 1],
        np.array([3.0, 0.0, 0.0, 6.0]),
    ),
)


# ----- primitive weighted mean and median

x_primitive = np.array([1.0, 2.0, 10.0, 20.0])
w_primitive = np.array([1.0, 2.0, 5.0, 2.0])

record(
    "WEIGHTED_MEAN_PRIMITIVE_ORACLE",
    math.isclose(
        weighted_mean(x_primitive, w_primitive),
        9.5,
        rel_tol=0.0,
        abs_tol=1e-15,
    ),
)

record(
    "WEIGHTED_MEDIAN_PRIMITIVE_ORACLE",
    weighted_median(x_primitive, w_primitive) == 10.0,
)


# ----- full 5-implicate / 999-replicate fixture

n = 8

base = np.array(
    [10, 20, 30, 40, 50, 60, 70, 80],
    dtype=float,
)

values = np.column_stack(
    [
        base,
        base + np.array([0, 1, 0, 1, 0, 1, 0, 1]),
        base + np.array([1, 0, 1, 0, 1, 0, 1, 0]),
        base + 2.0,
        base - 1.0,
    ]
)

w0 = np.column_stack(
    [
        np.array([1,2,3,4,5,6,7,8], dtype=float),
        np.array([2,2,3,4,5,6,7,8], dtype=float),
        np.array([1,3,3,4,5,6,7,8], dtype=float),
        np.array([1,2,4,4,5,6,7,8], dtype=float),
        np.array([1,2,3,5,5,6,7,8], dtype=float),
    ]
)

domain = np.ones((n, 5), dtype=bool)

# Deliberately vary domains across implicates.
domain[0, 1] = False
domain[7, 2] = False
domain[1, 3] = False
domain[6, 4] = False

# Deterministic 999 effective replicate weights around first-implicate weights.
wr = np.empty((n, 999), dtype=float)

for r in range(999):
    phase = (r % 17) - 8
    row_factor = 1.0 + (
        np.arange(n, dtype=float) - 3.5
    ) * phase * 0.001
    wr[:, r] = w0[:, 0] * row_factor

if np.any(wr <= 0.0):
    raise RuntimeError("synthetic replicate construction unexpectedly nonpositive")


mean_inf = scf_statistic_inference(
    values,
    w0,
    wr,
    domain,
    statistic="mean",
)


manual_implicate_means = []

for m in range(5):
    mask = domain[:, m]
    manual_implicate_means.append(
        float(
            np.dot(values[mask, m], w0[mask, m])
            / np.sum(w0[mask, m])
        )
    )

manual_implicate_means = np.asarray(
    manual_implicate_means,
    dtype=float,
)

manual_pooled = float(
    np.mean(manual_implicate_means)
)

manual_imp_var = float(
    np.sum(
        (
            manual_implicate_means
            - manual_pooled
        ) ** 2
    )
    / 4.0
)

manual_rep_means = np.asarray(
    [
        float(
            np.dot(values[:, 0], wr[:, r])
            / np.sum(wr[:, r])
        )
        for r in range(999)
    ],
    dtype=float,
)

manual_rep_center = float(
    np.mean(manual_rep_means)
)

manual_sampling_var = float(
    np.sum(
        (
            manual_rep_means
            - manual_rep_center
        ) ** 2
    )
    / 998.0
)

manual_combined = (
    (6.0 / 5.0) * manual_imp_var
    + manual_sampling_var
)


record(
    "PER_IMPLICATE_WEIGHTED_MEAN_ORACLE",
    np.allclose(
        mean_inf.implicate_statistics,
        manual_implicate_means,
        rtol=0.0,
        atol=1e-14,
    )
    and
    math.isclose(
        mean_inf.pooled_point,
        manual_pooled,
        rel_tol=0.0,
        abs_tol=1e-14,
    ),
)

record(
    "IMPUTATION_VARIANCE_DDOF1_ORACLE",
    math.isclose(
        mean_inf.imputation_variance,
        manual_imp_var,
        rel_tol=0.0,
        abs_tol=1e-14,
    ),
)

record(
    "FIRST_IMPLICATE_REPLICATE_MEAN_ORACLE",
    np.allclose(
        mean_inf.replicate_statistics,
        manual_rep_means,
        rtol=0.0,
        atol=1e-14,
    ),
)

record(
    "SAMPLING_VARIANCE_REPLICATE_CENTER_DDOF1_ORACLE",
    math.isclose(
        mean_inf.sampling_variance,
        manual_sampling_var,
        rel_tol=0.0,
        abs_tol=1e-14,
    )
    and
    math.isclose(
        mean_inf.replicate_mean,
        manual_rep_center,
        rel_tol=0.0,
        abs_tol=1e-14,
    ),
)

wrong_center_variance = float(
    np.sum(
        (
            manual_rep_means
            - manual_pooled
        ) ** 2
    )
    / 998.0
)

record(
    "SAMPLING_CENTER_NOT_POOLED_POINT",
    not math.isclose(
        manual_sampling_var,
        wrong_center_variance,
        rel_tol=0.0,
        abs_tol=1e-18,
    )
    and
    math.isclose(
        mean_inf.sampling_variance,
        manual_sampling_var,
        rel_tol=0.0,
        abs_tol=1e-14,
    ),
)

record(
    "SIX_OVER_FIVE_COMBINED_VARIANCE_ORACLE",
    math.isclose(
        mean_inf.combined_variance,
        manual_combined,
        rel_tol=0.0,
        abs_tol=1e-14,
    )
    and
    math.isclose(
        mean_inf.combined_se,
        math.sqrt(manual_combined),
        rel_tol=0.0,
        abs_tol=1e-14,
    ),
)


# ----- prove later implicates do not contaminate sampling replicates

values_later_changed = values.copy()
values_later_changed[:, 1:] += 10000.0

changed_inf = scf_statistic_inference(
    values_later_changed,
    w0,
    wr,
    domain,
    statistic="mean",
)

record(
    "SAMPLING_USES_FIRST_IMPLICATE_ONLY",
    np.array_equal(
        changed_inf.replicate_statistics,
        mean_inf.replicate_statistics,
    )
    and
    changed_inf.pooled_point != mean_inf.pooled_point,
)


# ----- weighted median through full engine

median_inf = scf_statistic_inference(
    values,
    w0,
    wr,
    domain,
    statistic="median",
)

manual_implicate_medians = np.asarray(
    [
        weighted_median(
            values[domain[:, m], m],
            w0[domain[:, m], m],
        )
        for m in range(5)
    ],
    dtype=float,
)

manual_rep_medians = np.asarray(
    [
        weighted_median(
            values[:, 0],
            wr[:, r],
        )
        for r in range(999)
    ],
    dtype=float,
)

record(
    "WEIGHTED_MEDIAN_FULL_ENGINE_ORACLE",
    np.array_equal(
        median_inf.implicate_statistics,
        manual_implicate_medians,
    )
    and
    np.array_equal(
        median_inf.replicate_statistics,
        manual_rep_medians,
    ),
)


# ----- direct owner/renter differences

owner = np.zeros((n, 5), dtype=bool)
renter = np.zeros((n, 5), dtype=bool)

owner[:4, :] = True
renter[4:, :] = True

# Per-implicate classification variation while staying disjoint/nonempty.
owner[3, 1] = False
renter[3, 1] = True

renter[4, 2] = False
owner[4, 2] = True

diff_inf = scf_owner_renter_difference_inference(
    values,
    w0,
    wr,
    owner,
    renter,
    statistic="mean",
)

manual_deltas = []

for m in range(5):
    om = owner[:, m]
    rm = renter[:, m]

    o = weighted_mean(
        values[om, m],
        w0[om, m],
    )
    r = weighted_mean(
        values[rm, m],
        w0[rm, m],
    )

    manual_deltas.append(r - o)

manual_deltas = np.asarray(
    manual_deltas,
    dtype=float,
)

manual_delta_reps = np.asarray(
    [
        weighted_mean(
            values[renter[:, 0], 0],
            wr[renter[:, 0], r],
        )
        -
        weighted_mean(
            values[owner[:, 0], 0],
            wr[owner[:, 0], r],
        )
        for r in range(999)
    ],
    dtype=float,
)

record(
    "DIRECT_OWNER_RENTER_IMPLICATE_DIFFERENCE_ORACLE",
    np.allclose(
        diff_inf.implicate_differences,
        manual_deltas,
        rtol=0.0,
        atol=1e-14,
    )
    and
    math.isclose(
        diff_inf.pooled_difference,
        float(np.mean(manual_deltas)),
        rel_tol=0.0,
        abs_tol=1e-14,
    ),
)

record(
    "DIRECT_OWNER_RENTER_REPLICATE_DIFFERENCE_ORACLE",
    np.allclose(
        diff_inf.replicate_differences,
        manual_delta_reps,
        rtol=0.0,
        atol=5e-14,
    ),
)


# Compare against an explicitly prohibited independent sampling-variance sum.
owner_only = scf_statistic_inference(
    values,
    w0,
    wr,
    owner,
    statistic="mean",
)

renter_only = scf_statistic_inference(
    values,
    w0,
    wr,
    renter,
    statistic="mean",
)

independent_sampling_shortcut = (
    owner_only.sampling_variance
    + renter_only.sampling_variance
)

record(
    "DIRECT_CONTRAST_COVARIANCE_PRESERVED",
    not math.isclose(
        diff_inf.sampling_variance,
        independent_sampling_shortcut,
        rel_tol=0.0,
        abs_tol=1e-18,
    ),
)


# ----- failure-closed tests

bad_implicate_count_rejected = False

try:
    scf_statistic_inference(
        values[:, :4],
        w0[:, :4],
        wr,
        domain[:, :4],
        statistic="mean",
    )
except ValueError:
    bad_implicate_count_rejected = True

record(
    "WRONG_IMPLICATE_COUNT_REJECTED",
    bad_implicate_count_rejected,
)


bad_replicate_count_rejected = False

try:
    scf_statistic_inference(
        values,
        w0,
        wr[:, :998],
        domain,
        statistic="mean",
    )
except ValueError:
    bad_replicate_count_rejected = True

record(
    "WRONG_REPLICATE_COUNT_REJECTED",
    bad_replicate_count_rejected,
)


bad_denominator_rejected = False

bad_wr = wr.copy()
bad_wr[:, 50] = 0.0

try:
    scf_statistic_inference(
        values,
        w0,
        bad_wr,
        domain,
        statistic="mean",
    )
except ValueError:
    bad_denominator_rejected = True

record(
    "NONPOSITIVE_REPLICATE_DENOMINATOR_REJECTED",
    bad_denominator_rejected,
)


nonfinite_outcome_rejected = False

bad_values = values.copy()
bad_values[0, 0] = np.nan

try:
    scf_statistic_inference(
        bad_values,
        w0,
        wr,
        domain,
        statistic="mean",
    )
except ValueError:
    nonfinite_outcome_rejected = True

record(
    "NONFINITE_OUTCOME_REJECTED",
    nonfinite_outcome_rejected,
)


overlap_rejected = False

bad_renter = renter.copy()
bad_renter[0, 0] = True

try:
    scf_owner_renter_difference_inference(
        values,
        w0,
        wr,
        owner,
        bad_renter,
        statistic="mean",
    )
except ValueError:
    overlap_rejected = True

record(
    "OWNER_RENTER_OVERLAP_REJECTED",
    overlap_rejected,
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


documentation_pass = all([
    replicate_first_implicate_doc,
    combined_formula_doc,
    effective_weight_doc,
    implicate_formula_doc,
    sampling_formula_doc,
    weight_and_implicate_doc,
    median_doc,
])


overall = all([
    documentation_pass,
    contract_pass,
    synthetic_pass,
])


lines = [
    "=" * 100,
    "E4A2E — EXACT SCF REPLICATE + MULTIPLE-IMPUTATION ENGINE PREFLIGHT",
    "=" * 100,
    "",
    "SCF_K_D_VALUES_READ=0",
    "SCF_REPLICATE_WEIGHT_VALUES_PARSED=0",
    "CPS_I_VALUES_NEWLY_READ=0",
    "DIMENSIONALITY_ANALYSIS_PERFORMED=0",
    "SYNTHETIC_ENGINE_VALUES_ONLY=1",
    "",
    "===== OFFICIAL SCF DESIGN =====",
    (
        "SCF_REPLICATE_FIRST_IMPLICATE_DOCUMENTATION=PASS"
        if replicate_first_implicate_doc
        else
        "SCF_REPLICATE_FIRST_IMPLICATE_DOCUMENTATION=FAIL"
    ),
    (
        "SCF_COMBINED_6_OVER_5_DOCUMENTATION=PASS"
        if combined_formula_doc
        else
        "SCF_COMBINED_6_OVER_5_DOCUMENTATION=FAIL"
    ),
    (
        "SCF_EFFECTIVE_REPLICATE_WEIGHT_DOCUMENTATION=PASS"
        if effective_weight_doc
        else
        "SCF_EFFECTIVE_REPLICATE_WEIGHT_DOCUMENTATION=FAIL"
    ),
    (
        "SCF_IMPUTATION_VARIANCE_DOCUMENTATION=PASS"
        if implicate_formula_doc
        else
        "SCF_IMPUTATION_VARIANCE_DOCUMENTATION=FAIL"
    ),
    (
        "SCF_SAMPLING_VARIANCE_DOCUMENTATION=PASS"
        if sampling_formula_doc
        else
        "SCF_SAMPLING_VARIANCE_DOCUMENTATION=FAIL"
    ),
    (
        "SCF_WEIGHT_IMPLICATE_KEY_DOCUMENTATION=PASS"
        if weight_and_implicate_doc
        else
        "SCF_WEIGHT_IMPLICATE_KEY_DOCUMENTATION=FAIL"
    ),
    (
        "SCF_WEIGHTED_MEDIAN_DOCUMENTATION=PASS"
        if median_doc
        else
        "SCF_WEIGHTED_MEDIAN_DOCUMENTATION=FAIL"
    ),
    "",
    "===== EXACT ENGINE =====",
    "SCF_IMPLICATE_COUNT=5",
    "SCF_REPLICATE_COUNT=999",
    "SCF_FULL_SAMPLE_WEIGHT=X42001",
    "SCF_REPLICATE_EFFECTIVE_WEIGHT=MAX_0_WT1B_R_X_MAX_0_MM_R",
    "SCF_SAMPLING_OUTCOME_IMPLICATE=1",
    "SCF_IMPUTATION_VARIANCE=SUM_SQ_AROUND_IMPLICATE_MEAN_DIV_4",
    "SCF_SAMPLING_VARIANCE=SUM_SQ_AROUND_REPLICATE_MEAN_DIV_998",
    "SCF_COMBINED_VARIANCE=(6/5)*IMPUTATION_VARIANCE+SAMPLING_VARIANCE",
    "SCF_COMBINED_SE=SQRT(COMBINED_VARIANCE)",
    (
        "SCF_EXACT_MI_REPLICATE_CONTRACT=PASS"
        if contract_pass
        else
        "SCF_EXACT_MI_REPLICATE_CONTRACT=FAIL"
    ),
    "",
    "===== STATISTICS =====",
    "SCF_PRIMARY_STATISTIC=WEIGHTED_MEAN",
    "SCF_FIN_ROBUSTNESS_STATISTIC=WEIGHTED_MEDIAN",
    "K_PRIMARY=FIN",
    "K_SENSITIVITY=LIQ,EQUITY,RETQLIQ",
    "D_PRIMARY_RAW=PIRTOTAL",
    "D_PRIMARY_STATE_SIGN=-1",
    "D_SECONDARY_RAW=DEBT2INC",
    "D_SECONDARY_STATE_SIGN=-1",
    "SCF_OWNER_RENTER_DIFFERENCE=RENTER_MINUS_OWNER_DIRECT",
    "SCF_INDEPENDENT_SE_SHORTCUT=PROHIBITED",
    "",
    "===== SYNTHETIC EXECUTABLE PREFLIGHT =====",
    (
        "SCF_SYNTHETIC_MI_REPLICATE_ENGINE_PREFLIGHT=PASS"
        if synthetic_pass
        else
        "SCF_SYNTHETIC_MI_REPLICATE_ENGINE_PREFLIGHT=FAIL"
    ),
    "",
    "SIGN_GATE=0",
    "MAGNITUDE_GATE=0",
    "SE_MAGNITUDE_GATE=0",
    "SIGNIFICANCE_GATE=0",
    "OWNER_RENTER_DIRECTION_GATE=0",
    "DIMENSIONALITY_GATE=0",
    "NO_OUTCOME_BASED_SCF_KD_GATE=PASS",
    "",
    "I_EMPIRICALLY_TESTED=1",
    "K_VALUES_OPEN_AUTHORIZED=0",
    "D_VALUES_OPEN_AUTHORIZED=0",
    "K_D_I_INFERENCE_AUTHORIZED=0",
    "K_EMPIRICALLY_TESTED=0",
    "D_EMPIRICALLY_TESTED=0",
    "FIVE_DIMENSIONALITY_PROVEN=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "",
    (
        "E4A2E_EXACT_SCF_REPLICATE_MI_ENGINE_PREFLIGHT=PASS"
        if overall
        else
        "E4A2E_EXACT_SCF_REPLICATE_MI_ENGINE_PREFLIGHT=FAIL"
    ),
    (
        "E4A2F_FIRST_SCF_KD_INFERENCE_EXECUTION_AUTHORIZED=1"
        if overall
        else
        "E4A2F_FIRST_SCF_KD_INFERENCE_EXECUTION_AUTHORIZED=0"
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
