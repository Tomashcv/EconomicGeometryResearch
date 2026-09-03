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

TARGETS = (
    ROOT
    / "data/metadata/E3B4B_official_2022_targets.tsv"
)

OUT = (
    ROOT
    / "data/results/E3B4B_2022_all_cu_major_category_benchmark.tsv"
)

COMP_OUT = (
    ROOT
    / "data/results/E3B4B_2022_all_cu_component_benchmark.tsv"
)

AUDIT = (
    ROOT
    / "data/metadata/E3B4B_all_cu_official_benchmark_audit.txt"
)


YEAR = 2022


EXPECTED_SHA = {
    INT21:
        "9b449829fd10ee71227a3de044e6b6d67e568cc7c02a759dda14e4b0278697f0",

    INT22:
        "c99a2f47c0084b7a88812b34c56a1a288be2798ff010b2b59dcf87e072773e17",

    DIA22:
        "c285e72fd7513c78caa158c75975c5b03e91049a9ffe9ee6d41966dc4ef20963",

    MAP:
        "a6dd2e592d45f0c7c8428a8265d3b857c615cd842e10241fff06d2a3c06c1e1f",
}


OFFICIAL_TOTAL = 72967.0
OFFICIAL_C_COST = 37172.0
OFFICIAL_H_SERVICE = 19056.0


# =============================================================================
# Helpers
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

    missing = fields - set(df.columns)

    if missing:
        raise RuntimeError(
            f"{member}: missing={sorted(missing)}"
        )

    return df


def norm_id(s: pd.Series) -> pd.Series:

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


def norm_ucc(s: pd.Series) -> pd.Series:

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


def num(s: pd.Series) -> pd.Series:

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
# Frozen integrated map
# =============================================================================

mapping = pd.read_csv(
    MAP,
    sep="\t",
    dtype=str,
).fillna("")


if len(mapping) != 645:
    raise RuntimeError(
        f"expected 645 integrated UCCs; got={len(mapping)}"
    )


if mapping["ucc"].nunique() != 645:
    raise RuntimeError(
        "integrated UCCs are not unique"
    )


if Counter(mapping["source"]) != Counter({
    "I": 398,
    "D": 247,
}):
    raise RuntimeError(
        "source count mutation"
    )


if Counter(mapping["factor"]) != Counter({
    "1": 642,
    "4": 3,
}):
    raise RuntimeError(
        "factor count mutation"
    )


mapping["factor_num"] = pd.to_numeric(
    mapping["factor"],
    errors="raise",
)


i_uccs = set(
    mapping.loc[
        mapping["source"] == "I",
        "ucc",
    ]
)

d_uccs = set(
    mapping.loc[
        mapping["source"] == "D",
        "ucc",
    ]
)


# =============================================================================
# Interview all-CU denominator
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
        & df["month"].between(1, 3)
    )

    scope[mask] = (
        df.loc[mask, "month"]
        - 1
    ) / 3.0

    mask = (
        (df["year"] == YEAR)
        & df["month"].between(4, 12)
    )

    scope[mask] = 1.0

    mask = (
        (df["year"] == YEAR + 1)
        & df["month"].between(1, 3)
    )

    scope[mask] = (
        4
        - df.loc[mask, "month"]
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

if not math.isfinite(I_POP) or I_POP <= 0:
    raise RuntimeError(
        f"invalid Interview denominator={I_POP}"
    )


# =============================================================================
# Diary all-CU denominator
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

if not math.isfinite(D_POP) or D_POP <= 0:
    raise RuntimeError(
        f"invalid Diary denominator={D_POP}"
    )


# =============================================================================
# Interview numerators
# =============================================================================

i_join = i_fam[
    [
        "key",
        "finlwt21",
    ]
]


i_parts = []
i_unmatched = 0


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
    df["newid"] = norm_id(df["NEWID"])
    df["ucc"] = norm_ucc(df["UCC"])
    df["ref_mo"] = num(df["REF_MO"])
    df["ref_yr"] = num(df["REF_YR"])

    df = df[
        df["ucc"].isin(i_uccs)
        & (df["ref_yr"] == YEAR)
        & df["ref_mo"].between(1, 12)
    ].copy()

    df["cost"] = (
        num(df["COST"])
        .fillna(0.0)
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

    i_unmatched += int(
        (m["_merge"] != "both").sum()
    )

    m["weighted"] = (
        m["cost"]
        * m["finlwt21"]
    )

    i_parts.append(
        m[
            [
                "ucc",
                "weighted",
            ]
        ]
    )


if i_unmatched:
    raise RuntimeError(
        f"Interview unmatched={i_unmatched}"
    )


i_exp = pd.concat(
    i_parts,
    ignore_index=True,
)


i_num = (
    i_exp
    .groupby("ucc")["weighted"]
    .sum()
    .to_dict()
)


# =============================================================================
# Diary numerators
# =============================================================================

d_join = d_fam[
    [
        "key",
        "finlwt21",
    ]
]


d_parts = []
d_unmatched = 0


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
    df["newid"] = norm_id(df["NEWID"])
    df["ucc"] = norm_ucc(df["UCC"])

    df = df[
        df["ucc"].isin(d_uccs)
    ].copy()

    df["cost"] = (
        num(df["COST"])
        .fillna(0.0)
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

    d_unmatched += int(
        (m["_merge"] != "both").sum()
    )

    m["weighted"] = (
        m["cost"]
        * m["finlwt21"]
    )

    d_parts.append(
        m[
            [
                "ucc",
                "weighted",
            ]
        ]
    )


if d_unmatched:
    raise RuntimeError(
        f"Diary unmatched={d_unmatched}"
    )


d_exp = pd.concat(
    d_parts,
    ignore_index=True,
)


d_num = (
    d_exp
    .groupby("ucc")["weighted"]
    .sum()
    .to_dict()
)


# =============================================================================
# Estimate every integrated UCC
# =============================================================================

ucc_rows = []


for _, row in mapping.iterrows():

    ucc = row["ucc"]
    source = row["source"]
    factor = float(row["factor_num"])

    if source == "I":

        numerator = float(
            i_num.get(
                ucc,
                0.0,
            )
        )

        mean = (
            numerator
            / I_POP
        )

    elif source == "D":

        numerator = float(
            d_num.get(
                ucc,
                0.0,
            )
        )

        mean = (
            numerator
            / D_POP
            * 13.0
        )

    else:

        raise RuntimeError(
            f"bad source={source}"
        )

    annual = mean * factor

    if not math.isfinite(annual):
        raise RuntimeError(
            f"non-finite UCC={ucc}"
        )

    ucc_rows.append({
        "ucc": ucc,
        "source": source,
        "factor": factor,
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
        "incomplete 645-UCC benchmark"
    )


# =============================================================================
# 14 major BLS categories
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


if bench["estimate_usd"].isna().any():

    bad = bench[
        bench["estimate_usd"].isna()
    ]

    raise RuntimeError(
        "missing benchmark categories:\n"
        + bad.to_string(index=False)
    )


bench["difference_usd"] = (
    bench["estimate_usd"]
    - bench["official_mean_usd"]
)

bench["absolute_difference_usd"] = (
    bench["difference_usd"].abs()
)

bench["ape"] = (
    bench["absolute_difference_usd"]
    / bench["official_mean_usd"]
)

bench["ape_pct"] = (
    bench["ape"]
    * 100.0
)

bench["within_5pct"] = (
    bench["ape"] <= 0.05
).astype(int)


estimated_total = float(
    bench["estimate_usd"].sum()
)

official_total_check = float(
    bench["official_mean_usd"].sum()
)


if official_total_check != OFFICIAL_TOTAL:
    raise RuntimeError(
        f"official total mutation={official_total_check}"
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
    bench["within_5pct"].sum()
)


# =============================================================================
# Project component benchmark
# =============================================================================

c_cost_est = float(
    ucc_df.loc[
        ucc_df["primary_component"]
        == "C_COST",
        "estimate_usd",
    ].sum()
)


h_service_est = float(
    ucc_df.loc[
        ucc_df["primary_component"]
        == "H_SERVICE",
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
        "pumd_estimate_usd":
            c_cost_est,
        "difference_usd":
            c_cost_est
            - OFFICIAL_C_COST,
        "ape_pct":
            100 * c_cost_ape,
    },
    {
        "component": "H_SERVICE",
        "official_target_usd":
            OFFICIAL_H_SERVICE,
        "pumd_estimate_usd":
            h_service_est,
        "difference_usd":
            h_service_est
            - OFFICIAL_H_SERVICE,
        "ape_pct":
            100 * h_service_ape,
    },
])


# =============================================================================
# Frozen gates
# =============================================================================

positive_categories = bool(
    (
        bench["estimate_usd"]
        > 0
    ).all()
)


structural = all([
    len(bench) == 14,
    len(ucc_df) == 645,
    i_unmatched == 0,
    d_unmatched == 0,
    positive_categories,
])


total_gate = (
    total_ape <= 0.03
)


weighted_error_gate = (
    weighted_error_ratio <= 0.03
)


category_gate = (
    within_5 >= 10
)


component_gate = (
    c_cost_ape <= 0.05
    and h_service_ape <= 0.05
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

OUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)


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


audit = "\n".join([
    "=" * 100,
    "ECONOMIC GEOMETRY RESEARCH — E3B4B ALL-CU OFFICIAL BLS BENCHMARK",
    "=" * 100,
    "",
    "REAL_INFLATION_ESTIMATED=0",
    "",
    "===== STRUCTURE =====",
    "INTEGRATED_UCCS=645",
    f"INTERVIEW_POP_DENOMINATOR={I_POP:.10f}",
    f"DIARY_POP_DENOMINATOR={D_POP:.10f}",
    f"INTERVIEW_UNMATCHED={i_unmatched}",
    f"DIARY_UNMATCHED={d_unmatched}",
    f"MAJOR_CATEGORY_COUNT={len(bench)}",
    (
        "STRUCTURAL_BENCHMARK_GATE=PASS"
        if structural
        else
        "STRUCTURAL_BENCHMARK_GATE=FAIL"
    ),
    "",
    "===== OFFICIAL TOTAL =====",
    f"OFFICIAL_TOTAL_USD={OFFICIAL_TOTAL:.10f}",
    f"PUMD_TOTAL_USD={estimated_total:.10f}",
    f"TOTAL_APE_PCT={100 * total_ape:.10f}",
    (
        "TOTAL_APE_LE_3PCT=PASS"
        if total_gate
        else
        "TOTAL_APE_LE_3PCT=FAIL"
    ),
    "",
    "===== CATEGORY REPLICATION =====",
    f"WEIGHTED_ABSOLUTE_ERROR_RATIO_PCT={100 * weighted_error_ratio:.10f}",
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
    "===== PROJECT COMPONENTS =====",
    f"C_COST_OFFICIAL_USD={OFFICIAL_C_COST:.10f}",
    f"C_COST_PUMD_USD={c_cost_est:.10f}",
    f"C_COST_APE_PCT={100 * c_cost_ape:.10f}",
    f"H_SERVICE_OFFICIAL_USD={OFFICIAL_H_SERVICE:.10f}",
    f"H_SERVICE_PUMD_USD={h_service_est:.10f}",
    f"H_SERVICE_APE_PCT={100 * h_service_ape:.10f}",
    (
        "COMPONENT_APE_LE_5PCT=PASS"
        if component_gate
        else
        "COMPONENT_APE_LE_5PCT=FAIL"
    ),
    "",
    "===== INTERPRETATION STATE =====",
    "OBSERVED_EXPENDITURE_CHANGE_EQUALS_INFLATION=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    (
        "E3B4A_MAGNITUDES_VALIDATED=1"
        if overall
        else
        "E3B4A_MAGNITUDES_VALIDATED=0"
    ),
    (
        "COHORT_POINT_ESTIMATE_INTERPRETATION_AUTHORIZED=1"
        if overall
        else
        "COHORT_POINT_ESTIMATE_INTERPRETATION_AUTHORIZED=0"
    ),
    "",
    (
        "E3B4B_ALL_CU_OFFICIAL_BENCHMARK=PASS"
        if overall
        else
        "E3B4B_ALL_CU_OFFICIAL_BENCHMARK=FAIL"
    ),
    "",
])


AUDIT.write_text(
    audit,
    encoding="utf-8",
)

print(audit)

if not overall:
    raise SystemExit(1)
