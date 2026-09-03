from __future__ import annotations

import csv
import hashlib
import io
import math
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

CEX = ROOT / "data/raw/cex/2022/intrvw22.zip"
CPS = ROOT / "data/raw/cps_asec/2022/asec2022_pubuse.zip"
SCF_FULL = ROOT / "data/raw/scf/2022/scf2022s.zip"
SCF_SUM = ROOT / "data/raw/scf/2022/scfp2022s.zip"

THRESHOLD_FILE = ROOT / "data/metadata/E3A3_support_thresholds.tsv"
MAPPING_FILE = ROOT / "data/metadata/E3A4_mapping.tsv"

OUT = ROOT / "results/tables/E3A5B_2022_support_counts.tsv"
SUMMARY = ROOT / "results/tables/E3A5B_2022_support_summary.txt"
EXEC_META = ROOT / "data/metadata/E3A5B_count_metadata.txt"


EXPECTED_HASHES = {
    CEX:
        "c99a2f47c0084b7a88812b34c56a1a288be2798ff010b2b59dcf87e072773e17",
    CPS:
        "61b6b6ba8ae70eb1b37acca8144163bb5c260d742b33152c639bebccc0a1fbb5",
    SCF_FULL:
        "409e6811df895766d50b2f597c10b1b3c5813e7d3e0e45d910ad26c0cb07f4eb",
    SCF_SUM:
        "3bb4d890ae2463ff6039ec7692e375f544dd98a55a37ca2cb2340354b9cc9d80",
    THRESHOLD_FILE:
        "f0abc60abf21a38c1f1268f1f299f3ceeee18b558b796daa0cbeb943e635ffa4",
    MAPPING_FILE:
        "12783a626edf3af3b8dccadfbe3d084c1b2af493a1e51966a963b20226f1c97e",
}


BASE_BANDS = (
    "25-34",
    "35-44",
    "45-54",
    "55-64",
)

TENURES = (
    "OWNER",
    "RENTER",
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()

    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)

    return h.hexdigest()


for path, expected in EXPECTED_HASHES.items():
    if not path.exists():
        raise RuntimeError(f"missing frozen input: {path}")

    actual = sha256(path)

    if actual != expected:
        raise RuntimeError(
            f"hash mismatch: {path}\n"
            f"expected={expected}\n"
            f"actual={actual}"
        )


# =============================================================================
# Frozen thresholds
# =============================================================================

thresholds = {}

with THRESHOLD_FILE.open(encoding="utf-8") as f:
    for row in csv.DictReader(f, delimiter="\t"):
        thresholds[row["survey"]] = (
            int(row["min_unique_units"]),
            float(row["min_kish_ess"]),
        )

expected_thresholds = {
    "CEX": (200, 100.0),
    "CPS_ASEC": (500, 250.0),
    "SCF": (100, 50.0),
}

if thresholds != expected_thresholds:
    raise RuntimeError(
        f"threshold mutation detected: {thresholds}"
    )


# =============================================================================
# Helpers
# =============================================================================

def to_int(value) -> int | None:
    if value is None:
        return None

    s = str(value).strip()

    if not s:
        return None

    try:
        return int(s)
    except ValueError:
        try:
            return int(float(s))
        except Exception:
            return None


def to_float(value) -> float | None:
    try:
        x = float(str(value).strip())
    except Exception:
        return None

    if not math.isfinite(x):
        return None

    return x


def age_band(age) -> str | None:
    age = to_int(age)

    if age is None:
        return None

    if 25 <= age <= 34:
        return "25-34"

    if 35 <= age <= 44:
        return "35-44"

    if 45 <= age <= 54:
        return "45-54"

    if 55 <= age <= 64:
        return "55-64"

    return None


def kish(weights: list[float]) -> float:
    if not weights:
        return 0.0

    s1 = sum(weights)
    s2 = sum(x * x for x in weights)

    if s2 <= 0:
        return 0.0

    return (s1 * s1) / s2


def cex_tenure(code) -> str | None:
    code = to_int(code)

    if code in {1, 2, 3}:
        return "OWNER"

    if code == 4:
        return "RENTER"

    return None


def cps_tenure(code) -> str | None:
    code = to_int(code)

    if code == 1:
        return "OWNER"

    if code == 2:
        return "RENTER"

    return None


def scf_tenure(row) -> str | None:
    x508 = to_int(row.x508)
    x601 = to_int(row.x601)
    x701 = to_int(row.x701)
    x7133 = to_int(row.x7133)

    owner = (
        x508 in {1, 2}
        or x601 in {1, 2, 3}
        or x701 in {1, 3, 4, 5, 6, 8}
        or (x701 == -7 and x7133 == 1)
    )

    if owner:
        return "OWNER"

    renter = (
        x508 == 3
        or x601 == 4
        or x701 == 2
    )

    if renter:
        return "RENTER"

    return None


cells: dict[str, dict[tuple[str, str], list[float]]] = {
    "CEX": defaultdict(list),
    "CPS_ASEC": defaultdict(list),
    "SCF": defaultdict(list),
}

# SCF X42001 is implicate-specific.
# Keep the five weight systems separate for support ESS.
scf_cells_by_implicate = {
    implicate: defaultdict(list)
    for implicate in range(1, 6)
}


# =============================================================================
# CEX
# =============================================================================

cex_units: dict[str, dict[str, list]] = {}

with zipfile.ZipFile(CEX) as zf:

    members = sorted(
        n for n in zf.namelist()
        if Path(n).name.lower().startswith("fmli")
        and Path(n).suffix.lower() == ".csv"
    )

    if len(members) != 4:
        raise RuntimeError(
            f"CEX expected four FMLI members; found={len(members)}"
        )

    for member in members:

        with zf.open(member, "r") as raw:

            txt = io.TextIOWrapper(
                raw,
                encoding="utf-8-sig",
                errors="strict",
                newline="",
            )

            reader = csv.DictReader(txt)

            fields = {
                x.upper(): x
                for x in (reader.fieldnames or [])
            }

            required = {
                "NEWID",
                "AGE_REF",
                "CUTENURE",
                "FINLWT21",
            }

            missing = required - set(fields)

            if missing:
                raise RuntimeError(
                    f"{member}: missing={sorted(missing)}"
                )

            for row in reader:

                newid = row[fields["NEWID"]].strip()

                if len(newid) != 8 or not newid.isdigit():
                    raise RuntimeError(
                        f"invalid NEWID={newid!r}"
                    )

                cu = newid[:-1]

                membership = (
                    age_band(row[fields["AGE_REF"]]),
                    cex_tenure(row[fields["CUTENURE"]]),
                )

                weight = to_float(
                    row[fields["FINLWT21"]]
                )

                rec = cex_units.setdefault(
                    cu,
                    {
                        "memberships": [],
                        "weights": [],
                    },
                )

                rec["memberships"].append(membership)

                if weight is not None and weight > 0:
                    rec["weights"].append(weight)


for rec in cex_units.values():

    memberships = set(rec["memberships"])

    if len(memberships) != 1:
        continue

    band, tenure = next(iter(memberships))

    if band not in BASE_BANDS:
        continue

    if tenure not in TENURES:
        continue

    if not rec["weights"]:
        continue

    weight = sum(rec["weights"]) / len(rec["weights"])

    cells["CEX"][(band, tenure)].append(weight)


# =============================================================================
# CPS ASEC
#
# Census positions are one-based:
#
# HRECORD   1 len1
# H_SEQ    29 len5
# HSUP_WGT 34 len8
# H_HHTYPE 61 len1
# H_TENURE 89 len1
#
# PRECORD   1 len1
# PH_SEQ   36 len5
# A_AGE    79 len2
# A_EXPRRP 82 len2
# =============================================================================

cps_house = {}
cps_refs = defaultdict(list)

with zipfile.ZipFile(CPS) as zf:

    members = [
        n for n in zf.namelist()
        if not n.endswith("/")
    ]

    if members != ["asec2022_pubuse.dat"]:
        raise RuntimeError(
            f"unexpected CPS member structure={members}"
        )

    with zf.open(members[0], "r") as raw:

        for bline in raw:

            line = bline.decode(
                "ascii",
                errors="strict",
            ).rstrip("\r\n")

            if not line:
                continue

            record_type = line[0:1]

            if record_type == "1":

                if len(line) < 89:
                    raise RuntimeError(
                        "short CPS household record"
                    )

                h_seq = to_int(line[28:33])
                weight = to_float(line[33:41])
                hh_type = to_int(line[60:61])
                tenure = to_int(line[88:89])

                if h_seq is None:
                    continue

                if h_seq in cps_house:
                    raise RuntimeError(
                        f"duplicate CPS H_SEQ={h_seq}"
                    )

                if (
                    hh_type == 1
                    and weight is not None
                    and weight > 0
                ):
                    cps_house[h_seq] = (
                        weight,
                        tenure,
                    )

            elif record_type == "3":

                if len(line) < 83:
                    raise RuntimeError(
                        "short CPS person record"
                    )

                ph_seq = to_int(line[35:40])
                age = to_int(line[78:80])
                exprrp = to_int(line[81:83])

                if (
                    ph_seq is not None
                    and age is not None
                    and exprrp in {1, 2}
                ):
                    cps_refs[ph_seq].append(age)


for h_seq, (weight, tenure_code) in cps_house.items():

    ref_ages = cps_refs.get(h_seq, [])

    if len(ref_ages) != 1:
        continue

    band = age_band(ref_ages[0])
    tenure = cps_tenure(tenure_code)

    if band not in BASE_BANDS:
        continue

    if tenure not in TENURES:
        continue

    cells["CPS_ASEC"][(band, tenure)].append(weight)


# =============================================================================
# SCF
# =============================================================================

def extract_single_dta(
    archive: Path,
    destination: Path,
) -> Path:

    with zipfile.ZipFile(archive) as zf:

        members = [
            n for n in zf.namelist()
            if Path(n).suffix.lower() == ".dta"
        ]

        if len(members) != 1:
            raise RuntimeError(
                f"{archive.name}: expected one DTA, got={members}"
            )

        member = members[0]

        zf.extract(member, destination)

        return destination / member


def stata_name_map(path: Path) -> dict[str, str]:

    with path.open("rb") as fh:

        reader = pd.io.stata.StataReader(
            fh,
            convert_categoricals=False,
        )

        names = list(
            reader.variable_labels().keys()
        )

    return {
        x.lower(): x
        for x in names
    }


with tempfile.TemporaryDirectory() as tempdir:

    temp = Path(tempdir)

    full_path = extract_single_dta(
        SCF_FULL,
        temp / "full",
    )

    sum_path = extract_single_dta(
        SCF_SUM,
        temp / "summary",
    )

    full_map = stata_name_map(full_path)
    sum_map = stata_name_map(sum_path)

    full_required = [
        "y1",
        "x14",
        "x508",
        "x601",
        "x701",
        "x7133",
        "x42001",
    ]

    summary_required = [
        "y1",
        "yy1",
    ]

    for name in full_required:

        if name not in full_map:
            raise RuntimeError(
                f"SCF full variable missing={name}"
            )

    for name in summary_required:

        if name not in sum_map:
            raise RuntimeError(
                f"SCF summary variable missing={name}"
            )

    full = pd.read_stata(
        full_path,
        columns=[
            full_map[x]
            for x in full_required
        ],
        convert_categoricals=False,
    )

    summary = pd.read_stata(
        sum_path,
        columns=[
            sum_map[x]
            for x in summary_required
        ],
        convert_categoricals=False,
    )

    full.columns = [
        x.lower()
        for x in full.columns
    ]

    summary.columns = [
        x.lower()
        for x in summary.columns
    ]


if full["y1"].duplicated().any():
    raise RuntimeError("SCF full Y1 is not unique")

if summary["y1"].duplicated().any():
    raise RuntimeError("SCF summary Y1 is not unique")


scf = full.merge(
    summary,
    on="y1",
    how="inner",
    validate="one_to_one",
)

if len(scf) != len(full):
    raise RuntimeError(
        "SCF Y1->YY1 mapping did not cover all full records"
    )


for yy1, grp in scf.groupby(
    "yy1",
    sort=False,
):

    if len(grp) != 5:
        continue

    family_id = to_int(yy1)

    if family_id is None:
        raise RuntimeError(
            f"invalid SCF YY1={yy1!r}"
        )

    implicate_rows = {}
    memberships = set()

    for row in grp.itertuples(index=False):

        y1 = to_int(row.y1)

        if y1 is None:
            raise RuntimeError(
                f"invalid SCF Y1 for YY1={yy1}"
            )

        # Official 2022 SCF codebook identity:
        # IMPLIC = Y1 - 10*YY1
        implicate = y1 - 10 * family_id

        if implicate not in {1, 2, 3, 4, 5}:
            raise RuntimeError(
                f"invalid SCF implicate identity "
                f"YY1={yy1} Y1={y1} IMPLIC={implicate}"
            )

        if implicate in implicate_rows:
            raise RuntimeError(
                f"duplicate SCF implicate "
                f"YY1={yy1} IMPLIC={implicate}"
            )

        membership = (
            age_band(row.x14),
            scf_tenure(row),
        )

        weight = to_float(row.x42001)

        implicate_rows[implicate] = (
            membership,
            weight,
        )

        memberships.add(membership)

    if set(implicate_rows) != {1, 2, 3, 4, 5}:
        raise RuntimeError(
            f"incomplete SCF implicates YY1={yy1} "
            f"found={sorted(implicate_rows)}"
        )

    # Cohort membership must remain identical across all
    # five multiple-imputation implicates.
    if len(memberships) != 1:
        continue

    band, tenure = next(iter(memberships))

    if band not in BASE_BANDS:
        continue

    if tenure not in TENURES:
        continue

    # Require valid positive analysis weight in every implicate.
    if any(
        weight is None
        or not math.isfinite(weight)
        or weight <= 0
        for _, weight in implicate_rows.values()
    ):
        continue

    # Preserve the five legitimate X42001 weight systems.
    for implicate in range(1, 6):

        _, weight = implicate_rows[implicate]

        scf_cells_by_implicate[
            implicate
        ][
            (band, tenure)
        ].append(weight)


# =============================================================================
# Output cells
# =============================================================================

def cohort_bands(
    age_group: str,
) -> list[str]:

    if age_group in BASE_BANDS:
        return [age_group]

    if age_group == "25-44":
        return [
            "25-34",
            "35-44",
        ]

    if age_group == "45-64":
        return [
            "45-54",
            "55-64",
        ]

    raise ValueError(age_group)


def cohort_weights(
    survey: str,
    age_group: str,
    tenure: str,
) -> list[float]:

    if survey == "SCF":
        raise RuntimeError(
            "SCF weights must remain implicate-specific"
        )

    out = []

    for band in cohort_bands(age_group):

        out.extend(
            cells[survey].get(
                (band, tenure),
                [],
            )
        )

    return out


def scf_cohort_weights(
    implicate: int,
    age_group: str,
    tenure: str,
) -> list[float]:

    out = []

    for band in cohort_bands(age_group):

        out.extend(
            scf_cells_by_implicate[
                implicate
            ].get(
                (band, tenure),
                [],
            )
        )

    return out


REPORT_CELLS = [
    ("25-34", "OWNER", "BASE"),
    ("25-34", "RENTER", "BASE"),
    ("35-44", "OWNER", "BASE"),
    ("35-44", "RENTER", "BASE"),
    ("45-54", "OWNER", "BASE"),
    ("45-54", "RENTER", "BASE"),
    ("55-64", "OWNER", "BASE"),
    ("55-64", "RENTER", "BASE"),
    ("25-44", "OWNER", "FALLBACK"),
    ("25-44", "RENTER", "FALLBACK"),
    ("45-64", "OWNER", "FALLBACK"),
]


rows = []

for age_group, tenure, tier in REPORT_CELLS:

    for survey in (
        "CEX",
        "CPS_ASEC",
        "SCF",
    ):

        if survey == "SCF":

            implicate_weights = {
                implicate: scf_cohort_weights(
                    implicate,
                    age_group,
                    tenure,
                )
                for implicate in range(1, 6)
            }

            n_by_implicate = {
                implicate: len(weights)
                for implicate, weights
                in implicate_weights.items()
            }

            if len(set(n_by_implicate.values())) != 1:
                raise RuntimeError(
                    f"SCF family-count mismatch across implicates: "
                    f"{age_group} {tenure} "
                    f"{n_by_implicate}"
                )

            n_unique = next(
                iter(n_by_implicate.values())
            )

            ess_by_implicate = {
                implicate: kish(weights)
                for implicate, weights
                in implicate_weights.items()
            }

            # Conservative pre-disclosure support rule.
            ess = min(
                ess_by_implicate.values()
            )

        else:

            weights = cohort_weights(
                survey,
                age_group,
                tenure,
            )

            n_unique = len(weights)
            ess = kish(weights)

        min_n, min_ess = thresholds[survey]

        passed = (
            n_unique >= min_n
            and ess >= min_ess
        )

        rows.append({
            "survey": survey,
            "age_group": age_group,
            "tenure": tenure,
            "tier": tier,
            "n_unique": n_unique,
            "kish_ess": f"{ess:.6f}",
            "min_unique": min_n,
            "min_kish_ess": f"{min_ess:.6f}",
            "support_pass": int(passed),
        })


OUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

with OUT.open(
    "w",
    newline="",
    encoding="utf-8",
) as f:

    fields = [
        "survey",
        "age_group",
        "tenure",
        "tier",
        "n_unique",
        "kish_ess",
        "min_unique",
        "min_kish_ess",
        "support_pass",
    ]

    writer = csv.DictWriter(
        f,
        fieldnames=fields,
        delimiter="\t",
    )

    writer.writeheader()
    writer.writerows(rows)


def cross_pass(
    age_group: str,
    tenure: str,
) -> bool:

    matched = [
        r
        for r in rows
        if r["age_group"] == age_group
        and r["tenure"] == tenure
    ]

    return (
        len(matched) == 3
        and all(
            r["support_pass"] == 1
            for r in matched
        )
    )


young_owner = cross_pass(
    "25-34",
    "OWNER",
)

young_renter = cross_pass(
    "25-34",
    "RENTER",
)

fallback_owner = cross_pass(
    "25-44",
    "OWNER",
)

fallback_renter = cross_pass(
    "25-44",
    "RENTER",
)


if young_owner and young_renter:

    young_selection = "25-34"

elif fallback_owner and fallback_renter:

    young_selection = "25-44_FALLBACK"

else:

    young_selection = "REJECTED"


if cross_pass("55-64", "OWNER"):

    established_selection = "55-64"

elif cross_pass("45-64", "OWNER"):

    established_selection = "45-64_FALLBACK"

else:

    established_selection = "REJECTED"


summary_lines = [
    "=" * 100,
    "ECONOMIC GEOMETRY RESEARCH — E3A5B 2022 SUPPORT COUNT OPENING",
    "=" * 100,
    "",
    "ECONOMIC_VALUES_OPENED=0",
    "INCOME_VALUES_OPENED=0",
    "EXPENDITURE_VALUES_OPENED=0",
    "WEALTH_VALUES_OPENED=0",
    "DEBT_VALUES_OPENED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "",
    "===== BASE CROSS-SURVEY GATES =====",
]

for age_group in BASE_BANDS:

    for tenure in TENURES:

        summary_lines.append(
            f"{age_group}_{tenure}_CROSS_SURVEY_PASS="
            f"{int(cross_pass(age_group, tenure))}"
        )


summary_lines += [
    "",
    "===== FROZEN FALLBACK GATES =====",
    (
        "25-44_OWNER_CROSS_SURVEY_PASS="
        + str(int(cross_pass("25-44", "OWNER")))
    ),
    (
        "25-44_RENTER_CROSS_SURVEY_PASS="
        + str(int(cross_pass("25-44", "RENTER")))
    ),
    (
        "45-64_OWNER_CROSS_SURVEY_PASS="
        + str(int(cross_pass("45-64", "OWNER")))
    ),
    "",
    "===== PRECOMMITTED SELECTION =====",
    f"YOUNG_CANONICAL={young_selection}",
    f"ESTABLISHED_OWNER_CANONICAL={established_selection}",
    "",
]

if young_selection == "REJECTED":

    summary_lines += [
        "PRIMARY_YOUNG_COMPARISON_AUTHORIZED=0",
        "E3B_COMPONENT_DESIGN_AUTHORIZED=0",
    ]

else:

    summary_lines += [
        "PRIMARY_YOUNG_COMPARISON_AUTHORIZED=1",
        "E3B_COMPONENT_DESIGN_AUTHORIZED=1",
    ]


summary_lines += [
    "",
    "SUPPORT_COUNTS_ARE_DESIGN_RESULTS_ONLY=1",
    "NO_CAUSAL_INTERPRETATION_AUTHORIZED=1",
    "NO_REAL_INFLATION_VALUE_AUTHORIZED=1",
    "",
]


SUMMARY.write_text(
    "\n".join(summary_lines),
    encoding="utf-8",
)


EXEC_META.write_text(
    "\n".join([
        f"CEX_SHA256={sha256(CEX)}",
        f"CPS_SHA256={sha256(CPS)}",
        f"SCF_FULL_SHA256={sha256(SCF_FULL)}",
        f"SCF_SUMMARY_SHA256={sha256(SCF_SUM)}",
        f"THRESHOLD_SHA256={sha256(THRESHOLD_FILE)}",
        f"MAPPING_SHA256={sha256(MAPPING_FILE)}",
        "SCF_IMPLICATE_ID_RULE=Y1_MINUS_10_TIMES_YY1",
        "SCF_KISH_ESS_RULE=MIN_OF_FIVE_IMPLICATES",
        "ECONOMIC_FIELDS_PARSED=0",
    ]) + "\n",
    encoding="utf-8",
)


print(SUMMARY.read_text(encoding="utf-8"))

print(f"OUTPUT_TABLE={OUT}")
print(f"OUTPUT_SUMMARY={SUMMARY}")
print(f"OUTPUT_METADATA={EXEC_META}")
