from __future__ import annotations

import hashlib
import json
import re
import sys
import zipfile
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

CONTRACT = ROOT / "data/metadata/E4A2B_cps_full_weight_bridge_contract.json"

E4A2_CONTRACT = ROOT / "data/metadata/E4A2_kdi_estimator_contract.json"
E4A2_AUDIT = ROOT / "data/metadata/E4A2_kdi_estimator_preflight_audit.txt"

E4A2A_CONTRACT = ROOT / "data/metadata/E4A2A_replicate_weight_acquisition_contract.json"
E4A2A_AUDIT = ROOT / "data/metadata/E4A2A_replicate_weight_schema_audit.txt"

CPS_MAIN = ROOT / "data/raw/cps_asec/2022/asec2022_pubuse.zip"
CPS_REP = ROOT / "data/raw/cps_asec/2022/CPS_ASEC_ASCII_REPWGT_2022.ZIP"
CPS_SAS = ROOT / "data/raw/cps_asec/2022/CPS_ASEC_ASCII_REPWGT_2022.SAS"
CPS_PERSON = ROOT / "data/raw/cps_asec/2022/persfmt.txt"
CPS_HOUSE = ROOT / "data/raw/cps_asec/2022/hhldfmt.txt"
CPS_INSTRUCTIONS = ROOT / "data/raw/cps_asec/2022/2022_ASEC_Replicate_Weight_Usage_Instructions.docx"

AUDIT = ROOT / "data/metadata/E4A2B_cps_full_weight_bridge_audit.txt"
SUMMARY = ROOT / "data/metadata/E4A2B_cps_full_weight_bridge_summary.tsv"


EXPECTED_SHA = {
    E4A2_CONTRACT:
        "40c85c629285e7cf0999250914d7928b9825047682bf41362327060adaef4f0a",
    E4A2_AUDIT:
        "9998c60b281874d15be0c01578abd7a5bb39a05f27b4d2971d7244987fbba24c",
    E4A2A_CONTRACT:
        "b2c6421b1c70444d7f4ea3dbcb2a036b4a0c790d1d8ad634b0b03d0cb9b20cb6",
    E4A2A_AUDIT:
        "ebf719755fbe7d0f6c5b0023f3900d435228b2e36d97f1e9a7da3fc4fe76b546",
    CPS_MAIN:
        "61b6b6ba8ae70eb1b37acca8144163bb5c260d742b33152c639bebccc0a1fbb5",
    CPS_REP:
        "ebd1cb1c43a9e08a0edd822eab431d80952f9a832cc4a5f87ea4e1d1884698f7",
    CPS_SAS:
        "19a847aaf7a68edfc9679f7a19e447281ff3d28991f24a1439a6f83ea4bcb98f",
    CPS_PERSON:
        "a1e5c906303e6bd155b51d6232e3ed648f2120084adf44393c93b8715eacc5de",
    CPS_HOUSE:
        "aa910ad5d4c2e825fc1f414f6d3b73cde3cd97c373d827bffa449aeb992c3c94",
    CPS_INSTRUCTIONS:
        "981043658928c925507e376625d313a7d6d7b473298c0468a20a3448a4236f63",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def require_hashes() -> None:
    for path, expected in EXPECTED_SHA.items():
        if not path.is_file():
            raise RuntimeError(f"missing required file={path}")
        actual = sha256(path)
        if actual != expected:
            raise RuntimeError(
                f"SHA mismatch {path}: expected={expected} actual={actual}"
            )


def parse_int_ascii(raw: bytes, field: str) -> int:
    text = raw.decode("ascii", errors="strict").strip()
    if not text:
        raise RuntimeError(f"blank numeric field={field}")
    if not re.fullmatch(r"[+-]?\d+", text):
        raise RuntimeError(f"non-integer encoding field={field}")
    return int(text)


def parse_fixed_units(raw: bytes, decimals: int, field: str) -> int:
    """
    Return integer units of 10**(-decimals).

    Supports the official implied-decimal digit encoding and an explicit
    decimal point defensively. No floating arithmetic is used.
    """
    text = raw.decode("ascii", errors="strict").strip()

    if not text:
        raise RuntimeError(f"blank fixed-decimal field={field}")

    if re.fullmatch(r"[+-]?\d+", text):
        return int(text)

    m = re.fullmatch(r"([+-]?)(\d+)\.(\d+)", text)
    if not m:
        raise RuntimeError(f"invalid fixed-decimal encoding field={field}")

    sign = -1 if m.group(1) == "-" else 1
    whole = m.group(2)
    frac = m.group(3)

    if len(frac) > decimals:
        raise RuntimeError(
            f"too many explicit decimals field={field}: observed={len(frac)} expected<={decimals}"
        )

    frac = frac.ljust(decimals, "0")
    return sign * (int(whole) * (10 ** decimals) + int(frac))


def unique_zip_member(path: Path, expected: str) -> zipfile.ZipFile:
    zf = zipfile.ZipFile(path)
    members = [x for x in zf.namelist() if not x.endswith("/")]
    if members != [expected]:
        zf.close()
        raise RuntimeError(f"{path.name}: unexpected members={members}")
    return zf


require_hashes()

upstream = E4A2A_AUDIT.read_text(encoding="utf-8")

for token in (
    "E4A2A_REPLICATE_WEIGHT_ACQUISITION_SCHEMA_AUDIT=PASS",
    "E4A2B_WEIGHT_BRIDGE_AUDIT_AUTHORIZED=1",
    "CPS_HOUSEHOLD_FULL_WEIGHT_BRIDGE=PENDING",
    "CPS_WEIGHT_VALUE_IDENTITY_TEST_PERFORMED=0",
    "CPS_REPLICATE_MERGE_SCHEMA=PASS",
):
    if token not in upstream:
        raise RuntimeError(f"missing upstream invariant={token}")


c = json.loads(CONTRACT.read_text(encoding="utf-8"))

if c["parent_commit"] != "6b8b670":
    raise RuntimeError("unexpected E4A2B parent commit")

if c["authorized_value_reads"]["PWWGT1_through_PWWGT160"] is not False:
    raise RuntimeError("PWWGT1-160 unexpectedly authorized")

if c["authorized_value_reads"]["I_outcomes"] is not False:
    raise RuntimeError("I outcomes unexpectedly authorized")

if c["authorized_value_reads"]["K_outcomes"] is not False:
    raise RuntimeError("K outcomes unexpectedly authorized")

if c["authorized_value_reads"]["D_outcomes"] is not False:
    raise RuntimeError("D outcomes unexpectedly authorized")


# =============================================================================
# Official PWWGT0 published total — documentation only
# =============================================================================

sas_text = CPS_SAS.read_text(encoding="utf-8", errors="strict")

m = re.search(
    r"(?mi)^\s*PWWGT0\s*=\s*([0-9]+\.[0-9]+)\s*$",
    sas_text,
)

if not m:
    raise RuntimeError("official PWWGT0 total not found exactly once")

if len(re.findall(r"(?mi)^\s*PWWGT0\s*=", sas_text)) != 1:
    raise RuntimeError("official PWWGT0 total occurrence count != 1")

official_pwwgt0_units = parse_fixed_units(
    m.group(1).encode("ascii"),
    4,
    "OFFICIAL_SAS_PWWGT0_TOTAL",
)


# =============================================================================
# CPS public-use main file
#
# Only the precommitted key/reference/full-weight fields are sliced.
# =============================================================================

households: dict[int, int] = {}
reference_people: dict[int, list[tuple[int, int]]] = defaultdict(list)

main_household_records = 0
main_person_records = 0
eligible_household_records = 0
reference_person_records = 0

with unique_zip_member(
    CPS_MAIN,
    "asec2022_pubuse.dat",
) as zf:
    with zf.open("asec2022_pubuse.dat", "r") as raw:
        for bline in raw:
            line = bline.rstrip(b"\r\n")

            if not line:
                continue

            record_type = line[0:1]

            if record_type == b"1":
                main_household_records += 1

                if len(line) < 61:
                    raise RuntimeError("short CPS household record")

                h_seq = parse_int_ascii(line[28:33], "H_SEQ")
                hsup_cents = parse_fixed_units(
                    line[33:41],
                    2,
                    "HSUP_WGT",
                )
                h_hhtype = parse_int_ascii(
                    line[60:61],
                    "H_HHTYPE",
                )

                if h_hhtype == 1:
                    eligible_household_records += 1

                    if h_seq in households:
                        raise RuntimeError(
                            f"duplicate eligible household H_SEQ={h_seq}"
                        )

                    households[h_seq] = hsup_cents

            elif record_type == b"3":
                main_person_records += 1

                if len(line) < 83:
                    raise RuntimeError("short CPS person record")

                # A_EXPRRP is inspected first conceptually, but all slices below
                # are from the explicitly authorized key/full-weight fields.
                exprrp = parse_int_ascii(
                    line[81:83],
                    "A_EXPRRP",
                )

                if exprrp in {1, 2}:
                    ph_seq = parse_int_ascii(
                        line[35:40],
                        "PH_SEQ",
                    )
                    pppos = parse_int_ascii(
                        line[42:44],
                        "PPPOS",
                    )
                    marsup_cents = parse_fixed_units(
                        line[70:78],
                        2,
                        "MARSUPWT",
                    )

                    reference_person_records += 1
                    reference_people[ph_seq].append(
                        (pppos, marsup_cents)
                    )


# =============================================================================
# CPS replicate file
#
# Only PWWGT0 and the two merge keys are sliced.
# Bytes corresponding to PWWGT1-PWWGT160 are never interpreted.
# =============================================================================

replicate_full_weights: dict[tuple[int, int], int] = {}

replicate_records = 0
replicate_record_length_failures = 0
pwwgt0_sum_units = 0

with unique_zip_member(
    CPS_REP,
    "CPS_ASEC_ASCII_REPWGT_2022.DAT",
) as zf:
    with zf.open(
        "CPS_ASEC_ASCII_REPWGT_2022.DAT",
        "r",
    ) as raw:
        for bline in raw:
            line = bline.rstrip(b"\r\n")

            if not line:
                continue

            replicate_records += 1

            if len(line) != 1456:
                replicate_record_length_failures += 1
                continue

            pwwgt0_units = parse_fixed_units(
                line[0:9],
                4,
                "PWWGT0",
            )
            h_seq = parse_int_ascii(
                line[1449:1454],
                "REPLICATE_H_SEQ",
            )
            pppos = parse_int_ascii(
                line[1454:1456],
                "REPLICATE_PPPOS",
            )

            key = (h_seq, pppos)

            if key in replicate_full_weights:
                raise RuntimeError(
                    f"duplicate replicate key H_SEQ,PPPOS={key}"
                )

            replicate_full_weights[key] = pwwgt0_units
            pwwgt0_sum_units += pwwgt0_units


# =============================================================================
# Precommitted bridge tests
# =============================================================================

households_with_exactly_one_reference = 0
households_with_bad_reference_count = 0

reference_pppos_41_mismatches = 0
missing_replicate_matches = 0

hsup_marsup_mismatches = 0
pwwgt0_marsup_precision_mismatches = 0
pwwgt0_marsup_max_abs_diff_units = 0

for h_seq, hsup_cents in households.items():
    refs = reference_people.get(h_seq, [])

    if len(refs) != 1:
        households_with_bad_reference_count += 1
        continue

    households_with_exactly_one_reference += 1

    pppos, marsup_cents = refs[0]

    if pppos != 41:
        reference_pppos_41_mismatches += 1

    if hsup_cents != marsup_cents:
        hsup_marsup_mismatches += 1

    rep_key = (h_seq, pppos)
    pwwgt0_units = replicate_full_weights.get(rep_key)

    if pwwgt0_units is None:
        missing_replicate_matches += 1
        continue

    # MARSUPWT uses 2 implied decimals; PWWGT0 uses 4.
    # Convert the former to 1e-4 units before comparing.
    marsup_units_1e4 = marsup_cents * 100
    abs_diff_units = abs(
        pwwgt0_units - marsup_units_1e4
    )

    pwwgt0_marsup_max_abs_diff_units = max(
        pwwgt0_marsup_max_abs_diff_units,
        abs_diff_units,
    )

    # 0.0050 == 50 units at 1e-4 precision.
    if abs_diff_units > 50:
        pwwgt0_marsup_precision_mismatches += 1


reference_structure_pass = (
    len(households) > 0
    and households_with_bad_reference_count == 0
    and households_with_exactly_one_reference == len(households)
)

pppos_pass = (
    reference_structure_pass
    and reference_pppos_41_mismatches == 0
)

replicate_length_pass = (
    replicate_records > 0
    and replicate_record_length_failures == 0
)

replicate_match_pass = (
    reference_structure_pass
    and missing_replicate_matches == 0
)

house_person_weight_pass = (
    reference_structure_pass
    and hsup_marsup_mismatches == 0
)

rep_person_weight_pass = (
    replicate_match_pass
    and pwwgt0_marsup_precision_mismatches == 0
)

pwwgt0_sum_pass = (
    pwwgt0_sum_units == official_pwwgt0_units
)

bridge_pass = all([
    reference_structure_pass,
    pppos_pass,
    replicate_length_pass,
    replicate_match_pass,
    house_person_weight_pass,
    rep_person_weight_pass,
    pwwgt0_sum_pass,
])


# =============================================================================
# Forensic summary — counts/differences only; no row-level weights emitted
# =============================================================================

summary_rows = [
    ("MAIN_HOUSEHOLD_RECORDS", str(main_household_records), "INFO"),
    ("MAIN_PERSON_RECORDS", str(main_person_records), "INFO"),
    ("ELIGIBLE_H_HHTYPE_1_HOUSEHOLDS", str(len(households)), "INFO"),
    ("REFERENCE_PERSON_RECORDS_ALL_HOUSEHOLDS", str(reference_person_records), "INFO"),
    (
        "ELIGIBLE_HOUSEHOLDS_EXACTLY_ONE_REFERENCE",
        str(households_with_exactly_one_reference),
        "PASS" if reference_structure_pass else "FAIL",
    ),
    (
        "ELIGIBLE_HOUSEHOLDS_BAD_REFERENCE_COUNT",
        str(households_with_bad_reference_count),
        "PASS" if reference_structure_pass else "FAIL",
    ),
    (
        "REFERENCE_PPPOS_41_MISMATCHES",
        str(reference_pppos_41_mismatches),
        "PASS" if pppos_pass else "FAIL",
    ),
    ("REPLICATE_RECORDS", str(replicate_records), "INFO"),
    (
        "REPLICATE_RECORD_LENGTH_FAILURES",
        str(replicate_record_length_failures),
        "PASS" if replicate_length_pass else "FAIL",
    ),
    (
        "MISSING_REFERENCE_REPLICATE_MATCHES",
        str(missing_replicate_matches),
        "PASS" if replicate_match_pass else "FAIL",
    ),
    (
        "HSUP_WGT_MARSUPWT_MISMATCHES",
        str(hsup_marsup_mismatches),
        "PASS" if house_person_weight_pass else "FAIL",
    ),
    (
        "PWWGT0_MARSUPWT_PRECISION_MISMATCHES",
        str(pwwgt0_marsup_precision_mismatches),
        "PASS" if rep_person_weight_pass else "FAIL",
    ),
    (
        "PWWGT0_MARSUPWT_MAX_ABS_DIFF_1E4_UNITS",
        str(pwwgt0_marsup_max_abs_diff_units),
        "PASS" if rep_person_weight_pass else "FAIL",
    ),
    (
        "PWWGT0_OFFICIAL_SUM",
        "MATCH" if pwwgt0_sum_pass else "MISMATCH",
        "PASS" if pwwgt0_sum_pass else "FAIL",
    ),
]

SUMMARY.write_text(
    "item\tobserved\tgate\n"
    + "\n".join(
        "\t".join(row)
        for row in summary_rows
    )
    + "\n",
    encoding="utf-8",
)


lines = [
    "=" * 100,
    "E4A2B — CPS FULL-WEIGHT BRIDGE AUDIT",
    "=" * 100,
    "",
    "CPS_MAIN_WEIGHT_VALUES_PARSED=1",
    "CPS_PWWGT0_VALUES_PARSED=1",
    "CPS_PWWGT1_160_VALUES_PARSED=0",
    "CPS_I_VALUES_READ=0",
    "SCF_K_D_VALUES_READ=0",
    "DIMENSIONALITY_OUTCOMES_OPENED=0",
    "",
    "===== OFFICIAL MERGE POPULATION =====",
    f"CPS_MAIN_HOUSEHOLD_RECORDS={main_household_records}",
    f"CPS_MAIN_PERSON_RECORDS={main_person_records}",
    f"CPS_H_HHTYPE_1_HOUSEHOLDS={len(households)}",
    f"CPS_REFERENCE_PERSON_RECORDS={reference_person_records}",
    (
        "CPS_ELIGIBLE_HOUSEHOLD_EXACTLY_ONE_REFERENCE=PASS"
        if reference_structure_pass
        else
        "CPS_ELIGIBLE_HOUSEHOLD_EXACTLY_ONE_REFERENCE=FAIL"
    ),
    (
        "CPS_REFERENCE_PERSON_PPPOS_41=PASS"
        if pppos_pass
        else
        "CPS_REFERENCE_PERSON_PPPOS_41=FAIL"
    ),
    "",
    "===== REPLICATE PARSER / MERGE =====",
    f"CPS_REPLICATE_RECORDS={replicate_records}",
    (
        "CPS_REPLICATE_LRECL_1456_VALUESIDE=PASS"
        if replicate_length_pass
        else
        "CPS_REPLICATE_LRECL_1456_VALUESIDE=FAIL"
    ),
    (
        "CPS_REFERENCE_PERSON_REPLICATE_MATCH=PASS"
        if replicate_match_pass
        else
        "CPS_REFERENCE_PERSON_REPLICATE_MATCH=FAIL"
    ),
    (
        "CPS_PWWGT0_OFFICIAL_SUM_CHECK=PASS"
        if pwwgt0_sum_pass
        else
        "CPS_PWWGT0_OFFICIAL_SUM_CHECK=FAIL"
    ),
    "",
    "===== FULL-WEIGHT IDENTITY =====",
    (
        "CPS_HSUP_WGT_MARSUPWT_EXACT_IDENTITY=PASS"
        if house_person_weight_pass
        else
        "CPS_HSUP_WGT_MARSUPWT_EXACT_IDENTITY=FAIL"
    ),
    "CPS_PWWGT0_MARSUPWT_TOLERANCE=0.0050",
    (
        "CPS_PWWGT0_MARSUPWT_PRECISION_BRIDGE=PASS"
        if rep_person_weight_pass
        else
        "CPS_PWWGT0_MARSUPWT_PRECISION_BRIDGE=FAIL"
    ),
    (
        "CPS_HOUSEHOLD_FULL_WEIGHT_BRIDGE=PASS"
        if bridge_pass
        else
        "CPS_HOUSEHOLD_FULL_WEIGHT_BRIDGE=FAIL"
    ),
    "CPS_WEIGHT_VALUE_IDENTITY_TEST_PERFORMED=1",
    "",
    "K_VALUES_OPEN_AUTHORIZED=0",
    "D_VALUES_OPEN_AUTHORIZED=0",
    "I_VALUES_OPEN_AUTHORIZED=0",
    "K_D_I_INFERENCE_AUTHORIZED=0",
    "",
    "K_EMPIRICALLY_TESTED=0",
    "D_EMPIRICALLY_TESTED=0",
    "I_EMPIRICALLY_TESTED=0",
    "FIVE_DIMENSIONALITY_PROVEN=0",
    "",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "",
    (
        "E4A2B_WEIGHT_BRIDGE_AUDIT=PASS"
        if bridge_pass
        else
        "E4A2B_WEIGHT_BRIDGE_AUDIT=FAIL"
    ),
    (
        "E4A2C_CPS_REPLICATE_ENGINE_PREFLIGHT_AUTHORIZED=1"
        if bridge_pass
        else
        "E4A2C_CPS_REPLICATE_ENGINE_PREFLIGHT_AUTHORIZED=0"
    ),
]

text = "\n".join(lines) + "\n"

AUDIT.write_text(
    text,
    encoding="utf-8",
)

sys.stdout.write(text)

if not bridge_pass:
    raise SystemExit(1)
