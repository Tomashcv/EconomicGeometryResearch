from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MATRIX = ROOT / "data" / "metadata" / "E3A_concept_matrix.tsv"
WAVES = ROOT / "data" / "metadata" / "E3A_scf_wave_plan.tsv"

EXPECTED_SCF_WAVES = [
    1989, 1992, 1995, 1998, 2001, 2004,
    2007, 2010, 2013, 2016, 2019, 2022,
]

REQUIRED_CONCEPTS = {
    "reference_age",
    "tenure",
    "children",
    "consumption_expenditure",
    "household_income",
    "employment_status",
    "financial_assets",
    "total_debt",
    "homeownership",
    "survey_weight",
    "multiple_imputation",
}

with MATRIX.open(encoding="utf-8") as f:
    rows = list(csv.DictReader(f, delimiter="\t"))

concepts = {r["concept"] for r in rows}

missing = sorted(REQUIRED_CONCEPTS - concepts)

if missing:
    raise RuntimeError(f"missing required concepts: {missing}")

with WAVES.open(encoding="utf-8") as f:
    wave_rows = list(csv.DictReader(f, delimiter="\t"))

actual_waves = [int(r["year"]) for r in wave_rows]

if actual_waves != EXPECTED_SCF_WAVES:
    raise RuntimeError(
        f"SCF wave mismatch expected={EXPECTED_SCF_WAVES} actual={actual_waves}"
    )

contract = (
    ROOT / "docs" / "E3A_source_contract.md"
).read_text(encoding="utf-8")

rules = (
    ROOT / "docs" / "E3A_pseudocohort_rules.md"
).read_text(encoding="utf-8")

required_phrases = [
    "must never be directly joined across surveys",
    "No scalar Real Inflation estimate is authorized in E3A",
    "SCF multiple imputation must be respected",
]

for phrase in required_phrases:
    if phrase not in contract:
        raise RuntimeError(f"missing contract phrase: {phrase}")

if "PROHIBITED" not in rules:
    raise RuntimeError("direct-join prohibition absent")

print("E3A_CONTRACT_AUDIT=PASS")
print(f"CONCEPT_ROWS={len(rows)}")
print(f"SCF_WAVES={len(actual_waves)}")
print("DIRECT_CROSS_SURVEY_JOIN=PROHIBITED")
print("REAL_INFLATION_ESTIMATION_AUTHORIZED=0")
print("E3A1_SCHEMA_RECON_AUTHORIZED=1")
