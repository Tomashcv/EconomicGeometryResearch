#!/usr/bin/env python3
from pathlib import Path
from html.parser import HTMLParser
import csv
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]

CONTRACT = ROOT / "data/metadata/E4C2D_targeted_c_identification_evidence_audit_contract.json"
LINEAGE = ROOT / "data/metadata/E4C2D_frozen_input_lineage.tsv"
MANIFEST = ROOT / "data/metadata/E4C2D_official_source_manifest.tsv"

CE_GUIDE = ROOT / "data/raw/reference_metadata/E4C2D/bls_ce_pumd_getting_started_guide.html"
CPI_AVG = ROOT / "data/raw/reference_metadata/E4C2D/bls_cpi_average_prices_factsheet.html"
PCE_PROFILE = ROOT / "data/raw/reference_metadata/E4C2D/bls_ce_pce_profile.html"
PCE_METHODS = ROOT / "data/raw/reference_metadata/E4C2D/bls_ce_pce_distribution_methods.html"

EXEC = ROOT / "data/metadata/E4C2D_execution.txt"
AUDIT = ROOT / "data/metadata/E4C2D_targeted_c_identification_evidence_audit.txt"
EVIDENCE = ROOT / "data/results/E4C2D_c_identification_evidence.tsv"
CONSTRAINTS = ROOT / "data/results/E4C2D_c_identification_constraints.tsv"
DECISION = ROOT / "data/results/E4C2D_c_identification_decision.tsv"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_tsv(path: Path):
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def html_text(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    p = TextExtractor()
    p.feed(raw)
    return re.sub(r"\s+", " ", " ".join(p.parts)).strip()


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().casefold()


def require_fragments(text: str, source: str, groups):
    n = norm(text)
    matched = []
    for label, alternatives in groups:
        ok = False
        for fragment in alternatives:
            if norm(fragment) in n:
                matched.append(label)
                ok = True
                break
        if not ok:
            raise RuntimeError(f"official semantic evidence not found in {source}: {label}")
    return matched


contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
if contract["phase"] != "E4C2D":
    raise RuntimeError("wrong E4C2D contract phase")

for row in read_tsv(LINEAGE):
    p = ROOT / row["artifact"]
    if not p.exists() or sha256(p) != row["sha256"]:
        raise RuntimeError(f"frozen E4C2C lineage mismatch: {row['artifact']}")

manifest = read_tsv(MANIFEST)
if len(manifest) != 4:
    raise RuntimeError("official source manifest must contain exactly four sources")

expected_paths = {str(p.relative_to(ROOT)) for p in (CE_GUIDE, CPI_AVG, PCE_PROFILE, PCE_METHODS)}
manifest_paths = {r["artifact"] for r in manifest}
if manifest_paths != expected_paths:
    raise RuntimeError("official source manifest path set mismatch")
for row in manifest:
    p = ROOT / row["artifact"]
    if not p.exists() or sha256(p) != row["sha256"]:
        raise RuntimeError(f"official source hash mismatch: {row['artifact']}")

ce = html_text(CE_GUIDE)
cpi = html_text(CPI_AVG)
pce_profile = html_text(PCE_PROFILE)
pce_methods = html_text(PCE_METHODS)

require_fragments(
    ce,
    "BLS CE PUMD guide",
    [
        (
            "GENERAL_TOTAL_COST_NO_UNIT_VALUE",
            [
                "Generally, the CE surveys only provide the total cost and no unit value",
            ],
        ),
        (
            "LIMITED_QUANTITY_QUALITY_FEW_EXPENDITURES",
            [
                "limited information on the quantity and quality of a few expenditures",
            ],
        ),
    ],
)

require_fragments(
    cpi,
    "BLS CPI average-price factsheet",
    [
        (
            "AVERAGE_PRICES_ARE_PRICE_LEVELS",
            [
                "average prices provide estimates of price levels",
                "average prices provide estimates of the average price paid by the consumer",
            ],
        ),
        (
            "CPI_MEASURES_PRICE_CHANGE",
            [
                "The CPI measures price change",
                "CPI measures price change",
            ],
        ),
        (
            "NO_AVERAGE_PRICES_SERVICES_DURABLES",
            [
                "does not publish average price data for services or durable goods",
                "do not publish average price data for services or durable goods",
            ],
        ),
    ],
)

require_fragments(
    pce_profile,
    "BLS CE-PCE profile",
    [
        (
            "CONCORDANCE_MAPS_UCC_TO_PCE",
            [
                "concordance matches CE item categories (UCCs) to the PCE categories",
                "matches CE item categories (UCCs) to the PCE categories",
            ],
        ),
        (
            "UCC_ASSIGNMENT_EXPERT_JUDGMENT",
            [
                "UCCs have been assigned to PCE series based on expert judgment",
                "assigned to PCE series based on expert judgment",
            ],
        ),
    ],
)

require_fragments(
    pce_methods,
    "BLS distributional PCE methods",
    [
        (
            "USE_CE_MICRODATA_TO_DISTRIBUTE_PCE",
            [
                "use Consumer Expenditure Surveys (CE) microdata to describe the distribution of PCE across households",
                "use Consumer Expenditure Surveys data to describe the distribution of PCE across households",
            ],
        ),
        (
            "PCE_SCALING_TO_MATCH_TOTALS",
            [
                "scaled up to consumer unit-level PCE estimates so that totals match",
                "CE expenditures are scaled up to consumer unit-level PCE estimates",
            ],
        ),
        (
            "SQRT_EQUIVALENCE_SCALE",
            [
                "dividing consumer unit total expenditures by the square root of the number of people",
                "square root of the number of people within the consumer unit",
            ],
        ),
    ],
)

evidence_rows = [
    {
        "question": "Q1_CEX_GENERAL_QUANTITY_OR_UNIT_VALUE",
        "official_source": "BLS_CE_PUMD_GUIDE",
        "finding": "CE generally provides total cost and no unit value; quantity/quality detail exists only for a few expenditures",
        "identification_effect": "BROAD_DIRECT_REAL_QUANTITY_NOT_IDENTIFIED",
    },
    {
        "question": "Q2_CPI_CROSS_CATEGORY_REFERENCE_PRICES",
        "official_source": "BLS_CPI_AVERAGE_PRICES",
        "finding": "BLS distinguishes CPI price-change indexes from average-price levels; average-price publication excludes broad classes including services and durable goods",
        "identification_effect": "COMPLETE_REFERENCE_PRICE_VECTOR_NOT_IDENTIFIED",
    },
    {
        "question": "Q3_CE_PCE_HOUSEHOLD_QUANTITY",
        "official_source": "BLS_CE_PCE_PROFILE",
        "finding": "CE-PCE concordance maps UCC classifications to PCE categories and uses expert judgment",
        "identification_effect": "CONCORDANCE_IS_CLASSIFICATION_NOT_DIRECT_QUANTITY",
    },
    {
        "question": "Q3_CE_PCE_HOUSEHOLD_QUANTITY",
        "official_source": "BLS_CE_PCE_DISTRIBUTION_METHODS",
        "finding": "distributional PCE uses CE microdata and scales consumer-unit estimates to PCE totals",
        "identification_effect": "HOUSEHOLD_PCE_IS_STATISTICAL_ALLOCATION_NOT_DIRECT_PHYSICAL_QUANTITY",
    },
    {
        "question": "Q4_EQUIVALENCE_SCALE",
        "official_source": "BLS_CE_PCE_DISTRIBUTION_METHODS",
        "finding": "BLS distributional-PCE work documents square-root household-size equivalization",
        "identification_effect": "OFFICIAL_EXAMPLE_ONLY_NOT_PROJECT_SELECTION",
    },
]

constraint_rows = [
    ("CEX_GENERAL_UNIT_VALUE_SUPPORT", "0"),
    ("CEX_LIMITED_ITEM_QUANTITY_INFORMATION_EXISTS", "1"),
    ("DIRECT_435_UCC_REAL_QUANTITY_IDENTIFIED", "0"),
    ("CPI_INDEX_LEVEL_EQUALS_CROSS_CATEGORY_PRICE_LEVEL", "0"),
    ("CPI_AVERAGE_PRICE_LEVEL_DATA_EXIST_FOR_SELECTED_ITEMS", "1"),
    ("CPI_AVERAGE_PRICE_UNIVERSAL_COVERAGE", "0"),
    ("COMPLETE_C_REFERENCE_PRICE_VECTOR_IDENTIFIED", "0"),
    ("CE_PCE_CONCORDANCE_IS_CLASSIFICATION_BRIDGE", "1"),
    ("CE_PCE_CONCORDANCE_DIRECTLY_OBSERVES_HOUSEHOLD_QUANTITY", "0"),
    ("DISTRIBUTIONAL_PCE_USES_CE_BASED_ALLOCATION_SCALING", "1"),
    ("BLS_SQRT_HOUSEHOLD_SIZE_EQUIVALENCE_EXAMPLE_OBSERVED", "1"),
    ("BLS_SQRT_EQUIVALENCE_SCALE_ADOPTED_BY_PROJECT", "0"),
    ("KDI_COMPARABILITY_RESOLVED", "0"),
]

decision_rows = [
    ("REFERENCE_PRICE_IDENTIFICATION_RESOLVED", "0"),
    ("HOUSEHOLD_REAL_QUANTITY_IDENTIFICATION_RESOLVED", "0"),
    ("DIRECT_C_QUANTITY_PATH_CURRENTLY_IDENTIFIED", "0"),
    ("COST_SIDE_REFERENCE_BASKET_TRACK_REMAINS_DISTINCT", "1"),
    ("EQUIVALENCE_SCALE_PLACEMENT_SELECTED", "0"),
    ("C_REAL_STATE_COORDINATE_IDENTIFIED", "0"),
    ("C_ARCHITECTURE_SELECTED", "0"),
    ("C_COORDINATE_VALUES_AUTHORIZED", "0"),
    ("FIVE_COMPONENT_STATE_VECTOR_AUTHORIZED", "0"),
    ("FIVE_COMPONENT_NORMALIZATION_AUTHORIZED", "0"),
    ("GEOMETRY_AUTHORIZED", "0"),
    ("DIMENSIONALITY_TEST_AUTHORIZED", "0"),
    ("REAL_INFLATION_ESTIMATION_AUTHORIZED", "0"),
    ("FINAL_SCALAR_AUTHORIZED", "0"),
    ("E4C2E_C_SEMANTIC_BRANCH_AND_MEASUREMENT_DESIGN_PREFLIGHT_AUTHORIZED", "1"),
]

for p in (EXEC, AUDIT, EVIDENCE, CONSTRAINTS, DECISION):
    p.parent.mkdir(parents=True, exist_ok=True)

with EVIDENCE.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(
        f,
        fieldnames=["question", "official_source", "finding", "identification_effect"],
        delimiter="\t",
        lineterminator="\n",
    )
    w.writeheader()
    w.writerows(evidence_rows)

with CONSTRAINTS.open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t", lineterminator="\n")
    w.writerow(["constraint", "value"])
    w.writerows(constraint_rows)

with DECISION.open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t", lineterminator="\n")
    w.writerow(["decision", "value"])
    w.writerows(decision_rows)

log = "\n".join([
    "================================================================================",
    "ECONOMIC GEOMETRY RESEARCH — E4C2D",
    "TARGETED C IDENTIFICATION-EVIDENCE AUDIT",
    "================================================================================",
    "RAW_SURVEY_DATA_READ=0",
    "NEW_CEX_ECONOMIC_VALUES_OPENED=0",
    "CPI_INDEX_VALUES_OPENED=0",
    "CPI_AVERAGE_PRICE_VALUES_OPENED=0",
    "PCE_EXPENDITURE_VALUES_OPENED=0",
    "PCE_PRICE_INDEX_VALUES_OPENED=0",
    "PCE_QUANTITY_INDEX_VALUES_OPENED=0",
    "REGIONAL_PRICE_PARITY_VALUES_OPENED=0",
    "OFFICIAL_BLS_DOCUMENTATION_HTML_OPENED=1",
    "OFFICIAL_SOURCE_COUNT=4",
    "CEX_GENERAL_UNIT_VALUE_SUPPORT=0",
    "CEX_LIMITED_ITEM_QUANTITY_INFORMATION_EXISTS=1",
    "DIRECT_435_UCC_REAL_QUANTITY_IDENTIFIED=0",
    "CPI_INDEX_LEVEL_EQUALS_CROSS_CATEGORY_PRICE_LEVEL=0",
    "CPI_AVERAGE_PRICE_LEVEL_DATA_EXIST_FOR_SELECTED_ITEMS=1",
    "CPI_AVERAGE_PRICE_UNIVERSAL_COVERAGE=0",
    "COMPLETE_C_REFERENCE_PRICE_VECTOR_IDENTIFIED=0",
    "CE_PCE_CONCORDANCE_IS_CLASSIFICATION_BRIDGE=1",
    "CE_PCE_CONCORDANCE_DIRECTLY_OBSERVES_HOUSEHOLD_QUANTITY=0",
    "DISTRIBUTIONAL_PCE_USES_CE_BASED_ALLOCATION_SCALING=1",
    "BLS_SQRT_HOUSEHOLD_SIZE_EQUIVALENCE_EXAMPLE_OBSERVED=1",
    "BLS_SQRT_EQUIVALENCE_SCALE_ADOPTED_BY_PROJECT=0",
    "KDI_COMPARABILITY_RESOLVED=0",
    "REFERENCE_PRICE_IDENTIFICATION_RESOLVED=0",
    "HOUSEHOLD_REAL_QUANTITY_IDENTIFICATION_RESOLVED=0",
    "DIRECT_C_QUANTITY_PATH_CURRENTLY_IDENTIFIED=0",
    "COST_SIDE_REFERENCE_BASKET_TRACK_REMAINS_DISTINCT=1",
    "EQUIVALENCE_SCALE_PLACEMENT_SELECTED=0",
    "C_REAL_STATE_COORDINATE_IDENTIFIED=0",
    "C_ARCHITECTURE_SELECTED=0",
    "C_COORDINATE_VALUES_COMPUTED=0",
    "TRANSFORMED_VALUES_COMPUTED=0",
    "GEOMETRY_PERFORMED=0",
    "C_COORDINATE_VALUES_AUTHORIZED=0",
    "FIVE_COMPONENT_STATE_VECTOR_AUTHORIZED=0",
    "FIVE_COMPONENT_NORMALIZATION_AUTHORIZED=0",
    "GEOMETRY_AUTHORIZED=0",
    "DIMENSIONALITY_TEST_AUTHORIZED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "E4C2D_NEGATIVE_IDENTIFICATION_EVIDENCE_IS_VALID=1",
    "E4C2D_TARGETED_C_IDENTIFICATION_EVIDENCE_AUDIT=PASS",
    "E4C2E_C_SEMANTIC_BRANCH_AND_MEASUREMENT_DESIGN_PREFLIGHT_AUTHORIZED=1",
]) + "\n"

EXEC.write_text(log, encoding="utf-8")
AUDIT.write_text(log, encoding="utf-8")
print(log, end="")
