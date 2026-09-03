from __future__ import annotations

import csv
import hashlib
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

INPUT = ROOT / "data" / "processed" / "E2C_annual_decomposition.csv"

OUT_MODELS = ROOT / "results" / "tables" / "E2D_model_selection.csv"
OUT_SEGMENTS = ROOT / "results" / "tables" / "E2D_selected_segments.csv"
OUT_SENS = ROOT / "results" / "tables" / "E2D_sensitivity.csv"
OUT_SUMMARY = ROOT / "results" / "tables" / "E2D_summary.txt"

EXPECTED_INPUT_SHA256 = (
    "6d3fe1beb27c59ce5771f298e5324fc07dad30173b3e8996944a3c806ad23221"
)

PRIMARY_MIN_LEN = 5
SENSITIVITY_MIN_LENS = (4, 6)
MAX_SEGMENTS = 8
D = 2


def sha256(path: Path) -> str:
    h = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)

    return h.hexdigest()


actual_hash = sha256(INPUT)

if actual_hash != EXPECTED_INPUT_SHA256:
    raise RuntimeError(
        "E2C input hash mismatch: "
        f"expected={EXPECTED_INPUT_SHA256} actual={actual_hash}"
    )


years: list[int] = []
raw_z: list[tuple[float, float]] = []

with INPUT.open(newline="", encoding="utf-8") as f:
    r = csv.DictReader(f)

    for row in r:
        dxc = row["delta_x_c"].strip()
        dxh = row["delta_x_h"].strip()

        if not dxc or not dxh:
            continue

        years.append(int(row["year"]))
        raw_z.append((float(dxc), float(dxh)))


if not raw_z:
    raise RuntimeError("no delta observations")

if years[0] != 1976 or years[-1] != 2025:
    raise RuntimeError(
        f"unexpected year range: {years[0]}-{years[-1]}"
    )

if any(b - a != 1 for a, b in zip(years[:-1], years[1:])):
    raise RuntimeError("annual changes are not consecutive")


T = len(raw_z)
N = T * D


# =============================================================================
# Prefix sums for exact segment SSE
# =============================================================================

prefix = [[0.0] * (T + 1) for _ in range(D)]
prefix_sq = [[0.0] * (T + 1) for _ in range(D)]

for i, z in enumerate(raw_z, start=1):
    for d in range(D):
        value = z[d]

        prefix[d][i] = prefix[d][i - 1] + value
        prefix_sq[d][i] = prefix_sq[d][i - 1] + value * value


def segment_sse(i: int, j: int) -> float:
    """
    SSE for observations [i, j), zero-based.
    """
    n = j - i

    if n <= 0:
        raise ValueError("empty segment")

    total = 0.0

    for d in range(D):
        s = prefix[d][j] - prefix[d][i]
        ss = prefix_sq[d][j] - prefix_sq[d][i]

        total += ss - (s * s) / n

    # Numerical guard.
    return max(total, 0.0)


def segment_mean(i: int, j: int) -> tuple[float, float]:
    n = j - i

    vals = []

    for d in range(D):
        s = prefix[d][j] - prefix[d][i]
        vals.append(s / n)

    return vals[0], vals[1]


def signature(mc: float, mh: float) -> str:
    if mc >= 0 and mh >= 0:
        return "C_UP_H_UP"

    if mc >= 0 and mh < 0:
        return "C_UP_H_DOWN"

    if mc < 0 and mh >= 0:
        return "C_DOWN_H_UP"

    return "C_DOWN_H_DOWN"


def solve(min_len: int, max_segments: int):
    feasible_max = min(max_segments, T // min_len)

    inf = float("inf")

    # dp[m][j] = best SSE for first j observations using m segments
    dp = [
        [inf] * (T + 1)
        for _ in range(feasible_max + 1)
    ]

    prev = [
        [None] * (T + 1)
        for _ in range(feasible_max + 1)
    ]

    dp[0][0] = 0.0

    for m in range(1, feasible_max + 1):
        min_j = m * min_len

        for j in range(min_j, T + 1):
            start_min = (m - 1) * min_len
            start_max = j - min_len

            for i in range(start_min, start_max + 1):
                if dp[m - 1][i] == inf:
                    continue

                candidate = dp[m - 1][i] + segment_sse(i, j)

                if candidate < dp[m][j]:
                    dp[m][j] = candidate
                    prev[m][j] = i

    models = []

    for m in range(1, feasible_max + 1):
        sse = dp[m][T]

        if not math.isfinite(sse):
            continue

        p = 2 * m + (m - 1)

        mse = max(sse / N, 1e-15)

        bic = N * math.log(mse) + p * math.log(N)

        models.append({
            "segments": m,
            "breaks": m - 1,
            "sse": sse,
            "parameters": p,
            "bic": bic,
        })

    if not models:
        raise RuntimeError("no feasible segmentation models")

    selected = min(models, key=lambda x: x["bic"])

    m = selected["segments"]
    j = T

    bounds = []

    while m > 0:
        i = prev[m][j]

        if i is None:
            raise RuntimeError("failed to reconstruct segmentation")

        bounds.append((i, j))

        j = i
        m -= 1

    bounds.reverse()

    segments = []

    for seg_num, (i, j) in enumerate(bounds, start=1):
        mc, mh = segment_mean(i, j)

        segments.append({
            "segment": seg_num,
            "start_year": years[i],
            "end_year": years[j - 1],
            "n_years": j - i,
            "mean_delta_x_c": mc,
            "mean_delta_x_h": mh,
            "signature": signature(mc, mh),
        })

    breaks = [
        seg["start_year"]
        for seg in segments[1:]
    ]

    return models, selected, segments, breaks


# =============================================================================
# Primary specification
# =============================================================================

models, selected, segments, breaks = solve(
    PRIMARY_MIN_LEN,
    MAX_SEGMENTS,
)


OUT_MODELS.parent.mkdir(parents=True, exist_ok=True)

with OUT_MODELS.open("w", newline="", encoding="utf-8") as f:
    fields = ["segments", "breaks", "sse", "parameters", "bic"]

    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(models)


with OUT_SEGMENTS.open("w", newline="", encoding="utf-8") as f:
    fields = [
        "segment",
        "start_year",
        "end_year",
        "n_years",
        "mean_delta_x_c",
        "mean_delta_x_h",
        "signature",
    ]

    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(segments)


# =============================================================================
# Sensitivity specifications
# =============================================================================

sens_rows = []

for min_len in SENSITIVITY_MIN_LENS:
    _, sel, segs, brks = solve(min_len, MAX_SEGMENTS)

    sens_rows.append({
        "min_segment_length": min_len,
        "selected_segments": sel["segments"],
        "selected_breaks": sel["breaks"],
        "bic": sel["bic"],
        "break_years": ",".join(str(x) for x in brks) if brks else "NONE",
    })


with OUT_SENS.open("w", newline="", encoding="utf-8") as f:
    fields = [
        "min_segment_length",
        "selected_segments",
        "selected_breaks",
        "bic",
        "break_years",
    ]

    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(sens_rows)


# =============================================================================
# Summary
# =============================================================================

segment_lines = [
    (
        f"SEGMENT_{r['segment']}="
        f"{r['start_year']}-{r['end_year']} "
        f"N={r['n_years']} "
        f"MEAN_DXC={r['mean_delta_x_c']:+.9f} "
        f"MEAN_DXH={r['mean_delta_x_h']:+.9f} "
        f"SIGNATURE={r['signature']}"
    )
    for r in segments
]

sensitivity_lines = [
    (
        f"MINLEN_{r['min_segment_length']}: "
        f"SEGMENTS={r['selected_segments']} "
        f"BREAKS={r['break_years']}"
    )
    for r in sens_rows
]

summary = "\n".join([
    "=" * 100,
    "ECONOMIC GEOMETRY RESEARCH — E2D PRECOMMITTED CHANGE-POINT DETECTION",
    "=" * 100,
    "",
    f"INPUT_SHA256={actual_hash}",
    f"START_CHANGE_YEAR={years[0]}",
    f"END_CHANGE_YEAR={years[-1]}",
    f"ANNUAL_CHANGE_OBSERVATIONS={T}",
    f"PRIMARY_MIN_SEGMENT_LENGTH={PRIMARY_MIN_LEN}",
    f"MAX_SEGMENTS={MAX_SEGMENTS}",
    "",
    "===== PRIMARY BIC SELECTION =====",
    f"SELECTED_SEGMENTS={selected['segments']}",
    f"SELECTED_BREAKS={selected['breaks']}",
    f"SELECTED_SSE={selected['sse']:.12f}",
    f"SELECTED_BIC={selected['bic']:.9f}",
    (
        "BREAK_YEARS="
        + (",".join(str(x) for x in breaks) if breaks else "NONE")
    ),
    "",
    "===== SELECTED SEGMENTS =====",
    *segment_lines,
    "",
    "===== MINIMUM-SEGMENT-LENGTH SENSITIVITY =====",
    *sensitivity_lines,
    "",
    "===== INTERPRETATION LIMIT =====",
    "Break years were selected without historical event labels.",
    "E2D detects changes in the mean annual [Delta x_C, Delta x_H] vector.",
    "Detected segments are descriptive statistical regimes, not causal regimes.",
    "Historical interpretation occurs only after this output is frozen.",
    "No Real Inflation scalar is estimated in E2D.",
    "",
])

OUT_SUMMARY.write_text(summary + "\n", encoding="utf-8")

print(summary)

print(f"OUTPUT_MODELS={OUT_MODELS}")
print(f"OUTPUT_SEGMENTS={OUT_SEGMENTS}")
print(f"OUTPUT_SENSITIVITY={OUT_SENS}")
print(f"OUTPUT_SUMMARY={OUT_SUMMARY}")
