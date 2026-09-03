from __future__ import annotations

import csv
import hashlib
import re
import shutil
import subprocess
import zipfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOME = Path.home()

ARCHIVE = ROOT / "data/raw/cex/sample_code/r-ucc.zip"

URL = "https://www.bls.gov/cex/pumd/r-ucc.zip"

OUT = ROOT / "data/metadata/E3B3C3_official_bls_sample_code_audit.txt"
INVENTORY = ROOT / "data/metadata/E3B3C3_sample_code_inventory.tsv"
CONTEXT = ROOT / "data/metadata/E3B3C3_semantic_context.tsv"
RAW_SHA = ROOT / "data/metadata/E3B3C3_raw_sha256.txt"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()

    with path.open("rb") as f:
        for block in iter(
            lambda: f.read(1024 * 1024),
            b"",
        ):
            h.update(block)

    return h.hexdigest()


def valid_zip(path: Path) -> bool:
    return (
        path.exists()
        and path.stat().st_size > 0
        and zipfile.is_zipfile(path)
    )


def acquire() -> bool:

    ARCHIVE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if valid_zip(ARCHIVE):
        print(
            "REUSE_OFFICIAL_SAMPLE_CODE=1",
            flush=True,
        )
        return True

    manual = HOME / "Downloads/r-ucc.zip"

    if valid_zip(manual):

        shutil.copy2(
            manual,
            ARCHIVE,
        )

        print(
            f"PROMOTE_BROWSER_DOWNLOAD={manual} -> {ARCHIVE}",
            flush=True,
        )

        return True

    tmp = Path(
        str(ARCHIVE) + ".part"
    )

    if tmp.exists():
        tmp.unlink()

    print(
        "AUTO_ACQUIRE_ATTEMPT=r-ucc.zip",
        flush=True,
    )

    rc = subprocess.run([
        "curl",
        "--http1.1",
        "-L",
        "--fail",
        "--retry", "2",
        "--connect-timeout", "30",
        "--max-time", "300",
        "-A",
        (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/150.0.0.0 Safari/537.36"
        ),
        "-e",
        "https://www.bls.gov/cex/pumd_doc.htm",
        URL,
        "-o",
        str(tmp),
    ]).returncode

    if rc == 0 and valid_zip(tmp):

        tmp.replace(
            ARCHIVE
        )

        print(
            "AUTO_ACQUIRE=PASS",
            flush=True,
        )

        return True

    if tmp.exists():
        tmp.unlink()

    return False


if not acquire():

    print()
    print("=" * 100)
    print("E3B3C3 BLS TRANSPORT INCOMPLETE")
    print("=" * 100)
    print(f"MANUAL_DOWNLOAD_REQUIRED={URL}")
    print("EXPECTED_BROWSER_FILENAME=r-ucc.zip")
    print()
    print(
        "Download the official BLS R sample-code ZIP "
        "to ~/Downloads and rerun this SAME frozen script."
    )
    print("COST_VALUES_READ=0")
    print("ECONOMIC_VALUES_OPENED=0")
    print("E3B3C3_TRANSPORT_READY=0")

    raise SystemExit(20)


# =============================================================================
# Archive inventory
# =============================================================================

inventory_rows = []
text_members: list[tuple[str, str]] = []

TEXT_EXTENSIONS = {
    ".r",
    ".txt",
    ".md",
    ".csv",
    ".do",
    ".sas",
}


with zipfile.ZipFile(
    ARCHIVE
) as zf:

    for name in sorted(
        zf.namelist()
    ):

        if name.endswith("/"):
            continue

        data = zf.read(
            name
        )

        suffix = Path(
            name
        ).suffix.lower()

        is_text_candidate = (
            suffix in TEXT_EXTENSIONS
        )

        text = ""

        if is_text_candidate:

            decoded = None

            for encoding in (
                "utf-8-sig",
                "utf-8",
                "cp1252",
                "latin-1",
            ):

                try:
                    decoded = data.decode(
                        encoding
                    )
                    break

                except UnicodeDecodeError:
                    continue

            if decoded is None:
                raise RuntimeError(
                    f"could not decode text member={name}"
                )

            text = decoded

            text_members.append(
                (name, text)
            )

        inventory_rows.append({
            "member": name,
            "bytes": len(data),
            "sha256": sha256_bytes(
                data
            ),
            "suffix": suffix,
            "text_candidate": int(
                is_text_candidate
            ),
            "line_count": (
                len(text.splitlines())
                if is_text_candidate
                else 0
            ),
        })


if not text_members:
    raise RuntimeError(
        "official archive contains no readable code/text members"
    )


with INVENTORY.open(
    "w",
    newline="",
    encoding="utf-8",
) as f:

    fields = [
        "member",
        "bytes",
        "sha256",
        "suffix",
        "text_candidate",
        "line_count",
    ]

    writer = csv.DictWriter(
        f,
        fieldnames=fields,
        delimiter="\t",
    )

    writer.writeheader()
    writer.writerows(
        inventory_rows
    )


RAW_SHA.write_text(
    f"{sha256_file(ARCHIVE)}  "
    "data/raw/cex/sample_code/r-ucc.zip\n",
    encoding="utf-8",
)


# =============================================================================
# Semantic source-code evidence
# =============================================================================

PATTERNS = {
    "FINLWT21":
        re.compile(
            r"\bfinlwt21\b",
            re.I,
        ),

    "WTREP":
        re.compile(
            r"\bwtrep(?:0?1|[0-9]{2})?\b|\bwtrep",
            re.I,
        ),

    "MO_SCOPE":
        re.compile(
            r"\bmo_?scope\b",
            re.I,
        ),

    "UCC":
        re.compile(
            r"\bucc\b",
            re.I,
        ),

    "COST":
        re.compile(
            r"\bcost\b",
            re.I,
        ),

    "SURVEY_SOURCE":
        re.compile(
            r"\bsurvey\b|\bsource\b",
            re.I,
        ),

    "FACTOR":
        re.compile(
            r"\bfactor\b",
            re.I,
        ),

    "DIARY_13":
        re.compile(
            r"(?:\*\s*13\b|\b13\s*\*|"
            r"\b13\b.{0,80}\bdiar|"
            r"\bdiar.{0,80}\b13\b)",
            re.I,
        ),

    "QNUM_OR_DIV4":
        re.compile(
            r"\bqnum\b|"
            r"finlwt21\s*/\s*4|"
            r"\bpopwt\b|"
            r"/\s*4\b",
            re.I,
        ),
}


context_rows = []

presence = Counter()


for member, text in text_members:

    lines = text.splitlines()

    for i, line in enumerate(
        lines,
        start=1,
    ):

        for concept, pattern in PATTERNS.items():

            if not pattern.search(
                line
            ):
                continue

            presence[
                concept
            ] += 1

            # Keep only compact source-code context:
            # previous/current/next line.
            lo = max(
                0,
                i - 2,
            )

            hi = min(
                len(lines),
                i + 1,
            )

            context = " || ".join(
                f"{j + 1}:{lines[j].strip()}"
                for j in range(
                    lo,
                    hi,
                )
            )

            context_rows.append({
                "concept": concept,
                "member": member,
                "line": i,
                "context": context,
            })


with CONTEXT.open(
    "w",
    newline="",
    encoding="utf-8",
) as f:

    fields = [
        "concept",
        "member",
        "line",
        "context",
    ]

    writer = csv.DictWriter(
        f,
        fieldnames=fields,
        delimiter="\t",
    )

    writer.writeheader()

    writer.writerows(
        sorted(
            context_rows,
            key=lambda r: (
                r["concept"],
                r["member"],
                int(r["line"]),
            ),
        )
    )


# =============================================================================
# Gates
# =============================================================================

required_core = {
    "FINLWT21",
    "WTREP",
    "MO_SCOPE",
    "UCC",
    "COST",
    "SURVEY_SOURCE",
}


core_pass = all(
    presence[x] > 0
    for x in required_core
)


periodicity_evidence = (
    presence["DIARY_13"] > 0
)


factor_evidence = (
    presence["FACTOR"] > 0
)


qnum_evidence = (
    presence["QNUM_OR_DIV4"] > 0
)


overall = (
    core_pass
    and periodicity_evidence
    and factor_evidence
    and qnum_evidence
)


summary = "\n".join([
    "=" * 100,
    "ECONOMIC GEOMETRY RESEARCH — E3B3C3 OFFICIAL BLS SAMPLE-CODE AUDIT",
    "=" * 100,
    "",
    "MICRODATA_DATA_ROWS_PARSED=0",
    "COST_VALUES_READ=0",
    "ECONOMIC_VALUES_OPENED=0",
    "REAL_INFLATION_ESTIMATED=0",
    "",
    "===== SOURCE =====",
    "SOURCE=BLS_OFFICIAL_R_UCC_SAMPLE_CODE",
    f"ARCHIVE_SHA256={sha256_file(ARCHIVE)}",
    f"ARCHIVE_MEMBERS={len(inventory_rows)}",
    f"TEXT_CODE_MEMBERS={len(text_members)}",
    "",
    "===== SEMANTIC EVIDENCE =====",
    f"FINLWT21_HITS={presence['FINLWT21']}",
    f"WTREP_HITS={presence['WTREP']}",
    f"MO_SCOPE_HITS={presence['MO_SCOPE']}",
    f"UCC_HITS={presence['UCC']}",
    f"COST_HITS={presence['COST']}",
    f"SURVEY_SOURCE_HITS={presence['SURVEY_SOURCE']}",
    f"QNUM_OR_DIV4_HITS={presence['QNUM_OR_DIV4']}",
    f"DIARY_13_HITS={presence['DIARY_13']}",
    f"FACTOR_HITS={presence['FACTOR']}",
    "",
    (
        "CORE_WEIGHT_AND_UCC_EVIDENCE=PASS"
        if core_pass
        else
        "CORE_WEIGHT_AND_UCC_EVIDENCE=FAIL"
    ),
    (
        "QNUM_WEIGHT_ADJUSTMENT_EVIDENCE=PASS"
        if qnum_evidence
        else
        "QNUM_WEIGHT_ADJUSTMENT_EVIDENCE=FAIL"
    ),
    (
        "DIARY_PERIODICITY_EVIDENCE=PASS"
        if periodicity_evidence
        else
        "DIARY_PERIODICITY_EVIDENCE=FAIL"
    ),
    (
        "HIERARCHY_FACTOR_EVIDENCE=PASS"
        if factor_evidence
        else
        "HIERARCHY_FACTOR_EVIDENCE=FAIL"
    ),
    "",
    "EXACT_INTEGRATED_ESTIMATOR_IMPLEMENTATION_FROZEN=0",
    "COST_VALUES_AUTHORIZED=0",
    "",
    (
        "E3B3C3_OFFICIAL_SAMPLE_CODE_AUDIT=PASS"
        if overall
        else
        "E3B3C3_OFFICIAL_SAMPLE_CODE_AUDIT=FAIL"
    ),
    (
        "E3B3C4_EXACT_ESTIMATOR_CONTRACT_AUTHORIZED=1"
        if overall
        else
        "E3B3C4_EXACT_ESTIMATOR_CONTRACT_AUTHORIZED=0"
    ),
    "",
])


OUT.write_text(
    summary,
    encoding="utf-8",
)

print(
    summary
)

if not overall:
    raise SystemExit(1)
