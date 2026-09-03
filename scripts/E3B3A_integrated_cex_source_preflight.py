from __future__ import annotations

import csv
import hashlib
import io
import re
import shutil
import subprocess
import zipfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOME = Path.home()

INT21 = ROOT / "data/raw/cex/2021/intrvw21.zip"
INT22 = ROOT / "data/raw/cex/2022/intrvw22.zip"
DIA22 = ROOT / "data/raw/cex/2022/diary22.zip"
STUBS = ROOT / "data/raw/cex/stubs/stubs.zip"

OUT = ROOT / "data/metadata/E3B3A_integrated_cex_source_preflight.txt"
HASHES = ROOT / "data/metadata/E3B3A_raw_sha256.txt"
HEADERS = ROOT / "data/metadata/E3B3A_cex_headers.tsv"
HIERARCHY = ROOT / "data/metadata/E3B3A_integrated_2022_hierarchy.tsv"

EXPECTED_INT22_SHA = (
    "c99a2f47c0084b7a88812b34c56a1a288be2798ff010b2b59dcf87e072773e17"
)

URLS = {
    INT21: "https://www.bls.gov/cex/pumd/data/comma/intrvw21.zip",
    DIA22: "https://www.bls.gov/cex/pumd/data/comma/diary22.zip",
    STUBS: "https://www.bls.gov/cex/pumd/stubs.zip",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()

    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)

    return h.hexdigest()


def valid_zip(path: Path) -> bool:
    return (
        path.exists()
        and path.stat().st_size > 0
        and zipfile.is_zipfile(path)
    )


def acquire(path: Path, url: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)

    if valid_zip(path):
        print(f"REUSE_VALID_ZIP={path.name}", flush=True)
        return True

    manual = HOME / "Downloads" / path.name

    if valid_zip(manual):
        shutil.copy2(manual, path)

        print(
            f"PROMOTE_BROWSER_DOWNLOAD={manual} -> {path}",
            flush=True,
        )

        return True

    tmp = Path(str(path) + ".part")

    if tmp.exists():
        tmp.unlink()

    print(f"AUTO_ACQUIRE_ATTEMPT={path.name}", flush=True)

    cmd = [
        "curl",
        "--http1.1",
        "-L",
        "--fail",
        "--retry", "2",
        "--connect-timeout", "30",
        "--max-time", "600",
        "-A",
        (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/150.0.0.0 Safari/537.36"
        ),
        "-e",
        "https://www.bls.gov/cex/pumd_data.htm",
        url,
        "-o",
        str(tmp),
    ]

    rc = subprocess.run(cmd).returncode

    if rc == 0 and valid_zip(tmp):
        tmp.replace(path)

        print(
            f"AUTO_ACQUIRE=PASS FILE={path.name}",
            flush=True,
        )

        return True

    if tmp.exists():
        tmp.unlink()

    print(
        f"AUTO_ACQUIRE=FAIL FILE={path.name}",
        flush=True,
    )

    return False


def first_header(
    zf: zipfile.ZipFile,
    member: str,
) -> list[str]:

    with zf.open(member, "r") as raw:
        line = raw.readline()

    if not line:
        raise RuntimeError(
            f"empty CSV member: {member}"
        )

    text = line.decode(
        "utf-8-sig",
        errors="strict",
    ).rstrip("\r\n")

    return next(csv.reader([text]))


def basename_member(
    zf: zipfile.ZipFile,
    expected_basename: str,
) -> str:

    matches = [
        name
        for name in zf.namelist()
        if Path(name).name.lower()
        == expected_basename.lower()
    ]

    if len(matches) != 1:
        raise RuntimeError(
            f"expected exactly one {expected_basename}; "
            f"found={matches}"
        )

    return matches[0]


# =============================================================================
# Frozen existing source
# =============================================================================

if not valid_zip(INT22):
    raise RuntimeError(
        "canonical 2022 Interview archive missing"
    )

if sha256(INT22) != EXPECTED_INT22_SHA:
    raise RuntimeError(
        "canonical intrvw22.zip SHA mismatch"
    )


# =============================================================================
# Acquire missing official sources
# =============================================================================

transport = {}

for path, url in URLS.items():
    transport[path] = acquire(path, url)


missing = [
    path
    for path, ok in transport.items()
    if not ok
]

if missing:

    print()
    print("=" * 100)
    print("E3B3A TRANSPORT INCOMPLETE")
    print("=" * 100)

    for path in missing:
        print(
            f"MANUAL_DOWNLOAD_REQUIRED={URLS[path]}"
        )
        print(
            f"EXPECTED_BROWSER_FILENAME={path.name}"
        )

    print()
    print(
        "Download the missing official ZIP(s) with the browser "
        "to ~/Downloads and rerun this SAME frozen script."
    )

    print("MICRODATA_DATA_ROWS_PARSED=0")
    print("ECONOMIC_VALUES_OPENED=0")
    print("E3B3A_TRANSPORT_READY=0")

    raise SystemExit(20)


# =============================================================================
# Calendar-year 2022 exact member plan
# =============================================================================

required_members = []

with zipfile.ZipFile(INT21) as zf:

    required_members += [
        (
            "INTERVIEW_2021_RELEASE",
            "FMLI",
            basename_member(zf, "fmli221.csv"),
            "2022Q1",
        ),
        (
            "INTERVIEW_2021_RELEASE",
            "MTBI",
            basename_member(zf, "mtbi221.csv"),
            "2022Q1",
        ),
    ]


with zipfile.ZipFile(INT22) as zf:

    for q in ("222", "223", "224"):

        required_members += [
            (
                "INTERVIEW_2022_RELEASE",
                "FMLI",
                basename_member(
                    zf,
                    f"fmli{q}.csv",
                ),
                f"2022Q{int(q[-1])}",
            ),
            (
                "INTERVIEW_2022_RELEASE",
                "MTBI",
                basename_member(
                    zf,
                    f"mtbi{q}.csv",
                ),
                f"2022Q{int(q[-1])}",
            ),
        ]


with zipfile.ZipFile(DIA22) as zf:

    for q in ("221", "222", "223", "224"):

        required_members += [
            (
                "DIARY_2022",
                "FMLD",
                basename_member(
                    zf,
                    f"fmld{q}.csv",
                ),
                f"2022Q{int(q[-1])}",
            ),
            (
                "DIARY_2022",
                "EXPD",
                basename_member(
                    zf,
                    f"expd{q}.csv",
                ),
                f"2022Q{int(q[-1])}",
            ),
        ]


# =============================================================================
# Header-only schema audit
# =============================================================================

required_by_family = {
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


archive_for_source = {
    "INTERVIEW_2021_RELEASE": INT21,
    "INTERVIEW_2022_RELEASE": INT22,
    "DIARY_2022": DIA22,
}


header_rows = []


for source, family, member, quarter in required_members:

    archive = archive_for_source[source]

    with zipfile.ZipFile(archive) as zf:

        header = first_header(
            zf,
            member,
        )

    upper = {
        x.upper()
        for x in header
    }

    missing_fields = sorted(
        required_by_family[family]
        - upper
    )

    header_rows.append({
        "source": source,
        "quarter": quarter,
        "family": family,
        "member": member,
        "column_count": len(header),
        "required_present": (
            len(required_by_family[family])
            - len(missing_fields)
        ),
        "required_total": len(
            required_by_family[family]
        ),
        "missing_required": (
            ",".join(missing_fields)
            if missing_fields
            else "NONE"
        ),
        "header_sha256": hashlib.sha256(
            ",".join(header).encode("utf-8")
        ).hexdigest(),
    })


with HEADERS.open(
    "w",
    newline="",
    encoding="utf-8",
) as f:

    fields = [
        "source",
        "quarter",
        "family",
        "member",
        "column_count",
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
    writer.writerows(header_rows)


schema_pass = all(
    row["missing_required"] == "NONE"
    for row in header_rows
)


# =============================================================================
# Integrated hierarchy metadata
# =============================================================================

with zipfile.ZipFile(STUBS) as zf:

    matches = [
        name
        for name in zf.namelist()
        if (
            "integ" in Path(name).name.lower()
            and "2022" in Path(name).name.lower()
            and Path(name).suffix.lower() == ".txt"
        )
    ]

    if len(matches) != 1:
        raise RuntimeError(
            "expected exactly one 2022 integrated hierarchy "
            f"member; found={matches}"
        )

    hierarchy_member = matches[0]

    raw = zf.read(
        hierarchy_member
    ).decode(
        "latin-1",
        errors="strict",
    )


hierarchy_rows = []

for lineno, line in enumerate(
    raw.splitlines(),
    start=1,
):

    if not line:
        continue

    line_type = line[0:1].strip()
    level = line[3:4].strip()
    title = line[6:69].strip()
    ucc = line[69:75].strip()
    # E3B3A R1:
    # CE-HG-Integ-2022.txt uses the year-specific legacy
    # fixed-width layout:
    #   source  position 80
    #   factor  position 83
    #   section position 86
    source = line[79:80].strip()
    factor = line[82:83].strip()
    section = line[85:].strip()

    if not re.fullmatch(
        r"\d{6}",
        ucc,
    ):
        continue

    hierarchy_rows.append({
        "line": lineno,
        "line_type": line_type,
        "level": level,
        "title": title,
        "ucc": ucc,
        "source": source,
        "factor": factor,
        "section": section,
    })


if not hierarchy_rows:
    raise RuntimeError(
        "no six-digit UCC rows parsed from "
        "CE-HG-Integ-2022"
    )


with HIERARCHY.open(
    "w",
    newline="",
    encoding="utf-8",
) as f:

    fields = [
        "line",
        "line_type",
        "level",
        "title",
        "ucc",
        "source",
        "factor",
        "section",
    ]

    writer = csv.DictWriter(
        f,
        fieldnames=fields,
        delimiter="\t",
    )

    writer.writeheader()
    writer.writerows(hierarchy_rows)


source_counts = Counter(
    row["source"]
    for row in hierarchy_rows
)

integrated_i = source_counts.get(
    "I",
    0,
)

integrated_d = source_counts.get(
    "D",
    0,
)


hierarchy_pass = (
    integrated_i > 0
    and integrated_d > 0
)


# =============================================================================
# Raw hashes
# =============================================================================

hash_lines = []

for path in (
    INT21,
    INT22,
    DIA22,
    STUBS,
):

    hash_lines.append(
        f"{sha256(path)}  "
        f"{path.relative_to(ROOT)}"
    )

HASHES.write_text(
    "\n".join(hash_lines) + "\n",
    encoding="utf-8",
)


# =============================================================================
# Final verdict
# =============================================================================

overall = (
    schema_pass
    and hierarchy_pass
)


summary = "\n".join([
    "=" * 100,
    "ECONOMIC GEOMETRY RESEARCH — E3B3A INTEGRATED CEX SOURCE PREFLIGHT",
    "=" * 100,
    "",
    "MICRODATA_DATA_ROWS_PARSED=0",
    "ECONOMIC_VALUES_OPENED=0",
    "EXPENDITURE_VALUES_OPENED=0",
    "REAL_INFLATION_ESTIMATED=0",
    "",
    "===== TRANSPORT =====",
    "E3B3A_TRANSPORT_READY=1",
    "",
    "===== CALENDAR-YEAR 2022 =====",
    "INTERVIEW_2022Q1_FROM_RELEASE_2021=PASS",
    "INTERVIEW_2022Q2_Q3_Q4_FROM_RELEASE_2022=PASS",
    "DIARY_2022Q1_Q2_Q3_Q4=PASS",
    "CALENDAR_YEAR_2022_SOURCE_PLAN=PASS",
    "",
    "===== HEADERS =====",
    (
        "INTERVIEW_DIARY_REQUIRED_SCHEMA=PASS"
        if schema_pass
        else
        "INTERVIEW_DIARY_REQUIRED_SCHEMA=FAIL"
    ),
    "",
    "===== INTEGRATED HIERARCHY =====",
    f"INTEGRATED_HIERARCHY_MEMBER={hierarchy_member}",
    f"INTEGRATED_UCC_ROWS={len(hierarchy_rows)}",
    f"INTEGRATED_INTERVIEW_UCC_ROWS={integrated_i}",
    f"INTEGRATED_DIARY_UCC_ROWS={integrated_d}",
    (
        "INTEGRATED_HIERARCHY_SOURCE_COVERAGE=PASS"
        if hierarchy_pass
        else
        "INTEGRATED_HIERARCHY_SOURCE_COVERAGE=FAIL"
    ),
    "",
    "===== DESIGN STATE =====",
    "RECORD_LEVEL_INTERVIEW_DIARY_JOIN=PROHIBITED",
    "C_COST_UCC_MAP_FROZEN=0",
    "H_SERVICE_UCC_MAP_FROZEN=0",
    "INTEGRATION_ARITHMETIC_FROZEN=0",
    "HOUSEHOLD_ECONOMIC_VALUES_AUTHORIZED=0",
    "",
    (
        "E3B3A_INTEGRATED_CEX_SOURCE_PREFLIGHT=PASS"
        if overall
        else
        "E3B3A_INTEGRATED_CEX_SOURCE_PREFLIGHT=FAIL"
    ),
    (
        "E3B3B_UCC_CLASSIFICATION_AND_ESTIMAND_PRECOMMIT_AUTHORIZED=1"
        if overall
        else
        "E3B3B_UCC_CLASSIFICATION_AND_ESTIMAND_PRECOMMIT_AUTHORIZED=0"
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
