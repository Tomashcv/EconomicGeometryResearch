from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CONTRACT = ROOT / "docs" / "E3A3_sample_support_gate_precommit.md"
THRESH = ROOT / "data" / "metadata" / "E3A3_support_thresholds.tsv"

expected = {
    "CEX": (200, 100),
    "CPS_ASEC": (500, 250),
    "SCF": (100, 50),
}

with THRESH.open(encoding="utf-8") as f:
    rows = list(csv.DictReader(f, delimiter="\t"))

actual = {
    r["survey"]: (
        int(r["min_unique_units"]),
        int(r["min_kish_ess"]),
    )
    for r in rows
}

if actual != expected:
    raise RuntimeError(
        f"threshold mismatch expected={expected} actual={actual}"
    )

text = CONTRACT.read_text(encoding="utf-8")

required = [
    "n_eff = (sum_i w_i)^2 / sum_i(w_i^2)",
    "Thresholds may not be lowered after counts are opened.",
    "AGE_BAND × TENURE",
    "AGE_BAND × TENURE × CHILDREN_STATUS",
    "YOUNG_RENTER = age 25-34, RENTER",
    "YOUNG_OWNER = age 25-34, OWNER",
    "12 / 12 waves pass.",
    "at least 10 / 12 waves pass;",
    "Counts remain closed until exact 2022 schema and code mappings are verified",
]

for token in required:
    if token not in text:
        raise RuntimeError(f"missing contract token: {token}")

print("E3A3_SUPPORT_GATE_PRECOMMIT=PASS")
print("ECONOMIC_VALUES_OPENED=0")
print("PSEUDOCOHORT_COUNTS_OPENED=0")
print("CEX_MIN_UNIQUE=200")
print("CEX_MIN_KISH_ESS=100")
print("CPS_MIN_UNIQUE=500")
print("CPS_MIN_KISH_ESS=250")
print("SCF_MIN_UNIQUE=100")
print("SCF_MIN_KISH_ESS=50")
print("THRESHOLD_MUTATION_AFTER_COUNTS=PROHIBITED")
print("CURRENT_SUPPORT_COUNTS_AUTHORIZED=0")
print("CPS_SCF_SCHEMA_MAPPING_AUDIT_REQUIRED=1")
