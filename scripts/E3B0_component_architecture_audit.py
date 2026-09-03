from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

DOC = ROOT / "docs/E3B0_component_architecture_precommit.md"
ROLES = ROOT / "data/metadata/E3B0_component_roles.tsv"
FORMULAS = ROOT / "data/metadata/E3B0_formula_registry.tsv"

OUT = ROOT / "data/metadata/E3B0_component_architecture_audit.txt"


text = DOC.read_text(encoding="utf-8")


required_tokens = [
    "STATE_CHANGE != COST_INFLATION",
    "C_COST",
    "C_POWER",
    "H_SERVICE",
    "H_ACCESS",
    "K is STATE-SIDE",
    "D is STATE-SIDE",
    "I is STATE-SIDE",
    "No direct record-level joins across surveys.",
    "nominal annual resource requirement",
    "GE_FINAL_INDEX_AUTHORIZED = 0",
    "HOUSEHOLD_ECONOMIC_VALUES_OPENED = 0",
]

for token in required_tokens:
    if token not in text:
        raise RuntimeError(
            f"missing contract token: {token}"
        )


with ROLES.open(encoding="utf-8") as f:
    role_rows = list(
        csv.DictReader(f, delimiter="\t")
    )

if len(role_rows) != 9:
    raise RuntimeError(
        f"unexpected role count={len(role_rows)}"
    )


# K/D/I must not directly enter Real Inflation.
for component in ("K", "D", "I"):

    rows = [
        r for r in role_rows
        if r["component"] == component
    ]

    if len(rows) != 1:
        raise RuntimeError(
            f"unexpected {component} rows"
        )

    if rows[0]["side"] != "STATE":
        raise RuntimeError(
            f"{component} must be STATE-side"
        )

    if (
        rows[0]["direct_real_inflation_admissible"]
        != "NO"
    ):
        raise RuntimeError(
            f"{component} improperly admitted directly "
            "to Real Inflation"
        )


# Consumption cost must be distinct from consumption power.
c_rows = [
    r for r in role_rows
    if r["component"] == "C"
]

if {
    r["subcomponent"]
    for r in c_rows
} != {
    "C_NONHOUSING_COST",
    "C_POWER",
}:
    raise RuntimeError(
        "C cost/power split corrupted"
    )


# Housing service and access must remain separate.
h_rows = [
    r for r in role_rows
    if r["component"] == "H"
]

if {
    r["subcomponent"]
    for r in h_rows
} != {
    "H_SERVICE",
    "H_ACCESS",
}:
    raise RuntimeError(
        "housing split corrupted"
    )


with FORMULAS.open(encoding="utf-8") as f:
    formula_rows = list(
        csv.DictReader(f, delimiter="\t")
    )

formula_ids = {
    r["id"]
    for r in formula_rows
}

required_formula_ids = {
    "STATE_VECTOR",
    "REAL_INFLATION_CANDIDATE",
    "ECONOMIC_POWER_CANDIDATE",
    "EP_CHANGE_IDENTITY",
    "COST_CONSUMPTION_CANDIDATE",
    "C_INFLATION_CANDIDATE",
    "GE_EXPLORATORY",
}

if formula_ids != required_formula_ids:
    raise RuntimeError(
        f"formula registry mismatch={formula_ids}"
    )


summary = "\n".join([
    "=" * 100,
    "ECONOMIC GEOMETRY RESEARCH — E3B0 COMPONENT ARCHITECTURE AUDIT",
    "=" * 100,
    "",
    "STATE_VECTOR_5D=HYPOTHESIS",
    "STATE_CHANGE_EQUALS_INFLATION=0",
    "",
    "C_COST_POWER_SPLIT=PASS",
    "H_SERVICE_ACCESS_SPLIT=PASS",
    "K_STATE_SIDE=PASS",
    "D_STATE_SIDE=PASS",
    "I_STATE_SIDE=PASS",
    "",
    "DIRECT_CROSS_SURVEY_JOIN=PROHIBITED",
    "FINAL_REAL_INFLATION_SCALAR_AUTHORIZED=0",
    "GE_FINAL_INDEX_AUTHORIZED=0",
    "",
    "HOUSEHOLD_ECONOMIC_VALUES_OPENED=0",
    "COMPONENT_WEIGHTS_SELECTED=0",
    "DIMENSIONALITY_SELECTED=0",
    "",
    "E3B0_COMPONENT_ARCHITECTURE=PASS",
    "E3B1_EXACT_COMPONENT_SCHEMA_AUDIT_AUTHORIZED=1",
    "",
])

OUT.write_text(
    summary,
    encoding="utf-8",
)

print(summary)
