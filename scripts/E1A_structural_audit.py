from __future__ import annotations

import csv
import hashlib
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "fred"
META = ROOT / "data" / "metadata"

MANIFEST = META / "E1_series_manifest.tsv"
HASHES = META / "E1_fred_sha256.txt"

MISSING_TOKENS = {"", ".", "NA", "NaN", "nan", "N/A"}

print("=" * 100)
print("ECONOMIC GEOMETRY RESEARCH — E1A US MINIMAL DATA STRUCTURAL AUDIT")
print("RAW INTEGRITY / SCHEMA / TEMPORAL STRUCTURE ONLY")
print("NO H1/H2 CALCULATION / NO ECONOMIC RESULT INSPECTION / NO ML")
print("=" * 100)

hard_errors: list[str] = []
warnings: list[str] = []

# ---------------------------------------------------------------------
# 1. Manifest
# ---------------------------------------------------------------------
if not MANIFEST.exists():
    hard_errors.append(f"MISSING_MANIFEST={MANIFEST}")
    print("\nMANIFEST=FAIL")
    sys.exit(1)

with MANIFEST.open(newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f, delimiter="\t"))

required_manifest_cols = {
    "series_id",
    "role",
    "source",
    "expected_frequency",
    "status",
}

manifest_cols = set(rows[0].keys()) if rows else set()

if manifest_cols != required_manifest_cols:
    hard_errors.append(
        f"MANIFEST_COLUMNS_BAD expected={sorted(required_manifest_cols)} "
        f"got={sorted(manifest_cols)}"
    )

series_ids = [r["series_id"] for r in rows]

if len(series_ids) != len(set(series_ids)):
    hard_errors.append("MANIFEST_DUPLICATE_SERIES_IDS")

print()
print("===== MANIFEST =====")
print(f"SERIES_COUNT={len(rows)}")
print(f"UNIQUE_SERIES_COUNT={len(set(series_ids))}")
print(f"SERIES_IDS={','.join(series_ids)}")

# ---------------------------------------------------------------------
# 2. Frozen SHA256 verification
# ---------------------------------------------------------------------
expected_hashes: dict[str, str] = {}

if not HASHES.exists():
    hard_errors.append(f"MISSING_HASH_FILE={HASHES}")
else:
    for line in HASHES.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            hard_errors.append(f"MALFORMED_HASH_LINE={line!r}")
            continue
        digest, path_text = parts
        expected_hashes[Path(path_text).name] = digest.lower()

print()
print("===== RAW HASH VERIFICATION =====")

hash_pass_count = 0

for sid in series_ids:
    path = RAW / f"{sid}.csv"

    if not path.exists():
        hard_errors.append(f"{sid}:MISSING_RAW_FILE")
        print(f"{sid}: FILE=MISSING")
        continue

    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    expected = expected_hashes.get(path.name)

    if expected is None:
        hard_errors.append(f"{sid}:NO_FROZEN_SHA256")
        status = "FAIL_NO_EXPECTED_HASH"
    elif actual != expected:
        hard_errors.append(
            f"{sid}:SHA256_MISMATCH expected={expected} actual={actual}"
        )
        status = "FAIL_MISMATCH"
    else:
        hash_pass_count += 1
        status = "PASS"

    print(f"{sid}: SHA256={status} ACTUAL={actual}")

print(f"HASH_PASS_COUNT={hash_pass_count}/{len(series_ids)}")

# ---------------------------------------------------------------------
# 3. Structural audit helpers
# ---------------------------------------------------------------------
def cadence_check(dates, frequency: str):
    if len(dates) < 2:
        return 0, Counter()

    diffs = [(b - a).days for a, b in zip(dates[:-1], dates[1:])]
    counts = Counter(diffs)

    bad = 0

    for d in diffs:
        if frequency == "quarterly":
            if not (89 <= d <= 93):
                bad += 1
        elif frequency == "monthly":
            if not (28 <= d <= 31):
                bad += 1
        elif frequency == "weekly":
            if d != 7:
                bad += 1
        else:
            bad += 1

    return bad, counts


print()
print("===== PER-SERIES STRUCTURAL AUDIT =====")

summary = []

for meta in rows:
    sid = meta["series_id"]
    expected_frequency = meta["expected_frequency"]
    source = meta["source"]
    path = RAW / f"{sid}.csv"

    if not path.exists():
        continue

    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        all_rows = list(reader)

    if not all_rows:
        hard_errors.append(f"{sid}:EMPTY_FILE")
        continue

    header = all_rows[0]
    body = all_rows[1:]

    expected_header = ["observation_date", sid]
    if header != expected_header:
        hard_errors.append(
            f"{sid}:BAD_HEADER expected={expected_header!r} got={header!r}"
        )

    parsed_dates = []
    date_parse_errors = 0
    numeric_parse_errors = 0
    missing_values = 0
    nonmissing_values = 0

    raw_date_strings = []

    for row_number, row in enumerate(body, start=2):
        if len(row) != 2:
            hard_errors.append(
                f"{sid}:BAD_COLUMN_COUNT row={row_number} columns={len(row)}"
            )
            continue

        date_text = row[0].strip()
        value_text = row[1].strip()

        raw_date_strings.append(date_text)

        try:
            dt = datetime.strptime(date_text, "%Y-%m-%d").date()
            parsed_dates.append(dt)
        except ValueError:
            date_parse_errors += 1

        if value_text in MISSING_TOKENS:
            missing_values += 1
        else:
            try:
                float(value_text)
                nonmissing_values += 1
            except ValueError:
                numeric_parse_errors += 1

    duplicate_dates = len(raw_date_strings) - len(set(raw_date_strings))

    out_of_order = 0
    if len(parsed_dates) >= 2:
        out_of_order = sum(
            curr <= prev
            for prev, curr in zip(parsed_dates[:-1], parsed_dates[1:])
        )

    cadence_bad, cadence_counts = cadence_check(
        parsed_dates,
        expected_frequency
    )

    # Cadence gaps are reported, but are not automatically a hard failure:
    # they can reflect source coverage or missing observations.
    if cadence_bad:
        warnings.append(
            f"{sid}:UNEXPECTED_CADENCE_INTERVALS={cadence_bad}"
        )

    if date_parse_errors:
        hard_errors.append(f"{sid}:DATE_PARSE_ERRORS={date_parse_errors}")

    if numeric_parse_errors:
        hard_errors.append(
            f"{sid}:NUMERIC_PARSE_ERRORS={numeric_parse_errors}"
        )

    if duplicate_dates:
        hard_errors.append(f"{sid}:DUPLICATE_DATES={duplicate_dates}")

    if out_of_order:
        hard_errors.append(f"{sid}:NON_INCREASING_DATES={out_of_order}")

    start = parsed_dates[0].isoformat() if parsed_dates else "NA"
    end = parsed_dates[-1].isoformat() if parsed_dates else "NA"

    common_diffs = ",".join(
        f"{k}d:{v}"
        for k, v in cadence_counts.most_common(6)
    ) or "NA"

    print()
    print(f"SERIES={sid}")
    print(f"ROLE={meta['role']}")
    print(f"SOURCE={source}")
    print(f"EXPECTED_FREQUENCY={expected_frequency}")
    print(f"ROWS={len(body)}")
    print(f"NONMISSING={nonmissing_values}")
    print(f"MISSING={missing_values}")
    print(f"START={start}")
    print(f"END={end}")
    print(f"DATE_PARSE_ERRORS={date_parse_errors}")
    print(f"NUMERIC_PARSE_ERRORS={numeric_parse_errors}")
    print(f"DUPLICATE_DATES={duplicate_dates}")
    print(f"NON_INCREASING_DATES={out_of_order}")
    print(f"UNEXPECTED_CADENCE_INTERVALS={cadence_bad}")
    print(f"COMMON_DAY_DIFFS={common_diffs}")

    summary.append(
        {
            "series": sid,
            "rows": len(body),
            "start": start,
            "end": end,
            "missing": missing_values,
            "cadence_bad": cadence_bad,
        }
    )

# ---------------------------------------------------------------------
# 4. Raw directory exactness
# ---------------------------------------------------------------------
actual_csvs = sorted(p.name for p in RAW.glob("*.csv"))
expected_csvs = sorted(f"{sid}.csv" for sid in series_ids)

extra_csvs = sorted(set(actual_csvs) - set(expected_csvs))
missing_csvs = sorted(set(expected_csvs) - set(actual_csvs))

print()
print("===== RAW DIRECTORY EXACTNESS =====")
print(f"EXPECTED_CSV_COUNT={len(expected_csvs)}")
print(f"ACTUAL_CSV_COUNT={len(actual_csvs)}")
print(f"EXTRA_CSV={','.join(extra_csvs) if extra_csvs else 'NONE'}")
print(f"MISSING_CSV={','.join(missing_csvs) if missing_csvs else 'NONE'}")

if extra_csvs:
    hard_errors.append(f"EXTRA_RAW_CSV={extra_csvs}")

if missing_csvs:
    hard_errors.append(f"MISSING_RAW_CSV={missing_csvs}")

# ---------------------------------------------------------------------
# 5. Coverage summary
# ---------------------------------------------------------------------
print()
print("===== COVERAGE SUMMARY =====")

for s in summary:
    print(
        f"{s['series']:20s} "
        f"ROWS={s['rows']:5d} "
        f"START={s['start']} "
        f"END={s['end']} "
        f"MISSING={s['missing']:3d} "
        f"CADENCE_WARN={s['cadence_bad']:3d}"
    )

# ---------------------------------------------------------------------
# 6. Final verdict
# ---------------------------------------------------------------------
print()
print("=" * 100)
print("E1A FINAL VERDICT")
print("=" * 100)

print(f"HARD_ERROR_COUNT={len(hard_errors)}")
print(f"WARNING_COUNT={len(warnings)}")

if warnings:
    print()
    print("WARNINGS:")
    for item in warnings:
        print(f"  - {item}")

if hard_errors:
    print()
    print("HARD_ERRORS:")
    for item in hard_errors:
        print(f"  - {item}")

    print()
    print("E1A_STRUCTURAL_AUDIT=FAIL")
    print("H1_H2_CALCULATION_AUTHORIZED=0")
    sys.exit(1)

print()
print("E1A_STRUCTURAL_AUDIT=PASS")
print("RAW_HASH_INTEGRITY=PASS")
print("RAW_SCHEMA_INTEGRITY=PASS")
print("TEMPORAL_ORDER_INTEGRITY=PASS")
print("H1_H2_CALCULATION_AUTHORIZED=1")
