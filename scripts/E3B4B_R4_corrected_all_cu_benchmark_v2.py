from __future__ import annotations

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

CONTRACT = (
    ROOT
    / "data/metadata/E3B4B_R3_R1_estimator_v2_ucc_source_contract.tsv"
)

R3_AUDIT = (
    ROOT
    / "data/metadata/E3B4B_R3_R1_repaired_source_family_contract_v2_audit.txt"
)

TARGETS = (
    ROOT
    / "data/metadata/E3B4B_official_2022_targets.tsv"
)

ORIGINAL_PRECOMMIT = (
    ROOT
    / "docs/E3B4B_all_cu_benchmark_precommit.md"
)

V1_BENCHMARK = (
    ROOT
    / "data/results/E3B4B_2022_all_cu_major_category_benchmark.tsv"
)

OUT = (
    ROOT
    / "data/results/E3B4B_R4_2022_all_cu_major_category_benchmark_v2.tsv"
)

COMP_OUT = (
    ROOT
    / "data/results/E3B4B_R4_2022_all_cu_component_benchmark_v2.tsv"
)

ITBI_OUT = (
    ROOT
    / "data/results/E3B4B_R4_2022_itbi_ucc_point_estimates.tsv"
)

DELTA_OUT = (
    ROOT
    / "data/results/E3B4B_R4_v1_v2_category_repair_delta.tsv"
)

AUDIT = (
    ROOT
    / "data/metadata/E3B4B_R4_corrected_all_cu_benchmark_v2_audit.txt"
)


YEAR = 2022

OFFICIAL_TOTAL = 72967.0
OFFICIAL_C_COST = 37172.0
OFFICIAL_H_SERVICE = 19056.0


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
        "72c253f9295aad902c39636277b7cf23aa5f651206eb8ff416d58a45e7bbf047",

    R3_AUDIT:
        "63a2cff4678bdb51ffc1be0e9e6c36ad7ccb5521ecb3beab4e35b1230dba66b4",

    TARGETS:
        "b8f8d0933e0fea647a1c307581afefe925be5a5e6c0ddfe773f9132e08129871",

    ORIGINAL_PRECOMMIT:
        "00d10d6e3664de89557ed36ac609502f9cc3aa22a3c41607254135f3f106196f",

    V1_BENCHMARK:
        "42cf805879f0ad9746e9f6bacfbc207cf531d09aac8b12da2430dd24a886eb14",
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
            f"{archive.name}: "
            f"expected one {basename}; "
            f"found={matches}"
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


# =============================================================================
# Frozen V2 contract
# =============================================================================

mapping = pd.read_csv(
    MAP,
    sep="\t",
    dtype=str,
).fillna("")

contract = pd.read_csv(
    CONTRACT,
    sep="\t",
    dtype=str,
).fillna("")


if len(mapping) != 645:
    raise RuntimeError(
        f"map rows={len(mapping)}"
    )


if len(contract) != 645:
    raise RuntimeError(
        f"contract rows={len(contract)}"
    )


if contract["ucc"].nunique() != 645:
    raise RuntimeError(
        "contract UCCs not unique"
    )


family_counts = Counter(
    contract["estimator_family"]
)


if family_counts != Counter({
    "MTBI": 390,
    "ITBI": 8,
    "EXPD": 247,
}):

    raise RuntimeError(
        f"V2 family mutation={family_counts}"
    )


factor_counts = Counter(
    contract["factor"]
)


if factor_counts != Counter({
    "1": 642,
    "4": 3,
}):

    raise RuntimeError(
        f"factor mutation={factor_counts}"
    )


mtbi_uccs = set(
    contract.loc[
        contract["estimator_family"]
        == "MTBI",
        "ucc",
    ]
)

itbi_uccs = set(
    contract.loc[
        contract["estimator_family"]
        == "ITBI",
        "ucc",
    ]
)

expd_uccs = set(
    contract.loc[
        contract["estimator_family"]
        == "EXPD",
        "ucc",
    ]
)


# =============================================================================
# Interview family/population denominator
# Same frozen calendar-year denominator as V1
# =============================================================================

I_PLAN = [
    (INT21, "221"),
    (INT22, "222"),
    (INT22, "223"),
    (INT22, "224"),
    (INT22, "231"),
]


i_fam_parts = []


for archive, q in I_PLAN:

    df = read_member(
        archive,
        f"fmli{q}.csv",
        {
            "NEWID",
            "FINLWT21",
            "QINTRVMO",
            "QINTRVYR",
        },
    )

    df["quarter"] = q
    df["newid"] = norm_id(df["NEWID"])
    df["finlwt21"] = num(df["FINLWT21"])
    df["month"] = num(df["QINTRVMO"])
    df["year"] = num(df["QINTRVYR"])

    if (
        df["finlwt21"].isna().any()
        or (df["finlwt21"] <= 0).any()
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
        & df["month"].between(
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
        & df["month"].between(
            4,
            12,
        )
    )

    scope[mask] = 1.0


    mask = (
        (df["year"] == YEAR + 1)
        & df["month"].between(
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


    df["key"] = (
        df["quarter"]
        + "|"
        + df["newid"]
    )


    if df["key"].duplicated().any():

        raise RuntimeError(
            f"duplicate FMLI key q={q}"
        )


    i_fam_parts.append(
        df[
            [
                "key",
                "finlwt21",
                "popwt",
            ]
        ]
    )


i_fam = pd.concat(
    i_fam_parts,
    ignore_index=True,
)


I_POP = float(
    i_fam["popwt"].sum()
)


if (
    not math.isfinite(I_POP)
    or I_POP <= 0
):

    raise RuntimeError(
        f"invalid Interview denominator={I_POP}"
    )


# =============================================================================
# Diary denominator
# =============================================================================

D_PLAN = [
    (DIA22, "221"),
    (DIA22, "222"),
    (DIA22, "223"),
    (DIA22, "224"),
]


d_fam_parts = []


for archive, q in D_PLAN:

    df = read_member(
        archive,
        f"fmld{q}.csv",
        {
            "NEWID",
            "FINLWT21",
        },
    )

    df["quarter"] = q
    df["newid"] = norm_id(df["NEWID"])
    df["finlwt21"] = num(df["FINLWT21"])


    if (
        df["finlwt21"].isna().any()
        or (df["finlwt21"] <= 0).any()
    ):

        raise RuntimeError(
            f"bad Diary weight q={q}"
        )


    df["popwt"] = (
        df["finlwt21"]
        / 4.0
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


    d_fam_parts.append(
        df[
            [
                "key",
                "finlwt21",
                "popwt",
            ]
        ]
    )


d_fam = pd.concat(
    d_fam_parts,
    ignore_index=True,
)


D_POP = float(
    d_fam["popwt"].sum()
)


if (
    not math.isfinite(D_POP)
    or D_POP <= 0
):

    raise RuntimeError(
        f"invalid Diary denominator={D_POP}"
    )


# =============================================================================
# Common family joins
# =============================================================================

i_join = i_fam[
    [
        "key",
        "finlwt21",
    ]
]


d_join = d_fam[
    [
        "key",
        "finlwt21",
    ]
]


# =============================================================================
# MTBI — 390 UCCs
# =============================================================================

mtbi_parts = []

mtbi_unmatched = 0
mtbi_missing_value = 0
mtbi_negative_value = 0
mtbi_selected_rows = 0


for archive, q in I_PLAN:

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

    df["quarter"] = q
    df["newid"] = norm_id(
        df["NEWID"]
    )
    df["ucc"] = norm_ucc(
        df["UCC"]
    )
    df["ref_mo"] = num(
        df["REF_MO"]
    )
    df["ref_yr"] = num(
        df["REF_YR"]
    )


    df = df[
        df["ucc"].isin(
            mtbi_uccs
        )
        & (df["ref_yr"] == YEAR)
        & df["ref_mo"].between(
            1,
            12,
        )
    ].copy()


    mtbi_selected_rows += len(df)

    raw_value = num(
        df["COST"]
    )

    mtbi_missing_value += int(
        raw_value.isna().sum()
    )

    df["value"] = (
        raw_value
        .fillna(0.0)
    )

    mtbi_negative_value += int(
        (df["value"] < 0).sum()
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


    mtbi_unmatched += int(
        (
            m["_merge"]
            != "both"
        ).sum()
    )


    m["weighted"] = (
        m["value"]
        * m["finlwt21"]
    )


    mtbi_parts.append(
        m[
            [
                "ucc",
                "weighted",
            ]
        ]
    )


if mtbi_unmatched:

    raise RuntimeError(
        f"MTBI unmatched={mtbi_unmatched}"
    )


mtbi_exp = pd.concat(
    mtbi_parts,
    ignore_index=True,
)


mtbi_num = (
    mtbi_exp
    .groupby("ucc")["weighted"]
    .sum()
    .to_dict()
)


# =============================================================================
# ITBI — corrected 8 UCCs
# =============================================================================

itbi_parts = []

itbi_unmatched = 0
itbi_missing_value = 0
itbi_negative_value = 0
itbi_selected_rows = 0
itbi_topcoded_rows = 0


for archive, q in I_PLAN:

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

    df["quarter"] = q
    df["newid"] = norm_id(
        df["NEWID"]
    )
    df["ucc"] = norm_ucc(
        df["UCC"]
    )
    df["ref_mo"] = num(
        df["REFMO"]
    )
    df["ref_yr"] = num(
        df["REFYR"]
    )


    df = df[
        df["ucc"].isin(
            itbi_uccs
        )
        & (df["ref_yr"] == YEAR)
        & df["ref_mo"].between(
            1,
            12,
        )
    ].copy()


    itbi_selected_rows += len(df)


    topflag = (
        df["VALUE_"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    itbi_topcoded_rows += int(
        topflag.eq("T").sum()
    )


    raw_value = num(
        df["VALUE"]
    )


    itbi_missing_value += int(
        raw_value.isna().sum()
    )


    df["value"] = (
        raw_value
        .fillna(0.0)
    )


    itbi_negative_value += int(
        (df["value"] < 0).sum()
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


    itbi_unmatched += int(
        (
            m["_merge"]
            != "both"
        ).sum()
    )


    m["weighted"] = (
        m["value"]
        * m["finlwt21"]
    )


    itbi_parts.append(
        m[
            [
                "ucc",
                "weighted",
            ]
        ]
    )


if itbi_unmatched:

    raise RuntimeError(
        f"ITBI unmatched={itbi_unmatched}"
    )


itbi_exp = pd.concat(
    itbi_parts,
    ignore_index=True,
)


itbi_num = (
    itbi_exp
    .groupby("ucc")["weighted"]
    .sum()
    .to_dict()
)


# =============================================================================
# EXPD — 247 Diary UCCs
# =============================================================================

expd_parts = []

expd_unmatched = 0
expd_missing_value = 0
expd_negative_value = 0
expd_selected_rows = 0


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


    df = df[
        df["ucc"].isin(
            expd_uccs
        )
    ].copy()


    expd_selected_rows += len(df)


    raw_value = num(
        df["COST"]
    )


    expd_missing_value += int(
        raw_value.isna().sum()
    )


    df["value"] = (
        raw_value
        .fillna(0.0)
    )


    expd_negative_value += int(
        (df["value"] < 0).sum()
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


    expd_unmatched += int(
        (
            m["_merge"]
            != "both"
        ).sum()
    )


    m["weighted"] = (
        m["value"]
        * m["finlwt21"]
    )


    expd_parts.append(
        m[
            [
                "ucc",
                "weighted",
            ]
        ]
    )


if expd_unmatched:

    raise RuntimeError(
        f"EXPD unmatched={expd_unmatched}"
    )


expd_exp = pd.concat(
    expd_parts,
    ignore_index=True,
)


expd_num = (
    expd_exp
    .groupby("ucc")["weighted"]
    .sum()
    .to_dict()
)


# =============================================================================
# Estimate all 645 UCCs
# =============================================================================

ucc_rows = []


for _, row in contract.iterrows():

    ucc = row["ucc"]
    family = row[
        "estimator_family"
    ]
    factor = float(
        row["factor"]
    )


    if family == "MTBI":

        numerator = float(
            mtbi_num.get(
                ucc,
                0.0,
            )
        )

        source_mean = (
            numerator
            / I_POP
        )


    elif family == "ITBI":

        numerator = float(
            itbi_num.get(
                ucc,
                0.0,
            )
        )

        source_mean = (
            numerator
            / I_POP
        )


    elif family == "EXPD":

        numerator = float(
            expd_num.get(
                ucc,
                0.0,
            )
        )

        source_mean = (
            numerator
            / D_POP
            * 13.0
        )


    else:

        raise RuntimeError(
            f"unknown family={family}"
        )


    annual = (
        source_mean
        * factor
    )


    if not math.isfinite(
        annual
    ):

        raise RuntimeError(
            f"non-finite UCC={ucc}"
        )


    ucc_rows.append({
        "ucc": ucc,
        "estimator_family":
            family,
        "factor":
            factor,
        "broad_category":
            row["broad_category"],
        "primary_component":
            row["primary_component"],
        "estimate_usd":
            annual,
    })


ucc_df = pd.DataFrame(
    ucc_rows
)


if len(ucc_df) != 645:

    raise RuntimeError(
        "incomplete 645-UCC estimate"
    )


# =============================================================================
# ITBI aggregate diagnostic
# =============================================================================

itbi_diag = (
    ucc_df[
        ucc_df[
            "estimator_family"
        ] == "ITBI"
    ]
    .copy()
    .sort_values("ucc")
)


if len(itbi_diag) != 8:

    raise RuntimeError(
        "ITBI estimate count != 8"
    )


itbi_diag.to_csv(
    ITBI_OUT,
    sep="\t",
    index=False,
    float_format="%.10f",
)


# =============================================================================
# 14 major categories
# =============================================================================

estimated = (
    ucc_df
    .groupby(
        "broad_category",
        as_index=False,
    )["estimate_usd"]
    .sum()
)


targets = pd.read_csv(
    TARGETS,
    sep="\t",
)


if len(targets) != 14:

    raise RuntimeError(
        "official target count != 14"
    )


bench = targets.merge(
    estimated,
    left_on="category",
    right_on="broad_category",
    how="left",
    validate="one_to_one",
)


if bench[
    "estimate_usd"
].isna().any():

    raise RuntimeError(
        "missing major-category estimates"
    )


bench["difference_usd"] = (
    bench["estimate_usd"]
    - bench["official_mean_usd"]
)


bench[
    "absolute_difference_usd"
] = bench[
    "difference_usd"
].abs()


bench["ape"] = (
    bench[
        "absolute_difference_usd"
    ]
    / bench[
        "official_mean_usd"
    ]
)


bench["ape_pct"] = (
    bench["ape"]
    * 100.0
)


bench["within_5pct"] = (
    bench["ape"]
    <= 0.05
).astype(int)


estimated_total = float(
    bench[
        "estimate_usd"
    ].sum()
)


official_total_check = float(
    bench[
        "official_mean_usd"
    ].sum()
)


if (
    official_total_check
    != OFFICIAL_TOTAL
):

    raise RuntimeError(
        f"official total mutation="
        f"{official_total_check}"
    )


total_ape = (
    abs(
        estimated_total
        - OFFICIAL_TOTAL
    )
    / OFFICIAL_TOTAL
)


weighted_error_ratio = (
    float(
        bench[
            "absolute_difference_usd"
        ].sum()
    )
    / OFFICIAL_TOTAL
)


within_5 = int(
    bench[
        "within_5pct"
    ].sum()
)


# =============================================================================
# Project components
# =============================================================================

c_cost_est = float(
    ucc_df.loc[
        ucc_df[
            "primary_component"
        ] == "C_COST",
        "estimate_usd",
    ].sum()
)


h_service_est = float(
    ucc_df.loc[
        ucc_df[
            "primary_component"
        ] == "H_SERVICE",
        "estimate_usd",
    ].sum()
)


c_cost_ape = (
    abs(
        c_cost_est
        - OFFICIAL_C_COST
    )
    / OFFICIAL_C_COST
)


h_service_ape = (
    abs(
        h_service_est
        - OFFICIAL_H_SERVICE
    )
    / OFFICIAL_H_SERVICE
)


component_df = pd.DataFrame([
    {
        "component": "C_COST",
        "official_target_usd":
            OFFICIAL_C_COST,
        "pumd_v2_estimate_usd":
            c_cost_est,
        "difference_usd":
            c_cost_est
            - OFFICIAL_C_COST,
        "ape_pct":
            100.0
            * c_cost_ape,
    },
    {
        "component": "H_SERVICE",
        "official_target_usd":
            OFFICIAL_H_SERVICE,
        "pumd_v2_estimate_usd":
            h_service_est,
        "difference_usd":
            h_service_est
            - OFFICIAL_H_SERVICE,
        "ape_pct":
            100.0
            * h_service_ape,
    },
])


# =============================================================================
# V1 -> V2 category deltas
# Diagnostic only — never a gate
# =============================================================================

v1 = pd.read_csv(
    V1_BENCHMARK,
    sep="\t",
)


delta = (
    bench[
        [
            "category",
            "official_mean_usd",
            "estimate_usd",
        ]
    ]
    .rename(
        columns={
            "estimate_usd":
                "v2_estimate_usd",
        }
    )
    .merge(
        v1[
            [
                "category",
                "estimate_usd",
            ]
        ].rename(
            columns={
                "estimate_usd":
                    "v1_estimate_usd",
            }
        ),
        on="category",
        how="left",
        validate="one_to_one",
    )
)


delta["v2_minus_v1_usd"] = (
    delta["v2_estimate_usd"]
    - delta["v1_estimate_usd"]
)


# =============================================================================
# EXACT ORIGINAL GATES — NO CHANGES
# =============================================================================

positive_categories = bool(
    (
        bench[
            "estimate_usd"
        ]
        > 0
    ).all()
)


structural = all([
    len(bench) == 14,
    len(ucc_df) == 645,
    mtbi_unmatched == 0,
    itbi_unmatched == 0,
    expd_unmatched == 0,
    positive_categories,
])


total_gate = (
    total_ape
    <= 0.03
)


weighted_error_gate = (
    weighted_error_ratio
    <= 0.03
)


category_gate = (
    within_5
    >= 10
)


component_gate = (
    c_cost_ape
    <= 0.05
    and
    h_service_ape
    <= 0.05
)


overall = all([
    structural,
    total_gate,
    weighted_error_gate,
    category_gate,
    component_gate,
])


# =============================================================================
# Outputs
# =============================================================================

bench[
    [
        "category",
        "official_mean_usd",
        "estimate_usd",
        "difference_usd",
        "absolute_difference_usd",
        "ape_pct",
        "within_5pct",
    ]
].to_csv(
    OUT,
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


delta.to_csv(
    DELTA_OUT,
    sep="\t",
    index=False,
    float_format="%.10f",
)


pip_row = bench[
    bench["category"]
    == "Personal insurance and pensions"
].iloc[0]


misc_row = bench[
    bench["category"]
    == "Miscellaneous"
].iloc[0]


edu_row = bench[
    bench["category"]
    == "Education"
].iloc[0]


audit_lines = [
    "=" * 100,
    "E3B4B R4 — CORRECTED ALL-CU OFFICIAL BLS BENCHMARK V2",
    "=" * 100,
    "",
    "COST_VALUES_READ=1",
    "ITBI_VALUE_VALUES_READ=1",
    "CORRECTED_ECONOMIC_VALUES_OPENED=1",
    "REAL_INFLATION_ESTIMATED=0",
    "",
    "===== ESTIMATOR V2 =====",
    "MTBI_UCCS=390",
    "ITBI_UCCS=8",
    "EXPD_UCCS=247",
    "ITII_APPENDED=0",
    "ITBI_POINT_VALUE_FIELD=VALUE",
    "ITBI_REFERENCE_MONTH_FIELD=REFMO",
    "ITBI_REFERENCE_YEAR_FIELD=REFYR",
    "",
    "===== POPULATION DENOMINATORS =====",
    f"INTERVIEW_POP_DENOMINATOR={I_POP:.10f}",
    f"DIARY_POP_DENOMINATOR={D_POP:.10f}",
    "",
    "===== SOURCE DIAGNOSTICS =====",
    f"MTBI_SELECTED_ROWS={mtbi_selected_rows}",
    f"ITBI_SELECTED_ROWS={itbi_selected_rows}",
    f"EXPD_SELECTED_ROWS={expd_selected_rows}",
    f"MTBI_UNMATCHED={mtbi_unmatched}",
    f"ITBI_UNMATCHED={itbi_unmatched}",
    f"EXPD_UNMATCHED={expd_unmatched}",
    f"MTBI_MISSING_VALUE_ROWS={mtbi_missing_value}",
    f"ITBI_MISSING_VALUE_ROWS={itbi_missing_value}",
    f"EXPD_MISSING_VALUE_ROWS={expd_missing_value}",
    f"MTBI_NEGATIVE_VALUE_ROWS={mtbi_negative_value}",
    f"ITBI_NEGATIVE_VALUE_ROWS={itbi_negative_value}",
    f"EXPD_NEGATIVE_VALUE_ROWS={expd_negative_value}",
    f"ITBI_TOPCODED_ROWS={itbi_topcoded_rows}",
    "NEGATIVE_VALUE_ACTION=PRESERVED",
    "MISSING_VALUE_ACTION=ZERO",
    "",
    "===== STRUCTURE =====",
    "INTEGRATED_UCCS=645",
    "MAJOR_CATEGORY_COUNT=14",
    (
        "STRUCTURAL_BENCHMARK_GATE=PASS"
        if structural
        else
        "STRUCTURAL_BENCHMARK_GATE=FAIL"
    ),
    "",
    "===== ORIGINAL TOTAL GATE =====",
    f"OFFICIAL_TOTAL_USD={OFFICIAL_TOTAL:.10f}",
    f"PUMD_V2_TOTAL_USD={estimated_total:.10f}",
    f"TOTAL_APE_PCT={100.0 * total_ape:.10f}",
    (
        "TOTAL_APE_LE_3PCT=PASS"
        if total_gate
        else
        "TOTAL_APE_LE_3PCT=FAIL"
    ),
    "",
    "===== ORIGINAL CATEGORY GATES =====",
    f"WEIGHTED_ABSOLUTE_ERROR_RATIO_PCT={100.0 * weighted_error_ratio:.10f}",
    (
        "WEIGHTED_ERROR_LE_3PCT=PASS"
        if weighted_error_gate
        else
        "WEIGHTED_ERROR_LE_3PCT=FAIL"
    ),
    f"CATEGORIES_WITHIN_5PCT={within_5}",
    (
        "AT_LEAST_10_OF_14_WITHIN_5PCT=PASS"
        if category_gate
        else
        "AT_LEAST_10_OF_14_WITHIN_5PCT=FAIL"
    ),
    "",
    "===== ORIGINAL COMPONENT GATE =====",
    f"C_COST_OFFICIAL_USD={OFFICIAL_C_COST:.10f}",
    f"C_COST_V2_USD={c_cost_est:.10f}",
    f"C_COST_APE_PCT={100.0 * c_cost_ape:.10f}",
    f"H_SERVICE_OFFICIAL_USD={OFFICIAL_H_SERVICE:.10f}",
    f"H_SERVICE_V2_USD={h_service_est:.10f}",
    f"H_SERVICE_APE_PCT={100.0 * h_service_ape:.10f}",
    (
        "COMPONENT_APE_LE_5PCT=PASS"
        if component_gate
        else
        "COMPONENT_APE_LE_5PCT=FAIL"
    ),
    "",
    "===== REPAIR-SENSITIVE CATEGORIES =====",
    f"PIP_V2_USD={float(pip_row['estimate_usd']):.10f}",
    f"PIP_V2_APE_PCT={float(pip_row['ape_pct']):.10f}",
    f"MISC_V2_USD={float(misc_row['estimate_usd']):.10f}",
    f"MISC_V2_APE_PCT={float(misc_row['ape_pct']):.10f}",
    f"EDUCATION_V2_USD={float(edu_row['estimate_usd']):.10f}",
    f"EDUCATION_V2_APE_PCT={float(edu_row['ape_pct']):.10f}",
    "",
    "===== HISTORICAL STATE =====",
    "ORIGINAL_E3B4B_V1_FAIL=PRESERVED",
    "ORIGINAL_E3B4A_V1_RESULTS=PRESERVED",
    "E3B4A_V1_MAGNITUDES_VALIDATED=0",
    "",
    "===== INTERPRETATION STATE =====",
    "OBSERVED_EXPENDITURE_CHANGE_EQUALS_INFLATION=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "COHORT_POINT_ESTIMATE_INTERPRETATION_AUTHORIZED=0",
    (
        "ESTIMATOR_V2_BENCHMARK_VALIDATED=1"
        if overall
        else
        "ESTIMATOR_V2_BENCHMARK_VALIDATED=0"
    ),
    (
        "E3B4A_V2_COHORT_RERUN_AUTHORIZED=1"
        if overall
        else
        "E3B4A_V2_COHORT_RERUN_AUTHORIZED=0"
    ),
    "",
    (
        "E3B4B_R4_CORRECTED_ALL_CU_BENCHMARK_V2=PASS"
        if overall
        else
        "E3B4B_R4_CORRECTED_ALL_CU_BENCHMARK_V2=FAIL"
    ),
    "",
]


AUDIT.write_text(
    "\n".join(audit_lines),
    encoding="utf-8",
)


print(
    "\n".join(audit_lines)
)


if not overall:
    raise SystemExit(1)
