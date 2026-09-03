from __future__ import annotations

import hashlib
import json
import math
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

YEAR = 2022

INT21 = ROOT / "data/raw/cex/2021/intrvw21.zip"
INT22 = ROOT / "data/raw/cex/2022/intrvw22.zip"
DIA22 = ROOT / "data/raw/cex/2022/diary22.zip"

ENGINE_CONTRACT = (
    ROOT
    / "data/metadata/E3B4C1_exact_brr_engine_contract.json"
)

ENGINE_AUDIT = (
    ROOT
    / "data/metadata/E3B4C1_exact_brr_engine_contract_audit.txt"
)

UCC_CONTRACT = (
    ROOT
    / "data/metadata/E3B4B_R3_R1_estimator_v2_ucc_source_contract.tsv"
)

FROZEN_COMPONENTS = (
    ROOT
    / "data/results/E3B4A_V2_2022_component_point_estimates.tsv"
)

FROZEN_COMPARISON = (
    ROOT
    / "data/results/E3B4A_V2_2022_owner_renter_comparison.tsv"
)

OUT_DENOM = (
    ROOT
    / "data/results/E3B4C2_2022_brr_denominators.tsv"
)

OUT_COMPONENT_REPS = (
    ROOT
    / "data/results/E3B4C2_2022_component_replicates.tsv"
)

OUT_DIFF_REPS = (
    ROOT
    / "data/results/E3B4C2_2022_difference_replicates.tsv"
)

OUT_RATIO_REPS = (
    ROOT
    / "data/results/E3B4C2_2022_ratio_replicates.tsv"
)

OUT_SUMMARY = (
    ROOT
    / "data/results/E3B4C2_2022_brr_inference_summary.tsv"
)

AUDIT = (
    ROOT
    / "data/metadata/E3B4C2_first_brr_execution_audit.txt"
)


EXPECTED_SHA = {
    INT21:
        "9b449829fd10ee71227a3de044e6b6d67e568cc7c02a759dda14e4b0278697f0",

    INT22:
        "c99a2f47c0084b7a88812b34c56a1a288be2798ff010b2b59dcf87e072773e17",

    DIA22:
        "c285e72fd7513c78caa158c75975c5b03e91049a9ffe9ee6d41966dc4ef20963",

    ENGINE_CONTRACT:
        "fcd2c315ab1ade9ef3cb96aabc04f37d1eba52c92b78e50543a15afec4650c1d",

    ENGINE_AUDIT:
        "747626ce8964ce07d0864adcd9c960d17ad24f4f61db631383325cfdbbb6f993",

    UCC_CONTRACT:
        "72c253f9295aad902c39636277b7cf23aa5f651206eb8ff416d58a45e7bbf047",

    FROZEN_COMPONENTS:
        "7fc2513c82b78a3c1ced549192ab45b2fe849361d296a57743cd1846b01ef366",

    FROZEN_COMPARISON:
        "46a7ee46e845a866d1a06b629c412d6ce7dfd80b80f2af99836e10516faee682",
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


engine_text = ENGINE_AUDIT.read_text(
    encoding="utf-8",
)

for token in (
    "E3B4C1_EXACT_BRR_ENGINE_CONTRACT=PASS",
    "E3B4C2_FIRST_BRR_EXECUTION_AUTHORIZED=1",
    "EXACT_REPLICATE_SET=PASS",
    "BRR_VARIANCE_CONTRACT=PASS",
):

    if token not in engine_text:
        raise RuntimeError(
            f"missing engine invariant={token}"
        )


engine = json.loads(
    ENGINE_CONTRACT.read_text(
        encoding="utf-8"
    )
)


REPS = [
    f"WTREP{i:02d}"
    for i in range(1, 45)
]

WEIGHTS = [
    "FINLWT21",
    *REPS,
]

if engine["replicate_weights"] != REPS:
    raise RuntimeError(
        "replicate set differs from frozen engine"
    )


AGE_BANDS = [
    "AGE25_34",
    "AGE35_44",
    "AGE45_54",
    "AGE55_64",
]

AGE_SPECS = [
    ("AGE25_34", 25, 34),
    ("AGE35_44", 35, 44),
    ("AGE45_54", 45, 54),
    ("AGE55_64", 55, 64),
]

COHORTS = [
    f"{age_band}_{tenure}"
    for age_band, _, _ in AGE_SPECS
    for tenure in ("OWNER", "RENTER")
]

CONTROL_COHORTS = [
    "AGE25_34_OWNER",
    "AGE25_34_RENTER",
]

COMPONENTS = [
    "C_COST",
    "H_SERVICE",
]

ATOL = 1e-8


# =============================================================================
# Helpers
# =============================================================================

def find_member(
    archive: Path,
    basename: str,
) -> str:

    with zipfile.ZipFile(archive) as zf:

        matches = [
            x for x in zf.namelist()
            if Path(x).name.lower()
            == basename.lower()
        ]

    if len(matches) != 1:

        raise RuntimeError(
            f"{archive.name}: "
            f"{basename}: {matches}"
        )

    return matches[0]


def read_member(
    archive: Path,
    basename: str,
    fields: set[str],
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
                usecols=lambda c:
                    c.strip().upper()
                    in fields,
                low_memory=False,
            )

    df.columns = [
        x.strip().upper()
        for x in df.columns
    ]

    missing = (
        fields
        - set(df.columns)
    )

    if missing:

        raise RuntimeError(
            f"{member}: "
            f"missing={sorted(missing)}"
        )

    return df


def norm_id(
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


def norm_ucc(
    s: pd.Series,
) -> pd.Series:

    x = (
        s.fillna("")
        .astype(str)
        .str.strip()
        .str.replace(
            r"\.0$",
            "",
            regex=True,
        )
    )

    return x.map(
        lambda v:
            v.zfill(6)
            if v.isdigit()
            else v
    )


def num(
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


def assign_cohort(
    age: pd.Series,
    tenure: pd.Series,
) -> pd.Series:

    out = pd.Series(
        "",
        index=age.index,
        dtype="object",
    )

    for age_band, age_min, age_max in AGE_SPECS:

        eligible = age.between(
            age_min,
            age_max,
        )

        out.loc[
            eligible
            & tenure.isin(
                [1, 2, 3]
            )
        ] = f"{age_band}_OWNER"

        out.loc[
            eligible
            & tenure.eq(4)
        ] = f"{age_band}_RENTER"

    return out


def parse_weights(
    df: pd.DataFrame,
    context: str,
) -> None:

    for col in WEIGHTS:

        x = num(
            df[col]
        )

        if col == "FINLWT21":

            if x.isna().any():
                raise RuntimeError(
                    f"{context}: "
                    f"missing FINLWT21"
                )

        # Official replicate files use missing for units
        # not selected into a particular half-sample.
        x = x.fillna(0.0)

        if (
            ~np.isfinite(
                x.to_numpy(dtype=float)
            )
        ).any():

            raise RuntimeError(
                f"{context}: "
                f"non-finite weight={col}"
            )

        if (
            x < 0
        ).any():

            raise RuntimeError(
                f"{context}: "
                f"negative weight={col}"
            )

        df[col] = x.astype(float)


def brr_stats(
    full: float,
    reps: np.ndarray,
) -> tuple[
    float,
    float,
    float,
    float,
]:

    reps = np.asarray(
        reps,
        dtype=float,
    )

    if reps.shape != (44,):
        raise RuntimeError(
            f"bad BRR shape={reps.shape}"
        )

    if not np.isfinite(
        reps
    ).all():
        raise RuntimeError(
            "non-finite BRR replicate"
        )

    variance = float(
        np.mean(
            (
                reps
                - float(full)
            ) ** 2
        )
    )

    if (
        not math.isfinite(
            variance
        )
        or variance < 0
    ):
        raise RuntimeError(
            f"bad BRR variance={variance}"
        )

    se = math.sqrt(
        variance
    )

    lower = (
        float(full)
        - 1.96 * se
    )

    upper = (
        float(full)
        + 1.96 * se
    )

    return (
        variance,
        se,
        lower,
        upper,
    )


# =============================================================================
# Frozen primary estimator map
# =============================================================================

ucc_contract = pd.read_csv(
    UCC_CONTRACT,
    sep="\t",
    dtype=str,
).fillna("")


primary = ucc_contract[
    ucc_contract[
        "primary_component"
    ].isin(
        COMPONENTS
    )
].copy()


family_counts = Counter(
    primary[
        "estimator_family"
    ]
)


if (
    len(primary) != 534
    or family_counts
    != Counter({
        "MTBI": 316,
        "ITBI": 3,
        "EXPD": 215,
    })
):

    raise RuntimeError(
        f"primary contract mutation: "
        f"rows={len(primary)} "
        f"counts={family_counts}"
    )


mtbi_uccs = set(
    primary.loc[
        primary[
            "estimator_family"
        ] == "MTBI",
        "ucc",
    ]
)

itbi_uccs = set(
    primary.loc[
        primary[
            "estimator_family"
        ] == "ITBI",
        "ucc",
    ]
)

expd_uccs = set(
    primary.loc[
        primary[
            "estimator_family"
        ] == "EXPD",
        "ucc",
    ]
)


# =============================================================================
# Family records + all 45 weights
# =============================================================================

I_PLAN = [
    (INT21, "221"),
    (INT22, "222"),
    (INT22, "223"),
    (INT22, "224"),
    (INT22, "231"),
]

D_PLAN = [
    (DIA22, "221"),
    (DIA22, "222"),
    (DIA22, "223"),
    (DIA22, "224"),
]


i_parts = []


for archive, q in I_PLAN:

    fields = {
        "NEWID",
        "AGE_REF",
        "CUTENURE",
        "QINTRVMO",
        "QINTRVYR",
        *WEIGHTS,
    }

    df = read_member(
        archive,
        f"fmli{q}.csv",
        fields,
    )

    parse_weights(
        df,
        f"FMLI {q}",
    )

    df["quarter"] = q

    df["newid"] = norm_id(
        df["NEWID"]
    )

    age = num(
        df["AGE_REF"]
    )

    tenure = num(
        df["CUTENURE"]
    )

    month = num(
        df["QINTRVMO"]
    )

    year = num(
        df["QINTRVYR"]
    )


    scope = np.full(
        len(df),
        np.nan,
        dtype=float,
    )


    mask = (
        (year == YEAR)
        & month.between(
            1,
            3,
        )
    )

    scope[mask] = (
        month.loc[
            mask
        ].to_numpy(
            dtype=float
        )
        - 1.0
    ) / 3.0


    mask = (
        (year == YEAR)
        & month.between(
            4,
            12,
        )
    )

    scope[mask] = 1.0


    mask = (
        (year == YEAR + 1)
        & month.between(
            1,
            3,
        )
    )

    scope[mask] = (
        4.0
        - month.loc[
            mask
        ].to_numpy(
            dtype=float
        )
    ) / 3.0


    if np.isnan(
        scope
    ).any():

        raise RuntimeError(
            f"unexpected Interview "
            f"calendar timing q={q}"
        )


    df["scope"] = scope

    df["cohort"] = assign_cohort(
        age,
        tenure,
    )

    df["key"] = (
        df["quarter"]
        + "|"
        + df["newid"]
    )


    if df["key"].duplicated().any():

        raise RuntimeError(
            f"duplicate FMLI key q={q}"
        )


    i_parts.append(
        df[
            [
                "key",
                "cohort",
                "scope",
                *WEIGHTS,
            ]
        ]
    )


i_fam = pd.concat(
    i_parts,
    ignore_index=True,
)


d_parts = []


for archive, q in D_PLAN:

    fields = {
        "NEWID",
        "AGE_REF",
        "CUTENURE",
        *WEIGHTS,
    }

    df = read_member(
        archive,
        f"fmld{q}.csv",
        fields,
    )

    parse_weights(
        df,
        f"FMLD {q}",
    )

    df["quarter"] = q

    df["newid"] = norm_id(
        df["NEWID"]
    )

    age = num(
        df["AGE_REF"]
    )

    tenure = num(
        df["CUTENURE"]
    )

    df["cohort"] = assign_cohort(
        age,
        tenure,
    )

    df["key"] = (
        df["quarter"]
        + "|"
        + df["newid"]
    )


    if df["key"].duplicated().any():

        raise RuntimeError(
            f"duplicate FMLD key q={q}"
        )


    d_parts.append(
        df[
            [
                "key",
                "cohort",
                *WEIGHTS,
            ]
        ]
    )


d_fam = pd.concat(
    d_parts,
    ignore_index=True,
)


# =============================================================================
# 45 source/cohort denominators
# =============================================================================

denominators: dict[
    tuple[str, str],
    np.ndarray,
] = {}

denom_rows = []


for cohort in COHORTS:

    z = i_fam[
        i_fam[
            "cohort"
        ] == cohort
    ]

    W = z[
        WEIGHTS
    ].to_numpy(
        dtype=float,
    )

    scope = z[
        "scope"
    ].to_numpy(
        dtype=float,
    )

    arr = (
        W
        * (
            scope[:, None]
            / 4.0
        )
    ).sum(
        axis=0
    )

    denominators[
        (
            cohort,
            "I",
        )
    ] = arr


    for idx, label in enumerate(
        WEIGHTS
    ):

        denom_rows.append({
            "year": YEAR,
            "cohort": cohort,
            "source": "I",
            "weight": label,
            "weight_type":
                "FULL"
                if idx == 0
                else "BRR",
            "population_denominator":
                float(arr[idx]),
        })


    z = d_fam[
        d_fam[
            "cohort"
        ] == cohort
    ]

    W = z[
        WEIGHTS
    ].to_numpy(
        dtype=float,
    )

    arr = (
        W
        / 4.0
    ).sum(
        axis=0
    )

    denominators[
        (
            cohort,
            "D",
        )
    ] = arr


    for idx, label in enumerate(
        WEIGHTS
    ):

        denom_rows.append({
            "year": YEAR,
            "cohort": cohort,
            "source": "D",
            "weight": label,
            "weight_type":
                "FULL"
                if idx == 0
                else "BRR",
            "population_denominator":
                float(arr[idx]),
        })


denom_df = pd.DataFrame(
    denom_rows
)


if len(
    denom_df
) != 720:

    raise RuntimeError(
        "denominator row count != 720"
    )

if len(
    denom_df[
        denom_df[
            "weight_type"
        ] == "BRR"
    ]
) != 704:

    raise RuntimeError(
        "replicate denominator row count "
        "!= 704"
    )


interview_rep_denom_pass = True
diary_rep_denom_pass = True


for cohort in COHORTS:

    arr = denominators[
        (
            cohort,
            "I",
        )
    ][1:]

    if (
        not np.isfinite(
            arr
        ).all()
        or not (
            arr > 0
        ).all()
    ):

        interview_rep_denom_pass = False


    arr = denominators[
        (
            cohort,
            "D",
        )
    ][1:]

    if (
        not np.isfinite(
            arr
        ).all()
        or not (
            arr > 0
        ).all()
    ):

        diary_rep_denom_pass = False


# =============================================================================
# Expense weighted-numerator accumulation
# =============================================================================

def add_group_numerators(
    accum: dict[
        tuple[str, str],
        np.ndarray,
    ],
    merged: pd.DataFrame,
) -> None:

    for cohort in COHORTS:

        c = merged[
            merged[
                "cohort"
            ] == cohort
        ]

        if c.empty:
            continue

        for ucc, g in c.groupby(
            "ucc",
            sort=False,
        ):

            value = g[
                "value"
            ].to_numpy(
                dtype=float,
            )

            W = g[
                WEIGHTS
            ].to_numpy(
                dtype=float,
            )

            weighted = (
                W
                * value[:, None]
            ).sum(
                axis=0
            )

            key = (
                cohort,
                ucc,
            )

            if key not in accum:

                accum[key] = np.zeros(
                    45,
                    dtype=float,
                )

            accum[key] += weighted


i_join = i_fam[
    [
        "key",
        "cohort",
        *WEIGHTS,
    ]
]

d_join = d_fam[
    [
        "key",
        "cohort",
        *WEIGHTS,
    ]
]


def interview_numerators(
    family: str,
    uccs: set[str],
) -> tuple[
    dict[
        tuple[str, str],
        np.ndarray,
    ],
    dict[str, int],
]:

    accum = {}

    selected = 0
    missing = 0
    negative = 0
    unmatched = 0


    for archive, q in I_PLAN:

        if family == "MTBI":

            df = read_member(
                archive,
                f"mtbi{q}.csv",
                {
                    "NEWID",
                    "UCC",
                    "COST",
                    "REF_MO",
                    "REF_YR",
                },
            )

            refmo = num(
                df["REF_MO"]
            )

            refyr = num(
                df["REF_YR"]
            )

            raw_value = num(
                df["COST"]
            )


        elif family == "ITBI":

            df = read_member(
                archive,
                f"itbi{q}.csv",
                {
                    "NEWID",
                    "UCC",
                    "VALUE",
                    "REFMO",
                    "REFYR",
                },
            )

            refmo = num(
                df["REFMO"]
            )

            refyr = num(
                df["REFYR"]
            )

            raw_value = num(
                df["VALUE"]
            )


        else:

            raise RuntimeError(
                f"unknown Interview family="
                f"{family}"
            )


        df["quarter"] = q

        df["newid"] = norm_id(
            df["NEWID"]
        )

        df["ucc"] = norm_ucc(
            df["UCC"]
        )


        keep = (
            df["ucc"].isin(
                uccs
            )
            & refyr.eq(
                YEAR
            )
            & refmo.between(
                1,
                12,
            )
        )


        df = df.loc[
            keep
        ].copy()

        raw_value = raw_value.loc[
            keep
        ]


        selected += len(df)

        missing += int(
            raw_value.isna().sum()
        )


        df["value"] = (
            raw_value
            .fillna(0.0)
            .to_numpy(
                dtype=float
            )
        )


        negative += int(
            (
                df["value"]
                < 0
            ).sum()
        )


        df["key"] = (
            df["quarter"]
            + "|"
            + df["newid"]
        )


        m = df.merge(
            i_join,
            on="key",
            how="left",
            validate="many_to_one",
            indicator=True,
        )


        unmatched += int(
            (
                m["_merge"]
                != "both"
            ).sum()
        )


        if unmatched:
            raise RuntimeError(
                f"{family} family join "
                f"unmatched={unmatched}"
            )


        m = m[
            m["cohort"].isin(
                COHORTS
            )
        ].copy()


        add_group_numerators(
            accum,
            m,
        )


    return (
        accum,
        {
            "selected": selected,
            "missing": missing,
            "negative": negative,
            "unmatched": unmatched,
        },
    )


def diary_numerators(
    uccs: set[str],
) -> tuple[
    dict[
        tuple[str, str],
        np.ndarray,
    ],
    dict[str, int],
]:

    accum = {}

    selected = 0
    missing = 0
    negative = 0
    unmatched = 0


    for archive, q in D_PLAN:

        df = read_member(
            archive,
            f"expd{q}.csv",
            {
                "NEWID",
                "UCC",
                "COST",
            },
        )


        df["quarter"] = q

        df["newid"] = norm_id(
            df["NEWID"]
        )

        df["ucc"] = norm_ucc(
            df["UCC"]
        )


        keep = df[
            "ucc"
        ].isin(
            uccs
        )


        df = df.loc[
            keep
        ].copy()


        raw_value = num(
            df["COST"]
        )


        selected += len(df)

        missing += int(
            raw_value.isna().sum()
        )


        df["value"] = (
            raw_value
            .fillna(0.0)
            .to_numpy(
                dtype=float
            )
        )


        negative += int(
            (
                df["value"]
                < 0
            ).sum()
        )


        df["key"] = (
            df["quarter"]
            + "|"
            + df["newid"]
        )


        m = df.merge(
            d_join,
            on="key",
            how="left",
            validate="many_to_one",
            indicator=True,
        )


        unmatched += int(
            (
                m["_merge"]
                != "both"
            ).sum()
        )


        if unmatched:
            raise RuntimeError(
                f"EXPD family join "
                f"unmatched={unmatched}"
            )


        m = m[
            m["cohort"].isin(
                COHORTS
            )
        ].copy()


        add_group_numerators(
            accum,
            m,
        )


    return (
        accum,
        {
            "selected": selected,
            "missing": missing,
            "negative": negative,
            "unmatched": unmatched,
        },
    )


mtbi_num, mtbi_diag = (
    interview_numerators(
        "MTBI",
        mtbi_uccs,
    )
)


itbi_num, itbi_diag = (
    interview_numerators(
        "ITBI",
        itbi_uccs,
    )
)


expd_num, expd_diag = (
    diary_numerators(
        expd_uccs,
    )
)


# =============================================================================
# 45 component estimates
# =============================================================================

component_arrays = {
    (
        cohort,
        component,
    ):
        np.zeros(
            45,
            dtype=float,
        )
    for cohort in COHORTS
    for component in COMPONENTS
}


for cohort in COHORTS:

    for _, r in primary.iterrows():

        ucc = r["ucc"]

        family = r[
            "estimator_family"
        ]

        component = r[
            "primary_component"
        ]

        factor = float(
            r["factor"]
        )


        if family == "MTBI":

            numerator = mtbi_num.get(
                (
                    cohort,
                    ucc,
                ),
                np.zeros(
                    45,
                    dtype=float,
                ),
            )

            estimate = (
                numerator
                / denominators[
                    (
                        cohort,
                        "I",
                    )
                ]
                * factor
            )


        elif family == "ITBI":

            numerator = itbi_num.get(
                (
                    cohort,
                    ucc,
                ),
                np.zeros(
                    45,
                    dtype=float,
                ),
            )

            estimate = (
                numerator
                / denominators[
                    (
                        cohort,
                        "I",
                    )
                ]
                * factor
            )


        elif family == "EXPD":

            numerator = expd_num.get(
                (
                    cohort,
                    ucc,
                ),
                np.zeros(
                    45,
                    dtype=float,
                ),
            )

            estimate = (
                numerator
                / denominators[
                    (
                        cohort,
                        "D",
                    )
                ]
                * 13.0
                * factor
            )


        else:

            raise RuntimeError(
                f"unknown estimator family="
                f"{family}"
            )


        if not np.isfinite(
            estimate
        ).all():

            raise RuntimeError(
                f"non-finite UCC estimate "
                f"{cohort} {ucc}"
            )


        component_arrays[
            (
                cohort,
                component,
            )
        ] += estimate



# =============================================================================
# E4B2 — controls, 8-cell outputs, inference, and structural gates
# =============================================================================

CONTROL_COMPONENT_REPS = (
    ROOT
    / "data/results/E3B4C2_2022_component_replicates.tsv"
)

CONTROL_DIFF_REPS = (
    ROOT
    / "data/results/E3B4C2_2022_difference_replicates.tsv"
)

CONTROL_RATIO_REPS = (
    ROOT
    / "data/results/E3B4C2_2022_ratio_replicates.tsv"
)

E4B1_AUDIT = (
    ROOT
    / "data/metadata/E4B1_ch_age35_64_coverage_extension_preflight_audit.txt"
)

E4B1_GRID = (
    ROOT
    / "data/metadata/E4B1_frozen_extended_cex_cohort_grid.tsv"
)

OUT_POINT = (
    ROOT
    / "data/results/E4B2_2022_ch_component_point_estimates.tsv"
)

OUT_COMPARE = (
    ROOT
    / "data/results/E4B2_2022_ch_owner_renter_comparison.tsv"
)

OUT_DENOM_E4B2 = (
    ROOT
    / "data/results/E4B2_2022_ch_brr_denominators.tsv"
)

OUT_COMPONENT_REPS_E4B2 = (
    ROOT
    / "data/results/E4B2_2022_ch_component_replicates.tsv"
)

OUT_DIFF_REPS_E4B2 = (
    ROOT
    / "data/results/E4B2_2022_ch_difference_replicates.tsv"
)

OUT_RATIO_REPS_E4B2 = (
    ROOT
    / "data/results/E4B2_2022_ch_ratio_replicates.tsv"
)

OUT_SUMMARY_E4B2 = (
    ROOT
    / "data/results/E4B2_2022_ch_brr_inference_summary.tsv"
)

AUDIT_E4B2 = (
    ROOT
    / "data/metadata/E4B2_first_ch_8_cell_coverage_execution_audit.txt"
)


EXPECTED_CONTROL_SHA = {
    CONTROL_COMPONENT_REPS:
        "be05c8a8849334906553a3eece1d31f50b4aaaffc5666cf5dcb032cb56ccdd1c",

    CONTROL_DIFF_REPS:
        "956fa63293e2f1c388cae7fc2ddd4a459e12194a6281c78e1d314e7c1d9dbaf0",

    CONTROL_RATIO_REPS:
        "17240bbebcfe81524829f9f6cc3e01072a642c60e982d7d7a5237b753323ae82",

    E4B1_AUDIT:
        "6284bbb15f4e753f4a6418c53afd048609315c4ec05a0334af654c3a4d6cb2ca",

    E4B1_GRID:
        "30bb005a3ddbe98561a3c891ecd63e2c6091fed89e1d633ba8d870e4eff265a1",
}


for path, expected in EXPECTED_CONTROL_SHA.items():

    actual = sha256(
        path
    )

    if actual != expected:

        raise RuntimeError(
            f"E4B2 frozen-control SHA mismatch "
            f"{path}: {actual}"
        )


e4b1_text = E4B1_AUDIT.read_text(
    encoding="utf-8",
)

for token in (
    "E4B1_C_H_AGE35_64_COVERAGE_EXTENSION_PREFLIGHT=PASS",
    "E4B2_FIRST_C_H_8_CELL_COVERAGE_EXECUTION_AUTHORIZED=1",
    "ONLY_COHORT_GRID_EXTENSION_AUTHORIZED=1",
    "AGE25_34_POINT_ESTIMATE_REPRODUCTION_REQUIRED=1",
    "AGE25_34_COMPONENT_REPLICATE_REPRODUCTION_REQUIRED=1",
    "AGE25_34_DIFFERENCE_REPLICATE_REPRODUCTION_REQUIRED=1",
    "AGE25_34_RATIO_REPLICATE_REPRODUCTION_REQUIRED=1",
    "AGE25_34_REPRODUCTION_ATOL=1e-8",
):
    if token not in e4b1_text:
        raise RuntimeError(
            f"missing E4B1 invariant={token}"
        )


grid = pd.read_csv(
    E4B1_GRID,
    sep="\t",
    dtype=str,
).fillna("")


expected_grid_rows = [
    ("AGE25_34_OWNER", "25", "34", "OWNER", "1,2,3"),
    ("AGE25_34_RENTER", "25", "34", "RENTER", "4"),
    ("AGE35_44_OWNER", "35", "44", "OWNER", "1,2,3"),
    ("AGE35_44_RENTER", "35", "44", "RENTER", "4"),
    ("AGE45_54_OWNER", "45", "54", "OWNER", "1,2,3"),
    ("AGE45_54_RENTER", "45", "54", "RENTER", "4"),
    ("AGE55_64_OWNER", "55", "64", "OWNER", "1,2,3"),
    ("AGE55_64_RENTER", "55", "64", "RENTER", "4"),
]


observed_grid_rows = [
    (
        str(r["cohort"]),
        str(r["age_min"]),
        str(r["age_max"]),
        str(r["tenure"]),
        str(r["cutensure"]),
    )
    for _, r in grid.iterrows()
]


if observed_grid_rows != expected_grid_rows:
    raise RuntimeError(
        "E4B1 frozen cohort grid mismatch"
    )


def cohort_parts(
    cohort: str,
) -> tuple[str, str]:

    for age_band in AGE_BANDS:

        prefix = age_band + "_"

        if cohort.startswith(
            prefix
        ):

            tenure = cohort[
                len(prefix):
            ]

            if tenure not in {
                "OWNER",
                "RENTER",
            }:
                break

            return (
                age_band,
                tenure,
            )

    raise RuntimeError(
        f"bad cohort label={cohort}"
    )


# =============================================================================
# All 8 cohorts must be represented in both CEX source family universes
# =============================================================================

source_family_counts = {}


for cohort in COHORTS:

    i_n = int(
        (
            i_fam[
                "cohort"
            ] == cohort
        ).sum()
    )

    d_n = int(
        (
            d_fam[
                "cohort"
            ] == cohort
        ).sum()
    )

    source_family_counts[
        (
            cohort,
            "I",
        )
    ] = i_n

    source_family_counts[
        (
            cohort,
            "D",
        )
    ] = d_n


all_8_cohorts_nonempty_pass = all(
    source_family_counts[
        (
            cohort,
            source,
        )
    ] > 0
    for cohort in COHORTS
    for source in (
        "I",
        "D",
    )
)


# =============================================================================
# Full-sample + replicate denominator gates
# =============================================================================

all_full_denominators_positive_pass = True
all_rep_denominators_positive_pass = True


for cohort in COHORTS:

    for source in (
        "I",
        "D",
    ):

        arr = np.asarray(
            denominators[
                (
                    cohort,
                    source,
                )
            ],
            dtype=float,
        )

        if arr.shape != (45,):
            raise RuntimeError(
                f"bad denominator shape "
                f"{cohort} {source}: {arr.shape}"
            )

        if (
            not math.isfinite(
                float(
                    arr[0]
                )
            )
            or arr[0] <= 0
        ):
            all_full_denominators_positive_pass = False

        if (
            not np.isfinite(
                arr[1:]
            ).all()
            or not (
                arr[1:]
                > 0
            ).all()
        ):
            all_rep_denominators_positive_pass = False


# =============================================================================
# 16 full-sample component point estimates
# =============================================================================

point_rows = []


for cohort in COHORTS:

    age_band, tenure = cohort_parts(
        cohort
    )

    for component in COMPONENTS:

        arr = np.asarray(
            component_arrays[
                (
                    cohort,
                    component,
                )
            ],
            dtype=float,
        )

        if arr.shape != (45,):
            raise RuntimeError(
                f"bad component array shape "
                f"{cohort} {component}: {arr.shape}"
            )

        point_rows.append({
            "year": YEAR,
            "age_band": age_band,
            "tenure": tenure,
            "cohort": cohort,
            "component": component,
            "annual_mean_nominal_usd":
                float(
                    arr[0]
                ),
        })


point_df = pd.DataFrame(
    point_rows
)


# =============================================================================
# Four age-band owner/renter comparison arrays
# =============================================================================

comparison_arrays = {}


for age_band in AGE_BANDS:

    owner_cohort = (
        age_band
        + "_OWNER"
    )

    renter_cohort = (
        age_band
        + "_RENTER"
    )

    for component in COMPONENTS:

        owner = np.asarray(
            component_arrays[
                (
                    owner_cohort,
                    component,
                )
            ],
            dtype=float,
        )

        renter = np.asarray(
            component_arrays[
                (
                    renter_cohort,
                    component,
                )
            ],
            dtype=float,
        )

        if (
            not np.isfinite(
                owner
            ).all()
            or not np.isfinite(
                renter
            ).all()
        ):
            raise RuntimeError(
                f"non-finite comparison source "
                f"{age_band} {component}"
            )

        if (
            owner == 0
        ).any():
            raise RuntimeError(
                f"owner component is zero in a "
                f"full/replicate statistic "
                f"{age_band} {component}"
            )

        difference = (
            renter
            - owner
        )

        ratio = (
            renter
            / owner
        )

        comparison_arrays[
            (
                age_band,
                component,
                "DIFFERENCE",
            )
        ] = difference

        comparison_arrays[
            (
                age_band,
                component,
                "RATIO",
            )
        ] = ratio


comparison_rows = []


for age_band in AGE_BANDS:

    for component in COMPONENTS:

        owner = component_arrays[
            (
                age_band
                + "_OWNER",
                component,
            )
        ]

        renter = component_arrays[
            (
                age_band
                + "_RENTER",
                component,
            )
        ]

        difference = comparison_arrays[
            (
                age_band,
                component,
                "DIFFERENCE",
            )
        ]

        ratio = comparison_arrays[
            (
                age_band,
                component,
                "RATIO",
            )
        ]

        comparison_rows.append({
            "year": YEAR,
            "age_band": age_band,
            "component": component,
            "owner_usd":
                float(
                    owner[0]
                ),
            "renter_usd":
                float(
                    renter[0]
                ),
            "renter_minus_owner_usd":
                float(
                    difference[0]
                ),
            "renter_to_owner_ratio":
                float(
                    ratio[0]
                ),
        })


comparison_df = pd.DataFrame(
    comparison_rows
)


# =============================================================================
# AGE25_34 frozen point-control identity
# =============================================================================

frozen_components = pd.read_csv(
    FROZEN_COMPONENTS,
    sep="\t",
)


point_control_max_abs_error = 0.0
age25_point_identity_pass = True


for cohort in CONTROL_COHORTS:

    for component in COMPONENTS:

        match = frozen_components[
            (
                frozen_components[
                    "cohort"
                ] == cohort
            )
            & (
                frozen_components[
                    "component"
                ] == component
            )
        ]

        if len(
            match
        ) != 1:
            raise RuntimeError(
                f"bad frozen point-control key "
                f"{cohort} {component}"
            )

        expected = float(
            match.iloc[0][
                "annual_mean_nominal_usd"
            ]
        )

        observed = float(
            component_arrays[
                (
                    cohort,
                    component,
                )
            ][0]
        )

        error = abs(
            observed
            - expected
        )

        point_control_max_abs_error = max(
            point_control_max_abs_error,
            error,
        )

        if error > ATOL:
            age25_point_identity_pass = False


# =============================================================================
# 704 component replicate rows
# =============================================================================

component_rep_rows = []


for cohort in COHORTS:

    age_band, tenure = cohort_parts(
        cohort
    )

    for component in COMPONENTS:

        arr = component_arrays[
            (
                cohort,
                component,
            )
        ]

        for r in range(
            1,
            45,
        ):

            component_rep_rows.append({
                "year": YEAR,
                "age_band":
                    age_band,
                "tenure":
                    tenure,
                "replicate":
                    r,
                "weight":
                    REPS[
                        r - 1
                    ],
                "cohort":
                    cohort,
                "component":
                    component,
                "estimate":
                    float(
                        arr[r]
                    ),
            })


component_rep_df = pd.DataFrame(
    component_rep_rows
)


# =============================================================================
# 352 direct difference + 352 direct ratio replicate rows
# =============================================================================

diff_rows = []
ratio_rows = []


for age_band in AGE_BANDS:

    for component in COMPONENTS:

        diff = comparison_arrays[
            (
                age_band,
                component,
                "DIFFERENCE",
            )
        ]

        ratio = comparison_arrays[
            (
                age_band,
                component,
                "RATIO",
            )
        ]

        for r in range(
            1,
            45,
        ):

            diff_rows.append({
                "year": YEAR,
                "age_band":
                    age_band,
                "replicate":
                    r,
                "weight":
                    REPS[
                        r - 1
                    ],
                "component":
                    component,
                "contrast":
                    "RENTER_MINUS_OWNER",
                "renter_minus_owner":
                    float(
                        diff[r]
                    ),
            })

            ratio_rows.append({
                "year": YEAR,
                "age_band":
                    age_band,
                "replicate":
                    r,
                "weight":
                    REPS[
                        r - 1
                    ],
                "component":
                    component,
                "contrast":
                    "RENTER_DIV_OWNER",
                "renter_to_owner_ratio":
                    float(
                        ratio[r]
                    ),
            })


diff_df = pd.DataFrame(
    diff_rows
)

ratio_df = pd.DataFrame(
    ratio_rows
)


# =============================================================================
# AGE25_34 exact frozen replicate controls
# =============================================================================

control_component = pd.read_csv(
    CONTROL_COMPONENT_REPS,
    sep="\t",
)

expected_component_control = (
    control_component[
        control_component[
            "cohort"
        ].isin(
            CONTROL_COHORTS
        )
    ]
    .copy()
)


observed_component_control = (
    component_rep_df[
        component_rep_df[
            "age_band"
        ] == "AGE25_34"
    ][
        [
            "year",
            "replicate",
            "weight",
            "cohort",
            "component",
            "estimate",
        ]
    ]
    .copy()
)


component_control_join = (
    observed_component_control
    .merge(
        expected_component_control,
        on=[
            "year",
            "replicate",
            "weight",
            "cohort",
            "component",
        ],
        how="outer",
        suffixes=(
            "_observed",
            "_expected",
        ),
        validate="one_to_one",
        indicator=True,
    )
)


if (
    component_control_join[
        "_merge"
    ] != "both"
).any():
    raise RuntimeError(
        "AGE25_34 component replicate key mismatch"
    )


component_rep_control_errors = np.abs(
    component_control_join[
        "estimate_observed"
    ].to_numpy(
        dtype=float
    )
    - component_control_join[
        "estimate_expected"
    ].to_numpy(
        dtype=float
    )
)


component_rep_control_max_abs_error = float(
    component_rep_control_errors.max(
        initial=0.0
    )
)


age25_component_rep_identity_pass = bool(
    (
        component_rep_control_errors
        <= ATOL
    ).all()
)


control_diff = pd.read_csv(
    CONTROL_DIFF_REPS,
    sep="\t",
)


observed_diff_control = (
    diff_df[
        diff_df[
            "age_band"
        ] == "AGE25_34"
    ][
        [
            "year",
            "replicate",
            "weight",
            "component",
            "renter_minus_owner",
        ]
    ]
    .copy()
)


diff_control_join = (
    observed_diff_control
    .merge(
        control_diff,
        on=[
            "year",
            "replicate",
            "weight",
            "component",
        ],
        how="outer",
        suffixes=(
            "_observed",
            "_expected",
        ),
        validate="one_to_one",
        indicator=True,
    )
)


if (
    diff_control_join[
        "_merge"
    ] != "both"
).any():
    raise RuntimeError(
        "AGE25_34 difference replicate key mismatch"
    )


diff_control_errors = np.abs(
    diff_control_join[
        "renter_minus_owner_observed"
    ].to_numpy(
        dtype=float
    )
    - diff_control_join[
        "renter_minus_owner_expected"
    ].to_numpy(
        dtype=float
    )
)


diff_control_max_abs_error = float(
    diff_control_errors.max(
        initial=0.0
    )
)


age25_diff_rep_identity_pass = bool(
    (
        diff_control_errors
        <= ATOL
    ).all()
)


control_ratio = pd.read_csv(
    CONTROL_RATIO_REPS,
    sep="\t",
)


observed_ratio_control = (
    ratio_df[
        ratio_df[
            "age_band"
        ] == "AGE25_34"
    ][
        [
            "year",
            "replicate",
            "weight",
            "component",
            "renter_to_owner_ratio",
        ]
    ]
    .copy()
)


ratio_control_join = (
    observed_ratio_control
    .merge(
        control_ratio,
        on=[
            "year",
            "replicate",
            "weight",
            "component",
        ],
        how="outer",
        suffixes=(
            "_observed",
            "_expected",
        ),
        validate="one_to_one",
        indicator=True,
    )
)


if (
    ratio_control_join[
        "_merge"
    ] != "both"
).any():
    raise RuntimeError(
        "AGE25_34 ratio replicate key mismatch"
    )


ratio_control_errors = np.abs(
    ratio_control_join[
        "renter_to_owner_ratio_observed"
    ].to_numpy(
        dtype=float
    )
    - ratio_control_join[
        "renter_to_owner_ratio_expected"
    ].to_numpy(
        dtype=float
    )
)


ratio_control_max_abs_error = float(
    ratio_control_errors.max(
        initial=0.0
    )
)


age25_ratio_rep_identity_pass = bool(
    (
        ratio_control_errors
        <= ATOL
    ).all()
)


# =============================================================================
# 32-row BRR inference summary
# =============================================================================

summary_rows = []


for cohort in COHORTS:

    for component in COMPONENTS:

        arr = component_arrays[
            (
                cohort,
                component,
            )
        ]

        variance, se, lower, upper = (
            brr_stats(
                float(
                    arr[0]
                ),
                arr[1:],
            )
        )

        summary_rows.append({
            "year": YEAR,
            "statistic_type":
                "COMPONENT",
            "cohort":
                cohort,
            "component":
                component,
            "estimate":
                float(
                    arr[0]
                ),
            "brr_variance":
                variance,
            "brr_se":
                se,
            "ci95_lower":
                lower,
            "ci95_upper":
                upper,
        })


for age_band in AGE_BANDS:

    for component in COMPONENTS:

        arr = comparison_arrays[
            (
                age_band,
                component,
                "DIFFERENCE",
            )
        ]

        variance, se, lower, upper = (
            brr_stats(
                float(
                    arr[0]
                ),
                arr[1:],
            )
        )

        summary_rows.append({
            "year": YEAR,
            "statistic_type":
                "RENTER_MINUS_OWNER",
            "cohort":
                (
                    age_band
                    + "_RENTER_MINUS_OWNER"
                ),
            "component":
                component,
            "estimate":
                float(
                    arr[0]
                ),
            "brr_variance":
                variance,
            "brr_se":
                se,
            "ci95_lower":
                lower,
            "ci95_upper":
                upper,
        })


for age_band in AGE_BANDS:

    for component in COMPONENTS:

        arr = comparison_arrays[
            (
                age_band,
                component,
                "RATIO",
            )
        ]

        variance, se, lower, upper = (
            brr_stats(
                float(
                    arr[0]
                ),
                arr[1:],
            )
        )

        summary_rows.append({
            "year": YEAR,
            "statistic_type":
                "RENTER_TO_OWNER_RATIO",
            "cohort":
                (
                    age_band
                    + "_RENTER_DIV_OWNER"
                ),
            "component":
                component,
            "estimate":
                float(
                    arr[0]
                ),
            "brr_variance":
                variance,
            "brr_se":
                se,
            "ci95_lower":
                lower,
            "ci95_upper":
                upper,
        })


summary = pd.DataFrame(
    summary_rows
)


# =============================================================================
# Exact output shapes + finite-value structural gates
# =============================================================================

point_shape_pass = (
    len(
        point_df
    ) == 16
)

comparison_shape_pass = (
    len(
        comparison_df
    ) == 8
)

denom_shape_pass = (
    len(
        denom_df
    ) == 720
)

component_rep_shape_pass = (
    len(
        component_rep_df
    ) == 704
)

difference_rep_shape_pass = (
    len(
        diff_df
    ) == 352
)

ratio_rep_shape_pass = (
    len(
        ratio_df
    ) == 352
)

summary_component_rows = int(
    (
        summary[
            "statistic_type"
        ] == "COMPONENT"
    ).sum()
)

summary_diff_rows = int(
    (
        summary[
            "statistic_type"
        ] == "RENTER_MINUS_OWNER"
    ).sum()
)

summary_ratio_rows = int(
    (
        summary[
            "statistic_type"
        ] == "RENTER_TO_OWNER_RATIO"
    ).sum()
)

summary_shape_pass = (
    len(
        summary
    ) == 32
    and summary_component_rows == 16
    and summary_diff_rows == 8
    and summary_ratio_rows == 8
)


point_finite_pass = bool(
    np.isfinite(
        point_df[
            "annual_mean_nominal_usd"
        ].to_numpy(
            dtype=float
        )
    ).all()
)


comparison_finite_pass = bool(
    np.isfinite(
        comparison_df[
            [
                "owner_usd",
                "renter_usd",
                "renter_minus_owner_usd",
                "renter_to_owner_ratio",
            ]
        ].to_numpy(
            dtype=float
        )
    ).all()
)


component_rep_finite_pass = bool(
    np.isfinite(
        component_rep_df[
            "estimate"
        ].to_numpy(
            dtype=float
        )
    ).all()
)


difference_rep_finite_pass = bool(
    np.isfinite(
        diff_df[
            "renter_minus_owner"
        ].to_numpy(
            dtype=float
        )
    ).all()
)


ratio_rep_finite_pass = bool(
    np.isfinite(
        ratio_df[
            "renter_to_owner_ratio"
        ].to_numpy(
            dtype=float
        )
    ).all()
)


summary_finite_pass = bool(
    np.isfinite(
        summary[
            [
                "estimate",
                "brr_variance",
                "brr_se",
                "ci95_lower",
                "ci95_upper",
            ]
        ].to_numpy(
            dtype=float
        )
    ).all()
    and (
        summary[
            "brr_variance"
        ] >= 0
    ).all()
    and (
        summary[
            "brr_se"
        ] >= 0
    ).all()
)


age25_invariance_pass = all([
    age25_point_identity_pass,
    age25_component_rep_identity_pass,
    age25_diff_rep_identity_pass,
    age25_ratio_rep_identity_pass,
])


exact_output_shape_pass = all([
    point_shape_pass,
    comparison_shape_pass,
    denom_shape_pass,
    component_rep_shape_pass,
    difference_rep_shape_pass,
    ratio_rep_shape_pass,
    summary_shape_pass,
])


all_estimates_finite_pass = all([
    point_finite_pass,
    comparison_finite_pass,
    component_rep_finite_pass,
    difference_rep_finite_pass,
    ratio_rep_finite_pass,
    summary_finite_pass,
])


overall = all([
    all_8_cohorts_nonempty_pass,
    all_full_denominators_positive_pass,
    all_rep_denominators_positive_pass,
    interview_rep_denom_pass,
    diary_rep_denom_pass,
    age25_invariance_pass,
    exact_output_shape_pass,
    all_estimates_finite_pass,
])


# =============================================================================
# Deterministic outputs
# =============================================================================

point_df.to_csv(
    OUT_POINT,
    sep="\t",
    index=False,
    float_format="%.12f",
)

comparison_df.to_csv(
    OUT_COMPARE,
    sep="\t",
    index=False,
    float_format="%.12f",
)

denom_df.to_csv(
    OUT_DENOM_E4B2,
    sep="\t",
    index=False,
    float_format="%.12f",
)

component_rep_df.to_csv(
    OUT_COMPONENT_REPS_E4B2,
    sep="\t",
    index=False,
    float_format="%.12f",
)

diff_df.to_csv(
    OUT_DIFF_REPS_E4B2,
    sep="\t",
    index=False,
    float_format="%.12f",
)

ratio_df.to_csv(
    OUT_RATIO_REPS_E4B2,
    sep="\t",
    index=False,
    float_format="%.12f",
)

summary.to_csv(
    OUT_SUMMARY_E4B2,
    sep="\t",
    index=False,
    float_format="%.12f",
)


# =============================================================================
# Audit
# =============================================================================

lines = [
    "=" * 100,
    "E4B2 — FIRST C-H 8-CELL COVERAGE EXECUTION",
    "=" * 100,
    "",
    "RAW_CEX_DATA_READ=1",
    "CEX_COST_VALUES_READ=1",
    "CEX_WTREP_VALUES_READ=1",
    "AGE25_34_CONTROL_VALUES_RECOMPUTED=1",
    "NEW_AGE35_64_C_H_VALUES_OPENED=1",
    "NEW_STANDARD_ERRORS_COMPUTED=1",
    "NEW_CONFIDENCE_INTERVALS_COMPUTED=1",
    "P_VALUES_COMPUTED=0",
    "DIMENSIONALITY_ANALYSIS_PERFORMED=0",
    "",
    "===== FROZEN ESTIMATOR =====",
    "ONLY_COHORT_GRID_EXTENSION_PERFORMED=1",
    "SOURCE_FAMILY_CHANGES_PERFORMED=0",
    "UCC_MAPPING_CHANGES_PERFORMED=0",
    "CALENDAR_SCOPE_CHANGES_PERFORMED=0",
    "WEIGHT_FORMULA_CHANGES_PERFORMED=0",
    "BRR_FORMULA_CHANGES_PERFORMED=0",
    "COMPONENT_DEFINITION_CHANGES_PERFORMED=0",
    "TENURE_DEFINITION_CHANGES_PERFORMED=0",
    "BRR_REPLICATE_COUNT=44",
    "",
    "===== COHORT SUPPORT =====",
    "CEX_COHORT_COUNT=8",
    (
        "ALL_8_COHORTS_NONEMPTY_IN_BOTH_CEX_SOURCES=PASS"
        if all_8_cohorts_nonempty_pass
        else
        "ALL_8_COHORTS_NONEMPTY_IN_BOTH_CEX_SOURCES=FAIL"
    ),
    (
        "ALL_FULL_SAMPLE_DENOMINATORS_FINITE_POSITIVE=PASS"
        if all_full_denominators_positive_pass
        else
        "ALL_FULL_SAMPLE_DENOMINATORS_FINITE_POSITIVE=FAIL"
    ),
    (
        "ALL_44_REPLICATE_DENOMINATORS_FINITE_POSITIVE=PASS"
        if all_rep_denominators_positive_pass
        else
        "ALL_44_REPLICATE_DENOMINATORS_FINITE_POSITIVE=FAIL"
    ),
    "",
    "===== AGE25_34 INVARIANCE CONTROL =====",
    f"AGE25_34_POINT_MAX_ABS_ERROR={point_control_max_abs_error:.12g}",
    (
        "AGE25_34_POINT_ESTIMATES_REPRODUCE=PASS"
        if age25_point_identity_pass
        else
        "AGE25_34_POINT_ESTIMATES_REPRODUCE=FAIL"
    ),
    f"AGE25_34_COMPONENT_REPLICATE_MAX_ABS_ERROR={component_rep_control_max_abs_error:.12g}",
    (
        "AGE25_34_COMPONENT_REPLICATES_REPRODUCE=PASS"
        if age25_component_rep_identity_pass
        else
        "AGE25_34_COMPONENT_REPLICATES_REPRODUCE=FAIL"
    ),
    f"AGE25_34_DIFFERENCE_REPLICATE_MAX_ABS_ERROR={diff_control_max_abs_error:.12g}",
    (
        "AGE25_34_DIFFERENCE_REPLICATES_REPRODUCE=PASS"
        if age25_diff_rep_identity_pass
        else
        "AGE25_34_DIFFERENCE_REPLICATES_REPRODUCE=FAIL"
    ),
    f"AGE25_34_RATIO_REPLICATE_MAX_ABS_ERROR={ratio_control_max_abs_error:.12g}",
    (
        "AGE25_34_RATIO_REPLICATES_REPRODUCE=PASS"
        if age25_ratio_rep_identity_pass
        else
        "AGE25_34_RATIO_REPLICATES_REPRODUCE=FAIL"
    ),
    "AGE25_34_REPRODUCTION_ATOL=1e-8",
    (
        "AGE25_34_INVARIANCE_CONTROL=PASS"
        if age25_invariance_pass
        else
        "AGE25_34_INVARIANCE_CONTROL=FAIL"
    ),
    "",
    "===== OUTPUT SHAPE =====",
    f"FULL_SAMPLE_COMPONENT_ROWS={len(point_df)}",
    f"OWNER_RENTER_COMPARISON_ROWS={len(comparison_df)}",
    f"BRR_DENOMINATOR_ROWS={len(denom_df)}",
    f"BRR_COMPONENT_REPLICATE_ROWS={len(component_rep_df)}",
    f"BRR_DIFFERENCE_REPLICATE_ROWS={len(diff_df)}",
    f"BRR_RATIO_REPLICATE_ROWS={len(ratio_df)}",
    f"BRR_INFERENCE_COMPONENT_ROWS={summary_component_rows}",
    f"BRR_INFERENCE_DIFFERENCE_ROWS={summary_diff_rows}",
    f"BRR_INFERENCE_RATIO_ROWS={summary_ratio_rows}",
    f"BRR_INFERENCE_SUMMARY_ROWS={len(summary)}",
    (
        "E4B2_EXACT_OUTPUT_SHAPE=PASS"
        if exact_output_shape_pass
        else
        "E4B2_EXACT_OUTPUT_SHAPE=FAIL"
    ),
    "",
    "===== FINITE VALUE GATES =====",
    (
        "E4B2_ALL_ESTIMATES_FINITE=PASS"
        if all_estimates_finite_pass
        else
        "E4B2_ALL_ESTIMATES_FINITE=FAIL"
    ),
    "",
    "===== OUTCOME-INDEPENDENT GATES =====",
    "DIRECTION_GATE=0",
    "MAGNITUDE_GATE=0",
    "SIGNIFICANCE_GATE=0",
    "OWNER_RENTER_DIRECTION_GATE=0",
    "SE_MAGNITUDE_GATE=0",
    "CROSS_DIMENSION_GATE=0",
    "NO_OUTCOME_BASED_CH_GATE=PASS",
    "",
    "H_ACCESS_IMPLEMENTED=0",
    "FIVE_COMPONENT_NORMALIZATION_AUTHORIZED=0",
    "FIVE_COMPONENT_VECTOR_AUTHORIZED=0",
    "DIMENSIONALITY_TEST_AUTHORIZED=0",
    "FIVE_DIMENSIONALITY_PROVEN=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "",
    (
        "E4B2_FIRST_C_H_8_CELL_COVERAGE_EXECUTION=PASS"
        if overall
        else
        "E4B2_FIRST_C_H_8_CELL_COVERAGE_EXECUTION=FAIL"
    ),
    (
        "E4B3_FULL_8_CELL_FIVE_COMPONENT_COVERAGE_CLOSEOUT_AUTHORIZED=1"
        if overall
        else
        "E4B3_FULL_8_CELL_FIVE_COMPONENT_COVERAGE_CLOSEOUT_AUTHORIZED=0"
    ),
    "",
]


for cohort in COHORTS:

    lines.append(
        f"{cohort}__INTERVIEW_FAMILY_ROWS="
        f"{source_family_counts[(cohort, 'I')]}"
    )

    lines.append(
        f"{cohort}__DIARY_FAMILY_ROWS="
        f"{source_family_counts[(cohort, 'D')]}"
    )


lines.extend([
    "",
    "===== FIRST REAL 8-CELL C-H INFERENCE =====",
])


for _, row in summary.iterrows():

    key = (
        str(
            row[
                "statistic_type"
            ]
        )
        + "__"
        + str(
            row[
                "cohort"
            ]
        )
        + "__"
        + str(
            row[
                "component"
            ]
        )
    ).upper()

    lines.extend([
        f"{key}__ESTIMATE={float(row['estimate']):.12f}",
        f"{key}__BRR_SE={float(row['brr_se']):.12f}",
        f"{key}__CI95_LOWER={float(row['ci95_lower']):.12f}",
        f"{key}__CI95_UPPER={float(row['ci95_upper']):.12f}",
    ])


lines.append("")


audit_text = "\n".join(
    lines
)


AUDIT_E4B2.write_text(
    audit_text,
    encoding="utf-8",
)


print(
    audit_text
)


if not overall:
    raise SystemExit(1)
