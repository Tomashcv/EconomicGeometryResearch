from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np

from E4A2C_cps_replicate_engine import (
    REPLICATE_COUNT,
    owner_renter_difference_with_replicates,
    weighted_share_with_replicates,
)


ROOT = Path(__file__).resolve().parents[1]

CONTRACT = (
    ROOT
    / "data/metadata/E4A2D_first_cps_i_inference_contract.json"
)

I_REPAIR = (
    ROOT
    / "data/metadata/E4A_R1_i_semantic_repair.json"
)

I_SEMANTICS = (
    ROOT
    / "data/metadata/E4A_R1_i_official_semantic_contract.tsv"
)

MAPPING = (
    ROOT
    / "data/metadata/E3A4_mapping.tsv"
)

E4A2_CONTRACT = (
    ROOT
    / "data/metadata/E4A2_kdi_estimator_contract.json"
)

E4A2B_AUDIT = (
    ROOT
    / "data/metadata/E4D1D_2019_runtime/CPS_ASEC/E4A2B_cps_full_weight_bridge_audit.txt"
)

E4A2B_SUMMARY = (
    ROOT
    / "data/metadata/E4A2B_cps_full_weight_bridge_summary.tsv"
)

E4A2C_CONTRACT = (
    ROOT
    / "data/metadata/E4A2C_cps_replicate_engine_contract.json"
)

E4A2C_ENGINE = (
    ROOT
    / "scripts/E4A2C_cps_replicate_engine.py"
)

E4A2C_AUDIT = (
    ROOT
    / "data/metadata/E4D1D_2019_runtime/CPS_ASEC/E4A2C_cps_replicate_engine_contract_audit.txt"
)

E4A2C_CHECKS = (
    ROOT
    / "data/metadata/E4A2C_synthetic_engine_checks.tsv"
)

CPS_MAIN = (
    ROOT
    / "data/raw/cps_asec/2019/asec2019_pubuse.zip"
)

CPS_REP = (
    ROOT
    / "data/raw/cps_asec/2019/CPS_ASEC_ASCII_REPWGT_2019.ZIP"
)

CPS_SAS = (
    ROOT
    / "data/raw/cps_asec/2019/CPS_ASEC_ASCII_REPWGT_2019.SAS"
)

PERSON_LAYOUT = (
    ROOT
    / "data/raw/cps_asec/2019/persfmt.txt"
)

HOUSE_LAYOUT = (
    ROOT
    / "data/raw/cps_asec/2019/hhldfmt.txt"
)

OUT_COHORT = (
    ROOT
    / "data/results/E4D1D_2019_runtime/CPS_ASEC/E4A2D_2022_cps_i_cohort_inference.tsv"
)

OUT_DIFF = (
    ROOT
    / "data/results/E4D1D_2019_runtime/CPS_ASEC/E4A2D_2022_cps_i_owner_renter_differences.tsv"
)

OUT_REPS = (
    ROOT
    / "data/results/E4D1D_2019_runtime/CPS_ASEC/E4A2D_2022_cps_i_replicate_estimates.tsv"
)

OUT_SUPPORT = (
    ROOT
    / "data/results/E4D1D_2019_runtime/CPS_ASEC/E4A2D_2022_cps_i_cohort_support.tsv"
)

AUDIT = (
    ROOT
    / "data/metadata/E4D1D_2019_runtime/CPS_ASEC/E4A2D_first_cps_i_inference_execution_audit.txt"
)


EXPECTED_SHA = {
    I_REPAIR:
        "26cd1ccdc183cbb02df6fb63f598c01df5c3a1ed7d34a918bf4e4f6fb5b00e03",

    I_SEMANTICS:
        "ebcf4594ecfff2353f0a0b71725c3b112dddb00cbef4b80e66d5129c27e49d78",

    MAPPING:
        "12783a626edf3af3b8dccadfbe3d084c1b2af493a1e51966a963b20226f1c97e",

    E4A2_CONTRACT:
        "40c85c629285e7cf0999250914d7928b9825047682bf41362327060adaef4f0a",

    E4A2B_AUDIT:
        "1434529f38aa100f3cb85ae2e13385a135415bcc0dd2a489ffe476916b1a76b2",

    E4A2B_SUMMARY:
        "475ba266f163b2e08fff3256567bd563c3cc17c4826240a8429275cdb2fc62bb",

    E4A2C_CONTRACT:
        "369899c360c2a67be3eb748f8c63c9a676764555d4232acdfbcd1f60e3ba5ad3",

    E4A2C_ENGINE:
        "247ffa926686f46b5237a98be907b2548a22e83fe8d7294627ee41efcdad93f9",

    E4A2C_AUDIT:
        "a4fff0ecc7663338a0e3b68c1531a1f7f9015aa3c73c8a90006f90580cf08294",

    E4A2C_CHECKS:
        "00306bbe02fe5363e3cd23adf9f868ab117875db1f60013c07b2900e4be6644c",

    CPS_MAIN:
        "e914463e75a0f6ab10f044e1835dff47dddfd57ed3995b26a9ab6cbd05ddd327",

    CPS_REP:
        "6281a4dee146bf72d5547a12b952ac51a07c83794c9ebe00433631030dab14de",

    CPS_SAS:
        "97e60a9fb698c72a343e0e9c346c3439987560461bbfcde42704cc3937b4c2e7",

    PERSON_LAYOUT:
        "be9b7912f64ac574b78b8d455660c2bece8605c080c5771e496446de869eb1da",

    HOUSE_LAYOUT:
        "eb3102622f5b9445e5ded16919dbb6de7b20eede0156fbbb4693bbb5124eaa31",
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


def check_hashes() -> None:
    for path, expected in EXPECTED_SHA.items():

        if not path.is_file():
            raise RuntimeError(
                f"missing required file={path}"
            )

        actual = sha256(path)

        if actual != expected:
            raise RuntimeError(
                f"SHA mismatch {path}: "
                f"expected={expected} actual={actual}"
            )


def parse_int_ascii(
    raw: bytes,
    field: str,
) -> int:

    text = raw.decode(
        "ascii",
        errors="strict",
    ).strip()

    if not text:
        raise RuntimeError(
            f"blank numeric field={field}"
        )

    if not re.fullmatch(
        r"[+-]?\d+",
        text,
    ):
        raise RuntimeError(
            f"invalid integer field={field}"
        )

    return int(text)


def parse_fixed_units(
    raw: bytes,
    decimals: int,
    field: str,
) -> int:
    """
    Return exact integer units of 10**(-decimals).

    Handles both implied-decimal integer encoding and explicit decimal
    encoding. No binary floating arithmetic is used at parse time.
    """

    text = raw.decode(
        "ascii",
        errors="strict",
    ).strip()

    if not text:
        raise RuntimeError(
            f"blank fixed-decimal field={field}"
        )

    if re.fullmatch(
        r"[+-]?\d+",
        text,
    ):
        return int(text)

    m = re.fullmatch(
        r"([+-]?)(\d+)\.(\d+)",
        text,
    )

    if not m:
        raise RuntimeError(
            f"invalid fixed-decimal field={field}"
        )

    sign = (
        -1
        if m.group(1) == "-"
        else 1
    )

    whole = m.group(2)
    frac = m.group(3)

    if len(frac) > decimals:
        raise RuntimeError(
            f"too many decimals field={field}: "
            f"observed={len(frac)} expected<={decimals}"
        )

    frac = frac.ljust(
        decimals,
        "0",
    )

    return sign * (
        int(whole) * (10 ** decimals)
        + int(frac)
    )


def unique_zip_member(
    archive: Path,
    expected_member: str,
):
    zf = zipfile.ZipFile(
        archive
    )

    members = [
        x
        for x in zf.namelist()
        if not x.endswith("/")
    ]

    if members != [
        expected_member
    ]:
        zf.close()

        raise RuntimeError(
            f"{archive.name}: "
            f"unexpected members={members}"
        )

    return zf


def f17(x: float) -> str:
    x = float(x)

    if not math.isfinite(x):
        raise RuntimeError(
            "attempted to serialize non-finite value"
        )

    return format(
        x,
        ".17g",
    )


check_hashes()


# =============================================================================
# Upstream exact authorization
# =============================================================================

upstream = E4A2C_AUDIT.read_text(
    encoding="utf-8"
)

for token in (
    "E4A2C_EXACT_CPS_REPLICATE_ENGINE_CONTRACT=PASS",
    "E4A2D_FIRST_CPS_I_INFERENCE_EXECUTION_AUTHORIZED=1",
    "CPS_EXACT_REPLICATE_SET=PASS",
    "CPS_SYNTHETIC_ENGINE_PREFLIGHT=PASS",
    "NO_OUTCOME_BASED_CPS_I_GATE=PASS",
):
    if token not in upstream:
        raise RuntimeError(
            f"missing E4A2C invariant={token}"
        )


contract = json.loads(
    CONTRACT.read_text(
        encoding="utf-8"
    )
)

if contract["parent_commit"] != "3ab40ce":
    raise RuntimeError(
        "unexpected E4A2D parent commit"
    )

if (
    contract["engine"]["replicate_count"]
    != REPLICATE_COUNT
):
    raise RuntimeError(
        "replicate count differs from frozen engine"
    )


# =============================================================================
# Official layout anchors — parser positions are not inferred from outcomes
# =============================================================================

house_layout = HOUSE_LAYOUT.read_text(
    encoding="utf-8",
    errors="strict",
)

person_layout = PERSON_LAYOUT.read_text(
    encoding="utf-8",
    errors="strict",
)

house_layout_pass = all(
    anchor in house_layout
    for anchor in (
        "H_SEQ                 5   29",
        "HSUP_WGT              8   34",
        "H_HHTYPE              1   61",
        "H_TENURE              1   89",
    )
)

person_layout_pass = all(
    anchor in person_layout
    for anchor in (
        "PH_SEQ                5   36",
        "PPPOS                 2   43",
        "MARSUPWT              8   71",
        "A_AGE                 2   79",
        "A_EXPRRP              2   82",
        "WEUEMP                1  333",
        "WEWKRS                1  334",
        "WRK_CK                1  341",
    )
)

if not house_layout_pass:
    raise RuntimeError(
        "official household layout anchors failed"
    )

if not person_layout_pass:
    raise RuntimeError(
        "official person layout anchors failed"
    )


# =============================================================================
# Precommitted official replicate parser sentinels
# =============================================================================

sas_text = CPS_SAS.read_text(
    encoding="utf-8",
    errors="strict",
)

SENTINELS = [
    0,
    1,
    80,
    160,
]

official_sentinel_units: dict[int, int] = {}

for r in SENTINELS:
    matches = re.findall(
        rf"(?mi)^\s*PWWGT{r}\s*=\s*"
        rf"([0-9]+\.[0-9]+)\s*$",
        sas_text,
    )

    if len(matches) != 1:
        raise RuntimeError(
            f"official PWWGT{r} total occurrence count="
            f"{len(matches)}"
        )

    official_sentinel_units[r] = (
        parse_fixed_units(
            matches[0].encode("ascii"),
            4,
            f"OFFICIAL_PWWGT{r}_TOTAL",
        )
    )


# =============================================================================
# Main CPS household/reference-person file
#
# Only precommitted fields are interpreted.
# =============================================================================

households: dict[
    int,
    tuple[int, int],
] = {}

reference_people: dict[
    int,
    list[
        tuple[
            int,
            int,
            int,
            int,
            int,
        ]
    ],
] = defaultdict(list)


main_household_records = 0
main_person_records = 0
eligible_h_hhtype_1 = 0
reference_person_records = 0


with unique_zip_member(
    CPS_MAIN,
    "asec2019_pubuse.dat",
) as zf:

    with zf.open(
        "asec2019_pubuse.dat",
        "r",
    ) as raw:

        for bline in raw:

            line = bline.rstrip(
                b"\r\n"
            )

            if not line:
                continue

            record_type = line[0:1]

            if record_type == b"1":

                main_household_records += 1

                if len(line) < 89:
                    raise RuntimeError(
                        "short CPS household record"
                    )

                h_seq = parse_int_ascii(
                    line[28:33],
                    "H_SEQ",
                )

                hsup_cents = parse_fixed_units(
                    line[33:41],
                    2,
                    "HSUP_WGT",
                )

                h_hhtype = parse_int_ascii(
                    line[60:61],
                    "H_HHTYPE",
                )

                h_tenure = parse_int_ascii(
                    line[88:89],
                    "H_TENURE",
                )

                if h_hhtype == 1:

                    eligible_h_hhtype_1 += 1

                    if h_seq in households:
                        raise RuntimeError(
                            f"duplicate eligible household "
                            f"H_SEQ={h_seq}"
                        )

                    households[h_seq] = (
                        hsup_cents,
                        h_tenure,
                    )

            elif record_type == b"3":

                main_person_records += 1

                if len(line) < 341:
                    raise RuntimeError(
                        "short CPS person record"
                    )

                exprrp = parse_int_ascii(
                    line[81:83],
                    "A_EXPRRP",
                )

                if exprrp in {
                    1,
                    2,
                }:

                    ph_seq = parse_int_ascii(
                        line[35:40],
                        "PH_SEQ",
                    )

                    pppos = parse_int_ascii(
                        line[42:44],
                        "PPPOS",
                    )

                    age = parse_int_ascii(
                        line[78:80],
                        "A_AGE",
                    )

                    weuemp = parse_int_ascii(
                        line[332:333],
                        "WEUEMP",
                    )

                    wewkrs = parse_int_ascii(
                        line[333:334],
                        "WEWKRS",
                    )

                    wrk_ck = parse_int_ascii(
                        line[340:341],
                        "WRK_CK",
                    )

                    reference_person_records += 1

                    reference_people[
                        ph_seq
                    ].append(
                        (
                            pppos,
                            age,
                            weuemp,
                            wewkrs,
                            wrk_ck,
                        )
                    )


reference_count_failures = 0
reference_pppos_failures = 0

all_reference_outcomes: list[
    tuple[
        int,
        int,
        int,
    ]
] = []

for h_seq in households:

    refs = reference_people.get(
        h_seq,
        [],
    )

    if len(refs) != 1:

        reference_count_failures += 1
        continue

    (
        pppos,
        _age,
        weuemp,
        wewkrs,
        wrk_ck,
    ) = refs[0]

    if pppos != 41:
        reference_pppos_failures += 1

    all_reference_outcomes.append(
        (
            weuemp,
            wewkrs,
            wrk_ck,
        )
    )


reference_link_pass = (
    len(households) > 0
    and
    reference_count_failures == 0
    and
    reference_pppos_failures == 0
)


# Official public-use domains.
WEUEMP_ALLOWED = set(
    range(
        0,
        10,
    )
)

WEWKRS_ALLOWED = set(
    range(
        0,
        6,
    )
)

WRK_CK_ALLOWED = set(
    range(
        0,
        3,
    )
)

observed_weuemp = {
    x[0]
    for x in all_reference_outcomes
}

observed_wewkrs = {
    x[1]
    for x in all_reference_outcomes
}

observed_wrk_ck = {
    x[2]
    for x in all_reference_outcomes
}

outcome_domain_pass = (
    observed_weuemp
    <= WEUEMP_ALLOWED
    and
    observed_wewkrs
    <= WEWKRS_ALLOWED
    and
    observed_wrk_ck
    <= WRK_CK_ALLOWED
)


# =============================================================================
# Frozen G1 population
# =============================================================================

AGE_BANDS = [
    (
        "AGE25_34",
        25,
        34,
    ),
    (
        "AGE35_44",
        35,
        44,
    ),
    (
        "AGE45_54",
        45,
        54,
    ),
    (
        "AGE55_64",
        55,
        64,
    ),
]

TENURE_LABEL = {
    1: "OWNER",
    2: "RENTER",
}


selected_rows: list[
    tuple[
        int,
        int,
        int,
        str,
        str,
        int,
        int,
        int,
        int,
    ]
] = []


for h_seq, (
    hsup_cents,
    h_tenure,
) in households.items():

    refs = reference_people.get(
        h_seq,
        [],
    )

    if len(refs) != 1:
        continue

    (
        pppos,
        age,
        weuemp,
        wewkrs,
        wrk_ck,
    ) = refs[0]

    if pppos != 41:
        continue

    tenure = TENURE_LABEL.get(
        h_tenure
    )

    if tenure is None:
        continue

    age_band = None

    for (
        label,
        low,
        high,
    ) in AGE_BANDS:

        if low <= age <= high:

            age_band = label
            break

    if age_band is None:
        continue

    selected_rows.append(
        (
            h_seq,
            pppos,
            hsup_cents,
            age_band,
            tenure,
            age,
            weuemp,
            wewkrs,
            wrk_ck,
        )
    )


selected_rows.sort(
    key=lambda x: (
        x[0],
        x[1],
    )
)


selected_count = len(
    selected_rows
)

if selected_count == 0:
    raise RuntimeError(
        "no rows in frozen G1 CPS population"
    )


selected_keys = [
    (
        row[0],
        row[1],
    )
    for row in selected_rows
]

if len(
    set(
        selected_keys
    )
) != selected_count:
    raise RuntimeError(
        "selected CPS reference-person keys are not unique"
    )


key_to_row = {
    key: i
    for i, key in enumerate(
        selected_keys
    )
}


hseq = np.asarray(
    [
        row[0]
        for row in selected_rows
    ],
    dtype=np.int64,
)

hsup = np.asarray(
    [
        row[2] / 100.0
        for row in selected_rows
    ],
    dtype=np.float64,
)

age_band = np.asarray(
    [
        row[3]
        for row in selected_rows
    ],
    dtype=object,
)

tenure = np.asarray(
    [
        row[4]
        for row in selected_rows
    ],
    dtype=object,
)

weuemp = np.asarray(
    [
        row[6]
        for row in selected_rows
    ],
    dtype=np.int16,
)

wewkrs = np.asarray(
    [
        row[7]
        for row in selected_rows
    ],
    dtype=np.int16,
)

wrk_ck = np.asarray(
    [
        row[8]
        for row in selected_rows
    ],
    dtype=np.int16,
)


# =============================================================================
# Replicate values — first real PWWGT1-PWWGT160 opening
#
# Store only frozen G1 reference-person rows. All-file parsing additionally
# checks the precommitted official total sentinels.
# =============================================================================

replicate_weights = np.empty(
    (
        selected_count,
        REPLICATE_COUNT,
    ),
    dtype=np.float64,
)

replicate_found = np.zeros(
    selected_count,
    dtype=bool,
)

sentinel_sums = {
    r: 0
    for r in SENTINELS
}

replicate_records = 0
replicate_lrecl_failures = 0
selected_negative_replicate_weight_count = 0


with unique_zip_member(
    CPS_REP,
    "CPS_ASEC_ASCII_REPWGT_2019.dat",
) as zf:

    with zf.open(
        "CPS_ASEC_ASCII_REPWGT_2019.dat",
        "r",
    ) as raw:

        for bline in raw:

            line = bline.rstrip(
                b"\r\n"
            )

            if not line:
                continue

            replicate_records += 1

            if len(line) != 1456:

                replicate_lrecl_failures += 1
                continue

            for r in SENTINELS:

                sentinel_sums[r] += (
                    parse_fixed_units(
                        line[
                            9 * r:
                            9 * (r + 1)
                        ],
                        4,
                        f"PWWGT{r}",
                    )
                )

            rep_h_seq = parse_int_ascii(
                line[1449:1454],
                "REPLICATE_H_SEQ",
            )

            rep_pppos = parse_int_ascii(
                line[1454:1456],
                "REPLICATE_PPPOS",
            )

            idx = key_to_row.get(
                (
                    rep_h_seq,
                    rep_pppos,
                )
            )

            if idx is None:
                continue

            if replicate_found[
                idx
            ]:

                raise RuntimeError(
                    "duplicate selected replicate match "
                    f"H_SEQ={rep_h_seq} PPPOS={rep_pppos}"
                )

            vals = np.fromiter(
                (
                    parse_fixed_units(
                        line[
                            9 * r:
                            9 * (r + 1)
                        ],
                        4,
                        f"PWWGT{r}",
                    )
                    / 10000.0

                    for r in range(
                        1,
                        161,
                    )
                ),
                dtype=np.float64,
                count=160,
            )

            selected_negative_replicate_weight_count += int(
                np.count_nonzero(
                    vals < 0.0
                )
            )

            replicate_weights[
                idx,
                :,
            ] = vals

            replicate_found[
                idx
            ] = True


replicate_lrecl_pass = (
    replicate_records > 0
    and
    replicate_lrecl_failures == 0
)

replicate_match_pass = bool(
    np.all(
        replicate_found
    )
)

sentinel_pass = all(
    sentinel_sums[r]
    == official_sentinel_units[r]
    for r in SENTINELS
)


if not replicate_match_pass:
    raise RuntimeError(
        "not every selected reference person "
        "has one replicate record"
    )


# =============================================================================
# Exact frozen estimands
# =============================================================================

ESTIMANDS = [
    (
        "I_FYFT_SHARE",
        "PRIMARY",
        1,
        np.isin(
            wewkrs,
            [
                1,
            ],
        ).astype(
            np.float64
        ),
    ),
    (
        "I_SEARCH_BURDEN_SHARE",
        "PRIMARY",
        -1,
        np.isin(
            weuemp,
            [
                2,
                3,
                4,
                5,
                6,
                7,
            ],
        ).astype(
            np.float64
        ),
    ),
    (
        "I_LONG_SEARCH_SHARE",
        "SECONDARY",
        -1,
        np.isin(
            weuemp,
            [
                6,
                7,
            ],
        ).astype(
            np.float64
        ),
    ),
    (
        "I_ANY_WORK_SHARE",
        "SECONDARY",
        1,
        np.isin(
            wrk_ck,
            [
                1,
            ],
        ).astype(
            np.float64
        ),
    ),
]


cohort_results: list[
    dict[str, object]
] = []

difference_results: list[
    dict[str, object]
] = []

replicate_output: list[
    dict[str, object]
] = []

support_rows: list[
    dict[str, object]
] = []


cohort_inference: dict[
    tuple[
        str,
        str,
        str,
    ],
    object,
] = {}


nonpositive_full_denominators = 0
nonpositive_replicate_denominators = 0
nonfinite_replicate_denominators = 0
nonfinite_estimates = 0
cohort_empty_count = 0


for (
    band,
    _low,
    _high,
) in AGE_BANDS:

    for ten in (
        "OWNER",
        "RENTER",
    ):

        mask = (
            (age_band == band)
            &
            (tenure == ten)
        )

        n = int(
            np.count_nonzero(
                mask
            )
        )

        if n == 0:

            cohort_empty_count += 1
            continue

        w0 = hsup[
            mask
        ]

        wr = replicate_weights[
            mask,
            :,
        ]

        full_denominator = float(
            np.sum(
                w0
            )
        )

        rep_denominators = np.sum(
            wr,
            axis=0,
        )

        if (
            not math.isfinite(
                full_denominator
            )
            or
            full_denominator <= 0.0
        ):
            nonpositive_full_denominators += 1

        nonfinite_replicate_denominators += int(
            np.count_nonzero(
                ~np.isfinite(
                    rep_denominators
                )
            )
        )

        nonpositive_replicate_denominators += int(
            np.count_nonzero(
                rep_denominators
                <= 0.0
            )
        )

        support_rows.append(
            {
                "year": 2019,
                "age_band": band,
                "tenure": ten,
                "unweighted_n": n,
                "full_sample_weight_sum": full_denominator,
                "replicate_denominator_min":
                    float(
                        np.min(
                            rep_denominators
                        )
                    ),
                "replicate_denominator_max":
                    float(
                        np.max(
                            rep_denominators
                        )
                    ),
                "replicate_count":
                    REPLICATE_COUNT,
            }
        )

        for (
            estimand,
            role,
            state_sign,
            indicator,
        ) in ESTIMANDS:

            inf = weighted_share_with_replicates(
                indicator[
                    mask
                ],
                w0,
                wr,
            )

            values_to_check = np.concatenate(
                (
                    np.asarray(
                        [
                            inf.theta0,
                            inf.variance,
                            inf.standard_error,
                        ],
                        dtype=np.float64,
                    ),
                    inf.replicate_estimates,
                )
            )

            if not np.isfinite(
                values_to_check
            ).all():

                nonfinite_estimates += 1

            cohort_inference[
                (
                    band,
                    ten,
                    estimand,
                )
            ] = inf

            cohort_results.append(
                {
                    "year": 2019,
                    "age_band": band,
                    "tenure": ten,
                    "estimand": estimand,
                    "role": role,
                    "state_sign": state_sign,
                    "unweighted_n": n,
                    "point_estimate":
                        inf.theta0,
                    "replicate_variance":
                        inf.variance,
                    "replicate_se":
                        inf.standard_error,
                    "replicate_count":
                        REPLICATE_COUNT,
                }
            )

            for r, value in enumerate(
                inf.replicate_estimates,
                start=1,
            ):

                replicate_output.append(
                    {
                        "year": 2019,
                        "statistic_type":
                            "COHORT_SHARE",
                        "age_band":
                            band,
                        "tenure_or_contrast":
                            ten,
                        "estimand":
                            estimand,
                        "replicate":
                            r,
                        "value":
                            float(
                                value
                            ),
                    }
                )


# =============================================================================
# Direct renter-minus-owner covariance-preserving contrasts
# =============================================================================

for (
    band,
    _low,
    _high,
) in AGE_BANDS:

    owner_mask = (
        (age_band == band)
        &
        (tenure == "OWNER")
    )

    renter_mask = (
        (age_band == band)
        &
        (tenure == "RENTER")
    )

    owner_n = int(
        np.count_nonzero(
            owner_mask
        )
    )

    renter_n = int(
        np.count_nonzero(
            renter_mask
        )
    )

    if (
        owner_n == 0
        or
        renter_n == 0
    ):
        continue

    for (
        estimand,
        role,
        state_sign,
        indicator,
    ) in ESTIMANDS:

        diff = (
            owner_renter_difference_with_replicates(
                indicator,
                owner_mask,
                renter_mask,
                hsup,
                replicate_weights,
            )
        )

        values_to_check = np.concatenate(
            (
                np.asarray(
                    [
                        diff.delta0,
                        diff.variance,
                        diff.standard_error,
                    ],
                    dtype=np.float64,
                ),
                diff.replicate_differences,
            )
        )

        if not np.isfinite(
            values_to_check
        ).all():

            nonfinite_estimates += 1

        difference_results.append(
            {
                "year": 2019,
                "age_band": band,
                "contrast":
                    "RENTER_MINUS_OWNER",
                "estimand": estimand,
                "role": role,
                "state_sign": state_sign,
                "owner_unweighted_n":
                    owner_n,
                "renter_unweighted_n":
                    renter_n,
                "difference":
                    diff.delta0,
                "replicate_variance":
                    diff.variance,
                "replicate_se":
                    diff.standard_error,
                "replicate_count":
                    REPLICATE_COUNT,
            }
        )

        for r, value in enumerate(
            diff.replicate_differences,
            start=1,
        ):

            replicate_output.append(
                {
                    "year": 2019,
                    "statistic_type":
                        "RENTER_MINUS_OWNER",
                    "age_band":
                        band,
                    "tenure_or_contrast":
                        "RENTER_MINUS_OWNER",
                    "estimand":
                        estimand,
                    "replicate":
                        r,
                    "value":
                        float(
                            value
                        ),
                }
            )


# =============================================================================
# Structural-only hard gates
# =============================================================================

cohort_count_pass = (
    cohort_empty_count == 0
    and
    len(
        support_rows
    ) == 8
)

denominator_pass = (
    nonpositive_full_denominators
    == 0
    and
    nonpositive_replicate_denominators
    == 0
    and
    nonfinite_replicate_denominators
    == 0
)

finite_pass = (
    nonfinite_estimates == 0
)

cohort_shape_pass = (
    len(
        cohort_results
    ) == 32
)

difference_shape_pass = (
    len(
        difference_results
    ) == 16
)

cohort_rep_rows = sum(
    1
    for row in replicate_output
    if row[
        "statistic_type"
    ] == "COHORT_SHARE"
)

difference_rep_rows = sum(
    1
    for row in replicate_output
    if row[
        "statistic_type"
    ] == "RENTER_MINUS_OWNER"
)

replicate_shape_pass = (
    cohort_rep_rows == 5120
    and
    difference_rep_rows == 2560
    and
    len(
        replicate_output
    ) == 7680
)

point_share_range_pass = all(
    0.0 <= float(
        row[
            "point_estimate"
        ]
    ) <= 1.0
    for row in cohort_results
)

# This range gate is mathematical only: full-sample positive-weight binary
# shares must be in [0,1]. It is not an economic magnitude gate.
structural_pass = all(
    [
        reference_link_pass,
        outcome_domain_pass,
        replicate_lrecl_pass,
        replicate_match_pass,
        sentinel_pass,
        cohort_count_pass,
        denominator_pass,
        finite_pass,
        cohort_shape_pass,
        difference_shape_pass,
        replicate_shape_pass,
        point_share_range_pass,
    ]
)


# =============================================================================
# Deterministic result serialization
# =============================================================================

OUT_COHORT.parent.mkdir(
    parents=True,
    exist_ok=True,
)


with OUT_COHORT.open(
    "w",
    encoding="utf-8",
    newline="",
) as f:

    fields = [
        "year",
        "age_band",
        "tenure",
        "estimand",
        "role",
        "state_sign",
        "unweighted_n",
        "point_estimate",
        "replicate_variance",
        "replicate_se",
        "replicate_count",
    ]

    w = csv.DictWriter(
        f,
        fieldnames=fields,
        delimiter="\t",
        lineterminator="\n",
    )

    w.writeheader()

    for row in cohort_results:

        out = dict(
            row
        )

        for key in (
            "point_estimate",
            "replicate_variance",
            "replicate_se",
        ):
            out[
                key
            ] = f17(
                out[
                    key
                ]
            )

        w.writerow(
            out
        )


with OUT_DIFF.open(
    "w",
    encoding="utf-8",
    newline="",
) as f:

    fields = [
        "year",
        "age_band",
        "contrast",
        "estimand",
        "role",
        "state_sign",
        "owner_unweighted_n",
        "renter_unweighted_n",
        "difference",
        "replicate_variance",
        "replicate_se",
        "replicate_count",
    ]

    w = csv.DictWriter(
        f,
        fieldnames=fields,
        delimiter="\t",
        lineterminator="\n",
    )

    w.writeheader()

    for row in difference_results:

        out = dict(
            row
        )

        for key in (
            "difference",
            "replicate_variance",
            "replicate_se",
        ):
            out[
                key
            ] = f17(
                out[
                    key
                ]
            )

        w.writerow(
            out
        )


with OUT_REPS.open(
    "w",
    encoding="utf-8",
    newline="",
) as f:

    fields = [
        "year",
        "statistic_type",
        "age_band",
        "tenure_or_contrast",
        "estimand",
        "replicate",
        "value",
    ]

    w = csv.DictWriter(
        f,
        fieldnames=fields,
        delimiter="\t",
        lineterminator="\n",
    )

    w.writeheader()

    for row in replicate_output:

        out = dict(
            row
        )

        out[
            "value"
        ] = f17(
            out[
                "value"
            ]
        )

        w.writerow(
            out
        )


with OUT_SUPPORT.open(
    "w",
    encoding="utf-8",
    newline="",
) as f:

    fields = [
        "year",
        "age_band",
        "tenure",
        "unweighted_n",
        "full_sample_weight_sum",
        "replicate_denominator_min",
        "replicate_denominator_max",
        "replicate_count",
    ]

    w = csv.DictWriter(
        f,
        fieldnames=fields,
        delimiter="\t",
        lineterminator="\n",
    )

    w.writeheader()

    for row in support_rows:

        out = dict(
            row
        )

        for key in (
            "full_sample_weight_sum",
            "replicate_denominator_min",
            "replicate_denominator_max",
        ):
            out[
                key
            ] = f17(
                out[
                    key
                ]
            )

        w.writerow(
            out
        )


# =============================================================================
# Audit: observed values are reported, never used as hypothesis gates
# =============================================================================

lines = [
    "=" * 100,
    "E4A2D — FIRST CPS I INFERENCE EXECUTION",
    "=" * 100,
    "",
    "CPS_I_VALUES_READ=1",
    "CPS_PWWGT1_160_VALUES_PARSED=1",
    "SCF_K_D_VALUES_READ=0",
    "DIMENSIONALITY_ANALYSIS_PERFORMED=0",
    "",
    "===== SOURCE / PARSER =====",
    "CPS_HOUSEHOLD_LAYOUT_VALUESIDE=PASS"
        if house_layout_pass
        else
        "CPS_HOUSEHOLD_LAYOUT_VALUESIDE=FAIL",
    "CPS_PERSON_LAYOUT_VALUESIDE=PASS"
        if person_layout_pass
        else
        "CPS_PERSON_LAYOUT_VALUESIDE=FAIL",
    f"CPS_MAIN_HOUSEHOLD_RECORDS={main_household_records}",
    f"CPS_MAIN_PERSON_RECORDS={main_person_records}",
    f"CPS_H_HHTYPE_1_HOUSEHOLDS={eligible_h_hhtype_1}",
    f"CPS_REFERENCE_PERSON_RECORDS={reference_person_records}",
    "CPS_REFERENCE_PERSON_LINKAGE_VALUESIDE=PASS"
        if reference_link_pass
        else
        "CPS_REFERENCE_PERSON_LINKAGE_VALUESIDE=FAIL",
    "CPS_I_OUTCOME_CODE_DOMAINS=PASS"
        if outcome_domain_pass
        else
        "CPS_I_OUTCOME_CODE_DOMAINS=FAIL",
    (
        "WEUEMP_OBSERVED_CODES="
        + ",".join(
            str(x)
            for x in sorted(
                observed_weuemp
            )
        )
    ),
    (
        "WEWKRS_OBSERVED_CODES="
        + ",".join(
            str(x)
            for x in sorted(
                observed_wewkrs
            )
        )
    ),
    (
        "WRK_CK_OBSERVED_CODES="
        + ",".join(
            str(x)
            for x in sorted(
                observed_wrk_ck
            )
        )
    ),
    "",
    "===== REPLICATE VALUE PARSER =====",
    f"CPS_REPLICATE_RECORDS={replicate_records}",
    "CPS_REPLICATE_LRECL_1456_VALUESIDE=PASS"
        if replicate_lrecl_pass
        else
        "CPS_REPLICATE_LRECL_1456_VALUESIDE=FAIL",
    f"CPS_SELECTED_G1_REFERENCE_PERSONS={selected_count}",
    "CPS_SELECTED_REFERENCE_REPLICATE_MATCH=PASS"
        if replicate_match_pass
        else
        "CPS_SELECTED_REFERENCE_REPLICATE_MATCH=FAIL",
    "CPS_REPLICATE_SENTINEL_TOTALS=PWWGT0,PWWGT1,PWWGT80,PWWGT160",
    "CPS_REPLICATE_SENTINEL_OFFICIAL_SUM_CHECK=PASS"
        if sentinel_pass
        else
        "CPS_REPLICATE_SENTINEL_OFFICIAL_SUM_CHECK=FAIL",
    (
        "CPS_SELECTED_NEGATIVE_REPLICATE_WEIGHT_COUNT="
        f"{selected_negative_replicate_weight_count}"
    ),
    "CPS_NEGATIVE_REPLICATE_WEIGHT_CLIPPING_PERFORMED=0",
    "",
    "===== FROZEN G1 COHORTS =====",
    "CPS_G1_COHORT_COUNT=8",
    "CPS_ALL_G1_COHORTS_NONEMPTY=PASS"
        if cohort_count_pass
        else
        "CPS_ALL_G1_COHORTS_NONEMPTY=FAIL",
    "CPS_FULL_SAMPLE_DENOMINATORS_POSITIVE=PASS"
        if (
            nonpositive_full_denominators
            == 0
        )
        else
        "CPS_FULL_SAMPLE_DENOMINATORS_POSITIVE=FAIL",
    "CPS_REPLICATE_DOMAIN_DENOMINATORS_FINITE_POSITIVE=PASS"
        if denominator_pass
        else
        "CPS_REPLICATE_DOMAIN_DENOMINATORS_FINITE_POSITIVE=FAIL",
    "",
    "===== FIRST REAL I INFERENCE =====",
    "I_PRIMARY_1=I_FYFT_SHARE",
    "I_PRIMARY_2=I_SEARCH_BURDEN_SHARE",
    "I_SECONDARY_1=I_LONG_SEARCH_SHARE",
    "I_SECONDARY_2=I_ANY_WORK_SHARE",
    f"CPS_I_COHORT_ESTIMATE_ROWS={len(cohort_results)}",
    f"CPS_I_COHORT_REPLICATE_ROWS={cohort_rep_rows}",
    f"CPS_I_OWNER_RENTER_DIFFERENCE_ROWS={len(difference_results)}",
    f"CPS_I_DIFFERENCE_REPLICATE_ROWS={difference_rep_rows}",
    "CPS_I_EXACT_OUTPUT_SHAPE=PASS"
        if (
            cohort_shape_pass
            and
            difference_shape_pass
            and
            replicate_shape_pass
        )
        else
        "CPS_I_EXACT_OUTPUT_SHAPE=FAIL",
    "CPS_I_ALL_ESTIMATES_FINITE=PASS"
        if finite_pass
        else
        "CPS_I_ALL_ESTIMATES_FINITE=FAIL",
    "CPS_I_FULL_SAMPLE_BINARY_SHARE_RANGE=PASS"
        if point_share_range_pass
        else
        "CPS_I_FULL_SAMPLE_BINARY_SHARE_RANGE=FAIL",
    "",
    "===== OUTCOME-INDEPENDENT GATES =====",
    "SIGN_GATE=0",
    "MAGNITUDE_GATE=0",
    "OWNER_RENTER_DIRECTION_GATE=0",
    "SE_MAGNITUDE_GATE=0",
    "SIGNIFICANCE_GATE=0",
    "DIMENSIONALITY_GATE=0",
    "NO_OUTCOME_BASED_I_GATE=PASS",
    "",
    "I_VALUES_OPENED=1",
    "I_EMPIRICALLY_TESTED=1"
        if structural_pass
        else
        "I_EMPIRICALLY_TESTED=0",
    "I_VALUES_REUSABLE_UNDER_FROZEN_PROVENANCE=1"
        if structural_pass
        else
        "I_VALUES_REUSABLE_UNDER_FROZEN_PROVENANCE=0",
    "I_SCALAR_AUTHORIZED=0",
    "",
    "K_VALUES_OPEN_AUTHORIZED=0",
    "D_VALUES_OPEN_AUTHORIZED=0",
    "K_D_I_INFERENCE_AUTHORIZED=0",
    "K_EMPIRICALLY_TESTED=0",
    "D_EMPIRICALLY_TESTED=0",
    "FIVE_DIMENSIONALITY_PROVEN=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "",
    "E4A2D_FIRST_CPS_I_INFERENCE_EXECUTION=PASS"
        if structural_pass
        else
        "E4A2D_FIRST_CPS_I_INFERENCE_EXECUTION=FAIL",
    "E4A2E_EXACT_SCF_REPLICATE_ENGINE_PREFLIGHT_AUTHORIZED=1"
        if structural_pass
        else
        "E4A2E_EXACT_SCF_REPLICATE_ENGINE_PREFLIGHT_AUTHORIZED=0",
]

text = (
    "\n".join(
        lines
    )
    + "\n"
)

AUDIT.write_text(
    text,
    encoding="utf-8",
)

sys.stdout.write(
    text
)

if not structural_pass:
    raise SystemExit(
        1
    )
