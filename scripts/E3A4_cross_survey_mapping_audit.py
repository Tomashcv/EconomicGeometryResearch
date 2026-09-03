from __future__ import annotations

import csv
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CONTRACT = ROOT / "docs" / "E3A4_cross_survey_cohort_mapping.md"
MAPPING = ROOT / "data" / "metadata" / "E3A4_mapping.tsv"
CEX_ZIP = ROOT / "data" / "raw" / "cex" / "2022" / "intrvw22.zip"

OUT = ROOT / "data" / "metadata" / "E3A4_mapping_audit.txt"

EXPECTED_CEX_SHA = (
    "c99a2f47c0084b7a88812b34c56a1a288be2798ff010b2b59dcf87e072773e17"
)

EXPECTED_CEX_CODES = {"1", "2", "3", "4", "5", "6"}


def sha256(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()

    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)

    return h.hexdigest()


# -----------------------------------------------------------------------------
# Contract invariants
# -----------------------------------------------------------------------------

text = CONTRACT.read_text(encoding="utf-8")

required_contract_tokens = [
    "G1 = AGE_BAND × TENURE",
    "G2_CANONICAL_AUTHORIZED = 0",
    "CUTENURE in {1,2,3} -> OWNER",
    "CUTENURE == 4 -> RENTER",
    "H_TENURE == 1 -> OWNER",
    "H_TENURE == 2 -> RENTER",
    "A_EXPRRP in {1,2}",
    "PH_SEQ == H_SEQ",
    "X508 in {1,2}",
    "X601 in {1,2,3}",
    "X701 in {1,3,4,5,6,8}",
    "X508 == 3",
    "X601 == 4",
    "X701 == 2",
    "SUPPORT_MEMBERSHIP = AMBIGUOUS",
    "E3A5_2022_SUPPORT_COUNTS_AUTHORIZED = 1",
]

for token in required_contract_tokens:
    if token not in text:
        raise RuntimeError(f"missing contract token: {token}")


# -----------------------------------------------------------------------------
# Mapping-table invariants
# -----------------------------------------------------------------------------

with MAPPING.open(encoding="utf-8") as f:
    rows = list(csv.DictReader(f, delimiter="\t"))

if len(rows) != 24:
    raise RuntimeError(f"unexpected mapping row count: {len(rows)}")

surveys = {r["survey"] for r in rows}

if surveys != {"CEX", "CPS", "SCF"}:
    raise RuntimeError(f"unexpected surveys: {surveys}")

g2_rows = [
    r for r in rows
    if r["concept"] == "children"
]

if len(g2_rows) != 3:
    raise RuntimeError("expected one children semantic row per survey")

if any(r["status"] != "G2_BLOCKED" for r in g2_rows):
    raise RuntimeError("G2 children mapping must remain blocked")


# -----------------------------------------------------------------------------
# CEX 2022 category-code sanity check
#
# Authorized inspection:
#   CUTENURE categorical values only.
#
# Explicitly NOT calculated:
#   frequencies
#   row counts
#   cohort counts
#   monetary values
# -----------------------------------------------------------------------------

if not CEX_ZIP.exists():
    raise RuntimeError("canonical CEX 2022 archive missing")

actual_sha = sha256(CEX_ZIP)

if actual_sha != EXPECTED_CEX_SHA:
    raise RuntimeError(
        f"CEX hash mismatch expected={EXPECTED_CEX_SHA} actual={actual_sha}"
    )

observed_codes: set[str] = set()

with zipfile.ZipFile(CEX_ZIP) as zf:
    members = sorted(
        n for n in zf.namelist()
        if Path(n).name.lower().startswith("fmli")
        and Path(n).suffix.lower() == ".csv"
    )

    if len(members) != 4:
        raise RuntimeError(f"expected 4 FMLI files, found {len(members)}")

    for member in members:
        import io

        with zf.open(member, "r") as raw:
            text_stream = io.TextIOWrapper(
                raw,
                encoding="utf-8-sig",
                errors="replace",
                newline="",
            )

            reader = csv.DictReader(text_stream)

            fields = {x.upper() for x in (reader.fieldnames or [])}

            if "CUTENURE" not in fields:
                raise RuntimeError(f"{member}: CUTENURE absent")

            # Find original-case header spelling.
            tenure_field = next(
                x for x in (reader.fieldnames or [])
                if x.upper() == "CUTENURE"
            )

            for row in reader:
                value = row[tenure_field].strip()

                if value:
                    observed_codes.add(value)


unexpected = sorted(observed_codes - EXPECTED_CEX_CODES)

if unexpected:
    raise RuntimeError(
        f"unexpected CEX CUTENURE codes: {unexpected}"
    )

if "4" not in observed_codes:
    raise RuntimeError("CEX 2022 anchor contains no RENTER code 4")

if not observed_codes.intersection({"1", "2", "3"}):
    raise RuntimeError("CEX 2022 anchor contains no OWNER code")


summary = "\n".join([
    "=" * 100,
    "ECONOMIC GEOMETRY RESEARCH — E3A4 CROSS-SURVEY COHORT MAPPING AUDIT",
    "=" * 100,
    "",
    f"CEX_ARCHIVE_SHA256={actual_sha}",
    "",
    "===== SEMANTIC STATUS =====",
    "G1_AGE_TENURE_MAPPING=PASS",
    "G2_CHILDREN_CROSS_SURVEY_MAPPING=BLOCKED",
    "",
    "===== CEX 2022 CATEGORY SANITY =====",
    "CEX_CUTENURE_DISTINCT_CODES=" + ",".join(sorted(observed_codes)),
    "CEX_CUTENURE_CODE_UNIVERSE=PASS",
    "CEX_CATEGORY_FREQUENCIES_CALCULATED=0",
    "",
    "===== CPS 2022 MAPPING =====",
    "CPS_REFERENCE_PERSON=A_EXPRRP_1_OR_2",
    "CPS_PERSON_HOUSEHOLD_JOIN=PH_SEQ_TO_H_SEQ",
    "CPS_OWNER=H_TENURE_1",
    "CPS_RENTER=H_TENURE_2",
    "CPS_OTHER=H_TENURE_0_OR_3",
    "",
    "===== SCF 2022 MAPPING =====",
    "SCF_FAMILY_ID=YY1",
    "SCF_IMPLICATE_ID=Y1",
    "SCF_REFERENCE_AGE=X14",
    "SCF_OWNER_RULE=FED_HOUSECL_LOGIC",
    "SCF_RENTER_RULE=STRICT_CATEGORICAL",
    "SCF_RENTER_DOLLAR_AMOUNT_USED=0",
    "SCF_IMPLICATE_AGREEMENT_REQUIRED=1",
    "",
    "===== DATA DISCLOSURE STATE =====",
    "PSEUDOCOHORT_COUNTS_OPENED=0",
    "SUPPORT_COUNTS_CALCULATED=0",
    "ECONOMIC_VALUES_OPENED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "",
    "E3A4_CROSS_SURVEY_MAPPING=PASS",
    "E3A5_2022_SUPPORT_COUNTS_AUTHORIZED=1",
    "",
])

OUT.write_text(summary, encoding="utf-8")

print(summary)
