from __future__ import annotations

import hashlib
import re
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

ARCHIVE = ROOT / "data/raw/cex/sample_code/r-ucc.zip"

OUT = ROOT / "data/metadata/E3B3C3_R1_R_sample_scope_forensic.txt"


EXPECTED_ARCHIVE_SHA = (
    "c2d8021f52b0118e8e73ce743de63cf872a2b8c668314f0977193ca54fc46a85"
)

EXPECTED_MEMBER_SHA = (
    "633e70db439a55a7910684a39e7c0609d59768d61e1db929b756c0e13c59b92e"
)

EXPECTED_MEMBER = (
    "R UCC/calendar_year_estimate_ucc.R"
)


def sha256_file(path: Path) -> str:

    h = hashlib.sha256()

    with path.open("rb") as f:
        for block in iter(
            lambda: f.read(1024 * 1024),
            b"",
        ):
            h.update(block)

    return h.hexdigest()


if sha256_file(ARCHIVE) != EXPECTED_ARCHIVE_SHA:
    raise RuntimeError(
        "official R archive SHA mismatch"
    )


with zipfile.ZipFile(ARCHIVE) as zf:

    members = [
        x
        for x in zf.namelist()
        if not x.endswith("/")
    ]

    if members != [EXPECTED_MEMBER]:
        raise RuntimeError(
            f"unexpected archive members={members}"
        )

    raw = zf.read(
        EXPECTED_MEMBER
    )


member_sha = hashlib.sha256(
    raw
).hexdigest()

if member_sha != EXPECTED_MEMBER_SHA:
    raise RuntimeError(
        f"R member SHA mismatch={member_sha}"
    )


text = raw.decode(
    "utf-8-sig",
    errors="strict",
)

lower = text.lower()


def hits(pattern: str) -> int:
    return len(
        re.findall(
            pattern,
            text,
            flags=re.I | re.S,
        )
    )


term_counts = {
    "FMLI": hits(r"\bfmli\b"),
    "MTBI": hits(r"\bmtbi\b"),
    "FMLD": hits(r"\bfmld\b"),
    "EXPD": hits(r"\bexpd\b"),
    "FINLWT21": hits(r"\bfinlwt21\b"),
    "QINTRVMO": hits(r"\bqintrvmo\b"),
    "QINTRVYR": hits(r"\bqintrvyr\b"),
    "POPWT": hits(r"\bpopwt\b"),
    "COST": hits(r"\bcost\b"),
    "WTREP": hits(r"\bwtrep"),
    "FACTOR": hits(r"\bfactor\b"),
}


first_scope = bool(
    re.search(
        r"\(\s*qintrvmo\s*-\s*1\s*\)"
        r"\s*/\s*3"
        r"\s*\*\s*finlwt21"
        r"\s*/\s*4",
        lower,
        flags=re.S,
    )
)


fifth_scope = bool(
    re.search(
        r"\(\s*4\s*-\s*qintrvmo\s*\)"
        r"\s*/\s*3"
        r"\s*\*\s*finlwt21"
        r"\s*/\s*4",
        lower,
        flags=re.S,
    )
)


full_scope = bool(
    re.search(
        r"finlwt21\s*/\s*4",
        lower,
    )
)


mean_formula = bool(
    re.search(
        r"sum\s*\(\s*cost\s*\*\s*finlwt21\s*\)"
        r"\s*/\s*"
        r"sum\s*\(\s*popwt\s*\)",
        lower,
        flags=re.S,
    )
)


diary_13_direct = bool(
    re.search(
        r"(?:\*\s*13\b|\b13\s*\*)",
        lower,
    )
)


interview_files_present = (
    term_counts["FMLI"] > 0
    and term_counts["MTBI"] > 0
)


diary_files_present = (
    term_counts["FMLD"] > 0
    or term_counts["EXPD"] > 0
)


calendar_formula_pass = all([
    term_counts["FINLWT21"] > 0,
    term_counts["QINTRVMO"] > 0,
    term_counts["QINTRVYR"] > 0,
    term_counts["POPWT"] > 0,
    first_scope,
    fifth_scope,
    full_scope,
    mean_formula,
])


scope_pass = (
    interview_files_present
    and not diary_files_present
    and calendar_formula_pass
)


scope = (
    "INTERVIEW_FMLI_MTBI_ONLY"
    if scope_pass
    else
    "UNRESOLVED"
)


lines = [
    "=" * 100,
    "E3B3C3 R1 — OFFICIAL R UCC SAMPLE-CODE SCOPE FORENSIC",
    "=" * 100,
    "",
    "MICRODATA_DATA_ROWS_PARSED=0",
    "COST_VALUES_READ=0",
    "ECONOMIC_VALUES_OPENED=0",
    "REAL_INFLATION_ESTIMATED=0",
    "",
    "===== SOURCE =====",
    f"ARCHIVE_SHA256={EXPECTED_ARCHIVE_SHA}",
    f"MEMBER={EXPECTED_MEMBER}",
    f"MEMBER_SHA256={member_sha}",
    f"R_SOURCE_LINES={len(text.splitlines())}",
    "",
    "===== FILE-FAMILY EVIDENCE =====",
]

for key in (
    "FMLI",
    "MTBI",
    "FMLD",
    "EXPD",
):

    lines.append(
        f"{key}_HITS={term_counts[key]}"
    )


lines += [
    "",
    "===== CALENDAR WEIGHT EVIDENCE =====",
    f"FINLWT21_HITS={term_counts['FINLWT21']}",
    f"QINTRVMO_HITS={term_counts['QINTRVMO']}",
    f"QINTRVYR_HITS={term_counts['QINTRVYR']}",
    f"POPWT_HITS={term_counts['POPWT']}",
    f"COST_HITS={term_counts['COST']}",
    f"FIRST_PARTIAL_SCOPE_FORMULA={int(first_scope)}",
    f"FIFTH_PARTIAL_SCOPE_FORMULA={int(fifth_scope)}",
    f"FULL_SCOPE_FINLWT21_DIV4={int(full_scope)}",
    f"MEAN_SUM_COST_FINLWT21_DIV_SUM_POPWT={int(mean_formula)}",
    "",
    "===== ABSENT DIRECT EVIDENCE =====",
    f"WTREP_HITS={term_counts['WTREP']}",
    f"FACTOR_HITS={term_counts['FACTOR']}",
    f"DIARY_X13_DIRECT={int(diary_13_direct)}",
    "",
    "===== CLASSIFICATION =====",
    f"R_SAMPLE_SCOPE={scope}",
    (
        "R_SAMPLE_CALENDAR_WEIGHT_FORMULA=PASS"
        if calendar_formula_pass
        else
        "R_SAMPLE_CALENDAR_WEIGHT_FORMULA=FAIL"
    ),
    (
        "R_SAMPLE_SELF_CONTAINED_INTERVIEW_DIARY_INTEGRATION=0"
        if scope_pass
        else
        "R_SAMPLE_SELF_CONTAINED_INTERVIEW_DIARY_INTEGRATION=UNRESOLVED"
    ),
    "DOCUMENTATION_REQUIRED_FOR_DIARY_PERIODICITY=1",
    "DOCUMENTATION_REQUIRED_FOR_BRR=1",
    "DOCUMENTATION_REQUIRED_FOR_HIERARCHY_FACTOR=1",
    "",
    "EXACT_INTEGRATED_ESTIMATOR_IMPLEMENTATION_FROZEN=0",
    "COST_VALUES_AUTHORIZED=0",
    "",
    (
        "E3B3C3_R1_R_SAMPLE_SCOPE_FORENSIC=PASS"
        if scope_pass
        else
        "E3B3C3_R1_R_SAMPLE_SCOPE_FORENSIC=FAIL"
    ),
    (
        "E3B3C3_R2_OFFICIAL_SOURCE_RECONCILIATION_AUTHORIZED=1"
        if scope_pass
        else
        "E3B3C3_R2_OFFICIAL_SOURCE_RECONCILIATION_AUTHORIZED=0"
    ),
    "",
]


OUT.write_text(
    "\n".join(lines),
    encoding="utf-8",
)

print(
    "\n".join(lines)
)

if not scope_pass:
    raise SystemExit(1)
