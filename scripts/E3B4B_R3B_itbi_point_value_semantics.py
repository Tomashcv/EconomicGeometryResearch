from __future__ import annotations

import csv
import hashlib
import re
import zipfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

R3A_SCHEMA = (
    ROOT
    / "data/metadata/E3B4B_R3A_itbi_2022_exact_schema.tsv"
)

R3A_AUDIT = (
    ROOT
    / "data/metadata/E3B4B_R3A_itbi_2022_exact_schema_audit.txt"
)

SAS_ZIP = (
    ROOT
    / "data/raw/cex/sample_code/sas-ucc.zip"
)

STATA_ZIP = (
    ROOT
    / "data/raw/cex/sample_code/stata-ucc.zip"
)

CONTEXT_OUT = (
    ROOT
    / "data/metadata/E3B4B_R3B_official_itbi_code_context.tsv"
)

AUDIT_OUT = (
    ROOT
    / "data/metadata/E3B4B_R3B_itbi_point_value_semantics_audit.txt"
)


EXPECTED_SHA = {
    R3A_SCHEMA:
        "424393405c97f4c0c299d680ad97ede22961aae2c2c8e0829a748b3ad1d1bd7b",

    R3A_AUDIT:
        "9e6fb282adbf508d66b75c134a15ee36efc79c36898cb9e7c8c0581fdae7c05b",

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


# =============================================================================
# Frozen R3A invariants
# =============================================================================

r3a_text = R3A_AUDIT.read_text(
    encoding="utf-8",
)


for token in (
    "DATA_ROWS_PARSED=0",
    "ITBI_REFERENCE_MONTH_FIELD=REFMO",
    "ITBI_REFERENCE_YEAR_FIELD=REFYR",
    "ITBI_POINT_VALUE_FIELD=VALUE",
    "ITBI_2022_SCHEMA_STABLE=PASS",
    "E3B4B_R3A_ITBI_EXACT_SCHEMA=PASS",
):

    if token not in r3a_text:

        raise RuntimeError(
            f"missing R3A invariant={token}"
        )


schema = pd.read_csv(
    R3A_SCHEMA,
    sep="\t",
    dtype=str,
).fillna("")


schema_pass = (
    len(schema) == 5
    and schema["newid_field"].eq("NEWID").all()
    and schema["ucc_field"].eq("UCC").all()
    and schema["reference_month_field"].eq("REFMO").all()
    and schema["reference_year_field"].eq("REFYR").all()
    and schema["point_value_field"].eq("VALUE").all()
    and schema["all_fields"].str.contains(
        r"(?:^|,)VALUE_(?:,|$)",
        regex=True,
    ).all()
)


# =============================================================================
# Official sample-code context extraction
# =============================================================================

def decode_archive(
    language: str,
    archive: Path,
) -> list[dict[str, object]]:

    rows = []

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


            lines = text.splitlines()


            for i, line in enumerate(
                lines,
                start=1,
            ):

                if not re.search(
                    r"\bITBI\b|\bITAB\b|\bVALUE_?\b|\bREFMO\b|\bREFYR\b",
                    line,
                    flags=re.I,
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


                rows.append({
                    "language": language,
                    "member": member,
                    "line": i,
                    "context": context,
                })


    return rows


context_rows = []

context_rows += decode_archive(
    "SAS",
    SAS_ZIP,
)

context_rows += decode_archive(
    "STATA",
    STATA_ZIP,
)


context_df = pd.DataFrame(
    context_rows,
    columns=[
        "language",
        "member",
        "line",
        "context",
    ],
)


context_df.to_csv(
    CONTEXT_OUT,
    sep="\t",
    index=False,
)


all_context = "\n".join(
    context_df["context"]
    .astype(str)
    .tolist()
)


itbi_code_evidence = bool(
    re.search(
        r"\bITBI\b|\bITAB\b",
        all_context,
        flags=re.I,
    )
)


value_code_evidence = bool(
    re.search(
        r"\bVALUE\b",
        all_context,
        flags=re.I,
    )
)


# Search for any code that appears to consume ITII directly
# as part of the point-estimator family.
itii_point_append_detected = bool(
    re.search(
        r"(?:SET|USE|APPEND|MERGE)"
        r"[^\n]{0,150}"
        r"\bITII\b",
        all_context,
        flags=re.I,
    )
)


# VALUE_ is a separate field and must never be selected
# as the numerical point-value field by our contract.
value_neq_value = bool(
    schema["all_fields"].str.contains(
        r"(?:^|,)VALUE(?:,|$)",
        regex=True,
    ).all()
    and schema["all_fields"].str.contains(
        r"(?:^|,)VALUE_(?:,|$)",
        regex=True,
    ).all()
)


overall = all([
    schema_pass,
    itbi_code_evidence,
    value_code_evidence,
    value_neq_value,
    not itii_point_append_detected,
])


lines = [
    "=" * 100,
    "E3B4B R3B — ITBI POINT-VALUE SEMANTICS",
    "=" * 100,
    "",
    "DATA_ROWS_PARSED=0",
    "COST_VALUES_READ=0",
    "ITBI_VALUE_VALUES_READ=0",
    "NEW_ECONOMIC_VALUES_OPENED=0",
    "REAL_INFLATION_ESTIMATED=0",
    "",
    "===== FROZEN 2022 SCHEMA =====",
    f"ITBI_SCHEMA_ROWS={len(schema)}",
    "ITBI_REFERENCE_MONTH_FIELD=REFMO",
    "ITBI_REFERENCE_YEAR_FIELD=REFYR",
    "ITBI_POINT_VALUE_FIELD=VALUE",
    "ITBI_TOPCODE_FLAG_FIELD=VALUE_",
    (
        "FROZEN_ITBI_SCHEMA=PASS"
        if schema_pass
        else
        "FROZEN_ITBI_SCHEMA=FAIL"
    ),
    "",
    "===== OFFICIAL SAMPLE CODE =====",
    f"OFFICIAL_CONTEXT_ROWS={len(context_df)}",
    f"ITBI_OR_ITAB_CODE_EVIDENCE={int(itbi_code_evidence)}",
    f"VALUE_CODE_EVIDENCE={int(value_code_evidence)}",
    f"ITII_DIRECT_POINT_APPEND_DETECTED={int(itii_point_append_detected)}",
    (
        "OFFICIAL_ITBI_CODE_CONTEXT=PASS"
        if (
            itbi_code_evidence
            and value_code_evidence
            and not itii_point_append_detected
        )
        else
        "OFFICIAL_ITBI_CODE_CONTEXT=FAIL"
    ),
    "",
    "===== V2 SEMANTICS =====",
    "MTBI_POINT_VALUE_FIELD=COST",
    "MTBI_REFERENCE_MONTH_FIELD=REF_MO",
    "MTBI_REFERENCE_YEAR_FIELD=REF_YR",
    "",
    "ITBI_POINT_VALUE_FIELD=VALUE",
    "ITBI_REFERENCE_MONTH_FIELD=REFMO",
    "ITBI_REFERENCE_YEAR_FIELD=REFYR",
    "ITBI_VALUE_UNDERSCORE_ROLE=TOPCODE_FLAG",
    "ITBI_VALUE_UNDERSCORE_AS_NUMERIC_VALUE=PROHIBITED",
    "ITII_POINT_ESTIMATE_APPEND=PROHIBITED",
    "",
    "EXPD_POINT_VALUE_FIELD=COST",
    "",
    (
        "ITBI_POINT_VALUE_SEMANTICS_FROZEN=1"
        if overall
        else
        "ITBI_POINT_VALUE_SEMANTICS_FROZEN=0"
    ),
    (
        "E3B4B_R3B_ITBI_POINT_VALUE_SEMANTICS=PASS"
        if overall
        else
        "E3B4B_R3B_ITBI_POINT_VALUE_SEMANTICS=FAIL"
    ),
    (
        "E3B4B_R3_REPAIR_AUTHORIZED=1"
        if overall
        else
        "E3B4B_R3_REPAIR_AUTHORIZED=0"
    ),
    "",
]


AUDIT_OUT.write_text(
    "\n".join(lines),
    encoding="utf-8",
)


print(
    "\n".join(lines)
)


if not overall:
    raise SystemExit(1)
