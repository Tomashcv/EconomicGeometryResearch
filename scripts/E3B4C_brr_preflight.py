from __future__ import annotations

import csv
import hashlib
import re
import zipfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

INT21 = ROOT / "data/raw/cex/2021/intrvw21.zip"
INT22 = ROOT / "data/raw/cex/2022/intrvw22.zip"
DIA22 = ROOT / "data/raw/cex/2022/diary22.zip"

SAS_ZIP = (
    ROOT
    / "data/raw/cex/sample_code/sas-ucc.zip"
)

STATA_ZIP = (
    ROOT
    / "data/raw/cex/sample_code/stata-ucc.zip"
)

MANIFEST = (
    ROOT
    / "data/metadata/E3B4C_official_brr_source_manifest.tsv"
)

HEADER_OUT = (
    ROOT
    / "data/metadata/E3B4C_brr_weight_header_audit.tsv"
)

CODE_OUT = (
    ROOT
    / "data/metadata/E3B4C_official_brr_code_context.tsv"
)

AUDIT = (
    ROOT
    / "data/metadata/E3B4C_brr_preflight_audit.txt"
)


EXPECTED_SHA = {
    INT21:
        "9b449829fd10ee71227a3de044e6b6d67e568cc7c02a759dda14e4b0278697f0",

    INT22:
        "c99a2f47c0084b7a88812b34c56a1a288be2798ff010b2b59dcf87e072773e17",

    DIA22:
        "c285e72fd7513c78caa158c75975c5b03e91049a9ffe9ee6d41966dc4ef20963",

    SAS_ZIP:
        "ac5cb7c45fe9c3f4902c678661e67e63e041027cfb0b60df5f09a5177176e758",

    STATA_ZIP:
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


REPLICATES = [
    f"WTREP{i:02d}"
    for i in range(1, 45)
]


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
            f"{archive.name}: {basename}: {matches}"
        )

    return matches[0]


def read_header(
    archive: Path,
    basename: str,
) -> tuple[str, list[str]]:

    name = find_member(
        archive,
        basename,
    )

    with zipfile.ZipFile(archive) as zf:

        with zf.open(name) as raw:
            first = raw.readline()

    if not first:
        raise RuntimeError(
            f"empty member={name}"
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
        name,
        [
            x.strip().upper()
            for x in fields
        ],
    )


# =============================================================================
# Header audit — NO ROWS PARSED
# =============================================================================

PLAN = [
    ("I", INT21, "FMLI", "221"),
    ("I", INT22, "FMLI", "222"),
    ("I", INT22, "FMLI", "223"),
    ("I", INT22, "FMLI", "224"),
    ("I", INT22, "FMLI", "231"),
    ("D", DIA22, "FMLD", "221"),
    ("D", DIA22, "FMLD", "222"),
    ("D", DIA22, "FMLD", "223"),
    ("D", DIA22, "FMLD", "224"),
]


header_rows = []


for survey, archive, family, quarter in PLAN:

    member, fields = read_header(
        archive,
        f"{family.lower()}{quarter}.csv",
    )

    field_set = set(fields)

    missing_reps = [
        x
        for x in REPLICATES
        if x not in field_set
    ]

    unexpected_rep_fields = sorted([
        x
        for x in field_set
        if re.fullmatch(
            r"WTREP\d+",
            x,
        )
        and x not in REPLICATES
    ])

    final_weight_present = (
        "FINLWT21" in field_set
    )

    pass_row = (
        final_weight_present
        and not missing_reps
        and not unexpected_rep_fields
    )

    header_rows.append({
        "survey": survey,
        "archive": archive.name,
        "family": family,
        "quarter": quarter,
        "member": member,
        "column_count": len(fields),
        "finlwt21_present":
            int(final_weight_present),
        "replicate_count":
            sum(
                x in field_set
                for x in REPLICATES
            ),
        "first_replicate_present":
            int(
                "WTREP01"
                in field_set
            ),
        "last_replicate_present":
            int(
                "WTREP44"
                in field_set
            ),
        "missing_replicates":
            ",".join(missing_reps)
            if missing_reps
            else "NONE",
        "unexpected_replicates":
            ",".join(
                unexpected_rep_fields
            )
            if unexpected_rep_fields
            else "NONE",
        "header_gate":
            "PASS"
            if pass_row
            else "FAIL",
        "header_sha256":
            hashlib.sha256(
                "\t".join(fields)
                .encode("utf-8")
            ).hexdigest(),
    })


header_df = pd.DataFrame(
    header_rows
)


header_df.to_csv(
    HEADER_OUT,
    sep="\t",
    index=False,
)


headers_pass = (
    len(header_df) == 9
    and header_df[
        "header_gate"
    ].eq("PASS").all()
    and header_df[
        "replicate_count"
    ].eq(44).all()
)


# =============================================================================
# Official local sample-code context
# =============================================================================

PATTERN = re.compile(
    r"(?:"
    r"WTREP0?1|"
    r"WTREP44|"
    r"WTREP01-WTREP44|"
    r"WTREP01-WTREP44|"
    r"WTREP01|"
    r"REPWT|"
    r"FINLWT21|"
    r"POPWT|"
    r"STDERR|"
    r"STANDARD ERROR|"
    r"SQRT|"
    r"/44|"
    r"\b44\b"
    r")",
    flags=re.I,
)


def decode(
    raw: bytes,
) -> str:

    for enc in (
        "utf-8-sig",
        "utf-8",
        "cp1252",
        "latin-1",
    ):

        try:
            return raw.decode(enc)

        except UnicodeDecodeError:
            continue

    raise RuntimeError(
        "cannot decode source file"
    )


contexts = []


for language, archive in (
    ("SAS", SAS_ZIP),
    ("STATA", STATA_ZIP),
):

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

            text = decode(
                zf.read(member)
            )

            lines = text.splitlines()

            for i, line in enumerate(
                lines,
                start=1,
            ):

                if not PATTERN.search(
                    line
                ):
                    continue

                lo = max(
                    0,
                    i - 3,
                )

                hi = min(
                    len(lines),
                    i + 2,
                )

                context = " || ".join(
                    f"{j + 1}:{lines[j].strip()}"
                    for j in range(
                        lo,
                        hi,
                    )
                )

                contexts.append({
                    "language":
                        language,
                    "member":
                        member,
                    "line":
                        i,
                    "context":
                        context,
                })


code_df = pd.DataFrame(
    contexts,
    columns=[
        "language",
        "member",
        "line",
        "context",
    ],
)


code_df.to_csv(
    CODE_OUT,
    sep="\t",
    index=False,
)


code_text = "\n".join(
    code_df["context"]
    .astype(str)
    .tolist()
)


finlwt_evidence = bool(
    re.search(
        r"\bFINLWT21\b",
        code_text,
        flags=re.I,
    )
)


wtrep_evidence = bool(
    re.search(
        r"\bWTREP01\b",
        code_text,
        flags=re.I,
    )
    and
    re.search(
        r"\bWTREP44\b",
        code_text,
        flags=re.I,
    )
)


repwt_evidence = bool(
    re.search(
        r"\bREPWT",
        code_text,
        flags=re.I,
    )
)


popwt_evidence = bool(
    re.search(
        r"\bPOPWT\b",
        code_text,
        flags=re.I,
    )
)


local_code_pass = all([
    finlwt_evidence,
    wtrep_evidence,
    repwt_evidence,
    popwt_evidence,
])


# =============================================================================
# Official-source manifest structure
# =============================================================================

manifest = pd.read_csv(
    MANIFEST,
    sep="\t",
    dtype=str,
).fillna("")


expected_sources = {
    "BLS_PUMD_GUIDE",
    "BLS_HANDBOOK_CALCULATION",
    "BLS_ANTHOLOGY_2003",
}


manifest_pass = (
    len(manifest) == 3
    and set(
        manifest["source_id"]
    ) == expected_sources
    and manifest[
        "url"
    ].str.startswith(
        "https://www.bls.gov/"
    ).all()
)


overall = all([
    headers_pass,
    local_code_pass,
    manifest_pass,
])


lines = [
    "=" * 100,
    "E3B4C — BRR 44-REPLICATE PREFLIGHT",
    "=" * 100,
    "",
    "MICRODATA_DATA_ROWS_PARSED=0",
    "COST_VALUES_READ=0",
    "ITBI_VALUE_VALUES_READ=0",
    "WTREP_VALUES_READ=0",
    "STANDARD_ERRORS_COMPUTED=0",
    "CONFIDENCE_INTERVALS_COMPUTED=0",
    "",
    "===== WEIGHT HEADERS =====",
    f"FAMILY_HEADER_ROWS={len(header_df)}",
    "FULL_SAMPLE_WEIGHT=FINLWT21",
    "REPLICATE_FIRST=WTREP01",
    "REPLICATE_LAST=WTREP44",
    "BRR_REPLICATE_COUNT=44",
    (
        "ALL_REQUIRED_WEIGHT_HEADERS=PASS"
        if headers_pass
        else
        "ALL_REQUIRED_WEIGHT_HEADERS=FAIL"
    ),
    "",
    "===== LOCAL OFFICIAL SAMPLE CODE =====",
    f"OFFICIAL_CODE_CONTEXT_ROWS={len(code_df)}",
    f"FINLWT21_CODE_EVIDENCE={int(finlwt_evidence)}",
    f"WTREP01_TO_WTREP44_CODE_EVIDENCE={int(wtrep_evidence)}",
    f"REPWT_CODE_EVIDENCE={int(repwt_evidence)}",
    f"POPWT_CODE_EVIDENCE={int(popwt_evidence)}",
    (
        "LOCAL_OFFICIAL_BRR_CODE_EVIDENCE=PASS"
        if local_code_pass
        else
        "LOCAL_OFFICIAL_BRR_CODE_EVIDENCE=FAIL"
    ),
    "",
    "===== OFFICIAL SOURCE PROVENANCE =====",
    f"OFFICIAL_SOURCE_COUNT={len(manifest)}",
    (
        "OFFICIAL_BRR_SOURCE_MANIFEST=PASS"
        if manifest_pass
        else
        "OFFICIAL_BRR_SOURCE_MANIFEST=FAIL"
    ),
    "",
    "===== FROZEN BRR SEMANTICS =====",
    "REPLICATE_NUMERATOR_USES_WTREPr=1",
    "REPLICATE_DENOMINATOR_USES_SAME_WTREPr=1",
    "FULL_SAMPLE_DENOMINATOR_REUSED_FOR_REPLICATES=0",
    "",
    "INTERVIEW_MO_SCOPE_APPLIED_TO_REPLICATE_DENOMINATOR=1",
    "DIARY_X13_APPLIED_WITHIN_EACH_REPLICATE=1",
    "HIERARCHY_FACTOR_APPLIED_WITHIN_EACH_REPLICATE=1",
    "",
    "INTEGRATED_UCC_SUM_WITHIN_REPLICATE=1",
    "BRR_VARIANCE_COMPUTED_AFTER_COMPONENT_INTEGRATION=1",
    "SOURCE_VARIANCE_POSTHOC_SUM=PROHIBITED",
    "",
    "OWNER_RENTER_DIFFERENCE_REPLICATE_DIRECT=1",
    "OWNER_RENTER_DIFFERENCE_SE_INDEPENDENCE_SHORTCUT=PROHIBITED",
    "OWNER_RENTER_RATIO_REPLICATE_DIRECT=1",
    "",
    "BRR_VARIANCE_FORMULA=(1/44)*SUM((THETA_R-THETA)^2)",
    "BRR_SE_FORMULA=SQRT(BRR_VARIANCE)",
    "",
    "NAIVE_IID_STANDARD_ERRORS=PROHIBITED",
    "COHORT_DEFINITION_FIXED_ACROSS_REPLICATES=1",
    "UCC_MAP_FIXED_ACROSS_REPLICATES=1",
    "ESTIMATOR_FAMILY_MAP_FIXED_ACROSS_REPLICATES=1",
    "",
    (
        "E3B4C_BRR_PREFLIGHT=PASS"
        if overall
        else
        "E3B4C_BRR_PREFLIGHT=FAIL"
    ),
    (
        "E3B4C1_EXACT_BRR_ENGINE_CONTRACT_AUTHORIZED=1"
        if overall
        else
        "E3B4C1_EXACT_BRR_ENGINE_CONTRACT_AUTHORIZED=0"
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
