from __future__ import annotations

import csv
import hashlib
import zipfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

INT21 = ROOT / "data/raw/cex/2021/intrvw21.zip"
INT22 = ROOT / "data/raw/cex/2022/intrvw22.zip"

OUT = (
    ROOT
    / "data/metadata/E3B4B_R3A_itbi_2022_exact_schema.tsv"
)

AUDIT = (
    ROOT
    / "data/metadata/E3B4B_R3A_itbi_2022_exact_schema_audit.txt"
)


EXPECTED_SHA = {
    INT21:
        "9b449829fd10ee71227a3de044e6b6d67e568cc7c02a759dda14e4b0278697f0",

    INT22:
        "c99a2f47c0084b7a88812b34c56a1a288be2798ff010b2b59dcf87e072773e17",
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


PLAN = [
    (INT21, "221"),
    (INT22, "222"),
    (INT22, "223"),
    (INT22, "224"),
    (INT22, "231"),
]


def find_member(
    archive: Path,
    basename: str,
) -> str:

    with zipfile.ZipFile(archive) as zf:

        matches = [
            x
            for x in zf.namelist()
            if Path(x).name.lower()
            == basename.lower()
        ]

    if len(matches) != 1:
        raise RuntimeError(
            f"{archive.name}: expected one "
            f"{basename}; found={matches}"
        )

    return matches[0]


rows = []


for archive, quarter in PLAN:

    member = find_member(
        archive,
        f"itbi{quarter}.csv",
    )

    with zipfile.ZipFile(archive) as zf:
        with zf.open(member) as raw:
            first = raw.readline()

    if not first:
        raise RuntimeError(
            f"empty ITBI member={member}"
        )

    header = next(
        csv.reader([
            first.decode(
                "utf-8-sig",
                errors="strict",
            ).rstrip("\r\n")
        ])
    )

    fields = [
        x.strip().upper()
        for x in header
    ]

    field_set = set(fields)

    # Exact concepts, allowing observed historical aliases.
    newid = (
        "NEWID"
        if "NEWID" in field_set
        else ""
    )

    ucc = (
        "UCC"
        if "UCC" in field_set
        else ""
    )

    month_candidates = [
        x
        for x in (
            "REFMO",
            "REF_MO",
        )
        if x in field_set
    ]

    year_candidates = [
        x
        for x in (
            "REFYR",
            "REF_YR",
        )
        if x in field_set
    ]

    value_candidates = [
        x
        for x in (
            "VALUE",
            "COST",
            "AMOUNT",
        )
        if x in field_set
    ]

    if newid != "NEWID":
        raise RuntimeError(
            f"{member}: NEWID absent"
        )

    if ucc != "UCC":
        raise RuntimeError(
            f"{member}: UCC absent"
        )

    if len(month_candidates) != 1:
        raise RuntimeError(
            f"{member}: monthly-reference aliases="
            f"{month_candidates}"
        )

    if len(year_candidates) != 1:
        raise RuntimeError(
            f"{member}: yearly-reference aliases="
            f"{year_candidates}"
        )

    if len(value_candidates) != 1:
        raise RuntimeError(
            f"{member}: point-value aliases="
            f"{value_candidates}"
        )

    rows.append({
        "archive": archive.name,
        "quarter": quarter,
        "member": member,
        "column_count": len(fields),
        "newid_field": newid,
        "ucc_field": ucc,
        "reference_month_field":
            month_candidates[0],
        "reference_year_field":
            year_candidates[0],
        "point_value_field":
            value_candidates[0],
        "all_fields":
            ",".join(fields),
        "header_sha256":
            hashlib.sha256(
                "\t".join(fields).encode(
                    "utf-8"
                )
            ).hexdigest(),
    })


df = pd.DataFrame(rows)

df.to_csv(
    OUT,
    sep="\t",
    index=False,
)


month_fields = sorted(
    df["reference_month_field"]
    .unique()
)

year_fields = sorted(
    df["reference_year_field"]
    .unique()
)

value_fields = sorted(
    df["point_value_field"]
    .unique()
)


schema_stable = (
    len(df) == 5
    and len(month_fields) == 1
    and len(year_fields) == 1
    and len(value_fields) == 1
)


# We do not force historical expectations into PASS;
# report actual local-byte schema.
actual_month = (
    month_fields[0]
    if len(month_fields) == 1
    else "MIXED"
)

actual_year = (
    year_fields[0]
    if len(year_fields) == 1
    else "MIXED"
)

actual_value = (
    value_fields[0]
    if len(value_fields) == 1
    else "MIXED"
)


lines = [
    "=" * 100,
    "E3B4B R3A — EXACT 2022 ITBI SCHEMA FORENSIC",
    "=" * 100,
    "",
    "DATA_ROWS_PARSED=0",
    "COST_VALUES_READ=0",
    "ITBI_VALUE_VALUES_READ=0",
    "NEW_ECONOMIC_VALUES_OPENED=0",
    "REAL_INFLATION_ESTIMATED=0",
    "",
    "===== ITBI FILES =====",
    f"ITBI_HEADER_ROWS={len(df)}",
    f"ITBI_REFERENCE_MONTH_FIELD={actual_month}",
    f"ITBI_REFERENCE_YEAR_FIELD={actual_year}",
    f"ITBI_POINT_VALUE_FIELD={actual_value}",
    "",
    "MTBI_SCHEMA_REUSE_FOR_ITBI=PROHIBITED",
    "ITII_POINT_ESTIMATE_APPEND=PROHIBITED",
    "",
    (
        "ITBI_2022_SCHEMA_STABLE=PASS"
        if schema_stable
        else
        "ITBI_2022_SCHEMA_STABLE=FAIL"
    ),
    (
        "E3B4B_R3A_ITBI_EXACT_SCHEMA=PASS"
        if schema_stable
        else
        "E3B4B_R3A_ITBI_EXACT_SCHEMA=FAIL"
    ),
    (
        "E3B4B_R3_REPAIR_AUTHORIZED=1"
        if schema_stable
        else
        "E3B4B_R3_REPAIR_AUTHORIZED=0"
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

if not schema_stable:
    raise SystemExit(1)
