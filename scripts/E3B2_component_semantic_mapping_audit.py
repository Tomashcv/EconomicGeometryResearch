from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

DOC = ROOT / "docs/E3B2_component_semantic_mapping_precommit.md"
MAP = ROOT / "data/metadata/E3B2_component_semantic_map.tsv"
RULES = ROOT / "data/metadata/E3B2_semantic_rules.tsv"

OUT = ROOT / "data/metadata/E3B2_component_semantic_mapping_audit.txt"


text = DOC.read_text(encoding="utf-8")

required_tokens = [
    "STATE_CHANGE != COST_INFLATION",
    "GE != REAL_INFLATION",
    "INTERVIEW_ONLY_C_COST_AUTHORIZED = 0",
    "INTEGRATED_CEX_REQUIRED = 1",
    "RESOURCES_PRIMARY_CANDIDATE = HTOTVAL",
    "I_PREVIOUS_YEAR_PRIMARY = 1",
    "ASSET_PRIMARY_K_AUTHORIZED = 0",
    "TURNDOWN_LONGRUN_PRIMARY = 0",
    "D_PRIMARY_BURDEN = PIRTOTAL",
    "HOMEEQ = HOUSES - MRTHEL",
    "HOUSEHOLD_ECONOMIC_VALUES_AUTHORIZED = 0",
]

for token in required_tokens:
    if token not in text:
        raise RuntimeError(
            f"missing semantic-contract token: {token}"
        )


with MAP.open(encoding="utf-8") as f:
    rows = list(
        csv.DictReader(f, delimiter="\t")
    )

if len(rows) != 17:
    raise RuntimeError(
        f"unexpected semantic-map rows={len(rows)}"
    )


def one(component: str, concept: str):
    matches = [
        r for r in rows
        if r["component"] == component
        and r["concept"] == concept
    ]

    if len(matches) != 1:
        raise RuntimeError(
            f"expected one row: {component}/{concept}"
        )

    return matches[0]


if one("C", "C_INTERVIEW_ONLY")["status"] != "PROHIBITED":
    raise RuntimeError(
        "Interview-only consumption cost was not prohibited"
    )

if one("R", "RESOURCES")["source"] != "HTOTVAL":
    raise RuntimeError(
        "Resources candidate mutated"
    )

if one("I", "I_CURRENT")["primary_longrun"] != "NO":
    raise RuntimeError(
        "current labor status improperly set as primary long-run I"
    )

if one("K", "K_CREDIT_DENIAL")["status"] != "MODERN_2016_PLUS":
    raise RuntimeError(
        "SCF credit-denial horizon restriction missing"
    )

if one("D", "D_PAYMENT_BURDEN")["source"] != "PIRTOTAL":
    raise RuntimeError(
        "primary debt burden mutated"
    )


with RULES.open(encoding="utf-8") as f:
    rule_rows = list(
        csv.DictReader(f, delimiter="\t")
    )

rules = {
    r["rule_id"]: r["value"]
    for r in rule_rows
}

required_rules = {
    "STATE_CHANGE_EQUALS_COST_INFLATION": "0",
    "GE_EQUALS_REAL_INFLATION": "0",
    "INTERVIEW_ONLY_C_COST_AUTHORIZED": "0",
    "INTEGRATED_CEX_REQUIRED": "1",
    "HOUSING_EXCLUDED_FROM_C_COST": "1",
    "MORTGAGE_PRINCIPAL_PRIMARY_H_SERVICE": "0",
    "RESOURCES_PRIMARY_CANDIDATE": "HTOTVAL",
    "RESOURCES_FINAL_DEFINITION_FROZEN": "0",
    "I_PREVIOUS_YEAR_PRIMARY": "1",
    "I_CURRENT_STATUS_PRIMARY": "0",
    "ASSET_PRIMARY_K_AUTHORIZED": "0",
    "TURNDOWN_LONGRUN_PRIMARY": "0",
    "FEARDENIAL_LONGRUN_PRIMARY": "0",
    "D_PRIMARY_BURDEN": "PIRTOTAL",
    "D_SECONDARY_LEVERAGE": "DEBT2INC",
    "D_STRESS_DIAGNOSTIC": "LATE60",
    "H_ACCESS_FINAL_FORMULA_FROZEN": "0",
    "HOUSEHOLD_ECONOMIC_VALUES_AUTHORIZED": "0",
}

if rules != required_rules:
    raise RuntimeError(
        f"semantic-rule registry mismatch={rules}"
    )


summary = "\n".join([
    "=" * 100,
    "ECONOMIC GEOMETRY RESEARCH — E3B2 COMPONENT SEMANTIC MAPPING AUDIT",
    "=" * 100,
    "",
    "STATE_CHANGE_EQUALS_COST_INFLATION=0",
    "GE_EQUALS_REAL_INFLATION=0",
    "",
    "INTERVIEW_ONLY_C_COST_AUTHORIZED=0",
    "INTEGRATED_CEX_REQUIRED=1",
    "HOUSING_EXCLUDED_FROM_C_COST=1",
    "",
    "RESOURCES_PRIMARY_CANDIDATE=HTOTVAL",
    "RESOURCES_FINAL_DEFINITION_FROZEN=0",
    "",
    "I_PREVIOUS_YEAR_PRIMARY=1",
    "I_CURRENT_STATUS_PRIMARY=0",
    "",
    "ASSET_PRIMARY_K_AUTHORIZED=0",
    "K_CREDIT_DENIAL_LONGRUN_PRIMARY=0",
    "",
    "D_PRIMARY_BURDEN=PIRTOTAL",
    "D_SECONDARY_LEVERAGE=DEBT2INC",
    "D_STRESS_DIAGNOSTIC=LATE60",
    "",
    "H_SERVICE_ACCESS_SPLIT=PRESERVED",
    "H_ACCESS_FINAL_FORMULA_FROZEN=0",
    "",
    "HOUSEHOLD_ECONOMIC_VALUES_OPENED=0",
    "HOUSEHOLD_ECONOMIC_VALUES_AUTHORIZED=0",
    "REAL_INFLATION_ESTIMATED=0",
    "COMPONENT_WEIGHTS_SELECTED=0",
    "DIMENSIONALITY_SELECTED=0",
    "",
    "E3B2_COMPONENT_SEMANTIC_MAPPING=PASS",
    "E3B3_INTEGRATED_SOURCE_AND_FORMULA_PREFLIGHT_AUTHORIZED=1",
    "",
])

OUT.write_text(
    summary,
    encoding="utf-8",
)

print(summary)
