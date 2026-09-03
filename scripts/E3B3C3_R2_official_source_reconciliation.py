from __future__ import annotations

import csv
import hashlib
import re
import zipfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

ARCHIVES = {
    "SAS": ROOT / "data/raw/cex/sample_code/sas-ucc.zip",
    "STATA": ROOT / "data/raw/cex/sample_code/stata-ucc.zip",
}

R1 = (
    ROOT
    / "data/metadata/E3B3C3_R1_R_sample_scope_forensic.txt"
)

OUT = (
    ROOT
    / "data/metadata/E3B3C3_R2_official_source_reconciliation.txt"
)

INVENTORY = (
    ROOT
    / "data/metadata/E3B3C3_R2_code_inventory.tsv"
)

CONTEXT = (
    ROOT
    / "data/metadata/E3B3C3_R2_semantic_context.tsv"
)

HASHES = (
    ROOT
    / "data/metadata/E3B3C3_R2_source_sha256.txt"
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


if not R1.exists():
    raise RuntimeError("missing frozen R1 forensic")

r1_text = R1.read_text(encoding="utf-8")

required_r1 = [
    "R_SAMPLE_SCOPE=INTERVIEW_FMLI_MTBI_ONLY",
    "R_SAMPLE_CALENDAR_WEIGHT_FORMULA=PASS",
    "E3B3C3_R1_R_SAMPLE_SCOPE_FORENSIC=PASS",
]

for token in required_r1:
    if token not in r1_text:
        raise RuntimeError(f"missing R1 invariant={token}")


PATTERNS = {
    "FMLI": re.compile(r"\bfmli\w*", re.I),
    "MTBI": re.compile(r"\bmtbi\w*", re.I),
    "FMLD": re.compile(r"\bfmld\w*", re.I),
    "EXPD": re.compile(r"\bexpd\w*", re.I),
    "FINLWT21": re.compile(r"\bfinlwt21\b", re.I),
    "WTREP": re.compile(r"\bwtrep(?:\d{1,2})?\b|\bwtrep", re.I),
    "UCC": re.compile(r"\bucc\b", re.I),
    "COST": re.compile(r"\bcost\b|\bexpend\w*\b", re.I),
    "FACTOR": re.compile(r"\bfactor\b", re.I),
    "INTERVIEW": re.compile(r"\binterview\b|\bintrvw\b", re.I),
    "DIARY": re.compile(r"\bdiary\b", re.I),
    "HIERARCHY": re.compile(r"\bhierarch\w*\b|\bsource.?selection\b", re.I),
}


# Specific periodicity pattern:
# direct multiply by 13 OR 13 close to Diary/FMLD/EXPD/weekly language.
DIARY13 = re.compile(
    r"(?:"
    r"\*\s*13(?:\.0+)?\b"
    r"|"
    r"\b13(?:\.0+)?\s*\*"
    r"|"
    r"(?:diary|fmld|expd|weekly).{0,160}\b13(?:\.0+)?\b"
    r"|"
    r"\b13(?:\.0+)?\b.{0,160}(?:diary|fmld|expd|weekly)"
    r")",
    re.I | re.S,
)


TEXT_SUFFIXES = {
    ".sas",
    ".do",
    ".ado",
    ".txt",
    ".r",
    ".csv",
}


inventory_rows = []
context_rows = []
source_totals: dict[str, Counter] = {}
diary13_totals: dict[str, int] = {}
hash_lines = []


for language, archive in ARCHIVES.items():

    if not archive.exists():
        raise RuntimeError(f"missing archive={archive}")

    if not zipfile.is_zipfile(archive):
        raise RuntimeError(f"invalid ZIP={archive}")

    hash_lines.append(
        f"{sha256(archive)}  "
        f"{archive.relative_to(ROOT)}"
    )

    counts = Counter()
    diary13_count = 0

    with zipfile.ZipFile(archive) as zf:

        members = [
            x
            for x in zf.namelist()
            if not x.endswith("/")
        ]

        if not members:
            raise RuntimeError(
                f"{language}: zero archive members"
            )

        for member in sorted(members):

            raw = zf.read(member)
            suffix = Path(member).suffix.lower()

            text_candidate = suffix in TEXT_SUFFIXES

            text = ""

            if text_candidate:

                decoded = None

                for enc in (
                    "utf-8-sig",
                    "utf-8",
                    "cp1252",
                    "latin-1",
                ):
                    try:
                        decoded = raw.decode(enc)
                        break
                    except UnicodeDecodeError:
                        continue

                if decoded is None:
                    raise RuntimeError(
                        f"cannot decode {member}"
                    )

                text = decoded

            inventory_rows.append({
                "language": language,
                "member": member,
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "suffix": suffix,
                "text_candidate": int(text_candidate),
                "line_count": (
                    len(text.splitlines())
                    if text_candidate
                    else 0
                ),
            })

            if not text_candidate:
                continue

            lines = text.splitlines()

            for concept, pattern in PATTERNS.items():

                for i, line in enumerate(lines, start=1):

                    if not pattern.search(line):
                        continue

                    counts[concept] += 1

                    lo = max(0, i - 2)
                    hi = min(len(lines), i + 1)

                    ctx = " || ".join(
                        f"{j + 1}:{lines[j].strip()}"
                        for j in range(lo, hi)
                    )

                    context_rows.append({
                        "language": language,
                        "concept": concept,
                        "member": member,
                        "line": i,
                        "context": ctx,
                    })

            for match in DIARY13.finditer(text):

                diary13_count += 1

                line_no = (
                    text.count(
                        "\n",
                        0,
                        match.start(),
                    )
                    + 1
                )

                lines2 = text.splitlines()

                lo = max(
                    0,
                    line_no - 2,
                )

                hi = min(
                    len(lines2),
                    line_no + 1,
                )

                ctx = " || ".join(
                    f"{j + 1}:{lines2[j].strip()}"
                    for j in range(lo, hi)
                )

                context_rows.append({
                    "language": language,
                    "concept": "DIARY_X13",
                    "member": member,
                    "line": line_no,
                    "context": ctx,
                })

    source_totals[language] = counts
    diary13_totals[language] = diary13_count


with INVENTORY.open(
    "w",
    newline="",
    encoding="utf-8",
) as f:

    fields = [
        "language",
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
    writer.writerows(inventory_rows)


with CONTEXT.open(
    "w",
    newline="",
    encoding="utf-8",
) as f:

    fields = [
        "language",
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
                r["language"],
                r["concept"],
                r["member"],
                int(r["line"]),
            ),
        )
    )


HASHES.write_text(
    "\n".join(hash_lines) + "\n",
    encoding="utf-8",
)


def direct_diary_pass(language: str) -> bool:

    c = source_totals[language]

    return (
        (c["FMLD"] > 0 or c["EXPD"] > 0)
        and c["FINLWT21"] > 0
        and c["UCC"] > 0
        and c["COST"] > 0
        and diary13_totals[language] > 0
    )


sas_diary = direct_diary_pass("SAS")
stata_diary = direct_diary_pass("STATA")

secondary_diary_pass = (
    sas_diary
    or stata_diary
)


# WTREP/factor are informative but deliberately not hard gates.
wtrep_any = any(
    source_totals[x]["WTREP"] > 0
    for x in source_totals
)

factor_any = any(
    source_totals[x]["FACTOR"] > 0
    for x in source_totals
)


overall = secondary_diary_pass


report = [
    "=" * 100,
    "E3B3C3 R2 — OFFICIAL SAS/STATA SOURCE RECONCILIATION",
    "=" * 100,
    "",
    "MICRODATA_DATA_ROWS_PARSED=0",
    "COST_VALUES_READ=0",
    "EXPENDITURE_VALUES_OPENED=0",
    "HOUSEHOLD_ECONOMIC_VALUES_OPENED=0",
    "REAL_INFLATION_ESTIMATED=0",
    "",
    "===== FROZEN R EVIDENCE =====",
    "R_SAMPLE_SCOPE=INTERVIEW_FMLI_MTBI_ONLY",
    "R_SAMPLE_CALENDAR_WEIGHT_FORMULA=PASS",
    "",
]


for language in ("SAS", "STATA"):

    c = source_totals[language]

    report += [
        f"===== {language} =====",
        f"FMLI_HITS={c['FMLI']}",
        f"MTBI_HITS={c['MTBI']}",
        f"FMLD_HITS={c['FMLD']}",
        f"EXPD_HITS={c['EXPD']}",
        f"FINLWT21_HITS={c['FINLWT21']}",
        f"WTREP_HITS={c['WTREP']}",
        f"UCC_HITS={c['UCC']}",
        f"COST_OR_EXPEND_HITS={c['COST']}",
        f"FACTOR_HITS={c['FACTOR']}",
        f"DIARY_HITS={c['DIARY']}",
        f"HIERARCHY_HITS={c['HIERARCHY']}",
        f"DIARY_X13_HITS={diary13_totals[language]}",
        (
            f"{language}_DIRECT_DIARY_IMPLEMENTATION=PASS"
            if direct_diary_pass(language)
            else
            f"{language}_DIRECT_DIARY_IMPLEMENTATION=FAIL"
        ),
        "",
    ]


report += [
    "===== RECONCILIATION =====",
    (
        "SECONDARY_OFFICIAL_DIARY_IMPLEMENTATION=PASS"
        if secondary_diary_pass
        else
        "SECONDARY_OFFICIAL_DIARY_IMPLEMENTATION=FAIL"
    ),
    (
        "SECONDARY_CODE_WTREP_EVIDENCE=PRESENT"
        if wtrep_any
        else
        "SECONDARY_CODE_WTREP_EVIDENCE=ABSENT"
    ),
    (
        "SECONDARY_CODE_FACTOR_EVIDENCE=PRESENT"
        if factor_any
        else
        "SECONDARY_CODE_FACTOR_EVIDENCE=ABSENT"
    ),
    "",
    "BRR_MAY_BE_GROUNDED_IN_OFFICIAL_METHODOLOGY=1",
    "HIERARCHY_FACTOR_MAY_BE_GROUNDED_IN_OFFICIAL_DOCUMENTATION=1",
    "",
    "EXACT_INTEGRATED_ESTIMATOR_IMPLEMENTATION_FROZEN=0",
    "COST_VALUES_AUTHORIZED=0",
    "",
    (
        "E3B3C3_R2_OFFICIAL_SOURCE_RECONCILIATION=PASS"
        if overall
        else
        "E3B3C3_R2_OFFICIAL_SOURCE_RECONCILIATION=FAIL"
    ),
    (
        "E3B3C4_EXACT_ESTIMATOR_CONTRACT_AUTHORIZED=1"
        if overall
        else
        "E3B3C4_EXACT_ESTIMATOR_CONTRACT_AUTHORIZED=0"
    ),
    "",
]


OUT.write_text(
    "\n".join(report),
    encoding="utf-8",
)

print("\n".join(report))

if not overall:
    raise SystemExit(1)
