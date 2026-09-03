from __future__ import annotations

import re
import zipfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

STUBS = ROOT / "data/raw/cex/stubs/stubs.zip"
OUT = ROOT / "data/metadata/E3B3A_R1_hierarchy_layout_forensic.txt"


VALID_SOURCE = {"I", "D", "G", "T", "S"}

VALID_FACTOR = {"", "1", "4"}

VALID_SECTION = {
    "CUCHARS",
    "FOOD",
    "EXPEND",
    "INCOME",
    "ASSETS",
    "ADDENDA",
}


with zipfile.ZipFile(STUBS) as zf:

    members = [
        name
        for name in zf.namelist()
        if (
            Path(name).name.lower()
            == "ce-hg-integ-2022.txt"
        )
    ]

    if len(members) != 1:
        raise RuntimeError(
            f"expected one CE-HG-Integ-2022.txt; found={members}"
        )

    member = members[0]

    raw = zf.read(member).decode(
        "latin-1",
        errors="strict",
    )


lines = []

for lineno, line in enumerate(
    raw.splitlines(),
    start=1,
):

    ucc = line[69:75].strip()

    if re.fullmatch(r"\d{6}", ucc):

        lines.append(
            (lineno, line, ucc)
        )


if not lines:
    raise RuntimeError(
        "zero UCC rows"
    )


def audit_layout(
    name: str,
    source_idx: int,
    factor_idx: int,
    section_idx: int,
):

    source_counter = Counter()
    factor_counter = Counter()
    section_counter = Counter()

    valid_source = 0
    valid_factor = 0
    valid_section = 0

    for _, line, _ in lines:

        source = line[
            source_idx:source_idx + 1
        ].strip()

        factor = line[
            factor_idx:factor_idx + 1
        ].strip()

        section = line[
            section_idx:
        ].strip().split()[0] if line[section_idx:].strip() else ""

        source_counter[source] += 1
        factor_counter[factor] += 1
        section_counter[section] += 1

        if source in VALID_SOURCE:
            valid_source += 1

        if factor in VALID_FACTOR:
            valid_factor += 1

        if section in VALID_SECTION:
            valid_section += 1

    return {
        "name": name,
        "source_pos": source_idx + 1,
        "factor_pos": factor_idx + 1,
        "section_pos": section_idx + 1,
        "valid_source": valid_source,
        "valid_factor": valid_factor,
        "valid_section": valid_section,
        "I": source_counter["I"],
        "D": source_counter["D"],
        "sources": source_counter,
        "factors": factor_counter,
        "sections": section_counter,
    }


# Current BLS web documentation.
current = audit_layout(
    "CURRENT_WEB_DOC",
    82,  # position 83
    85,  # position 86
    88,  # position 89
)

# Candidate legacy/year-specific layout implied by downloaded 2022 bytes.
legacy = audit_layout(
    "LEGACY_2022",
    79,  # position 80
    82,  # position 83
    85,  # position 86
)


def fmt_counter(c: Counter) -> str:
    return ",".join(
        f"{repr(k)}:{v}"
        for k, v in sorted(
            c.items(),
            key=lambda kv: kv[0],
        )
    )


report = [
    "=" * 100,
    "E3B3A R1 — 2022 INTEGRATED HIERARCHY LAYOUT FORENSIC",
    "=" * 100,
    "",
    f"HIERARCHY_MEMBER={member}",
    f"UCC_ROWS={len(lines)}",
    "",
]

for result in (current, legacy):

    report += [
        f"===== {result['name']} =====",
        f"SOURCE_POSITION={result['source_pos']}",
        f"FACTOR_POSITION={result['factor_pos']}",
        f"SECTION_POSITION={result['section_pos']}",
        f"VALID_SOURCE_ROWS={result['valid_source']}",
        f"VALID_FACTOR_ROWS={result['valid_factor']}",
        f"VALID_SECTION_ROWS={result['valid_section']}",
        f"INTERVIEW_ROWS={result['I']}",
        f"DIARY_ROWS={result['D']}",
        f"SOURCE_COUNTS={fmt_counter(result['sources'])}",
        f"FACTOR_COUNTS={fmt_counter(result['factors'])}",
        f"SECTION_COUNTS={fmt_counter(result['sections'])}",
        "",
    ]


legacy_pass = (
    legacy["I"] > 0
    and legacy["D"] > 0
    and legacy["valid_source"] > current["valid_source"]
    and legacy["valid_section"] > current["valid_section"]
)


report += [
    "MICRODATA_DATA_ROWS_PARSED=0",
    "ECONOMIC_VALUES_OPENED=0",
    "",
    (
        "YEAR_SPECIFIC_2022_LAYOUT=80_83_86"
        if legacy_pass
        else
        "YEAR_SPECIFIC_2022_LAYOUT=UNRESOLVED"
    ),
    (
        "E3B3A_R1_LAYOUT_FORENSIC=PASS"
        if legacy_pass
        else
        "E3B3A_R1_LAYOUT_FORENSIC=FAIL"
    ),
    "",
]


OUT.write_text(
    "\n".join(report),
    encoding="utf-8",
)

print(
    "\n".join(report)
)

if not legacy_pass:
    raise SystemExit(1)
