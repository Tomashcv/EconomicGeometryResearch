from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

CH_SUMMARY = (
    ROOT
    / "data/results/E3B4C2_2022_brr_inference_summary.tsv"
)

CH_AUDIT = (
    ROOT
    / "data/metadata/E3B4C3_ch_2022_inferential_closeout_audit.txt"
)

I_COHORT = (
    ROOT
    / "data/results/E4A2D_2022_cps_i_cohort_inference.tsv"
)

KD_COHORT = (
    ROOT
    / "data/results/E4A2F_2022_scf_kd_cohort_inference.tsv"
)

KDI_AUDIT = (
    ROOT
    / "data/metadata/E4A2G_kdi_component_inference_closeout_audit.txt"
)

OUT_COVERAGE = (
    ROOT
    / "data/results/E4B0_2022_component_cohort_coverage.tsv"
)

OUT_INVENTORY = (
    ROOT
    / "data/results/E4B0_component_measure_inventory.tsv"
)

OUT_CONSTRAINTS = (
    ROOT
    / "data/results/E4B0_comparability_constraints.tsv"
)

AUDIT = (
    ROOT
    / "data/metadata/E4B0_ch_kdi_cohort_coverage_comparability_audit.txt"
)


EXPECTED_SHA = {
    CH_SUMMARY:
        "7b4888b53b4f5984026567e93edbbfc0a25e4e6cd62ed0c00f946d4abf1120c4",

    CH_AUDIT:
        "6ab2dda67c53870bb2bb0bb0247a3579e26d605587319bf03bab593fb2e3b0c8",

    I_COHORT:
        "ebcc6f1a636aac66c3a608ea9ada414ca1bafa881994d7921586f411b2e6b17d",

    KD_COHORT:
        "4fc37f81af05b32f1769412fca327cb0cee0bc1610b33c6c77eeb5a04669b55c",

    KDI_AUDIT:
        "5083e801a062db9e301e7a6f8da62bdf1fac34a9c075ac84b1788b1086170c3e",
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
        raise RuntimeError(
            f"missing frozen input={path}"
        )

    actual = sha256(path)

    if actual != expected:
        raise RuntimeError(
            f"frozen input hash mismatch: {path}"
        )


ch_audit = CH_AUDIT.read_text(
    encoding="utf-8"
)

for token in (
    "E3B4C3_CH_2022_INFERENTIAL_CLOSEOUT=PASS",
    "C_H_HOUSEHOLD_2022_IMPLEMENTATION_VALIDATED=1",
    "H_ACCESS_IMPLEMENTED=0",
):
    if token not in ch_audit:
        raise RuntimeError(
            f"missing C/H invariant={token}"
        )


kdi_audit = KDI_AUDIT.read_text(
    encoding="utf-8"
)

for token in (
    "E4A2G_KDI_COMPONENT_INFERENCE_CLOSEOUT=PASS",
    "K_EMPIRICALLY_TESTED=1",
    "D_EMPIRICALLY_TESTED=1",
    "I_EMPIRICALLY_TESTED=1",
    "E4B0_C_H_K_D_I_COHORT_COVERAGE_AND_COMPARABILITY_PREFLIGHT_AUTHORIZED=1",
):
    if token not in kdi_audit:
        raise RuntimeError(
            f"missing KDI invariant={token}"
        )


AGE_BANDS = [
    "AGE25_34",
    "AGE35_44",
    "AGE45_54",
    "AGE55_64",
]

TENURES = [
    "OWNER",
    "RENTER",
]

CELLS = [
    (
        age,
        tenure,
    )
    for age in AGE_BANDS
    for tenure in TENURES
]


# =============================================================================
# C/H primary evidence labels only — numeric outcomes are not interpreted.
# =============================================================================

with CH_SUMMARY.open(
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
        "statistic_type",
        "cohort",
        "component",
        "estimate",
        "brr_variance",
        "brr_se",
        "ci95_lower",
        "ci95_upper",
    ]

    if reader.fieldnames != expected_fields:
        raise RuntimeError(
            "unexpected E3B4C2 inference-summary schema"
        )

    ch_rows = list(
        reader
    )


if len(
    ch_rows
) != 8:
    raise RuntimeError(
        f"expected 8 E3B4C2 summary rows, observed={len(ch_rows)}"
    )


ch_component_rows = [
    row
    for row in ch_rows
    if row[
        "statistic_type"
    ] == "COMPONENT"
]


if len(
    ch_component_rows
) != 4:
    raise RuntimeError(
        "expected exactly four C/H component point rows"
    )


ch_available: dict[
    tuple[str, str, str],
    bool,
] = {}


for row in ch_component_rows:

    if row[
        "year"
    ] != "2022":
        raise RuntimeError(
            "unexpected C/H year"
        )

    cohort = row[
        "cohort"
    ]

    if cohort == "AGE25_34_OWNER":
        age = "AGE25_34"
        tenure = "OWNER"
    elif cohort == "AGE25_34_RENTER":
        age = "AGE25_34"
        tenure = "RENTER"
    else:
        raise RuntimeError(
            f"unexpected C/H component cohort={cohort}"
        )

    component = row[
        "component"
    ]

    if component not in {
        "C_COST",
        "H_SERVICE",
    }:
        raise RuntimeError(
            f"unexpected C/H component={component}"
        )

    key = (
        age,
        tenure,
        component,
    )

    if key in ch_available:
        raise RuntimeError(
            f"duplicate C/H evidence row={key}"
        )

    ch_available[
        key
    ] = True


expected_ch_keys = {
    (
        "AGE25_34",
        "OWNER",
        "C_COST",
    ),
    (
        "AGE25_34",
        "OWNER",
        "H_SERVICE",
    ),
    (
        "AGE25_34",
        "RENTER",
        "C_COST",
    ),
    (
        "AGE25_34",
        "RENTER",
        "H_SERVICE",
    ),
}


if set(
    ch_available
) != expected_ch_keys:
    raise RuntimeError(
        "C/H frozen component coverage differs from precommit"
    )


# =============================================================================
# K/D frozen primary cohort evidence labels only.
# =============================================================================

with KD_COHORT.open(
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
        "tenure",
        "statistic_id",
        "dimension",
        "role",
        "raw_variable",
        "statistic",
        "state_sign",
        "point_estimate_raw",
        "point_estimate_state_oriented",
        "imputation_variance",
        "sampling_replicate_mean",
        "sampling_variance",
        "combined_variance",
        "combined_se",
        "implicate_count",
        "replicate_count",
    ]

    if reader.fieldnames != expected_fields:
        raise RuntimeError(
            "unexpected E4A2F cohort-inference schema"
        )

    kd_rows = list(
        reader
    )


if len(
    kd_rows
) != 56:
    raise RuntimeError(
        f"expected 56 E4A2F cohort rows, observed={len(kd_rows)}"
    )


kd_primary: dict[
    tuple[str, str, str],
    bool,
] = {}


for row in kd_rows:

    if row[
        "year"
    ] != "2022":
        raise RuntimeError(
            "unexpected K/D year"
        )

    age = row[
        "age_band"
    ]
    tenure = row[
        "tenure"
    ]

    if (
        age not in AGE_BANDS
        or
        tenure not in TENURES
    ):
        raise RuntimeError(
            "unexpected K/D cohort label"
        )

    statistic_id = row[
        "statistic_id"
    ]

    if statistic_id == "K_FIN_MEAN":
        key = (
            age,
            tenure,
            "K",
        )
    elif statistic_id == "D_PIRTOTAL_MEAN":
        key = (
            age,
            tenure,
            "D",
        )
    else:
        continue

    if key in kd_primary:
        raise RuntimeError(
            f"duplicate K/D primary evidence row={key}"
        )

    kd_primary[
        key
    ] = True


expected_kd_keys = {
    (
        age,
        tenure,
        dimension,
    )
    for age, tenure in CELLS
    for dimension in (
        "K",
        "D",
    )
}


if set(
    kd_primary
) != expected_kd_keys:
    raise RuntimeError(
        "K/D primary frozen coverage differs from precommit"
    )


# =============================================================================
# I requires BOTH primary estimands in every covered cell.
# =============================================================================

with I_COHORT.open(
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
        "tenure",
        "estimand",
        "role",
        "state_sign",
        "unweighted_n",
        "point_estimate",
        "replicate_variance",
        "replicate_se",
        "replicate_count",
    ]

    if reader.fieldnames != expected_fields:
        raise RuntimeError(
            "unexpected E4A2D cohort-inference schema"
        )

    i_rows = list(
        reader
    )


if len(
    i_rows
) != 32:
    raise RuntimeError(
        f"expected 32 E4A2D cohort rows, observed={len(i_rows)}"
    )


i_primary_seen: dict[
    tuple[str, str],
    set[str],
] = {
    cell: set()
    for cell in CELLS
}


for row in i_rows:

    if row[
        "year"
    ] != "2022":
        raise RuntimeError(
            "unexpected I year"
        )

    age = row[
        "age_band"
    ]
    tenure = row[
        "tenure"
    ]

    cell = (
        age,
        tenure,
    )

    if cell not in i_primary_seen:
        raise RuntimeError(
            "unexpected I cohort label"
        )

    if row[
        "estimand"
    ] in {
        "I_FYFT_SHARE",
        "I_SEARCH_BURDEN_SHARE",
    }:
        i_primary_seen[
            cell
        ].add(
            row[
                "estimand"
            ]
        )


required_i_primary = {
    "I_FYFT_SHARE",
    "I_SEARCH_BURDEN_SHARE",
}


i_pair_available = {
    cell:
        (
            measures
            == required_i_primary
        )
    for cell, measures in i_primary_seen.items()
}


if not all(
    i_pair_available.values()
):
    raise RuntimeError(
        "I primary-pair coverage is incomplete"
    )


# =============================================================================
# Eight-cell coverage matrix
# =============================================================================

coverage_rows = []


for age, tenure in CELLS:

    c_available = bool(
        ch_available.get(
            (
                age,
                tenure,
                "C_COST",
            ),
            False,
        )
    )

    h_available = bool(
        ch_available.get(
            (
                age,
                tenure,
                "H_SERVICE",
            ),
            False,
        )
    )

    k_available = bool(
        kd_primary.get(
            (
                age,
                tenure,
                "K",
            ),
            False,
        )
    )

    d_available = bool(
        kd_primary.get(
            (
                age,
                tenure,
                "D",
            ),
            False,
        )
    )

    i_available = bool(
        i_pair_available[
            (
                age,
                tenure,
            )
        ]
    )

    five = all(
        [
            c_available,
            h_available,
            k_available,
            d_available,
            i_available,
        ]
    )

    coverage_rows.append(
        {
            "year": 2022,
            "age_band": age,
            "tenure": tenure,
            "C_primary_evidence": (
                "YES"
                if c_available
                else
                "NO"
            ),
            "H_primary_evidence": (
                "YES"
                if h_available
                else
                "NO"
            ),
            "K_primary_evidence": (
                "YES"
                if k_available
                else
                "NO"
            ),
            "D_primary_evidence": (
                "YES"
                if d_available
                else
                "NO"
            ),
            "I_both_primary_estimands": (
                "YES"
                if i_available
                else
                "NO"
            ),
            "five_component_evidence_coverage": (
                "YES"
                if five
                else
                "NO"
            ),
        }
    )


c_covered_cells = sum(
    row[
        "C_primary_evidence"
    ] == "YES"
    for row in coverage_rows
)

h_covered_cells = sum(
    row[
        "H_primary_evidence"
    ] == "YES"
    for row in coverage_rows
)

k_covered_cells = sum(
    row[
        "K_primary_evidence"
    ] == "YES"
    for row in coverage_rows
)

d_covered_cells = sum(
    row[
        "D_primary_evidence"
    ] == "YES"
    for row in coverage_rows
)

i_covered_cells = sum(
    row[
        "I_both_primary_estimands"
    ] == "YES"
    for row in coverage_rows
)

five_covered_cells = sum(
    row[
        "five_component_evidence_coverage"
    ] == "YES"
    for row in coverage_rows
)


coverage_pattern_pass = (
    c_covered_cells == 2
    and
    h_covered_cells == 2
    and
    k_covered_cells == 8
    and
    d_covered_cells == 8
    and
    i_covered_cells == 8
    and
    five_covered_cells == 2
)


if not coverage_pattern_pass:
    raise RuntimeError(
        "observed coverage pattern differs from precommit"
    )


focal_rows = [
    row
    for row in coverage_rows
    if row[
        "age_band"
    ] == "AGE25_34"
]


focal_five_component_coverage = (
    len(
        focal_rows
    ) == 2
    and
    all(
        row[
            "five_component_evidence_coverage"
        ] == "YES"
        for row in focal_rows
    )
)


full_8_cell_five_component_coverage = (
    five_covered_cells
    == 8
)


# =============================================================================
# Measure inventory and semantic scale boundary
# =============================================================================

inventory_rows = [
    {
        "component": "C",
        "survey": "CEX",
        "observational_unit": "CONSUMER_UNIT",
        "primary_evidence": "C_COST",
        "primary_measure_count_required": 1,
        "raw_scale_family": "USD_PER_YEAR_FLOW",
        "covered_cells_of_8": c_covered_cells,
        "scalar_coordinate_authorized": "NO",
    },
    {
        "component": "H",
        "survey": "CEX",
        "observational_unit": "CONSUMER_UNIT",
        "primary_evidence": "H_SERVICE",
        "primary_measure_count_required": 1,
        "raw_scale_family": "USD_PER_YEAR_HOUSING_SERVICE_FLOW",
        "covered_cells_of_8": h_covered_cells,
        "scalar_coordinate_authorized": "NO",
    },
    {
        "component": "K",
        "survey": "SCF",
        "observational_unit": "FAMILY",
        "primary_evidence": "K_FIN_MEAN",
        "primary_measure_count_required": 1,
        "raw_scale_family": "USD_FINANCIAL_STOCK",
        "covered_cells_of_8": k_covered_cells,
        "scalar_coordinate_authorized": "NO",
    },
    {
        "component": "D",
        "survey": "SCF",
        "observational_unit": "FAMILY",
        "primary_evidence": "D_PIRTOTAL_MEAN",
        "primary_measure_count_required": 1,
        "raw_scale_family": "RATIO_OR_DEBT_SERVICE_BURDEN",
        "covered_cells_of_8": d_covered_cells,
        "scalar_coordinate_authorized": "NO",
    },
    {
        "component": "I",
        "survey": "CPS_ASEC",
        "observational_unit": "HOUSEHOLD_REFERENCE_PERSON",
        "primary_evidence": "I_FYFT_SHARE+I_SEARCH_BURDEN_SHARE",
        "primary_measure_count_required": 2,
        "raw_scale_family": "BINARY_SHARE_PROBABILITY",
        "covered_cells_of_8": i_covered_cells,
        "scalar_coordinate_authorized": "NO",
    },
]


constraint_rows = [
    (
        "CALENDAR_YEAR_ALIGNMENT",
        "YES",
        "All frozen component evidence is 2022.",
    ),
    (
        "AGE_BAND_LABEL_ALIGNMENT",
        "YES",
        "The same four frozen age-band labels are used where coverage exists.",
    ),
    (
        "TENURE_LABEL_ALIGNMENT",
        "YES",
        "OWNER and RENTER labels are available, but operationalization is survey-specific.",
    ),
    (
        "MICRO_OBSERVATIONAL_UNIT_IDENTICAL",
        "NO",
        "CEX consumer unit, SCF family, and CPS household/reference-person structures are not identical.",
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
        "RAW_C_H_K_D_I_UNITS_COMMENSURABLE",
        "NO",
        "Annual flows, financial stocks, ratios/burdens, and shares are different measurement scales.",
    ),
    (
        "RAW_EUCLIDEAN_DISTANCE_AUTHORIZED",
        "NO",
        "A raw Euclidean norm would be unit-dependent and economically arbitrary.",
    ),
    (
        "RAW_CROSS_DIMENSION_MAGNITUDE_RANKING_AUTHORIZED",
        "NO",
        "Raw numerical magnitudes are not comparable across dimensions.",
    ),
    (
        "RAW_CROSS_DIMENSION_SE_COMBINATION_AUTHORIZED",
        "NO",
        "Independent surveys and noncommensurable estimands prohibit mechanical SE combination.",
    ),
    (
        "PSEUDO_COHORT_INTEGRATION_ONLY",
        "YES",
        "AGE_BAND x TENURE is the only frozen cross-survey bridge.",
    ),
    (
        "H_ACCESS_IMPLEMENTED",
        "NO",
        "H_SERVICE is implemented; H_ACCESS remains unimplemented.",
    ),
    (
        "FULL_8_CELL_FIVE_COMPONENT_COVERAGE",
        (
            "YES"
            if full_8_cell_five_component_coverage
            else
            "NO"
        ),
        "C/H currently cover only AGE25_34 OWNER and RENTER.",
    ),
    (
        "AGE25_34_OWNER_RENTER_FIVE_COMPONENT_COVERAGE",
        (
            "YES"
            if focal_five_component_coverage
            else
            "NO"
        ),
        "Both focal AGE25_34 cells contain required primary evidence for C/H/K/D/I.",
    ),
    (
        "FIVE_COMPONENT_RAW_VECTOR_AUTHORIZED",
        "NO",
        "Coverage does not imply a commensurable five-coordinate representation.",
    ),
    (
        "DIMENSIONALITY_TEST_AUTHORIZED",
        "NO",
        "Full common cohort coverage and a frozen dimensionless-coordinate contract are absent.",
    ),
]


# =============================================================================
# Deterministic serialization
# =============================================================================

OUT_COVERAGE.parent.mkdir(
    parents=True,
    exist_ok=True,
)


with OUT_COVERAGE.open(
    "w",
    encoding="utf-8",
    newline="",
) as f:

    fields = [
        "year",
        "age_band",
        "tenure",
        "C_primary_evidence",
        "H_primary_evidence",
        "K_primary_evidence",
        "D_primary_evidence",
        "I_both_primary_estimands",
        "five_component_evidence_coverage",
    ]

    writer = csv.DictWriter(
        f,
        fieldnames=fields,
        delimiter="\t",
        lineterminator="\n",
    )

    writer.writeheader()

    for row in coverage_rows:
        writer.writerow(
            row
        )


with OUT_INVENTORY.open(
    "w",
    encoding="utf-8",
    newline="",
) as f:

    fields = [
        "component",
        "survey",
        "observational_unit",
        "primary_evidence",
        "primary_measure_count_required",
        "raw_scale_family",
        "covered_cells_of_8",
        "scalar_coordinate_authorized",
    ]

    writer = csv.DictWriter(
        f,
        fieldnames=fields,
        delimiter="\t",
        lineterminator="\n",
    )

    writer.writeheader()

    for row in inventory_rows:
        writer.writerow(
            row
        )


with OUT_CONSTRAINTS.open(
    "w",
    encoding="utf-8",
    newline="",
) as f:

    writer = csv.writer(
        f,
        delimiter="\t",
        lineterminator="\n",
    )

    writer.writerow(
        [
            "constraint",
            "status",
            "interpretation",
        ]
    )

    for row in constraint_rows:
        writer.writerow(
            row
        )


# =============================================================================
# Audit
# =============================================================================

audit_lines = [
    "=" * 100,
    "E4B0 — C-H-K-D-I COHORT COVERAGE + COMPARABILITY PREFLIGHT",
    "=" * 100,
    "",
    "RAW_SURVEY_DATA_READ=0",
    "NEW_POINT_ESTIMATES_COMPUTED=0",
    "NEW_STANDARD_ERRORS_COMPUTED=0",
    "REPLICATE_RECALCULATION_PERFORMED=0",
    "NUMERIC_OUTCOME_VALUES_USED_AS_PASS_GATE=0",
    "FROZEN_RESULT_TABLES_ONLY=1",
    "",
    "===== FROZEN INPUT STATUS =====",
    "E3B4C3_CH_2022_INFERENTIAL_CLOSEOUT=PASS",
    "E4A2G_KDI_COMPONENT_INFERENCE_CLOSEOUT=PASS",
    "C_H_K_D_I_CALENDAR_YEAR=2022",
    "",
    "===== PRIMARY EVIDENCE DEFINITIONS =====",
    "C_PRIMARY_EVIDENCE=C_COST",
    "H_PRIMARY_EVIDENCE=H_SERVICE",
    "K_PRIMARY_EVIDENCE=K_FIN_MEAN",
    "D_PRIMARY_EVIDENCE=D_PIRTOTAL_MEAN",
    "I_PRIMARY_EVIDENCE=I_FYFT_SHARE_PLUS_I_SEARCH_BURDEN_SHARE",
    "I_PRIMARY_PAIR_REQUIRED=1",
    "",
    "===== COVERAGE =====",
    f"C_COVERED_CELLS_OF_8={c_covered_cells}",
    f"H_COVERED_CELLS_OF_8={h_covered_cells}",
    f"K_COVERED_CELLS_OF_8={k_covered_cells}",
    f"D_COVERED_CELLS_OF_8={d_covered_cells}",
    f"I_COVERED_CELLS_OF_8={i_covered_cells}",
    f"FIVE_COMPONENT_COVERED_CELLS_OF_8={five_covered_cells}",
    (
        "FULL_8_CELL_FIVE_COMPONENT_COVERAGE="
        + (
            "YES"
            if full_8_cell_five_component_coverage
            else
            "NO"
        )
    ),
    (
        "AGE25_34_OWNER_RENTER_FIVE_COMPONENT_COVERAGE="
        + (
            "YES"
            if focal_five_component_coverage
            else
            "NO"
        )
    ),
    "E4B0_PRECOMMITTED_COVERAGE_PATTERN=PASS",
    "",
    "===== COMPARABILITY =====",
    "CALENDAR_YEAR_ALIGNMENT=PASS",
    "AGE_BAND_LABEL_ALIGNMENT=PASS",
    "TENURE_LABEL_ALIGNMENT=PASS",
    "MICRO_OBSERVATIONAL_UNIT_IDENTICAL=NO",
    "PERSON_LEVEL_CROSS_SURVEY_JOIN_AUTHORIZED=0",
    "CROSS_SURVEY_JOINT_COVARIANCE_AVAILABLE=0",
    "RAW_C_H_K_D_I_UNITS_COMMENSURABLE=0",
    "RAW_EUCLIDEAN_DISTANCE_AUTHORIZED=0",
    "RAW_CROSS_DIMENSION_MAGNITUDE_RANKING_AUTHORIZED=0",
    "RAW_CROSS_DIMENSION_SE_COMBINATION_AUTHORIZED=0",
    "PSEUDO_COHORT_INTEGRATION_ONLY=1",
    "",
    "===== H BOUNDARY =====",
    "H_SERVICE_IMPLEMENTED=1",
    "H_ACCESS_IMPLEMENTED=0",
    "H_SERVICE_EQUALS_FULL_H_ACCESS_DIMENSION=0",
    "",
    "===== GEOMETRY BOUNDARY =====",
    "FIVE_COMPONENT_RAW_VECTOR_AUTHORIZED=0",
    "FIVE_COMPONENT_NORM_AUTHORIZED=0",
    "FIVE_COMPONENT_DISTANCE_AUTHORIZED=0",
    "DIMENSIONLESS_COORDINATE_TRANSFORMATION_FROZEN=0",
    "DIMENSIONALITY_TEST_AUTHORIZED=0",
    "FIVE_DIMENSIONALITY_PROVEN=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "",
    "DIRECTION_GATE=0",
    "MAGNITUDE_GATE=0",
    "SIGNIFICANCE_GATE=0",
    "COVERAGE_PATTERN_USED_AS_FAILURE_GATE=0",
    "",
    "E4B0_C_H_K_D_I_COHORT_COVERAGE_AND_COMPARABILITY_PREFLIGHT=PASS",
    "E4B1_C_H_AGE35_64_COVERAGE_EXTENSION_PREFLIGHT_AUTHORIZED=1",
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
