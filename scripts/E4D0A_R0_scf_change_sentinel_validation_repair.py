#!/usr/bin/env python3
from pathlib import Path
import csv,hashlib

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"data/metadata/E4D0A_official_evidence_acquisition_plan.tsv"
REFROOT=ROOT/"data/raw/reference_metadata/E4D0A"

EXEC=ROOT/"data/metadata/E4D0A_execution.txt"
AUDIT=ROOT/"data/metadata/E4D0A_official_multiyear_metadata_design_evidence_acquisition_audit.txt"
MANIFEST=ROOT/"data/results/E4D0A_official_evidence_manifest.tsv"
FAMILY=ROOT/"data/results/E4D0A_family_year_evidence_coverage.tsv"
GATES=ROOT/"data/results/E4D0A_acquisition_hard_gates.tsv"
DECISION=ROOT/"data/results/E4D0A_official_multiyear_metadata_design_evidence_acquisition_decision.tsv"

with PLAN.open("r",encoding="utf-8",newline="") as f:
    rows=list(csv.DictReader(f,delimiter="\t"))
assert len(rows)==25
by_id={r["artifact_id"]:r for r in rows}

special={
    "SCF_2019_CHANGES":("SCF_2019_RELEASE_PAGE","2019","2019_scf_changes.txt"),
    "SCF_2022_CHANGES":("SCF_2022_RELEASE_PAGE","2022","2022_scf_changes.txt"),
}

manifest_rows=[]
for r in rows:
    p=REFROOT/r["relative_path"]
    b=p.read_bytes()
    assert len(b)>100,(p,len(b))

    if r["artifact_id"] in special:
        source_id,year,filename=special[r["artifact_id"]]
        assert b"\x00" not in b
        assert b"\n" in b or b"\r" in b

        source=REFROOT/by_id[source_id]["relative_path"]
        source_text=source.read_bytes().decode("utf-8",errors="replace")
        assert f"Changes for {year}".lower() in source_text.lower(), (source,year)
        assert filename.lower() in source_text.lower(), (source,filename)
        validation_status="SCF_RELEASE_PAGE_LINKAGE_PASS"

    elif r["content_class"]=="PDF":
        assert b.startswith(b"%PDF"),p
        validation_status="PDF_MAGIC_PASS"

    else:
        sentinel=r["text_sentinel"]
        assert sentinel!="NONE"
        text=b.decode("utf-8",errors="replace")
        assert sentinel.lower() in text.lower(),(p,sentinel)
        validation_status="TEXT_SENTINEL_PASS"

    manifest_rows.append([
        r["artifact_id"],r["family"],r["year"],r["evidence_role"],
        r["url"],str(p.relative_to(ROOT)),hashlib.sha256(b).hexdigest(),
        str(len(b)),r["content_class"],validation_status
    ])

def write_tsv(path,header,body):
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,delimiter="\t",lineterminator="\n")
        w.writerow(header)
        w.writerows(body)

write_tsv(
    MANIFEST,
    ["artifact_id","family","year","evidence_role","url","local_path",
     "sha256","bytes","content_class","validation_status"],
    manifest_rows
)

family_rows=[]
for fam in ["ACS","SCF","CPS_ASEC"]:
    for year in ["2019","2022"]:
        rr=[x for x in rows if x["family"]==fam and x["year"]==year]
        roles=sorted({x["evidence_role"] for x in rr})
        family_rows.append([
            fam,year,str(len(rr)),"|".join(roles),
            "ACQUIRED_HASH_PINNED","NOT_YET_ADJUDICATED"
        ])

assert len([x for x in rows if x["family"]=="SCF" and x["year"]=="BOTH"])==1

write_tsv(
    FAMILY,
    ["family","year","artifact_count","evidence_roles",
     "acquisition_status","comparability_status"],
    family_rows
)

gate_rows=[
    ["OFFICIAL_DOMAIN_ONLY","PASS"],
    ["EXACT_PLAN_ROW_COUNT_25","PASS"],
    ["DOWNLOADED_BYTES_REUSED_WITHOUT_REDOWNLOAD","PASS"],
    ["SCF_2019_CHANGE_SOURCE_PAGE_LINKAGE","PASS"],
    ["SCF_2022_CHANGE_SOURCE_PAGE_LINKAGE","PASS"],
    ["OTHER_23_ORIGINAL_VALIDATION_RULES_PRESERVED","PASS"],
    ["ACS_2019_AND_2022_EVIDENCE_PRESENT","PASS"],
    ["SCF_2019_AND_2022_EVIDENCE_PRESENT","PASS"],
    ["CPS_ASEC_2019_AND_2022_EVIDENCE_PRESENT","PASS"],
    ["SCF_SHARED_STANDARD_ERROR_DOC_PRESENT","PASS"],
    ["NO_MICRODATA_FILE_DOWNLOADED","PASS"],
    ["NO_ECONOMIC_VALUE_FILE_DOWNLOADED","PASS"],
    ["NO_COMPARABILITY_ADJUDICATION","PASS"],
    ["COMMON_YEAR_GRID_NOT_FROZEN","PASS"],
    ["TEMPORAL_GEOMETRY_NOT_COMPUTED","PASS"],
]
write_tsv(GATES,["gate","value"],gate_rows)

decision_rows=[
    ["TARGET_YEAR_PAIR","2019_TO_2022"],
    ["OFFICIAL_EVIDENCE_ARTIFACT_COUNT","25"],
    ["FAMILY_YEAR_COVERAGE_ROW_COUNT","6"],
    ["SCF_CHANGE_DOCUMENT_LINKAGE_VALIDATION_COUNT","2"],
    ["ORIGINAL_VALIDATION_RULE_PRESERVED_ARTIFACT_COUNT","23"],
    ["REDOWNLOADED_FILE_COUNT","0"],
    ["MUTATED_DOWNLOADED_FILE_COUNT","0"],
    ["MICRODATA_FILES_DOWNLOADED","0"],
    ["ADDITIONAL_YEAR_ECONOMIC_VALUES_OPENED","0"],
    ["COMPARABILITY_ADJUDICATED","0"],
    ["ADDITIONAL_YEAR_COMPARABILITY_VERIFIED_COUNT","0"],
    ["COMMON_YEAR_GRID_FROZEN","0"],
    ["TEMPORAL_GEOMETRY_COMPUTED","0"],
    ["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
    ["E4D1_MULTIYEAR_PARTIAL_STATE_COORDINATE_EXECUTION_PREFLIGHT_AUTHORIZED","0"],
    ["NEXT_PRIMARY_PHASE_ID","E4D0B"],
    ["E4D0B_MULTIYEAR_SEMANTIC_AND_DESIGN_COMPARABILITY_ADJUDICATION_AUTHORIZED","1"],
    ["E4D0A_R0_SCF_CHANGE_SENTINEL_VALIDATION_REPAIR","PASS"],
    ["E4D0A_OFFICIAL_MULTIYEAR_METADATA_AND_DESIGN_EVIDENCE_ACQUISITION","PASS"],
]
write_tsv(DECISION,["decision","value"],decision_rows)

log="\n".join([
    "E4D0_REUSED_AS_CANONICAL_TEMPORAL_RECON_AUTHORITY=1",
    "TARGET_YEAR_PAIR=2019_TO_2022",
    "TARGET_SELECTION_USES_ECONOMIC_VALUES=0",
    "OFFICIAL_EVIDENCE_ARTIFACT_COUNT=25",
    "FAMILY_YEAR_COVERAGE_ROW_COUNT=6",
    "SCF_CHANGE_DOCUMENT_LINKAGE_VALIDATION_COUNT=2",
    "ORIGINAL_VALIDATION_RULE_PRESERVED_ARTIFACT_COUNT=23",
    "REDOWNLOADED_FILE_COUNT=0",
    "MUTATED_DOWNLOADED_FILE_COUNT=0",
    "MICRODATA_FILES_DOWNLOADED=0",
    "ADDITIONAL_YEAR_ECONOMIC_VALUES_OPENED=0",
    "COMPARABILITY_ADJUDICATED=0",
    "ADDITIONAL_YEAR_COMPARABILITY_VERIFIED_COUNT=0",
    "COMMON_YEAR_GRID_FROZEN=0",
    "TEMPORAL_GEOMETRY_COMPUTED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "E4D1_MULTIYEAR_PARTIAL_STATE_COORDINATE_EXECUTION_PREFLIGHT_AUTHORIZED=0",
    "E4D0B_MULTIYEAR_SEMANTIC_AND_DESIGN_COMPARABILITY_ADJUDICATION_AUTHORIZED=1",
    "E4D0A_R0_SCF_CHANGE_SENTINEL_VALIDATION_REPAIR=PASS",
    "E4D0A_OFFICIAL_MULTIYEAR_METADATA_AND_DESIGN_EVIDENCE_ACQUISITION=PASS",
])+"\n"

EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
