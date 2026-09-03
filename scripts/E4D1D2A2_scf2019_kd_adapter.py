from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from E4A2E_scf_replicate_mi_engine import (
    IMPLICATE_COUNT,
    REPLICATE_COUNT,
    effective_replicate_weights,
    scf_owner_renter_difference_inference,
    scf_statistic_inference,
)


ROOT = Path(__file__).resolve().parents[1]

CONTRACT = (
    ROOT
    / "data/metadata/E4A2F_first_scf_kd_inference_contract.json"
)

MAPPING = ROOT / "data/metadata/E3A4_mapping.tsv"

ARCH = (
    ROOT
    / "data/metadata/E4A_kdi_household_state_architecture.json"
)

E4A2_CONTRACT = (
    ROOT
    / "data/metadata/E4A2_kdi_estimator_contract.json"
)

E4A2A_AUDIT = (
    ROOT
    / "data/metadata/E4D1D_2019_runtime/SCF/E4A2A_replicate_weight_schema_audit.txt"
)

E4A2D_AUDIT = (
    ROOT
    / "data/metadata/E4D1D_2019_runtime/SCF/E4A2D_first_cps_i_inference_execution_audit.txt"
)

E4A2E_CONTRACT = (
    ROOT
    / "data/metadata/E4A2E_scf_replicate_mi_engine_contract.json"
)

E4A2E_ENGINE = (
    ROOT
    / "scripts/E4A2E_scf_replicate_mi_engine.py"
)

E4A2E_AUDIT = (
    ROOT
    / "data/metadata/E4D1D_2019_runtime/SCF/E4A2E_exact_scf_replicate_mi_engine_preflight_audit.txt"
)

E4A2E_CHECKS = (
    ROOT
    / "data/metadata/E4A2E_synthetic_scf_engine_checks.tsv"
)

SCF_FULL_ZIP = (
    ROOT
    / "data/raw/scf/2019/scf2019s.zip"
)

SCF_SUMMARY_ZIP = (
    ROOT
    / "data/raw/scf/2019/scfp2019s.zip"
)

SCF_REP_ZIP = (
    ROOT
    / "data/raw/scf/2019/scf2019rw1s.zip"
)

CODEBOOK = (
    ROOT
    / "data/raw/scf/2019/codebk2019.txt"
)

OUT_COHORT = (
    ROOT
    / "data/results/E4D1D_2019_runtime/SCF/E4A2F_2022_scf_kd_cohort_inference.tsv"
)

OUT_DIFF = (
    ROOT
    / "data/results/E4D1D_2019_runtime/SCF/E4A2F_2022_scf_kd_owner_renter_differences.tsv"
)

OUT_IMPLICATES = (
    ROOT
    / "data/results/E4D1D_2019_runtime/SCF/E4A2F_2022_scf_kd_implicate_statistics.tsv"
)

OUT_REPLICATES = (
    ROOT
    / "data/results/E4D1D_2019_runtime/SCF/E4A2F_2022_scf_kd_replicate_statistics.tsv"
)

OUT_SUPPORT = (
    ROOT
    / "data/results/E4D1D_2019_runtime/SCF/E4A2F_2022_scf_kd_cohort_support.tsv"
)

AUDIT = (
    ROOT
    / "data/metadata/E4D1D_2019_runtime/SCF/E4A2F_first_scf_kd_inference_execution_audit.txt"
)


EXPECTED_SHA = {
    MAPPING:
        "12783a626edf3af3b8dccadfbe3d084c1b2af493a1e51966a963b20226f1c97e",

    ARCH:
        "72f8967f5dd3be78bd5b3cb12e5ee0af249a2bfaae94d0312070f143c181b986",

    E4A2_CONTRACT:
        "40c85c629285e7cf0999250914d7928b9825047682bf41362327060adaef4f0a",

    E4A2A_AUDIT:
        "ebf719755fbe7d0f6c5b0023f3900d435228b2e36d97f1e9a7da3fc4fe76b546",

    E4A2D_AUDIT:
        "3a11c270856fb82bd96506befe7317bf33b5e07bf85a2d981b5490007328442a",

    E4A2E_CONTRACT:
        "e535ef36f3829e759fd0563d9eeb06dbb54afb8db4bceca42456bf6d217a3064",

    E4A2E_ENGINE:
        "216c4e8bd52104bba0db3d69be17ac54fa8c86893c9f21c6c1b6ec5890d9722a",

    E4A2E_AUDIT:
        "6ab9c355a2a63ee01040284263cfcd98db5105b554f08533b384a0e33e31641b",

    E4A2E_CHECKS:
        "92d8e35c98e471ff80667f98d433b47ef75ebaddd41062656bfdd22b144fe33a",

    SCF_FULL_ZIP:
        "09557c46bd5f7ab4433fa97aa980dd47a7b542485909219e6bd42570cb3d401d",

    SCF_SUMMARY_ZIP:
        "b00122c18b4dfe22cc50b179bc3f1cfefb7ec08b59f71775c101d4aece41e22a",

    SCF_REP_ZIP:
        "67543b58865df36508ee8d9b873cf9da9f72dfe33de0331be60fbf357a1fead8",

    CODEBOOK:
        "f0011275e744071a53c038238328156868442174b46e2a8507c6dc62e0245bf9",
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


def check_hashes() -> None:
    for path, expected in EXPECTED_SHA.items():

        if not path.is_file():
            raise RuntimeError(
                f"missing required file={path}"
            )

        actual = sha256(path)

        if actual != expected:
            raise RuntimeError(
                f"SHA mismatch {path}: "
                f"expected={expected} actual={actual}"
            )


def f17(x: float) -> str:
    x = float(x)

    if not math.isfinite(x):
        raise RuntimeError(
            "attempted to serialize non-finite value"
        )

    return format(
        x,
        ".17g",
    )


def require_integer_series(
    name: str,
    series: pd.Series,
) -> np.ndarray:
    arr = pd.to_numeric(
        series,
        errors="raise",
    ).to_numpy(
        dtype=np.float64,
    )

    if not np.isfinite(arr).all():
        raise RuntimeError(
            f"{name} contains non-finite values"
        )

    rounded = np.rint(arr)

    if not np.array_equal(
        arr,
        rounded,
    ):
        raise RuntimeError(
            f"{name} contains non-integer values"
        )

    return rounded.astype(
        np.int64
    )


def exact_member(
    archive: Path,
    expected: str,
    tempdir: Path,
) -> Path:
    with zipfile.ZipFile(
        archive
    ) as zf:

        members = [
            x
            for x in zf.namelist()
            if not x.endswith("/")
        ]

        if members != [
            expected
        ]:
            raise RuntimeError(
                f"{archive.name}: unexpected members={members}"
            )

        zf.extract(
            expected,
            tempdir,
        )

    return (
        tempdir
        / expected
    )


check_hashes()


# =============================================================================
# Upstream exact authorization
# =============================================================================

upstream = E4A2E_AUDIT.read_text(
    encoding="utf-8"
)

for token in (
    "E4A2E_EXACT_SCF_REPLICATE_MI_ENGINE_PREFLIGHT=PASS",
    "E4A2F_FIRST_SCF_KD_INFERENCE_EXECUTION_AUTHORIZED=1",
    "SCF_EXACT_MI_REPLICATE_CONTRACT=PASS",
    "SCF_SYNTHETIC_MI_REPLICATE_ENGINE_PREFLIGHT=PASS",
    "NO_OUTCOME_BASED_SCF_KD_GATE=PASS",
):
    if token not in upstream:
        raise RuntimeError(
            f"missing E4A2E invariant={token}"
        )


contract = json.loads(
    CONTRACT.read_text(
        encoding="utf-8"
    )
)

if contract["parent_commit"] != "6c074f1":
    raise RuntimeError(
        "unexpected E4A2F parent commit"
    )

if (
    contract["sampling_replicates"]["replicate_count"]
    != REPLICATE_COUNT
):
    raise RuntimeError(
        "replicate count differs from frozen engine"
    )

if (
    contract["multiple_imputation"]["implicate_count"]
    != IMPLICATE_COUNT
):
    raise RuntimeError(
        "implicate count differs from frozen engine"
    )


# =============================================================================
# First real K-D + replicate opening
# =============================================================================

full_columns = [
    "y1",
    "yy1",
    "x14",
    "x508",
    "x601",
    "x701",
    "x7133",
    "x42001",
]

summary_columns = [
    "y1",
    "yy1",
    "fin",
    "liq",
    "equity",
    "retqliq",
    "pirtotal",
    "debt2inc",
]

wt_columns = [
    f"wt1b{i}"
    for i in range(
        1,
        1000,
    )
]

mm_columns = [
    f"mm{i}"
    for i in range(
        1,
        1000,
    )
]

replicate_columns = [
    "y1",
    "yy1",
    *wt_columns,
    *mm_columns,
]


with tempfile.TemporaryDirectory(
    prefix="e4a2f_scf_"
) as td_raw:

    td = Path(
        td_raw
    )

    full_path = exact_member(
        SCF_FULL_ZIP,
        "p19i6.dta",
        td,
    )

    summary_path = exact_member(
        SCF_SUMMARY_ZIP,
        "rscfp2019.dta",
        td,
    )

    rep_path = exact_member(
        SCF_REP_ZIP,
        "p19_rw1.dta",
        td,
    )

    full = pd.read_stata(
        full_path,
        columns=full_columns,
        convert_categoricals=False,
    )

    summary = pd.read_stata(
        summary_path,
        columns=summary_columns,
        convert_categoricals=False,
    )

    rep = pd.read_stata(
        rep_path,
        columns=replicate_columns,
        convert_categoricals=False,
    )


# =============================================================================
# Source structure and one-to-one outcome join
# =============================================================================

for df_name, df in (
    (
        "full",
        full,
    ),
    (
        "summary",
        summary,
    ),
    (
        "replicate",
        rep,
    ),
):
    if list(
        df.columns
    ) != (
        full_columns
        if df_name == "full"
        else
        summary_columns
        if df_name == "summary"
        else
        replicate_columns
    ):
        raise RuntimeError(
            f"{df_name}: unexpected selected-column order"
        )


full["y1"] = require_integer_series(
    "full.y1",
    full["y1"],
)

full["yy1"] = require_integer_series(
    "full.yy1",
    full["yy1"],
)

summary["y1"] = require_integer_series(
    "summary.y1",
    summary["y1"],
)

summary["yy1"] = require_integer_series(
    "summary.yy1",
    summary["yy1"],
)

rep["y1"] = require_integer_series(
    "rep.y1",
    rep["y1"],
)

rep["yy1"] = require_integer_series(
    "rep.yy1",
    rep["yy1"],
)


full_duplicate_y1 = int(
    full["y1"].duplicated().sum()
)

summary_duplicate_y1 = int(
    summary["y1"].duplicated().sum()
)

rep_duplicate_y1 = int(
    rep["y1"].duplicated().sum()
)


full_summary_key_pass = (
    full_duplicate_y1 == 0
    and
    summary_duplicate_y1 == 0
    and
    len(full) == len(summary)
    and
    set(
        zip(
            full["y1"],
            full["yy1"],
        )
    )
    ==
    set(
        zip(
            summary["y1"],
            summary["yy1"],
        )
    )
)


if not full_summary_key_pass:
    raise RuntimeError(
        "full/summary Y1,YY1 one-to-one key gate failed"
    )


joined = full.merge(
    summary,
    on=[
        "y1",
        "yy1",
    ],
    how="inner",
    validate="one_to_one",
    sort=False,
)


if len(joined) != len(full):
    raise RuntimeError(
        "full/summary merge row count changed"
    )


joined["implicate"] = (
    joined["y1"]
    - 10 * joined["yy1"]
)


implicate_values = set(
    require_integer_series(
        "implicate",
        joined["implicate"],
    ).tolist()
)

implicate_domain_pass = (
    implicate_values
    == {
        1,
        2,
        3,
        4,
        5,
    }
)


family_group_sizes = (
    joined
    .groupby(
        "yy1",
        sort=False,
    )["implicate"]
    .agg(
        lambda s: tuple(
            sorted(
                int(x)
                for x in s
            )
        )
    )
)


exact_five_implicates_pass = (
    len(
        family_group_sizes
    ) > 0
    and
    all(
        x
        == (
            1,
            2,
            3,
            4,
            5,
        )
        for x in family_group_sizes
    )
)


if not (
    implicate_domain_pass
    and
    exact_five_implicates_pass
):
    raise RuntimeError(
        "SCF exact five-implicate structure failed"
    )


families = np.asarray(
    sorted(
        int(x)
        for x in joined[
            "yy1"
        ].unique()
    ),
    dtype=np.int64,
)

family_count = len(
    families
)

family_index = {
    int(yy1): i
    for i, yy1 in enumerate(
        families
    )
}


# =============================================================================
# Build exact family x 5 matrices
# =============================================================================

VALUE_COLUMNS = [
    "fin",
    "liq",
    "equity",
    "retqliq",
    "pirtotal",
    "debt2inc",
]

value_matrices = {
    name: np.empty(
        (
            family_count,
            IMPLICATE_COUNT,
        ),
        dtype=np.float64,
    )
    for name in VALUE_COLUMNS
}

full_weights = np.empty(
    (
        family_count,
        IMPLICATE_COUNT,
    ),
    dtype=np.float64,
)

age_matrix = np.empty(
    (
        family_count,
        IMPLICATE_COUNT,
    ),
    dtype=np.float64,
)

x508_matrix = np.empty_like(
    age_matrix
)

x601_matrix = np.empty_like(
    age_matrix
)

x701_matrix = np.empty_like(
    age_matrix
)

x7133_matrix = np.empty_like(
    age_matrix
)

first_y1_by_family: dict[
    int,
    int,
] = {}


for row in joined.itertuples(
    index=False
):

    fi = family_index[
        int(
            row.yy1
        )
    ]

    mi = int(
        row.implicate
    ) - 1

    full_weights[
        fi,
        mi,
    ] = float(
        row.x42001
    )

    age_matrix[
        fi,
        mi,
    ] = float(
        row.x14
    )

    x508_matrix[
        fi,
        mi,
    ] = float(
        row.x508
    )

    x601_matrix[
        fi,
        mi,
    ] = float(
        row.x601
    )

    x701_matrix[
        fi,
        mi,
    ] = float(
        row.x701
    )

    x7133_matrix[
        fi,
        mi,
    ] = float(
        row.x7133
    )

    for name in VALUE_COLUMNS:

        value_matrices[
            name
        ][
            fi,
            mi,
        ] = float(
            getattr(
                row,
                name,
            )
        )

    if mi == 0:

        first_y1_by_family[
            int(
                row.yy1
            )
        ] = int(
            row.y1
        )


all_input_finite_pass = all(
    np.isfinite(
        matrix
    ).all()
    for matrix in [
        full_weights,
        age_matrix,
        x508_matrix,
        x601_matrix,
        x701_matrix,
        x7133_matrix,
        *value_matrices.values(),
    ]
)


full_weight_nonnegative_pass = (
    all_input_finite_pass
    and
    np.all(
        full_weights
        >= 0.0
    )
)


if not all_input_finite_pass:
    raise RuntimeError(
        "opened SCF K-D/cohort/full-weight inputs contain non-finite values"
    )

if not full_weight_nonnegative_pass:
    raise RuntimeError(
        "SCF full-sample weights contain negative values"
    )


# =============================================================================
# Frozen raw G1 cohort matrices
# =============================================================================

owner = (
    np.isin(
        x508_matrix,
        [
            1.0,
            2.0,
        ],
    )
    |
    np.isin(
        x601_matrix,
        [
            1.0,
            2.0,
            3.0,
        ],
    )
    |
    np.isin(
        x701_matrix,
        [
            1.0,
            3.0,
            4.0,
            5.0,
            6.0,
            8.0,
        ],
    )
    |
    (
        (
            x701_matrix
            == -7.0
        )
        &
        (
            x7133_matrix
            == 1.0
        )
    )
)


renter = (
    ~owner
    &
    (
        (
            x508_matrix
            == 3.0
        )
        |
        (
            x601_matrix
            == 4.0
        )
        |
        (
            x701_matrix
            == 2.0
        )
    )
)


if np.any(
    owner
    & renter
):
    raise RuntimeError(
        "SCF owner/renter raw rules overlap"
    )


AGE_BANDS = [
    (
        "AGE25_34",
        25.0,
        34.0,
    ),
    (
        "AGE35_44",
        35.0,
        44.0,
    ),
    (
        "AGE45_54",
        45.0,
        54.0,
    ),
    (
        "AGE55_64",
        55.0,
        64.0,
    ),
]


cohort_domains: dict[
    tuple[
        str,
        str,
    ],
    np.ndarray,
] = {}


for (
    band,
    low,
    high,
) in AGE_BANDS:

    age_mask = (
        (
            age_matrix
            >= low
        )
        &
        (
            age_matrix
            <= high
        )
    )

    cohort_domains[
        (
            band,
            "OWNER",
        )
    ] = (
        age_mask
        &
        owner
    )

    cohort_domains[
        (
            band,
            "RENTER",
        )
    ] = (
        age_mask
        &
        renter
    )


all_cohorts_nonempty_pass = all(
    bool(
        np.all(
            np.sum(
                mask,
                axis=0,
            )
            > 0
        )
    )
    for mask in cohort_domains.values()
)


if not all_cohorts_nonempty_pass:
    raise RuntimeError(
        "one or more frozen G1 cohorts are empty in an implicate"
    )


# =============================================================================
# Replicate-file exact match to implicate 1
# =============================================================================

rep_implicate = (
    rep["y1"].to_numpy(
        dtype=np.int64
    )
    - 10
    * rep["yy1"].to_numpy(
        dtype=np.int64
    )
)


replicate_first_implicate_pass = bool(
    np.all(
        rep_implicate
        == 1
    )
)


replicate_family_unique_pass = (
    rep_duplicate_y1 == 0
    and
    not rep[
        "yy1"
    ].duplicated().any()
)


rep_family_set = set(
    int(x)
    for x in rep[
        "yy1"
    ]
)


family_set = set(
    int(x)
    for x in families
)


replicate_family_match_pass = (
    rep_family_set
    == family_set
    and
    len(rep)
    == family_count
)


if not all([
    replicate_first_implicate_pass,
    replicate_family_unique_pass,
    replicate_family_match_pass,
]):
    raise RuntimeError(
        "SCF replicate family/first-implicate structure failed"
    )


rep = (
    rep
    .set_index(
        "yy1",
        drop=False,
    )
    .loc[
        families
    ]
)


expected_rep_y1 = np.asarray(
    [
        first_y1_by_family[
            int(
                yy1
            )
        ]
        for yy1 in families
    ],
    dtype=np.int64,
)


replicate_y1_match_pass = np.array_equal(
    rep[
        "y1"
    ].to_numpy(
        dtype=np.int64
    ),
    expected_rep_y1,
)


if not replicate_y1_match_pass:
    raise RuntimeError(
        "SCF replicate Y1 does not match first implicate Y1"
    )


raw_wt = rep[
    wt_columns
].to_numpy(
    dtype=np.float64
)

raw_mm = rep[
    mm_columns
].to_numpy(
    dtype=np.float64
)


raw_wt_negative_count = int(
    np.count_nonzero(
        np.isfinite(
            raw_wt
        )
        &
        (
            raw_wt
            < 0.0
        )
    )
)

raw_mm_negative_count = int(
    np.count_nonzero(
        np.isfinite(
            raw_mm
        )
        &
        (
            raw_mm
            < 0.0
        )
    )
)

raw_wt_missing_count = int(
    np.count_nonzero(
        np.isnan(
            raw_wt
        )
    )
)

raw_mm_missing_count = int(
    np.count_nonzero(
        np.isnan(
            raw_mm
        )
    )
)


effective_weights = effective_replicate_weights(
    raw_wt,
    raw_mm,
)


effective_weight_shape_pass = (
    effective_weights.shape
    == (
        family_count,
        REPLICATE_COUNT,
    )
    and
    np.isfinite(
        effective_weights
    ).all()
    and
    np.all(
        effective_weights
        >= 0.0
    )
)


if not effective_weight_shape_pass:
    raise RuntimeError(
        "effective SCF replicate weight matrix invalid"
    )


# Free large raw matrices after exact transformation.
del raw_wt
del raw_mm
del rep


# =============================================================================
# Frozen statistics
# =============================================================================

STATISTICS = [
    {
        "statistic_id":
            "K_FIN_MEAN",
        "dimension":
            "K",
        "role":
            "PRIMARY",
        "variable":
            "fin",
        "statistic":
            "mean",
        "state_sign":
            1,
    },
    {
        "statistic_id":
            "K_FIN_MEDIAN",
        "dimension":
            "K",
        "role":
            "ROBUSTNESS",
        "variable":
            "fin",
        "statistic":
            "median",
        "state_sign":
            1,
    },
    {
        "statistic_id":
            "K_LIQ_MEAN",
        "dimension":
            "K",
        "role":
            "SENSITIVITY",
        "variable":
            "liq",
        "statistic":
            "mean",
        "state_sign":
            1,
    },
    {
        "statistic_id":
            "K_EQUITY_MEAN",
        "dimension":
            "K",
        "role":
            "SENSITIVITY",
        "variable":
            "equity",
        "statistic":
            "mean",
        "state_sign":
            1,
    },
    {
        "statistic_id":
            "K_RETQLIQ_MEAN",
        "dimension":
            "K",
        "role":
            "SENSITIVITY",
        "variable":
            "retqliq",
        "statistic":
            "mean",
        "state_sign":
            1,
    },
    {
        "statistic_id":
            "D_PIRTOTAL_MEAN",
        "dimension":
            "D",
        "role":
            "PRIMARY",
        "variable":
            "pirtotal",
        "statistic":
            "mean",
        "state_sign":
            -1,
    },
    {
        "statistic_id":
            "D_DEBT2INC_MEAN",
        "dimension":
            "D",
        "role":
            "SECONDARY",
        "variable":
            "debt2inc",
        "statistic":
            "mean",
        "state_sign":
            -1,
    },
]


cohort_results: list[
    dict[str, object]
] = []

difference_results: list[
    dict[str, object]
] = []

implicate_results: list[
    dict[str, object]
] = []

replicate_results: list[
    dict[str, object]
] = []

support_results: list[
    dict[str, object]
] = []


nonpositive_full_denominator_count = 0
nonpositive_replicate_denominator_count = 0
nonfinite_estimate_count = 0


# =============================================================================
# Support and denominator gates
# =============================================================================

for (
    band,
    _low,
    _high,
) in AGE_BANDS:

    for tenure in (
        "OWNER",
        "RENTER",
    ):

        domain = cohort_domains[
            (
                band,
                tenure,
            )
        ]

        first_domain = domain[
            :,
            0,
        ]

        rep_den = np.sum(
            effective_weights[
                first_domain,
                :,
            ],
            axis=0,
        )

        bad_rep_den = int(
            np.count_nonzero(
                (
                    ~np.isfinite(
                        rep_den
                    )
                )
                |
                (
                    rep_den
                    <= 0.0
                )
            )
        )

        nonpositive_replicate_denominator_count += (
            bad_rep_den
        )

        for m in range(
            IMPLICATE_COUNT
        ):

            mask = domain[
                :,
                m,
            ]

            wsum = float(
                np.sum(
                    full_weights[
                        mask,
                        m,
                    ]
                )
            )

            if (
                not math.isfinite(
                    wsum
                )
                or
                wsum
                <= 0.0
            ):
                nonpositive_full_denominator_count += 1

            support_results.append(
                {
                    "year":
                        2022,
                    "age_band":
                        band,
                    "tenure":
                        tenure,
                    "implicate":
                        m + 1,
                    "unweighted_family_n":
                        int(
                            np.count_nonzero(
                                mask
                            )
                        ),
                    "full_sample_weight_sum":
                        wsum,
                    "replicate_denominator_min":
                        (
                            float(
                                np.min(
                                    rep_den
                                )
                            )
                            if m == 0
                            else None
                        ),
                    "replicate_denominator_max":
                        (
                            float(
                                np.max(
                                    rep_den
                                )
                            )
                            if m == 0
                            else None
                        ),
                    "replicate_count":
                        (
                            REPLICATE_COUNT
                            if m == 0
                            else None
                        ),
                }
            )


denominator_pass = (
    nonpositive_full_denominator_count
    == 0
    and
    nonpositive_replicate_denominator_count
    == 0
)


if not denominator_pass:
    raise RuntimeError(
        "one or more SCF point/replicate domain denominators are invalid"
    )


# =============================================================================
# Cohort inference
# =============================================================================

for (
    band,
    _low,
    _high,
) in AGE_BANDS:

    for tenure in (
        "OWNER",
        "RENTER",
    ):

        domain = cohort_domains[
            (
                band,
                tenure,
            )
        ]

        for spec in STATISTICS:

            values = value_matrices[
                spec[
                    "variable"
                ]
            ]

            inf = scf_statistic_inference(
                values,
                full_weights,
                effective_weights,
                domain,
                statistic=spec[
                    "statistic"
                ],
            )

            all_values = np.concatenate(
                [
                    np.asarray(
                        [
                            inf.pooled_point,
                            inf.imputation_variance,
                            inf.replicate_mean,
                            inf.sampling_variance,
                            inf.combined_variance,
                            inf.combined_se,
                        ],
                        dtype=np.float64,
                    ),
                    inf.implicate_statistics,
                    inf.replicate_statistics,
                ]
            )

            if not np.isfinite(
                all_values
            ).all():
                nonfinite_estimate_count += 1

            state_sign = int(
                spec[
                    "state_sign"
                ]
            )

            cohort_results.append(
                {
                    "year":
                        2022,
                    "age_band":
                        band,
                    "tenure":
                        tenure,
                    "statistic_id":
                        spec[
                            "statistic_id"
                        ],
                    "dimension":
                        spec[
                            "dimension"
                        ],
                    "role":
                        spec[
                            "role"
                        ],
                    "raw_variable":
                        spec[
                            "variable"
                        ].upper(),
                    "statistic":
                        spec[
                            "statistic"
                        ].upper(),
                    "state_sign":
                        state_sign,
                    "point_estimate_raw":
                        inf.pooled_point,
                    "point_estimate_state_oriented":
                        state_sign
                        * inf.pooled_point,
                    "imputation_variance":
                        inf.imputation_variance,
                    "sampling_replicate_mean":
                        inf.replicate_mean,
                    "sampling_variance":
                        inf.sampling_variance,
                    "combined_variance":
                        inf.combined_variance,
                    "combined_se":
                        inf.combined_se,
                    "implicate_count":
                        IMPLICATE_COUNT,
                    "replicate_count":
                        REPLICATE_COUNT,
                }
            )

            for m, value in enumerate(
                inf.implicate_statistics,
                start=1,
            ):
                implicate_results.append(
                    {
                        "year":
                            2022,
                        "statistic_type":
                            "COHORT",
                        "age_band":
                            band,
                        "tenure_or_contrast":
                            tenure,
                        "statistic_id":
                            spec[
                                "statistic_id"
                            ],
                        "implicate":
                            m,
                        "raw_value":
                            float(
                                value
                            ),
                        "state_oriented_value":
                            state_sign
                            * float(
                                value
                            ),
                    }
                )

            for r, value in enumerate(
                inf.replicate_statistics,
                start=1,
            ):
                replicate_results.append(
                    {
                        "year":
                            2022,
                        "statistic_type":
                            "COHORT",
                        "age_band":
                            band,
                        "tenure_or_contrast":
                            tenure,
                        "statistic_id":
                            spec[
                                "statistic_id"
                            ],
                        "replicate":
                            r,
                        "raw_value":
                            float(
                                value
                            ),
                        "state_oriented_value":
                            state_sign
                            * float(
                                value
                            ),
                    }
                )


# =============================================================================
# Direct owner-renter contrasts
# =============================================================================

for (
    band,
    _low,
    _high,
) in AGE_BANDS:

    owner_domain = cohort_domains[
        (
            band,
            "OWNER",
        )
    ]

    renter_domain = cohort_domains[
        (
            band,
            "RENTER",
        )
    ]

    for spec in STATISTICS:

        values = value_matrices[
            spec[
                "variable"
            ]
        ]

        diff = scf_owner_renter_difference_inference(
            values,
            full_weights,
            effective_weights,
            owner_domain,
            renter_domain,
            statistic=spec[
                "statistic"
            ],
        )

        all_values = np.concatenate(
            [
                np.asarray(
                    [
                        diff.pooled_difference,
                        diff.imputation_variance,
                        diff.replicate_mean_difference,
                        diff.sampling_variance,
                        diff.combined_variance,
                        diff.combined_se,
                    ],
                    dtype=np.float64,
                ),
                diff.implicate_differences,
                diff.replicate_differences,
            ]
        )

        if not np.isfinite(
            all_values
        ).all():
            nonfinite_estimate_count += 1

        state_sign = int(
            spec[
                "state_sign"
            ]
        )

        difference_results.append(
            {
                "year":
                    2022,
                "age_band":
                    band,
                "contrast":
                    "RENTER_MINUS_OWNER",
                "statistic_id":
                    spec[
                        "statistic_id"
                    ],
                "dimension":
                    spec[
                        "dimension"
                    ],
                "role":
                    spec[
                        "role"
                    ],
                "raw_variable":
                    spec[
                        "variable"
                    ].upper(),
                "statistic":
                    spec[
                        "statistic"
                    ].upper(),
                "state_sign":
                    state_sign,
                "difference_raw":
                    diff.pooled_difference,
                "difference_state_oriented":
                    state_sign
                    * diff.pooled_difference,
                "imputation_variance":
                    diff.imputation_variance,
                "sampling_replicate_mean_difference":
                    diff.replicate_mean_difference,
                "sampling_variance":
                    diff.sampling_variance,
                "combined_variance":
                    diff.combined_variance,
                "combined_se":
                    diff.combined_se,
                "implicate_count":
                    IMPLICATE_COUNT,
                "replicate_count":
                    REPLICATE_COUNT,
            }
        )

        for m, value in enumerate(
            diff.implicate_differences,
            start=1,
        ):
            implicate_results.append(
                {
                    "year":
                        2022,
                    "statistic_type":
                        "RENTER_MINUS_OWNER",
                    "age_band":
                        band,
                    "tenure_or_contrast":
                        "RENTER_MINUS_OWNER",
                    "statistic_id":
                        spec[
                            "statistic_id"
                        ],
                    "implicate":
                        m,
                    "raw_value":
                        float(
                            value
                        ),
                    "state_oriented_value":
                        state_sign
                        * float(
                            value
                        ),
                }
            )

        for r, value in enumerate(
            diff.replicate_differences,
            start=1,
        ):
            replicate_results.append(
                {
                    "year":
                        2022,
                    "statistic_type":
                        "RENTER_MINUS_OWNER",
                    "age_band":
                        band,
                    "tenure_or_contrast":
                        "RENTER_MINUS_OWNER",
                    "statistic_id":
                        spec[
                            "statistic_id"
                        ],
                    "replicate":
                        r,
                    "raw_value":
                        float(
                            value
                        ),
                    "state_oriented_value":
                        state_sign
                        * float(
                            value
                        ),
                }
            )


# =============================================================================
# Exact structural output gates
# =============================================================================

cohort_shape_pass = (
    len(
        cohort_results
    )
    == 56
)

difference_shape_pass = (
    len(
        difference_results
    )
    == 28
)

cohort_implicate_rows = sum(
    1
    for x in implicate_results
    if x[
        "statistic_type"
    ] == "COHORT"
)

difference_implicate_rows = sum(
    1
    for x in implicate_results
    if x[
        "statistic_type"
    ] == "RENTER_MINUS_OWNER"
)

implicate_shape_pass = (
    cohort_implicate_rows
    == 280
    and
    difference_implicate_rows
    == 140
    and
    len(
        implicate_results
    )
    == 420
)

cohort_replicate_rows = sum(
    1
    for x in replicate_results
    if x[
        "statistic_type"
    ] == "COHORT"
)

difference_replicate_rows = sum(
    1
    for x in replicate_results
    if x[
        "statistic_type"
    ] == "RENTER_MINUS_OWNER"
)

replicate_shape_pass = (
    cohort_replicate_rows
    == 55944
    and
    difference_replicate_rows
    == 27972
    and
    len(
        replicate_results
    )
    == 83916
)

support_shape_pass = (
    len(
        support_results
    )
    == 40
)

finite_estimates_pass = (
    nonfinite_estimate_count
    == 0
)


structural_pass = all(
    [
        full_summary_key_pass,
        implicate_domain_pass,
        exact_five_implicates_pass,
        all_input_finite_pass,
        full_weight_nonnegative_pass,
        all_cohorts_nonempty_pass,
        replicate_first_implicate_pass,
        replicate_family_unique_pass,
        replicate_family_match_pass,
        replicate_y1_match_pass,
        effective_weight_shape_pass,
        denominator_pass,
        finite_estimates_pass,
        cohort_shape_pass,
        difference_shape_pass,
        implicate_shape_pass,
        replicate_shape_pass,
        support_shape_pass,
    ]
)


# =============================================================================
# Deterministic result serialization
# =============================================================================

OUT_COHORT.parent.mkdir(
    parents=True,
    exist_ok=True,
)


with OUT_COHORT.open(
    "w",
    encoding="utf-8",
    newline="",
) as f:

    fields = [
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

    writer = csv.DictWriter(
        f,
        fieldnames=fields,
        delimiter="\t",
        lineterminator="\n",
    )

    writer.writeheader()

    for row in cohort_results:

        out = dict(
            row
        )

        for key in (
            "point_estimate_raw",
            "point_estimate_state_oriented",
            "imputation_variance",
            "sampling_replicate_mean",
            "sampling_variance",
            "combined_variance",
            "combined_se",
        ):
            out[
                key
            ] = f17(
                out[
                    key
                ]
            )

        writer.writerow(
            out
        )


with OUT_DIFF.open(
    "w",
    encoding="utf-8",
    newline="",
) as f:

    fields = [
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

    writer = csv.DictWriter(
        f,
        fieldnames=fields,
        delimiter="\t",
        lineterminator="\n",
    )

    writer.writeheader()

    for row in difference_results:

        out = dict(
            row
        )

        for key in (
            "difference_raw",
            "difference_state_oriented",
            "imputation_variance",
            "sampling_replicate_mean_difference",
            "sampling_variance",
            "combined_variance",
            "combined_se",
        ):
            out[
                key
            ] = f17(
                out[
                    key
                ]
            )

        writer.writerow(
            out
        )


with OUT_IMPLICATES.open(
    "w",
    encoding="utf-8",
    newline="",
) as f:

    fields = [
        "year",
        "statistic_type",
        "age_band",
        "tenure_or_contrast",
        "statistic_id",
        "implicate",
        "raw_value",
        "state_oriented_value",
    ]

    writer = csv.DictWriter(
        f,
        fieldnames=fields,
        delimiter="\t",
        lineterminator="\n",
    )

    writer.writeheader()

    for row in implicate_results:

        out = dict(
            row
        )

        out[
            "raw_value"
        ] = f17(
            out[
                "raw_value"
            ]
        )

        out[
            "state_oriented_value"
        ] = f17(
            out[
                "state_oriented_value"
            ]
        )

        writer.writerow(
            out
        )


with OUT_REPLICATES.open(
    "w",
    encoding="utf-8",
    newline="",
) as f:

    fields = [
        "year",
        "statistic_type",
        "age_band",
        "tenure_or_contrast",
        "statistic_id",
        "replicate",
        "raw_value",
        "state_oriented_value",
    ]

    writer = csv.DictWriter(
        f,
        fieldnames=fields,
        delimiter="\t",
        lineterminator="\n",
    )

    writer.writeheader()

    for row in replicate_results:

        out = dict(
            row
        )

        out[
            "raw_value"
        ] = f17(
            out[
                "raw_value"
            ]
        )

        out[
            "state_oriented_value"
        ] = f17(
            out[
                "state_oriented_value"
            ]
        )

        writer.writerow(
            out
        )


with OUT_SUPPORT.open(
    "w",
    encoding="utf-8",
    newline="",
) as f:

    fields = [
        "year",
        "age_band",
        "tenure",
        "implicate",
        "unweighted_family_n",
        "full_sample_weight_sum",
        "replicate_denominator_min",
        "replicate_denominator_max",
        "replicate_count",
    ]

    writer = csv.DictWriter(
        f,
        fieldnames=fields,
        delimiter="\t",
        lineterminator="\n",
    )

    writer.writeheader()

    for row in support_results:

        out = dict(
            row
        )

        out[
            "full_sample_weight_sum"
        ] = f17(
            out[
                "full_sample_weight_sum"
            ]
        )

        for key in (
            "replicate_denominator_min",
            "replicate_denominator_max",
        ):
            if out[
                key
            ] is not None:
                out[
                    key
                ] = f17(
                    out[
                        key
                    ]
                )
            else:
                out[
                    key
                ] = ""

        if out[
            "replicate_count"
        ] is None:
            out[
                "replicate_count"
            ] = ""

        writer.writerow(
            out
        )


# =============================================================================
# Audit — economic values are NEVER hypothesis gates
# =============================================================================

lines = [
    "=" * 100,
    "E4A2F — FIRST SCF K-D INFERENCE EXECUTION",
    "=" * 100,
    "",
    "SCF_K_D_VALUES_READ=1",
    "SCF_REPLICATE_WEIGHT_VALUES_PARSED=1",
    "CPS_I_VALUES_NEWLY_READ=0",
    "DIMENSIONALITY_ANALYSIS_PERFORMED=0",
    "",
    "===== SOURCE / IMPUTATION STRUCTURE =====",
    f"SCF_FULL_IMPLICATE_ROWS={len(full)}",
    f"SCF_SUMMARY_IMPLICATE_ROWS={len(summary)}",
    f"SCF_UNIQUE_FAMILIES={family_count}",
    (
        "SCF_FULL_SUMMARY_ONE_TO_ONE_JOIN=PASS"
        if full_summary_key_pass
        else
        "SCF_FULL_SUMMARY_ONE_TO_ONE_JOIN=FAIL"
    ),
    (
        "SCF_IMPLICATE_DOMAIN_1_TO_5=PASS"
        if implicate_domain_pass
        else
        "SCF_IMPLICATE_DOMAIN_1_TO_5=FAIL"
    ),
    (
        "SCF_EXACT_FIVE_IMPLICATES_PER_FAMILY=PASS"
        if exact_five_implicates_pass
        else
        "SCF_EXACT_FIVE_IMPLICATES_PER_FAMILY=FAIL"
    ),
    (
        "SCF_OPENED_KD_INPUTS_FINITE=PASS"
        if all_input_finite_pass
        else
        "SCF_OPENED_KD_INPUTS_FINITE=FAIL"
    ),
    (
        "SCF_FULL_SAMPLE_WEIGHTS_NONNEGATIVE=PASS"
        if full_weight_nonnegative_pass
        else
        "SCF_FULL_SAMPLE_WEIGHTS_NONNEGATIVE=FAIL"
    ),
    "",
    "===== FROZEN RAW G1 COHORTS =====",
    "SCF_REFERENCE_AGE=X14",
    "SCF_OWNER_RULE=E3A4_FED_HOUSECL_RAW_LOGIC",
    "SCF_RENTER_RULE=E3A4_STRICT_CATEGORICAL",
    "SCF_COHORT_CLASSIFICATION=PER_IMPLICATE",
    "SCF_G1_COHORT_COUNT=8",
    (
        "SCF_ALL_G1_COHORTS_NONEMPTY_EVERY_IMPLICATE=PASS"
        if all_cohorts_nonempty_pass
        else
        "SCF_ALL_G1_COHORTS_NONEMPTY_EVERY_IMPLICATE=FAIL"
    ),
    "",
    "===== REAL 999-REPLICATE PARSER =====",
    f"SCF_REPLICATE_ROWS={family_count}",
    (
        "SCF_REPLICATE_ROWS_FIRST_IMPLICATE_ONLY=PASS"
        if replicate_first_implicate_pass
        else
        "SCF_REPLICATE_ROWS_FIRST_IMPLICATE_ONLY=FAIL"
    ),
    (
        "SCF_REPLICATE_ONE_ROW_PER_FAMILY=PASS"
        if replicate_family_unique_pass
        else
        "SCF_REPLICATE_ONE_ROW_PER_FAMILY=FAIL"
    ),
    (
        "SCF_REPLICATE_FAMILY_SET_MATCH=PASS"
        if replicate_family_match_pass
        else
        "SCF_REPLICATE_FAMILY_SET_MATCH=FAIL"
    ),
    (
        "SCF_REPLICATE_Y1_FIRST_IMPLICATE_MATCH=PASS"
        if replicate_y1_match_pass
        else
        "SCF_REPLICATE_Y1_FIRST_IMPLICATE_MATCH=FAIL"
    ),
    "SCF_REPLICATE_COUNT=999",
    f"SCF_RAW_WT1B_NEGATIVE_VALUE_COUNT={raw_wt_negative_count}",
    f"SCF_RAW_MM_NEGATIVE_VALUE_COUNT={raw_mm_negative_count}",
    f"SCF_RAW_WT1B_MISSING_VALUE_COUNT={raw_wt_missing_count}",
    f"SCF_RAW_MM_MISSING_VALUE_COUNT={raw_mm_missing_count}",
    "SCF_EFFECTIVE_WEIGHT_TRANSFORM=MAX_0_WT1B_R_X_MAX_0_MM_R",
    (
        "SCF_EFFECTIVE_REPLICATE_WEIGHT_MATRIX=PASS"
        if effective_weight_shape_pass
        else
        "SCF_EFFECTIVE_REPLICATE_WEIGHT_MATRIX=FAIL"
    ),
    (
        "SCF_FULL_SAMPLE_AND_REPLICATE_DOMAIN_DENOMINATORS=PASS"
        if denominator_pass
        else
        "SCF_FULL_SAMPLE_AND_REPLICATE_DOMAIN_DENOMINATORS=FAIL"
    ),
    "",
    "===== FIRST REAL K-D INFERENCE =====",
    "K_PRIMARY=FIN_WEIGHTED_MEAN",
    "K_ROBUSTNESS=FIN_WEIGHTED_MEDIAN",
    "K_SENSITIVITY=LIQ,EQUITY,RETQLIQ",
    "D_PRIMARY_RAW=PIRTOTAL_WEIGHTED_MEAN",
    "D_PRIMARY_STATE_SIGN=-1",
    "D_SECONDARY_RAW=DEBT2INC_WEIGHTED_MEAN",
    "D_SECONDARY_STATE_SIGN=-1",
    f"SCF_KD_COHORT_ESTIMATE_ROWS={len(cohort_results)}",
    f"SCF_KD_COHORT_IMPLICATE_ROWS={cohort_implicate_rows}",
    f"SCF_KD_COHORT_REPLICATE_ROWS={cohort_replicate_rows}",
    f"SCF_KD_OWNER_RENTER_DIFFERENCE_ROWS={len(difference_results)}",
    f"SCF_KD_DIFFERENCE_IMPLICATE_ROWS={difference_implicate_rows}",
    f"SCF_KD_DIFFERENCE_REPLICATE_ROWS={difference_replicate_rows}",
    f"SCF_KD_ALL_IMPLICATE_ROWS={len(implicate_results)}",
    f"SCF_KD_ALL_REPLICATE_ROWS={len(replicate_results)}",
    f"SCF_KD_SUPPORT_ROWS={len(support_results)}",
    (
        "SCF_KD_EXACT_OUTPUT_SHAPE=PASS"
        if all([
            cohort_shape_pass,
            difference_shape_pass,
            implicate_shape_pass,
            replicate_shape_pass,
            support_shape_pass,
        ])
        else
        "SCF_KD_EXACT_OUTPUT_SHAPE=FAIL"
    ),
    (
        "SCF_KD_ALL_ESTIMATES_FINITE=PASS"
        if finite_estimates_pass
        else
        "SCF_KD_ALL_ESTIMATES_FINITE=FAIL"
    ),
    "",
    "===== OUTCOME-INDEPENDENT GATES =====",
    "SIGN_GATE=0",
    "MAGNITUDE_GATE=0",
    "OWNER_RENTER_DIRECTION_GATE=0",
    "SE_MAGNITUDE_GATE=0",
    "SIGNIFICANCE_GATE=0",
    "DIMENSIONALITY_GATE=0",
    "NO_OUTCOME_BASED_KD_GATE=PASS",
    "",
    "I_EMPIRICALLY_TESTED=1",
    (
        "K_EMPIRICALLY_TESTED=1"
        if structural_pass
        else
        "K_EMPIRICALLY_TESTED=0"
    ),
    (
        "D_EMPIRICALLY_TESTED=1"
        if structural_pass
        else
        "D_EMPIRICALLY_TESTED=0"
    ),
    "K_SCALAR_AUTHORIZED=0",
    "D_SCALAR_AUTHORIZED=0",
    "K_D_I_INFERENCE_AUTHORIZED=0",
    "FIVE_DIMENSIONALITY_PROVEN=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "",
    (
        "E4A2F_FIRST_SCF_KD_INFERENCE_EXECUTION=PASS"
        if structural_pass
        else
        "E4A2F_FIRST_SCF_KD_INFERENCE_EXECUTION=FAIL"
    ),
    (
        "E4A2G_KDI_COMPONENT_INFERENCE_CLOSEOUT_AUTHORIZED=1"
        if structural_pass
        else
        "E4A2G_KDI_COMPONENT_INFERENCE_CLOSEOUT_AUTHORIZED=0"
    ),
]

text = (
    "\n".join(
        lines
    )
    + "\n"
)

AUDIT.write_text(
    text,
    encoding="utf-8",
)

sys.stdout.write(
    text
)

if not structural_pass:
    raise SystemExit(
        1
    )
