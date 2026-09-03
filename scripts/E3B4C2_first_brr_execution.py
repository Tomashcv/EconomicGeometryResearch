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


COHORTS = [
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

    eligible = age.between(
        25,
        34,
    )

    out.loc[
        eligible
        & tenure.isin(
            [1, 2, 3]
        )
    ] = "AGE25_34_OWNER"

    out.loc[
        eligible
        & tenure.eq(4)
    ] = "AGE25_34_RENTER"

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
    denom_df[
        denom_df[
            "weight_type"
        ] == "BRR"
    ]
) != 176:

    raise RuntimeError(
        "replicate denominator row count "
        "!= 176"
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
# Full-sample identity
# =============================================================================

frozen_components = pd.read_csv(
    FROZEN_COMPONENTS,
    sep="\t",
)


full_component_identity_pass = True

component_identity_max_abs = 0.0


for cohort in COHORTS:

    for component in COMPONENTS:

        observed = float(
            component_arrays[
                (
                    cohort,
                    component,
                )
            ][0]
        )


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


        if len(match) != 1:

            raise RuntimeError(
                f"bad frozen component key "
                f"{cohort} {component}"
            )


        expected = float(
            match.iloc[0][
                "annual_mean_nominal_usd"
            ]
        )


        error = abs(
            observed
            - expected
        )


        component_identity_max_abs = max(
            component_identity_max_abs,
            error,
        )


        if error > ATOL:

            full_component_identity_pass = False


# =============================================================================
# Full + replicate comparison statistics
# =============================================================================

comparison_arrays = {}


for component in COMPONENTS:

    owner = component_arrays[
        (
            "AGE25_34_OWNER",
            component,
        )
    ]

    renter = component_arrays[
        (
            "AGE25_34_RENTER",
            component,
        )
    ]


    difference = (
        renter
        - owner
    )


    if (
        ~np.isfinite(
            owner
        )
    ).any() or (
        owner == 0
    ).any():

        raise RuntimeError(
            f"invalid owner denominator statistic "
            f"for ratio component={component}"
        )


    ratio = (
        renter
        / owner
    )


    comparison_arrays[
        (
            component,
            "DIFFERENCE",
        )
    ] = difference


    comparison_arrays[
        (
            component,
            "RATIO",
        )
    ] = ratio


frozen_comparison = pd.read_csv(
    FROZEN_COMPARISON,
    sep="\t",
)


full_comparison_identity_pass = True
comparison_identity_max_abs = 0.0


for component in COMPONENTS:

    match = frozen_comparison[
        frozen_comparison[
            "component"
        ] == component
    ]


    if len(match) != 1:

        raise RuntimeError(
            f"bad frozen comparison component="
            f"{component}"
        )


    row = match.iloc[0]


    expected_diff = float(
        row[
            "renter_minus_owner_usd"
        ]
    )


    expected_ratio = float(
        row[
            "renter_to_owner_ratio"
        ]
    )


    observed_diff = float(
        comparison_arrays[
            (
                component,
                "DIFFERENCE",
            )
        ][0]
    )


    observed_ratio = float(
        comparison_arrays[
            (
                component,
                "RATIO",
            )
        ][0]
    )


    for observed, expected in (
        (
            observed_diff,
            expected_diff,
        ),
        (
            observed_ratio,
            expected_ratio,
        ),
    ):

        error = abs(
            observed
            - expected
        )

        comparison_identity_max_abs = max(
            comparison_identity_max_abs,
            error,
        )

        if error > ATOL:

            full_comparison_identity_pass = False


# =============================================================================
# Replicate result tables
# =============================================================================

component_rep_rows = []


for cohort in COHORTS:

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


diff_rows = []
ratio_rows = []


for component in COMPONENTS:

    diff = comparison_arrays[
        (
            component,
            "DIFFERENCE",
        )
    ]

    ratio = comparison_arrays[
        (
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
            "replicate":
                r,
            "weight":
                REPS[
                    r - 1
                ],
            "component":
                component,
            "renter_minus_owner":
                float(
                    diff[r]
                ),
        })


        ratio_rows.append({
            "year": YEAR,
            "replicate":
                r,
            "weight":
                REPS[
                    r - 1
                ],
            "component":
                component,
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
# Inference summary
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


for component in COMPONENTS:

    arr = comparison_arrays[
        (
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
            "AGE25_34_RENTER_MINUS_OWNER",
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


for component in COMPONENTS:

    arr = comparison_arrays[
        (
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
            "AGE25_34_RENTER_DIV_OWNER",
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
# Frozen hard gates — no significance gate
# =============================================================================

component_rep_shape_pass = (
    len(
        component_rep_df
    ) == 176
)


difference_rep_shape_pass = (
    len(
        diff_df
    ) == 88
)


ratio_rep_shape_pass = (
    len(
        ratio_df
    ) == 88
)


component_finite_pass = bool(
    np.isfinite(
        component_rep_df[
            "estimate"
        ].to_numpy(
            dtype=float
        )
    ).all()
)


difference_finite_pass = bool(
    np.isfinite(
        diff_df[
            "renter_minus_owner"
        ].to_numpy(
            dtype=float
        )
    ).all()
)


ratio_finite_pass = bool(
    np.isfinite(
        ratio_df[
            "renter_to_owner_ratio"
        ].to_numpy(
            dtype=float
        )
    ).all()
)


variance_pass = bool(
    np.isfinite(
        summary[
            "brr_variance"
        ].to_numpy(
            dtype=float
        )
    ).all()
    and (
        summary[
            "brr_variance"
        ] >= 0
    ).all()
)


se_pass = bool(
    np.isfinite(
        summary[
            "brr_se"
        ].to_numpy(
            dtype=float
        )
    ).all()
    and (
        summary[
            "brr_se"
        ] >= 0
    ).all()
)


ci_finite_pass = bool(
    np.isfinite(
        summary[
            [
                "ci95_lower",
                "ci95_upper",
            ]
        ].to_numpy(
            dtype=float
        )
    ).all()
)


overall = all([
    full_component_identity_pass,
    full_comparison_identity_pass,
    interview_rep_denom_pass,
    diary_rep_denom_pass,
    component_rep_shape_pass,
    difference_rep_shape_pass,
    ratio_rep_shape_pass,
    component_finite_pass,
    difference_finite_pass,
    ratio_finite_pass,
    variance_pass,
    se_pass,
    ci_finite_pass,
])


# =============================================================================
# Outputs
# =============================================================================

denom_df.to_csv(
    OUT_DENOM,
    sep="\t",
    index=False,
    float_format="%.12f",
)


component_rep_df.to_csv(
    OUT_COMPONENT_REPS,
    sep="\t",
    index=False,
    float_format="%.12f",
)


diff_df.to_csv(
    OUT_DIFF_REPS,
    sep="\t",
    index=False,
    float_format="%.12f",
)


ratio_df.to_csv(
    OUT_RATIO_REPS,
    sep="\t",
    index=False,
    float_format="%.12f",
)


summary.to_csv(
    OUT_SUMMARY,
    sep="\t",
    index=False,
    float_format="%.12f",
)


# =============================================================================
# Audit
# =============================================================================

lines = [
    "=" * 100,
    "E3B4C2 — FIRST 44-REPLICATE BRR EXECUTION",
    "=" * 100,
    "",
    "MICRODATA_DATA_ROWS_PARSED=1",
    "COST_VALUES_READ=1",
    "ITBI_VALUE_VALUES_READ=1",
    "WTREP_VALUES_READ=1",
    "STANDARD_ERRORS_COMPUTED=1",
    "CONFIDENCE_INTERVALS_COMPUTED=1",
    "P_VALUES_COMPUTED=0",
    "REAL_INFLATION_ESTIMATED=0",
    "",
    "===== FULL-SAMPLE IDENTITY =====",
    f"COMPONENT_IDENTITY_MAX_ABS_ERROR={component_identity_max_abs:.12g}",
    (
        "FULL_SAMPLE_COMPONENT_IDENTITY=PASS"
        if full_component_identity_pass
        else
        "FULL_SAMPLE_COMPONENT_IDENTITY=FAIL"
    ),
    f"COMPARISON_IDENTITY_MAX_ABS_ERROR={comparison_identity_max_abs:.12g}",
    (
        "FULL_SAMPLE_COMPARISON_IDENTITY=PASS"
        if full_comparison_identity_pass
        else
        "FULL_SAMPLE_COMPARISON_IDENTITY=FAIL"
    ),
    "FULL_SAMPLE_IDENTITY_ATOL=1e-8",
    "",
    "===== REPLICATE DENOMINATORS =====",
    (
        "INTERVIEW_REPLICATE_DENOMINATORS_FINITE_POSITIVE=PASS"
        if interview_rep_denom_pass
        else
        "INTERVIEW_REPLICATE_DENOMINATORS_FINITE_POSITIVE=FAIL"
    ),
    (
        "DIARY_REPLICATE_DENOMINATORS_FINITE_POSITIVE=PASS"
        if diary_rep_denom_pass
        else
        "DIARY_REPLICATE_DENOMINATORS_FINITE_POSITIVE=FAIL"
    ),
    "",
    "===== SOURCE DIAGNOSTICS =====",
    f"MTBI_SELECTED_ROWS={mtbi_diag['selected']}",
    f"ITBI_SELECTED_ROWS={itbi_diag['selected']}",
    f"EXPD_SELECTED_ROWS={expd_diag['selected']}",
    f"MTBI_MISSING_VALUE_ROWS={mtbi_diag['missing']}",
    f"ITBI_MISSING_VALUE_ROWS={itbi_diag['missing']}",
    f"EXPD_MISSING_VALUE_ROWS={expd_diag['missing']}",
    f"MTBI_NEGATIVE_VALUE_ROWS={mtbi_diag['negative']}",
    f"ITBI_NEGATIVE_VALUE_ROWS={itbi_diag['negative']}",
    f"EXPD_NEGATIVE_VALUE_ROWS={expd_diag['negative']}",
    "MISSING_EXPENDITURE_VALUE_ACTION=ZERO",
    "MISSING_REPLICATE_WEIGHT_ACTION=ZERO",
    "NEGATIVE_EXPENDITURE_VALUE_ACTION=PRESERVED",
    "",
    "===== REPLICATE SHAPE =====",
    "REPLICATE_COUNT=44",
    f"COMPONENT_REPLICATE_ROWS={len(component_rep_df)}",
    f"DIFFERENCE_REPLICATE_ROWS={len(diff_df)}",
    f"RATIO_REPLICATE_ROWS={len(ratio_df)}",
    (
        "COMPONENT_REPLICATE_SHAPE=PASS"
        if component_rep_shape_pass
        else
        "COMPONENT_REPLICATE_SHAPE=FAIL"
    ),
    (
        "DIFFERENCE_REPLICATE_SHAPE=PASS"
        if difference_rep_shape_pass
        else
        "DIFFERENCE_REPLICATE_SHAPE=FAIL"
    ),
    (
        "RATIO_REPLICATE_SHAPE=PASS"
        if ratio_rep_shape_pass
        else
        "RATIO_REPLICATE_SHAPE=FAIL"
    ),
    "",
    "===== FINITE-VALUE GATES =====",
    (
        "ALL_REPLICATE_COMPONENT_VALUES_FINITE=PASS"
        if component_finite_pass
        else
        "ALL_REPLICATE_COMPONENT_VALUES_FINITE=FAIL"
    ),
    (
        "ALL_REPLICATE_DIFFERENCES_FINITE=PASS"
        if difference_finite_pass
        else
        "ALL_REPLICATE_DIFFERENCES_FINITE=FAIL"
    ),
    (
        "ALL_REPLICATE_RATIOS_FINITE=PASS"
        if ratio_finite_pass
        else
        "ALL_REPLICATE_RATIOS_FINITE=FAIL"
    ),
    (
        "BRR_VARIANCE_NONNEGATIVE=PASS"
        if variance_pass
        else
        "BRR_VARIANCE_NONNEGATIVE=FAIL"
    ),
    (
        "BRR_SE_FINITE=PASS"
        if se_pass
        else
        "BRR_SE_FINITE=FAIL"
    ),
    (
        "CI95_FINITE=PASS"
        if ci_finite_pass
        else
        "CI95_FINITE=FAIL"
    ),
    "",
    "===== FROZEN METHODS =====",
    "BRR_VARIANCE_FORMULA=(1/44)*SUM((THETA_R-THETA)^2)",
    "CI95_MULTIPLIER=1.96",
    "OWNER_RENTER_DIFFERENCE_REPLICATE=DIRECT",
    "OWNER_RENTER_RATIO_REPLICATE=DIRECT",
    "SOURCE_VARIANCE_POSTHOC_SUM=PROHIBITED",
    "",
    "SIGN_GATE=0",
    "MAGNITUDE_GATE=0",
    "SE_MAGNITUDE_GATE=0",
    "CI_EXCLUDES_NULL_GATE=0",
    "OUTCOME_BASED_SELECTION=0",
    "",
]


for _, r in summary.iterrows():

    key = (
        str(
            r["statistic_type"]
        )
        + "__"
        + str(
            r["cohort"]
        )
        + "__"
        + str(
            r["component"]
        )
    ).upper()


    key = (
        key
        .replace(
            "-",
            "_",
        )
        .replace(
            "/",
            "_",
        )
    )


    lines.extend([
        f"{key}__ESTIMATE={float(r['estimate']):.12f}",
        f"{key}__BRR_SE={float(r['brr_se']):.12f}",
        f"{key}__CI95_LOWER={float(r['ci95_lower']):.12f}",
        f"{key}__CI95_UPPER={float(r['ci95_upper']):.12f}",
    ])


lines.extend([
    "",
    (
        "COHORT_INFERENTIAL_INTERPRETATION_AUTHORIZED=1"
        if overall
        else
        "COHORT_INFERENTIAL_INTERPRETATION_AUTHORIZED=0"
    ),
    "OBSERVED_EXPENDITURE_CHANGE_EQUALS_INFLATION=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "",
    (
        "E3B4C2_FIRST_BRR_EXECUTION=PASS"
        if overall
        else
        "E3B4C2_FIRST_BRR_EXECUTION=FAIL"
    ),
    "",
])


AUDIT.write_text(
    "\n".join(lines),
    encoding="utf-8",
)


print(
    "\n".join(lines)
)


if not overall:
    raise SystemExit(1)
