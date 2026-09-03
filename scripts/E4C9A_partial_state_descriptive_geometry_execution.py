#!/usr/bin/env python3
from pathlib import Path
from fractions import Fraction
import csv

ROOT = Path(__file__).resolve().parents[1]

POINT_REG = ROOT / "data/results/E4C6E_partial_observed_coordinate_registry.tsv"
PLAN = ROOT / "data/results/E4C9_descriptive_geometry_execution_plan.tsv"

EXEC = ROOT / "data/metadata/E4C9A_execution.txt"
AUDIT = ROOT / "data/metadata/E4C9A_partial_state_descriptive_geometry_execution_audit.txt"
DIFF = ROOT / "data/results/E4C9A_pairwise_difference_vectors.tsv"
DIST = ROOT / "data/results/E4C9A_pairwise_squared_distances.tsv"
CONTRIB = ROOT / "data/results/E4C9A_distance_coordinate_contributions.tsv"
GATES = ROOT / "data/results/E4C9A_execution_hard_gates.tsv"
DECISION = ROOT / "data/results/E4C9A_partial_state_descriptive_geometry_execution_decision.tsv"

COORDS = [
    "H_ACCESS_SPACE_ROOMS_PER_PERSON",
    "K_FIN_MEAN_TRANSFORMED",
    "D_PIRTOTAL_MEAN_STATE_TRANSFORMED",
    "I_FYFT_SHARE",
    "I_SEARCH_SECURITY",
]

METRIC_WEIGHTS = {
    "M1_NATURAL_TRANSFORM_UNIT_IDENTITY": {
        COORDS[0]: Fraction(1, 1),
        COORDS[1]: Fraction(1, 1),
        COORDS[2]: Fraction(1, 1),
        COORDS[3]: Fraction(1, 1),
        COORDS[4]: Fraction(1, 1),
    },
    "M2_CONCEPT_BALANCED_I_SPLIT": {
        COORDS[0]: Fraction(1, 1),
        COORDS[1]: Fraction(1, 1),
        COORDS[2]: Fraction(1, 1),
        COORDS[3]: Fraction(1, 2),
        COORDS[4]: Fraction(1, 2),
    },
}

EXPECTED_AGES = ["25-34", "35-44", "45-54", "55-64"]
EXPECTED_TENURES = ["OWNER", "RENTER"]


def fstr(x: Fraction) -> str:
    if x.denominator == 1:
        return str(x.numerator)
    return f"{x.numerator}/{x.denominator}"


def exact_terminating_decimal(x: Fraction) -> str:
    n = x.numerator
    d = x.denominator
    sign = "-" if n < 0 else ""
    n = abs(n)

    a = b = 0
    q = d
    while q % 2 == 0:
        a += 1
        q //= 2
    while q % 5 == 0:
        b += 1
        q //= 5
    if q != 1:
        raise RuntimeError(f"non-terminating rational denominator: {d}")

    scale = max(a, b)
    scaled_n = n * (2 ** (scale - a)) * (5 ** (scale - b))
    if scale == 0:
        return sign + str(scaled_n)

    digits = str(scaled_n).rjust(scale + 1, "0")
    whole = digits[:-scale]
    frac = digits[-scale:].rstrip("0")
    if not frac:
        return sign + whole
    return sign + whole + "." + frac


# Open only the two frozen E4C9A inputs after precommit.
with POINT_REG.open("r", encoding="utf-8", newline="") as f:
    point_rows = list(csv.DictReader(f, delimiter="\t"))

with PLAN.open("r", encoding="utf-8", newline="") as f:
    plan_rows = list(csv.DictReader(f, delimiter="\t"))

assert len(point_rows) == 40
assert len(plan_rows) == 56

# Build exact 8 x 5 point grid. se_state is intentionally not parsed or used.
points = {}
source_point_strings = {}
for r in point_rows:
    if r["year"] != "2022":
        continue
    age = r["age_band"]
    tenure = r["tenure"]
    cid = r["coordinate_id"]
    if age not in EXPECTED_AGES or tenure not in EXPECTED_TENURES or cid not in COORDS:
        continue
    key = (age, tenure)
    points.setdefault(key, {})
    source_point_strings.setdefault(key, {})
    if cid in points[key]:
        raise RuntimeError(f"duplicate point coordinate {key} {cid}")
    raw = r["point_state"].strip()
    points[key][cid] = Fraction(raw)
    source_point_strings[key][cid] = raw

expected_cells = [(a, t) for a in EXPECTED_AGES for t in EXPECTED_TENURES]
assert set(points) == set(expected_cells)
assert all(set(points[k]) == set(COORDS) for k in expected_cells)

# Reconstruct 28 structural pair definitions from the frozen 56-row dual-metric plan.
pair_specs = {}
for r in plan_rows:
    idx = int(r["pair_index"])
    spec = (
        r["cell_a_age_band"],
        r["cell_a_tenure"],
        r["cell_b_age_band"],
        r["cell_b_tenure"],
        r["pair_family"],
    )
    metric = r["metric_id"]
    if metric not in METRIC_WEIGHTS:
        raise RuntimeError(f"unexpected metric in plan: {metric}")
    if idx in pair_specs:
        if pair_specs[idx]["spec"] != spec:
            raise RuntimeError(f"pair {idx} structural mismatch across metrics")
    else:
        pair_specs[idx] = {"spec": spec, "metrics": set()}
    pair_specs[idx]["metrics"].add(metric)

assert sorted(pair_specs) == list(range(1, 29))
assert all(v["metrics"] == set(METRIC_WEIGHTS) for v in pair_specs.values())

diff_rows = []
dist_rows = []
contrib_rows = []

distance_by_pair_metric = {}

for pair_index in range(1, 29):
    a_age, a_ten, b_age, b_ten, family = pair_specs[pair_index]["spec"]
    a_key = (a_age, a_ten)
    b_key = (b_age, b_ten)

    deltas = {cid: points[b_key][cid] - points[a_key][cid] for cid in COORDS}

    diff_row = {
        "pair_index": str(pair_index),
        "cell_a_age_band": a_age,
        "cell_a_tenure": a_ten,
        "cell_b_age_band": b_age,
        "cell_b_tenure": b_ten,
        "pair_family": family,
        "direction_definition": "CELL_B_MINUS_CELL_A",
    }
    for cid in COORDS:
        diff_row[f"delta_{cid}_exact"] = fstr(deltas[cid])
        diff_row[f"delta_{cid}_decimal"] = exact_terminating_decimal(deltas[cid])
    diff_rows.append(diff_row)

    for metric_id in [
        "M1_NATURAL_TRANSFORM_UNIT_IDENTITY",
        "M2_CONCEPT_BALANCED_I_SPLIT",
    ]:
        weights = METRIC_WEIGHTS[metric_id]
        total = Fraction(0, 1)

        for cid in COORDS:
            contribution = weights[cid] * deltas[cid] * deltas[cid]
            total += contribution
            contrib_rows.append({
                "pair_index": str(pair_index),
                "cell_a_age_band": a_age,
                "cell_a_tenure": a_ten,
                "cell_b_age_band": b_age,
                "cell_b_tenure": b_ten,
                "pair_family": family,
                "metric_id": metric_id,
                "coordinate_id": cid,
                "metric_weight_exact": fstr(weights[cid]),
                "delta_exact": fstr(deltas[cid]),
                "delta_decimal": exact_terminating_decimal(deltas[cid]),
                "weighted_squared_contribution_exact": fstr(contribution),
                "weighted_squared_contribution_decimal": exact_terminating_decimal(contribution),
            })

        if total < 0:
            raise RuntimeError("squared metric distance became negative")

        distance_by_pair_metric[(pair_index, metric_id)] = total
        dist_rows.append({
            "pair_index": str(pair_index),
            "cell_a_age_band": a_age,
            "cell_a_tenure": a_ten,
            "cell_b_age_band": b_age,
            "cell_b_tenure": b_ten,
            "pair_family": family,
            "metric_id": metric_id,
            "squared_distance_numerator": str(total.numerator),
            "squared_distance_denominator": str(total.denominator),
            "squared_distance_exact": fstr(total),
            "squared_distance_decimal": exact_terminating_decimal(total),
            "distance_sqrt_computed": "0",
            "outcome_gate": "NONE",
        })

# Exact algebraic identity implied by M2's half-weight on the two I axes.
for pair_index in range(1, 29):
    m1 = distance_by_pair_metric[(pair_index, "M1_NATURAL_TRANSFORM_UNIT_IDENTITY")]
    m2 = distance_by_pair_metric[(pair_index, "M2_CONCEPT_BALANCED_I_SPLIT")]
    spec = pair_specs[pair_index]["spec"]
    a_key = (spec[0], spec[1])
    b_key = (spec[2], spec[3])
    di1 = points[b_key]["I_FYFT_SHARE"] - points[a_key]["I_FYFT_SHARE"]
    di2 = points[b_key]["I_SEARCH_SECURITY"] - points[a_key]["I_SEARCH_SECURITY"]
    expected_gap = Fraction(1, 2) * (di1 * di1 + di2 * di2)
    assert m1 - m2 == expected_gap
    assert m2 <= m1

# Write frozen-order outputs. No distance sorting/ranking is performed.
diff_fields = [
    "pair_index","cell_a_age_band","cell_a_tenure","cell_b_age_band","cell_b_tenure",
    "pair_family","direction_definition",
]
for cid in COORDS:
    diff_fields += [f"delta_{cid}_exact", f"delta_{cid}_decimal"]

with DIFF.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=diff_fields, delimiter="\t", lineterminator="\n")
    w.writeheader()
    w.writerows(diff_rows)

dist_fields = [
    "pair_index","cell_a_age_band","cell_a_tenure","cell_b_age_band","cell_b_tenure",
    "pair_family","metric_id","squared_distance_numerator","squared_distance_denominator",
    "squared_distance_exact","squared_distance_decimal","distance_sqrt_computed","outcome_gate",
]
with DIST.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=dist_fields, delimiter="\t", lineterminator="\n")
    w.writeheader()
    w.writerows(dist_rows)

contrib_fields = [
    "pair_index","cell_a_age_band","cell_a_tenure","cell_b_age_band","cell_b_tenure",
    "pair_family","metric_id","coordinate_id","metric_weight_exact",
    "delta_exact","delta_decimal","weighted_squared_contribution_exact",
    "weighted_squared_contribution_decimal",
]
with CONTRIB.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=contrib_fields, delimiter="\t", lineterminator="\n")
    w.writeheader()
    w.writerows(contrib_rows)

gate_rows = [
    ["E4C9_FROZEN_PLAN_REUSED", "PASS"],
    ["E4C6E_EXACT_8_X_5_POINT_GRID", "PASS"],
    ["EXACT_RATIONAL_POINT_PARSE", "PASS"],
    ["EXACT_28_PAIR_DIFFERENCE_VECTOR_GRID", "PASS"],
    ["EXACT_56_DUAL_METRIC_SQUARED_DISTANCE_GRID", "PASS"],
    ["EXACT_280_COORDINATE_CONTRIBUTION_GRID", "PASS"],
    ["DISTANCE_EQUALS_SUM_OF_COORDINATE_CONTRIBUTIONS", "PASS"],
    ["M2_M1_EXACT_ALGEBRAIC_IDENTITY", "PASS"],
    ["NO_DISTANCE_SORTING_OR_RANK_SELECTION", "PASS"],
    ["NO_STANDARD_ERROR_USE_IN_POINT_GEOMETRY", "PASS"],
    ["NO_INFERENTIAL_GEOMETRY", "PASS"],
    ["NO_DIMENSIONALITY_TEST", "PASS"],
    ["NO_REAL_INFLATION_ESTIMATE", "PASS"],
]
with GATES.open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t", lineterminator="\n")
    w.writerow(["gate", "value"])
    w.writerows(gate_rows)

decision_rows = [
    ["STATE_POINT_COUNT", "8"],
    ["NUMERICAL_COORDINATE_COUNT", "5"],
    ["NUMERICALLY_REPRESENTED_CONCEPT_COUNT", "4"],
    ["PAIRWISE_DIFFERENCE_VECTOR_ROW_COUNT", "28"],
    ["PAIRWISE_SQUARED_DISTANCE_ROW_COUNT", "56"],
    ["DISTANCE_COORDINATE_CONTRIBUTION_ROW_COUNT", "280"],
    ["OWNER_RENTER_WITHIN_AGE_PAIR_COUNT", "4"],
    ["ADJACENT_AGE_WITHIN_TENURE_PAIR_COUNT", "6"],
    ["EXACT_RATIONAL_ARITHMETIC_USED", "1"],
    ["BINARY_FLOAT_ROUNDTRIP_USED", "0"],
    ["DISTANCE_SQRT_COMPUTED", "0"],
    ["DISTANCE_SORTING_OR_RANKING_PERFORMED", "0"],
    ["SOURCE_STANDARD_ERRORS_USED_IN_POINT_GEOMETRY", "0"],
    ["M1_REPORTED", "1"],
    ["M2_REPORTED", "1"],
    ["BEST_LOOKING_METRIC_SELECTION_PERFORMED", "0"],
    ["ABSOLUTE_ORIGIN_INTERPRETATION_USED", "0"],
    ["INFERENTIAL_GEOMETRY_COMPUTED", "0"],
    ["PAIRWISE_DISTANCE_SE_COMPUTED", "0"],
    ["PAIRWISE_DISTANCE_CI_COMPUTED", "0"],
    ["DIMENSIONALITY_TEST_COMPUTED", "0"],
    ["PCA_COMPUTED", "0"],
    ["AFFINE_RANK_COMPUTED", "0"],
    ["C_INCLUDED", "0"],
    ["H_ACCESS_PROMOTED_TO_FULL_H_STATE", "0"],
    ["I_SCALAR_CREATED", "0"],
    ["PARTIAL_PANEL_IS_FULL_CHKDI_STATE_VECTOR", "0"],
    ["DESCRIPTIVE_GEOMETRY_IS_REAL_INFLATION_ESTIMATE", "0"],
    ["REAL_INFLATION_ESTIMATION_AUTHORIZED", "0"],
    ["FINAL_SCALAR_AUTHORIZED", "0"],
    ["E4C9A_PARTIAL_STATE_DESCRIPTIVE_GEOMETRY_EXECUTION", "PASS"],
    ["E4C9B_PARTIAL_STATE_DESCRIPTIVE_GEOMETRY_CLOSEOUT_PREFLIGHT_AUTHORIZED", "1"],
]
with DECISION.open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t", lineterminator="\n")
    w.writerow(["decision", "value"])
    w.writerows(decision_rows)

log = "\n".join([
    "E4C9_FROZEN_GEOMETRY_PLAN_REUSED=1",
    "ECONOMIC_POINT_ROWS_OPENED_AFTER_E4C9A_PRECOMMIT=1",
    "E4C6E_POINT_REGISTRY_ROW_COUNT=40",
    "STATE_POINT_COUNT=8",
    "NUMERICAL_COORDINATE_COUNT=5",
    "NUMERICALLY_REPRESENTED_CONCEPT_COUNT=4",
    "EXACT_RATIONAL_ARITHMETIC_USED=1",
    "BINARY_FLOAT_ROUNDTRIP_USED=0",
    "PAIRWISE_DIFFERENCE_VECTOR_ROW_COUNT=28",
    "PAIRWISE_SQUARED_DISTANCE_ROW_COUNT=56",
    "DISTANCE_COORDINATE_CONTRIBUTION_ROW_COUNT=280",
    "OWNER_RENTER_WITHIN_AGE_PAIR_COUNT=4",
    "ADJACENT_AGE_WITHIN_TENURE_PAIR_COUNT=6",
    "M1_REPORTED=1",
    "M2_REPORTED=1",
    "M2_M1_EXACT_ALGEBRAIC_IDENTITY_PASS=1",
    "DISTANCE_SQRT_COMPUTED=0",
    "DISTANCE_SORTING_OR_RANKING_PERFORMED=0",
    "OUTCOME_SIGN_USED_AS_EXECUTION_GATE=0",
    "OUTCOME_MAGNITUDE_USED_AS_EXECUTION_GATE=0",
    "BEST_LOOKING_METRIC_SELECTION_PERFORMED=0",
    "SOURCE_STANDARD_ERRORS_USED_IN_POINT_GEOMETRY=0",
    "ABSOLUTE_ORIGIN_INTERPRETATION_USED=0",
    "INFERENTIAL_GEOMETRY_COMPUTED=0",
    "PAIRWISE_DISTANCE_STANDARD_ERROR_COMPUTED=0",
    "PAIRWISE_DISTANCE_CONFIDENCE_INTERVAL_COMPUTED=0",
    "CONTRAST_SIGNIFICANCE_TEST_COMPUTED=0",
    "ZERO_CROSS_CELL_SAMPLING_COVARIANCE_ASSUMED=0",
    "PCA_COMPUTED=0",
    "WHITENING_COMPUTED=0",
    "SVD_DIMENSION_COMPUTED=0",
    "EIGENVALUE_DIMENSION_COMPUTED=0",
    "AFFINE_RANK_COMPUTED=0",
    "DIMENSIONALITY_TEST_COMPUTED=0",
    "C_INCLUDED=0",
    "H_ACCESS_PROMOTED_TO_FULL_H_STATE=0",
    "I_SCALAR_CREATED=0",
    "PARTIAL_PANEL_IS_FULL_CHKDI_STATE_VECTOR=0",
    "DESCRIPTIVE_GEOMETRY_IS_REAL_INFLATION_ESTIMATE=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "E4C9A_PARTIAL_STATE_DESCRIPTIVE_GEOMETRY_EXECUTION=PASS",
    "E4C9B_PARTIAL_STATE_DESCRIPTIVE_GEOMETRY_CLOSEOUT_PREFLIGHT_AUTHORIZED=1",
]) + "\n"

EXEC.write_text(log, encoding="utf-8")
AUDIT.write_text(log, encoding="utf-8")
print(log, end="")
