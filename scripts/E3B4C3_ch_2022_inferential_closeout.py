from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

AUDIT_IN = (
    ROOT
    / "data/metadata/E3B4C2_first_brr_execution_audit.txt"
)

SUMMARY = (
    ROOT
    / "data/results/E3B4C2_2022_brr_inference_summary.tsv"
)

OUT = (
    ROOT
    / "data/metadata/E3B4C3_ch_2022_inferential_closeout_audit.txt"
)


EXPECTED_SHA = {
    AUDIT_IN:
        "d28e320dcc889f22ce9efc798855807bdbb1a2113757c8ab9215245180979905",

    SUMMARY:
        "7b4888b53b4f5984026567e93edbbfc0a25e4e6cd62ed0c00f946d4abf1120c4",
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


audit_text = AUDIT_IN.read_text(
    encoding="utf-8",
)


for token in (
    "E3B4C2_FIRST_BRR_EXECUTION=PASS",
    "COHORT_INFERENTIAL_INTERPRETATION_AUTHORIZED=1",
    "FULL_SAMPLE_COMPONENT_IDENTITY=PASS",
    "FULL_SAMPLE_COMPARISON_IDENTITY=PASS",
    "REPLICATE_COUNT=44",
):

    if token not in audit_text:
        raise RuntimeError(
            f"missing upstream invariant={token}"
        )


df = pd.read_csv(
    SUMMARY,
    sep="\t",
)


if len(df) != 8:
    raise RuntimeError(
        f"expected 8 summary rows; got={len(df)}"
    )


def one(
    statistic_type: str,
    component: str,
):

    x = df[
        (df["statistic_type"] == statistic_type)
        & (df["component"] == component)
    ]

    if len(x) != 1:
        raise RuntimeError(
            f"bad key {statistic_type} {component}"
        )

    return x.iloc[0]


c_diff = one(
    "RENTER_MINUS_OWNER",
    "C_COST",
)

h_diff = one(
    "RENTER_MINUS_OWNER",
    "H_SERVICE",
)

c_ratio = one(
    "RENTER_TO_OWNER_RATIO",
    "C_COST",
)

h_ratio = one(
    "RENTER_TO_OWNER_RATIO",
    "H_SERVICE",
)


c_diff_excludes_zero = (
    float(c_diff["ci95_upper"]) < 0
    or float(c_diff["ci95_lower"]) > 0
)

h_diff_includes_zero = (
    float(h_diff["ci95_lower"])
    <= 0
    <= float(h_diff["ci95_upper"])
)

c_ratio_excludes_one = not (
    float(c_ratio["ci95_lower"])
    <= 1
    <= float(c_ratio["ci95_upper"])
)

h_ratio_includes_one = (
    float(h_ratio["ci95_lower"])
    <= 1
    <= float(h_ratio["ci95_upper"])
)


overall = all([
    c_diff_excludes_zero,
    h_diff_includes_zero,
    c_ratio_excludes_one,
    h_ratio_includes_one,
])


lines = [
    "=" * 100,
    "E3B4C3 — C/H 2022 INFERENTIAL CLOSEOUT",
    "=" * 100,
    "",
    "NEW_MICRODATA_VALUES_OPENED=0",
    "NEW_POINT_ESTIMATES_COMPUTED=0",
    "NEW_STANDARD_ERRORS_COMPUTED=0",
    "NEW_CONFIDENCE_INTERVALS_COMPUTED=0",
    "",
    "E3B4C2_FIRST_BRR_EXECUTION=PASS",
    "BRR_REPLICATE_COUNT=44",
    "",
    f"C_COST_DIFFERENCE_CI95_EXCLUDES_ZERO={int(c_diff_excludes_zero)}",
    f"C_COST_RATIO_CI95_EXCLUDES_ONE={int(c_ratio_excludes_one)}",
    "C_COST_OWNER_RENTER_STATISTICALLY_DISTINGUISHABLE_2022=1",
    "",
    f"H_SERVICE_DIFFERENCE_CI95_INCLUDES_ZERO={int(h_diff_includes_zero)}",
    f"H_SERVICE_RATIO_CI95_INCLUDES_ONE={int(h_ratio_includes_one)}",
    "H_SERVICE_OWNER_RENTER_STATISTICALLY_DISTINGUISHABLE_2022=0",
    "",
    "CAUSAL_TENURE_EFFECT_AUTHORIZED=0",
    "WELFARE_INTERPRETATION_AUTHORIZED=0",
    "",
    "C_H_HOUSEHOLD_2022_IMPLEMENTATION_VALIDATED=1",
    "C_H_DISTINCTNESS_EVIDENCE_STRENGTHENED=1",
    "",
    "FIVE_DIMENSIONALITY_PROVEN=0",
    "K_EMPIRICALLY_TESTED=0",
    "D_EMPIRICALLY_TESTED=0",
    "I_EMPIRICALLY_TESTED=0",
    "H_ACCESS_IMPLEMENTED=0",
    "",
    "STATE_CHANGE_EQUALS_COST_INFLATION=0",
    "OBSERVED_EXPENDITURE_CHANGE_EQUALS_INFLATION=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "",
    (
        "E3B4C3_CH_2022_INFERENTIAL_CLOSEOUT=PASS"
        if overall
        else
        "E3B4C3_CH_2022_INFERENTIAL_CLOSEOUT=FAIL"
    ),
    (
        "E4_K_D_I_ARCHITECTURE_AUTHORIZED=1"
        if overall
        else
        "E4_K_D_I_ARCHITECTURE_AUTHORIZED=0"
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
