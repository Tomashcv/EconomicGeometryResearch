from __future__ import annotations

import csv
import hashlib
import re
import zipfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

MAP = ROOT / "data/metadata/E3B3C1_component_ucc_map.tsv"

C2 = ROOT / "data/metadata/E3B3C2_bls_estimator_semantics_audit.txt"
R1 = ROOT / "data/metadata/E3B3C3_R1_R_sample_scope_forensic.txt"
R2 = ROOT / "data/metadata/E3B3C3_R2_official_source_reconciliation.txt"

R_ZIP = ROOT / "data/raw/cex/sample_code/r-ucc.zip"
SAS_ZIP = ROOT / "data/raw/cex/sample_code/sas-ucc.zip"
STATA_ZIP = ROOT / "data/raw/cex/sample_code/stata-ucc.zip"

OUT = ROOT / "data/metadata/E3B3C4_exact_point_estimator_contract_audit.txt"


EXPECTED_SHA = {
    MAP:
        "a6dd2e592d45f0c7c8428a8265d3b857"
        "c615cd842e10241fff06d2a3c06c1e1f",

    C2:
        "7a886cde1b2e0a05fa73b343098486211"
        "df61921598816e4e9b073f835dcee07",

    R1:
        "61e8d95973d331690f740292791545fc49"
        "c7082aa321af57d534988371ec84e1",

    R2:
        "01c3c7b1ebfe4e6fcccb899b18d96a6d3"
        "8f2644943b7e300014edef745e53a29",

    R_ZIP:
        "c2d8021f52b0118e8e73ce743de63cf8"
        "72a2b8c668314f0977193ca54fc46a85",

    SAS_ZIP:
        "ac5cb7c45fe9c3f4902c678661e67e63"
        "e041027cfb0b60df5f09a5177176e758",

    STATA_ZIP:
        "a16f8d1a513e9ad6224613dbe85e5fea"
        "fb8fe8af3b339f99ed55307ed5a73558",
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


def read_zip_text(
    path: Path,
) -> str:

    chunks = []

    with zipfile.ZipFile(path) as zf:

        for name in zf.namelist():

            if name.endswith("/"):
                continue

            suffix = Path(name).suffix.lower()

            if suffix not in {
                ".r",
                ".sas",
                ".do",
                ".txt",
            }:
                continue

            raw = zf.read(name)

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
                    pass

            if decoded is None:
                raise RuntimeError(
                    f"cannot decode {name}"
                )

            chunks.append(decoded)

    return "\n".join(chunks)


r_code = read_zip_text(R_ZIP)
sas_code = read_zip_text(SAS_ZIP)
stata_code = read_zip_text(STATA_ZIP)

all_code = "\n".join([
    r_code,
    sas_code,
    stata_code,
])


# =============================================================================
# Frozen-map invariants
# =============================================================================

with MAP.open(
    encoding="utf-8",
) as f:

    rows = list(
        csv.DictReader(
            f,
            delimiter="\t",
        )
    )


if len(rows) != 645:
    raise RuntimeError(
        f"expected 645 UCCs; got={len(rows)}"
    )


class_counts = Counter(
    r["component_class"]
    for r in rows
)

source_counts = Counter(
    r["source"]
    for r in rows
)

factor_counts = Counter(
    r["factor"]
    for r in rows
)


map_pass = (
    class_counts["C_COST_PRIMARY"] == 435
    and class_counts["H_SERVICE_CORE"] == 99
    and source_counts == Counter({
        "I": 398,
        "D": 247,
    })
    and factor_counts == Counter({
        "1": 642,
        "4": 3,
    })
)


# =============================================================================
# Frozen upstream-result invariants
# =============================================================================

c2_text = C2.read_text(
    encoding="utf-8"
)

r1_text = R1.read_text(
    encoding="utf-8"
)

r2_text = R2.read_text(
    encoding="utf-8"
)


upstream_pass = all(
    token in text
    for token, text in [
        (
            "E3B3C2_BLS_ESTIMATOR_SEMANTICS_PREFLIGHT=PASS",
            c2_text,
        ),
        (
            "E3B3C3_R1_R_SAMPLE_SCOPE_FORENSIC=PASS",
            r1_text,
        ),
        (
            "E3B3C3_R2_OFFICIAL_SOURCE_RECONCILIATION=PASS",
            r2_text,
        ),
    ]
)


# =============================================================================
# Direct official-code formula evidence
# =============================================================================

r_calendar_numerator = bool(
    re.search(
        r"sum\s*\(\s*cost\s*\*\s*finlwt21\s*\)"
        r"\s*/\s*sum\s*\(\s*popwt\s*\)",
        r_code,
        flags=re.I | re.S,
    )
)


r_first_scope = bool(
    re.search(
        r"\(\s*qintrvmo\s*-\s*1\s*\)"
        r"\s*/\s*3"
        r"\s*\*\s*finlwt21"
        r"\s*/\s*4",
        r_code,
        flags=re.I | re.S,
    )
)


r_fifth_scope = bool(
    re.search(
        r"\(\s*4\s*-\s*qintrvmo\s*\)"
        r"\s*/\s*3"
        r"\s*\*\s*finlwt21"
        r"\s*/\s*4",
        r_code,
        flags=re.I | re.S,
    )
)


r_missing_zero = bool(
    re.search(
        r"replace\s*\(\s*cost\s*,"
        r"\s*is\.na\s*\(\s*cost\s*\)"
        r"\s*,\s*0\s*\)",
        r_code,
        flags=re.I | re.S,
    )
)


diary_x13 = bool(
    re.search(
        r"cost\s*\*\s*`?var'?[\s\S]{0,30}\*\s*13"
        r"|"
        r"\(\s*aggexp\s*/\s*aggpop\s*\)\s*\*\s*13"
        r"|"
        r"\*\s*13.{0,100}diary",
        stata_code + "\n" + sas_code,
        flags=re.I | re.S,
    )
)


wtrep_evidence = bool(
    re.search(
        r"wtrep01\s*-\s*wtrep44"
        r"|"
        r"wtrep01-wtrep44",
        sas_code + "\n" + stata_code,
        flags=re.I,
    )
)


# Detect prohibited transformations of COST in the official sample code.
negative_clipping_detected = bool(
    re.search(
        r"abs\s*\(\s*cost\s*\)"
        r"|"
        r"cost\s*=\s*max\s*\(\s*cost\s*,\s*0"
        r"|"
        r"replace\s+cost\s*=\s*0\s+if\s+cost\s*<\s*0",
        all_code,
        flags=re.I,
    )
)


code_pass = all([
    r_calendar_numerator,
    r_first_scope,
    r_fifth_scope,
    r_missing_zero,
    diary_x13,
    wtrep_evidence,
    not negative_clipping_detected,
])


overall = all([
    map_pass,
    upstream_pass,
    code_pass,
])


report = [
    "=" * 100,
    "ECONOMIC GEOMETRY RESEARCH — E3B3C4 EXACT POINT-ESTIMATOR CONTRACT AUDIT",
    "=" * 100,
    "",
    "MICRODATA_DATA_ROWS_PARSED=0",
    "COST_VALUES_READ=0",
    "EXPENDITURE_VALUES_OPENED=0",
    "HOUSEHOLD_ECONOMIC_VALUES_OPENED=0",
    "REAL_INFLATION_ESTIMATED=0",
    "",
    "===== FROZEN MAP =====",
    f"C_COST_PRIMARY_UCCS={class_counts['C_COST_PRIMARY']}",
    f"H_SERVICE_CORE_UCCS={class_counts['H_SERVICE_CORE']}",
    f"SOURCE_COUNTS={dict(sorted(source_counts.items()))}",
    f"FACTOR_COUNTS={dict(sorted(factor_counts.items()))}",
    (
        "FROZEN_UCC_MAP_INVARIANTS=PASS"
        if map_pass
        else
        "FROZEN_UCC_MAP_INVARIANTS=FAIL"
    ),
    "",
    "===== UPSTREAM EVIDENCE =====",
    (
        "UPSTREAM_ESTIMATOR_EVIDENCE=PASS"
        if upstream_pass
        else
        "UPSTREAM_ESTIMATOR_EVIDENCE=FAIL"
    ),
    "",
    "===== DIRECT OFFICIAL-CODE EVIDENCE =====",
    f"INTERVIEW_MEAN_FORMULA={int(r_calendar_numerator)}",
    f"INTERVIEW_FIRST_SCOPE_FORMULA={int(r_first_scope)}",
    f"INTERVIEW_FIFTH_SCOPE_FORMULA={int(r_fifth_scope)}",
    f"MISSING_COST_ZERO_FILL={int(r_missing_zero)}",
    f"DIARY_X13_IMPLEMENTATION={int(diary_x13)}",
    f"WTREP01_TO_WTREP44_IMPLEMENTATION={int(wtrep_evidence)}",
    f"NEGATIVE_COST_CLIPPING_DETECTED={int(negative_clipping_detected)}",
    (
        "DIRECT_CODE_ESTIMATOR_EVIDENCE=PASS"
        if code_pass
        else
        "DIRECT_CODE_ESTIMATOR_EVIDENCE=FAIL"
    ),
    "",
    "===== CONTRACT =====",
    "SOURCE_SPECIFIC_POPULATION_DENOMINATORS=1",
    "ZERO_SPENDERS_INCLUDED_IN_DENOMINATOR=1",
    "POSITIVE_SPENDER_CONDITIONING=PROHIBITED",
    "NEGATIVE_COST=PRESERVE",
    "COST_WINSORIZATION=PROHIBITED",
    "DIARY_ALLOC_FILTER=NONE",
    "HIERARCHY_FACTOR_APPLIED_UCC_LEVEL=1",
    "COMPONENT_SUM_AFTER_UCC_ESTIMATION=1",
    "OBSERVED_EXPENDITURE_CHANGE_EQUALS_INFLATION=0",
    "",
    "BRR_REQUIRED_FOR_FINAL_INFERENCE=1",
    "BRR_COMPONENT_ENGINE_FROZEN=0",
    "NAIVE_IID_STANDARD_ERRORS=PROHIBITED",
    "",
    (
        "POINT_ESTIMATOR_CONTRACT_FROZEN=1"
        if overall
        else
        "POINT_ESTIMATOR_CONTRACT_FROZEN=0"
    ),
    (
        "COST_VALUES_AUTHORIZED=1"
        if overall
        else
        "COST_VALUES_AUTHORIZED=0"
    ),
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    (
        "E3B3C4_EXACT_POINT_ESTIMATOR_CONTRACT=PASS"
        if overall
        else
        "E3B3C4_EXACT_POINT_ESTIMATOR_CONTRACT=FAIL"
    ),
    (
        "E3B4A_FIRST_CEX_POINT_ESTIMATES_AUTHORIZED=1"
        if overall
        else
        "E3B4A_FIRST_CEX_POINT_ESTIMATES_AUTHORIZED=0"
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

if not overall:
    raise SystemExit(1)
