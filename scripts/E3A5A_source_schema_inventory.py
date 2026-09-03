from __future__ import annotations

import csv
import hashlib
import subprocess
import tempfile
import zipfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

CPS = ROOT / "data" / "raw" / "cps_asec" / "2022" / "asec2022_pubuse.zip"
SCF_FULL = ROOT / "data" / "raw" / "scf" / "2022" / "scf2022s.zip"
SCF_SUM = ROOT / "data" / "raw" / "scf" / "2022" / "scfp2022s.zip"

OUT = ROOT / "data" / "metadata" / "E3A5A_source_schema_inventory.txt"
HASHES = ROOT / "data" / "metadata" / "E3A5A_raw_sha256.txt"
CPS_MEMBERS = ROOT / "data" / "metadata" / "E3A5A_cps_archive_members.tsv"
SCF_SCHEMA = ROOT / "data" / "metadata" / "E3A5A_scf_schema.tsv"


URLS = {
    CPS: (
        "https://www2.census.gov/programs-surveys/cps/"
        "datasets/2022/march/asec2022_pubuse.zip"
    ),
    SCF_FULL: (
        "https://www.federalreserve.gov/econres/files/scf2022s.zip"
    ),
    SCF_SUM: (
        "https://www.federalreserve.gov/econres/files/scfp2022s.zip"
    ),
}


SCF_FULL_REQUIRED = {
    "y1",
    "x14",
    "x508",
    "x601",
    "x701",
    "x7133",
    "x42001",
}

SCF_SUM_REQUIRED = {
    "y1",
    "yy1",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()

    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)

    return h.hexdigest()


def acquire(path: Path, url: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        if not zipfile.is_zipfile(path):
            raise RuntimeError(
                f"existing source is not ZIP: {path}"
            )

        print(f"REUSE_VALID_ZIP={path.name}", flush=True)
        return

    tmp = Path(str(path) + ".part")

    if tmp.exists():
        tmp.unlink()

    cmd = [
        "curl",
        "--http1.1",
        "-L",
        "--fail",
        "--retry", "3",
        "--connect-timeout", "30",
        "--max-time", "900",
        "-A", "Mozilla/5.0",
        url,
        "-o", str(tmp),
    ]

    print(f"ACQUIRE={path.name}", flush=True)

    subprocess.run(cmd, check=True)

    if not zipfile.is_zipfile(tmp):
        raise RuntimeError(
            f"downloaded object is not ZIP: {path.name}"
        )

    tmp.replace(path)


def archive_members(path: Path):
    records = []

    with zipfile.ZipFile(path) as zf:
        for info in sorted(
            zf.infolist(),
            key=lambda x: x.filename.lower(),
        ):
            if info.is_dir():
                continue

            p = Path(info.filename)

            records.append({
                "member": info.filename,
                "suffix": p.suffix.lower() or "NONE",
                "compressed_bytes": info.compress_size,
                "uncompressed_bytes": info.file_size,
            })

    return records


def find_single_dta(zip_path: Path, temp_root: Path) -> Path:
    with zipfile.ZipFile(zip_path) as zf:
        dta_members = [
            n
            for n in zf.namelist()
            if Path(n).suffix.lower() == ".dta"
        ]

        if len(dta_members) != 1:
            raise RuntimeError(
                f"{zip_path.name}: expected exactly one DTA; "
                f"found={dta_members}"
            )

        member = dta_members[0]

        zf.extract(member, temp_root)

        return temp_root / member


def stata_schema(path: Path) -> list[str]:
    # pandas 3.0 removed StataReader.close().
    # Own the file handle explicitly so Python closes it after
    # metadata-only variable-label inspection.
    with path.open("rb") as fh:
        reader = pd.io.stata.StataReader(
            fh,
            convert_categoricals=False,
        )
        labels = reader.variable_labels()

    return list(labels.keys())


# =============================================================================
# Acquisition
# =============================================================================

for path, url in URLS.items():
    acquire(path, url)


# =============================================================================
# Basic source integrity
# =============================================================================

for path in (CPS, SCF_FULL, SCF_SUM):
    if not zipfile.is_zipfile(path):
        raise RuntimeError(
            f"invalid ZIP after acquisition: {path}"
        )

    if path.stat().st_size <= 0:
        raise RuntimeError(
            f"empty archive: {path}"
        )


# =============================================================================
# CPS archive inventory — member metadata only
# =============================================================================

cps_records = archive_members(CPS)

if not cps_records:
    raise RuntimeError("CPS archive has no members")

CPS_MEMBERS.parent.mkdir(parents=True, exist_ok=True)

with CPS_MEMBERS.open(
    "w",
    newline="",
    encoding="utf-8",
) as f:

    fields = [
        "member",
        "suffix",
        "compressed_bytes",
        "uncompressed_bytes",
    ]

    w = csv.DictWriter(
        f,
        fieldnames=fields,
        delimiter="\t",
    )

    w.writeheader()
    w.writerows(cps_records)


# =============================================================================
# SCF archive metadata + Stata schema only
# =============================================================================

scf_schema_rows = []

with tempfile.TemporaryDirectory() as td:
    temp = Path(td)

    full_dta = find_single_dta(
        SCF_FULL,
        temp / "full",
    )

    sum_dta = find_single_dta(
        SCF_SUM,
        temp / "summary",
    )

    full_columns = stata_schema(full_dta)
    sum_columns = stata_schema(sum_dta)

    full_lower = {x.lower() for x in full_columns}
    sum_lower = {x.lower() for x in sum_columns}

    for name in sorted(SCF_FULL_REQUIRED):
        scf_schema_rows.append({
            "source": "SCF_FULL",
            "variable": name.upper(),
            "present": int(name in full_lower),
        })

    for name in sorted(SCF_SUM_REQUIRED):
        scf_schema_rows.append({
            "source": "SCF_SUMMARY",
            "variable": name.upper(),
            "present": int(name in sum_lower),
        })


with SCF_SCHEMA.open(
    "w",
    newline="",
    encoding="utf-8",
) as f:

    fields = [
        "source",
        "variable",
        "present",
    ]

    w = csv.DictWriter(
        f,
        fieldnames=fields,
        delimiter="\t",
    )

    w.writeheader()
    w.writerows(scf_schema_rows)


scf_full_pass = all(
    row["present"] == 1
    for row in scf_schema_rows
    if row["source"] == "SCF_FULL"
)

scf_sum_pass = all(
    row["present"] == 1
    for row in scf_schema_rows
    if row["source"] == "SCF_SUMMARY"
)


# =============================================================================
# Raw hashes
# =============================================================================

hash_lines = []

for path in (CPS, SCF_FULL, SCF_SUM):
    hash_lines.append(
        f"{sha256(path)}  {path.relative_to(ROOT)}"
    )

HASHES.write_text(
    "\n".join(hash_lines) + "\n",
    encoding="utf-8",
)


# =============================================================================
# CPS file-type summary
# =============================================================================

suffix_counts = {}

for row in cps_records:
    suffix = row["suffix"]
    suffix_counts[suffix] = suffix_counts.get(suffix, 0) + 1


lines = [
    "=" * 100,
    "ECONOMIC GEOMETRY RESEARCH — E3A5A SOURCE + SCHEMA INVENTORY",
    "=" * 100,
    "",
    "DATA_ROWS_PARSED=0",
    "PSEUDOCOHORT_COUNTS_OPENED=0",
    "SUPPORT_COUNTS_CALCULATED=0",
    "ECONOMIC_VALUES_OPENED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "",
    "===== SOURCE ARCHIVES =====",
    f"CPS_ARCHIVE_BYTES={CPS.stat().st_size}",
    f"SCF_FULL_ARCHIVE_BYTES={SCF_FULL.stat().st_size}",
    f"SCF_SUMMARY_ARCHIVE_BYTES={SCF_SUM.stat().st_size}",
    "",
    "===== CPS ARCHIVE =====",
    f"CPS_MEMBER_COUNT={len(cps_records)}",
]

for suffix in sorted(suffix_counts):
    lines.append(
        f"CPS_SUFFIX_{suffix.replace('.', '').upper()}="
        f"{suffix_counts[suffix]}"
    )

lines += [
    "",
    "CPS_MEMBER_NAMES:",
]

for row in cps_records:
    lines.append(
        f"  {row['member']} "
        f"SUFFIX={row['suffix']} "
        f"BYTES={row['uncompressed_bytes']}"
    )

lines += [
    "",
    "===== SCF SCHEMA =====",
    f"SCF_FULL_REQUIRED_SCHEMA={'PASS' if scf_full_pass else 'FAIL'}",
    f"SCF_SUMMARY_REQUIRED_SCHEMA={'PASS' if scf_sum_pass else 'FAIL'}",
]

for row in scf_schema_rows:
    lines.append(
        f"{row['source']}_{row['variable']}="
        f"{'PASS' if row['present'] else 'FAIL'}"
    )


overall = scf_full_pass and scf_sum_pass

lines += [
    "",
    "===== VERDICT =====",
    (
        "E3A5A_SOURCE_SCHEMA_INVENTORY=PASS"
        if overall
        else "E3A5A_SOURCE_SCHEMA_INVENTORY=FAIL"
    ),
    (
        "E3A5B_SUPPORT_PARSER_PRECOMMIT_AUTHORIZED=1"
        if overall
        else "E3A5B_SUPPORT_PARSER_PRECOMMIT_AUTHORIZED=0"
    ),
    "SUPPORT_COUNTS_AUTHORIZED=0",
    "",
]

text = "\n".join(lines)

OUT.write_text(
    text + "\n",
    encoding="utf-8",
)

print(text)

if not overall:
    raise SystemExit(1)
