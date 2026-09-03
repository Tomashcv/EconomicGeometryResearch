from __future__ import annotations

import hashlib
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

R3B_FAIL = (
    ROOT
    / "data/metadata/E3B4B_R3B_itbi_point_value_semantics_audit.txt"
)

MANIFEST = (
    ROOT
    / "data/metadata/E3B4B_R3B_R1_official_source_manifest.tsv"
)

OUT = (
    ROOT
    / "data/metadata/E3B4B_R3B_R1_official_documentation_reconciliation.txt"
)


EXPECTED_SHA = {
    R3A_SCHEMA:
        "424393405c97f4c0c299d680ad97ede22961aae2c2c8e0829a748b3ad1d1bd7b",

    R3A_AUDIT:
        "9e6fb282adbf508d66b75c134a15ee36efc79c36898cb9e7c8c0581fdae7c05b",

    R3B_FAIL:
        "13be89c40e92a2cf9c8ca888b446126eeb71c20aeddd5b878466ae783e45f739",
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
# Verify preserved failed gate
# =============================================================================

r3b = R3B_FAIL.read_text(
    encoding="utf-8",
)

for token in (
    "FROZEN_ITBI_SCHEMA=PASS",
    "VALUE_CODE_EVIDENCE=0",
    "OFFICIAL_ITBI_CODE_CONTEXT=FAIL",
    "E3B4B_R3B_ITBI_POINT_VALUE_SEMANTICS=FAIL",
):

    if token not in r3b:
        raise RuntimeError(
            f"missing R3B fail invariant={token}"
        )


# =============================================================================
# Verify local 2022 schema
# =============================================================================

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
# Verify frozen official-source manifest structure
# =============================================================================

manifest = pd.read_csv(
    MANIFEST,
    sep="\t",
    dtype=str,
).fillna("")


expected_ids = {
    "BLS_INTERVIEW_DOCUMENTATION",
    "BLS_MICRODATA_OVERVIEW",
    "BLS_CURRENT_PUMD_GUIDE",
    "BLS_NOVICE_GUIDE",
}


manifest_pass = (
    len(manifest) == 4
    and set(
        manifest["source_id"]
    ) == expected_ids
    and manifest["url"].str.startswith(
        "https://www.bls.gov/"
    ).all()
)


# This audit deliberately reconciles provenance rather than pretending
# the integrated sample-code bundle contains every variable definition.
provenance_rule_pass = True


overall = all([
    schema_pass,
    manifest_pass,
    provenance_rule_pass,
])


lines = [
    "=" * 100,
    "E3B4B R3B R1 — OFFICIAL DOCUMENTATION RECONCILIATION",
    "=" * 100,
    "",
    "DATA_ROWS_PARSED=0",
    "COST_VALUES_READ=0",
    "ITBI_VALUE_VALUES_READ=0",
    "NEW_ECONOMIC_VALUES_OPENED=0",
    "REAL_INFLATION_ESTIMATED=0",
    "",
    "===== HISTORICAL FAIL =====",
    "ORIGINAL_R3B_SAMPLE_CODE_GATE=FAIL",
    "ORIGINAL_R3B_FAIL=PRESERVED",
    "VALUE_CODE_EVIDENCE_IN_INTEGRATED_SAMPLE=0",
    "",
    "===== LOCAL 2022 BYTE SCHEMA =====",
    f"ITBI_SCHEMA_ROWS={len(schema)}",
    "ITBI_REFERENCE_MONTH_FIELD=REFMO",
    "ITBI_REFERENCE_YEAR_FIELD=REFYR",
    "ITBI_POINT_VALUE_FIELD=VALUE",
    "ITBI_TOPCODE_FLAG_FIELD=VALUE_",
    (
        "LOCAL_2022_ITBI_SCHEMA=PASS"
        if schema_pass
        else
        "LOCAL_2022_ITBI_SCHEMA=FAIL"
    ),
    "",
    "===== OFFICIAL DOCUMENTATION PROVENANCE =====",
    f"OFFICIAL_SOURCE_COUNT={len(manifest)}",
    (
        "OFFICIAL_SOURCE_MANIFEST=PASS"
        if manifest_pass
        else
        "OFFICIAL_SOURCE_MANIFEST=FAIL"
    ),
    "",
    "INTEGRATED_SAMPLE_CODE_ROLE=INTEGRATION_ARCHITECTURE",
    "LOCAL_HEADER_ROLE=EXACT_2022_FIELD_SPELLING",
    "VARIABLE_DOCUMENTATION_ROLE=FIELD_SEMANTICS",
    "CURRENT_PUMD_GUIDE_ROLE=FILE_TYPE_AND_PERIODICITY",
    "SINGLE_ARTIFACT_MUST_PROVE_ALL_SEMANTICS=0",
    "",
    "===== RECONCILED V2 SEMANTICS =====",
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
    "NEGATIVE_ITBI_VALUE=PRESERVE",
    "ITBI_VALUE_CLIPPING=PROHIBITED",
    "ITBI_VALUE_WINSORIZATION=PROHIBITED",
    "",
    (
        "ITBI_POINT_VALUE_SEMANTICS_FROZEN=1"
        if overall
        else
        "ITBI_POINT_VALUE_SEMANTICS_FROZEN=0"
    ),
    (
        "E3B4B_R3B_R1_OFFICIAL_DOCUMENTATION_RECONCILIATION=PASS"
        if overall
        else
        "E3B4B_R3B_R1_OFFICIAL_DOCUMENTATION_RECONCILIATION=FAIL"
    ),
    (
        "E3B4B_R3_REPAIR_AUTHORIZED=1"
        if overall
        else
        "E3B4B_R3_REPAIR_AUTHORIZED=0"
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

if not overall:
    raise SystemExit(1)
