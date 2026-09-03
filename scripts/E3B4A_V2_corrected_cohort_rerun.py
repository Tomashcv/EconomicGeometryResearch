from __future__ import annotations

import hashlib
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

CONTRACT = (
    ROOT
    / "data/metadata/E3B4B_R3_R1_estimator_v2_ucc_source_contract.tsv"
)

R4_AUDIT = (
    ROOT
    / "data/metadata/E3B4B_R4_corrected_all_cu_benchmark_v2_audit.txt"
)

V1_DENOM = (
    ROOT
    / "data/results/E3B4A_2022_cohort_denominators.tsv"
)

V1_COMPONENT = (
    ROOT
    / "data/results/E3B4A_2022_component_point_estimates.tsv"
)

OUT_DENOM = (
    ROOT
    / "data/results/E3B4A_V2_2022_cohort_denominators.tsv"
)

OUT_UCC = (
    ROOT
    / "data/results/E3B4A_V2_2022_primary_ucc_estimates.tsv"
)

OUT_COMPONENT = (
    ROOT
    / "data/results/E3B4A_V2_2022_component_point_estimates.tsv"
)

OUT_COMPARE = (
    ROOT
    / "data/results/E3B4A_V2_2022_owner_renter_comparison.tsv"
)

OUT_ITBI = (
    ROOT
    / "data/results/E3B4A_V2_2022_itbi_primary_ucc_estimates.tsv"
)

OUT_DELTA = (
    ROOT
    / "data/results/E3B4A_V2_v1_v2_component_delta.tsv"
)

AUDIT = (
    ROOT
    / "data/metadata/E3B4A_V2_corrected_cohort_rerun_audit.txt"
)


EXPECTED_SHA = {
    INT21:
        "9b449829fd10ee71227a3de044e6b6d67e568cc7c02a759dda14e4b0278697f0",

    INT22:
        "c99a2f47c0084b7a88812b34c56a1a288be2798ff010b2b59dcf87e072773e17",

    DIA22:
        "c285e72fd7513c78caa158c75975c5b03e91049a9ffe9ee6d41966dc4ef20963",

    CONTRACT:
        "72c253f9295aad902c39636277b7cf23aa5f651206eb8ff416d58a45e7bbf047",

    R4_AUDIT:
        "5694812f3cdf0fcdb60f2fea09842873f4a08790ffc5b0359970742a76d1eab3",

    V1_DENOM:
        "1bd03f0ba5cf9939536cf404f7a42a5385b48b1c1a4e504b1a17fcf7789cc744",

    V1_COMPONENT:
        "453c2a122b68fac9cbaa3b8e19dbbacbcc858fb4a6781588525266d132b86fd2",
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


r4_text = R4_AUDIT.read_text(
    encoding="utf-8"
)

for token in (
    "E3B4B_R4_CORRECTED_ALL_CU_BENCHMARK_V2=PASS",
    "ESTIMATOR_V2_BENCHMARK_VALIDATED=1",
    "E3B4A_V2_COHORT_RERUN_AUTHORIZED=1",
):

    if token not in r4_text:

        raise RuntimeError(
            f"missing R4 invariant={token}"
        )


# =============================================================================
# Helpers
# =============================================================================

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
            f"{archive.name}: expected one "
            f"{basename}; found={matches}"
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
            f"{member}: missing="
            f"{sorted(missing)}"
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
        lambda x:
            x.zfill(6)
            if x.isdigit()
            else x
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


def cohort_from(
    age: pd.Series,
    tenure: pd.Series,
) -> pd.Series:

    out = pd.Series(
        "",
        index=age.index,
        dtype="object",
    )

    eligible_age = age.between(
        25,
        34,
    )

    owner = (
        eligible_age
        & tenure.isin(
            [1, 2, 3]
        )
    )

    renter = (
        eligible_age
        & tenure.eq(4)
    )

    out.loc[owner] = (
        "AGE25_34_OWNER"
    )

    out.loc[renter] = (
        "AGE25_34_RENTER"
    )

    return out


COHORTS = [
    "AGE25_34_OWNER",
    "AGE25_34_RENTER",
]


# =============================================================================
# Frozen primary V2 contract
# =============================================================================

contract = pd.read_csv(
    CONTRACT,
    sep="\t",
    dtype=str,
).fillna("")


primary = contract[
    contract[
        "primary_component"
    ].isin([
        "C_COST",
        "H_SERVICE",
    ])
].copy()


if len(primary) != 534:

    raise RuntimeError(
        f"primary UCC count={len(primary)}"
    )


family_counts = Counter(
    primary[
        "estimator_family"
    ]
)


if family_counts != Counter({
    "MTBI": 316,
    "ITBI": 3,
    "EXPD": 215,
}):

    raise RuntimeError(
        f"primary V2 family mutation="
        f"{family_counts}"
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
# Interview family universe
# =============================================================================

I_PLAN = [
    (INT21, "221"),
    (INT22, "222"),
    (INT22, "223"),
    (INT22, "224"),
    (INT22, "231"),
]


i_parts = []


for archive, q in I_PLAN:

    df = read_member(
        archive,
        f"fmli{q}.csv",
        {
            "NEWID",
            "AGE_REF",
            "CUTENURE",
            "FINLWT21",
            "QINTRVMO",
            "QINTRVYR",
        },
    )

    df["quarter"] = q
    df["newid"] = norm_id(
        df["NEWID"]
    )

    df["age"] = num(
        df["AGE_REF"]
    )

    df["tenure"] = num(
        df["CUTENURE"]
    )

    df["finlwt21"] = num(
        df["FINLWT21"]
    )

    df["month"] = num(
        df["QINTRVMO"]
    )

    df["year"] = num(
        df["QINTRVYR"]
    )


    if (
        df["finlwt21"].isna().any()
        or
        (df["finlwt21"] <= 0).any()
    ):

        raise RuntimeError(
            f"bad Interview weight q={q}"
        )


    scope = np.full(
        len(df),
        np.nan,
        dtype=float,
    )


    mask = (
        (df["year"] == YEAR)
        &
        df["month"].between(
            1,
            3,
        )
    )

    scope[mask] = (
        df.loc[
            mask,
            "month",
        ]
        - 1
    ) / 3.0


    mask = (
        (df["year"] == YEAR)
        &
        df["month"].between(
            4,
            12,
        )
    )

    scope[mask] = 1.0


    mask = (
        (df["year"] == YEAR + 1)
        &
        df["month"].between(
            1,
            3,
        )
    )

    scope[mask] = (
        4
        - df.loc[
            mask,
            "month",
        ]
    ) / 3.0


    if np.isnan(scope).any():

        raise RuntimeError(
            f"unexpected Interview timing q={q}"
        )


    df["popwt"] = (
        df["finlwt21"]
        / 4.0
        * scope
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
            f"duplicate FMLI key q={q}"
        )


    i_parts.append(
        df[
            [
                "key",
                "finlwt21",
                "popwt",
                "cohort",
            ]
        ]
    )


i_fam = pd.concat(
    i_parts,
    ignore_index=True,
)


# =============================================================================
# Diary family universe
# =============================================================================

D_PLAN = [
    (DIA22, "221"),
    (DIA22, "222"),
    (DIA22, "223"),
    (DIA22, "224"),
]


d_parts = []


for archive, q in D_PLAN:

    df = read_member(
        archive,
        f"fmld{q}.csv",
        {
            "NEWID",
            "AGE_REF",
            "CUTENURE",
            "FINLWT21",
        },
    )

    df["quarter"] = q

    df["newid"] = norm_id(
        df["NEWID"]
    )

    df["age"] = num(
        df["AGE_REF"]
    )

    df["tenure"] = num(
        df["CUTENURE"]
    )

    df["finlwt21"] = num(
        df["FINLWT21"]
    )


    if (
        df["finlwt21"].isna().any()
        or
        (df["finlwt21"] <= 0).any()
    ):

        raise RuntimeError(
            f"bad Diary weight q={q}"
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
            f"duplicate FMLD key q={q}"
        )


    d_parts.append(
        df[
            [
                "key",
                "finlwt21",
                "popwt",
                "cohort",
            ]
        ]
    )


d_fam = pd.concat(
    d_parts,
    ignore_index=True,
)


# =============================================================================
# Cohort denominators
# =============================================================================

denom_rows = []


for cohort in COHORTS:

    for source, fam in (
        ("I", i_fam),
        ("D", d_fam),
    ):

        x = fam[
            fam["cohort"]
            == cohort
        ]

        denom_rows.append({
            "year": YEAR,
            "cohort": cohort,
            "source": source,
            "family_rows":
                len(x),
            "unique_newid":
                x["key"].nunique(),
            "population_denominator":
                float(
                    x["popwt"].sum()
                ),
        })


denom = pd.DataFrame(
    denom_rows
)


# =============================================================================
# Compare denominators to V1
# =============================================================================

v1_denom = pd.read_csv(
    V1_DENOM,
    sep="\t",
)


denom_check = denom.merge(
    v1_denom,
    on=[
        "year",
        "cohort",
        "source",
    ],
    suffixes=(
        "_v2",
        "_v1",
    ),
    validate="one_to_one",
)


denominator_identity_pass = bool(
    (
        denom_check[
            "family_rows_v2"
        ]
        ==
        denom_check[
            "family_rows_v1"
        ]
    ).all()
    and
    (
        denom_check[
            "unique_newid_v2"
        ]
        ==
        denom_check[
            "unique_newid_v1"
        ]
    ).all()
    and
    np.allclose(
        denom_check[
            "population_denominator_v2"
        ],
        denom_check[
            "population_denominator_v1"
        ],
        rtol=0.0,
        atol=1e-6,
    )
)


if not denominator_identity_pass:

    raise RuntimeError(
        "V2 cohort denominators changed from V1"
    )


pop_lookup = {
    (
        r["cohort"],
        r["source"],
    ):
        float(
            r[
                "population_denominator"
            ]
        )
    for _, r in denom.iterrows()
}


# =============================================================================
# Expense-table join helpers
# =============================================================================

i_join = i_fam[
    [
        "key",
        "finlwt21",
        "cohort",
    ]
]


d_join = d_fam[
    [
        "key",
        "finlwt21",
        "cohort",
    ]
]


def aggregate_interview_family(
    family: str,
    uccs: set[str],
) -> tuple[
    dict[tuple[str, str], float],
    dict[str, int],
]:

    pieces = []

    unmatched = 0
    missing = 0
    negative = 0
    selected = 0
    topcoded = 0


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

            df["ref_mo"] = num(
                df["REF_MO"]
            )

            df["ref_yr"] = num(
                df["REF_YR"]
            )

            raw = num(
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
                    "VALUE_",
                    "REFMO",
                    "REFYR",
                },
            )

            df["ref_mo"] = num(
                df["REFMO"]
            )

            df["ref_yr"] = num(
                df["REFYR"]
            )

            raw = num(
                df["VALUE"]
            )

            topflag = (
                df["VALUE_"]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.upper()
            )

            topcoded += int(
                topflag.eq("T").sum()
            )


        else:

            raise RuntimeError(
                f"bad Interview family={family}"
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
            &
            (df["ref_yr"] == YEAR)
            &
            df["ref_mo"].between(
                1,
                12,
            )
        )


        df = df.loc[
            keep
        ].copy()


        raw = raw.loc[
            keep
        ]


        selected += len(df)

        missing += int(
            raw.isna().sum()
        )


        df["value"] = (
            raw
            .fillna(0.0)
            .to_numpy()
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


        m = m[
            m["cohort"].isin(
                COHORTS
            )
        ].copy()


        m["weighted"] = (
            m["value"]
            * m["finlwt21"]
        )


        pieces.append(
            m[
                [
                    "cohort",
                    "ucc",
                    "weighted",
                ]
            ]
        )


    if unmatched:

        raise RuntimeError(
            f"{family} unmatched={unmatched}"
        )


    all_rows = pd.concat(
        pieces,
        ignore_index=True,
    )


    agg = (
        all_rows
        .groupby(
            [
                "cohort",
                "ucc",
            ]
        )["weighted"]
        .sum()
        .to_dict()
    )


    diag = {
        "selected": selected,
        "unmatched": unmatched,
        "missing": missing,
        "negative": negative,
        "topcoded": topcoded,
    }


    return agg, diag


def aggregate_diary(
    uccs: set[str],
) -> tuple[
    dict[tuple[str, str], float],
    dict[str, int],
]:

    pieces = []

    unmatched = 0
    missing = 0
    negative = 0
    selected = 0


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


        raw = num(
            df["COST"]
        )


        selected += len(df)

        missing += int(
            raw.isna().sum()
        )


        df["value"] = (
            raw
            .fillna(0.0)
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


        m = m[
            m["cohort"].isin(
                COHORTS
            )
        ].copy()


        m["weighted"] = (
            m["value"]
            * m["finlwt21"]
        )


        pieces.append(
            m[
                [
                    "cohort",
                    "ucc",
                    "weighted",
                ]
            ]
        )


    if unmatched:

        raise RuntimeError(
            f"EXPD unmatched={unmatched}"
        )


    all_rows = pd.concat(
        pieces,
        ignore_index=True,
    )


    agg = (
        all_rows
        .groupby(
            [
                "cohort",
                "ucc",
            ]
        )["weighted"]
        .sum()
        .to_dict()
    )


    diag = {
        "selected": selected,
        "unmatched": unmatched,
        "missing": missing,
        "negative": negative,
        "topcoded": 0,
    }


    return agg, diag


mtbi_num, mtbi_diag = (
    aggregate_interview_family(
        "MTBI",
        mtbi_uccs,
    )
)


itbi_num, itbi_diag = (
    aggregate_interview_family(
        "ITBI",
        itbi_uccs,
    )
)


expd_num, expd_diag = (
    aggregate_diary(
        expd_uccs
    )
)


# =============================================================================
# Every cohort x every primary UCC
# =============================================================================

rows = []


for cohort in COHORTS:

    for _, r in primary.iterrows():

        ucc = r["ucc"]
        family = r[
            "estimator_family"
        ]

        factor = float(
            r["factor"]
        )


        if family == "MTBI":

            numerator = float(
                mtbi_num.get(
                    (
                        cohort,
                        ucc,
                    ),
                    0.0,
                )
            )

            raw_mean = (
                numerator
                /
                pop_lookup[
                    (
                        cohort,
                        "I",
                    )
                ]
            )


        elif family == "ITBI":

            numerator = float(
                itbi_num.get(
                    (
                        cohort,
                        ucc,
                    ),
                    0.0,
                )
            )

            raw_mean = (
                numerator
                /
                pop_lookup[
                    (
                        cohort,
                        "I",
                    )
                ]
            )


        elif family == "EXPD":

            numerator = float(
                expd_num.get(
                    (
                        cohort,
                        ucc,
                    ),
                    0.0,
                )
            )

            raw_mean = (
                numerator
                /
                pop_lookup[
                    (
                        cohort,
                        "D",
                    )
                ]
                * 13.0
            )


        else:

            raise RuntimeError(
                f"unknown family={family}"
            )


        estimate = (
            raw_mean
            * factor
        )


        if not math.isfinite(
            estimate
        ):

            raise RuntimeError(
                f"non-finite estimate "
                f"{cohort} {ucc}"
            )


        rows.append({
            "year": YEAR,
            "cohort": cohort,
            "ucc": ucc,
            "component":
                r["primary_component"],
            "estimator_family":
                family,
            "factor":
                factor,
            "broad_category":
                r["broad_category"],
            "subcategory":
                r["subcategory"],
            "leaf_title":
                r["leaf_title"],
            "annual_mean_nominal_usd":
                estimate,
        })


ucc_df = pd.DataFrame(
    rows
)


if len(ucc_df) != 1068:

    raise RuntimeError(
        f"expected 1068 cohort-UCC rows; "
        f"got={len(ucc_df)}"
    )


# =============================================================================
# Component estimates
# =============================================================================

component = (
    ucc_df
    .groupby(
        [
            "year",
            "cohort",
            "component",
        ],
        as_index=False,
    )[
        "annual_mean_nominal_usd"
    ]
    .sum()
)


if len(component) != 4:

    raise RuntimeError(
        f"component rows={len(component)}"
    )


family_component = (
    ucc_df
    .groupby(
        [
            "cohort",
            "component",
            "estimator_family",
        ]
    )[
        "annual_mean_nominal_usd"
    ]
    .sum()
    .to_dict()
)


for idx, row in component.iterrows():

    cohort = row["cohort"]
    comp = row["component"]

    component.loc[
        idx,
        "mtbi_contribution_usd",
    ] = family_component.get(
        (
            cohort,
            comp,
            "MTBI",
        ),
        0.0,
    )

    component.loc[
        idx,
        "itbi_contribution_usd",
    ] = family_component.get(
        (
            cohort,
            comp,
            "ITBI",
        ),
        0.0,
    )

    component.loc[
        idx,
        "expd_contribution_usd",
    ] = family_component.get(
        (
            cohort,
            comp,
            "EXPD",
        ),
        0.0,
    )


component = component[
    [
        "year",
        "cohort",
        "component",
        "mtbi_contribution_usd",
        "itbi_contribution_usd",
        "expd_contribution_usd",
        "annual_mean_nominal_usd",
    ]
]


# =============================================================================
# V1 -> V2 mechanical delta
# =============================================================================

v1_component = pd.read_csv(
    V1_COMPONENT,
    sep="\t",
)


delta = component[
    [
        "year",
        "cohort",
        "component",
        "annual_mean_nominal_usd",
        "itbi_contribution_usd",
    ]
].rename(
    columns={
        "annual_mean_nominal_usd":
            "v2_usd",
    }
).merge(
    v1_component[
        [
            "year",
            "cohort",
            "component",
            "annual_mean_nominal_usd",
        ]
    ].rename(
        columns={
            "annual_mean_nominal_usd":
                "v1_usd",
        }
    ),
    on=[
        "year",
        "cohort",
        "component",
    ],
    how="left",
    validate="one_to_one",
)


delta["v2_minus_v1_usd"] = (
    delta["v2_usd"]
    - delta["v1_usd"]
)


h_delta = delta[
    delta["component"]
    == "H_SERVICE"
]


c_delta = delta[
    delta["component"]
    == "C_COST"
]


h_identity_pass = np.allclose(
    h_delta[
        "v2_minus_v1_usd"
    ],
    0.0,
    rtol=0.0,
    atol=1e-8,
)


c_identity_pass = np.allclose(
    c_delta[
        "v2_minus_v1_usd"
    ],
    c_delta[
        "itbi_contribution_usd"
    ],
    rtol=0.0,
    atol=1e-8,
)


# =============================================================================
# Owner vs renter
# =============================================================================

owner = component[
    component["cohort"]
    == "AGE25_34_OWNER"
][
    [
        "component",
        "annual_mean_nominal_usd",
    ]
].rename(
    columns={
        "annual_mean_nominal_usd":
            "owner_25_34_usd",
    }
)


renter = component[
    component["cohort"]
    == "AGE25_34_RENTER"
][
    [
        "component",
        "annual_mean_nominal_usd",
    ]
].rename(
    columns={
        "annual_mean_nominal_usd":
            "renter_25_34_usd",
    }
)


comparison = owner.merge(
    renter,
    on="component",
    how="inner",
    validate="one_to_one",
)


comparison.insert(
    0,
    "year",
    YEAR,
)


comparison[
    "renter_minus_owner_usd"
] = (
    comparison[
        "renter_25_34_usd"
    ]
    -
    comparison[
        "owner_25_34_usd"
    ]
)


comparison[
    "renter_to_owner_ratio"
] = (
    comparison[
        "renter_25_34_usd"
    ]
    /
    comparison[
        "owner_25_34_usd"
    ]
)


# =============================================================================
# ITBI primary diagnostics
# =============================================================================

itbi_primary = ucc_df[
    ucc_df[
        "estimator_family"
    ] == "ITBI"
].copy()


if len(itbi_primary) != 6:

    raise RuntimeError(
        f"expected 6 cohort x ITBI rows; "
        f"got={len(itbi_primary)}"
    )


# =============================================================================
# Structural gates only
# =============================================================================

expected_rows = {
    ("AGE25_34_OWNER", "I"): 1486,
    ("AGE25_34_RENTER", "I"): 1918,
    ("AGE25_34_OWNER", "D"): 775,
    ("AGE25_34_RENTER", "D"): 908,
}


row_count_pass = True


for _, r in denom.iterrows():

    expected = expected_rows[
        (
            r["cohort"],
            r["source"],
        )
    ]

    if int(
        r["family_rows"]
    ) != expected:

        row_count_pass = False


structural = all([
    len(ucc_df) == 1068,
    len(component) == 4,
    len(comparison) == 2,
    len(itbi_primary) == 6,
    row_count_pass,
    denominator_identity_pass,
    h_identity_pass,
    c_identity_pass,
])


# =============================================================================
# Outputs
# =============================================================================

denom.to_csv(
    OUT_DENOM,
    sep="\t",
    index=False,
    float_format="%.10f",
)


ucc_df.to_csv(
    OUT_UCC,
    sep="\t",
    index=False,
    float_format="%.10f",
)


component.to_csv(
    OUT_COMPONENT,
    sep="\t",
    index=False,
    float_format="%.10f",
)


comparison.to_csv(
    OUT_COMPARE,
    sep="\t",
    index=False,
    float_format="%.10f",
)


itbi_primary.to_csv(
    OUT_ITBI,
    sep="\t",
    index=False,
    float_format="%.10f",
)


delta.to_csv(
    OUT_DELTA,
    sep="\t",
    index=False,
    float_format="%.10f",
)


# =============================================================================
# Audit
# =============================================================================

lines = [
    "=" * 100,
    "E3B4A V2 — CORRECTED 2022 COHORT POINT ESTIMATES",
    "=" * 100,
    "",
    "COST_VALUES_READ=1",
    "ITBI_VALUE_VALUES_READ=1",
    "CORRECTED_COHORT_ECONOMIC_VALUES_OPENED=1",
    "REAL_INFLATION_ESTIMATED=0",
    "",
    "===== DESIGN =====",
    "YEAR=2022",
    "COHORT_1=AGE25_34_OWNER",
    "COHORT_2=AGE25_34_RENTER",
    "AGE_RANGE=25..34",
    "OWNER_CUTENURE=1,2,3",
    "RENTER_CUTENURE=4",
    "",
    "===== VALIDATED V2 PRIMARY MAP =====",
    "PRIMARY_UCCS=534",
    f"PRIMARY_MTBI_UCCS={family_counts['MTBI']}",
    f"PRIMARY_ITBI_UCCS={family_counts['ITBI']}",
    f"PRIMARY_EXPD_UCCS={family_counts['EXPD']}",
    "",
    "===== DENOMINATOR IDENTITY =====",
    f"DENOMINATOR_IDENTITY_WITH_V1={'PASS' if denominator_identity_pass else 'FAIL'}",
    f"EXPECTED_FAMILY_ROW_COUNTS={'PASS' if row_count_pass else 'FAIL'}",
    "",
]


for _, r in denom.iterrows():

    lines.extend([
        (
            f"{r['cohort']}_{r['source']}_FAMILY_ROWS="
            f"{int(r['family_rows'])}"
        ),
        (
            f"{r['cohort']}_{r['source']}_POP_DENOMINATOR="
            f"{float(r['population_denominator']):.10f}"
        ),
    ])


lines.extend([
    "",
    "===== SOURCE DIAGNOSTICS =====",
    f"MTBI_SELECTED_ROWS={mtbi_diag['selected']}",
    f"ITBI_SELECTED_ROWS={itbi_diag['selected']}",
    f"EXPD_SELECTED_ROWS={expd_diag['selected']}",
    f"MTBI_UNMATCHED={mtbi_diag['unmatched']}",
    f"ITBI_UNMATCHED={itbi_diag['unmatched']}",
    f"EXPD_UNMATCHED={expd_diag['unmatched']}",
    f"MTBI_MISSING_VALUE_ROWS={mtbi_diag['missing']}",
    f"ITBI_MISSING_VALUE_ROWS={itbi_diag['missing']}",
    f"EXPD_MISSING_VALUE_ROWS={expd_diag['missing']}",
    f"MTBI_NEGATIVE_VALUE_ROWS={mtbi_diag['negative']}",
    f"ITBI_NEGATIVE_VALUE_ROWS={itbi_diag['negative']}",
    f"EXPD_NEGATIVE_VALUE_ROWS={expd_diag['negative']}",
    f"ITBI_TOPCODED_ROWS={itbi_diag['topcoded']}",
    "NEGATIVE_VALUE_ACTION=PRESERVED",
    "MISSING_VALUE_ACTION=ZERO",
    "",
    "===== V1 -> V2 MECHANICAL IDENTITIES =====",
    (
        "H_SERVICE_V2_EQUALS_V1=PASS"
        if h_identity_pass
        else
        "H_SERVICE_V2_EQUALS_V1=FAIL"
    ),
    (
        "C_COST_V2_MINUS_V1_EQUALS_ITBI_CONTRIBUTION=PASS"
        if c_identity_pass
        else
        "C_COST_V2_MINUS_V1_EQUALS_ITBI_CONTRIBUTION=FAIL"
    ),
    "",
    "===== OUTPUT STRUCTURE =====",
    f"PRIMARY_UCC_ESTIMATE_ROWS={len(ucc_df)}",
    f"ITBI_PRIMARY_COHORT_UCC_ROWS={len(itbi_primary)}",
    f"COMPONENT_ESTIMATE_ROWS={len(component)}",
    f"OWNER_RENTER_COMPARISON_ROWS={len(comparison)}",
    "",
    "POINT_ESTIMATE_VALUES_HARD_GATED_BY_SIGN=0",
    "POINT_ESTIMATE_VALUES_HARD_GATED_BY_MAGNITUDE=0",
    "OUTCOME_BASED_SELECTION=0",
    "",
    f"STRUCTURAL_COHORT_RERUN_GATE={'PASS' if structural else 'FAIL'}",
    "",
    "===== HISTORICAL STATE =====",
    "E3B4A_V1_RESULTS=PRESERVED",
    "E3B4A_V1_MAGNITUDES_VALIDATED=0",
    "",
    "===== INTERPRETATION =====",
    "ESTIMATOR_V2_BENCHMARK_VALIDATED=1",
    (
        "CORRECTED_COHORT_POINT_ESTIMATES_VALIDATED=1"
        if structural
        else
        "CORRECTED_COHORT_POINT_ESTIMATES_VALIDATED=0"
    ),
    (
        "COHORT_POINT_ESTIMATE_INTERPRETATION_AUTHORIZED=1"
        if structural
        else
        "COHORT_POINT_ESTIMATE_INTERPRETATION_AUTHORIZED=0"
    ),
    "COHORT_INFERENTIAL_INTERPRETATION_AUTHORIZED=0",
    "BRR_REQUIRED_BEFORE_INFERENCE=1",
    "OBSERVED_EXPENDITURE_CHANGE_EQUALS_INFLATION=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "",
    (
        "E3B4A_V2_CORRECTED_COHORT_RERUN=PASS"
        if structural
        else
        "E3B4A_V2_CORRECTED_COHORT_RERUN=FAIL"
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


if not structural:
    raise SystemExit(1)
