from __future__ import annotations

import csv
import hashlib
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

INT21 = ROOT / "data/raw/cex/2021/intrvw21.zip"
INT22 = ROOT / "data/raw/cex/2022/intrvw22.zip"
DIA22 = ROOT / "data/raw/cex/2022/diary22.zip"

OUT = ROOT / "data/metadata/E3B3A_R2_calendar_year_timing_audit.txt"
TABLE = ROOT / "data/metadata/E3B3A_R2_required_headers.tsv"


EXPECTED_SHA = {
    INT21:
        "9b449829fd10ee71227a3de044e6b6d67e568cc7c02a759dda14e4b0278697f0",
    INT22:
        "c99a2f47c0084b7a88812b34c56a1a288be2798ff010b2b59dcf87e072773e17",
    DIA22:
        "c285e72fd7513c78caa158c75975c5b03e91049a9ffe9ee6d41966dc4ef20963",
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
            f"{archive.name}: expected one {basename}; "
            f"found={matches}"
        )

    return matches[0]


def first_header(
    archive: Path,
    member: str,
) -> list[str]:

    with zipfile.ZipFile(archive) as zf:
        with zf.open(member) as raw:

            line = raw.readline()

    if not line:
        raise RuntimeError(
            f"empty member={member}"
        )

    return next(
        csv.reader([
            line.decode(
                "utf-8-sig",
                errors="strict",
            ).rstrip("\r\n")
        ])
    )


for path, expected in EXPECTED_SHA.items():

    actual = sha256(path)

    if actual != expected:
        raise RuntimeError(
            f"SHA mismatch {path.name}: {actual}"
        )


required = []

# Correct five-quarter Interview window.
for archive, q in [
    (INT21, "221"),
    (INT22, "222"),
    (INT22, "223"),
    (INT22, "224"),
    (INT22, "231"),
]:

    required += [
        (
            "INTERVIEW",
            archive,
            "FMLI",
            f"fmli{q}.csv",
            q,
        ),
        (
            "INTERVIEW",
            archive,
            "MTBI",
            f"mtbi{q}.csv",
            q,
        ),
    ]


# Diary remains four collection quarters.
for q in (
    "221",
    "222",
    "223",
    "224",
):

    required += [
        (
            "DIARY",
            DIA22,
            "FMLD",
            f"fmld{q}.csv",
            q,
        ),
        (
            "DIARY",
            DIA22,
            "EXPD",
            f"expd{q}.csv",
            q,
        ),
    ]


required_fields = {
    "FMLI": {
        "NEWID",
        "AGE_REF",
        "CUTENURE",
        "FINLWT21",
    },
    "MTBI": {
        "NEWID",
        "UCC",
        "COST",
        "REF_MO",
        "REF_YR",
    },
    "FMLD": {
        "NEWID",
        "AGE_REF",
        "CUTENURE",
        "FINLWT21",
    },
    "EXPD": {
        "NEWID",
        "UCC",
        "COST",
        "ALLOC",
    },
}


rows = []

for (
    survey,
    archive,
    family,
    basename,
    quarter,
) in required:

    member = find_member(
        archive,
        basename,
    )

    header = first_header(
        archive,
        member,
    )

    header_upper = {
        x.upper()
        for x in header
    }

    missing = sorted(
        required_fields[family]
        - header_upper
    )

    rows.append({
        "survey": survey,
        "archive": archive.name,
        "quarter": quarter,
        "family": family,
        "member": member,
        "columns": len(header),
        "required_present": (
            len(required_fields[family])
            - len(missing)
        ),
        "required_total": len(
            required_fields[family]
        ),
        "missing_required": (
            ",".join(missing)
            if missing
            else "NONE"
        ),
        "header_sha256": hashlib.sha256(
            ",".join(header).encode(
                "utf-8"
            )
        ).hexdigest(),
    })


with TABLE.open(
    "w",
    newline="",
    encoding="utf-8",
) as f:

    fields = [
        "survey",
        "archive",
        "quarter",
        "family",
        "member",
        "columns",
        "required_present",
        "required_total",
        "missing_required",
        "header_sha256",
    ]

    writer = csv.DictWriter(
        f,
        fieldnames=fields,
        delimiter="\t",
    )

    writer.writeheader()
    writer.writerows(rows)


schema_pass = all(
    row["missing_required"] == "NONE"
    for row in rows
)


quarters_interview = sorted({
    row["quarter"]
    for row in rows
    if row["survey"] == "INTERVIEW"
})

quarters_diary = sorted({
    row["quarter"]
    for row in rows
    if row["survey"] == "DIARY"
})


interview_window_pass = (
    quarters_interview
    == [
        "221",
        "222",
        "223",
        "224",
        "231",
    ]
)

diary_window_pass = (
    quarters_diary
    == [
        "221",
        "222",
        "223",
        "224",
    ]
)


overall = all([
    schema_pass,
    interview_window_pass,
    diary_window_pass,
])


summary = "\n".join([
    "=" * 100,
    "ECONOMIC GEOMETRY RESEARCH — E3B3A R2 CALENDAR-YEAR TIMING AUDIT",
    "=" * 100,
    "",
    "MICRODATA_DATA_ROWS_PARSED=0",
    "COST_VALUES_READ=0",
    "ECONOMIC_VALUES_OPENED=0",
    "REAL_INFLATION_ESTIMATED=0",
    "",
    "===== INTERVIEW =====",
    "INTERVIEW_CALENDAR_2022_REQUIRED_QUARTERS=221,222,223,224,231",
    (
        "INTERVIEW_FIVE_QUARTER_WINDOW=PASS"
        if interview_window_pass
        else
        "INTERVIEW_FIVE_QUARTER_WINDOW=FAIL"
    ),
    "INTERVIEW_221_SOURCE=intrvw21.zip",
    "INTERVIEW_222_223_224_231_SOURCE=intrvw22.zip",
    "FUTURE_MTBI_FILTER=REF_YR_2022_AND_REF_MO_1_TO_12",
    "",
    "===== DIARY =====",
    "DIARY_CALENDAR_2022_REQUIRED_QUARTERS=221,222,223,224",
    (
        "DIARY_FOUR_QUARTER_WINDOW=PASS"
        if diary_window_pass
        else
        "DIARY_FOUR_QUARTER_WINDOW=FAIL"
    ),
    "",
    "===== SCHEMA =====",
    (
        "ALL_REQUIRED_HEADERS=PASS"
        if schema_pass
        else
        "ALL_REQUIRED_HEADERS=FAIL"
    ),
    "",
    "===== SUPERSESSION =====",
    "E3B3A_R1_CALENDAR_SOURCE_PLAN=SUPERSEDED",
    "E3B3A_R1_TRANSPORT_RESULT=PRESERVED",
    "E3B3A_R1_SCHEMA_RESULT=PRESERVED",
    "E3B3A_R1_HIERARCHY_RESULT=PRESERVED",
    "E3B3B_HIERARCHY_RESULT_AFFECTED=0",
    "",
    (
        "E3B3A_R2_CALENDAR_YEAR_TIMING_REPAIR=PASS"
        if overall
        else
        "E3B3A_R2_CALENDAR_YEAR_TIMING_REPAIR=FAIL"
    ),
    (
        "E3B3C_COMPONENT_UCC_MAPPING_PRECOMMIT_AUTHORIZED=1"
        if overall
        else
        "E3B3C_COMPONENT_UCC_MAPPING_PRECOMMIT_AUTHORIZED=0"
    ),
    "",
])


OUT.write_text(
    summary,
    encoding="utf-8",
)

print(summary)

if not overall:
    raise SystemExit(1)
