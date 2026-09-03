from __future__ import annotations

import csv
import hashlib
import zipfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

INT21 = ROOT / "data/raw/cex/2021/intrvw21.zip"
INT22 = ROOT / "data/raw/cex/2022/intrvw22.zip"
DIA22 = ROOT / "data/raw/cex/2022/diary22.zip"

MAP = ROOT / "data/metadata/E3B3C1_component_ucc_map.tsv"

OUT = ROOT / "data/metadata/E3B3C2_bls_estimator_semantics_audit.txt"
HEADER_OUT = ROOT / "data/metadata/E3B3C2_weight_header_audit.tsv"
FACTOR4_OUT = ROOT / "data/metadata/E3B3C2_factor4_uccs.tsv"


EXPECTED_MAP_SHA = (
    "a6dd2e592d45f0c7c8428a8265d3b857"
    "c615cd842e10241fff06d2a3c06c1e1f"
)


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


# =============================================================================
# Frozen map
# =============================================================================

if sha256(MAP) != EXPECTED_MAP_SHA:
    raise RuntimeError(
        "E3B3C1 component-map SHA mismatch"
    )


with MAP.open(
    encoding="utf-8",
) as f:

    map_rows = list(
        csv.DictReader(
            f,
            delimiter="\t",
        )
    )


if len(map_rows) != 645:
    raise RuntimeError(
        f"expected 645 mapped UCCs; got={len(map_rows)}"
    )


class_counts = Counter(
    r["component_class"]
    for r in map_rows
)

factor_counts = Counter(
    r["factor"]
    for r in map_rows
)

source_counts = Counter(
    r["source"]
    for r in map_rows
)


expected_classes = {
    "C_COST_PRIMARY": 435,
    "DURABLE_SERVICE_PENDING": 63,
    "EXCLUDED_INSURANCE_PENSION": 7,
    "EXCLUDED_TRANSFER": 9,
    "H_NONCORE_PENDING": 32,
    "H_SERVICE_CORE": 99,
}

if dict(sorted(class_counts.items())) != expected_classes:
    raise RuntimeError(
        f"class-count mutation={dict(class_counts)}"
    )


if factor_counts != Counter({
    "1": 642,
    "4": 3,
}):
    raise RuntimeError(
        f"factor-count mutation={dict(factor_counts)}"
    )


if source_counts != Counter({
    "I": 398,
    "D": 247,
}):
    raise RuntimeError(
        f"source-count mutation={dict(source_counts)}"
    )


factor4 = [
    r
    for r in map_rows
    if r["factor"] == "4"
]


with FACTOR4_OUT.open(
    "w",
    newline="",
    encoding="utf-8",
) as f:

    fields = [
        "ucc",
        "source",
        "factor",
        "component_class",
        "broad_category",
        "subcategory",
        "leaf_title",
    ]

    writer = csv.DictWriter(
        f,
        fieldnames=fields,
        delimiter="\t",
    )

    writer.writeheader()

    for row in sorted(
        factor4,
        key=lambda r: r["ucc"],
    ):
        writer.writerow({
            k: row[k]
            for k in fields
        })


# =============================================================================
# Header-only field audit
# =============================================================================

repweights = {
    f"WTREP{i:02d}"
    for i in range(1, 45)
}


interview_required = {
    "NEWID",
    "FINLWT21",
    "QINTRVMO",
    "QINTRVYR",
} | repweights


diary_required = {
    "NEWID",
    "FINLWT21",
} | repweights


header_plan = []

for archive, q in [
    (INT21, "221"),
    (INT22, "222"),
    (INT22, "223"),
    (INT22, "224"),
    (INT22, "231"),
]:

    header_plan.append((
        "INTERVIEW",
        archive,
        f"fmli{q}.csv",
        q,
        interview_required,
    ))


for q in (
    "221",
    "222",
    "223",
    "224",
):

    header_plan.append((
        "DIARY",
        DIA22,
        f"fmld{q}.csv",
        q,
        diary_required,
    ))


header_rows = []


for (
    survey,
    archive,
    basename,
    quarter,
    required,
) in header_plan:

    member = find_member(
        archive,
        basename,
    )

    header = first_header(
        archive,
        member,
    )

    upper = {
        x.upper()
        for x in header
    }

    missing = sorted(
        required - upper
    )

    header_rows.append({
        "survey": survey,
        "archive": archive.name,
        "quarter": quarter,
        "member": member,
        "column_count": len(header),
        "required_present": (
            len(required)
            - len(missing)
        ),
        "required_total": len(required),
        "repweights_present": sum(
            x in upper
            for x in repweights
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


with HEADER_OUT.open(
    "w",
    newline="",
    encoding="utf-8",
) as f:

    fields = [
        "survey",
        "archive",
        "quarter",
        "member",
        "column_count",
        "required_present",
        "required_total",
        "repweights_present",
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


header_pass = all(
    r["missing_required"] == "NONE"
    and r["repweights_present"] == 44
    for r in header_rows
)


interview_quarters = sorted({
    r["quarter"]
    for r in header_rows
    if r["survey"] == "INTERVIEW"
})

diary_quarters = sorted({
    r["quarter"]
    for r in header_rows
    if r["survey"] == "DIARY"
})


timing_pass = (
    interview_quarters
    == ["221", "222", "223", "224", "231"]
    and diary_quarters
    == ["221", "222", "223", "224"]
)


overall = all([
    header_pass,
    timing_pass,
    len(factor4) == 3,
])


summary = "\n".join([
    "=" * 100,
    "ECONOMIC GEOMETRY RESEARCH — E3B3C2 BLS ESTIMATOR SEMANTICS AUDIT",
    "=" * 100,
    "",
    "COST_VALUES_READ=0",
    "EXPENDITURE_VALUES_OPENED=0",
    "HOUSEHOLD_ECONOMIC_VALUES_OPENED=0",
    "REAL_INFLATION_ESTIMATED=0",
    "",
    "===== FROZEN COMPONENT MAP =====",
    "MAPPED_UCCS=645",
    "C_COST_PRIMARY_UCCS=435",
    "H_SERVICE_CORE_UCCS=99",
    f"SOURCE_COUNTS={dict(sorted(source_counts.items()))}",
    f"FACTOR_COUNTS={dict(sorted(factor_counts.items()))}",
    f"FACTOR4_UCC_COUNT={len(factor4)}",
    "",
    "===== OFFICIAL WEIGHTING SEMANTICS =====",
    "QNUM_ANNUAL=4",
    "INTERVIEW_MO_SCOPE_RULE=FROZEN",
    "DIARY_MO_SCOPE=3",
    "DIARY_WEEKLY_TO_QUARTER_MULTIPLIER=13",
    "MTBI_CALENDAR_FILTER=REF_YR_2022_AND_REF_MO_1_TO_12",
    "RECORD_LEVEL_INTERVIEW_DIARY_JOIN=PROHIBITED",
    "",
    "===== SCHEMA =====",
    (
        "FINLWT21_AND_TIMING_FIELDS=PASS"
        if header_pass
        else
        "FINLWT21_AND_TIMING_FIELDS=FAIL"
    ),
    (
        "WTREP01_TO_WTREP44=PASS"
        if header_pass
        else
        "WTREP01_TO_WTREP44=FAIL"
    ),
    (
        "FIVE_PLUS_FOUR_QUARTER_PLAN=PASS"
        if timing_pass
        else
        "FIVE_PLUS_FOUR_QUARTER_PLAN=FAIL"
    ),
    "",
    "===== INFERENCE =====",
    "FINAL_NAIVE_IID_STANDARD_ERRORS=PROHIBITED",
    "BRR_REQUIRED_FOR_FINAL_CEX_INFERENCE=1",
    "BRR_REPLICATE_COUNT=44",
    "",
    "===== IMPLEMENTATION STATE =====",
    "POINT_ESTIMATE_SEMANTICS_FROZEN=1",
    "EXACT_INTEGRATED_ESTIMATOR_IMPLEMENTATION_FROZEN=0",
    "COST_VALUES_AUTHORIZED=0",
    "",
    (
        "E3B3C2_BLS_ESTIMATOR_SEMANTICS_PREFLIGHT=PASS"
        if overall
        else
        "E3B3C2_BLS_ESTIMATOR_SEMANTICS_PREFLIGHT=FAIL"
    ),
    (
        "E3B3C3_OFFICIAL_SAMPLE_CODE_AUDIT_AUTHORIZED=1"
        if overall
        else
        "E3B3C3_OFFICIAL_SAMPLE_CODE_AUDIT_AUTHORIZED=0"
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
