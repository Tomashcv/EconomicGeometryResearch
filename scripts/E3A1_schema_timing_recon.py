from __future__ import annotations

import csv
import hashlib
import subprocess
import sys
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]

META = ROOT / "data" / "metadata"
DOC = META / "E3A1_docs"

MANIFEST = META / "E3A1_official_sources.tsv"
OUT = META / "E3A1_schema_timing_recon.txt"
HASHES = META / "E3A1_document_sha256.txt"

DOC.mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def acquire(url: str, dest: Path) -> None:
    subprocess.run(
        [
            "curl",
            "-L",
            "--fail",
            "--retry",
            "3",
            "--connect-timeout",
            "30",
            "-A",
            "Mozilla/5.0",
            url,
            "-o",
            str(dest),
        ],
        check=True,
    )


with MANIFEST.open(encoding="utf-8") as f:
    sources = list(csv.DictReader(f, delimiter="\t"))

name_map = {
    "PUMD_dictionary": "ce_pumd_dictionary.xlsx",
    "2022_data_dictionary": "cps_asec_2022_dictionary.pdf",
    "2022_house_layout": "cps_asec_2022_house_layout.txt",
    "2022_family_layout": "cps_asec_2022_family_layout.txt",
    "2022_person_layout": "cps_asec_2022_person_layout.txt",
    "bulletin_macro": "scf_bulletin_macro.txt",
    "2022_codebook": "scf_2022_codebook.txt",
}

paths = {}

for row in sources:
    resource = row["resource"]
    dest = DOC / name_map[resource]

    print(f"ACQUIRE={resource}", flush=True)
    acquire(row["url"], dest)

    if dest.stat().st_size == 0:
        raise RuntimeError(f"empty acquisition: {dest}")

    paths[resource] = dest


# =============================================================================
# CEX XLSX textual extraction — schema only
# =============================================================================

def xlsx_text(path: Path) -> str:
    pieces = []

    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if not name.startswith("xl/"):
                continue
            if not name.endswith(".xml"):
                continue

            try:
                root = ET.fromstring(z.read(name))
            except ET.ParseError:
                continue

            for elem in root.iter():
                if elem.text:
                    pieces.append(elem.text)

    return "\n".join(pieces).upper()


cex = xlsx_text(paths["PUMD_dictionary"])

cex_required = [
    "NEWID",
    "AGE_REF",
    "FAM_SIZE",
    "PERSLT18",
    "CUTENURE",
    "FINLWT21",
]

cex_status = {}

for token in cex_required:
    cex_status[token] = token in cex


# =============================================================================
# CPS schemas
# =============================================================================

house = paths["2022_house_layout"].read_text(
    encoding="utf-8", errors="replace"
).upper()

family = paths["2022_family_layout"].read_text(
    encoding="utf-8", errors="replace"
).upper()

person = paths["2022_person_layout"].read_text(
    encoding="utf-8", errors="replace"
).upper()

# Some of the fixed-layout helper files are compact, therefore also retain
# dictionary PDF as archived evidence. Variable verification below relies on
# official text layouts where available.

cps_house_required = [
    "H_TENURE",
    "H_NUMPER",
]

cps_person_required = [
    "A_AGE",
    "A_MARITL",
    "A_FAMNUM",
    "A_WKSTAT",
    "MARSUPWT",
]

cps_house_status = {x: x in house for x in cps_house_required}
cps_person_status = {x: x in person for x in cps_person_required}


# =============================================================================
# SCF harmonized macro
# =============================================================================

scf = paths["bulletin_macro"].read_text(
    encoding="utf-8", errors="replace"
).upper()

scf_required = [
    "AGE",
    "AGECL",
    "KIDS",
    "HOUSECL",
    "INCOME",
    "FIN",
    "LIQ",
    "STOCKS",
    "RETQLIQ",
    "HOUSES",
    "ASSET",
    "DEBT",
    "MRTHEL",
    "HOMEEQ",
    "NETWORTH",
    "DEBT2INC",
    "PIRTOTAL",
    "PIRMORT",
    "WGT",
]

scf_status = {x: x in scf for x in scf_required}


# =============================================================================
# Hard schema gates
# =============================================================================

failures = []

for group, statuses in [
    ("CEX", cex_status),
    ("CPS_HOUSE", cps_house_status),
    ("CPS_PERSON", cps_person_status),
    ("SCF", scf_status),
]:
    for variable, passed in statuses.items():
        if not passed:
            failures.append(f"{group}:{variable}")


# =============================================================================
# Hash manifest
# =============================================================================

hash_lines = []

for resource, path in sorted(paths.items()):
    digest = sha256(path)
    hash_lines.append(f"{digest}  {path.relative_to(ROOT)}")

HASHES.write_text("\n".join(hash_lines) + "\n", encoding="utf-8")


def lines_for(prefix: str, statuses: dict[str, bool]) -> list[str]:
    return [
        f"{prefix}_{name}={'PASS' if ok else 'FAIL'}"
        for name, ok in statuses.items()
    ]


summary = [
    "=" * 100,
    "ECONOMIC GEOMETRY RESEARCH — E3A1 SCHEMA/TIMING RECON",
    "=" * 100,
    "",
    "ECONOMIC_VALUES_OPENED=0",
    "COHORT_COUNTS_OPENED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "",
    "===== CEX DOCUMENTED VARIABLES =====",
    *lines_for("CEX", cex_status),
    "",
    "===== CPS HOUSEHOLD VARIABLES =====",
    *lines_for("CPS", cps_house_status),
    "",
    "===== CPS PERSON VARIABLES =====",
    *lines_for("CPS", cps_person_status),
    "",
    "===== SCF HARMONIZED VARIABLES =====",
    *lines_for("SCF", scf_status),
    "",
    "===== TEMPORAL CONTRACT =====",
    "CEX_RELEASE_YEAR_EQUALS_CALENDAR_YEAR=0",
    "CEX_2022_PACKAGE_EXPECTED_WINDOW=2022Q2_TO_2023Q1",
    "CPS_ASEC_2022_INCOME_REFERENCE_YEAR=2021",
    "SCF_2022_INCOME_REFERENCE_PERIOD=PREVIOUS_CALENDAR_YEAR",
    "FLOW_STOCK_DISTINCTION_REQUIRED=1",
    "",
    "===== NEXT GATE =====",
    "PSEUDOCOHORT_SUPPORT_GATE_FROZEN=0",
    "PSEUDOCOHORT_COUNTS_AUTHORIZED=0",
]

if failures:
    summary += [
        "",
        "===== FAILURES =====",
        *failures,
        "",
        "E3A1_SCHEMA_TIMING_RECON=FAIL",
    ]
else:
    summary += [
        "",
        "E3A1_SCHEMA_TIMING_RECON=PASS",
        "E3A2_SUPPORT_GATE_PRECOMMIT_AUTHORIZED=1",
    ]


text = "\n".join(summary) + "\n"

OUT.write_text(text, encoding="utf-8")
print(text)

if failures:
    sys.exit(1)
