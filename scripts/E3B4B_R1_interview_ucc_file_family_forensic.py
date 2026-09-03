from __future__ import annotations

import csv
import hashlib
import zipfile
from collections import Counter
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

INT21 = ROOT / "data/raw/cex/2021/intrvw21.zip"
INT22 = ROOT / "data/raw/cex/2022/intrvw22.zip"
DIA22 = ROOT / "data/raw/cex/2022/diary22.zip"

MAP = ROOT / "data/metadata/E3B3C1_component_ucc_map.tsv"

BENCH = (
    ROOT
    / "data/results/E3B4B_2022_all_cu_major_category_benchmark.tsv"
)

AUDIT = (
    ROOT
    / "data/metadata/E3B4B_R1_interview_ucc_file_family_forensic.txt"
)

COVERAGE = (
    ROOT
    / "data/metadata/E3B4B_R1_interview_ucc_file_family_coverage.tsv"
)

SUMMARY = (
    ROOT
    / "data/metadata/E3B4B_R1_file_family_category_summary.tsv"
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

    BENCH:
        "42cf805879f0ad9746e9f6bacfbc207cf531d09aac8b12da2430dd24a886eb14",
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
            f"{archive.name}: expected one "
            f"{basename}; found={matches}"
        )

    return matches[0]


def normalize_ucc(
    value: str,
) -> str:

    x = (
        str(value)
        .strip()
    )

    if x.endswith(".0"):
        x = x[:-2]

    if x.isdigit():
        x = x.zfill(6)

    return x


def read_ucc_set(
    archive: Path,
    basename: str,
) -> set[str]:

    member = find_member(
        archive,
        basename,
    )

    with zipfile.ZipFile(archive) as zf:
        with zf.open(member) as f:

            df = pd.read_csv(
                f,
                dtype=str,
                usecols=lambda c:
                    c.strip().upper()
                    == "UCC",
                low_memory=False,
            )

    if len(df.columns) != 1:
        raise RuntimeError(
            f"{member}: UCC column unavailable"
        )

    col = df.columns[0]

    return {
        normalize_ucc(x)
        for x in df[col].dropna()
        if normalize_ucc(x)
    }


# =============================================================================
# Frozen hierarchy map
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


i_map = mapping[
    mapping["source"] == "I"
].copy()

d_map = mapping[
    mapping["source"] == "D"
].copy()


if len(i_map) != 398:
    raise RuntimeError(
        f"expected 398 Interview UCCs; got={len(i_map)}"
    )


if len(d_map) != 247:
    raise RuntimeError(
        f"expected 247 Diary UCCs; got={len(d_map)}"
    )


# =============================================================================
# Physical file-family UCC presence
# =============================================================================

I_PLAN = [
    (INT21, "221"),
    (INT22, "222"),
    (INT22, "223"),
    (INT22, "224"),
    (INT22, "231"),
]


mtbi_union: set[str] = set()
itbi_union: set[str] = set()


for archive, q in I_PLAN:

    mtbi_union |= read_ucc_set(
        archive,
        f"mtbi{q}.csv",
    )

    itbi_union |= read_ucc_set(
        archive,
        f"itbi{q}.csv",
    )


expd_union: set[str] = set()


for q in (
    "221",
    "222",
    "223",
    "224",
):

    expd_union |= read_ucc_set(
        DIA22,
        f"expd{q}.csv",
    )


# =============================================================================
# Classify every frozen Interview UCC
# =============================================================================

rows = []


for _, r in i_map.iterrows():

    ucc = r["ucc"]

    in_mtbi = (
        ucc in mtbi_union
    )

    in_itbi = (
        ucc in itbi_union
    )

    if in_mtbi and in_itbi:
        location = "BOTH"

    elif in_mtbi:
        location = "MTBI_ONLY"

    elif in_itbi:
        location = "ITBI_ONLY"

    else:
        location = "NEITHER"

    rows.append({
        "ucc": ucc,
        "file_family_location": location,
        "in_mtbi": int(in_mtbi),
        "in_itbi": int(in_itbi),
        "factor": r["factor"],
        "component_class":
            r["component_class"],
        "primary_component":
            r["primary_component"],
        "broad_category":
            r["broad_category"],
        "subcategory":
            r["subcategory"],
        "leaf_title":
            r["leaf_title"],
    })


coverage = pd.DataFrame(
    rows
)


if len(coverage) != 398:
    raise RuntimeError(
        "Interview coverage row-count mismatch"
    )


if coverage["ucc"].nunique() != 398:
    raise RuntimeError(
        "Interview UCC duplication"
    )


coverage.to_csv(
    COVERAGE,
    sep="\t",
    index=False,
)


location_counts = Counter(
    coverage[
        "file_family_location"
    ]
)


# =============================================================================
# Special subsets
# =============================================================================

pensions = coverage[
    (
        coverage["broad_category"]
        == "Personal insurance and pensions"
    )
    & (
        coverage["subcategory"]
        == "Pensions and Social Security"
    )
].copy()


life_insurance = coverage[
    (
        coverage["broad_category"]
        == "Personal insurance and pensions"
    )
    & (
        coverage["subcategory"]
        == "Life and other personal insurance"
    )
].copy()


factor4 = coverage[
    coverage["factor"] == "4"
].copy()


misc = coverage[
    coverage["broad_category"]
    == "Miscellaneous"
].copy()


# =============================================================================
# Diary coverage sanity
# =============================================================================

d_present = sum(
    ucc in expd_union
    for ucc in d_map["ucc"]
)

d_missing = (
    len(d_map)
    - d_present
)


# =============================================================================
# Existing benchmark residual identity
# =============================================================================

bench = pd.read_csv(
    BENCH,
    sep="\t",
)


pip = bench[
    bench["category"]
    == "Personal insurance and pensions"
].iloc[0]


pip_official = float(
    pip["official_mean_usd"]
)

pip_estimate = float(
    pip["estimate_usd"]
)

pip_gap = (
    pip_official
    - pip_estimate
)


PUBLISHED_LIFE = 519.20
PUBLISHED_PENSIONS = 8222.80


life_identity = (
    abs(
        pip_estimate
        - PUBLISHED_LIFE
    )
    <= 0.02
)


pension_gap_identity = (
    abs(
        pip_gap
        - PUBLISHED_PENSIONS
    )
    <= 0.02
)


# =============================================================================
# Category/file-family summary
# =============================================================================

summary = (
    coverage
    .groupby(
        [
            "broad_category",
            "file_family_location",
        ],
        as_index=False,
    )
    .size()
    .rename(
        columns={
            "size": "ucc_count"
        }
    )
)


summary.to_csv(
    SUMMARY,
    sep="\t",
    index=False,
)


classification_pass = (
    sum(location_counts.values())
    == 398
)


diary_pass = (
    d_present + d_missing
    == 247
)


residual_pass = (
    life_identity
    and pension_gap_identity
)


mtbi_only_assumption_disproved = (
    location_counts[
        "ITBI_ONLY"
    ] > 0
    or location_counts[
        "BOTH"
    ] > 0
)


overall = all([
    classification_pass,
    diary_pass,
    residual_pass,
])


lines = [
    "=" * 100,
    "E3B4B R1 — INTERVIEW UCC FILE-FAMILY COVERAGE FORENSIC",
    "=" * 100,
    "",
    "REAL_INFLATION_ESTIMATED=0",
    "ESTIMATOR_MUTATION_AUTHORIZED=0",
    "",
    "===== FROZEN MAP =====",
    "INTERVIEW_MAPPED_UCCS=398",
    "DIARY_MAPPED_UCCS=247",
    "",
    "===== INTERVIEW PHYSICAL COVERAGE =====",
    f"MTBI_ONLY_UCCS={location_counts['MTBI_ONLY']}",
    f"ITBI_ONLY_UCCS={location_counts['ITBI_ONLY']}",
    f"BOTH_UCCS={location_counts['BOTH']}",
    f"NEITHER_UCCS={location_counts['NEITHER']}",
    (
        "INTERVIEW_UCC_CLASSIFICATION=PASS"
        if classification_pass
        else
        "INTERVIEW_UCC_CLASSIFICATION=FAIL"
    ),
    "",
    "===== SPECIAL SUBSETS =====",
    f"PENSIONS_SOCIAL_SECURITY_UCCS={len(pensions)}",
    (
        "PENSIONS_LOCATIONS="
        + ",".join(
            sorted(
                pensions[
                    "file_family_location"
                ].unique()
            )
        )
    ),
    f"LIFE_INSURANCE_UCCS={len(life_insurance)}",
    (
        "LIFE_INSURANCE_LOCATIONS="
        + ",".join(
            sorted(
                life_insurance[
                    "file_family_location"
                ].unique()
            )
        )
    ),
    f"FACTOR4_UCCS={len(factor4)}",
    (
        "FACTOR4_LOCATIONS="
        + ",".join(
            sorted(
                factor4[
                    "file_family_location"
                ].unique()
            )
        )
    ),
    f"MISCELLANEOUS_INTERVIEW_UCCS={len(misc)}",
    "",
    "===== DIARY SANITY =====",
    f"DIARY_UCCS_PRESENT_IN_EXPD={d_present}",
    f"DIARY_UCCS_NOT_PRESENT_IN_EXPD={d_missing}",
    "",
    "===== BENCHMARK RESIDUAL IDENTITY =====",
    f"PIP_OFFICIAL_USD={pip_official:.10f}",
    f"PIP_CURRENT_ESTIMATE_USD={pip_estimate:.10f}",
    f"PIP_RESIDUAL_USD={pip_gap:.10f}",
    f"PUBLISHED_LIFE_INSURANCE_USD={PUBLISHED_LIFE:.10f}",
    f"PUBLISHED_PENSIONS_SOCSEC_USD={PUBLISHED_PENSIONS:.10f}",
    (
        "CURRENT_PIP_EQUALS_PUBLISHED_LIFE_INSURANCE=PASS"
        if life_identity
        else
        "CURRENT_PIP_EQUALS_PUBLISHED_LIFE_INSURANCE=FAIL"
    ),
    (
        "PIP_RESIDUAL_EQUALS_PUBLISHED_PENSIONS_SOCSEC=PASS"
        if pension_gap_identity
        else
        "PIP_RESIDUAL_EQUALS_PUBLISHED_PENSIONS_SOCSEC=FAIL"
    ),
    "",
    (
        "MTBI_ONLY_INTERVIEW_ASSUMPTION_DISPROVED=1"
        if mtbi_only_assumption_disproved
        else
        "MTBI_ONLY_INTERVIEW_ASSUMPTION_DISPROVED=0"
    ),
    "",
    "E3B4B_ORIGINAL_FAIL=PRESERVED",
    "E3B4A_MAGNITUDES_VALIDATED=0",
    "COHORT_POINT_ESTIMATE_INTERPRETATION_AUTHORIZED=0",
    "",
    (
        "E3B4B_R1_FILE_FAMILY_COVERAGE_FORENSIC=PASS"
        if overall
        else
        "E3B4B_R1_FILE_FAMILY_COVERAGE_FORENSIC=FAIL"
    ),
    (
        "E3B4B_R2_SOURCE_FAMILY_ESTIMATOR_REPAIR_PREFLIGHT_AUTHORIZED=1"
        if overall and mtbi_only_assumption_disproved
        else
        "E3B4B_R2_SOURCE_FAMILY_ESTIMATOR_REPAIR_PREFLIGHT_AUTHORIZED=0"
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
