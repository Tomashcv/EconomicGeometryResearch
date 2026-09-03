from __future__ import annotations

from collections import Counter
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

MAP = ROOT / "data/metadata/E3B3C1_component_ucc_map.tsv"

R2_COVERAGE = (
    ROOT
    / "data/metadata/E3B4B_R2_complete_ucc_family_coverage.tsv"
)

R3A_SCHEMA = (
    ROOT
    / "data/metadata/E3B4B_R3A_itbi_2022_exact_schema.tsv"
)

R3A_AUDIT = (
    ROOT
    / "data/metadata/E3B4B_R3A_itbi_2022_exact_schema_audit.txt"
)

R3BR1_AUDIT = (
    ROOT
    / "data/metadata/E3B4B_R3B_R1_official_documentation_reconciliation.txt"
)

CONTRACT_OUT = (
    ROOT
    / "data/metadata/E3B4B_R3_R1_estimator_v2_ucc_source_contract.tsv"
)

AUDIT_OUT = (
    ROOT
    / "data/metadata/E3B4B_R3_R1_repaired_source_family_contract_v2_audit.txt"
)


# =============================================================================
# Upstream frozen invariants
# =============================================================================

r3a_text = R3A_AUDIT.read_text(encoding="utf-8")
r3br1_text = R3BR1_AUDIT.read_text(encoding="utf-8")

for token in (
    "E3B4B_R3A_ITBI_EXACT_SCHEMA=PASS",
    "ITBI_REFERENCE_MONTH_FIELD=REFMO",
    "ITBI_REFERENCE_YEAR_FIELD=REFYR",
    "ITBI_POINT_VALUE_FIELD=VALUE",
):
    if token not in r3a_text:
        raise RuntimeError(f"missing R3A invariant: {token}")

for token in (
    "E3B4B_R3B_R1_OFFICIAL_DOCUMENTATION_RECONCILIATION=PASS",
    "ITBI_POINT_VALUE_SEMANTICS_FROZEN=1",
    "E3B4B_R3_REPAIR_AUTHORIZED=1",
    "ITBI_VALUE_UNDERSCORE_ROLE=TOPCODE_FLAG",
    "ITII_POINT_ESTIMATE_APPEND=PROHIBITED",
):
    if token not in r3br1_text:
        raise RuntimeError(f"missing R3B R1 invariant: {token}")


# =============================================================================
# Exact 2022 ITBI schema
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
# Frozen hierarchy + R2 physical observations
# =============================================================================

mapping = pd.read_csv(
    MAP,
    sep="\t",
    dtype=str,
).fillna("")

coverage = pd.read_csv(
    R2_COVERAGE,
    sep="\t",
    dtype=str,
).fillna("")

if len(mapping) != 645 or mapping["ucc"].nunique() != 645:
    raise RuntimeError("frozen map is not exactly 645 unique UCCs")

if len(coverage) != 645 or coverage["ucc"].nunique() != 645:
    raise RuntimeError("R2 coverage is not exactly 645 unique UCCs")

if Counter(mapping["source"]) != Counter({"I": 398, "D": 247}):
    raise RuntimeError("frozen survey-source counts changed")

merged = mapping.merge(
    coverage[
        [
            "ucc",
            "survey_source",
            "physical_families",
            "physical_family_count",
        ]
    ],
    on="ucc",
    how="left",
    validate="one_to_one",
)

if merged["physical_families"].isna().any():
    raise RuntimeError("incomplete map-to-coverage merge")

if not merged["source"].eq(merged["survey_source"]).all():
    raise RuntimeError("survey-source disagreement")


# =============================================================================
# Repaired exact point-estimator contract
# =============================================================================

rows = []

for _, r in merged.iterrows():

    ucc = r["ucc"]
    source = r["source"]
    physical = r["physical_families"]

    physical_set = (
        set()
        if physical == "NONE"
        else {x for x in physical.split(",") if x}
    )

    if source == "I":

        if "ITBI" in physical_set:
            family = "ITBI"
            value_field = "VALUE"
            month_field = "REFMO"
            year_field = "REFYR"

        else:
            family = "MTBI"
            value_field = "COST"
            month_field = "REF_MO"
            year_field = "REF_YR"

        if "ITII" in physical_set and "ITBI" not in physical_set:
            raise RuntimeError(
                f"ITII-only UCC cannot become point source: {ucc}"
            )

    elif source == "D":

        family = "EXPD"
        value_field = "COST"
        month_field = "NA"
        year_field = "NA"

        if (
            ("DTBD" in physical_set or "DTID" in physical_set)
            and "EXPD" not in physical_set
        ):
            raise RuntimeError(
                f"Diary income-family collision for UCC {ucc}: {physical}"
            )

    else:
        raise RuntimeError(f"unknown survey source {source}")

    released = int(family in physical_set)

    zero_policy = (
        "OBSERVED_RECORDS"
        if released
        else "EMPTY_RELEASED_RECORD_SET_NUMERATOR_ZERO"
    )

    rows.append(
        {
            "ucc": ucc,
            "survey_source": source,
            "estimator_family": family,
            "point_value_field": value_field,
            "reference_month_field": month_field,
            "reference_year_field": year_field,
            "released_2022_record_present": released,
            "zero_record_policy": zero_policy,
            "physical_families_observed": physical,
            "factor": r["factor"],
            "component_class": r["component_class"],
            "primary_component": r["primary_component"],
            "broad_category": r["broad_category"],
            "subcategory": r["subcategory"],
            "leaf_title": r["leaf_title"],
        }
    )

contract = pd.DataFrame(rows)

contract.to_csv(
    CONTRACT_OUT,
    sep="\t",
    index=False,
)


# =============================================================================
# Hard structural gates
# =============================================================================

family_counts = Counter(contract["estimator_family"])

family_pass = (
    family_counts
    == Counter(
        {
            "MTBI": 390,
            "ITBI": 8,
            "EXPD": 247,
        }
    )
)

primary = contract[
    contract["primary_component"].isin(
        ["C_COST", "H_SERVICE"]
    )
].copy()

primary_counts = Counter(primary["estimator_family"])

primary_pass = (
    len(primary) == 534
    and primary_counts
    == Counter(
        {
            "MTBI": 316,
            "ITBI": 3,
            "EXPD": 215,
        }
    )
)

zero = contract[
    contract["released_2022_record_present"] == 0
]

primary_zero = primary[
    primary["released_2022_record_present"] == 0
]

zero_counts = Counter(zero["estimator_family"])

zero_pass = (
    len(zero) == 20
    and len(primary_zero) == 19
    and zero_counts
    == Counter(
        {
            "MTBI": 16,
            "EXPD": 4,
        }
    )
)

factor4 = contract[
    contract["factor"] == "4"
]

factor4_pass = (
    len(factor4) == 3
    and factor4["estimator_family"].eq("ITBI").all()
    and factor4["point_value_field"].eq("VALUE").all()
)

pensions = contract[
    (contract["broad_category"] == "Personal insurance and pensions")
    & (contract["subcategory"] == "Pensions and Social Security")
]

pensions_pass = (
    len(pensions) == 5
    and pensions["estimator_family"].eq("ITBI").all()
    and pensions["point_value_field"].eq("VALUE").all()
)

itbi = contract[
    contract["estimator_family"] == "ITBI"
]

itbi_schema_contract_pass = (
    len(itbi) == 8
    and itbi["point_value_field"].eq("VALUE").all()
    and itbi["reference_month_field"].eq("REFMO").all()
    and itbi["reference_year_field"].eq("REFYR").all()
)

mismatch_count = int(
    (
        (
            contract["estimator_family"] == "ITBI"
        )
        & (
            contract["point_value_field"] != "VALUE"
        )
    ).sum()
)

overall = all(
    [
        schema_pass,
        family_pass,
        primary_pass,
        zero_pass,
        factor4_pass,
        pensions_pass,
        itbi_schema_contract_pass,
        mismatch_count == 0,
    ]
)


# =============================================================================
# Audit
# =============================================================================

lines = [
    "=" * 100,
    "E3B4B R3 R1 — REPAIRED EXACT SOURCE-FAMILY CONTRACT V2",
    "=" * 100,
    "",
    "DATA_ROWS_PARSED=0",
    "COST_VALUES_READ=0",
    "ITBI_VALUE_VALUES_READ=0",
    "NEW_ECONOMIC_VALUES_OPENED=0",
    "REAL_INFLATION_ESTIMATED=0",
    "",
    "===== SOURCE-FAMILY CONTRACT =====",
    f"TOTAL_UCCS={len(contract)}",
    f"MTBI_UCCS={family_counts['MTBI']}",
    f"ITBI_UCCS={family_counts['ITBI']}",
    f"EXPD_UCCS={family_counts['EXPD']}",
    (
        "V2_SOURCE_FAMILY_COUNTS=PASS"
        if family_pass
        else "V2_SOURCE_FAMILY_COUNTS=FAIL"
    ),
    "",
    "===== PRIMARY CONTRACT =====",
    f"PRIMARY_UCCS={len(primary)}",
    f"PRIMARY_MTBI_UCCS={primary_counts['MTBI']}",
    f"PRIMARY_ITBI_UCCS={primary_counts['ITBI']}",
    f"PRIMARY_EXPD_UCCS={primary_counts['EXPD']}",
    (
        "PRIMARY_V2_SOURCE_FAMILY_COUNTS=PASS"
        if primary_pass
        else "PRIMARY_V2_SOURCE_FAMILY_COUNTS=FAIL"
    ),
    "",
    "===== ZERO RELEASED RECORDS =====",
    f"ZERO_RELEASED_RECORD_UCCS={len(zero)}",
    f"ZERO_RECORD_MTBI_UCCS={zero_counts['MTBI']}",
    f"ZERO_RECORD_EXPD_UCCS={zero_counts['EXPD']}",
    f"ZERO_RECORD_ITBI_UCCS={zero_counts['ITBI']}",
    f"PRIMARY_ZERO_RELEASED_RECORD_UCCS={len(primary_zero)}",
    "EMPTY_RELEASED_RECORD_SET_NUMERATOR=0",
    (
        "ZERO_RECORD_CONTRACT=PASS"
        if zero_pass
        else "ZERO_RECORD_CONTRACT=FAIL"
    ),
    "",
    "===== ITBI NORMALIZATION =====",
    "ITBI_POINT_VALUE_FIELD=VALUE",
    "ITBI_REFERENCE_MONTH_FIELD=REFMO",
    "ITBI_REFERENCE_YEAR_FIELD=REFYR",
    "ITBI_VALUE_UNDERSCORE_ROLE=TOPCODE_FLAG",
    "ITII_POINT_ESTIMATE_APPEND=PROHIBITED",
    f"ITBI_SCHEMA_CONTRACT_UCCS={len(itbi)}",
    f"ITBI_SCHEMA_MISMATCH_UCCS={mismatch_count}",
    (
        "ITBI_SCHEMA_CONTRACT=PASS"
        if itbi_schema_contract_pass
        else "ITBI_SCHEMA_CONTRACT=FAIL"
    ),
    "",
    "===== CRITICAL REPAIR SUBSETS =====",
    f"FACTOR4_UCCS={len(factor4)}",
    (
        "FACTOR4_ESTIMATOR_FAMILY=ITBI"
        if factor4_pass
        else "FACTOR4_ESTIMATOR_FAMILY=FAIL"
    ),
    f"PENSIONS_SOCIAL_SECURITY_UCCS={len(pensions)}",
    (
        "PENSIONS_ESTIMATOR_FAMILY=ITBI"
        if pensions_pass
        else "PENSIONS_ESTIMATOR_FAMILY=FAIL"
    ),
    "",
    "===== HISTORICAL STATE =====",
    "ORIGINAL_E3B4B_BENCHMARK_FAIL=PRESERVED",
    "ORIGINAL_E3B4A_V1_RESULTS=PRESERVED",
    "ORIGINAL_R3_SCHEMA_MISMATCH=PRESERVED",
    "ORIGINAL_R3B_SAMPLE_CODE_GATE_FAIL=PRESERVED",
    "",
    "E3B4A_V1_MAGNITUDES_VALIDATED=0",
    "COHORT_POINT_ESTIMATE_INTERPRETATION_AUTHORIZED=0",
    "",
    (
        "ESTIMATOR_V2_SOURCE_FAMILY_CONTRACT_FROZEN=1"
        if overall
        else "ESTIMATOR_V2_SOURCE_FAMILY_CONTRACT_FROZEN=0"
    ),
    "ESTIMATOR_V2_EXECUTION_AUTHORIZED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "",
    (
        "E3B4B_R3_R1_REPAIRED_SOURCE_FAMILY_CONTRACT_V2=PASS"
        if overall
        else "E3B4B_R3_R1_REPAIRED_SOURCE_FAMILY_CONTRACT_V2=FAIL"
    ),
    (
        "E3B4B_R4_CORRECTED_ALL_CU_BENCHMARK_V2_AUTHORIZED=1"
        if overall
        else "E3B4B_R4_CORRECTED_ALL_CU_BENCHMARK_V2_AUTHORIZED=0"
    ),
    "",
]

AUDIT_OUT.write_text(
    "\n".join(lines),
    encoding="utf-8",
)

print("\n".join(lines))

if not overall:
    raise SystemExit(1)
