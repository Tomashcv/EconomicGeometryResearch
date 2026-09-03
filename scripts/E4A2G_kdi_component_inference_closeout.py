from __future__ import annotations

import csv
import hashlib
import math
import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

I_DIFF = (
    ROOT
    / "data/results/E4A2D_2022_cps_i_owner_renter_differences.tsv"
)

KD_DIFF = (
    ROOT
    / "data/results/E4A2F_2022_scf_kd_owner_renter_differences.tsv"
)

I_AUDIT = (
    ROOT
    / "data/metadata/E4A2D_first_cps_i_inference_execution_audit.txt"
)

KD_AUDIT = (
    ROOT
    / "data/metadata/E4A2F_first_scf_kd_inference_execution_audit.txt"
)

OUT_LEDGER = (
    ROOT
    / "data/results/E4A2G_2022_kdi_component_contrast_ledger.tsv"
)

OUT_SUMMARY = (
    ROOT
    / "data/results/E4A2G_2022_kdi_dimension_summary.tsv"
)

AUDIT = (
    ROOT
    / "data/metadata/E4A2G_kdi_component_inference_closeout_audit.txt"
)


EXPECTED_SHA = {
    I_DIFF:
        "9f37c768f3aa71ecc67b70d606f3c6b01abdd77ca3bcfa63acce96c2773acdf1",

    KD_DIFF:
        "b6e93c38560b8919662328a2e15da5d015d62e42da070af321339c295615393a",

    I_AUDIT:
        "3a11c270856fb82bd96506befe7317bf33b5e07bf85a2d981b5490007328442a",

    KD_AUDIT:
        "aa5f5440d3869f3e20cb3a78691e065f2ad6559190007692198c80997bb409ad",
}


AGE_ORDER = {
    "AGE25_34": 0,
    "AGE35_44": 1,
    "AGE45_54": 2,
    "AGE55_64": 3,
}


K_ORDER = {
    "K_FIN_MEAN": 0,
    "K_FIN_MEDIAN": 1,
    "K_LIQ_MEAN": 2,
    "K_EQUITY_MEAN": 3,
    "K_RETQLIQ_MEAN": 4,
}


D_ORDER = {
    "D_PIRTOTAL_MEAN": 0,
    "D_DEBT2INC_MEAN": 1,
}


I_ORDER = {
    "I_FYFT_SHARE": 0,
    "I_SEARCH_BURDEN_SHARE": 1,
    "I_LONG_SEARCH_SHARE": 2,
    "I_ANY_WORK_SHARE": 3,
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
    if sha256(path) != expected:
        raise RuntimeError(
            f"frozen hash mismatch: {path}"
        )


def parse_finite(name: str, raw: str) -> float:
    value = float(raw)

    if not math.isfinite(value):
        raise RuntimeError(
            f"non-finite {name}"
        )

    return value


def direction(value: float) -> str:
    if value > 0.0:
        return "POSITIVE"
    if value < 0.0:
        return "NEGATIVE"
    return "ZERO"


def interpretation(value: float) -> str:
    if value > 0.0:
        return "RENTER_HIGHER_STATE"
    if value < 0.0:
        return "RENTER_LOWER_STATE"
    return "NO_STATE_DIFFERENCE"


def f17(value: float) -> str:
    if not math.isfinite(value):
        raise RuntimeError(
            "attempt to serialize non-finite value"
        )

    return format(
        float(value),
        ".17g",
    )


rows: list[dict[str, object]] = []


# =============================================================================
# SCF K-D frozen contrasts
# =============================================================================

with KD_DIFF.open(
    "r",
    encoding="utf-8",
    newline="",
) as f:

    reader = csv.DictReader(
        f,
        delimiter="\t",
    )

    expected_fields = [
        "year",
        "age_band",
        "contrast",
        "statistic_id",
        "dimension",
        "role",
        "raw_variable",
        "statistic",
        "state_sign",
        "difference_raw",
        "difference_state_oriented",
        "imputation_variance",
        "sampling_replicate_mean_difference",
        "sampling_variance",
        "combined_variance",
        "combined_se",
        "implicate_count",
        "replicate_count",
    ]

    if reader.fieldnames != expected_fields:
        raise RuntimeError(
            "unexpected E4A2F difference schema"
        )

    for x in reader:
        dimension = x["dimension"]

        if dimension not in {
            "K",
            "D",
        }:
            raise RuntimeError(
                "unexpected E4A2F dimension"
            )

        state_sign = int(
            x["state_sign"]
        )

        if state_sign not in {
            -1,
            1,
        }:
            raise RuntimeError(
                "invalid E4A2F state sign"
            )

        raw_diff = parse_finite(
            "difference_raw",
            x["difference_raw"],
        )

        state_diff = parse_finite(
            "difference_state_oriented",
            x["difference_state_oriented"],
        )

        se = parse_finite(
            "combined_se",
            x["combined_se"],
        )

        if se < 0.0:
            raise RuntimeError(
                "negative E4A2F SE"
            )

        if not math.isclose(
            state_diff,
            state_sign * raw_diff,
            rel_tol=1e-12,
            abs_tol=1e-12,
        ):
            raise RuntimeError(
                "E4A2F state orientation identity failed"
            )

        ci_low = (
            state_diff
            - 1.96 * se
        )
        ci_high = (
            state_diff
            + 1.96 * se
        )

        rows.append(
            {
                "year": int(x["year"]),
                "survey": "SCF",
                "dimension": dimension,
                "measure_id": x["statistic_id"],
                "role": x["role"],
                "age_band": x["age_band"],
                "contrast": x["contrast"],
                "state_sign": state_sign,
                "raw_difference": raw_diff,
                "state_oriented_difference": state_diff,
                "se": se,
                "ci95_low_state": ci_low,
                "ci95_high_state": ci_high,
                "ci95_excludes_zero":
                    (
                        ci_low > 0.0
                        or
                        ci_high < 0.0
                    ),
                "state_direction": direction(
                    state_diff
                ),
                "state_interpretation":
                    interpretation(
                        state_diff
                    ),
                "inference_source":
                    "SCF_5_IMPLICATE_PLUS_999_REPLICATE",
            }
        )


# =============================================================================
# CPS I frozen contrasts
# =============================================================================

with I_DIFF.open(
    "r",
    encoding="utf-8",
    newline="",
) as f:

    reader = csv.DictReader(
        f,
        delimiter="\t",
    )

    expected_fields = [
        "year",
        "age_band",
        "contrast",
        "estimand",
        "role",
        "state_sign",
        "owner_unweighted_n",
        "renter_unweighted_n",
        "difference",
        "replicate_variance",
        "replicate_se",
        "replicate_count",
    ]

    if reader.fieldnames != expected_fields:
        raise RuntimeError(
            "unexpected E4A2D difference schema"
        )

    for x in reader:
        state_sign = int(
            x["state_sign"]
        )

        if state_sign not in {
            -1,
            1,
        }:
            raise RuntimeError(
                "invalid E4A2D state sign"
            )

        raw_diff = parse_finite(
            "difference",
            x["difference"],
        )

        se = parse_finite(
            "replicate_se",
            x["replicate_se"],
        )

        if se < 0.0:
            raise RuntimeError(
                "negative E4A2D SE"
            )

        state_diff = (
            state_sign
            * raw_diff
        )

        ci_low = (
            state_diff
            - 1.96 * se
        )
        ci_high = (
            state_diff
            + 1.96 * se
        )

        rows.append(
            {
                "year": int(x["year"]),
                "survey": "CPS_ASEC",
                "dimension": "I",
                "measure_id": x["estimand"],
                "role": x["role"],
                "age_band": x["age_band"],
                "contrast": x["contrast"],
                "state_sign": state_sign,
                "raw_difference": raw_diff,
                "state_oriented_difference": state_diff,
                "se": se,
                "ci95_low_state": ci_low,
                "ci95_high_state": ci_high,
                "ci95_excludes_zero":
                    (
                        ci_low > 0.0
                        or
                        ci_high < 0.0
                    ),
                "state_direction": direction(
                    state_diff
                ),
                "state_interpretation":
                    interpretation(
                        state_diff
                    ),
                "inference_source":
                    "CPS_160_REPLICATE",
            }
        )


# =============================================================================
# Structural checks and deterministic order
# =============================================================================

if len(rows) != 44:
    raise RuntimeError(
        f"expected 44 KDI contrasts, observed={len(rows)}"
    )


counts = defaultdict(int)

for row in rows:
    counts[
        row[
            "dimension"
        ]
    ] += 1

if dict(
    counts
) != {
    "K": 20,
    "D": 8,
    "I": 16,
}:
    raise RuntimeError(
        f"unexpected dimension counts={dict(counts)}"
    )


def measure_order(
    dimension: str,
    measure_id: str,
) -> int:

    if dimension == "K":
        return K_ORDER[
            measure_id
        ]

    if dimension == "D":
        return D_ORDER[
            measure_id
        ]

    if dimension == "I":
        return I_ORDER[
            measure_id
        ]

    raise RuntimeError(
        "unknown dimension"
    )


rows.sort(
    key=lambda r: (
        {
            "K": 0,
            "D": 1,
            "I": 2,
        }[
            r["dimension"]
        ],
        measure_order(
            r["dimension"],
            r["measure_id"],
        ),
        AGE_ORDER[
            r["age_band"]
        ],
    )
)


# =============================================================================
# Descriptive dimension summary — NEVER a gate
# =============================================================================

summary_rows = []

for dimension in (
    "K",
    "D",
    "I",
):
    subset = [
        row
        for row in rows
        if row[
            "dimension"
        ] == dimension
    ]

    positive = sum(
        1
        for row in subset
        if row[
            "state_direction"
        ] == "POSITIVE"
    )

    negative = sum(
        1
        for row in subset
        if row[
            "state_direction"
        ] == "NEGATIVE"
    )

    zero = sum(
        1
        for row in subset
        if row[
            "state_direction"
        ] == "ZERO"
    )

    excludes_zero = sum(
        1
        for row in subset
        if row[
            "ci95_excludes_zero"
        ]
    )

    summary_rows.append(
        {
            "dimension": dimension,
            "contrast_rows": len(
                subset
            ),
            "state_positive_rows":
                positive,
            "state_negative_rows":
                negative,
            "state_zero_rows":
                zero,
            "ci95_excludes_zero_rows":
                excludes_zero,
            "directional_pattern":
                (
                    "ALL_POSITIVE"
                    if positive == len(subset)
                    else
                    "ALL_NEGATIVE"
                    if negative == len(subset)
                    else
                    "MIXED"
                ),
            "direction_used_as_gate":
                "NO",
            "ci95_used_as_gate":
                "NO",
        }
    )


# =============================================================================
# Serialize
# =============================================================================

OUT_LEDGER.parent.mkdir(
    parents=True,
    exist_ok=True,
)


with OUT_LEDGER.open(
    "w",
    encoding="utf-8",
    newline="",
) as f:

    fields = [
        "year",
        "survey",
        "dimension",
        "measure_id",
        "role",
        "age_band",
        "contrast",
        "state_sign",
        "raw_difference",
        "state_oriented_difference",
        "se",
        "ci95_low_state",
        "ci95_high_state",
        "ci95_excludes_zero",
        "state_direction",
        "state_interpretation",
        "inference_source",
    ]

    writer = csv.DictWriter(
        f,
        fieldnames=fields,
        delimiter="\t",
        lineterminator="\n",
    )

    writer.writeheader()

    for row in rows:
        out = dict(
            row
        )

        for key in (
            "raw_difference",
            "state_oriented_difference",
            "se",
            "ci95_low_state",
            "ci95_high_state",
        ):
            out[
                key
            ] = f17(
                out[
                    key
                ]
            )

        out[
            "ci95_excludes_zero"
        ] = (
            "YES"
            if out[
                "ci95_excludes_zero"
            ]
            else
            "NO"
        )

        writer.writerow(
            out
        )


with OUT_SUMMARY.open(
    "w",
    encoding="utf-8",
    newline="",
) as f:

    fields = [
        "dimension",
        "contrast_rows",
        "state_positive_rows",
        "state_negative_rows",
        "state_zero_rows",
        "ci95_excludes_zero_rows",
        "directional_pattern",
        "direction_used_as_gate",
        "ci95_used_as_gate",
    ]

    writer = csv.DictWriter(
        f,
        fieldnames=fields,
        delimiter="\t",
        lineterminator="\n",
    )

    writer.writeheader()

    for row in summary_rows:
        writer.writerow(
            row
        )


# =============================================================================
# Closeout audit
# =============================================================================

summary_by_dimension = {
    row[
        "dimension"
    ]: row
    for row in summary_rows
}


heterogeneity_observed = (
    len(
        {
            row[
                "directional_pattern"
            ]
            for row in summary_rows
        }
    )
    > 1
)


audit_lines = [
    "=" * 100,
    "E4A2G — K-D-I COMPONENT INFERENCE CLOSEOUT",
    "=" * 100,
    "",
    "RAW_SURVEY_DATA_READ=0",
    "SURVEY_REESTIMATION_PERFORMED=0",
    "REPLICATE_RECALCULATION_PERFORMED=0",
    "FROZEN_RESULT_TABLES_ONLY=1",
    "",
    "===== INPUT STATUS =====",
    "E4A2D_CPS_I_FROZEN_PASS=1",
    "E4A2F_SCF_KD_FROZEN_PASS=1",
    "K_EMPIRICALLY_TESTED=1",
    "D_EMPIRICALLY_TESTED=1",
    "I_EMPIRICALLY_TESTED=1",
    "",
    "===== CLOSEOUT SHAPE =====",
    f"K_CONTRAST_ROWS={counts['K']}",
    f"D_CONTRAST_ROWS={counts['D']}",
    f"I_CONTRAST_ROWS={counts['I']}",
    f"KDI_CONTRAST_ROWS={len(rows)}",
    f"KDI_DIMENSION_SUMMARY_ROWS={len(summary_rows)}",
    "KDI_EXACT_CLOSEOUT_SHAPE=PASS",
    "",
    "===== COMMON STATE ORIENTATION =====",
    "RAW_CONTRAST=RENTER_MINUS_OWNER",
    "STATE_ORIENTED_CONTRAST=STATE_SIGN_X_RAW_CONTRAST",
    "HIGHER_STATE=BETTER_WITHIN_COMPONENT",
    "KDI_STATE_ORIENTATION=PASS",
    "",
    "===== DESCRIPTIVE DIRECTION COUNTS — NOT GATES =====",
    (
        "K_STATE_DIRECTIONAL_PATTERN="
        + summary_by_dimension[
            "K"
        ][
            "directional_pattern"
        ]
    ),
    (
        "K_CI95_EXCLUDES_ZERO_ROWS="
        + str(
            summary_by_dimension[
                "K"
            ][
                "ci95_excludes_zero_rows"
            ]
        )
    ),
    (
        "D_STATE_DIRECTIONAL_PATTERN="
        + summary_by_dimension[
            "D"
        ][
            "directional_pattern"
        ]
    ),
    (
        "D_CI95_EXCLUDES_ZERO_ROWS="
        + str(
            summary_by_dimension[
                "D"
            ][
                "ci95_excludes_zero_rows"
            ]
        )
    ),
    (
        "I_STATE_DIRECTIONAL_PATTERN="
        + summary_by_dimension[
            "I"
        ][
            "directional_pattern"
        ]
    ),
    (
        "I_CI95_EXCLUDES_ZERO_ROWS="
        + str(
            summary_by_dimension[
                "I"
            ][
                "ci95_excludes_zero_rows"
            ]
        )
    ),
    (
        "KDI_COMPONENT_DIRECTIONAL_HETEROGENEITY_OBSERVED="
        + (
            "1"
            if heterogeneity_observed
            else
            "0"
        )
    ),
    "DIRECTION_USED_AS_GATE=0",
    "CI95_EXCLUDES_ZERO_USED_AS_GATE=0",
    "SIGNIFICANCE_GATE=0",
    "MAGNITUDE_GATE=0",
    "",
    "===== CROSS-SURVEY BOUNDARY =====",
    "SCF_CPS_INDEPENDENT_SAMPLES=1",
    "PERSON_LEVEL_JOIN_AUTHORIZED=0",
    "CROSS_SURVEY_JOINT_COVARIANCE_AVAILABLE=0",
    "CROSS_DIMENSION_ABSOLUTE_MAGNITUDE_COMPARISON_AUTHORIZED=0",
    "CROSS_DIMENSION_SE_COMBINATION_AUTHORIZED=0",
    "PSEUDO_COHORT_INTEGRATION_ONLY=1",
    "",
    "K_SCALAR_AUTHORIZED=0",
    "D_SCALAR_AUTHORIZED=0",
    "I_SCALAR_AUTHORIZED=0",
    "KDI_SCALAR_AUTHORIZED=0",
    "FIVE_DIMENSIONALITY_PROVEN=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "",
    "E4A2G_KDI_COMPONENT_INFERENCE_CLOSEOUT=PASS",
    "E4B0_C_H_K_D_I_COHORT_COVERAGE_AND_COMPARABILITY_PREFLIGHT_AUTHORIZED=1",
]

audit_text = (
    "\n".join(
        audit_lines
    )
    + "\n"
)

AUDIT.write_text(
    audit_text,
    encoding="utf-8",
)

sys.stdout.write(
    audit_text
)
