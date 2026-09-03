from __future__ import annotations

import csv
import hashlib
import io
import json
import subprocess
import tempfile
import zipfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

CEX = ROOT / "data/raw/cex/2022/intrvw22.zip"
SCF_SUM = ROOT / "data/raw/scf/2022/scfp2022s.zip"

CPS_META = ROOT / "data/metadata/E3B1_cps_2022_variables.json"

OUT = ROOT / "data/metadata/E3B1_exact_component_schema_audit.txt"
TABLE = ROOT / "data/metadata/E3B1_candidate_variables.tsv"


EXPECTED_CEX_SHA = (
    "c99a2f47c0084b7a88812b34c56a1a288be2798ff010b2b59dcf87e072773e17"
)

EXPECTED_SCF_SUM_SHA = (
    "3bb4d890ae2463ff6039ec7692e375f544dd98a55a37ca2cb2340354b9cc9d80"
)

CPS_META_URL = (
    "https://api.census.gov/data/2022/cps/asec/mar/variables.json"
)


CEX_FMLI_REQUIRED = {
    "NEWID",
    "AGE_REF",
    "CUTENURE",
    "FINLWT21",
}

CEX_MTBI_REQUIRED = {
    "NEWID",
    "UCC",
    "COST",
    "REF_MO",
    "REF_YR",
}


CPS_GROUPS = {
    "RESOURCE": {
        "H_SEQ",
        "HSUP_WGT",
        "H_HHTYPE",
        "H_TENURE",
        "HTOTVAL",
    },
    "REFERENCE": {
        "PH_SEQ",
        "A_AGE",
        "A_EXPRRP",
    },
    "I_CURRENT": {
        "A_LFSR",
        "A_WKSTAT",
    },
    "I_PREVIOUS_YEAR": {
        "WORKYN",
        "WEWKRS",
        "WEUEMP",
        "WEXP",
        "WTEMP",
    },
}


SCF_GROUPS = {
    "CONTEXT": {
        "Y1",
        "YY1",
        "WGT",
        "AGE",
        "HOUSECL",
    },
    "K": {
        "ASSET",
        "FIN",
        "LIQ",
        "STOCKS",
        "RETQLIQ",
        "EQUITY",
        "HLIQ",
        "TURNDOWN",
        "FEARDENIAL",
    },
    "D": {
        "DEBT",
        "DEBT2INC",
        "PIRTOTAL",
        "PIRMORT",
        "MRTHEL",
        "LATE60",
    },
    "H_BALANCE_SHEET": {
        "HOUSES",
        "HOMEEQ",
        "NETWORTH",
    },
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()

    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)

    return h.hexdigest()


def acquire_cps_metadata() -> None:
    if CPS_META.exists():
        return

    tmp = Path(str(CPS_META) + ".part")

    if tmp.exists():
        tmp.unlink()

    subprocess.run(
        [
            "curl",
            "-L",
            "--fail",
            "--retry", "3",
            "--connect-timeout", "30",
            "--max-time", "300",
            CPS_META_URL,
            "-o", str(tmp),
        ],
        check=True,
    )

    # Structural JSON validation before promotion.
    obj = json.loads(
        tmp.read_text(encoding="utf-8")
    )

    if "variables" not in obj:
        raise RuntimeError(
            "Census metadata object lacks variables"
        )

    tmp.replace(CPS_META)


def first_csv_header(
    zf: zipfile.ZipFile,
    member: str,
) -> list[str]:

    with zf.open(member, "r") as raw:

        # Strictly first record only.
        line = raw.readline()

        if not line:
            raise RuntimeError(
                f"empty CSV member={member}"
            )

        decoded = line.decode(
            "utf-8-sig",
            errors="strict",
        ).rstrip("\r\n")

        return next(
            csv.reader([decoded])
        )


def find_single_dta(
    archive: Path,
    destination: Path,
) -> Path:

    with zipfile.ZipFile(archive) as zf:

        members = [
            name
            for name in zf.namelist()
            if Path(name).suffix.lower() == ".dta"
        ]

        if len(members) != 1:
            raise RuntimeError(
                f"{archive.name}: expected one DTA; "
                f"found={members}"
            )

        member = members[0]

        zf.extract(
            member,
            destination,
        )

        return destination / member


def stata_labels(path: Path) -> dict[str, str]:

    with path.open("rb") as fh:

        reader = pd.io.stata.StataReader(
            fh,
            convert_categoricals=False,
        )

        labels = reader.variable_labels()

    return {
        name.upper(): label
        for name, label in labels.items()
    }


# =============================================================================
# Frozen-input integrity
# =============================================================================

if sha256(CEX) != EXPECTED_CEX_SHA:
    raise RuntimeError(
        "CEX frozen SHA mismatch"
    )

if sha256(SCF_SUM) != EXPECTED_SCF_SUM_SHA:
    raise RuntimeError(
        "SCF summary frozen SHA mismatch"
    )


# =============================================================================
# CEX — header-only
# =============================================================================

cex_rows = []

with zipfile.ZipFile(CEX) as zf:

    fmli = sorted(
        name
        for name in zf.namelist()
        if Path(name).name.lower().startswith("fmli")
        and Path(name).suffix.lower() == ".csv"
    )

    mtbi = sorted(
        name
        for name in zf.namelist()
        if Path(name).name.lower().startswith("mtbi")
        and Path(name).suffix.lower() == ".csv"
    )

    if len(fmli) != 4:
        raise RuntimeError(
            f"expected 4 FMLI files; got={len(fmli)}"
        )

    if len(mtbi) != 4:
        raise RuntimeError(
            f"expected 4 MTBI files; got={len(mtbi)}"
        )

    for family, members, required in [
        ("FMLI", fmli, CEX_FMLI_REQUIRED),
        ("MTBI", mtbi, CEX_MTBI_REQUIRED),
    ]:

        for member in members:

            header = {
                x.upper()
                for x in first_csv_header(
                    zf,
                    member,
                )
            }

            for variable in sorted(required):

                cex_rows.append({
                    "source": "CEX",
                    "group": family,
                    "variable": variable,
                    "present": int(
                        variable in header
                    ),
                    "label": "HEADER_ONLY",
                })


# =============================================================================
# CPS — official metadata API only
# =============================================================================

acquire_cps_metadata()

cps_obj = json.loads(
    CPS_META.read_text(
        encoding="utf-8"
    )
)

cps_variables = cps_obj["variables"]

cps_rows = []

for group, variables in CPS_GROUPS.items():

    for variable in sorted(variables):

        meta = cps_variables.get(variable)

        cps_rows.append({
            "source": "CPS_ASEC",
            "group": group,
            "variable": variable,
            "present": int(
                meta is not None
            ),
            "label": (
                str(meta.get("label", ""))
                if meta
                else ""
            ),
        })


# =============================================================================
# SCF — Stata metadata only
# =============================================================================

scf_rows = []

with tempfile.TemporaryDirectory() as td:

    dta = find_single_dta(
        SCF_SUM,
        Path(td),
    )

    labels = stata_labels(dta)

    for group, variables in SCF_GROUPS.items():

        for variable in sorted(variables):

            scf_rows.append({
                "source": "SCF_SUMMARY",
                "group": group,
                "variable": variable,
                "present": int(
                    variable in labels
                ),
                "label": labels.get(
                    variable,
                    "",
                ),
            })


# =============================================================================
# Combined candidate table
# =============================================================================

rows = (
    cex_rows
    + cps_rows
    + scf_rows
)

TABLE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

with TABLE.open(
    "w",
    newline="",
    encoding="utf-8",
) as f:

    fields = [
        "source",
        "group",
        "variable",
        "present",
        "label",
    ]

    writer = csv.DictWriter(
        f,
        fieldnames=fields,
        delimiter="\t",
    )

    writer.writeheader()
    writer.writerows(rows)


# =============================================================================
# Gates
# =============================================================================

def pass_group(
    source: str,
    group: str,
) -> bool:

    selected = [
        r
        for r in rows
        if r["source"] == source
        and r["group"] == group
    ]

    return (
        bool(selected)
        and all(
            r["present"] == 1
            for r in selected
        )
    )


cex_fmli_pass = pass_group(
    "CEX",
    "FMLI",
)

cex_mtbi_pass = pass_group(
    "CEX",
    "MTBI",
)

cps_resource_pass = pass_group(
    "CPS_ASEC",
    "RESOURCE",
)

cps_reference_pass = pass_group(
    "CPS_ASEC",
    "REFERENCE",
)

cps_i_current_pass = pass_group(
    "CPS_ASEC",
    "I_CURRENT",
)

cps_i_prev_pass = pass_group(
    "CPS_ASEC",
    "I_PREVIOUS_YEAR",
)

scf_context_pass = pass_group(
    "SCF_SUMMARY",
    "CONTEXT",
)

scf_k_pass = pass_group(
    "SCF_SUMMARY",
    "K",
)

scf_d_pass = pass_group(
    "SCF_SUMMARY",
    "D",
)

scf_h_pass = pass_group(
    "SCF_SUMMARY",
    "H_BALANCE_SHEET",
)


overall = all([
    cex_fmli_pass,
    cex_mtbi_pass,
    cps_resource_pass,
    cps_reference_pass,
    cps_i_current_pass,
    cps_i_prev_pass,
    scf_context_pass,
    scf_k_pass,
    scf_d_pass,
    scf_h_pass,
])


summary = "\n".join([
    "=" * 100,
    "ECONOMIC GEOMETRY RESEARCH — E3B1 EXACT COMPONENT SCHEMA AUDIT",
    "=" * 100,
    "",
    "DATA_ROWS_PARSED=0",
    "ECONOMIC_VALUES_OPENED=0",
    "COHORT_ECONOMIC_ESTIMATES_CALCULATED=0",
    "REAL_INFLATION_ESTIMATED=0",
    "",
    "===== CEX =====",
    f"CEX_FMLI_CONTEXT_SCHEMA={'PASS' if cex_fmli_pass else 'FAIL'}",
    f"CEX_MTBI_EXPENDITURE_SCHEMA={'PASS' if cex_mtbi_pass else 'FAIL'}",
    "CEX_COST_VALUES_READ=0",
    "CEX_UCC_COMPONENT_MAPPING_FROZEN=0",
    "",
    "===== CPS ASEC =====",
    f"CPS_RESOURCE_CANDIDATE_SCHEMA={'PASS' if cps_resource_pass else 'FAIL'}",
    f"CPS_REFERENCE_SCHEMA={'PASS' if cps_reference_pass else 'FAIL'}",
    f"CPS_I_CURRENT_SCHEMA={'PASS' if cps_i_current_pass else 'FAIL'}",
    f"CPS_I_PREVIOUS_YEAR_SCHEMA={'PASS' if cps_i_prev_pass else 'FAIL'}",
    "CPS_RESOURCE_FORMULA_FROZEN=0",
    "CPS_VALUES_READ=0",
    "",
    "===== SCF =====",
    f"SCF_CONTEXT_SCHEMA={'PASS' if scf_context_pass else 'FAIL'}",
    f"SCF_K_CANDIDATE_SCHEMA={'PASS' if scf_k_pass else 'FAIL'}",
    f"SCF_D_CANDIDATE_SCHEMA={'PASS' if scf_d_pass else 'FAIL'}",
    f"SCF_H_BALANCE_SHEET_SCHEMA={'PASS' if scf_h_pass else 'FAIL'}",
    "SCF_OBSERVATIONS_READ=0",
    "SCF_COMPONENT_FORMULAS_FROZEN=0",
    "",
    "===== STATUS =====",
    "COMPONENT_WEIGHTS_SELECTED=0",
    "DIMENSIONALITY_SELECTED=0",
    "FINAL_REAL_INFLATION_SCALAR_AUTHORIZED=0",
    "",
    (
        "E3B1_EXACT_COMPONENT_SCHEMA_AUDIT=PASS"
        if overall
        else
        "E3B1_EXACT_COMPONENT_SCHEMA_AUDIT=FAIL"
    ),
    (
        "E3B2_COMPONENT_SEMANTIC_MAPPING_PRECOMMIT_AUTHORIZED=1"
        if overall
        else
        "E3B2_COMPONENT_SEMANTIC_MAPPING_PRECOMMIT_AUTHORIZED=0"
    ),
    "",
])


OUT.write_text(
    summary,
    encoding="utf-8",
)

print(summary)

if not overall:
    raise SystemExit(1)
