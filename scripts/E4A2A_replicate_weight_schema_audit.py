from __future__ import annotations

import hashlib
import json
import re
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

UPSTREAM = (
    ROOT
    / "data/metadata/E4A2_kdi_estimator_preflight_audit.txt"
)

UPSTREAM_CONTRACT = (
    ROOT
    / "data/metadata/E4A2_kdi_estimator_contract.json"
)

ACQ_CONTRACT = (
    ROOT
    / "data/metadata/E4A2A_replicate_weight_acquisition_contract.json"
)


SCF_REP = (
    ROOT
    / "data/raw/scf/2022/scf2022rw1s.zip"
)

SCF_CODEBOOK = (
    ROOT
    / "data/raw/scf/2022/codebk2022.txt"
)


CPS_REP = (
    ROOT
    / "data/raw/cps_asec/2022/CPS_ASEC_ASCII_REPWGT_2022.ZIP"
)

CPS_SAS = (
    ROOT
    / "data/raw/cps_asec/2022/CPS_ASEC_ASCII_REPWGT_2022.SAS"
)

CPS_DOCX = (
    ROOT
    / "data/raw/cps_asec/2022/2022_ASEC_Replicate_Weight_Usage_Instructions.docx"
)

CPS_PERSON = (
    ROOT
    / "data/raw/cps_asec/2022/persfmt.txt"
)

CPS_HOUSE = (
    ROOT
    / "data/raw/cps_asec/2022/hhldfmt.txt"
)


HASH_OUT = (
    ROOT
    / "data/metadata/E4A2A_official_acquisition_hashes.tsv"
)

SCHEMA_OUT = (
    ROOT
    / "data/metadata/E4A2A_replicate_weight_schema.tsv"
)

AUDIT = (
    ROOT
    / "data/metadata/E4A2A_replicate_weight_schema_audit.txt"
)


EXPECTED_SHA = {
    UPSTREAM:
        "9998c60b281874d15be0c01578abd7a5bb39a05f27b4d2971d7244987fbba24c",

    UPSTREAM_CONTRACT:
        "40c85c629285e7cf0999250914d7928b9825047682bf41362327060adaef4f0a"
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


for path, expected in EXPECTED_SHA.items():

    actual = sha256(path)

    if actual != expected:

        raise RuntimeError(
            f"SHA mismatch {path}: {actual}"
        )


for path in (
    SCF_REP,
    SCF_CODEBOOK,
    CPS_REP,
    CPS_SAS,
    CPS_DOCX,
    CPS_PERSON,
    CPS_HOUSE,
):

    if not path.is_file():

        raise RuntimeError(
            f"missing acquired official file={path}"
        )


# =============================================================================
# Upstream
# =============================================================================

text = UPSTREAM.read_text(
    encoding="utf-8"
)

for token in (
    "E4A2_KDI_ESTIMATOR_PREFLIGHT=PASS",
    "E4A2A_REPLICATE_WEIGHT_ACQUISITION_SCHEMA_AUDIT_AUTHORIZED=1",
    "SCF_BOOTSTRAP_REPLICATES_REQUIRED=999",
    "CPS_REPLICATE_COUNT=160",
):

    if token not in text:

        raise RuntimeError(
            f"missing upstream invariant={token}"
        )


contract = json.loads(
    ACQ_CONTRACT.read_text(
        encoding="utf-8"
    )
)


# =============================================================================
# ZIP integrity
# =============================================================================

def zip_integrity(
    path: Path,
) -> tuple[
    bool,
    list[str],
]:

    try:

        with zipfile.ZipFile(path) as zf:

            members = zf.namelist()

            bad = zf.testzip()

        return (
            bad is None,
            members,
        )

    except Exception:

        return (
            False,
            [],
        )


scf_zip_pass, scf_members = zip_integrity(
    SCF_REP
)

cps_zip_pass, cps_members = zip_integrity(
    CPS_REP
)


# =============================================================================
# SCF Stata METADATA ONLY
# =============================================================================

scf_dta_members = [
    x
    for x in scf_members
    if x.lower().endswith(
        ".dta"
    )
]


scf_member_pass = (
    len(
        scf_dta_members
    ) == 1
)


scf_columns: list[str] = []


if (
    scf_zip_pass
    and scf_member_pass
):

    with zipfile.ZipFile(
        SCF_REP
    ) as zf:

        with tempfile.TemporaryDirectory() as td:

            member = scf_dta_members[0]

            out = (
                Path(td)
                / Path(member).name
            )

            with zf.open(
                member
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

                labels = (
                    reader
                    .variable_labels()
                )

                scf_columns = [
                    str(x).upper()
                    for x in labels.keys()
                ]

            finally:

                try:
                    reader.close()
                except Exception:
                    pass


scf_set = set(
    scf_columns
)


expected_wt = {
    f"WT1B{i}"
    for i in range(
        1,
        1000,
    )
}

expected_mm = {
    f"MM{i}"
    for i in range(
        1,
        1000,
    )
}

expected_scf = {
    "Y1",
    "YY1",
    *expected_wt,
    *expected_mm,
}


scf_y1_pass = (
    "Y1" in scf_set
)

scf_yy1_pass = (
    "YY1" in scf_set
)

scf_wt_pass = (
    expected_wt
    <= scf_set
    and len(
        [
            x
            for x in scf_set
            if re.fullmatch(
                r"WT1B\d+",
                x,
            )
        ]
    ) == 999
)

scf_mm_pass = (
    expected_mm
    <= scf_set
    and len(
        [
            x
            for x in scf_set
            if re.fullmatch(
                r"MM\d+",
                x,
            )
        ]
    ) == 999
)


scf_exact_schema_pass = (
    scf_set
    == expected_scf
)


# =============================================================================
# SCF official codebook contract
# =============================================================================

codebook = SCF_CODEBOOK.read_text(
    encoding="utf-8",
    errors="replace",
)


scf_codebook_exact_anchors_pass = all(
    token in codebook
    for token in (
        "WT1B1-WT1B999",
        "MM1-MM999",
        "xxx.rep_wgts(KEEP=Y1",
        "WGTS{I}=MAX(0,MULT{I})*MAX(0,RWGT{I})",
    )
)

scf_codebook_first_implicate_pass = (
    re.search(
        r"Replicate\s+weights\s+were\s+computed\s+only\s+for\s+the\s+first\s+implicate",
        codebook,
    )
    is not None
)

scf_codebook_pass = all([
    scf_codebook_exact_anchors_pass,
    scf_codebook_first_implicate_pass,
])


# =============================================================================
# CPS archive member
# =============================================================================

cps_dat_members = [
    x
    for x in cps_members
    if (
        Path(x)
        .name
        .upper()
        ==
        "CPS_ASEC_ASCII_REPWGT_2022.DAT"
    )
]


cps_member_pass = (
    len(
        cps_dat_members
    ) == 1
)


# =============================================================================
# CPS official SAS layout — TEXT ONLY
# =============================================================================

sas = CPS_SAS.read_text(
    encoding="utf-8",
    errors="replace",
)


lrecl_match = re.search(
    r"lrecl\s*=\s*(\d+)",
    sas,
    flags=re.I,
)


cps_lrecl = (
    int(
        lrecl_match.group(1)
    )
    if lrecl_match
    else None
)


weight_matches = re.findall(
    r"@(\d+)\s+pwwgt(\d+)\s+f9\.4",
    sas,
    flags=re.I,
)


weight_positions = {
    int(idx):
        int(pos)
    for pos, idx
    in weight_matches
}


expected_weight_positions = {
    i:
        1 + 9 * i
    for i in range(
        0,
        161,
    )
}


cps_weight_layout_pass = (
    weight_positions
    == expected_weight_positions
)


hseq_pass = bool(
    re.search(
        r"@1450\s+h_seq\s+f5\.0",
        sas,
        flags=re.I,
    )
)


pppos_pass = bool(
    re.search(
        r"@1455\s+pppos\s+\$char2\.",
        sas,
        flags=re.I,
    )
)


cps_sas_layout_pass = all([
    cps_lrecl == 1456,
    cps_weight_layout_pass,
    hseq_pass,
    pppos_pass,
])


# =============================================================================
# CPS DOCX usage instructions — DOCUMENT TEXT ONLY
# =============================================================================

def docx_text(
    path: Path,
) -> str:

    with zipfile.ZipFile(
        path
    ) as zf:

        xml = zf.read(
            "word/document.xml"
        )

    root = ET.fromstring(
        xml
    )

    ns = {
        "w":
            "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    }

    parts = [
        node.text or ""
        for node in root.findall(
            ".//w:t",
            ns,
        )
    ]

    return " ".join(
        parts
    )


cps_instruction_text = docx_text(
    CPS_DOCX
)


instruction_low = (
    cps_instruction_text
    .lower()
)


cps_instruction_pass = all(
    token in instruction_low
    for token in (
        "h_seq",
        "pppos",
        "replicate",
        "160",
        "reference person",
        "household",
    )
)


cps_pwwgt0_marsupwt_doc_pass = all(
    token in instruction_low
    for token in (
        "pwwgt0",
        "marsupwt",
    )
)


# =============================================================================
# CPS official person / household layouts
# =============================================================================

person = CPS_PERSON.read_text(
    encoding="utf-8",
    errors="replace",
)

house = CPS_HOUSE.read_text(
    encoding="utf-8",
    errors="replace",
)


def layout_line(
    text: str,
    variable: str,
    length: int,
    position: int,
) -> bool:

    pattern = (
        rf"(?m)^\s*"
        rf"{re.escape(variable)}"
        rf"\s+{length}"
        rf"\s+{position}"
        rf"\b"
    )

    return bool(
        re.search(
            pattern,
            text,
            flags=re.I,
        )
    )


cps_person_layout_pass = all([
    layout_line(
        person,
        "PH_SEQ",
        5,
        36,
    ),
    layout_line(
        person,
        "PPPOS",
        2,
        43,
    ),
    layout_line(
        person,
        "MARSUPWT",
        8,
        71,
    ),
    layout_line(
        person,
        "A_EXPRRP",
        2,
        82,
    ),
])


cps_house_layout_pass = all([
    layout_line(
        house,
        "H_SEQ",
        5,
        29,
    ),
    layout_line(
        house,
        "HSUP_WGT",
        8,
        34,
    ),
    layout_line(
        house,
        "H_HHTYPE",
        1,
        61,
    ),
    layout_line(
        house,
        "H_TENURE",
        1,
        89,
    ),
])


cps_merge_schema_pass = all([
    cps_instruction_pass,
    cps_person_layout_pass,
    cps_house_layout_pass,
    hseq_pass,
    pppos_pass,
])


# =============================================================================
# Immutable acquisition hashes
# =============================================================================

hash_rows = []


for path in (
    SCF_REP,
    SCF_CODEBOOK,
    CPS_REP,
    CPS_SAS,
    CPS_DOCX,
    CPS_PERSON,
    CPS_HOUSE,
):

    hash_rows.append({
        "artifact":
            str(
                path.relative_to(
                    ROOT
                )
            ),
        "bytes":
            path.stat().st_size,
        "sha256":
            sha256(
                path
            ),
    })


pd.DataFrame(
    hash_rows
).to_csv(
    HASH_OUT,
    sep="\t",
    index=False,
)


# =============================================================================
# Schema output
# =============================================================================

schema_rows = [
    {
        "source":
            "SCF_REPLICATE",
        "item":
            "STATA_MEMBER",
        "observed":
            (
                scf_dta_members[0]
                if len(
                    scf_dta_members
                ) == 1
                else
                "|".join(
                    scf_dta_members
                )
            ),
        "gate":
            (
                "PASS"
                if scf_member_pass
                else "FAIL"
            ),
    },
    {
        "source":
            "SCF_REPLICATE",
        "item":
            "YY1_CASE_ID",
        "observed":
            (
                "PRESENT"
                if scf_yy1_pass
                else "ABSENT"
            ),
        "gate":
            (
                "PASS"
                if scf_yy1_pass
                else "FAIL"
            ),
    },
    {
        "source":
            "SCF_REPLICATE",
        "item":
            "VARIABLE_COUNT",
        "observed":
            str(
                len(
                    scf_columns
                )
            ),
        "gate":
            (
                "PASS"
                if scf_exact_schema_pass
                else "FAIL"
            ),
    },
    {
        "source":
            "SCF_REPLICATE",
        "item":
            "WT1B_COUNT",
        "observed":
            str(
                len(
                    expected_wt
                    & scf_set
                )
            ),
        "gate":
            (
                "PASS"
                if scf_wt_pass
                else "FAIL"
            ),
    },
    {
        "source":
            "SCF_REPLICATE",
        "item":
            "MM_COUNT",
        "observed":
            str(
                len(
                    expected_mm
                    & scf_set
                )
            ),
        "gate":
            (
                "PASS"
                if scf_mm_pass
                else "FAIL"
            ),
    },
    {
        "source":
            "CPS_REPLICATE",
        "item":
            "ASCII_MEMBER",
        "observed":
            (
                cps_dat_members[0]
                if len(
                    cps_dat_members
                ) == 1
                else
                "|".join(
                    cps_dat_members
                )
            ),
        "gate":
            (
                "PASS"
                if cps_member_pass
                else "FAIL"
            ),
    },
    {
        "source":
            "CPS_REPLICATE",
        "item":
            "LRECL",
        "observed":
            str(
                cps_lrecl
            ),
        "gate":
            (
                "PASS"
                if cps_lrecl == 1456
                else "FAIL"
            ),
    },
    {
        "source":
            "CPS_REPLICATE",
        "item":
            "PWWGT_FIELD_COUNT",
        "observed":
            str(
                len(
                    weight_positions
                )
            ),
        "gate":
            (
                "PASS"
                if cps_weight_layout_pass
                else "FAIL"
            ),
    },
    {
        "source":
            "CPS_REPLICATE",
        "item":
            "MERGE_KEYS",
        "observed":
            "H_SEQ,PPPOS",
        "gate":
            (
                "PASS"
                if (
                    hseq_pass
                    and pppos_pass
                )
                else "FAIL"
            ),
    },
]


pd.DataFrame(
    schema_rows
).to_csv(
    SCHEMA_OUT,
    sep="\t",
    index=False,
)


# =============================================================================
# Classification
# =============================================================================

scf_pass = all([
    scf_zip_pass,
    scf_member_pass,
    scf_y1_pass,
    scf_yy1_pass,
    scf_wt_pass,
    scf_mm_pass,
    scf_exact_schema_pass,
    scf_codebook_pass,
])


cps_pass = all([
    cps_zip_pass,
    cps_member_pass,
    cps_sas_layout_pass,
    cps_instruction_pass,
    cps_pwwgt0_marsupwt_doc_pass,
    cps_person_layout_pass,
    cps_house_layout_pass,
    cps_merge_schema_pass,
])


overall = (
    scf_pass
    and cps_pass
)


lines = [
    "=" * 100,
    "E4A2A — OFFICIAL REPLICATE-WEIGHT ACQUISITION + SCHEMA AUDIT",
    "=" * 100,
    "",
    "SCF_K_D_VALUES_READ=0",
    "CPS_I_VALUES_READ=0",
    "SCF_REPLICATE_WEIGHT_VALUES_PARSED=0",
    "CPS_REPLICATE_WEIGHT_VALUES_PARSED=0",
    "DIMENSIONALITY_OUTCOMES_OPENED=0",
    "",
    "===== ACQUISITION =====",
    "SCF_REPLICATE_SOURCE=FEDERAL_RESERVE",
    "SCF_CODEBOOK_SOURCE=FEDERAL_RESERVE",
    "CPS_REPLICATE_SOURCE=CENSUS_BUREAU",
    "CPS_LAYOUT_SOURCE=CENSUS_BUREAU",
    "CPS_INSTRUCTION_SOURCE=CENSUS_BUREAU",
    "",
    (
        "SCF_REPLICATE_ZIP_INTEGRITY=PASS"
        if scf_zip_pass
        else
        "SCF_REPLICATE_ZIP_INTEGRITY=FAIL"
    ),
    (
        "CPS_REPLICATE_ZIP_INTEGRITY=PASS"
        if cps_zip_pass
        else
        "CPS_REPLICATE_ZIP_INTEGRITY=FAIL"
    ),
    "",
    "===== SCF REPLICATE SCHEMA =====",
    f"SCF_STATA_MEMBER_COUNT={len(scf_dta_members)}",
    (
        "SCF_STATA_MEMBER="
        + (
            scf_dta_members[0]
            if len(
                scf_dta_members
            ) == 1
            else "UNRESOLVED"
        )
    ),
    f"SCF_REPLICATE_VARIABLE_COUNT={len(scf_columns)}",
    (
        "SCF_Y1_KEY=PASS"
        if scf_y1_pass
        else
        "SCF_Y1_KEY=FAIL"
    ),
    (
        "SCF_YY1_CASE_ID=PASS"
        if scf_yy1_pass
        else
        "SCF_YY1_CASE_ID=FAIL"
    ),
    f"SCF_WT1B_COUNT={len(expected_wt & scf_set)}",
    f"SCF_MM_COUNT={len(expected_mm & scf_set)}",
    (
        "SCF_WT1B_1_TO_999=PASS"
        if scf_wt_pass
        else
        "SCF_WT1B_1_TO_999=FAIL"
    ),
    (
        "SCF_MM_1_TO_999=PASS"
        if scf_mm_pass
        else
        "SCF_MM_1_TO_999=FAIL"
    ),
    (
        "SCF_EXACT_REPLICATE_SCHEMA=PASS"
        if scf_exact_schema_pass
        else
        "SCF_EXACT_REPLICATE_SCHEMA=FAIL"
    ),
    (
        "SCF_OFFICIAL_CODEBOOK_REPLICATE_CONTRACT=PASS"
        if scf_codebook_pass
        else
        "SCF_OFFICIAL_CODEBOOK_REPLICATE_CONTRACT=FAIL"
    ),
    "SCF_EFFECTIVE_REPLICATE_WEIGHT=MAX_0_WT1B_R_X_MAX_0_MM_R",
    "SCF_REPLICATE_MERGE_KEY=Y1",
    "",
    "===== CPS REPLICATE SCHEMA =====",
    f"CPS_ASCII_MEMBER_COUNT={len(cps_dat_members)}",
    (
        "CPS_ASCII_MEMBER="
        + (
            cps_dat_members[0]
            if len(
                cps_dat_members
            ) == 1
            else "UNRESOLVED"
        )
    ),
    f"CPS_RECORD_LENGTH={cps_lrecl}",
    f"CPS_PWWGT_FIELD_COUNT={len(weight_positions)}",
    "CPS_FULL_REPLICATE_FILE_WEIGHT=PWWGT0",
    "CPS_REPLICATE_WEIGHTS=PWWGT1_PWWGT160",
    "CPS_REPLICATE_COUNT=160",
    "CPS_REPLICATE_KEYS=H_SEQ,PPPOS",
    (
        "CPS_OFFICIAL_SAS_LAYOUT=PASS"
        if cps_sas_layout_pass
        else
        "CPS_OFFICIAL_SAS_LAYOUT=FAIL"
    ),
    (
        "CPS_USAGE_INSTRUCTION_SCHEMA=PASS"
        if cps_instruction_pass
        else
        "CPS_USAGE_INSTRUCTION_SCHEMA=FAIL"
    ),
    (
        "CPS_PWWGT0_MARSUPWT_DOCUMENTATION=PASS"
        if cps_pwwgt0_marsupwt_doc_pass
        else
        "CPS_PWWGT0_MARSUPWT_DOCUMENTATION=FAIL"
    ),
    "",
    "===== CPS MAIN-DATA MERGE SCHEMA =====",
    "CPS_PERSON_HOUSE_KEY=PH_SEQ",
    "CPS_PERSON_REPLICATE_POSITION_KEY=PPPOS",
    "CPS_PERSON_POINT_WEIGHT=MARSUPWT",
    "CPS_HOUSE_KEY=H_SEQ",
    "CPS_HOUSE_POINT_WEIGHT=HSUP_WGT",
    (
        "CPS_PERSON_LAYOUT=PASS"
        if cps_person_layout_pass
        else
        "CPS_PERSON_LAYOUT=FAIL"
    ),
    (
        "CPS_HOUSEHOLD_LAYOUT=PASS"
        if cps_house_layout_pass
        else
        "CPS_HOUSEHOLD_LAYOUT=FAIL"
    ),
    (
        "CPS_REPLICATE_MERGE_SCHEMA=PASS"
        if cps_merge_schema_pass
        else
        "CPS_REPLICATE_MERGE_SCHEMA=FAIL"
    ),
    "",
    "===== FULL-WEIGHT BRIDGE =====",
    "CPS_E4A2_POINT_WEIGHT=HSUP_WGT",
    "CPS_REPLICATE_BASE_WEIGHT=PWWGT0",
    "CPS_PWWGT0_DOCUMENTED_COUNTERPART=MARSUPWT",
    "CPS_HOUSEHOLD_FULL_WEIGHT_BRIDGE=PENDING",
    "CPS_WEIGHT_VALUE_IDENTITY_TEST_PERFORMED=0",
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
        "E4A2A_REPLICATE_WEIGHT_ACQUISITION_SCHEMA_AUDIT=PASS"
        if overall
        else
        "E4A2A_REPLICATE_WEIGHT_ACQUISITION_SCHEMA_AUDIT=FAIL"
    ),
    (
        "E4A2B_WEIGHT_BRIDGE_AUDIT_AUTHORIZED=1"
        if overall
        else
        "E4A2B_WEIGHT_BRIDGE_AUDIT_AUTHORIZED=0"
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
    raise SystemExit(1)
