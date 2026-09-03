from __future__ import annotations

import csv
import hashlib
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

INT21 = ROOT / "data/raw/cex/2021/intrvw21.zip"
INT22 = ROOT / "data/raw/cex/2022/intrvw22.zip"
DIA22 = ROOT / "data/raw/cex/2022/diary22.zip"

MAP = ROOT / "data/metadata/E3B3C1_component_ucc_map.tsv"

R1_COVERAGE = (
    ROOT
    / "data/metadata/E3B4B_R1_interview_ucc_file_family_coverage.tsv"
)

R1_AUDIT = (
    ROOT
    / "data/metadata/E3B4B_R1_interview_ucc_file_family_forensic.txt"
)

SAS_CODE = ROOT / "data/raw/cex/sample_code/sas-ucc.zip"
STATA_CODE = ROOT / "data/raw/cex/sample_code/stata-ucc.zip"

AUDIT = (
    ROOT
    / "data/metadata/E3B4B_R2_complete_ucc_source_family_inventory.txt"
)

INVENTORY = (
    ROOT
    / "data/metadata/E3B4B_R2_ucc_bearing_file_inventory.tsv"
)

COVERAGE = (
    ROOT
    / "data/metadata/E3B4B_R2_complete_ucc_family_coverage.tsv"
)

UNRESOLVED = (
    ROOT
    / "data/metadata/E3B4B_R2_unresolved_uccs.tsv"
)

CODE_CONTEXT = (
    ROOT
    / "data/metadata/E3B4B_R2_official_code_file_family_context.tsv"
)


EXPECTED_SHA = {
    INT21:
        "9b449829fd10ee71227a3de044e6b6d67e568cc7c02a759dda14e4b0278697f0",

    INT22:
        "c99a2f47c0084b7a88812b34c56a1a288be2798ff010b2b59dcf87e072773e17",

    DIA22:
        "c285e72fd7513c78caa158c75975c5b03e91049a9ffe9ee6d41966dc4ef20963",

    MAP:
        "a6dd2e592d45f0c7c8428a8265d3b857c615cd842e10241fff06d2a3c06c1e1f",

    R1_COVERAGE:
        "3c7fe8d9993a94baa350de3116272cf72cc95a12e46d3313ac0fead0f4b7f6d5",

    R1_AUDIT:
        "830b5dd924178c57c0c380226f28633a71481462dfc16170d626d2e6c15360f8",

    SAS_CODE:
        "ac5cb7c45fe9c3f4902c678661e67e63e041027cfb0b60df5f09a5177176e758",

    STATA_CODE:
        "a16f8d1a513e9ad6224613dbe85e5feafb8fe8af3b339f99ed55307ed5a73558",
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


for path, expected in EXPECTED_SHA.items():

    actual = sha256(path)

    if actual != expected:
        raise RuntimeError(
            f"SHA mismatch {path}: {actual}"
        )


r1_text = R1_AUDIT.read_text(
    encoding="utf-8",
)

for token in (
    "E3B4B_R1_FILE_FAMILY_COVERAGE_FORENSIC=PASS",
    "MTBI_ONLY_INTERVIEW_ASSUMPTION_DISPROVED=1",
    "PENSIONS_LOCATIONS=ITBI_ONLY",
    "FACTOR4_LOCATIONS=ITBI_ONLY",
):

    if token not in r1_text:
        raise RuntimeError(
            f"missing R1 invariant={token}"
        )


# =============================================================================
# Helpers
# =============================================================================

def normalize_ucc(value: object) -> str:

    x = str(value).strip()

    if x.endswith(".0"):
        x = x[:-2]

    if x.isdigit():
        x = x.zfill(6)

    return x


def parse_member(
    member: str,
) -> tuple[str, str] | None:

    base = Path(member).name.lower()

    m = re.fullmatch(
        r"([a-z0-9_]+?)(\d{3})x?\.csv",
        base,
    )

    if not m:
        return None

    family = m.group(1).upper()
    quarter = m.group(2)

    return family, quarter


def read_header(
    zf: zipfile.ZipFile,
    member: str,
) -> list[str]:

    with zf.open(member) as raw:

        line = raw.readline()

    if not line:
        return []

    return next(
        csv.reader([
            line.decode(
                "utf-8-sig",
                errors="strict",
            ).rstrip("\r\n")
        ])
    )


def read_ucc_column(
    archive: Path,
    member: str,
) -> set[str]:

    with zipfile.ZipFile(archive) as zf:
        with zf.open(member) as raw:

            df = pd.read_csv(
                raw,
                dtype=str,
                usecols=lambda c:
                    c.strip().upper()
                    == "UCC",
                low_memory=False,
            )

    if len(df.columns) != 1:
        raise RuntimeError(
            f"{member}: expected one UCC column"
        )

    col = df.columns[0]

    return {
        normalize_ucc(x)
        for x in df[col].dropna()
        if normalize_ucc(x)
    }


FIELD_PATTERN = re.compile(
    r"(?:"
    r"COST|"
    r"VALUE|"
    r"AMOUNT|"
    r"EXP|"
    r"REF|"
    r"YEAR|"
    r"MONTH|"
    r"QYEAR|"
    r"FINLWT|"
    r"WTREP|"
    r"ALLOC|"
    r"IMPNUM|"
    r"FLAG"
    r")",
    re.I,
)


# =============================================================================
# Scan every relevant UCC-bearing CSV member
# =============================================================================

archive_plan = [
    (
        "I",
        INT21,
        {"221"},
    ),
    (
        "I",
        INT22,
        {"222", "223", "224", "231"},
    ),
    (
        "D",
        DIA22,
        {"221", "222", "223", "224"},
    ),
]


family_uccs: dict[
    tuple[str, str],
    set[str],
] = defaultdict(set)

inventory_rows = []


for survey, archive, allowed_quarters in archive_plan:

    with zipfile.ZipFile(archive) as zf:

        for member in sorted(zf.namelist()):

            if member.endswith("/"):
                continue

            parsed = parse_member(member)

            if parsed is None:
                continue

            family, quarter = parsed

            if quarter not in allowed_quarters:
                continue

            header = read_header(
                zf,
                member,
            )

            upper = [
                x.strip().upper()
                for x in header
            ]

            has_ucc = (
                "UCC" in upper
            )

            if not has_ucc:
                continue

            uccs = read_ucc_column(
                archive,
                member,
            )

            family_uccs[
                (
                    survey,
                    family,
                )
            ] |= uccs

            semantic_fields = [
                x
                for x in upper
                if FIELD_PATTERN.search(x)
            ]

            inventory_rows.append({
                "survey": survey,
                "archive": archive.name,
                "quarter": quarter,
                "family": family,
                "member": member,
                "column_count": len(header),
                "unique_uccs_in_member":
                    len(uccs),
                "semantic_header_fields":
                    ",".join(
                        semantic_fields
                    ),
            })


inventory = pd.DataFrame(
    inventory_rows
)


if inventory.empty:
    raise RuntimeError(
        "no UCC-bearing files detected"
    )


inventory.to_csv(
    INVENTORY,
    sep="\t",
    index=False,
)


# =============================================================================
# Frozen map
# =============================================================================

mapping = pd.read_csv(
    MAP,
    sep="\t",
    dtype=str,
).fillna("")


if len(mapping) != 645:
    raise RuntimeError(
        f"expected 645 UCCs; got={len(mapping)}"
    )


if mapping["ucc"].nunique() != 645:
    raise RuntimeError(
        "mapped UCCs not unique"
    )


if Counter(mapping["source"]) != Counter({
    "I": 398,
    "D": 247,
}):
    raise RuntimeError(
        "source-count mutation"
    )


if Counter(mapping["factor"]) != Counter({
    "1": 642,
    "4": 3,
}):
    raise RuntimeError(
        "factor-count mutation"
    )


# =============================================================================
# Classify all 645 mapped UCCs against all physical families
# =============================================================================

coverage_rows = []


for _, row in mapping.iterrows():

    ucc = row["ucc"]
    survey = row["source"]

    families = sorted([
        family
        for (
            survey_key,
            family
        ), uccs in family_uccs.items()
        if survey_key == survey
        and ucc in uccs
    ])

    coverage_rows.append({
        "ucc": ucc,
        "survey_source": survey,
        "physical_families":
            ",".join(families)
            if families
            else "NONE",
        "physical_family_count":
            len(families),
        "factor": row["factor"],
        "component_class":
            row["component_class"],
        "primary_component":
            row["primary_component"],
        "broad_category":
            row["broad_category"],
        "subcategory":
            row["subcategory"],
        "leaf_title":
            row["leaf_title"],
    })


coverage = pd.DataFrame(
    coverage_rows
)


if len(coverage) != 645:
    raise RuntimeError(
        "coverage row-count mutation"
    )


coverage.to_csv(
    COVERAGE,
    sep="\t",
    index=False,
)


unresolved = coverage[
    coverage[
        "physical_family_count"
    ] == 0
].copy()


unresolved.to_csv(
    UNRESOLVED,
    sep="\t",
    index=False,
)


# =============================================================================
# Prior R1 unresolved sets
# =============================================================================

r1 = pd.read_csv(
    R1_COVERAGE,
    sep="\t",
    dtype=str,
).fillna("")


prior_i_neither = set(
    r1.loc[
        r1["file_family_location"]
        == "NEITHER",
        "ucc",
    ]
)


if len(prior_i_neither) != 16:
    raise RuntimeError(
        f"expected 16 prior I-neither; "
        f"got={len(prior_i_neither)}"
    )


expd_uccs = family_uccs.get(
    (
        "D",
        "EXPD",
    ),
    set(),
)


diary_map_uccs = set(
    mapping.loc[
        mapping["source"] == "D",
        "ucc",
    ]
)


prior_d_absent_expd = (
    diary_map_uccs
    - expd_uccs
)


if len(prior_d_absent_expd) != 4:
    raise RuntimeError(
        f"expected 4 prior D-not-EXPD; "
        f"got={len(prior_d_absent_expd)}"
    )


coverage_lookup = {
    row["ucc"]:
        row["physical_families"]
    for _, row in coverage.iterrows()
}


prior_i_resolved = {
    ucc
    for ucc in prior_i_neither
    if coverage_lookup[ucc]
    != "NONE"
}


prior_d_resolved = {
    ucc
    for ucc in prior_d_absent_expd
    if coverage_lookup[ucc]
    != "NONE"
}


# =============================================================================
# Critical subsets
# =============================================================================

primary = coverage[
    coverage[
        "primary_component"
    ].isin([
        "C_COST",
        "H_SERVICE",
    ])
].copy()


if len(primary) != 534:
    raise RuntimeError(
        f"expected 534 primary UCCs; "
        f"got={len(primary)}"
    )


primary_unresolved = primary[
    primary[
        "physical_family_count"
    ] == 0
].copy()


primary_itbi = primary[
    primary[
        "physical_families"
    ].str.split(",")
    .map(
        lambda xs:
            "ITBI" in xs
    )
].copy()


pensions = coverage[
    (
        coverage["broad_category"]
        == "Personal insurance and pensions"
    )
    & (
        coverage["subcategory"]
        == "Pensions and Social Security"
    )
]


factor4 = coverage[
    coverage["factor"] == "4"
]


known_itbi_pass = (
    len(pensions) == 5
    and pensions[
        "physical_families"
    ].eq("ITBI").all()
    and len(factor4) == 3
    and factor4[
        "physical_families"
    ].eq("ITBI").all()
)


# =============================================================================
# Official sample-code file-family context
# =============================================================================

CODE_PATTERN = re.compile(
    r"\b(?:"
    r"MTBI|MTAB|"
    r"ITBI|ITAB|"
    r"EXPD|EXPN|"
    r"DTBD|DTAB|"
    r"ITII|DTID"
    r")\b",
    re.I,
)


code_rows = []


for language, archive in (
    ("SAS", SAS_CODE),
    ("STATA", STATA_CODE),
):

    with zipfile.ZipFile(archive) as zf:

        for member in zf.namelist():

            if member.endswith("/"):
                continue

            suffix = (
                Path(member)
                .suffix
                .lower()
            )

            if suffix not in {
                ".sas",
                ".do",
                ".txt",
            }:
                continue

            raw = zf.read(member)

            text = None

            for enc in (
                "utf-8-sig",
                "utf-8",
                "cp1252",
                "latin-1",
            ):

                try:
                    text = raw.decode(enc)
                    break

                except UnicodeDecodeError:
                    continue

            if text is None:
                raise RuntimeError(
                    f"cannot decode {member}"
                )

            lines = text.splitlines()

            for i, line in enumerate(
                lines,
                start=1,
            ):

                if not CODE_PATTERN.search(
                    line
                ):
                    continue

                lo = max(
                    0,
                    i - 2,
                )

                hi = min(
                    len(lines),
                    i + 1,
                )

                context = " || ".join(
                    f"{j + 1}:"
                    f"{lines[j].strip()}"
                    for j in range(
                        lo,
                        hi,
                    )
                )

                code_rows.append({
                    "language": language,
                    "member": member,
                    "line": i,
                    "context": context,
                })


code_df = pd.DataFrame(
    code_rows
)


code_df.to_csv(
    CODE_CONTEXT,
    sep="\t",
    index=False,
)


code_text = "\n".join(
    code_df["context"].tolist()
)


itab_code_evidence = bool(
    re.search(
        r"\bITBI\b|\bITAB\b",
        code_text,
        flags=re.I,
    )
)


diary_code_evidence = bool(
    re.search(
        r"\bEXPD\b|\bEXPN\b",
        code_text,
        flags=re.I,
    )
)


# =============================================================================
# Summary metrics
# =============================================================================

i_families = sorted({
    family
    for (
        survey,
        family
    ) in family_uccs
    if survey == "I"
})


d_families = sorted({
    family
    for (
        survey,
        family
    ) in family_uccs
    if survey == "D"
})


i_unresolved = int(
    (
        (
            coverage["survey_source"]
            == "I"
        )
        & (
            coverage[
                "physical_family_count"
            ]
            == 0
        )
    ).sum()
)


d_unresolved = int(
    (
        (
            coverage["survey_source"]
            == "D"
        )
        & (
            coverage[
                "physical_family_count"
            ]
            == 0
        )
    ).sum()
)


primary_unresolved_n = len(
    primary_unresolved
)


# This forensic can PASS even if unresolved UCCs remain.
# Exact estimator V2 is authorized only when primary
# source-family coverage is complete.
forensic_pass = all([
    len(coverage) == 645,
    known_itbi_pass,
    itab_code_evidence,
    diary_code_evidence,
])


v2_contract_authorized = (
    forensic_pass
    and primary_unresolved_n == 0
)


# =============================================================================
# Audit
# =============================================================================

lines = [
    "=" * 100,
    "E3B4B R2 — COMPLETE UCC SOURCE-FAMILY INVENTORY",
    "=" * 100,
    "",
    "COST_VALUES_READ=0",
    "NEW_ECONOMIC_VALUES_OPENED=0",
    "REAL_INFLATION_ESTIMATED=0",
    "",
    "===== DISCOVERED UCC-BEARING FAMILIES =====",
    (
        "INTERVIEW_UCC_FAMILIES="
        + ",".join(i_families)
    ),
    (
        "DIARY_UCC_FAMILIES="
        + ",".join(d_families)
    ),
    f"UCC_BEARING_MEMBER_ROWS={len(inventory)}",
    "",
    "===== COMPLETE MAP COVERAGE =====",
    "FROZEN_UCCS=645",
    f"INTERVIEW_UNRESOLVED_UCCS={i_unresolved}",
    f"DIARY_UNRESOLVED_UCCS={d_unresolved}",
    f"TOTAL_UNRESOLVED_UCCS={len(unresolved)}",
    "",
    "===== PRIOR R1 NEITHER FOLLOW-UP =====",
    "PRIOR_INTERVIEW_NEITHER_UCCS=16",
    (
        "PRIOR_INTERVIEW_NEITHER_NOW_RESOLVED="
        f"{len(prior_i_resolved)}"
    ),
    (
        "PRIOR_INTERVIEW_NEITHER_STILL_UNRESOLVED="
        f"{16 - len(prior_i_resolved)}"
    ),
    "PRIOR_DIARY_NOT_IN_EXPD_UCCS=4",
    (
        "PRIOR_DIARY_NOT_IN_EXPD_NOW_OTHER_FAMILY="
        f"{len(prior_d_resolved)}"
    ),
    (
        "PRIOR_DIARY_STILL_UNRESOLVED="
        f"{4 - len(prior_d_resolved)}"
    ),
    "",
    "===== PRIMARY ESTIMATOR MAP =====",
    "PRIMARY_UCCS=534",
    f"PRIMARY_ITBI_UCCS={len(primary_itbi)}",
    f"PRIMARY_UNRESOLVED_UCCS={primary_unresolved_n}",
    "",
    "===== KNOWN ITBI FINDING REPLICATION =====",
    f"PENSIONS_SOCIAL_SECURITY_UCCS={len(pensions)}",
    (
        "PENSIONS_PHYSICAL_FAMILIES="
        + ",".join(
            sorted(
                pensions[
                    "physical_families"
                ].unique()
            )
        )
    ),
    f"FACTOR4_UCCS={len(factor4)}",
    (
        "FACTOR4_PHYSICAL_FAMILIES="
        + ",".join(
            sorted(
                factor4[
                    "physical_families"
                ].unique()
            )
        )
    ),
    (
        "KNOWN_ITBI_FINDINGS_REPLICATED=PASS"
        if known_itbi_pass
        else
        "KNOWN_ITBI_FINDINGS_REPLICATED=FAIL"
    ),
    "",
    "===== OFFICIAL SAMPLE CODE =====",
    (
        "ITBI_OR_ITAB_CODE_EVIDENCE=PASS"
        if itab_code_evidence
        else
        "ITBI_OR_ITAB_CODE_EVIDENCE=FAIL"
    ),
    (
        "DIARY_EXPD_OR_EXPN_CODE_EVIDENCE=PASS"
        if diary_code_evidence
        else
        "DIARY_EXPD_OR_EXPN_CODE_EVIDENCE=FAIL"
    ),
    "",
    "===== STATE =====",
    "E3B4B_ORIGINAL_FAIL=PRESERVED",
    "E3B4A_ORIGINAL_RESULTS=PRESERVED",
    "ESTIMATOR_V2_FROZEN=0",
    "ESTIMATOR_V2_EXECUTION_AUTHORIZED=0",
    "E3B4A_MAGNITUDES_VALIDATED=0",
    "COHORT_POINT_ESTIMATE_INTERPRETATION_AUTHORIZED=0",
    "",
    (
        "E3B4B_R2_COMPLETE_SOURCE_FAMILY_INVENTORY=PASS"
        if forensic_pass
        else
        "E3B4B_R2_COMPLETE_SOURCE_FAMILY_INVENTORY=FAIL"
    ),
    (
        "E3B4B_R3_EXACT_SOURCE_FAMILY_CONTRACT_AUTHORIZED=1"
        if v2_contract_authorized
        else
        "E3B4B_R3_EXACT_SOURCE_FAMILY_CONTRACT_AUTHORIZED=0"
    ),
    "",
]


AUDIT.write_text(
    "\n".join(lines),
    encoding="utf-8",
)

print(
    "\n".join(lines)
)

if not forensic_pass:
    raise SystemExit(1)
