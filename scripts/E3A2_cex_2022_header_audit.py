from __future__ import annotations

import csv
import hashlib
import io
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = ROOT / "data" / "raw" / "cex" / "2022"
META = ROOT / "data" / "metadata"

ZIP_PATH = RAW_DIR / "intrvw22.zip"

OUT_HEADERS = META / "E3A2_cex_2022_headers.tsv"
OUT_SUMMARY = META / "E3A2_cex_2022_header_audit.txt"

URL = "https://www.bls.gov/cex/pumd/data/comma/intrvw22.zip"

REQUIRED_FMLI = {
    "NEWID",
    "AGE_REF",
    "FAM_SIZE",
    "PERSLT18",
    "CUTENURE",
    "FINLWT21",
}

REQUIRED_MTBI = {
    "NEWID",
    "UCC",
}

REQUIRED_MEMI = {
    "NEWID",
    "MEMBNO",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()

    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)

    return h.hexdigest()


def acquire() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    tmp = ZIP_PATH.with_suffix(".zip.part")

    if tmp.exists():
        tmp.unlink()

    cmd = [
        "curl",
        "--http1.1",
        "-L",
        "--fail",
        "--retry", "2",
        "--connect-timeout", "30",
        "--max-time", "300",
        "-A",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
        "-e",
        "https://www.bls.gov/cex/pumd_data.htm",
        URL,
        "-o",
        str(tmp),
    ]

    print("ACQUIRE_OFFICIAL_CEX_2022_INTERVIEW_CSV=1", flush=True)

    subprocess.run(cmd, check=True)

    tmp.replace(ZIP_PATH)


def read_header(zf: zipfile.ZipFile, member: str) -> list[str]:
    # CRITICAL:
    # Read only enough bytes to obtain the first CSV record.
    # No second/data record is requested or parsed.

    with zf.open(member, "r") as raw:
        text = io.TextIOWrapper(
            raw,
            encoding="utf-8-sig",
            errors="replace",
            newline="",
        )

        reader = csv.reader(text)

        try:
            header = next(reader)
        except StopIteration:
            raise RuntimeError(f"empty CSV member: {member}")

        return [x.strip().upper() for x in header]


def family(member: str) -> str | None:
    base = Path(member).name.upper()

    if not base.endswith(".CSV"):
        return None

    if base.startswith("FMLI"):
        return "FMLI"

    if base.startswith("MTBI"):
        return "MTBI"

    if base.startswith("MEMI"):
        return "MEMI"

    return None


if not ZIP_PATH.exists():
    acquire()

if ZIP_PATH.stat().st_size < 1_000_000:
    raise RuntimeError(
        f"archive suspiciously small: {ZIP_PATH.stat().st_size} bytes"
    )

if not zipfile.is_zipfile(ZIP_PATH):
    raise RuntimeError("downloaded CEX object is not a ZIP archive")

archive_sha = sha256(ZIP_PATH)

records = []

with zipfile.ZipFile(ZIP_PATH) as zf:
    members = sorted(
        name for name in zf.namelist()
        if not name.endswith("/")
    )

    selected = [
        name for name in members
        if family(name) is not None
    ]

    for member in selected:
        fam = family(member)

        header = read_header(zf, member)
        header_set = set(header)

        if fam == "FMLI":
            required = REQUIRED_FMLI
        elif fam == "MTBI":
            required = REQUIRED_MTBI
        elif fam == "MEMI":
            required = REQUIRED_MEMI
        else:
            raise AssertionError(fam)

        missing = sorted(required - header_set)

        records.append({
            "family": fam,
            "member": member,
            "column_count": len(header),
            "required_count": len(required),
            "required_present": len(required) - len(missing),
            "missing_required": ",".join(missing) if missing else "NONE",
            "header_sha256": hashlib.sha256(
                ",".join(header).encode("utf-8")
            ).hexdigest(),
        })


family_records = {
    fam: [r for r in records if r["family"] == fam]
    for fam in ("FMLI", "MTBI", "MEMI")
}

failures = []

for fam in ("FMLI", "MTBI", "MEMI"):
    if not family_records[fam]:
        failures.append(f"NO_{fam}_CSV_FOUND")

for r in records:
    if r["missing_required"] != "NONE":
        failures.append(
            f"{r['family']}:{r['member']}:"
            f"MISSING={r['missing_required']}"
        )


META.mkdir(parents=True, exist_ok=True)

with OUT_HEADERS.open("w", newline="", encoding="utf-8") as f:
    fields = [
        "family",
        "member",
        "column_count",
        "required_count",
        "required_present",
        "missing_required",
        "header_sha256",
    ]

    w = csv.DictWriter(
        f,
        fieldnames=fields,
        delimiter="\t",
    )

    w.writeheader()
    w.writerows(records)


summary = [
    "=" * 100,
    "ECONOMIC GEOMETRY RESEARCH — E3A2 CEX 2022 EXACT HEADER AUDIT",
    "=" * 100,
    "",
    f"OFFICIAL_ARCHIVE={ZIP_PATH.relative_to(ROOT)}",
    f"ARCHIVE_SHA256={archive_sha}",
    f"ARCHIVE_BYTES={ZIP_PATH.stat().st_size}",
    "",
    "DATA_ROWS_PARSED=0",
    "ROW_COUNTS_CALCULATED=0",
    "COHORT_COUNTS_OPENED=0",
    "ECONOMIC_VALUES_OPENED=0",
    "WEIGHTED_STATISTICS_CALCULATED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "",
    "===== FILE FAMILIES =====",
    f"FMLI_HEADER_FILES={len(family_records['FMLI'])}",
    f"MTBI_HEADER_FILES={len(family_records['MTBI'])}",
    f"MEMI_HEADER_FILES={len(family_records['MEMI'])}",
    "",
    "===== REQUIRED VARIABLE GATES =====",
]

for fam in ("FMLI", "MTBI", "MEMI"):
    recs = family_records[fam]

    if not recs:
        summary.append(f"{fam}_REQUIRED_SCHEMA=FAIL")
        continue

    passed = all(
        r["missing_required"] == "NONE"
        for r in recs
    )

    summary.append(
        f"{fam}_REQUIRED_SCHEMA={'PASS' if passed else 'FAIL'}"
    )


if failures:
    summary += [
        "",
        "===== FAILURES =====",
        *failures,
        "",
        "E3A2_CEX_2022_EXACT_HEADER_AUDIT=FAIL",
        "E3A3_SAMPLE_SUPPORT_GATE_PRECOMMIT_AUTHORIZED=0",
    ]
else:
    summary += [
        "",
        "E3A2_CEX_2022_EXACT_HEADER_AUDIT=PASS",
        "CEX_2022_EXACT_HEADER_VERIFIED=1",
        "E3A3_SAMPLE_SUPPORT_GATE_PRECOMMIT_AUTHORIZED=1",
        "PSEUDOCOHORT_COUNTS_AUTHORIZED=0",
    ]


text = "\n".join(summary) + "\n"

OUT_SUMMARY.write_text(text, encoding="utf-8")

print(text)

if failures:
    sys.exit(1)
