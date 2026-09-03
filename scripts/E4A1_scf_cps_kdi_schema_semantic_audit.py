from __future__ import annotations

import hashlib
import json
import tempfile
import zipfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

CPS = (
    ROOT
    / "data/raw/cps_asec/2022/asec2022_pubuse.zip"
)

SCF_FULL = (
    ROOT
    / "data/raw/scf/2022/scf2022s.zip"
)

SCF_SUM = (
    ROOT
    / "data/raw/scf/2022/scfp2022s.zip"
)

CPS_META = (
    ROOT
    / "data/metadata/E3B1_cps_2022_variables.json"
)

E4A_CONTRACT = (
    ROOT
    / "data/metadata/E4A_kdi_household_state_architecture.json"
)

SEMANTICS = (
    ROOT
    / "data/metadata/E4A1_official_semantic_evidence.tsv"
)

SCHEMA_OUT = (
    ROOT
    / "data/metadata/E4A1_local_schema_audit.tsv"
)

HASH_OUT = (
    ROOT
    / "data/metadata/E4A1_local_source_hashes.tsv"
)

AUDIT = (
    ROOT
    / "data/metadata/E4A1_scf_cps_kdi_schema_semantic_audit.txt"
)


# =============================================================================
# Helpers
# =============================================================================

def sha256(path: Path) -> str:

    h = hashlib.sha256()

    with path.open("rb") as f:

        for block in iter(
            lambda: f.read(1024 * 1024),
            b"",
        ):
            h.update(block)

    return h.hexdigest()


def exact_members(
    archive: Path,
) -> list[str]:

    with zipfile.ZipFile(
        archive
    ) as zf:

        return zf.namelist()


def stata_columns_from_zip(
    archive: Path,
    expected_member: str,
) -> list[str]:

    with zipfile.ZipFile(
        archive
    ) as zf:

        members = zf.namelist()

        if members != [
            expected_member
        ]:
            raise RuntimeError(
                f"{archive.name}: "
                f"unexpected members={members}"
            )

        with tempfile.TemporaryDirectory() as td:

            out = (
                Path(td)
                / Path(
                    expected_member
                ).name
            )

            with zf.open(
                expected_member
            ) as src:

                out.write_bytes(
                    src.read()
                )

            reader = pd.read_stata(
                out,
                iterator=True,
                convert_categoricals=False,
            )

            try:

                labels = reader.variable_labels()

                cols = [
                    str(x).lower()
                    for x in labels.keys()
                ]

            finally:

                try:
                    reader.close()
                except Exception:
                    pass

    return cols


# =============================================================================
# Local archive structure — metadata only
# =============================================================================

for p in (
    CPS,
    SCF_FULL,
    SCF_SUM,
    CPS_META,
    E4A_CONTRACT,
    SEMANTICS,
):

    if not p.is_file():
        raise RuntimeError(
            f"missing required file={p}"
        )


cps_members = exact_members(
    CPS
)

scf_full_members = exact_members(
    SCF_FULL
)

scf_sum_members = exact_members(
    SCF_SUM
)


cps_archive_pass = (
    cps_members
    == ["asec2022_pubuse.dat"]
)

scf_archive_pass = (
    scf_full_members
    == ["p22i6.dta"]
    and scf_sum_members
    == ["rscfp2022.dta"]
)


# =============================================================================
# Actual SCF Stata metadata
# =============================================================================

full_cols = set(
    stata_columns_from_zip(
        SCF_FULL,
        "p22i6.dta",
    )
)

sum_cols = set(
    stata_columns_from_zip(
        SCF_SUM,
        "rscfp2022.dta",
    )
)


required_full = {
    "y1",
    "x42001",
    "x14",
    "x508",
    "x601",
    "x701",
    "x7133",
}

required_sum = {
    "y1",
    "yy1",
    "wgt",
    "fin",
    "liq",
    "equity",
    "retqliq",
    "pirtotal",
    "debt2inc",
    "debt",
    "houses",
    "homeeq",
}


missing_full = sorted(
    required_full
    - full_cols
)

missing_sum = sorted(
    required_sum
    - sum_cols
)


scf_schema_pass = (
    not missing_full
    and not missing_sum
)


# =============================================================================
# Frozen Census API metadata inventory
# =============================================================================

obj = json.loads(
    CPS_META.read_text(
        encoding="utf-8"
    )
)


variables = obj.get(
    "variables",
    obj,
)


required_cps = {
    "H_SEQ",
    "HSUP_WGT",
    "H_TENURE",
    "HTOTVAL",
    "A_AGE",
    "A_EXPRRP",
    "HRSWK",
    "LKWEEKS",
    "NWLKWK",
    "WEUEMP",
    "WEWKRS",
    "WEXP",
    "WKSWORK",
    "WORKYN",
    "WTEMP",
}


missing_cps = sorted(
    x
    for x in required_cps
    if x not in variables
)


cps_metadata_pass = (
    not missing_cps
)


# =============================================================================
# Official semantic evidence table
# =============================================================================

sem = pd.read_csv(
    SEMANTICS,
    sep="\t",
    dtype=str,
).fillna("")


sem_by_var = {
    row["variable"]:
        row
    for _, row in sem.iterrows()
}


required_semantic_vars = {
    "H_SEQ",
    "HSUP_WGT",
    "H_TENURE",
    "HTOTVAL",
    "A_AGE",
    "A_EXPRRP",
    "HRSWK",
    "LKWEEKS",
    "NWLKWK",
    "WEUEMP",
    "WEWKRS",
    "WEXP",
    "WKSWORK",
    "WORKYN",
    "WTEMP",
    "FIN",
    "PIRTOTAL",
    "DEBT2INC",
    "X42001",
}


semantic_manifest_pass = (
    required_semantic_vars
    <= set(
        sem_by_var
    )
)


wewkrs_is_recode = (
    sem_by_var[
        "WEWKRS"
    ][
        "semantic_class"
    ]
    == "CATEGORICAL_RECODE"
)


weuemp_is_recode = (
    sem_by_var[
        "WEUEMP"
    ][
        "semantic_class"
    ]
    == "CATEGORICAL_RECODE"
)


wkswork_is_cardinal = (
    sem_by_var[
        "WKSWORK"
    ][
        "semantic_class"
    ]
    == "CARDINAL_WEEKS"
)


lkweeks_is_cardinal = (
    sem_by_var[
        "LKWEEKS"
    ][
        "semantic_class"
    ]
    == "CARDINAL_WEEKS"
)


nwlkwk_is_cardinal = (
    sem_by_var[
        "NWLKWK"
    ][
        "semantic_class"
    ]
    == "CARDINAL_WEEKS"
)


# =============================================================================
# Test frozen E4A I semantics against official coding
# =============================================================================

architecture = json.loads(
    E4A_CONTRACT.read_text(
        encoding="utf-8"
    )
)


i_primary = {
    x["variable"]:
        x["direction"]
    for x in architecture[
        "I"
    ][
        "primary_observables"
    ]
}


e4a_wewkrs_claim = (
    i_primary.get(
        "WEWKRS"
    )
    == "HIGHER_BETTER"
)


e4a_weuemp_claim = (
    i_primary.get(
        "WEUEMP"
    )
    == "HIGHER_WORSE"
)


# Higher numeric WEWKRS is NOT monotonic better:
# 1 = full-year full-time
# ...
# 5 = nonworker.
wewkrs_e4a_semantics_pass = not (
    e4a_wewkrs_claim
    and wewkrs_is_recode
)


# WEUEMP includes 8=full-year worker and 9=nonworker,
# so global numeric ordering cannot represent a monotonic
# search-burden scale.
weuemp_e4a_semantics_pass = not (
    e4a_weuemp_claim
    and weuemp_is_recode
)


i_semantic_pass = all([
    wewkrs_e4a_semantics_pass,
    weuemp_e4a_semantics_pass,
])


repair_candidates_pass = all([
    wkswork_is_cardinal,
    lkweeks_is_cardinal,
    nwlkwk_is_cardinal,
])


# =============================================================================
# Structural schema table
# =============================================================================

schema_rows = []


for var in sorted(
    required_full
):

    schema_rows.append({
        "source":
            "SCF_FULL",
        "variable":
            var.upper(),
        "present":
            int(
                var in full_cols
            ),
        "economic_value_read":
            0,
    })


for var in sorted(
    required_sum
):

    schema_rows.append({
        "source":
            "SCF_SUMMARY",
        "variable":
            var.upper(),
        "present":
            int(
                var in sum_cols
            ),
        "economic_value_read":
            0,
    })


for var in sorted(
    required_cps
):

    schema_rows.append({
        "source":
            "CPS_ASEC_METADATA",
        "variable":
            var,
        "present":
            int(
                var in variables
            ),
        "economic_value_read":
            0,
    })


schema_df = pd.DataFrame(
    schema_rows
)


schema_df.to_csv(
    SCHEMA_OUT,
    sep="\t",
    index=False,
)


hash_df = pd.DataFrame([
    {
        "artifact":
            str(
                CPS.relative_to(
                    ROOT
                )
            ),
        "sha256":
            sha256(
                CPS
            ),
    },
    {
        "artifact":
            str(
                SCF_FULL.relative_to(
                    ROOT
                )
            ),
        "sha256":
            sha256(
                SCF_FULL
            ),
    },
    {
        "artifact":
            str(
                SCF_SUM.relative_to(
                    ROOT
                )
            ),
        "sha256":
            sha256(
                SCF_SUM
            ),
    },
    {
        "artifact":
            str(
                CPS_META.relative_to(
                    ROOT
                )
            ),
        "sha256":
            sha256(
                CPS_META
            ),
    },
])


hash_df.to_csv(
    HASH_OUT,
    sep="\t",
    index=False,
)


# =============================================================================
# Classification
# =============================================================================

structural_schema_pass = all([
    cps_archive_pass,
    scf_archive_pass,
    scf_schema_pass,
    cps_metadata_pass,
    semantic_manifest_pass,
])


# This audit is expected to FAIL if the frozen E4A I semantic
# assumption is contradicted by official source coding.
overall = (
    structural_schema_pass
    and i_semantic_pass
)


repair_authorized = (
    structural_schema_pass
    and not i_semantic_pass
    and repair_candidates_pass
)


lines = [
    "=" * 100,
    "E4A1 — SCF / CPS K-D-I SCHEMA + SEMANTIC AUDIT",
    "=" * 100,
    "",
    "CPS_DATA_ROWS_PARSED=0",
    "SCF_DATA_ROWS_PARSED=0",
    "CPS_I_VALUES_READ=0",
    "SCF_K_VALUES_READ=0",
    "SCF_D_VALUES_READ=0",
    "",
    "===== LOCAL ARCHIVES =====",
    (
        "CPS_LOCAL_ARCHIVE_STRUCTURE=PASS"
        if cps_archive_pass
        else
        "CPS_LOCAL_ARCHIVE_STRUCTURE=FAIL"
    ),
    (
        "SCF_LOCAL_ARCHIVE_STRUCTURE=PASS"
        if scf_archive_pass
        else
        "SCF_LOCAL_ARCHIVE_STRUCTURE=FAIL"
    ),
    "",
    "===== SCF STATA METADATA =====",
    f"SCF_FULL_REQUIRED_VARIABLES={len(required_full)}",
    f"SCF_FULL_MISSING={','.join(missing_full) if missing_full else 'NONE'}",
    f"SCF_SUMMARY_REQUIRED_VARIABLES={len(required_sum)}",
    f"SCF_SUMMARY_MISSING={','.join(missing_sum) if missing_sum else 'NONE'}",
    (
        "SCF_K_D_SCHEMA=PASS"
        if scf_schema_pass
        else
        "SCF_K_D_SCHEMA=FAIL"
    ),
    "",
    "===== CPS METADATA =====",
    f"CPS_REQUIRED_VARIABLES={len(required_cps)}",
    f"CPS_METADATA_MISSING={','.join(missing_cps) if missing_cps else 'NONE'}",
    (
        "CPS_OFFICIAL_METADATA_VARIABLES=PASS"
        if cps_metadata_pass
        else
        "CPS_OFFICIAL_METADATA_VARIABLES=FAIL"
    ),
    "",
    "===== E4A I SEMANTIC FALSIFICATION =====",
    "WEWKRS_OFFICIAL_CLASS=CATEGORICAL_RECODE",
    "WEWKRS_OFFICIAL_POSITION=334",
    "WEWKRS_OFFICIAL_LENGTH=1",
    "WEWKRS_NUMERIC_HIGHER_EQUALS_BETTER=0",
    (
        "E4A_WEWKRS_DIRECTION_SEMANTICS=PASS"
        if wewkrs_e4a_semantics_pass
        else
        "E4A_WEWKRS_DIRECTION_SEMANTICS=FAIL"
    ),
    "",
    "WEUEMP_OFFICIAL_CLASS=CATEGORICAL_RECODE",
    "WEUEMP_OFFICIAL_POSITION=333",
    "WEUEMP_OFFICIAL_LENGTH=1",
    "WEUEMP_GLOBAL_NUMERIC_HIGHER_EQUALS_WORSE=0",
    (
        "E4A_WEUEMP_DIRECTION_SEMANTICS=PASS"
        if weuemp_e4a_semantics_pass
        else
        "E4A_WEUEMP_DIRECTION_SEMANTICS=FAIL"
    ),
    "",
    (
        "E4A_I_PRIMARY_SEMANTICS=PASS"
        if i_semantic_pass
        else
        "E4A_I_PRIMARY_SEMANTICS=FAIL"
    ),
    "",
    "===== REPAIR CANDIDATES =====",
    "WKSWORK_OFFICIAL_CLASS=CARDINAL_WEEKS",
    "WKSWORK_POSITION=338",
    "LKWEEKS_OFFICIAL_CLASS=CARDINAL_WEEKS",
    "LKWEEKS_POSITION=305",
    "NWLKWK_OFFICIAL_CLASS=CARDINAL_WEEKS",
    "NWLKWK_POSITION=309",
    (
        "I_CARDINAL_REPAIR_FIELDS_AVAILABLE=PASS"
        if repair_candidates_pass
        else
        "I_CARDINAL_REPAIR_FIELDS_AVAILABLE=FAIL"
    ),
    "",
    "===== STATE =====",
    (
        "K_D_SCHEMA_READY_FOR_LATER_CONTRACT=1"
        if scf_schema_pass
        else
        "K_D_SCHEMA_READY_FOR_LATER_CONTRACT=0"
    ),
    "K_EMPIRICALLY_TESTED=0",
    "D_EMPIRICALLY_TESTED=0",
    "I_EMPIRICALLY_TESTED=0",
    "FIVE_DIMENSIONALITY_PROVEN=0",
    "K_D_I_ECONOMIC_OPEN_AUTHORIZED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "",
    (
        "E4A1_SCF_CPS_KDI_SCHEMA_AUDIT=PASS"
        if overall
        else
        "E4A1_SCF_CPS_KDI_SCHEMA_AUDIT=FAIL"
    ),
    (
        "E4A_R1_I_SEMANTIC_REPAIR_AUTHORIZED=1"
        if repair_authorized
        else
        "E4A_R1_I_SEMANTIC_REPAIR_AUTHORIZED=0"
    ),
    "",
]


AUDIT.write_text(
    "\n".join(lines),
    encoding="utf-8",
)


print(
    "\n".join(lines)
)


if not overall:
    raise RuntimeError(
        "E4A1 scientific schema/semantic audit FAIL"
    )
