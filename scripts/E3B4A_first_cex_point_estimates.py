from __future__ import annotations

import csv
import hashlib
import math
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

INT21 = ROOT / "data/raw/cex/2021/intrvw21.zip"
INT22 = ROOT / "data/raw/cex/2022/intrvw22.zip"
DIA22 = ROOT / "data/raw/cex/2022/diary22.zip"

MAP = ROOT / "data/metadata/E3B3C1_component_ucc_map.tsv"
CONTRACT = ROOT / "data/metadata/E3B3C4_exact_point_estimator_contract_audit.txt"

OUT_DIR = ROOT / "data/results"

DEN_OUT = OUT_DIR / "E3B4A_2022_cohort_denominators.tsv"
UCC_OUT = OUT_DIR / "E3B4A_2022_primary_ucc_estimates.tsv"
COMP_OUT = OUT_DIR / "E3B4A_2022_component_point_estimates.tsv"
COMPARE_OUT = OUT_DIR / "E3B4A_2022_owner_renter_comparison.tsv"
ALLOC_OUT = OUT_DIR / "E3B4A_2022_diary_alloc_counts.tsv"

AUDIT = ROOT / "data/metadata/E3B4A_first_cex_point_estimates_audit.txt"


EXPECTED_SHA = {
    INT21:
        "9b449829fd10ee71227a3de044e6b6d67e568cc7c02a759dda14e4b0278697f0",

    INT22:
        "c99a2f47c0084b7a88812b34c56a1a288be2798ff010b2b59dcf87e072773e17",

    DIA22:
        "c285e72fd7513c78caa158c75975c5b03e91049a9ffe9ee6d41966dc4ef20963",

    MAP:
        "a6dd2e592d45f0c7c8428a8265d3b857c615cd842e10241fff06d2a3c06c1e1f",

    CONTRACT:
        "6f4ce4054e026ab0d2785e622e1222e52e7784b61f4f547e3e7d760d650983ca",
}


YEAR = 2022

OWNER = "AGE25_34_OWNER"
RENTER = "AGE25_34_RENTER"

COHORTS = (
    OWNER,
    RENTER,
)


# =============================================================================
# Generic helpers
# =============================================================================

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


contract_text = CONTRACT.read_text(
    encoding="utf-8"
)

for token in (
    "POINT_ESTIMATOR_CONTRACT_FROZEN=1",
    "COST_VALUES_AUTHORIZED=1",
    "E3B4A_FIRST_CEX_POINT_ESTIMATES_AUTHORIZED=1",
):

    if token not in contract_text:
        raise RuntimeError(
            f"missing parent authorization={token}"
        )


def find_member(
    archive: Path,
    basename: str,
) -> str:

    with zipfile.ZipFile(archive) as zf:

        matches = [
            name
            for name in zf.namelist()
            if Path(name).name.lower()
            == basename.lower()
        ]

    if len(matches) != 1:
        raise RuntimeError(
            f"{archive.name}: expected exactly one "
            f"{basename}; found={matches}"
        )

    return matches[0]


def read_member(
    archive: Path,
    basename: str,
    required: set[str],
) -> pd.DataFrame:

    member = find_member(
        archive,
        basename,
    )

    with zipfile.ZipFile(archive) as zf:
        with zf.open(member) as f:

            df = pd.read_csv(
                f,
                dtype=str,
                usecols=lambda c: (
                    c.strip().upper()
                    in required
                ),
                low_memory=False,
            )

    df.columns = [
        c.strip().upper()
        for c in df.columns
    ]

    missing = sorted(
        required
        - set(df.columns)
    )

    if missing:
        raise RuntimeError(
            f"{member}: missing fields={missing}"
        )

    return df


def normalize_id(
    s: pd.Series,
) -> pd.Series:

    return (
        s.fillna("")
        .astype(str)
        .str.strip()
        .str.replace(
            r"\.0$",
            "",
            regex=True,
        )
    )


def normalize_ucc(
    s: pd.Series,
) -> pd.Series:

    out = (
        s.fillna("")
        .astype(str)
        .str.strip()
        .str.replace(
            r"\.0$",
            "",
            regex=True,
        )
    )

    return out.map(
        lambda x: (
            x.zfill(6)
            if x.isdigit()
            else x
        )
    )


def numeric(
    s: pd.Series,
) -> pd.Series:

    return pd.to_numeric(
        (
            s.fillna("")
            .astype(str)
            .str.strip()
            .str.replace(
                ",",
                "",
                regex=False,
            )
        ),
        errors="coerce",
    )


def cohort_from(
    age: pd.Series,
    tenure: pd.Series,
) -> pd.Series:

    young = age.between(
        25,
        34,
        inclusive="both",
    )

    owner = (
        young
        & tenure.isin([
            1,
            2,
            3,
        ])
    )

    renter = (
        young
        & (tenure == 4)
    )

    return pd.Series(
        np.select(
            [
                owner,
                renter,
            ],
            [
                OWNER,
                RENTER,
            ],
            default="",
        ),
        index=age.index,
        dtype="object",
    )


# =============================================================================
# Frozen UCC map
# =============================================================================

ucc_map = pd.read_csv(
    MAP,
    sep="\t",
    dtype=str,
).fillna("")

primary = ucc_map[
    ucc_map["primary_component"].isin(
        [
            "C_COST",
            "H_SERVICE",
        ]
    )
].copy()


if len(primary) != 534:
    raise RuntimeError(
        f"expected 534 primary UCCs; got={len(primary)}"
    )


if primary["ucc"].nunique() != 534:
    raise RuntimeError(
        "primary UCCs are not unique"
    )


if Counter(
    primary["primary_component"]
) != Counter({
    "C_COST": 435,
    "H_SERVICE": 99,
}):
    raise RuntimeError(
        "primary component count mutation"
    )


if Counter(
    primary["source"]
) != Counter({
    "I": 319,
    "D": 215,
}):
    raise RuntimeError(
        "primary source count mutation"
    )


primary["factor_num"] = pd.to_numeric(
    primary["factor"],
    errors="raise",
)


if Counter(
    primary["factor"]
) != Counter({
    "1": 531,
    "4": 3,
}):
    raise RuntimeError(
        "primary factor count mutation"
    )


interview_uccs = set(
    primary.loc[
        primary["source"] == "I",
        "ucc",
    ]
)

diary_uccs = set(
    primary.loc[
        primary["source"] == "D",
        "ucc",
    ]
)


# =============================================================================
# Interview family universe
# =============================================================================

INTERVIEW_PLAN = [
    (INT21, "221"),
    (INT22, "222"),
    (INT22, "223"),
    (INT22, "224"),
    (INT22, "231"),
]


int_family_parts = []


for archive, quarter in INTERVIEW_PLAN:

    df = read_member(
        archive,
        f"fmli{quarter}.csv",
        {
            "NEWID",
            "AGE_REF",
            "CUTENURE",
            "FINLWT21",
            "QINTRVMO",
            "QINTRVYR",
        },
    )

    df["quarter"] = quarter

    df["newid"] = normalize_id(
        df["NEWID"]
    )

    if (df["newid"] == "").any():
        raise RuntimeError(
            f"blank Interview NEWID quarter={quarter}"
        )

    df["age"] = numeric(
        df["AGE_REF"]
    )

    df["tenure"] = numeric(
        df["CUTENURE"]
    )

    df["finlwt21"] = numeric(
        df["FINLWT21"]
    )

    df["qintrvmo"] = numeric(
        df["QINTRVMO"]
    )

    df["qintrvyr"] = numeric(
        df["QINTRVYR"]
    )


    if (
        df["finlwt21"].isna().any()
        or (df["finlwt21"] <= 0).any()
    ):
        raise RuntimeError(
            f"invalid Interview FINLWT21 quarter={quarter}"
        )


    scope = np.full(
        len(df),
        np.nan,
        dtype=float,
    )

    mask = (
        (df["qintrvyr"] == YEAR)
        & df["qintrvmo"].between(
            1,
            3,
            inclusive="both",
        )
    )

    scope[mask] = (
        (
            df.loc[
                mask,
                "qintrvmo",
            ]
            - 1
        )
        / 3
    )


    mask = (
        (df["qintrvyr"] == YEAR)
        & df["qintrvmo"].between(
            4,
            12,
            inclusive="both",
        )
    )

    scope[mask] = 1.0


    mask = (
        (df["qintrvyr"] == YEAR + 1)
        & df["qintrvmo"].between(
            1,
            3,
            inclusive="both",
        )
    )

    scope[mask] = (
        (
            4
            - df.loc[
                mask,
                "qintrvmo",
            ]
        )
        / 3
    )


    if np.isnan(scope).any():

        bad = df.loc[
            np.isnan(scope),
            [
                "quarter",
                "QINTRVMO",
                "QINTRVYR",
            ],
        ].head(20)

        raise RuntimeError(
            "unexpected Interview timing rows:\n"
            + bad.to_string(
                index=False
            )
        )


    df["mo_scope"] = scope

    df["popwt"] = (
        df["finlwt21"]
        / 4.0
        * df["mo_scope"]
    )

    df["cohort"] = cohort_from(
        df["age"],
        df["tenure"],
    )

    df["key"] = (
        df["quarter"]
        + "|"
        + df["newid"]
    )


    if df["key"].duplicated().any():
        raise RuntimeError(
            f"duplicate Interview family key quarter={quarter}"
        )


    int_family_parts.append(
        df[
            [
                "quarter",
                "newid",
                "key",
                "cohort",
                "finlwt21",
                "popwt",
            ]
        ]
    )


int_family = pd.concat(
    int_family_parts,
    ignore_index=True,
)


# =============================================================================
# Diary family universe
# =============================================================================

DIARY_PLAN = [
    (DIA22, "221"),
    (DIA22, "222"),
    (DIA22, "223"),
    (DIA22, "224"),
]


diary_family_parts = []


for archive, quarter in DIARY_PLAN:

    df = read_member(
        archive,
        f"fmld{quarter}.csv",
        {
            "NEWID",
            "AGE_REF",
            "CUTENURE",
            "FINLWT21",
        },
    )

    df["quarter"] = quarter

    df["newid"] = normalize_id(
        df["NEWID"]
    )

    if (df["newid"] == "").any():
        raise RuntimeError(
            f"blank Diary NEWID quarter={quarter}"
        )

    df["age"] = numeric(
        df["AGE_REF"]
    )

    df["tenure"] = numeric(
        df["CUTENURE"]
    )

    df["finlwt21"] = numeric(
        df["FINLWT21"]
    )

    if (
        df["finlwt21"].isna().any()
        or (df["finlwt21"] <= 0).any()
    ):
        raise RuntimeError(
            f"invalid Diary FINLWT21 quarter={quarter}"
        )

    df["popwt"] = (
        df["finlwt21"]
        / 4.0
    )

    df["cohort"] = cohort_from(
        df["age"],
        df["tenure"],
    )

    df["key"] = (
        df["quarter"]
        + "|"
        + df["newid"]
    )


    if df["key"].duplicated().any():
        raise RuntimeError(
            f"duplicate Diary family key quarter={quarter}"
        )


    diary_family_parts.append(
        df[
            [
                "quarter",
                "newid",
                "key",
                "cohort",
                "finlwt21",
                "popwt",
            ]
        ]
    )


diary_family = pd.concat(
    diary_family_parts,
    ignore_index=True,
)


# =============================================================================
# Source-specific cohort denominators
# =============================================================================

den_rows = []
denominators = {}


for source, fam in (
    ("I", int_family),
    ("D", diary_family),
):

    for cohort in COHORTS:

        sub = fam[
            fam["cohort"] == cohort
        ].copy()

        denominator = float(
            sub["popwt"].sum()
        )

        if (
            not math.isfinite(
                denominator
            )
            or denominator <= 0
        ):
            raise RuntimeError(
                f"invalid denominator "
                f"source={source} cohort={cohort}: "
                f"{denominator}"
            )

        denominators[
            (
                source,
                cohort,
            )
        ] = denominator

        den_rows.append({
            "year": YEAR,
            "cohort": cohort,
            "source": source,
            "family_rows": len(sub),
            "unique_newid": (
                sub["newid"].nunique()
            ),
            "population_denominator": denominator,
        })


den_df = pd.DataFrame(
    den_rows
)


# =============================================================================
# Interview expenditure opening
# =============================================================================

int_merge = int_family[
    [
        "key",
        "cohort",
        "finlwt21",
    ]
].copy()


int_exp_parts = []

interview_unmatched = 0


for archive, quarter in INTERVIEW_PLAN:

    df = read_member(
        archive,
        f"mtbi{quarter}.csv",
        {
            "NEWID",
            "UCC",
            "COST",
            "REF_MO",
            "REF_YR",
        },
    )

    df["quarter"] = quarter

    df["newid"] = normalize_id(
        df["NEWID"]
    )

    df["ucc"] = normalize_ucc(
        df["UCC"]
    )

    df["ref_mo"] = numeric(
        df["REF_MO"]
    )

    df["ref_yr"] = numeric(
        df["REF_YR"]
    )


    df = df[
        df["ucc"].isin(
            interview_uccs
        )
        & (df["ref_yr"] == YEAR)
        & df["ref_mo"].between(
            1,
            12,
            inclusive="both",
        )
    ].copy()


    df["cost_num"] = numeric(
        df["COST"]
    )

    df["missing_cost"] = (
        df["cost_num"].isna()
    )

    df["cost_num"] = (
        df["cost_num"]
        .fillna(0.0)
    )

    df["negative_cost"] = (
        df["cost_num"] < 0
    )

    df["key"] = (
        df["quarter"]
        + "|"
        + df["newid"]
    )


    merged = df.merge(
        int_merge,
        on="key",
        how="left",
        validate="many_to_one",
        indicator=True,
    )


    unmatched = int(
        (
            merged["_merge"]
            != "both"
        ).sum()
    )

    interview_unmatched += unmatched


    merged = merged[
        merged["cohort"].isin(
            COHORTS
        )
    ].copy()


    merged["weighted_cost"] = (
        merged["cost_num"]
        * merged["finlwt21"]
    )


    int_exp_parts.append(
        merged[
            [
                "cohort",
                "ucc",
                "weighted_cost",
                "missing_cost",
                "negative_cost",
            ]
        ]
    )


if interview_unmatched != 0:
    raise RuntimeError(
        f"Interview unmatched expenditure/family keys="
        f"{interview_unmatched}"
    )


int_exp = pd.concat(
    int_exp_parts,
    ignore_index=True,
)


int_agg = (
    int_exp
    .groupby(
        [
            "cohort",
            "ucc",
        ],
        as_index=False,
    )
    .agg(
        numerator_weighted_cost=(
            "weighted_cost",
            "sum",
        ),
        expenditure_record_count=(
            "ucc",
            "size",
        ),
        missing_cost_count=(
            "missing_cost",
            "sum",
        ),
        negative_cost_count=(
            "negative_cost",
            "sum",
        ),
    )
)


# =============================================================================
# Diary expenditure opening
# =============================================================================

diary_merge = diary_family[
    [
        "key",
        "cohort",
        "finlwt21",
    ]
].copy()


diary_exp_parts = []
alloc_parts = []

diary_unmatched = 0


for archive, quarter in DIARY_PLAN:

    df = read_member(
        archive,
        f"expd{quarter}.csv",
        {
            "NEWID",
            "UCC",
            "COST",
            "ALLOC",
        },
    )

    df["quarter"] = quarter

    df["newid"] = normalize_id(
        df["NEWID"]
    )

    df["ucc"] = normalize_ucc(
        df["UCC"]
    )


    df = df[
        df["ucc"].isin(
            diary_uccs
        )
    ].copy()


    df["cost_num"] = numeric(
        df["COST"]
    )

    df["missing_cost"] = (
        df["cost_num"].isna()
    )

    df["cost_num"] = (
        df["cost_num"]
        .fillna(0.0)
    )

    df["negative_cost"] = (
        df["cost_num"] < 0
    )

    df["alloc_status"] = (
        df["ALLOC"]
        .fillna("")
        .astype(str)
        .str.strip()
        .replace(
            "",
            "MISSING_OR_BLANK",
        )
    )

    df["key"] = (
        df["quarter"]
        + "|"
        + df["newid"]
    )


    merged = df.merge(
        diary_merge,
        on="key",
        how="left",
        validate="many_to_one",
        indicator=True,
    )


    unmatched = int(
        (
            merged["_merge"]
            != "both"
        ).sum()
    )

    diary_unmatched += unmatched


    merged = merged[
        merged["cohort"].isin(
            COHORTS
        )
    ].copy()


    merged["weighted_cost"] = (
        merged["cost_num"]
        * merged["finlwt21"]
    )


    diary_exp_parts.append(
        merged[
            [
                "cohort",
                "ucc",
                "weighted_cost",
                "missing_cost",
                "negative_cost",
            ]
        ]
    )


    alloc_parts.append(
        merged[
            [
                "cohort",
                "alloc_status",
            ]
        ]
    )


if diary_unmatched != 0:
    raise RuntimeError(
        f"Diary unmatched expenditure/family keys="
        f"{diary_unmatched}"
    )


diary_exp = pd.concat(
    diary_exp_parts,
    ignore_index=True,
)


diary_agg = (
    diary_exp
    .groupby(
        [
            "cohort",
            "ucc",
        ],
        as_index=False,
    )
    .agg(
        numerator_weighted_cost=(
            "weighted_cost",
            "sum",
        ),
        expenditure_record_count=(
            "ucc",
            "size",
        ),
        missing_cost_count=(
            "missing_cost",
            "sum",
        ),
        negative_cost_count=(
            "negative_cost",
            "sum",
        ),
    )
)


alloc_raw = pd.concat(
    alloc_parts,
    ignore_index=True,
)


alloc_df = (
    alloc_raw
    .groupby(
        [
            "cohort",
            "alloc_status",
        ],
        as_index=False,
    )
    .size()
    .rename(
        columns={
            "size":
                "selected_expenditure_rows"
        }
    )
)


# =============================================================================
# Full 534-UCC estimates, including zero-spending UCCs
# =============================================================================

int_lookup = {
    (
        row["cohort"],
        row["ucc"],
    ): row
    for _, row in int_agg.iterrows()
}


diary_lookup = {
    (
        row["cohort"],
        row["ucc"],
    ): row
    for _, row in diary_agg.iterrows()
}


ucc_rows = []


for cohort in COHORTS:

    for _, map_row in primary.iterrows():

        ucc = map_row["ucc"]
        source = map_row["source"]

        lookup = (
            int_lookup
            if source == "I"
            else diary_lookup
        )

        observed = lookup.get(
            (
                cohort,
                ucc,
            )
        )


        if observed is None:

            numerator = 0.0
            record_count = 0
            missing_count = 0
            negative_count = 0

        else:

            numerator = float(
                observed[
                    "numerator_weighted_cost"
                ]
            )

            record_count = int(
                observed[
                    "expenditure_record_count"
                ]
            )

            missing_count = int(
                observed[
                    "missing_cost_count"
                ]
            )

            negative_count = int(
                observed[
                    "negative_cost_count"
                ]
            )


        denominator = denominators[
            (
                source,
                cohort,
            )
        ]


        raw_mean = (
            numerator
            / denominator
        )


        periodicity_multiplier = (
            13.0
            if source == "D"
            else 1.0
        )


        source_mean = (
            raw_mean
            * periodicity_multiplier
        )


        factor = float(
            map_row["factor_num"]
        )


        annual_mean = (
            source_mean
            * factor
        )


        if not math.isfinite(
            annual_mean
        ):
            raise RuntimeError(
                f"non-finite estimate "
                f"cohort={cohort} ucc={ucc}"
            )


        ucc_rows.append({
            "year": YEAR,
            "cohort": cohort,
            "ucc": ucc,
            "source": source,
            "factor": int(factor),
            "primary_component":
                map_row[
                    "primary_component"
                ],
            "broad_category":
                map_row[
                    "broad_category"
                ],
            "subcategory":
                map_row[
                    "subcategory"
                ],
            "population_denominator":
                denominator,
            "numerator_weighted_cost":
                numerator,
            "source_periodicity_multiplier":
                periodicity_multiplier,
            "raw_source_mean_usd":
                raw_mean,
            "annual_mean_nominal_usd":
                annual_mean,
            "expenditure_record_count":
                record_count,
            "missing_cost_count":
                missing_count,
            "negative_cost_count":
                negative_count,
        })


ucc_df = pd.DataFrame(
    ucc_rows
)


if len(ucc_df) != (
    len(COHORTS)
    * 534
):
    raise RuntimeError(
        f"unexpected UCC-estimate rows={len(ucc_df)}"
    )


for cohort in COHORTS:

    sub = ucc_df[
        ucc_df["cohort"]
        == cohort
    ]

    if sub["ucc"].nunique() != 534:
        raise RuntimeError(
            f"incomplete UCC coverage cohort={cohort}"
        )


# =============================================================================
# Component aggregation
# =============================================================================

component_rows = []


for cohort in COHORTS:

    for component in (
        "C_COST",
        "H_SERVICE",
    ):

        sub = ucc_df[
            (
                ucc_df["cohort"]
                == cohort
            )
            & (
                ucc_df[
                    "primary_component"
                ]
                == component
            )
        ]


        i_value = float(
            sub.loc[
                sub["source"] == "I",
                "annual_mean_nominal_usd",
            ].sum()
        )


        d_value = float(
            sub.loc[
                sub["source"] == "D",
                "annual_mean_nominal_usd",
            ].sum()
        )


        total = (
            i_value
            + d_value
        )


        if not math.isfinite(
            total
        ):
            raise RuntimeError(
                f"non-finite component "
                f"{cohort} {component}"
            )


        component_rows.append({
            "year": YEAR,
            "cohort": cohort,
            "component": component,
            "interview_contribution_usd":
                i_value,
            "diary_contribution_usd":
                d_value,
            "annual_mean_nominal_usd":
                total,
        })


component_df = pd.DataFrame(
    component_rows
)


if len(component_df) != 4:
    raise RuntimeError(
        "expected exactly four component estimates"
    )


# =============================================================================
# Mechanical owner/renter comparison
# =============================================================================

comparison_rows = []


for component in (
    "C_COST",
    "H_SERVICE",
):

    owner_value = float(
        component_df.loc[
            (
                component_df["cohort"]
                == OWNER
            )
            & (
                component_df["component"]
                == component
            ),
            "annual_mean_nominal_usd",
        ].iloc[0]
    )


    renter_value = float(
        component_df.loc[
            (
                component_df["cohort"]
                == RENTER
            )
            & (
                component_df["component"]
                == component
            ),
            "annual_mean_nominal_usd",
        ].iloc[0]
    )


    ratio = (
        renter_value
        / owner_value
        if owner_value != 0
        else np.nan
    )


    comparison_rows.append({
        "year": YEAR,
        "component": component,
        "owner_25_34_usd":
            owner_value,
        "renter_25_34_usd":
            renter_value,
        "renter_minus_owner_usd":
            renter_value
            - owner_value,
        "renter_to_owner_ratio":
            ratio,
    })


comparison_df = pd.DataFrame(
    comparison_rows
)


# =============================================================================
# Diagnostics
# =============================================================================

int_missing = int(
    int_exp[
        "missing_cost"
    ].sum()
)

int_negative = int(
    int_exp[
        "negative_cost"
    ].sum()
)

diary_missing = int(
    diary_exp[
        "missing_cost"
    ].sum()
)

diary_negative = int(
    diary_exp[
        "negative_cost"
    ].sum()
)


factor4_rows = ucc_df[
    ucc_df["factor"] == 4
]


structural_pass = all([
    interview_unmatched == 0,
    diary_unmatched == 0,
    len(ucc_df) == 1068,
    len(component_df) == 4,
    len(factor4_rows) == 6,
    ucc_df[
        "annual_mean_nominal_usd"
    ].notna().all(),
])


# =============================================================================
# Write outputs
# =============================================================================

OUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


den_df.to_csv(
    DEN_OUT,
    sep="\t",
    index=False,
    float_format="%.10f",
)


ucc_df.to_csv(
    UCC_OUT,
    sep="\t",
    index=False,
    float_format="%.10f",
)


component_df.to_csv(
    COMP_OUT,
    sep="\t",
    index=False,
    float_format="%.10f",
)


comparison_df.to_csv(
    COMPARE_OUT,
    sep="\t",
    index=False,
    float_format="%.10f",
)


alloc_df.to_csv(
    ALLOC_OUT,
    sep="\t",
    index=False,
)


audit_lines = [
    "=" * 100,
    "ECONOMIC GEOMETRY RESEARCH — E3B4A FIRST CEX POINT ESTIMATES",
    "=" * 100,
    "",
    "COST_VALUES_READ=1",
    "EXPENDITURE_VALUES_OPENED=1",
    "HOUSEHOLD_ECONOMIC_VALUES_OPENED=1",
    "REAL_INFLATION_ESTIMATED=0",
    "",
    "===== DESIGN =====",
    "YEAR=2022",
    "COHORT_1=AGE25_34_OWNER",
    "COHORT_2=AGE25_34_RENTER",
    "OWNER_CUTENURE=1,2,3",
    "RENTER_CUTENURE=4",
    "AGE_RANGE=25..34",
    "",
    "===== FROZEN PRIMARY MAP =====",
    "PRIMARY_UCCS=534",
    "C_COST_PRIMARY_UCCS=435",
    "H_SERVICE_CORE_UCCS=99",
    "PRIMARY_INTERVIEW_UCCS=319",
    "PRIMARY_DIARY_UCCS=215",
    "PRIMARY_FACTOR1_UCCS=531",
    "PRIMARY_FACTOR4_UCCS=3",
    "",
    "===== DENOMINATORS =====",
]

for row in den_rows:

    audit_lines += [
        (
            f"{row['cohort']}_{row['source']}"
            f"_FAMILY_ROWS={row['family_rows']}"
        ),
        (
            f"{row['cohort']}_{row['source']}"
            f"_UNIQUE_NEWID={row['unique_newid']}"
        ),
        (
            f"{row['cohort']}_{row['source']}"
            f"_POP_DENOMINATOR="
            f"{row['population_denominator']:.10f}"
        ),
    ]


audit_lines += [
    "",
    "===== COST DIAGNOSTICS =====",
    f"INTERVIEW_SELECTED_EXPENDITURE_ROWS={len(int_exp)}",
    f"DIARY_SELECTED_EXPENDITURE_ROWS={len(diary_exp)}",
    f"INTERVIEW_UNMATCHED_FAMILY_KEYS={interview_unmatched}",
    f"DIARY_UNMATCHED_FAMILY_KEYS={diary_unmatched}",
    f"INTERVIEW_MISSING_COST_ROWS={int_missing}",
    f"DIARY_MISSING_COST_ROWS={diary_missing}",
    f"INTERVIEW_NEGATIVE_COST_ROWS={int_negative}",
    f"DIARY_NEGATIVE_COST_ROWS={diary_negative}",
    "NEGATIVE_COST_ACTION=PRESERVED",
    "MISSING_COST_ACTION=ZERO",
    "DIARY_ALLOC_FILTER=NONE",
    "",
    "===== OUTPUT STRUCTURE =====",
    f"PRIMARY_UCC_ESTIMATE_ROWS={len(ucc_df)}",
    f"COMPONENT_ESTIMATE_ROWS={len(component_df)}",
    f"OWNER_RENTER_COMPARISON_ROWS={len(comparison_df)}",
    f"FACTOR4_COHORT_UCC_ROWS={len(factor4_rows)}",
    "",
    "POINT_ESTIMATE_VALUES_HARD_GATED_BY_SIGN=0",
    "POINT_ESTIMATE_VALUES_HARD_GATED_BY_MAGNITUDE=0",
    "OUTCOME_BASED_UCC_SELECTION=0",
    "",
    "OBSERVED_EXPENDITURE_CHANGE_EQUALS_INFLATION=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "ECONOMIC_INTERPRETATION_AUTHORIZED=0",
    "",
    (
        "E3B4A_FIRST_CEX_POINT_ESTIMATES=PASS"
        if structural_pass
        else
        "E3B4A_FIRST_CEX_POINT_ESTIMATES=FAIL"
    ),
    (
        "E3B4B_ALL_CU_BENCHMARK_VALIDATION_AUTHORIZED=1"
        if structural_pass
        else
        "E3B4B_ALL_CU_BENCHMARK_VALIDATION_AUTHORIZED=0"
    ),
    "",
]


AUDIT.write_text(
    "\n".join(
        audit_lines
    ),
    encoding="utf-8",
)


print(
    "\n".join(
        audit_lines
    )
)


if not structural_pass:
    raise SystemExit(1)
