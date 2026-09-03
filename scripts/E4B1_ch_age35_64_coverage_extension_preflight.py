from __future__ import annotations

import ast
import csv
import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

LINEAGE = (
    ROOT
    / "data/metadata/E4B1_frozen_cex_estimator_lineage.tsv"
)

CONTRACT = (
    ROOT
    / "data/metadata/E4B1_ch_age35_64_coverage_extension_contract.json"
)

MAPPING = (
    ROOT
    / "data/metadata/E3A4_mapping.tsv"
)

POINT_CONTRACT = (
    ROOT
    / "data/metadata/E3B3C4_estimator_contract.tsv"
)

BRR_CONTRACT = (
    ROOT
    / "data/metadata/E3B4C1_exact_brr_engine_contract.json"
)

POINT_SCRIPT = (
    ROOT
    / "scripts/E3B4A_V2_corrected_cohort_rerun.py"
)

BRR_SCRIPT = (
    ROOT
    / "scripts/E3B4C2_first_brr_execution.py"
)

POINT_AUDIT = (
    ROOT
    / "data/metadata/E3B4A_V2_corrected_cohort_rerun_audit.txt"
)

BRR_AUDIT = (
    ROOT
    / "data/metadata/E3B4C2_first_brr_execution_audit.txt"
)

AUDIT = (
    ROOT
    / "data/metadata/E4B1_ch_age35_64_coverage_extension_preflight_audit.txt"
)

OUT_GRID = (
    ROOT
    / "data/metadata/E4B1_frozen_extended_cex_cohort_grid.tsv"
)

OUT_SHAPE = (
    ROOT
    / "data/metadata/E4B1_e4b2_expected_output_shape.tsv"
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()

    with path.open("rb") as f:
        for block in iter(
            lambda: f.read(1024 * 1024),
            b"",
        ):
            h.update(block)

    return h.hexdigest()


# =============================================================================
# Lineage snapshot must match current tracked artifacts exactly.
# =============================================================================

with LINEAGE.open(
    "r",
    encoding="utf-8",
    newline="",
) as f:

    reader = csv.DictReader(
        f,
        delimiter="\t",
    )

    if reader.fieldnames != [
        "artifact",
        "sha256",
        "role",
    ]:
        raise RuntimeError(
            "unexpected E4B1 lineage schema"
        )

    lineage_rows = list(
        reader
    )


if len(
    lineage_rows
) != 16:
    raise RuntimeError(
        f"expected 16 lineage rows, observed={len(lineage_rows)}"
    )


for row in lineage_rows:

    path = (
        ROOT
        / row[
            "artifact"
        ]
    )

    if not path.is_file():
        raise RuntimeError(
            f"missing lineage artifact={path}"
        )

    actual = sha256(
        path
    )

    if actual != row[
        "sha256"
    ]:
        raise RuntimeError(
            f"lineage hash mismatch={path}"
        )


# =============================================================================
# Frozen cross-survey CEX cohort semantics
# =============================================================================

with MAPPING.open(
    "r",
    encoding="utf-8",
    newline="",
) as f:

    reader = csv.DictReader(
        f,
        delimiter="\t",
    )

    mapping_rows = [
        row
        for row in reader
        if row[
            "survey"
        ] == "CEX"
    ]


mapping = {
    row[
        "concept"
    ]: row
    for row in mapping_rows
}


required_mapping = {
    "reference_age": (
        "AGE_REF",
        "direct",
        "FROZEN",
    ),
    "owner": (
        "CUTENURE",
        "1|2|3",
        "FROZEN",
    ),
    "renter": (
        "CUTENURE",
        "4",
        "FROZEN",
    ),
    "other_tenure": (
        "CUTENURE",
        "5|6|missing|unexpected",
        "FROZEN",
    ),
    "weight": (
        "FINLWT21",
        "direct",
        "FROZEN",
    ),
}


for concept, expected in required_mapping.items():

    row = mapping.get(
        concept
    )

    if row is None:
        raise RuntimeError(
            f"missing CEX mapping concept={concept}"
        )

    observed = (
        row[
            "source_variables"
        ],
        row[
            "canonical_rule"
        ],
        row[
            "status"
        ],
    )

    if observed != expected:
        raise RuntimeError(
            f"CEX mapping mismatch concept={concept}: {observed}"
        )


cohort_mapping_pass = True


# =============================================================================
# Point estimator static contract
# =============================================================================

with POINT_CONTRACT.open(
    "r",
    encoding="utf-8",
    newline="",
) as f:

    rows = list(
        csv.DictReader(
            f,
            delimiter="\t",
        )
    )


point_rules = {
    row[
        "rule"
    ]:
        row[
            "value"
        ]
    for row in rows
}


required_point_rules = {
    "INTERVIEW_QUARTERS":
        "221,222,223,224,231",

    "INTERVIEW_REF_YEAR":
        "2022",

    "INTERVIEW_REF_MONTHS":
        "1..12",

    "QNUM":
        "4",

    "INTERVIEW_POPWT":
        "FINLWT21/4*MO_SCOPE/3",

    "DIARY_QUARTERS":
        "221,222,223,224",

    "DIARY_MO_SCOPE":
        "3",

    "DIARY_POPWT":
        "FINLWT21/4",

    "DIARY_PERIODICITY_MULTIPLIER":
        "13",

    "SOURCE_SELECTION":
        "FROZEN_INTEGRATED_HIERARCHY",

    "HIERARCHY_FACTOR":
        "UCC_LEVEL_1_OR_4",

    "ZERO_SPENDERS_INCLUDED":
        "1",

    "MISSING_COST_AFTER_JOIN":
        "ZERO",

    "NEGATIVE_COST":
        "PRESERVE",

    "COST_CLIPPING":
        "PROHIBITED",

    "COST_WINSORIZATION":
        "PROHIBITED",

    "INTERVIEW_DIARY_RECORD_JOIN":
        "PROHIBITED",

    "C_COST_PRIMARY_UCCS":
        "435",

    "H_SERVICE_CORE_UCCS":
        "99",

    "BRR_REPLICATES":
        "44",
}


for rule, expected in required_point_rules.items():

    observed = point_rules.get(
        rule
    )

    if observed != expected:
        raise RuntimeError(
            f"point-estimator contract mismatch "
            f"{rule}: expected={expected} observed={observed}"
        )


point_contract_pass = True


# =============================================================================
# BRR static contract
# =============================================================================

brr = json.loads(
    BRR_CONTRACT.read_text(
        encoding="utf-8"
    )
)


expected_reps = [
    f"WTREP{i:02d}"
    for i in range(
        1,
        45,
    )
]


brr_checks = [
    brr[
        "full_sample_weight"
    ] == "FINLWT21",

    brr[
        "replicate_count"
    ] == 44,

    brr[
        "replicate_weights"
    ] == expected_reps,

    brr[
        "brr_variance"
    ] == "(1/44)*SUM((THETA_R-THETA)^2)",

    brr[
        "brr_se"
    ] == "SQRT(BRR_VARIANCE)",

    brr[
        "difference_replication"
    ] == "DIRECT_RENTER_MINUS_OWNER",

    brr[
        "ratio_replication"
    ] == "DIRECT_RENTER_DIV_OWNER",

    brr[
        "difference_independence_shortcut_prohibited"
    ] is True,

    brr[
        "interview"
    ][
        "replicate_denominator_uses_same_replicate_weight"
    ] is True,

    brr[
        "diary"
    ][
        "replicate_denominator_uses_same_replicate_weight"
    ] is True,

    brr[
        "hierarchy_factor_applied_inside_replicate"
    ] is True,

    brr[
        "component_sum_inside_replicate"
    ] is True,

    brr[
        "source_variance_posthoc_sum_prohibited"
    ] is True,
]


if not all(
    brr_checks
):
    raise RuntimeError(
        "BRR frozen contract mismatch"
    )


if brr[
    "cohorts"
] != {
    "AGE25_34_OWNER": {
        "age_min": 25,
        "age_max": 34,
        "cutensure": [
            1,
            2,
            3,
        ],
    },
    "AGE25_34_RENTER": {
        "age_min": 25,
        "age_max": 34,
        "cutensure": [
            4,
        ],
    },
}:
    raise RuntimeError(
        "existing BRR cohort contract is not exact AGE25_34 control"
    )


brr_contract_pass = True


# =============================================================================
# Validated audits must be PASS before extension.
# =============================================================================

point_audit = POINT_AUDIT.read_text(
    encoding="utf-8"
)

for token in (
    "E3B4A_V2_CORRECTED_COHORT_RERUN=PASS",
    "CORRECTED_COHORT_POINT_ESTIMATES_VALIDATED=1",
):
    if token not in point_audit:
        raise RuntimeError(
            f"missing point audit invariant={token}"
        )


brr_audit = BRR_AUDIT.read_text(
    encoding="utf-8"
)

for token in (
    "E3B4C2_FIRST_BRR_EXECUTION=PASS",
    "BRR_REPLICATE_COUNT=44",
):
    if token not in brr_audit:
        raise RuntimeError(
            f"missing BRR audit invariant={token}"
        )


validated_existing_execution_pass = True


# =============================================================================
# Static source audit: both validated scripts currently restrict to 25-34.
# This proves E4B2's intended change is an explicit cohort extension rather
# than silently accepting an already-broadened executor.
# =============================================================================

point_source = POINT_SCRIPT.read_text(
    encoding="utf-8"
)

brr_source = BRR_SCRIPT.read_text(
    encoding="utf-8"
)


required_point_anchors = [
    'age.between(\n        25,\n        34,\n    )',
    'tenure.isin(\n            [1, 2, 3]\n        )',
    'tenure.eq(4)',
    '"AGE25_34_OWNER"',
    '"AGE25_34_RENTER"',
]


for anchor in required_point_anchors:
    if anchor not in point_source:
        raise RuntimeError(
            f"validated point-script anchor missing={anchor!r}"
        )


required_brr_anchors = [
    'age.between(\n        25,\n        34,\n    )',
    'tenure.isin(\n            [1, 2, 3]\n        )',
    'tenure.eq(4)',
    '"AGE25_34_OWNER"',
    '"AGE25_34_RENTER"',
]


for anchor in required_brr_anchors:
    if anchor not in brr_source:
        raise RuntimeError(
            f"validated BRR-script anchor missing={anchor!r}"
        )


# Also ensure no later target labels are already embedded in either validated
# executor.
for forbidden in (
    "AGE35_44_OWNER",
    "AGE35_44_RENTER",
    "AGE45_54_OWNER",
    "AGE45_54_RENTER",
    "AGE55_64_OWNER",
    "AGE55_64_RENTER",
):
    if (
        forbidden in point_source
        or
        forbidden in brr_source
    ):
        raise RuntimeError(
            f"unexpected pre-existing expanded cohort label={forbidden}"
        )


existing_executor_scope_pass = True


# =============================================================================
# Frozen E4B2 extension grid / exact expected shapes
# =============================================================================

contract = json.loads(
    CONTRACT.read_text(
        encoding="utf-8"
    )
)


grid = contract[
    "frozen_cohort_grid"
]


expected_grid = [
    (
        "AGE25_34_OWNER",
        25,
        34,
        "1,2,3",
    ),
    (
        "AGE25_34_RENTER",
        25,
        34,
        "4",
    ),
    (
        "AGE35_44_OWNER",
        35,
        44,
        "1,2,3",
    ),
    (
        "AGE35_44_RENTER",
        35,
        44,
        "4",
    ),
    (
        "AGE45_54_OWNER",
        45,
        54,
        "1,2,3",
    ),
    (
        "AGE45_54_RENTER",
        45,
        54,
        "4",
    ),
    (
        "AGE55_64_OWNER",
        55,
        64,
        "1,2,3",
    ),
    (
        "AGE55_64_RENTER",
        55,
        64,
        "4",
    ),
]


observed_grid = [
    (
        x[
            "cohort"
        ],
        x[
            "age_min"
        ],
        x[
            "age_max"
        ],
        ",".join(
            str(v)
            for v in x[
                "cutensure"
            ]
        ),
    )
    for x in grid
]


if observed_grid != expected_grid:
    raise RuntimeError(
        "E4B2 frozen cohort grid mismatch"
    )


shape = contract[
    "E4B2_expected_shapes"
]


expected_shape = {
    "cohort_count":
        8,

    "component_count":
        2,

    "age_band_count":
        4,

    "replicate_count":
        44,

    "full_sample_component_rows":
        16,

    "owner_renter_component_comparison_rows":
        8,

    "BRR_denominator_rows":
        720,

    "BRR_component_replicate_rows":
        704,

    "BRR_difference_replicate_rows":
        352,

    "BRR_ratio_replicate_rows":
        352,

    "BRR_inference_component_rows":
        16,

    "BRR_inference_difference_rows":
        8,

    "BRR_inference_ratio_rows":
        8,

    "BRR_inference_summary_rows":
        32,
}


if shape != expected_shape:
    raise RuntimeError(
        f"E4B2 expected shape mismatch={shape}"
    )


extension_contract_pass = True


# =============================================================================
# Serialize static preflight tables
# =============================================================================

OUT_GRID.parent.mkdir(
    parents=True,
    exist_ok=True,
)


with OUT_GRID.open(
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
            "cohort",
            "age_min",
            "age_max",
            "tenure",
            "cutensure",
            "status",
        ]
    )

    for (
        cohort,
        low,
        high,
        cutensure,
    ) in expected_grid:

        tenure = (
            "OWNER"
            if cohort.endswith(
                "_OWNER"
            )
            else
            "RENTER"
        )

        writer.writerow(
            [
                cohort,
                low,
                high,
                tenure,
                cutensure,
                "FROZEN_FOR_E4B2",
            ]
        )


with OUT_SHAPE.open(
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
            "item",
            "expected_rows",
        ]
    )

    for item in (
        "full_sample_component_rows",
        "owner_renter_component_comparison_rows",
        "BRR_denominator_rows",
        "BRR_component_replicate_rows",
        "BRR_difference_replicate_rows",
        "BRR_ratio_replicate_rows",
        "BRR_inference_component_rows",
        "BRR_inference_difference_rows",
        "BRR_inference_ratio_rows",
        "BRR_inference_summary_rows",
    ):
        writer.writerow(
            [
                item,
                shape[
                    item
                ],
            ]
        )


# =============================================================================
# Audit
# =============================================================================

audit_lines = [
    "=" * 100,
    "E4B1 — C-H AGE35-64 COVERAGE EXTENSION PREFLIGHT",
    "=" * 100,
    "",
    "RAW_CEX_DATA_READ=0",
    "NEW_C_H_VALUES_OPENED=0",
    "BRR_REPLICATE_VALUES_OPENED=0",
    "FROZEN_CODE_METADATA_RESULTS_ONLY=1",
    "",
    "===== EXISTING VALIDATED CEX LINEAGE =====",
    f"E4B1_LINEAGE_ARTIFACT_COUNT={len(lineage_rows)}",
    "E4B1_LINEAGE_HASH_RECHECK=PASS",
    "E3A4_CEX_COHORT_MAPPING=PASS",
    "E3B3C4_POINT_ESTIMATOR_CONTRACT=PASS",
    "E3B4C1_BRR_ENGINE_CONTRACT=PASS",
    "E3B4A_V2_VALIDATED_POINT_EXECUTION=PASS",
    "E3B4C2_VALIDATED_BRR_EXECUTION=PASS",
    "",
    "===== CURRENT EXECUTOR SCOPE =====",
    "CURRENT_CEX_COHORT_COUNT=2",
    "CURRENT_COHORT_1=AGE25_34_OWNER",
    "CURRENT_COHORT_2=AGE25_34_RENTER",
    "CURRENT_POINT_EXECUTOR_SCOPE_AUDIT=PASS",
    "CURRENT_BRR_EXECUTOR_SCOPE_AUDIT=PASS",
    "",
    "===== FROZEN E4B2 EXTENSION =====",
    "E4B2_COHORT_COUNT=8",
    "E4B2_AGE_BANDS=AGE25_34,AGE35_44,AGE45_54,AGE55_64",
    "E4B2_OWNER_CUTENURE=1,2,3",
    "E4B2_RENTER_CUTENURE=4",
    "E4B2_OTHER_TENURE_EXCLUDED=1",
    "E4B2_COHORT_GRID_CONTRACT=PASS",
    "",
    "===== ESTIMATOR IMMUTABILITY =====",
    "SOURCE_FAMILY_CHANGES_AUTHORIZED=0",
    "UCC_MAPPING_CHANGES_AUTHORIZED=0",
    "CALENDAR_SCOPE_CHANGES_AUTHORIZED=0",
    "WEIGHT_FORMULA_CHANGES_AUTHORIZED=0",
    "BRR_FORMULA_CHANGES_AUTHORIZED=0",
    "COMPONENT_DEFINITION_CHANGES_AUTHORIZED=0",
    "TENURE_DEFINITION_CHANGES_AUTHORIZED=0",
    "ONLY_COHORT_GRID_EXTENSION_AUTHORIZED=1",
    "",
    "===== AGE25_34 INVARIANCE CONTROL =====",
    "AGE25_34_POINT_ESTIMATE_REPRODUCTION_REQUIRED=1",
    "AGE25_34_COMPONENT_REPLICATE_REPRODUCTION_REQUIRED=1",
    "AGE25_34_DIFFERENCE_REPLICATE_REPRODUCTION_REQUIRED=1",
    "AGE25_34_RATIO_REPLICATE_REPRODUCTION_REQUIRED=1",
    "AGE25_34_REPRODUCTION_ATOL=1e-8",
    "",
    "===== E4B2 EXPECTED SHAPE =====",
    "E4B2_FULL_SAMPLE_COMPONENT_ROWS=16",
    "E4B2_OWNER_RENTER_COMPARISON_ROWS=8",
    "E4B2_BRR_DENOMINATOR_ROWS=720",
    "E4B2_BRR_COMPONENT_REPLICATE_ROWS=704",
    "E4B2_BRR_DIFFERENCE_REPLICATE_ROWS=352",
    "E4B2_BRR_RATIO_REPLICATE_ROWS=352",
    "E4B2_BRR_INFERENCE_SUMMARY_ROWS=32",
    "E4B2_EXACT_OUTPUT_SHAPE_CONTRACT=PASS",
    "",
    "===== OUTCOME-INDEPENDENT GATES =====",
    "DIRECTION_GATE=0",
    "MAGNITUDE_GATE=0",
    "SIGNIFICANCE_GATE=0",
    "OWNER_RENTER_DIRECTION_GATE=0",
    "CROSS_DIMENSION_GATE=0",
    "NO_OUTCOME_BASED_CH_EXTENSION_GATE=PASS",
    "",
    "H_ACCESS_IMPLEMENTED=0",
    "FIVE_COMPONENT_NORMALIZATION_AUTHORIZED=0",
    "FIVE_COMPONENT_VECTOR_AUTHORIZED=0",
    "DIMENSIONALITY_TEST_AUTHORIZED=0",
    "FIVE_DIMENSIONALITY_PROVEN=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "",
    "E4B1_C_H_AGE35_64_COVERAGE_EXTENSION_PREFLIGHT=PASS",
    "E4B2_FIRST_C_H_8_CELL_COVERAGE_EXECUTION_AUTHORIZED=1",
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
