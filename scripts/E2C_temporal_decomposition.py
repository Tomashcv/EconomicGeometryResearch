from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "fred"

OUT_DATA = ROOT / "data" / "processed" / "E2C_annual_decomposition.csv"
OUT_REGIMES = ROOT / "results" / "tables" / "E2C_descriptive_regimes.csv"
OUT_SUMMARY = ROOT / "results" / "tables" / "E2C_summary.txt"

SERIES = {
    "Y": "A229RC0Q052SBEA",
    "P": "PCECTPI",
    "H": "USSTHPI",
}

REF_YEAR = 1975
MISSING = {"", ".", "NA", "NaN", "nan", "N/A"}


def load(series_id: str) -> dict[str, float]:
    path = RAW / f"{series_id}.csv"
    out = {}

    with path.open(newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)

        for row in r:
            d = row["observation_date"].strip()
            v = row[series_id].strip()

            if v in MISSING:
                continue

            if d in out:
                raise RuntimeError(f"{series_id}: duplicate date {d}")

            out[d] = float(v)

    return out


def annual_mean_quarterly(values: dict[str, float]) -> dict[int, float]:
    groups = defaultdict(list)

    for d, v in values.items():
        year = int(d[:4])
        month = int(d[5:7])

        if month not in {1, 4, 7, 10}:
            raise RuntimeError(f"unexpected quarterly date: {d}")

        groups[year].append((month, v))

    out = {}

    for year, obs in groups.items():
        months = {m for m, _ in obs}

        if len(obs) == 4 and months == {1, 4, 7, 10}:
            out[year] = sum(v for _, v in obs) / 4.0

    return out


def ols_slope(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return float("nan")

    xbar = sum(xs) / len(xs)
    ybar = sum(ys) / len(ys)

    num = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys))
    den = sum((x - xbar) ** 2 for x in xs)

    if den == 0:
        return float("nan")

    return num / den


def trailing_slope(rows, idx, key, window):
    if idx + 1 < window:
        return None

    part = rows[idx - window + 1: idx + 1]

    years = [r["year"] for r in part]

    if any(b - a != 1 for a, b in zip(years[:-1], years[1:])):
        return None

    vals = [r[key] for r in part]

    return ols_slope(years, vals)


raw = {k: load(v) for k, v in SERIES.items()}

Y = annual_mean_quarterly(raw["Y"])
P = annual_mean_quarterly(raw["P"])
H = annual_mean_quarterly(raw["H"])

years = sorted(set(Y) & set(P) & set(H))
years = [y for y in years if y >= REF_YEAR]

if not years or years[0] != REF_YEAR:
    raise RuntimeError("1975 reference year unavailable")

y0 = Y[REF_YEAR]
p0 = P[REF_YEAR]
h0 = H[REF_YEAR]

rows = []

prev_xc = None
prev_xh = None
prev_gap = None

for year in years:
    ln_y = math.log(Y[year] / y0)
    ln_p = math.log(P[year] / p0)
    ln_h = math.log(H[year] / h0)

    x_c = ln_y - ln_p
    x_h = ln_y - ln_h
    gap = ln_h - ln_p

    dx_c = None if prev_xc is None else x_c - prev_xc
    dx_h = None if prev_xh is None else x_h - prev_xh
    dgap = None if prev_gap is None else gap - prev_gap

    rows.append({
        "year": year,
        "ln_income_rel": ln_y,
        "ln_consumer_price_rel": ln_p,
        "ln_house_price_rel": ln_h,
        "x_c": x_c,
        "x_h": x_h,
        "gap_housing_minus_consumption": gap,
        "delta_x_c": dx_c,
        "delta_x_h": dx_h,
        "delta_gap": dgap,
    })

    prev_xc = x_c
    prev_xh = x_h
    prev_gap = gap


for i, row in enumerate(rows):
    for window in (5, 10):
        row[f"slope_x_c_{window}y"] = trailing_slope(
            rows, i, "x_c", window
        )
        row[f"slope_x_h_{window}y"] = trailing_slope(
            rows, i, "x_h", window
        )
        row[f"slope_gap_{window}y"] = trailing_slope(
            rows, i, "gap_housing_minus_consumption", window
        )

    sc = row["slope_x_c_5y"]
    sh = row["slope_x_h_5y"]

    if sc is None or sh is None:
        row["regime_signature_5y"] = ""
    elif sc >= 0 and sh >= 0:
        row["regime_signature_5y"] = "C_UP_H_UP"
    elif sc >= 0 and sh < 0:
        row["regime_signature_5y"] = "C_UP_H_DOWN"
    elif sc < 0 and sh >= 0:
        row["regime_signature_5y"] = "C_DOWN_H_UP"
    else:
        row["regime_signature_5y"] = "C_DOWN_H_DOWN"


# ------------------------------------------------------------------
# Zero crossings of housing coordinate
# ------------------------------------------------------------------

zero_crossings = []

for prev, curr in zip(rows[:-1], rows[1:]):
    a = prev["x_h"]
    b = curr["x_h"]

    if a == 0:
        continue

    if a < 0 <= b:
        zero_crossings.append(
            f"{prev['year']}->{curr['year']}: NEG_TO_NONNEG"
        )

    elif a > 0 >= b:
        zero_crossings.append(
            f"{prev['year']}->{curr['year']}: POS_TO_NONPOS"
        )


# ------------------------------------------------------------------
# Consecutive descriptive 5y-sign regimes
# ------------------------------------------------------------------

regime_rows = []

valid = [
    r for r in rows
    if r["regime_signature_5y"]
]

if valid:
    start = valid[0]["year"]
    prev_year = valid[0]["year"]
    label = valid[0]["regime_signature_5y"]

    for r in valid[1:]:
        year = r["year"]
        current_label = r["regime_signature_5y"]

        if year == prev_year + 1 and current_label == label:
            prev_year = year
            continue

        regime_rows.append({
            "start_year": start,
            "end_year": prev_year,
            "years": prev_year - start + 1,
            "signature": label,
        })

        start = year
        prev_year = year
        label = current_label

    regime_rows.append({
        "start_year": start,
        "end_year": prev_year,
        "years": prev_year - start + 1,
        "signature": label,
    })


# ------------------------------------------------------------------
# Checkpoints every five years + final year
# ------------------------------------------------------------------

checkpoint_years = [
    y for y in years
    if y == REF_YEAR or y % 5 == 0
]

if years[-1] not in checkpoint_years:
    checkpoint_years.append(years[-1])

by_year = {r["year"]: r for r in rows}

checkpoint_lines = []

for year in checkpoint_years:
    r = by_year[year]

    checkpoint_lines.append(
        f"{year}: "
        f"x_C={r['x_c']:+.6f} "
        f"x_H={r['x_h']:+.6f} "
        f"GAP={r['gap_housing_minus_consumption']:+.6f} "
        f"SLOPE_C_5Y="
        f"{'NA' if r['slope_x_c_5y'] is None else f'{r['slope_x_c_5y']:+.6f}'} "
        f"SLOPE_H_5Y="
        f"{'NA' if r['slope_x_h_5y'] is None else f'{r['slope_x_h_5y']:+.6f}'} "
        f"REGIME={r['regime_signature_5y'] or 'NA'}"
    )


# ------------------------------------------------------------------
# Extremes
# ------------------------------------------------------------------

min_xh = min(rows, key=lambda r: r["x_h"])
max_xh = max(rows, key=lambda r: r["x_h"])

delta_rows = [r for r in rows if r["delta_x_h"] is not None]

worst_h_year = min(delta_rows, key=lambda r: r["delta_x_h"])
best_h_year = max(delta_rows, key=lambda r: r["delta_x_h"])

largest_gap_widen = max(delta_rows, key=lambda r: r["delta_gap"])
largest_gap_narrow = min(delta_rows, key=lambda r: r["delta_gap"])


# ------------------------------------------------------------------
# Write CSVs
# ------------------------------------------------------------------

OUT_DATA.parent.mkdir(parents=True, exist_ok=True)
OUT_REGIMES.parent.mkdir(parents=True, exist_ok=True)
OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)

with OUT_DATA.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

with OUT_REGIMES.open("w", newline="", encoding="utf-8") as f:
    fields = ["start_year", "end_year", "years", "signature"]
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(regime_rows)


last = rows[-1]

summary = "\n".join([
    "=" * 100,
    "ECONOMIC GEOMETRY RESEARCH — E2C TEMPORAL DECOMPOSITION",
    "=" * 100,
    "",
    f"REFERENCE_YEAR={REF_YEAR}",
    f"START_YEAR={rows[0]['year']}",
    f"END_YEAR={rows[-1]['year']}",
    f"COMPLETE_YEARS={len(rows)}",
    "",
    "===== ENDPOINT COMPONENTS =====",
    f"LN_INCOME_REL={last['ln_income_rel']:.9f}",
    f"LN_CONSUMER_PRICE_REL={last['ln_consumer_price_rel']:.9f}",
    f"LN_HOUSE_PRICE_REL={last['ln_house_price_rel']:.9f}",
    f"X_C={last['x_c']:.9f}",
    f"X_H={last['x_h']:.9f}",
    f"GAP_H_MINUS_P={last['gap_housing_minus_consumption']:.9f}",
    "",
    "===== HOUSING ACCESS RANGE =====",
    f"MIN_X_H_YEAR={min_xh['year']}",
    f"MIN_X_H={min_xh['x_h']:.9f}",
    f"MAX_X_H_YEAR={max_xh['year']}",
    f"MAX_X_H={max_xh['x_h']:.9f}",
    "",
    "===== ANNUAL DYNAMICS EXTREMES =====",
    f"WORST_ANNUAL_H_YEAR={worst_h_year['year']}",
    f"WORST_ANNUAL_DELTA_X_H={worst_h_year['delta_x_h']:.9f}",
    f"BEST_ANNUAL_H_YEAR={best_h_year['year']}",
    f"BEST_ANNUAL_DELTA_X_H={best_h_year['delta_x_h']:.9f}",
    f"LARGEST_GAP_WIDEN_YEAR={largest_gap_widen['year']}",
    f"LARGEST_DELTA_GAP={largest_gap_widen['delta_gap']:.9f}",
    f"LARGEST_GAP_NARROW_YEAR={largest_gap_narrow['year']}",
    f"SMALLEST_DELTA_GAP={largest_gap_narrow['delta_gap']:.9f}",
    "",
    "===== X_H ZERO CROSSINGS =====",
    *(zero_crossings if zero_crossings else ["NONE"]),
    "",
    "===== FIVE-YEAR CHECKPOINTS =====",
    *checkpoint_lines,
    "",
    "===== DESCRIPTIVE 5Y-SLOPE REGIME SEGMENTS =====",
    *[
        f"{r['start_year']}-{r['end_year']}: "
        f"{r['signature']} ({r['years']} years)"
        for r in regime_rows
    ],
    "",
    "===== INTERPRETATION LIMIT =====",
    "E2C is exploratory.",
    "Regime signatures are descriptive sign labels, not validated economic regimes.",
    "No structural-break model has yet been fitted.",
    "No Real Inflation scalar is estimated in E2C.",
    "",
])

OUT_SUMMARY.write_text(summary + "\n", encoding="utf-8")

print(summary)
print(f"OUTPUT_DATA={OUT_DATA}")
print(f"OUTPUT_REGIMES={OUT_REGIMES}")
print(f"OUTPUT_SUMMARY={OUT_SUMMARY}")
