from __future__ import annotations

import csv
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "fred"

OUT_CPI = ROOT / "data" / "processed" / "E2B_cpi_quarterly_robustness.csv"
OUT_LONG = ROOT / "data" / "processed" / "E2B_longrun_annual_robustness.csv"
OUT_SUMMARY = ROOT / "results" / "tables" / "E2B_robustness_summary.txt"

MISSING = {"", ".", "NA", "NaN", "nan", "N/A"}

SERIES = {
    "Y": "A229RC0Q052SBEA",
    "PCE": "PCECTPI",
    "CPI": "CPIAUCSL",
    "H_CORE": "PONHPIM226S",
    "H_LONG": "USSTHPI",
}


def load(series_id: str) -> dict[str, float]:
    path = RAW / f"{series_id}.csv"
    out: dict[str, float] = {}

    with path.open(newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)

        for row in r:
            d = row["observation_date"].strip()
            v = row[series_id].strip()

            if v in MISSING:
                continue

            if d in out:
                raise RuntimeError(f"{series_id}: duplicate {d}")

            out[d] = float(v)

    return out


def quarter_start(date_text: str) -> str:
    d = datetime.strptime(date_text, "%Y-%m-%d")
    qmonth = ((d.month - 1) // 3) * 3 + 1
    return f"{d.year:04d}-{qmonth:02d}-01"


def quarter_ordinal(date_text: str) -> int:
    d = datetime.strptime(date_text, "%Y-%m-%d")
    q = (d.month - 1) // 3
    return d.year * 4 + q


def complete_quarterly_mean_monthly(
    values: dict[str, float]
) -> dict[str, float]:
    groups: dict[str, list[tuple[int, float]]] = defaultdict(list)

    for d, v in values.items():
        dt = datetime.strptime(d, "%Y-%m-%d")
        groups[quarter_start(d)].append((dt.month, v))

    out: dict[str, float] = {}

    for qdate, obs in groups.items():
        qdt = datetime.strptime(qdate, "%Y-%m-%d")
        expected_months = {
            qdt.month,
            qdt.month + 1,
            qdt.month + 2,
        }

        observed_months = {m for m, _ in obs}

        if len(obs) == 3 and observed_months == expected_months:
            out[qdate] = sum(v for _, v in obs) / 3.0

    return out


def complete_annual_mean_quarterly(
    values: dict[str, float]
) -> dict[int, float]:
    groups: dict[int, list[tuple[int, float]]] = defaultdict(list)

    for d, v in values.items():
        dt = datetime.strptime(d, "%Y-%m-%d")

        if dt.month not in {1, 4, 7, 10}:
            raise RuntimeError(f"unexpected quarterly date {d}")

        groups[dt.year].append((dt.month, v))

    out: dict[int, float] = {}

    for year, obs in groups.items():
        months = {m for m, _ in obs}

        if len(obs) == 4 and months == {1, 4, 7, 10}:
            out[year] = sum(v for _, v in obs) / 4.0

    return out


raw = {k: load(v) for k, v in SERIES.items()}

# =============================================================================
# TEST A — CPI ROBUSTNESS, QUARTERLY
# =============================================================================

cpi_q = complete_quarterly_mean_monthly(raw["CPI"])

ref_q = "1991-01-01"

common_q = sorted(
    set(raw["Y"])
    & set(raw["H_CORE"])
    & set(cpi_q)
)

common_q = [d for d in common_q if d >= ref_q]

if not common_q or common_q[0] != ref_q:
    raise RuntimeError("CPI robustness reference quarter unavailable")

y0 = raw["Y"][ref_q]
cpi0 = cpi_q[ref_q]
h0 = raw["H_CORE"][ref_q]

cpi_rows = []

prev = None

for d in common_q:
    y_rel = raw["Y"][d] / y0
    p_rel = cpi_q[d] / cpi0
    h_rel = raw["H_CORE"][d] / h0

    xc = math.log(y_rel / p_rel)
    xh = math.log(y_rel / h_rel)

    dxc = None
    dxh = None

    if prev is not None:
        prev_date, prev_xc, prev_xh = prev

        # Never bridge a missing quarter.
        if quarter_ordinal(d) - quarter_ordinal(prev_date) == 1:
            dxc = xc - prev_xc
            dxh = xh - prev_xh

    cpi_rows.append({
        "date": d,
        "x_c_cpi": xc,
        "x_h_core": xh,
        "divergence": xc - xh,
        "delta_x_c": dxc,
        "delta_x_h": dxh,
    })

    prev = (d, xc, xh)


valid_cpi_delta = [
    r for r in cpi_rows
    if r["delta_x_c"] is not None
]

cpi_pred = [
    r for r in valid_cpi_delta
    if r["delta_x_c"] > 0 and r["delta_x_h"] < 0
]

cpi_rev = [
    r for r in valid_cpi_delta
    if r["delta_x_c"] < 0 and r["delta_x_h"] > 0
]

cpi_last = cpi_rows[-1]

cpi_endpoint_replication = (
    cpi_last["x_c_cpi"] > 0
    and cpi_last["x_h_core"] < 0
)

cpi_discordance_replication = len(cpi_pred) > len(cpi_rev)


# =============================================================================
# TEST B — LONG-RUN ROBUSTNESS, ANNUAL
# =============================================================================

y_a = complete_annual_mean_quarterly(raw["Y"])
p_a = complete_annual_mean_quarterly(raw["PCE"])
h_a = complete_annual_mean_quarterly(raw["H_LONG"])

common_y = sorted(set(y_a) & set(p_a) & set(h_a))
common_y = [y for y in common_y if y >= 1975]

if not common_y or common_y[0] != 1975:
    raise RuntimeError("long-run reference year unavailable")

ref_y = 1975

y0a = y_a[ref_y]
p0a = p_a[ref_y]
h0a = h_a[ref_y]

long_rows = []

prev = None

for year in common_y:
    y_rel = y_a[year] / y0a
    p_rel = p_a[year] / p0a
    h_rel = h_a[year] / h0a

    xc = math.log(y_rel / p_rel)
    xh = math.log(y_rel / h_rel)

    dxc = None
    dxh = None

    if prev is not None:
        prev_year, prev_xc, prev_xh = prev

        if year - prev_year == 1:
            dxc = xc - prev_xc
            dxh = xh - prev_xh

    long_rows.append({
        "year": year,
        "x_c_long": xc,
        "x_h_long": xh,
        "divergence": xc - xh,
        "delta_x_c": dxc,
        "delta_x_h": dxh,
    })

    prev = (year, xc, xh)


valid_long_delta = [
    r for r in long_rows
    if r["delta_x_c"] is not None
]

long_pred = [
    r for r in valid_long_delta
    if r["delta_x_c"] > 0 and r["delta_x_h"] < 0
]

long_rev = [
    r for r in valid_long_delta
    if r["delta_x_c"] < 0 and r["delta_x_h"] > 0
]

long_last = long_rows[-1]

long_endpoint_replication = (
    long_last["x_c_long"] > 0
    and long_last["x_h_long"] < 0
)

long_discordance_replication = len(long_pred) > len(long_rev)

e2b_survives = (
    cpi_last["x_c_cpi"] > 0
    and cpi_last["x_h_core"] < 0
    and long_last["x_c_long"] > 0
    and long_last["x_h_long"] < 0
)


# =============================================================================
# WRITE OUTPUTS
# =============================================================================

OUT_CPI.parent.mkdir(parents=True, exist_ok=True)
OUT_LONG.parent.mkdir(parents=True, exist_ok=True)
OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, rows: list[dict]):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


write_csv(OUT_CPI, cpi_rows)
write_csv(OUT_LONG, long_rows)

summary = f"""\
====================================================================================================
ECONOMIC GEOMETRY RESEARCH — E2B PRECOMMITTED ROBUSTNESS ATTACK
====================================================================================================

===== TEST A: CPI QUARTERLY ROBUSTNESS =====
REFERENCE_QUARTER={ref_q}
START_QUARTER={cpi_rows[0]['date']}
END_QUARTER={cpi_rows[-1]['date']}
VALID_LEVEL_QUARTERS={len(cpi_rows)}
VALID_CONSECUTIVE_DELTAS={len(valid_cpi_delta)}
ENDPOINT_X_C_CPI={cpi_last['x_c_cpi']:.9f}
ENDPOINT_X_H_CORE={cpi_last['x_h_core']:.9f}
ENDPOINT_REPLICATION={int(cpi_endpoint_replication)}
PREDICTED_DISCORDANCE_COUNT={len(cpi_pred)}
REVERSE_DISCORDANCE_COUNT={len(cpi_rev)}
DISCORDANCE_DIRECTION_REPLICATION={int(cpi_discordance_replication)}

===== TEST B: LONG-RUN ANNUAL ROBUSTNESS =====
REFERENCE_YEAR={ref_y}
START_YEAR={long_rows[0]['year']}
END_YEAR={long_rows[-1]['year']}
VALID_YEARS={len(long_rows)}
VALID_CONSECUTIVE_YEAR_DELTAS={len(valid_long_delta)}
ENDPOINT_X_C_LONG={long_last['x_c_long']:.9f}
ENDPOINT_X_H_LONG={long_last['x_h_long']:.9f}
ENDPOINT_REPLICATION={int(long_endpoint_replication)}
PREDICTED_DISCORDANCE_COUNT={len(long_pred)}
REVERSE_DISCORDANCE_COUNT={len(long_rev)}
DISCORDANCE_DIRECTION_REPLICATION={int(long_discordance_replication)}

===== PRECOMMITTED E2B VERDICT =====
E2B_ROBUSTNESS_SURVIVES={int(e2b_survives)}

===== LIMITS =====
E2B is not an independent statistical replication.
The US observations overlap E2A.
No causal claim is authorized.
H1 multidimensionality is not established by E2B.
"""

OUT_SUMMARY.write_text(summary, encoding="utf-8")

print(summary)
print(f"OUTPUT_CPI={OUT_CPI}")
print(f"OUTPUT_LONG={OUT_LONG}")
print(f"OUTPUT_SUMMARY={OUT_SUMMARY}")
