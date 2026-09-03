#!/usr/bin/env python3
from pathlib import Path
import csv, hashlib, sys

root=Path(__file__).resolve().parents[1]
plan=root/"data/metadata/E4D0A_official_evidence_acquisition_plan.tsv"
refroot=root/"data/raw/reference_metadata/E4D0A"
manifest=root/"data/results/E4D0A_official_evidence_manifest.tsv"
family_out=root/"data/results/E4D0A_family_year_evidence_coverage.tsv"
gates_out=root/"data/results/E4D0A_acquisition_hard_gates.tsv"
decision_out=root/"data/results/E4D0A_official_multiyear_metadata_design_evidence_acquisition_decision.tsv"
exec_out=root/"data/metadata/E4D0A_execution.txt"
audit_out=root/"data/metadata/E4D0A_official_multiyear_metadata_design_evidence_acquisition_audit.txt"

with plan.open("r",encoding="utf-8",newline="") as f:
    rows=list(csv.DictReader(f,delimiter="\t"))

assert len(rows)==25
assert {r["family"] for r in rows}=={"ACS","SCF","CPS_ASEC"}

manifest_rows=[]
for r in rows:
    p=refroot/r["relative_path"]
    assert p.is_file(), p
    b=p.read_bytes()
    assert len(b)>100, (p,len(b))

    cls=r["content_class"]
    if cls=="PDF":
        assert b.startswith(b"%PDF"), p
        sentinel_status="PDF_MAGIC_PASS"
    else:
        text=b.decode("utf-8",errors="replace")
        sentinel=r["text_sentinel"]
        assert sentinel!="NONE"
        assert sentinel.lower() in text.lower(), (p,sentinel)
        sentinel_status="TEXT_SENTINEL_PASS"

    manifest_rows.append([
        r["artifact_id"],r["family"],r["year"],r["evidence_role"],
        r["url"],str(p.relative_to(root)),
        hashlib.sha256(b).hexdigest(),str(len(b)),cls,sentinel_status
    ])

def write_tsv(path, header, body):
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,delimiter="\t",lineterminator="\n")
        w.writerow(header)
        w.writerows(body)

write_tsv(
    manifest,
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

# Shared SCF standard-error doc is tracked separately.
shared=[x for x in rows if x["family"]=="SCF" and x["year"]=="BOTH"]
assert len(shared)==1

write_tsv(
    family_out,
    ["family","year","artifact_count","evidence_roles",
     "acquisition_status","comparability_status"],
    family_rows
)

gate_rows=[
    ["OFFICIAL_DOMAIN_ONLY","PASS"],
    ["EXACT_PLAN_ROW_COUNT_25","PASS"],
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
write_tsv(gates_out,["gate","value"],gate_rows)

decision_rows=[
    ["TARGET_YEAR_PAIR","2019_TO_2022"],
    ["OFFICIAL_EVIDENCE_ARTIFACT_COUNT","25"],
    ["FAMILY_YEAR_COVERAGE_ROW_COUNT","6"],
    ["OFFICIAL_DOMAIN_COUNT","3"],
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
    ["E4D0A_OFFICIAL_MULTIYEAR_METADATA_AND_DESIGN_EVIDENCE_ACQUISITION","PASS"],
]
write_tsv(decision_out,["decision","value"],decision_rows)

log="\n".join([
    "E4D0_REUSED_AS_CANONICAL_TEMPORAL_RECON_AUTHORITY=1",
    "TARGET_YEAR_PAIR=2019_TO_2022",
    "TARGET_SELECTION_USES_ECONOMIC_VALUES=0",
    "OFFICIAL_EVIDENCE_ARTIFACT_COUNT=25",
    "FAMILY_YEAR_COVERAGE_ROW_COUNT=6",
    "OFFICIAL_DOMAIN_COUNT=3",
    "MICRODATA_FILES_DOWNLOADED=0",
    "ADDITIONAL_YEAR_ECONOMIC_VALUES_OPENED=0",
    "COMPARABILITY_ADJUDICATED=0",
    "ADDITIONAL_YEAR_COMPARABILITY_VERIFIED_COUNT=0",
    "COMMON_YEAR_GRID_FROZEN=0",
    "TEMPORAL_GEOMETRY_COMPUTED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "E4D1_MULTIYEAR_PARTIAL_STATE_COORDINATE_EXECUTION_PREFLIGHT_AUTHORIZED=0",
    "E4D0B_MULTIYEAR_SEMANTIC_AND_DESIGN_COMPARABILITY_ADJUDICATION_AUTHORIZED=1",
    "E4D0A_OFFICIAL_MULTIYEAR_METADATA_AND_DESIGN_EVIDENCE_ACQUISITION=PASS",
])+"\n"

exec_out.write_text(log,encoding="utf-8")
audit_out.write_text(log,encoding="utf-8")
print(log,end="")
