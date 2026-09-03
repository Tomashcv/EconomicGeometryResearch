from __future__ import annotations

import csv
import hashlib
import re
import zipfile
from collections import Counter
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

INT21 = ROOT / "data/raw/cex/2021/intrvw21.zip"
INT22 = ROOT / "data/raw/cex/2022/intrvw22.zip"
DIA22 = ROOT / "data/raw/cex/2022/diary22.zip"

MAP = ROOT / "data/metadata/E3B3C1_component_ucc_map.tsv"

R2_COVERAGE = (
    ROOT
    / "data/metadata/E3B4B_R2_complete_ucc_family_coverage.tsv"
)

R2_AUDIT = (
    ROOT
    / "data/metadata/E3B4B_R2_complete_ucc_source_family_inventory.txt"
)

SAS_CODE = ROOT / "data/raw/cex/sample_code/sas-ucc.zip"
STATA_CODE = ROOT / "data/raw/cex/sample_code/stata-ucc.zip"

CONTRACT_OUT = (
    ROOT
    / "data/metadata/E3B4B_R3_estimator_v2_ucc_source_contract.tsv"
)

HEADER_OUT = (
    ROOT
    / "data/metadata/E3B4B_R3_source_family_header_audit.tsv"
)

AUDIT = (
    ROOT
    / "data/metadata/E3B4B_R3_exact_source_family_contract_v2.txt"
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

    R2_COVERAGE:
        "df2ae2cc161a44f63ed609c8eb165af94f98315ac53a754de6b8896d1aa2dc34",

    R2_AUDIT:
        "7a4fc4ad634c2a74328a2c8c9213f6b6b7731740aa111154b75e9aac0d410f40",

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


# =============================================================================
# Verify historical R2 FAIL is preserved
# =============================================================================

r2_text = R2_AUDIT.read_text(
    encoding="utf-8",
)

for token in (
    "E3B4B_R2_COMPLETE_SOURCE_FAMILY_INVENTORY=FAIL",
    "ESTIMATOR_V2_FROZEN=0",
    "E3B4A_MAGNITUDES_VALIDATED=0",
):

    if token not in r2_text:
        raise RuntimeError(
            f"missing frozen R2 invariant={token}"
        )


# =============================================================================
# Helpers
# =============================================================================

def find_member(
    archive: Path,
    basename: str,
) -> str:

    with zipfile.ZipFile(archive) as zf:

        matches = [
            x
            for x in zf.namelist()
            if Path(x).name.lower()
            == basename.lower()
        ]

    if len(matches) != 1:
        raise RuntimeError(
            f"{archive.name}: expected exactly one "
            f"{basename}; found={matches}"
        )

    return matches[0]


def header(
    archive: Path,
    basename: str,
) -> tuple[str, list[str]]:

    member = find_member(
        archive,
        basename,
    )

    with zipfile.ZipFile(archive) as zf:
        with zf.open(member) as raw:

            first = raw.readline()

    if not first:
        raise RuntimeError(
            f"empty member={member}"
        )

    fields = next(
        csv.reader([
            first.decode(
                "utf-8-sig",
                errors="strict",
            ).rstrip("\r\n")
        ])
    )

    return (
        member,
        [
            x.strip().upper()
            for x in fields
        ],
    )


def read_code(
    archive: Path,
) -> str:

    chunks: list[str] = []

    with zipfile.ZipFile(archive) as zf:

        for member in zf.namelist():

            if member.endswith("/"):
                continue

            if Path(member).suffix.lower() not in {
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

            chunks.append(text)

    return "\n".join(chunks)


# =============================================================================
# Frozen map + physical 2022 coverage
# =============================================================================

mapping = pd.read_csv(
    MAP,
    sep="\t",
    dtype=str,
).fillna("")


coverage = pd.read_csv(
    R2_COVERAGE,
    sep="\t",
    dtype=str,
).fillna("")


if len(mapping) != 645:
    raise RuntimeError(
        f"map row count={len(mapping)}"
    )


if len(coverage) != 645:
    raise RuntimeError(
        f"coverage row count={len(coverage)}"
    )


if mapping["ucc"].nunique() != 645:
    raise RuntimeError(
        "map UCCs are not unique"
    )


if coverage["ucc"].nunique() != 645:
    raise RuntimeError(
        "coverage UCCs are not unique"
    )


if Counter(mapping["source"]) != Counter({
    "I": 398,
    "D": 247,
}):
    raise RuntimeError(
        "survey-source count mutation"
    )


df = mapping.merge(
    coverage[
        [
            "ucc",
            "survey_source",
            "physical_families",
            "physical_family_count",
        ]
    ],
    on="ucc",
    how="left",
    validate="one_to_one",
)


if df["physical_families"].isna().any():
    raise RuntimeError(
        "coverage merge incomplete"
    )


if not (
    df["source"]
    == df["survey_source"]
).all():

    raise RuntimeError(
        "hierarchy survey source disagrees with R2 coverage"
    )


# =============================================================================
# Freeze estimator family
# =============================================================================

contract_rows = []


for _, row in df.iterrows():

    ucc = row["ucc"]
    source = row["source"]

    physical = row[
        "physical_families"
    ]

    physical_set = (
        set()
        if physical == "NONE"
        else set(
            x
            for x in physical.split(",")
            if x
        )
    )


    if source == "I":

        # Point estimate uses ITBI when the released UCC is
        # physically produced there.
        if "ITBI" in physical_set:

            estimator_family = "ITBI"

        else:

            # All remaining integrated Interview EXPEND UCCs
            # remain MTBI-domain, including zero-record 2022 UCCs.
            estimator_family = "MTBI"


        if (
            "ITII" in physical_set
            and "ITBI" not in physical_set
        ):
            raise RuntimeError(
                f"ITII-only point-source candidate ucc={ucc}"
            )


    elif source == "D":

        estimator_family = "EXPD"

        if (
            ("DTBD" in physical_set)
            or ("DTID" in physical_set)
        ) and "EXPD" not in physical_set:

            raise RuntimeError(
                f"Diary income-family collision ucc={ucc} "
                f"physical={physical}"
            )


    else:

        raise RuntimeError(
            f"unknown survey source={source}"
        )


    released_record_present = int(
        estimator_family
        in physical_set
    )


    zero_record_policy = (
        "OBSERVED_RECORDS"
        if released_record_present
        else
        "EMPTY_RELEASED_RECORD_SET_NUMERATOR_ZERO"
    )


    contract_rows.append({
        "ucc": ucc,
        "survey_source": source,
        "estimator_family":
            estimator_family,
        "released_2022_record_present":
            released_record_present,
        "zero_record_policy":
            zero_record_policy,
        "physical_families_observed":
            physical,
        "factor":
            row["factor"],
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


contract = pd.DataFrame(
    contract_rows
)


if len(contract) != 645:
    raise RuntimeError(
        "contract row-count mutation"
    )


contract.to_csv(
    CONTRACT_OUT,
    sep="\t",
    index=False,
)


family_counts = Counter(
    contract["estimator_family"]
)


primary = contract[
    contract[
        "primary_component"
    ].isin([
        "C_COST",
        "H_SERVICE",
    ])
].copy()


primary_family_counts = Counter(
    primary["estimator_family"]
)


zero_records = contract[
    contract[
        "released_2022_record_present"
    ] == 0
]


primary_zero_records = primary[
    primary[
        "released_2022_record_present"
    ] == 0
]


# =============================================================================
# Critical known ITBI subsets
# =============================================================================

pensions = contract[
    (
        contract["broad_category"]
        == "Personal insurance and pensions"
    )
    & (
        contract["subcategory"]
        == "Pensions and Social Security"
    )
]


factor4 = contract[
    contract["factor"] == "4"
]


pensions_itbi = (
    len(pensions) == 5
    and pensions[
        "estimator_family"
    ].eq("ITBI").all()
)


factor4_itbi = (
    len(factor4) == 3
    and factor4[
        "estimator_family"
    ].eq("ITBI").all()
)


# =============================================================================
# Header-only schema audit
# =============================================================================

I_PLAN = [
    (INT21, "221"),
    (INT22, "222"),
    (INT22, "223"),
    (INT22, "224"),
    (INT22, "231"),
]


D_PLAN = [
    (DIA22, "221"),
    (DIA22, "222"),
    (DIA22, "223"),
    (DIA22, "224"),
]


header_rows = []


def audit_family_header(
    archive: Path,
    quarter: str,
    family: str,
    required_exact: set[str],
    year_aliases: set[str] | None = None,
) -> None:

    member, fields = header(
        archive,
        f"{family.lower()}{quarter}.csv",
    )

    field_set = set(fields)

    missing = sorted(
        required_exact
        - field_set
    )


    year_field = ""

    if year_aliases:

        present = sorted(
            year_aliases
            & field_set
        )

        if len(present) != 1:
            raise RuntimeError(
                f"{member}: expected exactly one year alias "
                f"from {sorted(year_aliases)}; got={present}"
            )

        year_field = present[0]


    if missing:
        raise RuntimeError(
            f"{member}: missing required={missing}"
        )


    header_rows.append({
        "family": family.upper(),
        "archive": archive.name,
        "quarter": quarter,
        "member": member,
        "column_count": len(fields),
        "required_fields_pass": 1,
        "reference_year_field":
            year_field or "NA",
        "header_sha256":
            hashlib.sha256(
                "\t".join(
                    fields
                ).encode("utf-8")
            ).hexdigest(),
    })


for archive, q in I_PLAN:

    audit_family_header(
        archive,
        q,
        "MTBI",
        {
            "NEWID",
            "UCC",
            "COST",
            "REF_MO",
        },
        {
            "REF_YR",
            "REFYR",
        },
    )

    audit_family_header(
        archive,
        q,
        "ITBI",
        {
            "NEWID",
            "UCC",
            "COST",
            "REF_MO",
        },
        {
            "REF_YR",
            "REFYR",
        },
    )


for archive, q in D_PLAN:

    audit_family_header(
        archive,
        q,
        "EXPD",
        {
            "NEWID",
            "UCC",
            "COST",
            "ALLOC",
        },
        None,
    )


header_df = pd.DataFrame(
    header_rows
)


header_df.to_csv(
    HEADER_OUT,
    sep="\t",
    index=False,
)


mtbi_year_fields = sorted(
    header_df.loc[
        header_df["family"]
        == "MTBI",
        "reference_year_field",
    ].unique()
)


itbi_year_fields = sorted(
    header_df.loc[
        header_df["family"]
        == "ITBI",
        "reference_year_field",
    ].unique()
)


header_pass = (
    len(header_df) == 14
    and header_df[
        "required_fields_pass"
    ].eq(1).all()
)


# =============================================================================
# Official sample-code evidence
# =============================================================================

code = (
    read_code(SAS_CODE)
    + "\n"
    + read_code(STATA_CODE)
)


mtab_evidence = bool(
    re.search(
        r"\bMTAB\b|\bMTBI\b",
        code,
        flags=re.I,
    )
)


itab_evidence = bool(
    re.search(
        r"\bITAB\b|\bITBI\b",
        code,
        flags=re.I,
    )
)


expn_evidence = bool(
    re.search(
        r"\bEXPN\b|\bEXPD\b",
        code,
        flags=re.I,
    )
)


# Sample point-estimator code should not require
# appending the ITII multiple-imputation iteration file.
itii_direct_point_append = bool(
    re.search(
        r"(?:append|set|merge|use)"
        r"[^\n]{0,100}\bITII\b",
        code,
        flags=re.I,
    )
)


code_pass = (
    mtab_evidence
    and itab_evidence
    and expn_evidence
    and not itii_direct_point_append
)


# =============================================================================
# Frozen count gates
# =============================================================================

family_count_pass = (
    family_counts
    == Counter({
        "MTBI": 390,
        "ITBI": 8,
        "EXPD": 247,
    })
)


primary_family_count_pass = (
    primary_family_counts
    == Counter({
        "MTBI": 316,
        "ITBI": 3,
        "EXPD": 215,
    })
)


zero_record_pass = (
    len(zero_records) == 20
    and len(primary_zero_records) == 19
)


overall = all([
    family_count_pass,
    primary_family_count_pass,
    zero_record_pass,
    pensions_itbi,
    factor4_itbi,
    header_pass,
    code_pass,
])


# =============================================================================
# Audit
# =============================================================================

lines = [
    "=" * 100,
    "E3B4B R3 — EXACT UCC SOURCE-FAMILY CONTRACT V2",
    "=" * 100,
    "",
    "COST_VALUES_READ=0",
    "NEW_ECONOMIC_VALUES_OPENED=0",
    "REAL_INFLATION_ESTIMATED=0",
    "",
    "===== 645-UCC V2 SOURCE CONTRACT =====",
    f"MTBI_UCCS={family_counts['MTBI']}",
    f"ITBI_UCCS={family_counts['ITBI']}",
    f"EXPD_UCCS={family_counts['EXPD']}",
    (
        "V2_SOURCE_FAMILY_COUNTS=PASS"
        if family_count_pass
        else
        "V2_SOURCE_FAMILY_COUNTS=FAIL"
    ),
    "",
    "===== PRIMARY 534-UCC CONTRACT =====",
    f"PRIMARY_MTBI_UCCS={primary_family_counts['MTBI']}",
    f"PRIMARY_ITBI_UCCS={primary_family_counts['ITBI']}",
    f"PRIMARY_EXPD_UCCS={primary_family_counts['EXPD']}",
    (
        "PRIMARY_V2_SOURCE_FAMILY_COUNTS=PASS"
        if primary_family_count_pass
        else
        "PRIMARY_V2_SOURCE_FAMILY_COUNTS=FAIL"
    ),
    "",
    "===== ZERO RELEASED RECORDS =====",
    f"ZERO_RELEASED_RECORD_UCCS={len(zero_records)}",
    f"PRIMARY_ZERO_RELEASED_RECORD_UCCS={len(primary_zero_records)}",
    "EMPTY_RELEASED_RECORD_SET_NUMERATOR=0",
    (
        "ZERO_RECORD_CONTRACT=PASS"
        if zero_record_pass
        else
        "ZERO_RECORD_CONTRACT=FAIL"
    ),
    "",
    "===== CRITICAL ITBI REPAIR =====",
    f"PENSIONS_SOCIAL_SECURITY_UCCS={len(pensions)}",
    (
        "PENSIONS_ESTIMATOR_FAMILY=ITBI"
        if pensions_itbi
        else
        "PENSIONS_ESTIMATOR_FAMILY=FAIL"
    ),
    f"FACTOR4_UCCS={len(factor4)}",
    (
        "FACTOR4_ESTIMATOR_FAMILY=ITBI"
        if factor4_itbi
        else
        "FACTOR4_ESTIMATOR_FAMILY=FAIL"
    ),
    "",
    "===== HEADER CONTRACT =====",
    f"HEADER_AUDIT_ROWS={len(header_df)}",
    (
        "MTBI_REFERENCE_YEAR_FIELDS="
        + ",".join(mtbi_year_fields)
    ),
    (
        "ITBI_REFERENCE_YEAR_FIELDS="
        + ",".join(itbi_year_fields)
    ),
    (
        "SOURCE_FAMILY_HEADERS=PASS"
        if header_pass
        else
        "SOURCE_FAMILY_HEADERS=FAIL"
    ),
    "",
    "===== OFFICIAL SAMPLE CODE =====",
    f"MTAB_OR_MTBI_POINT_CODE_EVIDENCE={int(mtab_evidence)}",
    f"ITAB_OR_ITBI_POINT_CODE_EVIDENCE={int(itab_evidence)}",
    f"EXPN_OR_EXPD_POINT_CODE_EVIDENCE={int(expn_evidence)}",
    f"ITII_DIRECT_POINT_APPEND_DETECTED={int(itii_direct_point_append)}",
    (
        "OFFICIAL_POINT_CODE_FAMILY_EVIDENCE=PASS"
        if code_pass
        else
        "OFFICIAL_POINT_CODE_FAMILY_EVIDENCE=FAIL"
    ),
    "",
    "===== HISTORICAL STATE =====",
    "E3B4B_ORIGINAL_BENCHMARK_FAIL=PRESERVED",
    "E3B4A_V1_RESULTS=PRESERVED",
    "E3B4A_V1_MAGNITUDES_VALIDATED=0",
    "COHORT_POINT_ESTIMATE_INTERPRETATION_AUTHORIZED=0",
    "",
    (
        "ESTIMATOR_V2_SOURCE_FAMILY_CONTRACT_FROZEN=1"
        if overall
        else
        "ESTIMATOR_V2_SOURCE_FAMILY_CONTRACT_FROZEN=0"
    ),
    "ESTIMATOR_V2_EXECUTION_AUTHORIZED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "",
    (
        "E3B4B_R3_EXACT_SOURCE_FAMILY_CONTRACT_V2=PASS"
        if overall
        else
        "E3B4B_R3_EXACT_SOURCE_FAMILY_CONTRACT_V2=FAIL"
    ),
    (
        "E3B4B_R4_CORRECTED_ALL_CU_BENCHMARK_V2_AUTHORIZED=1"
        if overall
        else
        "E3B4B_R4_CORRECTED_ALL_CU_BENCHMARK_V2_AUTHORIZED=0"
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

if not overall:
    raise SystemExit(1)
