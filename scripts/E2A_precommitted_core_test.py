from __future__ import annotations

import csv
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "fred"
OUT_DATA = ROOT / "data" / "processed" / "E2A_us_core_coordinates.csv"
OUT_SUMMARY = ROOT / "results" / "tables" / "E2A_us_core_summary.txt"

REFERENCE_DATE = "1991-01-01"

SERIES = {
    "Y": "A229RC0Q052SBEA",       # nominal disposable income per capita
    "Y_REAL": "A229RX0Q048SBEA",  # official real DPI per capita QA
    "P": "PCECTPI",               # canonical consumer price index
    "H": "PONHPIM226S",           # canonical house price index
    "C_NOM": "A794RC0Q052SBEA",   # nominal PCE per capita QA
    "C_REAL": "A794RX0Q048SBEA",  # real PCE per capita QA
}


def load_series(series_id: str) -> dict[str, float]:
    path = RAW / f"{series_id}.csv"

    out: dict[str, float] = {}

    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        expected = {"observation_date", series_id}
        if set(reader.fieldnames or []) != expected:
            raise RuntimeError(
                f"{series_id}: unexpected header {reader.fieldnames!r}"
            )

        for row in reader:
            date = row["observation_date"].strip()
            value = row[series_id].strip()

            if value in {"", ".", "NA", "NaN", "nan", "N/A"}:
                continue

            if date in out:
                raise RuntimeError(f"{series_id}: duplicate date {date}")

            out[date] = float(value)

    return out


def pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys):
        raise ValueError("length mismatch")

    if len(xs) < 2:
        return float("nan")

    mx = statistics.fmean(xs)
    my = statistics.fmean(ys)

    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    denx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    deny = math.sqrt(sum((y - my) ** 2 for y in ys))

    if denx == 0 or deny == 0:
        return float("nan")

    return num / (denx * deny)


data = {name: load_series(series_id) for name, series_id in SERIES.items()}

common_dates = sorted(
    set.intersection(*(set(values) for values in data.values()))
)

dates = [d for d in common_dates if d >= REFERENCE_DATE]

if not dates:
    raise RuntimeError("no common dates")

if dates[0] != REFERENCE_DATE:
    raise RuntimeError(
        f"reference mismatch: expected {REFERENCE_DATE}, got {dates[0]}"
    )

# Reference values are frozen by E1B.
y0 = data["Y"][REFERENCE_DATE]
yr0 = data["Y_REAL"][REFERENCE_DATE]
p0 = data["P"][REFERENCE_DATE]
h0 = data["H"][REFERENCE_DATE]
cn0 = data["C_NOM"][REFERENCE_DATE]
cr0 = data["C_REAL"][REFERENCE_DATE]

rows = []

qa_dpi_relative_errors = []
qa_pce_relative_errors = []

prev_xc = None
prev_xh = None

for date in dates:
    y = data["Y"][date]
    yr = data["Y_REAL"][date]
    p = data["P"][date]
    h = data["H"][date]
    cn = data["C_NOM"][date]
    cr = data["C_REAL"][date]

    y_rel = y / y0
    p_rel = p / p0
    h_rel = h / h0

    # H2 core coordinates
    cpp = y_rel / p_rel
    ha = y_rel / h_rel

    x_c = math.log(cpp)
    x_h = math.log(ha)

    divergence = x_c - x_h

    delta_x_c = None if prev_xc is None else x_c - prev_xc
    delta_x_h = None if prev_xh is None else x_h - prev_xh

    # ---------------------------------------------------------------
    # Independent QA:
    # Nominal income / PCE deflator should track official real DPI.
    # Nominal PCE / PCE deflator should track official real PCE.
    # Everything is compared after rebasing to the same reference.
    # ---------------------------------------------------------------

    official_real_dpi_rel = yr / yr0
    reconstructed_real_dpi_rel = cpp

    official_real_pce_rel = cr / cr0
    reconstructed_real_pce_rel = (cn / cn0) / p_rel

    dpi_error = abs(
        reconstructed_real_dpi_rel / official_real_dpi_rel - 1.0
    )

    pce_error = abs(
        reconstructed_real_pce_rel / official_real_pce_rel - 1.0
    )

    qa_dpi_relative_errors.append(dpi_error)
    qa_pce_relative_errors.append(pce_error)

    rows.append(
        {
            "date": date,
            "income_rel": y_rel,
            "consumer_price_rel": p_rel,
            "house_price_rel": h_rel,
            "cpp_index_1991q1_100": cpp * 100.0,
            "ha_index_1991q1_100": ha * 100.0,
            "x_c": x_c,
            "x_h": x_h,
            "divergence_xc_minus_xh": divergence,
            "delta_x_c": delta_x_c,
            "delta_x_h": delta_x_h,
            "qa_real_dpi_relative_error": dpi_error,
            "qa_real_pce_relative_error": pce_error,
        }
    )

    prev_xc = x_c
    prev_xh = x_h


OUT_DATA.parent.mkdir(parents=True, exist_ok=True)
OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)

fieldnames = [
    "date",
    "income_rel",
    "consumer_price_rel",
    "house_price_rel",
    "cpp_index_1991q1_100",
    "ha_index_1991q1_100",
    "x_c",
    "x_h",
    "divergence_xc_minus_xh",
    "delta_x_c",
    "delta_x_h",
    "qa_real_dpi_relative_error",
    "qa_real_pce_relative_error",
]

with OUT_DATA.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()

    for row in rows:
        writer.writerow(row)


xcs = [r["x_c"] for r in rows]
xhs = [r["x_h"] for r in rows]

dxcs = [
    r["delta_x_c"]
    for r in rows
    if r["delta_x_c"] is not None
]

dxhs = [
    r["delta_x_h"]
    for r in rows
    if r["delta_x_h"] is not None
]

if len(dxcs) != len(dxhs):
    raise RuntimeError("delta alignment failure")

p2_quarters = [
    r for r in rows
    if r["delta_x_c"] is not None
    and r["delta_x_c"] > 0
    and r["delta_x_h"] < 0
]

reverse_quarters = [
    r for r in rows
    if r["delta_x_c"] is not None
    and r["delta_x_c"] < 0
    and r["delta_x_h"] > 0
]

both_positive = [
    r for r in rows
    if r["delta_x_c"] is not None
    and r["delta_x_c"] > 0
    and r["delta_x_h"] > 0
]

both_negative = [
    r for r in rows
    if r["delta_x_c"] is not None
    and r["delta_x_c"] < 0
    and r["delta_x_h"] < 0
]

level_corr = pearson(xcs, xhs)
delta_corr = pearson(dxcs, dxhs)

last = rows[-1]

lines = [
    "=" * 100,
    "ECONOMIC GEOMETRY RESEARCH — E2A PRECOMMITTED US CORE H1/H2 TEST",
    "=" * 100,
    "",
    f"REFERENCE_DATE={REFERENCE_DATE}",
    f"START_DATE={rows[0]['date']}",
    f"END_DATE={rows[-1]['date']}",
    f"QUARTERS={len(rows)}",
    "",
    "===== QA =====",
    f"MAX_REAL_DPI_RECONSTRUCTION_RELATIVE_ERROR={max(qa_dpi_relative_errors):.12f}",
    f"MAX_REAL_PCE_RECONSTRUCTION_RELATIVE_ERROR={max(qa_pce_relative_errors):.12f}",
    "",
    "===== ENDPOINT RELATIVE TO 1991Q1 =====",
    f"CPP_INDEX={last['cpp_index_1991q1_100']:.6f}",
    f"HA_INDEX={last['ha_index_1991q1_100']:.6f}",
    f"X_C={last['x_c']:.9f}",
    f"X_H={last['x_h']:.9f}",
    f"DIVERGENCE_XC_MINUS_XH={last['divergence_xc_minus_xh']:.9f}",
    "",
    "===== DESCRIPTIVE DEPENDENCE =====",
    f"LEVEL_PEARSON_CORR_XC_XH={level_corr:.9f}",
    f"DELTA_PEARSON_CORR_DXC_DXH={delta_corr:.9f}",
    "",
    "===== PRECOMMITTED SIGN TEST =====",
    f"AVAILABLE_DELTA_QUARTERS={len(dxcs)}",
    f"DXC_POS_DXH_NEG={len(p2_quarters)}",
    f"DXC_NEG_DXH_POS={len(reverse_quarters)}",
    f"DXC_POS_DXH_POS={len(both_positive)}",
    f"DXC_NEG_DXH_NEG={len(both_negative)}",
    f"P2_EXISTS={int(len(p2_quarters) > 0)}",
    "",
    "===== IDENTITY CHECK =====",
    "DIVERGENCE_XC_MINUS_XH = ln(HOUSE_PRICE_REL / CONSUMER_PRICE_REL)",
    "Income cancels algebraically from this divergence quantity.",
    "",
    "===== INTERPRETATION LIMIT =====",
    "P2_EXISTS=1 is evidence that consumption and housing-access changes can move in opposite directions.",
    "It does NOT establish H1 multidimensionality by itself.",
    "No causal claim is authorized.",
    "",
]

summary = "\n".join(lines)

OUT_SUMMARY.write_text(summary + "\n", encoding="utf-8")

print(summary)
print(f"OUTPUT_DATA={OUT_DATA}")
print(f"OUTPUT_SUMMARY={OUT_SUMMARY}")
