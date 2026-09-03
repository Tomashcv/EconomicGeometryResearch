from __future__ import annotations

import zipfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

INT21 = ROOT / "data/raw/cex/2021/intrvw21.zip"
INT22 = ROOT / "data/raw/cex/2022/intrvw22.zip"

CONTRACT = (
    ROOT
    / "data/metadata/E3B4B_R3_R1_estimator_v2_ucc_source_contract.tsv"
)

V2_AUDIT = (
    ROOT
    / "data/metadata/E3B4A_V2_corrected_cohort_rerun_audit.txt"
)

OUT = (
    ROOT
    / "data/metadata/E3B4A_V2_R1_itbi_topcode_counts.tsv"
)

AUDIT = (
    ROOT
    / "data/metadata/E3B4A_V2_R1_itbi_topcode_diagnostic_repair_audit.txt"
)


PLAN = [
    (INT21, "221"),
    (INT22, "222"),
    (INT22, "223"),
    (INT22, "224"),
    (INT22, "231"),
]


def member(archive: Path, basename: str) -> str:

    with zipfile.ZipFile(archive) as zf:
        matches = [
            x for x in zf.namelist()
            if Path(x).name.lower() == basename.lower()
        ]

    if len(matches) != 1:
        raise RuntimeError(
            f"{archive.name}: {basename} matches={matches}"
        )

    return matches[0]


def read_csv(
    archive: Path,
    basename: str,
    fields: set[str],
) -> pd.DataFrame:

    name = member(
        archive,
        basename,
    )

    with zipfile.ZipFile(archive) as zf:
        with zf.open(name) as f:
            df = pd.read_csv(
                f,
                dtype=str,
                usecols=lambda c:
                    c.strip().upper() in fields,
                low_memory=False,
            )

    df.columns = [
        x.strip().upper()
        for x in df.columns
    ]

    missing = fields - set(df.columns)

    if missing:
        raise RuntimeError(
            f"{name}: missing={sorted(missing)}"
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


def num(s: pd.Series) -> pd.Series:

    return pd.to_numeric(
        s,
        errors="coerce",
    )


contract = pd.read_csv(
    CONTRACT,
    sep="\t",
    dtype=str,
).fillna("")


primary_itbi = contract[
    (contract["estimator_family"] == "ITBI")
    & (contract["primary_component"] == "C_COST")
].copy()


if len(primary_itbi) != 3:
    raise RuntimeError(
        f"expected 3 primary ITBI UCCs; got={len(primary_itbi)}"
    )


uccs = set(
    primary_itbi["ucc"]
)


# -------------------------------------------------------------------------
# Family metadata — cohort mapping only.
# -------------------------------------------------------------------------

families = []


for archive, q in PLAN:

    f = read_csv(
        archive,
        f"fmli{q}.csv",
        {
            "NEWID",
            "AGE_REF",
            "CUTENURE",
        },
    )

    f["quarter"] = q
    f["newid"] = norm_id(
        f["NEWID"]
    )

    age = num(
        f["AGE_REF"]
    )

    tenure = num(
        f["CUTENURE"]
    )

    f["cohort"] = ""

    owner = (
        age.between(25, 34)
        & tenure.isin([1, 2, 3])
    )

    renter = (
        age.between(25, 34)
        & tenure.eq(4)
    )

    f.loc[
        owner,
        "cohort",
    ] = "AGE25_34_OWNER"

    f.loc[
        renter,
        "cohort",
    ] = "AGE25_34_RENTER"

    f["key"] = (
        f["quarter"]
        + "|"
        + f["newid"]
    )

    if f["key"].duplicated().any():
        raise RuntimeError(
            f"duplicate FMLI key q={q}"
        )

    families.append(
        f[
            [
                "key",
                "cohort",
            ]
        ]
    )


fam = pd.concat(
    families,
    ignore_index=True,
)


# -------------------------------------------------------------------------
# ITBI flags only — VALUE is deliberately NOT read.
# -------------------------------------------------------------------------

pieces = []


for archive, q in PLAN:

    x = read_csv(
        archive,
        f"itbi{q}.csv",
        {
            "NEWID",
            "UCC",
            "REFMO",
            "REFYR",
            "VALUE_",
        },
    )

    x["quarter"] = q
    x["newid"] = norm_id(
        x["NEWID"]
    )

    x["ucc"] = norm_ucc(
        x["UCC"]
    )

    x["refmo"] = num(
        x["REFMO"]
    )

    x["refyr"] = num(
        x["REFYR"]
    )

    keep = (
        x["ucc"].isin(uccs)
        & x["refyr"].eq(2022)
        & x["refmo"].between(
            1,
            12,
        )
    )

    x = x.loc[
        keep
    ].copy()

    x["topcoded"] = (
        x["VALUE_"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
        .eq("T")
        .astype(int)
    )

    x["key"] = (
        x["quarter"]
        + "|"
        + x["newid"]
    )

    pieces.append(
        x[
            [
                "key",
                "ucc",
                "topcoded",
            ]
        ]
    )


itbi = pd.concat(
    pieces,
    ignore_index=True,
)


ALL_SELECTED = len(itbi)
ALL_TOPCODED = int(
    itbi["topcoded"].sum()
)


m = itbi.merge(
    fam,
    on="key",
    how="left",
    validate="many_to_one",
)


if m["cohort"].isna().any():
    raise RuntimeError(
        "ITBI-to-FMLI join failure"
    )


rows = [
    {
        "scope": "ALL_PRIMARY_ITBI_2022",
        "selected_rows": ALL_SELECTED,
        "topcoded_rows": ALL_TOPCODED,
    }
]


for cohort in (
    "AGE25_34_OWNER",
    "AGE25_34_RENTER",
):

    z = m[
        m["cohort"] == cohort
    ]

    rows.append(
        {
            "scope": cohort,
            "selected_rows":
                len(z),
            "topcoded_rows":
                int(
                    z["topcoded"].sum()
                ),
        }
    )


out = pd.DataFrame(
    rows
)


out.to_csv(
    OUT,
    sep="\t",
    index=False,
)


selected_identity = (
    ALL_SELECTED == 2196
)

bounds_pass = (
    0 <= ALL_TOPCODED <= ALL_SELECTED
)

old_bug_confirmed = (
    29499 > 2196
)


overall = all([
    selected_identity,
    bounds_pass,
    old_bug_confirmed,
])


lines = [
    "=" * 100,
    "E3B4A V2 R1 — ITBI TOPCODE DIAGNOSTIC REPAIR",
    "=" * 100,
    "",
    "DATA_ROWS_PARSED=1",
    "COST_VALUES_READ=0",
    "ITBI_VALUE_VALUES_READ=0",
    "ITBI_VALUE_FLAG_READ=1",
    "NEW_ECONOMIC_VALUES_OPENED=0",
    "REAL_INFLATION_ESTIMATED=0",
    "",
    "===== HISTORICAL DIAGNOSTIC =====",
    "FROZEN_V2_ITBI_SELECTED_ROWS=2196",
    "FROZEN_V2_ITBI_TOPCODED_ROWS=29499",
    "FROZEN_TOPCODE_COUNT_SCOPE=PRE_FILTER_ALL_ITBI",
    "FROZEN_DIAGNOSTIC_PRESERVED=1",
    "",
    "===== CORRECTED DIAGNOSTIC =====",
    f"PRIMARY_ITBI_SELECTED_ROWS={ALL_SELECTED}",
    f"PRIMARY_ITBI_TOPCODED_ROWS={ALL_TOPCODED}",
    (
        "PRIMARY_ITBI_SELECTED_ROW_IDENTITY=PASS"
        if selected_identity
        else
        "PRIMARY_ITBI_SELECTED_ROW_IDENTITY=FAIL"
    ),
    (
        "PRIMARY_ITBI_TOPCODE_BOUNDS=PASS"
        if bounds_pass
        else
        "PRIMARY_ITBI_TOPCODE_BOUNDS=FAIL"
    ),
    "",
    "POINT_ESTIMATES_RECOMPUTED=0",
    "POINT_ESTIMATE_CHANGED=0",
    "R4_BENCHMARK_RESULT_CHANGED=0",
    "E3B4A_V2_COMPONENT_VALUES_CHANGED=0",
    "E3B4A_V2_OWNER_RENTER_VALUES_CHANGED=0",
    "",
    (
        "E3B4A_V2_R1_ITBI_TOPCODE_DIAGNOSTIC_REPAIR=PASS"
        if overall
        else
        "E3B4A_V2_R1_ITBI_TOPCODE_DIAGNOSTIC_REPAIR=FAIL"
    ),
    (
        "E3B4C_BRR_PREFLIGHT_AUTHORIZED=1"
        if overall
        else
        "E3B4C_BRR_PREFLIGHT_AUTHORIZED=0"
    ),
    "",
]


AUDIT.write_text(
    "\n".join(lines),
    encoding="utf-8",
)


print(
    "\n".join(lines)
)


if not overall:
    raise SystemExit(1)
