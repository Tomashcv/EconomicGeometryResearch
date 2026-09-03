from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FAILED = ROOT / "data" / "metadata" / "E3A1_attempt1_transport_403.txt"
CONTRACT = ROOT / "docs" / "E3A1R1_transport_repair.md"
EVIDENCE = ROOT / "data" / "metadata" / "E3A1R1_cex_variable_evidence.tsv"
SOURCES = ROOT / "data" / "metadata" / "E3A1R1_official_sources.tsv"

required_variables = {
    "NEWID",
    "FINLWT21",
    "AGE_REF",
    "FAM_SIZE",
    "PERSLT18",
    "CUTENURE",
}

if not FAILED.exists():
    raise RuntimeError("failed E3A1 attempt log is not preserved")

failed_text = FAILED.read_text(
    encoding="utf-8",
    errors="replace",
)

required_failure_evidence = [
    "ACQUIRE=PUMD_dictionary",
    "403",
    "CalledProcessError",
]

for token in required_failure_evidence:
    if token not in failed_text:
        raise RuntimeError(
            f"missing failed-attempt evidence: {token}"
        )

contract = CONTRACT.read_text(encoding="utf-8")

required_contract_tokens = [
    "TRANSPORT_FAILURE",
    "CEX_2022_EXACT_HEADER_VERIFICATION = DEFERRED",
    "ABORTED_TRANSPORT_403",
    "No cohort counts are authorized",
]

for token in required_contract_tokens:
    if token not in contract:
        raise RuntimeError(
            f"missing repair-contract token: {token}"
        )

with EVIDENCE.open(encoding="utf-8") as f:
    rows = list(csv.DictReader(f, delimiter="\t"))

actual_variables = {row["variable"] for row in rows}

if actual_variables != required_variables:
    raise RuntimeError(
        f"CEX variable evidence mismatch "
        f"expected={sorted(required_variables)} "
        f"actual={sorted(actual_variables)}"
    )

for row in rows:
    if row["exact_2022_header_status"] != "DEFERRED":
        raise RuntimeError(
            "repair may not claim exact 2022 CEX header verification"
        )

with SOURCES.open(encoding="utf-8") as f:
    source_rows = list(csv.DictReader(f, delimiter="\t"))

if len(source_rows) < 7:
    raise RuntimeError("official source provenance incomplete")

print("E3A1_ORIGINAL_EXECUTION=ABORTED_TRANSPORT_403")
print("ECONOMIC_VALUES_OPENED=0")
print("COHORT_COUNTS_OPENED=0")
print("CEX_CANDIDATE_VARIABLES_PRESERVED=1")
print("CEX_2022_EXACT_HEADER_VERIFIED=0")
print("CEX_2022_EXACT_HEADER_STATUS=DEFERRED")
print("E3A1R1_TRANSPORT_REPAIR=PASS")
print("HEADER_ONLY_ANCHOR_RECON_AUTHORIZED=1")
print("PSEUDOCOHORT_COUNTS_AUTHORIZED=0")
print("REAL_INFLATION_ESTIMATION_AUTHORIZED=0")
