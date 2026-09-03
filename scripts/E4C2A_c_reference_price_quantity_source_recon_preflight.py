from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

CONTRACT = (
    ROOT
    / "data/metadata/E4C2A_c_reference_price_quantity_source_recon_contract.json"
)

OUT_SOURCES = (
    ROOT
    / "data/results/E4C2A_official_c_source_registry.tsv"
)

OUT_SUPPORT = (
    ROOT
    / "data/results/E4C2A_c_architecture_source_support_matrix.tsv"
)

OUT_NEXT = (
    ROOT
    / "data/results/E4C2A_next_metadata_audit_requirements.tsv"
)

AUDIT = (
    ROOT
    / "data/metadata/E4C2A_c_reference_price_quantity_source_recon_preflight_audit.txt"
)


contract = json.loads(
    CONTRACT.read_text(
        encoding="utf-8"
    )
)


source_rows = [
    {
        "source_id": "BLS_CE_CPI_CONCORDANCE",
        "agency": "BLS",
        "official_public": "YES",
        "documentation_url":
            "https://www.bls.gov/cpi/additional-resources/ce-cpi-concordance.htm",
        "source_type": "CLASSIFICATION_CONCORDANCE",
        "capability": "CE_UCC_TO_CPI_ELI",
        "2022_specific_lineage": "JANUARY_2022_WEIGHT_UPDATE_ARCHIVE_DOCUMENTED",
        "numeric_values_opened": "NO",
        "recon_status": "STRONG_LINEAGE",
    },
    {
        "source_id": "BLS_CPI_ITEM_AGGREGATION",
        "agency": "BLS",
        "official_public": "YES",
        "documentation_url":
            "https://www.bls.gov/cpi/additional-resources/cpi-item-aggregation.htm",
        "source_type": "CLASSIFICATION_HIERARCHY",
        "capability": "PUBLIC_ITEM_STRATUM_STRUCTURE",
        "2022_specific_lineage": "NOT_VALUE_DEPENDENT",
        "numeric_values_opened": "NO",
        "recon_status": "STRONG_LINEAGE",
    },
    {
        "source_id": "BLS_CPI_PUBLICATION_LEVEL",
        "agency": "BLS",
        "official_public": "YES",
        "documentation_url":
            "https://www.bls.gov/cpi/additional-resources/index-publication-level.htm",
        "source_type": "SERIES_PUBLICATION_METADATA",
        "capability": "IDENTIFY_PUBLIC_CPI_ITEM_INDEX_COVERAGE",
        "2022_specific_lineage": "PUBLIC_SERIES_METADATA",
        "numeric_values_opened": "NO",
        "recon_status": "STRONG_LINEAGE",
    },
    {
        "source_id": "BLS_CPI_AVERAGE_PRICE_LIST",
        "agency": "BLS",
        "official_public": "YES",
        "documentation_url":
            "https://www.bls.gov/cpi/additional-resources/average-price-publication-list.htm",
        "source_type": "AVERAGE_PRICE_PUBLICATION_METADATA",
        "capability": "SELECT_PHYSICAL_UNIT_AVERAGE_PRICES",
        "2022_specific_lineage": "SERIES_EXISTENCE_ONLY",
        "numeric_values_opened": "NO",
        "recon_status": "PARTIAL_ONLY",
    },
    {
        "source_id": "BLS_CE_PCE_CONCORDANCE",
        "agency": "BLS",
        "official_public": "YES",
        "documentation_url":
            "https://www.bls.gov/cex/cecomparison/pce_profile.htm",
        "source_type": "CLASSIFICATION_CONCORDANCE",
        "capability": "CE_UCC_TO_PCE_PRODUCT_CATEGORY",
        "2022_specific_lineage": "CONCORDANCE_METHOD_DOCUMENTED",
        "numeric_values_opened": "NO",
        "recon_status": "STRONG_LINEAGE",
    },
    {
        "source_id": "BEA_PCE_PRICE_QUANTITY_METHODS",
        "agency": "BEA",
        "official_public": "YES",
        "documentation_url":
            "https://www.bea.gov/index.php/help/faq/521",
        "source_type": "PRICE_QUANTITY_METHOD_DOCUMENTATION",
        "capability": "DETAILED_PCE_DEFLATION_QUANTITY_EXTRAPOLATION_DIRECT_VALUATION",
        "2022_specific_lineage": "METHOD_REFERENCE",
        "numeric_values_opened": "NO",
        "recon_status": "STRONG_METHOD_REFERENCE",
    },
    {
        "source_id": "BEA_REGIONAL_PRICE_PARITIES",
        "agency": "BEA",
        "official_public": "YES",
        "documentation_url":
            "https://www.bea.gov/resources/methodologies/rpp",
        "source_type": "SPATIAL_PRICE_LEVEL_METHOD",
        "capability": "GEOGRAPHIC_SAME_YEAR_PRICE_LEVEL_COMPARISON",
        "2022_specific_lineage": "2022_RPP_EXISTS",
        "numeric_values_opened": "NO",
        "recon_status": "SPATIAL_SENSITIVITY_ONLY",
    },
    {
        "source_id": "CENSUS_THREE_PARAMETER_EQUIVALENCE_SCALE",
        "agency": "CENSUS",
        "official_public": "YES",
        "documentation_url":
            "https://www.census.gov/topics/income-poverty/income-inequality/about/metrics/equivalence.html",
        "source_type": "HOUSEHOLD_COMPOSITION_ADJUSTMENT_METHOD",
        "capability": "OFFICIAL_THREE_PARAMETER_EQUIVALENCE_ADJUSTMENT",
        "2022_specific_lineage": "FORMULA_NOT_YEAR_SPECIFIC",
        "numeric_values_opened": "NO",
        "recon_status": "OFFICIAL_CANDIDATE_SENSITIVITY",
    },
]

sources = pd.DataFrame(source_rows)

if len(sources) != 8:
    raise RuntimeError("official source registry shape mismatch")

if not (sources["official_public"] == "YES").all():
    raise RuntimeError("all E4C2A registered sources must be official/public")

if not (sources["numeric_values_opened"] == "NO").all():
    raise RuntimeError("E4C2A must not open numeric source values")


support_rows = [
    {
        "candidate_id": "C_A",
        "candidate_family": "REFERENCE_BUNDLE_AFFORDABILITY",
        "classification_lineage_feasible": "YES",
        "price_source_lineage_feasible": "YES",
        "same_year_cross_sectional_identification_resolved": "NO",
        "equivalence_policy_resolved": "NO",
        "K_D_I_overlap_resolved": "NOT_PRIMARY_BLOCKER",
        "architecture_selected": "NO",
    },
    {
        "candidate_id": "C_B",
        "candidate_family": "REAL_CONSUMPTION_COMMAND",
        "classification_lineage_feasible": "YES",
        "price_source_lineage_feasible": "YES",
        "same_year_cross_sectional_identification_resolved": "POTENTIALLY",
        "equivalence_policy_resolved": "NO",
        "K_D_I_overlap_resolved": "NOT_PRIMARY_BLOCKER",
        "architecture_selected": "NO",
    },
    {
        "candidate_id": "C_C",
        "candidate_family":
            "EXPENDITURE_BURDEN_WITH_PREDECLARED_RESOURCE_DENOMINATOR",
        "classification_lineage_feasible": "NOT_REQUIRED_FOR_CORE_RATIO",
        "price_source_lineage_feasible": "OPTIONAL",
        "same_year_cross_sectional_identification_resolved": "POTENTIALLY",
        "equivalence_policy_resolved": "NO",
        "K_D_I_overlap_resolved": "NO",
        "architecture_selected": "NO",
    },
]

support = pd.DataFrame(support_rows)

if len(support) != 3:
    raise RuntimeError("architecture support matrix shape mismatch")

if (support["architecture_selected"] != "NO").any():
    raise RuntimeError("E4C2A must not select C architecture")


next_rows = [
    {
        "item": "FROZEN_C_UCC_UNIVERSE",
        "required": "YES",
        "may_read_numeric_economic_values": "NO",
        "purpose":
            "Identify the exact UCC universe already used by frozen C_COST.",
    },
    {
        "item": "JAN_2022_CE_UCC_TO_CPI_ELI_CONCORDANCE_SCHEMA",
        "required": "YES",
        "may_read_numeric_economic_values": "NO",
        "purpose":
            "Audit metadata-level mapping coverage from frozen C UCCs to CPI ELIs.",
    },
    {
        "item": "CPI_ELI_TO_PUBLIC_ITEM_STRATUM_PUBLICATION_COVERAGE",
        "required": "YES",
        "may_read_numeric_economic_values": "NO",
        "purpose":
            "Determine which mapped consumption categories have public CPI index lineage.",
    },
    {
        "item": "CE_UCC_TO_PCE_PRODUCT_CONCORDANCE_SCHEMA",
        "required": "YES",
        "may_read_numeric_economic_values": "NO",
        "purpose":
            "Build an independent metadata crosswalk to detailed PCE categories.",
    },
    {
        "item": "AVERAGE_PRICE_COVERAGE_DIAGNOSTIC",
        "required": "YES",
        "may_read_numeric_economic_values": "NO",
        "purpose":
            "Confirm average-price publications cover only a subset of the frozen C universe.",
    },
    {
        "item": "EQUIVALENCE_SCALE_PLACEMENT_DECISION",
        "required": "YES",
        "may_read_numeric_economic_values": "NO",
        "purpose":
            "Decide whether household composition adjustment belongs inside C or as sensitivity.",
    },
    {
        "item": "NO_PRICE_OR_PCE_VALUES_UNTIL_POST_COVERAGE_CONTRACT",
        "required": "YES",
        "may_read_numeric_economic_values": "NO",
        "purpose":
            "Preserve chronology before numerical deflation or quantity construction.",
    },
]

next_df = pd.DataFrame(next_rows)

if len(next_df) != 7:
    raise RuntimeError("next metadata audit register shape mismatch")

if not (next_df["may_read_numeric_economic_values"] == "NO").all():
    raise RuntimeError("next metadata audit must remain pre-value")


OUT_SOURCES.parent.mkdir(parents=True, exist_ok=True)

sources.to_csv(
    OUT_SOURCES,
    sep="\t",
    index=False,
    lineterminator="\n",
)

support.to_csv(
    OUT_SUPPORT,
    sep="\t",
    index=False,
    lineterminator="\n",
)

next_df.to_csv(
    OUT_NEXT,
    sep="\t",
    index=False,
    lineterminator="\n",
)


audit_lines = [
    "=" * 100,
    "E4C2A — C REFERENCE / PRICE / QUANTITY SOURCE RECON PREFLIGHT",
    "=" * 100,
    "",
    "RAW_SURVEY_DATA_READ=0",
    "NEW_ECONOMIC_VALUES_OPENED=0",
    "PRICE_INDEX_VALUES_OPENED=0",
    "AVERAGE_PRICE_VALUES_OPENED=0",
    "PCE_VALUES_OPENED=0",
    "REGIONAL_PRICE_PARITY_VALUES_OPENED=0",
    "COORDINATE_VALUES_COMPUTED=0",
    "TRANSFORMED_VALUES_COMPUTED=0",
    "GEOMETRY_PERFORMED=0",
    "",
    "===== OFFICIAL SOURCE RECON =====",
    "OFFICIAL_PUBLIC_SOURCE_COUNT=8",
    "BLS_CE_CPI_CONCORDANCE_STATUS=STRONG_LINEAGE",
    "BLS_CE_CPI_2022_ARCHIVE_DOCUMENTED=1",
    "BLS_CPI_ITEM_STRUCTURE_STATUS=STRONG_LINEAGE",
    "BLS_CPI_AVERAGE_PRICES_COMPLETE_C_BUNDLE=0",
    "BLS_CE_PCE_CONCORDANCE_STATUS=STRONG_LINEAGE",
    "BEA_PCE_PRICE_QUANTITY_METHOD_STATUS=STRONG_METHOD_REFERENCE",
    "BEA_RPP_DIRECT_AGE_TENURE_IDENTIFICATION=0",
    "CENSUS_EQUIVALENCE_SCALE_AVAILABLE=1",
    "C_PRIMARY_EQUIVALENCE_SCALE_SELECTED=0",
    "E4C2A_SOURCE_REGISTRY_SHAPE=PASS",
    "",
    "===== C ARCHITECTURE SUPPORT =====",
    "C_A_SOURCE_LINEAGE_FEASIBLE=1",
    "C_A_SAME_YEAR_CROSS_SECTIONAL_IDENTIFICATION_RESOLVED=0",
    "C_B_SOURCE_LINEAGE_FEASIBLE=1",
    "C_B_DEFLATION_ARCHITECTURE_RESOLVED=0",
    "C_C_RESOURCE_LINEAGE_FEASIBLE=1",
    "C_C_K_D_I_OVERLAP_RESOLVED=0",
    "C_ARCHITECTURE_SELECTED=0",
    "E4C2A_ARCHITECTURE_SUPPORT_SHAPE=PASS",
    "",
    "===== NEXT METADATA AUDIT =====",
    "E4C2B_METADATA_AUDIT_REQUIREMENT_COUNT=7",
    "E4C2B_PRICE_VALUES_AUTHORIZED=0",
    "E4C2B_PCE_VALUES_AUTHORIZED=0",
    "E4C2B_C_CONCORDANCE_AND_CATEGORY_COVERAGE_AUDIT_PREFLIGHT_AUTHORIZED=1",
    "E4C2A_NEXT_AUDIT_SHAPE=PASS",
    "",
    "===== HARD BOUNDARY =====",
    "C_COORDINATE_VALUES_AUTHORIZED=0",
    "FIVE_COMPONENT_STATE_VECTOR_AUTHORIZED=0",
    "FIVE_COMPONENT_NORMALIZATION_AUTHORIZED=0",
    "DIMENSIONALITY_TEST_AUTHORIZED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "",
    "E4C2A_C_REFERENCE_PRICE_QUANTITY_SOURCE_RECON_PREFLIGHT=PASS",
]

audit_text = "\n".join(audit_lines) + "\n"

AUDIT.write_text(
    audit_text,
    encoding="utf-8",
)

sys.stdout.write(audit_text)
