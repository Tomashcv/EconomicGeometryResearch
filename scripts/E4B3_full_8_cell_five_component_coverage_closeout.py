from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

B0_COVERAGE = (
    ROOT
    / "data/results/E4B0_2022_component_cohort_coverage.tsv"
)

B0_CONSTRAINTS = (
    ROOT
    / "data/results/E4B0_comparability_constraints.tsv"
)

B2_POINT = (
    ROOT
    / "data/results/E4B2_2022_ch_component_point_estimates.tsv"
)

B2_INFERENCE = (
    ROOT
    / "data/results/E4B2_2022_ch_brr_inference_summary.tsv"
)

A2G_LEDGER = (
    ROOT
    / "data/results/E4A2G_2022_kdi_component_contrast_ledger.tsv"
)

CONTRACT = (
    ROOT
    / "data/metadata/E4B3_full_8_cell_five_component_coverage_closeout_contract.json"
)

OUT_COVERAGE = (
    ROOT
    / "data/results/E4B3_2022_five_component_evidence_coverage.tsv"
)

OUT_SUMMARY = (
    ROOT
    / "data/results/E4B3_five_component_evidence_coverage_summary.tsv"
)

OUT_LEDGER = (
    ROOT
    / "data/results/E4B3_2022_primary_component_contrast_ledger.tsv"
)

OUT_CONSTRAINTS = (
    ROOT
    / "data/results/E4B3_coordinate_readiness_constraints.tsv"
)

AUDIT = (
    ROOT
    / "data/metadata/E4B3_full_8_cell_five_component_coverage_closeout_audit.txt"
)


contract = json.loads(
    CONTRACT.read_text(
        encoding="utf-8"
    )
)


age_bands = [
    "AGE25_34",
    "AGE35_44",
    "AGE45_54",
    "AGE55_64",
]

tenures = [
    "OWNER",
    "RENTER",
]


# =============================================================================
# Frozen result tables only.
# =============================================================================

b0 = pd.read_csv(
    B0_COVERAGE,
    sep="\t",
    dtype=str,
)

b2_point = pd.read_csv(
    B2_POINT,
    sep="\t",
)

b2_inf = pd.read_csv(
    B2_INFERENCE,
    sep="\t",
)

kdi = pd.read_csv(
    A2G_LEDGER,
    sep="\t",
)


# =============================================================================
# Exact common grid.
# =============================================================================

expected_cells = {
    (
        age,
        tenure,
    )
    for age in age_bands
    for tenure in tenures
}

observed_b0_cells = {
    (
        str(row.age_band),
        str(row.tenure),
    )
    for row in b0.itertuples(
        index=False
    )
}

if observed_b0_cells != expected_cells:
    raise RuntimeError(
        "E4B0 common cohort grid mismatch"
    )


# =============================================================================
# C/H coverage from frozen E4B2 point estimates.
# =============================================================================

required_b2_cols = {
    "year",
    "age_band",
    "tenure",
    "cohort",
    "component",
    "annual_mean_nominal_usd",
}

if set(
    b2_point.columns
) != required_b2_cols:
    raise RuntimeError(
        f"unexpected E4B2 point schema={list(b2_point.columns)}"
    )

if len(
    b2_point
) != 16:
    raise RuntimeError(
        f"expected 16 E4B2 point rows, observed={len(b2_point)}"
    )

if set(
    b2_point[
        "component"
    ].astype(
        str
    )
) != {
    "C_COST",
    "H_SERVICE",
}:
    raise RuntimeError(
        "unexpected E4B2 component set"
    )

ch_coverage = {}

for age, tenure in sorted(
    expected_cells
):

    sub = b2_point[
        (
            b2_point[
                "age_band"
            ].astype(
                str
            )
            == age
        )
        &
        (
            b2_point[
                "tenure"
            ].astype(
                str
            )
            == tenure
        )
    ]

    counts = (
        sub[
            "component"
        ]
        .astype(
            str
        )
        .value_counts()
        .to_dict()
    )

    ch_coverage[
        (
            age,
            tenure,
        )
    ] = {
        "C":
            counts.get(
                "C_COST",
                0,
            )
            == 1,

        "H":
            counts.get(
                "H_SERVICE",
                0,
            )
            == 1,
    }


# =============================================================================
# K/D/I coverage was frozen in E4B0 and must already be 8/8.
# =============================================================================

b0_map = {
    (
        str(row.age_band),
        str(row.tenure),
    ): row
    for row in b0.itertuples(
        index=False
    )
}

coverage_rows = []

for age in age_bands:
    for tenure in tenures:

        key = (
            age,
            tenure,
        )

        prior = b0_map[
            key
        ]

        c_ok = ch_coverage[
            key
        ][
            "C"
        ]

        h_ok = ch_coverage[
            key
        ][
            "H"
        ]

        k_ok = (
            str(
                prior.K_primary_evidence
            )
            == "YES"
        )

        d_ok = (
            str(
                prior.D_primary_evidence
            )
            == "YES"
        )

        i_ok = (
            str(
                prior.I_both_primary_estimands
            )
            == "YES"
        )

        all_ok = all(
            [
                c_ok,
                h_ok,
                k_ok,
                d_ok,
                i_ok,
            ]
        )

        coverage_rows.append(
            {
                "year":
                    2022,

                "age_band":
                    age,

                "tenure":
                    tenure,

                "C_primary_evidence":
                    "YES"
                    if c_ok
                    else "NO",

                "H_primary_evidence":
                    "YES"
                    if h_ok
                    else "NO",

                "K_primary_evidence":
                    "YES"
                    if k_ok
                    else "NO",

                "D_primary_evidence":
                    "YES"
                    if d_ok
                    else "NO",

                "I_both_primary_estimands":
                    "YES"
                    if i_ok
                    else "NO",

                "five_component_evidence_coverage":
                    "YES"
                    if all_ok
                    else "NO",
            }
        )


coverage = pd.DataFrame(
    coverage_rows
)

if len(
    coverage
) != 8:
    raise RuntimeError(
        "coverage row count mismatch"
    )

for col in (
    "C_primary_evidence",
    "H_primary_evidence",
    "K_primary_evidence",
    "D_primary_evidence",
    "I_both_primary_estimands",
    "five_component_evidence_coverage",
):
    if not (
        coverage[
            col
        ]
        == "YES"
    ).all():
        raise RuntimeError(
            f"full evidence coverage not reached for {col}"
        )


# =============================================================================
# Component evidence summary.
# =============================================================================

summary_rows = [
    {
        "component": "C",
        "survey": "CEX",
        "primary_evidence": "C_COST",
        "covered_cells_of_8": 8,
        "coordinate_readiness":
            "EVIDENCE_ONLY__C_COORDINATE_SEMANTICS_NOT_FROZEN",
    },
    {
        "component": "H",
        "survey": "CEX",
        "primary_evidence": "H_SERVICE",
        "covered_cells_of_8": 8,
        "coordinate_readiness":
            "EVIDENCE_ONLY__H_ACCESS_NOT_IMPLEMENTED",
    },
    {
        "component": "K",
        "survey": "SCF",
        "primary_evidence": "K_FIN_MEAN",
        "covered_cells_of_8": 8,
        "coordinate_readiness":
            "STATE_ORIENTATION_FROZEN__DIMENSIONLESS_TRANSFORM_NOT_FROZEN",
    },
    {
        "component": "D",
        "survey": "SCF",
        "primary_evidence": "D_PIRTOTAL_MEAN",
        "covered_cells_of_8": 8,
        "coordinate_readiness":
            "STATE_ORIENTATION_FROZEN__DIMENSIONLESS_TRANSFORM_NOT_FROZEN",
    },
    {
        "component": "I",
        "survey": "CPS_ASEC",
        "primary_evidence":
            "I_FYFT_SHARE+I_SEARCH_BURDEN_SHARE",
        "covered_cells_of_8": 8,
        "coordinate_readiness":
            "TWO_PRIMARY_ESTIMANDS__I_SCALAR_NOT_FROZEN",
    },
]

summary = pd.DataFrame(
    summary_rows
)


# =============================================================================
# Primary C/H renter-minus-owner contrasts.
# No state sign is invented.
# =============================================================================

required_inf_cols = {
    "year",
    "statistic_type",
    "cohort",
    "component",
    "estimate",
    "brr_variance",
    "brr_se",
    "ci95_lower",
    "ci95_upper",
}

if set(
    b2_inf.columns
) != required_inf_cols:
    raise RuntimeError(
        f"unexpected E4B2 inference schema={list(b2_inf.columns)}"
    )

ch_diff = b2_inf[
    b2_inf[
        "statistic_type"
    ].astype(
        str
    )
    == "RENTER_MINUS_OWNER"
].copy()

if len(
    ch_diff
) != 8:
    raise RuntimeError(
        f"expected 8 C/H difference rows, observed={len(ch_diff)}"
    )

ledger_rows = []

for row in ch_diff.itertuples(
    index=False
):

    cohort = str(
        row.cohort
    )

    suffix = (
        "_RENTER_MINUS_OWNER"
    )

    if not cohort.endswith(
        suffix
    ):
        raise RuntimeError(
            f"unexpected C/H contrast cohort={cohort}"
        )

    age = cohort[
        :-len(
            suffix
        )
    ]

    component = str(
        row.component
    )

    measure_id = (
        "C_COST"
        if component == "C_COST"
        else "H_SERVICE"
    )

    raw = float(
        row.estimate
    )

    se = float(
        row.brr_se
    )

    lo = float(
        row.ci95_lower
    )

    hi = float(
        row.ci95_upper
    )

    if not all(
        math.isfinite(
            x
        )
        for x in (
            raw,
            se,
            lo,
            hi,
        )
    ):
        raise RuntimeError(
            "nonfinite C/H contrast"
        )

    ledger_rows.append(
        {
            "year": 2022,
            "survey": "CEX",
            "component":
                "C"
                if component == "C_COST"
                else "H",

            "measure_id":
                measure_id,

            "role":
                "PRIMARY",

            "age_band":
                age,

            "contrast":
                "RENTER_MINUS_OWNER",

            "state_sign":
                "",

            "raw_difference":
                raw,

            "state_oriented_difference":
                "",

            "se":
                se,

            "ci95_low":
                lo,

            "ci95_high":
                hi,

            "state_orientation_status":
                "NOT_FROZEN_FOR_C_H",

            "inference_source":
                "CEX_44_REPLICATE_BRR",
        }
    )


# =============================================================================
# Primary K/D/I contrasts from frozen E4A2G ledger.
# =============================================================================

required_kdi_cols = {
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
}

if set(
    kdi.columns
) != required_kdi_cols:
    raise RuntimeError(
        f"unexpected E4A2G ledger schema={list(kdi.columns)}"
    )


primary_ids = {
    "K_FIN_MEAN",
    "D_PIRTOTAL_MEAN",
    "I_FYFT_SHARE",
    "I_SEARCH_BURDEN_SHARE",
}

kdi_primary = kdi[
    kdi[
        "measure_id"
    ].astype(
        str
    ).isin(
        primary_ids
    )
].copy()

if len(
    kdi_primary
) != 16:
    raise RuntimeError(
        f"expected 16 primary K/D/I contrast rows, observed={len(kdi_primary)}"
    )

counts = (
    kdi_primary[
        "measure_id"
    ]
    .astype(
        str
    )
    .value_counts()
    .to_dict()
)

expected_counts = {
    "K_FIN_MEAN": 4,
    "D_PIRTOTAL_MEAN": 4,
    "I_FYFT_SHARE": 4,
    "I_SEARCH_BURDEN_SHARE": 4,
}

if counts != expected_counts:
    raise RuntimeError(
        f"primary K/D/I measure counts mismatch={counts}"
    )


for row in kdi_primary.itertuples(
    index=False
):

    raw = float(
        row.raw_difference
    )

    state = float(
        row.state_oriented_difference
    )

    se = float(
        row.se
    )

    lo = float(
        row.ci95_low_state
    )

    hi = float(
        row.ci95_high_state
    )

    if not all(
        math.isfinite(
            x
        )
        for x in (
            raw,
            state,
            se,
            lo,
            hi,
        )
    ):
        raise RuntimeError(
            "nonfinite K/D/I primary contrast"
        )

    ledger_rows.append(
        {
            "year":
                int(
                    row.year
                ),

            "survey":
                str(
                    row.survey
                ),

            "component":
                str(
                    row.dimension
                ),

            "measure_id":
                str(
                    row.measure_id
                ),

            "role":
                str(
                    row.role
                ),

            "age_band":
                str(
                    row.age_band
                ),

            "contrast":
                str(
                    row.contrast
                ),

            "state_sign":
                int(
                    row.state_sign
                ),

            "raw_difference":
                raw,

            "state_oriented_difference":
                state,

            "se":
                se,

            "ci95_low":
                lo,

            "ci95_high":
                hi,

            "state_orientation_status":
                "FROZEN_IN_E4A2G",

            "inference_source":
                str(
                    row.inference_source
                ),
        }
    )


ledger = pd.DataFrame(
    ledger_rows
)

if len(
    ledger
) != 24:
    raise RuntimeError(
        f"expected 24 primary ledger rows, observed={len(ledger)}"
    )


expected_component_counts = {
    "C": 4,
    "H": 4,
    "K": 4,
    "D": 4,
    "I": 8,
}

component_counts = (
    ledger[
        "component"
    ]
    .value_counts()
    .to_dict()
)

if component_counts != expected_component_counts:
    raise RuntimeError(
        f"primary component ledger counts mismatch={component_counts}"
    )


# =============================================================================
# Coordinate-readiness constraints.
# =============================================================================

constraint_rows = [
    (
        "FULL_8_CELL_FIVE_COMPONENT_EVIDENCE_COVERAGE",
        "YES",
        "All required frozen primary evidence exists in every common pseudo-cohort cell.",
    ),
    (
        "MICRO_OBSERVATIONAL_UNIT_IDENTICAL",
        "NO",
        "CEX consumer units, SCF families, and CPS household/reference-person units remain distinct.",
    ),
    (
        "PERSON_LEVEL_CROSS_SURVEY_JOIN_AUTHORIZED",
        "NO",
        "Independent survey samples prohibit person-level joining.",
    ),
    (
        "CROSS_SURVEY_JOINT_COVARIANCE_AVAILABLE",
        "NO",
        "No frozen joint covariance spans CEX, SCF, and CPS.",
    ),
    (
        "PSEUDO_COHORT_INTEGRATION_ONLY",
        "YES",
        "AGE_BAND x TENURE remains the only authorized cross-survey bridge.",
    ),
    (
        "RAW_C_H_K_D_I_UNITS_COMMENSURABLE",
        "NO",
        "Flows, stocks, ratios, and shares remain different raw measurement scales.",
    ),
    (
        "C_COORDINATE_SEMANTICS_FROZEN",
        "NO",
        "C_COST evidence coverage does not by itself define a state coordinate.",
    ),
    (
        "H_ACCESS_IMPLEMENTED",
        "NO",
        "H_SERVICE is measured but full housing-access state remains unimplemented.",
    ),
    (
        "H_SERVICE_EQUALS_FULL_H_DIMENSION",
        "NO",
        "Housing service expenditure must not be silently equated with a complete H coordinate.",
    ),
    (
        "I_SCALAR_AUTHORIZED",
        "NO",
        "I retains two primary estimands and no scalar combination is frozen.",
    ),
    (
        "FIVE_COMPONENT_STATE_VECTOR_AUTHORIZED",
        "NO",
        "Evidence coverage does not authorize a five-coordinate state vector.",
    ),
    (
        "FIVE_COMPONENT_NORMALIZATION_AUTHORIZED",
        "NO",
        "No dimensionless-coordinate transformation has been frozen.",
    ),
    (
        "DIMENSIONALITY_TEST_AUTHORIZED",
        "NO",
        "Coordinate semantics and transformation rules must be frozen first.",
    ),
    (
        "REAL_INFLATION_ESTIMATION_AUTHORIZED",
        "NO",
        "Component evidence coverage is not a Real Inflation estimator.",
    ),
    (
        "FINAL_SCALAR_AUTHORIZED",
        "NO",
        "No final scalar is authorized.",
    ),
]

constraints = pd.DataFrame(
    constraint_rows,
    columns=[
        "constraint",
        "status",
        "interpretation",
    ],
)

if len(
    constraints
) != 15:
    raise RuntimeError(
        "constraint row count mismatch"
    )


# =============================================================================
# Descriptive direction counts — explicitly not gates.
# =============================================================================

def sign_counts(
    values: pd.Series,
) -> tuple[int, int, int]:

    vals = pd.to_numeric(
        values,
        errors="raise",
    )

    return (
        int(
            (
                vals
                > 0
            ).sum()
        ),
        int(
            (
                vals
                < 0
            ).sum()
        ),
        int(
            (
                vals
                == 0
            ).sum()
        ),
    )


c_pos, c_neg, c_zero = sign_counts(
    ledger.loc[
        ledger[
            "component"
        ]
        == "C",
        "raw_difference",
    ]
)

h_pos, h_neg, h_zero = sign_counts(
    ledger.loc[
        ledger[
            "component"
        ]
        == "H",
        "raw_difference",
    ]
)

k_pos, k_neg, k_zero = sign_counts(
    ledger.loc[
        ledger[
            "component"
        ]
        == "K",
        "state_oriented_difference",
    ]
)

d_pos, d_neg, d_zero = sign_counts(
    ledger.loc[
        ledger[
            "component"
        ]
        == "D",
        "state_oriented_difference",
    ]
)

i_pos, i_neg, i_zero = sign_counts(
    ledger.loc[
        ledger[
            "component"
        ]
        == "I",
        "state_oriented_difference",
    ]
)


# =============================================================================
# Serialize exact frozen-result closeout.
# =============================================================================

OUT_COVERAGE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

coverage.to_csv(
    OUT_COVERAGE,
    sep="\t",
    index=False,
    lineterminator="\n",
)

summary.to_csv(
    OUT_SUMMARY,
    sep="\t",
    index=False,
    lineterminator="\n",
)

ledger = ledger.sort_values(
    [
        "component",
        "measure_id",
        "age_band",
    ],
    kind="stable",
)

ledger.to_csv(
    OUT_LEDGER,
    sep="\t",
    index=False,
    lineterminator="\n",
)

constraints.to_csv(
    OUT_CONSTRAINTS,
    sep="\t",
    index=False,
    lineterminator="\n",
)


# =============================================================================
# Audit.
# =============================================================================

audit_lines = [
    "=" * 100,
    "E4B3 — FULL 8-CELL FIVE-COMPONENT EVIDENCE-COVERAGE CLOSEOUT",
    "=" * 100,
    "",
    "RAW_SURVEY_DATA_READ=0",
    "SURVEY_REESTIMATION_PERFORMED=0",
    "REPLICATE_RECALCULATION_PERFORMED=0",
    "FROZEN_RESULT_TABLES_ONLY=1",
    "",
    "===== FULL EVIDENCE COVERAGE =====",
    "C_COVERED_CELLS_OF_8=8",
    "H_COVERED_CELLS_OF_8=8",
    "K_COVERED_CELLS_OF_8=8",
    "D_COVERED_CELLS_OF_8=8",
    "I_COVERED_CELLS_OF_8=8",
    "FIVE_COMPONENT_EVIDENCE_COVERED_CELLS_OF_8=8",
    "FULL_8_CELL_FIVE_COMPONENT_EVIDENCE_COVERAGE=YES",
    "E4B3_EXACT_COVERAGE_SHAPE=PASS",
    "",
    "===== PRIMARY CONTRAST LEDGER =====",
    "C_PRIMARY_CONTRAST_ROWS=4",
    "H_PRIMARY_CONTRAST_ROWS=4",
    "K_PRIMARY_CONTRAST_ROWS=4",
    "D_PRIMARY_CONTRAST_ROWS=4",
    "I_PRIMARY_CONTRAST_ROWS=8",
    "PRIMARY_CONTRAST_LEDGER_ROWS=24",
    "E4B3_EXACT_PRIMARY_LEDGER_SHAPE=PASS",
    "",
    "===== DESCRIPTIVE DIRECTION COUNTS — NOT GATES =====",
    f"C_RAW_POSITIVE_ROWS={c_pos}",
    f"C_RAW_NEGATIVE_ROWS={c_neg}",
    f"C_RAW_ZERO_ROWS={c_zero}",
    f"H_RAW_POSITIVE_ROWS={h_pos}",
    f"H_RAW_NEGATIVE_ROWS={h_neg}",
    f"H_RAW_ZERO_ROWS={h_zero}",
    f"K_STATE_POSITIVE_ROWS={k_pos}",
    f"K_STATE_NEGATIVE_ROWS={k_neg}",
    f"K_STATE_ZERO_ROWS={k_zero}",
    f"D_STATE_POSITIVE_ROWS={d_pos}",
    f"D_STATE_NEGATIVE_ROWS={d_neg}",
    f"D_STATE_ZERO_ROWS={d_zero}",
    f"I_STATE_POSITIVE_ROWS={i_pos}",
    f"I_STATE_NEGATIVE_ROWS={i_neg}",
    f"I_STATE_ZERO_ROWS={i_zero}",
    "DIRECTION_USED_AS_GATE=0",
    "MAGNITUDE_USED_AS_GATE=0",
    "SIGNIFICANCE_USED_AS_GATE=0",
    "CROSS_COMPONENT_AGREEMENT_USED_AS_GATE=0",
    "",
    "===== COVERAGE / COORDINATE BOUNDARY =====",
    "FULL_EVIDENCE_COVERAGE_EQUALS_COORDINATE_READINESS=0",
    "C_COORDINATE_SEMANTICS_FROZEN=0",
    "H_SERVICE_IMPLEMENTED=1",
    "H_ACCESS_IMPLEMENTED=0",
    "H_SERVICE_EQUALS_FULL_H_DIMENSION=0",
    "I_PRIMARY_ESTIMAND_COUNT=2",
    "I_SCALAR_AUTHORIZED=0",
    "",
    "===== CROSS-SURVEY BOUNDARY =====",
    "SCF_CPS_CEX_INDEPENDENT_SAMPLES=1",
    "MICRO_OBSERVATIONAL_UNIT_IDENTICAL=NO",
    "PERSON_LEVEL_CROSS_SURVEY_JOIN_AUTHORIZED=0",
    "CROSS_SURVEY_JOINT_COVARIANCE_AVAILABLE=0",
    "PSEUDO_COHORT_INTEGRATION_ONLY=1",
    "RAW_C_H_K_D_I_UNITS_COMMENSURABLE=0",
    "",
    "===== GEOMETRY BOUNDARY =====",
    "FIVE_COMPONENT_STATE_VECTOR_AUTHORIZED=0",
    "FIVE_COMPONENT_NORMALIZATION_AUTHORIZED=0",
    "RAW_EUCLIDEAN_DISTANCE_AUTHORIZED=0",
    "DIMENSIONALITY_TEST_AUTHORIZED=0",
    "FIVE_DIMENSIONALITY_PROVEN=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "",
    "E4B3_FULL_8_CELL_FIVE_COMPONENT_COVERAGE_CLOSEOUT=PASS",
    "E4C0_COMPONENT_COORDINATE_SEMANTICS_AND_TRANSFORMATION_PREFLIGHT_AUTHORIZED=1",
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
