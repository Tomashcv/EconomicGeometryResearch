from __future__ import annotations

import csv
import hashlib
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TREE = ROOT / "data/metadata/E3B3B_ucc_hierarchy_tree.tsv"

OUT = ROOT / "data/metadata/E3B3C1_component_ucc_mapping_audit.txt"
MAP = ROOT / "data/metadata/E3B3C1_component_ucc_map.tsv"
SUMMARY = ROOT / "data/metadata/E3B3C1_component_counts.tsv"

EXPECTED_TREE_SHA = (
    "136dca44d16777650ac0c8901f3b23187fd9f64bb7bf3208b8c10e16d3960a4c"
)


PRIMARY_C_BROAD = {
    "Food",
    "Alcoholic beverages",
    "Apparel and services",
    "Transportation",
    "Healthcare",
    "Entertainment",
    "Personal care products and services",
    "Reading",
    "Education",
    "Tobacco products and smoking supplies",
    "Miscellaneous",
}


H_SERVICE_CORE = {
    "Shelter",
    "Utilities, fuels, and public services",
}


H_NONCORE_PENDING = {
    "Household operations",
    "Housekeeping supplies",
}


DURABLE_PENDING = {
    "Household furnishings and equipment",
}


EXPECTED_BROAD = {
    "Food",
    "Alcoholic beverages",
    "Apparel and services",
    "Cash contributions",
    "Education",
    "Entertainment",
    "Healthcare",
    "Housing",
    "Miscellaneous",
    "Personal care products and services",
    "Personal insurance and pensions",
    "Reading",
    "Tobacco products and smoking supplies",
    "Transportation",
}


EXPECTED_CLASSES = {
    "C_COST_PRIMARY",
    "H_SERVICE_CORE",
    "H_NONCORE_PENDING",
    "DURABLE_SERVICE_PENDING",
    "EXCLUDED_TRANSFER",
    "EXCLUDED_INSURANCE_PENSION",
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


if sha256(TREE) != EXPECTED_TREE_SHA:
    raise RuntimeError(
        "frozen E3B3B hierarchy tree SHA mismatch"
    )


with TREE.open(
    encoding="utf-8",
) as f:

    all_rows = list(
        csv.DictReader(
            f,
            delimiter="\t",
        )
    )


rows = [
    r
    for r in all_rows
    if r["section"] in {
        "FOOD",
        "EXPEND",
    }
]


if len(rows) != 645:
    raise RuntimeError(
        f"expected 645 FOOD/EXPEND rows; got={len(rows)}"
    )


uccs = [
    r["ucc"]
    for r in rows
]

if len(set(uccs)) != 645:
    raise RuntimeError(
        "FOOD/EXPEND UCCs are not unique"
    )


def classify(row: dict[str, str]) -> tuple[str, str, str]:

    section = row["section"]

    if section == "FOOD":

        broad = row["level_2_title"].strip()

        if broad != "Food":
            raise RuntimeError(
                f"unexpected FOOD broad category "
                f"ucc={row['ucc']} broad={broad!r}"
            )

        return (
            broad,
            row["level_3_title"].strip(),
            "C_COST_PRIMARY",
        )

    if section != "EXPEND":
        raise RuntimeError(
            f"unexpected section={section}"
        )

    broad = row["level_2_title"].strip()
    sub = row["level_3_title"].strip()

    if broad in (
        PRIMARY_C_BROAD
        - {"Food"}
    ):
        return (
            broad,
            sub,
            "C_COST_PRIMARY",
        )

    if broad == "Housing":

        if sub in H_SERVICE_CORE:
            return (
                broad,
                sub,
                "H_SERVICE_CORE",
            )

        if sub in H_NONCORE_PENDING:
            return (
                broad,
                sub,
                "H_NONCORE_PENDING",
            )

        if sub in DURABLE_PENDING:
            return (
                broad,
                sub,
                "DURABLE_SERVICE_PENDING",
            )

        raise RuntimeError(
            f"unmapped Housing subcategory "
            f"ucc={row['ucc']} sub={sub!r}"
        )

    if broad == "Cash contributions":
        return (
            broad,
            sub,
            "EXCLUDED_TRANSFER",
        )

    if broad == "Personal insurance and pensions":
        return (
            broad,
            sub,
            "EXCLUDED_INSURANCE_PENSION",
        )

    raise RuntimeError(
        f"unmapped broad category "
        f"ucc={row['ucc']} broad={broad!r}"
    )


mapped = []

for row in rows:

    broad, sub, component_class = classify(
        row
    )

    if row["source"] not in {
        "I",
        "D",
    }:
        raise RuntimeError(
            f"invalid source ucc={row['ucc']}"
        )

    if row["factor"] not in {
        "1",
        "4",
    }:
        raise RuntimeError(
            f"invalid factor ucc={row['ucc']} "
            f"factor={row['factor']!r}"
        )

    if component_class == "C_COST_PRIMARY":
        primary_component = "C_COST"

    elif component_class == "H_SERVICE_CORE":
        primary_component = "H_SERVICE"

    else:
        primary_component = "NONE"

    mapped.append({
        "ucc": row["ucc"],
        "source": row["source"],
        "factor": row["factor"],
        "section": row["section"],
        "broad_category": broad,
        "subcategory": sub,
        "leaf_title": row["leaf_title"],
        "component_class": component_class,
        "primary_component": primary_component,
        "hierarchy_path": row["hierarchy_path"],
    })


# =============================================================================
# Integrity gates
# =============================================================================

if len(mapped) != 645:
    raise RuntimeError(
        "mapping row-count mismatch"
    )


if len({
    r["ucc"]
    for r in mapped
}) != 645:
    raise RuntimeError(
        "mapping duplicated a UCC"
    )


classes = {
    r["component_class"]
    for r in mapped
}

if classes != EXPECTED_CLASSES:
    raise RuntimeError(
        f"class-set mismatch={classes}"
    )


broad_categories = {
    r["broad_category"]
    for r in mapped
}

if broad_categories != EXPECTED_BROAD:
    raise RuntimeError(
        f"broad-category mismatch={broad_categories}"
    )


c_uccs = {
    r["ucc"]
    for r in mapped
    if r["primary_component"] == "C_COST"
}

h_uccs = {
    r["ucc"]
    for r in mapped
    if r["primary_component"] == "H_SERVICE"
}

if not c_uccs:
    raise RuntimeError(
        "empty C_COST"
    )

if not h_uccs:
    raise RuntimeError(
        "empty H_SERVICE"
    )

if c_uccs & h_uccs:
    raise RuntimeError(
        "C_COST/H_SERVICE overlap"
    )


housing_rows = [
    r
    for r in mapped
    if r["broad_category"] == "Housing"
]

housing_classes = {
    r["component_class"]
    for r in housing_rows
}

expected_housing_classes = {
    "H_SERVICE_CORE",
    "H_NONCORE_PENDING",
    "DURABLE_SERVICE_PENDING",
}

if housing_classes != expected_housing_classes:
    raise RuntimeError(
        f"housing partition mismatch={housing_classes}"
    )


# =============================================================================
# Write frozen map
# =============================================================================

MAP.parent.mkdir(
    parents=True,
    exist_ok=True,
)


fields = [
    "ucc",
    "source",
    "factor",
    "section",
    "broad_category",
    "subcategory",
    "leaf_title",
    "component_class",
    "primary_component",
    "hierarchy_path",
]


with MAP.open(
    "w",
    newline="",
    encoding="utf-8",
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fields,
        delimiter="\t",
    )

    writer.writeheader()

    writer.writerows(
        sorted(
            mapped,
            key=lambda r: (
                r["component_class"],
                r["broad_category"],
                r["subcategory"],
                r["ucc"],
            ),
        )
    )


class_counts = Counter(
    r["component_class"]
    for r in mapped
)

source_counts = Counter(
    r["source"]
    for r in mapped
)

factor_counts = Counter(
    r["factor"]
    for r in mapped
)


summary_rows = []

for component_class in sorted(
    class_counts
):

    selected = [
        r
        for r in mapped
        if r["component_class"]
        == component_class
    ]

    summary_rows.append({
        "component_class": component_class,
        "ucc_count": len(selected),
        "interview_uccs": sum(
            r["source"] == "I"
            for r in selected
        ),
        "diary_uccs": sum(
            r["source"] == "D"
            for r in selected
        ),
        "factor_1_uccs": sum(
            r["factor"] == "1"
            for r in selected
        ),
        "factor_4_uccs": sum(
            r["factor"] == "4"
            for r in selected
        ),
    })


with SUMMARY.open(
    "w",
    newline="",
    encoding="utf-8",
) as f:

    summary_fields = [
        "component_class",
        "ucc_count",
        "interview_uccs",
        "diary_uccs",
        "factor_1_uccs",
        "factor_4_uccs",
    ]

    writer = csv.DictWriter(
        f,
        fieldnames=summary_fields,
        delimiter="\t",
    )

    writer.writeheader()
    writer.writerows(summary_rows)


overall = True


audit = "\n".join([
    "=" * 100,
    "ECONOMIC GEOMETRY RESEARCH — E3B3C1 COMPONENT UCC MAPPING AUDIT",
    "=" * 100,
    "",
    "COST_VALUES_READ=0",
    "EXPENDITURE_VALUES_OPENED=0",
    "HOUSEHOLD_ECONOMIC_VALUES_OPENED=0",
    "REAL_INFLATION_ESTIMATED=0",
    "",
    "===== INPUT =====",
    f"FOOD_EXPEND_UCCS={len(mapped)}",
    f"UNIQUE_UCCS={len(set(r['ucc'] for r in mapped))}",
    f"BROAD_CATEGORY_COUNT={len(broad_categories)}",
    "",
    "===== MAPPING =====",
    f"CLASS_COUNTS={dict(sorted(class_counts.items()))}",
    f"SOURCE_COUNTS={dict(sorted(source_counts.items()))}",
    f"FACTOR_COUNTS={dict(sorted(factor_counts.items()))}",
    f"C_COST_PRIMARY_UCCS={len(c_uccs)}",
    f"H_SERVICE_CORE_UCCS={len(h_uccs)}",
    "C_COST_H_SERVICE_OVERLAP=0",
    "UNMAPPED_UCCS=0",
    "",
    "===== DESIGN =====",
    "C_COST_UCC_MAP_FROZEN=1",
    "H_SERVICE_CORE_UCC_MAP_FROZEN=1",
    "H_ACCESS_UCC_MAP=NOT_APPLICABLE",
    "H_NONCORE_PENDING_PRESERVED=1",
    "DURABLE_SERVICE_PENDING_PRESERVED=1",
    "INTEGRATION_ARITHMETIC_FROZEN=0",
    "HOUSEHOLD_ECONOMIC_VALUES_AUTHORIZED=0",
    "",
    (
        "E3B3C1_COMPONENT_UCC_MAPPING=PASS"
        if overall
        else
        "E3B3C1_COMPONENT_UCC_MAPPING=FAIL"
    ),
    "E3B3C2_BLS_ESTIMATOR_PREFLIGHT_AUTHORIZED=1",
    "",
])


OUT.write_text(
    audit,
    encoding="utf-8",
)

print(audit)
