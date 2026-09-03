from __future__ import annotations

import csv
import hashlib
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

STUBS = ROOT / "data/raw/cex/stubs/stubs.zip"

OUT = ROOT / "data/metadata/E3B3B_hierarchy_tree_audit.txt"
TREE = ROOT / "data/metadata/E3B3B_ucc_hierarchy_tree.tsv"
BROAD = ROOT / "data/metadata/E3B3B_broad_hierarchy_inventory.tsv"
DUPS = ROOT / "data/metadata/E3B3B_expenditure_duplicate_ucc_audit.tsv"


EXPECTED_STUBS_SHA = (
    "58098e493f0e99239b1f306555e3c1ff2cda57e5cb0287517b22a1b789166d33"
)

VALID_SOURCE = {
    "I",
    "D",
}

VALID_SECTION = {
    "CUCHARS",
    "FOOD",
    "EXPEND",
    "INCOME",
    "ASSETS",
    "ADDENDA",
}

EXPENDITURE_SECTIONS = {
    "FOOD",
    "EXPEND",
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


if sha256(STUBS) != EXPECTED_STUBS_SHA:
    raise RuntimeError(
        "stubs.zip SHA mismatch"
    )


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


# =============================================================================
# Logical-record reconstruction
# =============================================================================

records: list[dict] = []

for lineno, line in enumerate(
    raw.splitlines(),
    start=1,
):

    type_code = line[0:1].strip()

    # Comment lines.
    if type_code == "*":
        continue

    title = line[6:69].strip()

    # Type 2 = continuation of title from previous logical record.
    if type_code == "2":

        if not records:
            raise RuntimeError(
                f"orphan type-2 line at {lineno}"
            )

        if title:
            records[-1]["title"] = (
                records[-1]["title"]
                + " "
                + title
            ).strip()

        records[-1]["end_line"] = lineno

        continue

    if type_code != "1":
        continue

    level_raw = line[3:4].strip()

    if not level_raw.isdigit():
        continue

    level = int(level_raw)

    if not 1 <= level <= 9:
        raise RuntimeError(
            f"invalid hierarchy level={level} line={lineno}"
        )

    ucc = line[69:75].strip()

    # Proven year-specific 2022 layout from E3B3A R1.
    source = line[79:80].strip()
    factor = line[82:83].strip()
    section = line[85:].strip()

    records.append({
        "start_line": lineno,
        "end_line": lineno,
        "level": level,
        "title": title,
        "ucc": ucc,
        "source": source,
        "factor": factor,
        "section": section,
    })


if not records:
    raise RuntimeError(
        "zero logical hierarchy records"
    )


# =============================================================================
# Reconstruct ancestry
# =============================================================================

stack: dict[int, dict] = {}

ucc_occurrences = []

for rec in records:

    level = rec["level"]

    # A new record at level L closes previous records at L and below.
    for key in list(stack):
        if key >= level:
            del stack[key]

    level_titles = {
        k: stack[k]["title"]
        for k in sorted(stack)
        if k < level
    }

    level_titles[level] = rec["title"]

    # Six-digit I/D UCC occurrences are the integrated-source records.
    if (
        re.fullmatch(r"\d{6}", rec["ucc"])
        and rec["source"] in VALID_SOURCE
    ):

        row = {
            "start_line": rec["start_line"],
            "end_line": rec["end_line"],
            "level": level,
            "ucc": rec["ucc"],
            "source": rec["source"],
            "factor": rec["factor"],
            "section": rec["section"],
            "leaf_title": rec["title"],
        }

        for n in range(1, 10):
            row[f"level_{n}_title"] = (
                level_titles.get(n, "")
            )

        path_parts = [
            level_titles[n]
            for n in sorted(level_titles)
            if level_titles[n]
        ]

        row["hierarchy_path"] = " > ".join(
            path_parts
        )

        ucc_occurrences.append(row)

    stack[level] = rec


if not ucc_occurrences:
    raise RuntimeError(
        "zero I/D UCC occurrences"
    )


# =============================================================================
# Basic integrity
# =============================================================================

invalid_sections = sorted({
    r["section"]
    for r in ucc_occurrences
    if r["section"] not in VALID_SECTION
})

if invalid_sections:
    raise RuntimeError(
        f"unexpected sections={invalid_sections}"
    )


missing_paths = [
    r
    for r in ucc_occurrences
    if not r["hierarchy_path"]
]

if missing_paths:
    raise RuntimeError(
        f"missing hierarchy paths={len(missing_paths)}"
    )


# =============================================================================
# Write full tree
# =============================================================================

TREE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

tree_fields = [
    "start_line",
    "end_line",
    "level",
    "ucc",
    "source",
    "factor",
    "section",
    "leaf_title",
] + [
    f"level_{n}_title"
    for n in range(1, 10)
] + [
    "hierarchy_path",
]


with TREE.open(
    "w",
    newline="",
    encoding="utf-8",
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=tree_fields,
        delimiter="\t",
    )

    writer.writeheader()
    writer.writerows(
        ucc_occurrences
    )


# =============================================================================
# Counts and expenditure subset
# =============================================================================

source_counts = Counter(
    r["source"]
    for r in ucc_occurrences
)

section_counts = Counter(
    r["section"]
    for r in ucc_occurrences
)

factor_counts = Counter(
    r["factor"]
    for r in ucc_occurrences
)

unique_all = {
    r["ucc"]
    for r in ucc_occurrences
}

exp_rows = [
    r
    for r in ucc_occurrences
    if r["section"] in EXPENDITURE_SECTIONS
]

unique_exp = {
    r["ucc"]
    for r in exp_rows
}


# =============================================================================
# Duplicate / semantic-conflict audit
# =============================================================================

by_ucc = defaultdict(list)

for row in exp_rows:
    by_ucc[row["ucc"]].append(row)


duplicate_groups = {
    ucc: rows
    for ucc, rows in by_ucc.items()
    if len(rows) > 1
}


dup_rows = []

source_conflicts = []
factor_conflicts = []

for ucc, rows in sorted(
    duplicate_groups.items()
):

    sources = sorted({
        r["source"]
        for r in rows
    })

    factors = sorted({
        r["factor"]
        for r in rows
    })

    sections = sorted({
        r["section"]
        for r in rows
    })

    paths = sorted({
        r["hierarchy_path"]
        for r in rows
    })

    source_conflict = (
        len(sources) > 1
    )

    factor_conflict = (
        len(factors) > 1
    )

    if source_conflict:
        source_conflicts.append(ucc)

    if factor_conflict:
        factor_conflicts.append(ucc)

    dup_rows.append({
        "ucc": ucc,
        "occurrences": len(rows),
        "sources": ",".join(sources),
        "factors": ",".join(factors),
        "sections": ",".join(sections),
        "unique_paths": len(paths),
        "source_conflict": int(
            source_conflict
        ),
        "factor_conflict": int(
            factor_conflict
        ),
    })


with DUPS.open(
    "w",
    newline="",
    encoding="utf-8",
) as f:

    fields = [
        "ucc",
        "occurrences",
        "sources",
        "factors",
        "sections",
        "unique_paths",
        "source_conflict",
        "factor_conflict",
    ]

    writer = csv.DictWriter(
        f,
        fieldnames=fields,
        delimiter="\t",
    )

    writer.writeheader()
    writer.writerows(
        dup_rows
    )


# =============================================================================
# Broad hierarchy inventory
# =============================================================================

broad_counter = Counter()

for row in exp_rows:

    # Store the first three available hierarchy labels.
    hierarchy_labels = [
        row[f"level_{n}_title"]
        for n in range(1, 10)
        if row[f"level_{n}_title"]
    ]

    l1 = (
        hierarchy_labels[0]
        if len(hierarchy_labels) >= 1
        else ""
    )

    l2 = (
        hierarchy_labels[1]
        if len(hierarchy_labels) >= 2
        else ""
    )

    l3 = (
        hierarchy_labels[2]
        if len(hierarchy_labels) >= 3
        else ""
    )

    broad_counter[
        (
            row["section"],
            l1,
            l2,
            l3,
            row["source"],
        )
    ] += 1


broad_rows = []

for (
    section,
    l1,
    l2,
    l3,
    source,
), count in sorted(
    broad_counter.items()
):

    broad_rows.append({
        "section": section,
        "level_1_or_first": l1,
        "level_2_or_second": l2,
        "level_3_or_third": l3,
        "source": source,
        "occurrence_count": count,
    })


with BROAD.open(
    "w",
    newline="",
    encoding="utf-8",
) as f:

    fields = [
        "section",
        "level_1_or_first",
        "level_2_or_second",
        "level_3_or_third",
        "source",
        "occurrence_count",
    ]

    writer = csv.DictWriter(
        f,
        fieldnames=fields,
        delimiter="\t",
    )

    writer.writeheader()
    writer.writerows(
        broad_rows
    )


# =============================================================================
# Gates
# =============================================================================

expected_source_counts = {
    "I": 755,
    "D": 484,
}

expected_section_counts = {
    "ADDENDA": 470,
    "ASSETS": 71,
    "CUCHARS": 31,
    "EXPEND": 529,
    "FOOD": 116,
    "INCOME": 22,
}

source_count_pass = (
    dict(sorted(source_counts.items()))
    == expected_source_counts
)

section_count_pass = (
    dict(sorted(section_counts.items()))
    == expected_section_counts
)

conflict_pass = (
    len(source_conflicts) == 0
    and len(factor_conflicts) == 0
)

overall = all([
    source_count_pass,
    section_count_pass,
    conflict_pass,
    len(exp_rows) > 0,
    len(unique_exp) > 0,
])


summary = "\n".join([
    "=" * 100,
    "ECONOMIC GEOMETRY RESEARCH — E3B3B HIERARCHY TREE AUDIT",
    "=" * 100,
    "",
    "MICRODATA_DATA_ROWS_PARSED=0",
    "COST_VALUES_READ=0",
    "EXPENDITURE_VALUES_OPENED=0",
    "HOUSEHOLD_ECONOMIC_VALUES_OPENED=0",
    "REAL_INFLATION_ESTIMATED=0",
    "",
    "===== FULL INTEGRATED HIERARCHY =====",
    f"LOGICAL_RECORDS={len(records)}",
    f"ID_UCC_OCCURRENCES={len(ucc_occurrences)}",
    f"UNIQUE_ID_UCCS={len(unique_all)}",
    f"SOURCE_COUNTS={dict(sorted(source_counts.items()))}",
    f"SECTION_COUNTS={dict(sorted(section_counts.items()))}",
    f"FACTOR_COUNTS={dict(sorted(factor_counts.items()))}",
    f"SOURCE_COUNT_REPLICATION={'PASS' if source_count_pass else 'FAIL'}",
    f"SECTION_COUNT_REPLICATION={'PASS' if section_count_pass else 'FAIL'}",
    "",
    "===== EXPENDITURE UNIVERSE =====",
    f"FOOD_EXPEND_OCCURRENCES={len(exp_rows)}",
    f"FOOD_EXPEND_UNIQUE_UCCS={len(unique_exp)}",
    f"EXPENDITURE_DUPLICATE_UCC_GROUPS={len(duplicate_groups)}",
    f"EXPENDITURE_SOURCE_CONFLICTS={len(source_conflicts)}",
    f"EXPENDITURE_FACTOR_CONFLICTS={len(factor_conflicts)}",
    f"EXPENDITURE_SOURCE_FACTOR_CONSISTENCY={'PASS' if conflict_pass else 'FAIL'}",
    "",
    "===== CLASSIFICATION STATE =====",
    "KEYWORD_ONLY_UCC_CLASSIFICATION=PROHIBITED",
    "C_COST_UCC_MAP_FROZEN=0",
    "H_SERVICE_UCC_MAP_FROZEN=0",
    "INTEGRATION_ARITHMETIC_FROZEN=0",
    "HOUSEHOLD_ECONOMIC_VALUES_AUTHORIZED=0",
    "",
    (
        "E3B3B_HIERARCHY_TREE_RECONSTRUCTION=PASS"
        if overall
        else
        "E3B3B_HIERARCHY_TREE_RECONSTRUCTION=FAIL"
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
