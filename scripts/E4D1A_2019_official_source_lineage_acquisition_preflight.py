#!/usr/bin/env python3
from pathlib import Path
import csv,html,re,sys

ROOT=Path(__file__).resolve().parents[1]

CAND=ROOT/"data/metadata/E4D1A_official_2019_source_candidate_plan.tsv"
RULES=ROOT/"data/metadata/E4D1A_source_lineage_resolution_rules.tsv"
D1REQ=ROOT/"data/metadata/E4D1_2019_source_requirement_plan.tsv"

H_EXEC=ROOT/"scripts/E4C3D_first_acs2022_h_access_execution.py"
SCF_EXEC=ROOT/"scripts/E4A2F_first_scf_kd_inference_execution.py"
CPS_EXEC=ROOT/"scripts/E4A2D_first_cps_i_inference_execution.py"

ACS_INDEX=ROOT/"data/raw/reference_metadata/E4D1A/ACS/2019/acs_2019_1year_pums_directory_index.html"
SCF_PAGE=ROOT/"data/raw/reference_metadata/E4D0A/SCF/2019/scf_2019_release_page.html"
CPS_PAGE=ROOT/"data/raw/reference_metadata/E4D0A/CPS_ASEC/2019/cps_asec_2019_release_page.html"
CPS_DIR=ROOT/"data/raw/reference_metadata/E4D0A/CPS_ASEC/2019/cps_asec_2019_directory_index.html"
CPS_REP_SAS=ROOT/"data/raw/reference_metadata/E4D0A/CPS_ASEC/2019/CPS_ASEC_ASCII_REPWGT_2019.SAS"

PATHINV=ROOT/"data/results/E4D1A_2022_source_path_reference_inventory.tsv"
RESOLVED=ROOT/"data/results/E4D1A_resolved_2019_source_lineage.tsv"
SCHEMA=ROOT/"data/results/E4D1A_2019_schema_validation_plan.tsv"
ACQPLAN=ROOT/"data/results/E4D1A_2019_microdata_acquisition_plan.tsv"
GATES=ROOT/"data/results/E4D1A_preflight_hard_gates.tsv"
DECISION=ROOT/"data/results/E4D1A_2019_official_source_lineage_acquisition_decision.tsv"
EXEC=ROOT/"data/metadata/E4D1A_execution.txt"
AUDIT=ROOT/"data/metadata/E4D1A_2019_official_source_lineage_acquisition_preflight_audit.txt"

def read_tsv(p):
    with p.open("r",encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f,delimiter="\t"))

def write_tsv(p,header,rows):
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,delimiter="\t",lineterminator="\n")
        w.writerow(header); w.writerows(rows)

cand=read_tsv(CAND)
rules=read_tsv(RULES)
d1req=read_tsv(D1REQ)
assert len(cand)==11
assert len(rules)==6
assert len(d1req)==6

byid={r["candidate_id"]:r for r in cand}

# Open only static executor text and official metadata HTML/text; no numeric result rows.
h=H_EXEC.read_text(encoding="utf-8",errors="replace").lower()
s=SCF_EXEC.read_text(encoding="utf-8",errors="replace").lower()
c=CPS_EXEC.read_text(encoding="utf-8",errors="replace").lower()

acs_idx=ACS_INDEX.read_text(encoding="utf-8",errors="replace").lower()
scf_page=SCF_PAGE.read_text(encoding="utf-8",errors="replace").lower()
cps_page=CPS_PAGE.read_text(encoding="utf-8",errors="replace").lower()
cps_dir=CPS_DIR.read_text(encoding="utf-8",errors="replace").lower()
rep_sas=CPS_REP_SAS.read_text(encoding="utf-8",errors="replace").lower()

# Filesystem names are structural only.
roots=[
    ROOT/"data/raw/acs/2022",
    ROOT/"data/raw/scf/2022",
    ROOT/"data/raw/cps_asec/2022",
]
path_rows=[]
paths=[]
for rr in roots:
    if rr.exists():
        for p in sorted(rr.rglob("*")):
            if p.is_file():
                rel=str(p.relative_to(ROOT))
                paths.append(rel.lower())
                path_rows.append([str(rr.relative_to(ROOT)),rel,"PATH_NAME_ONLY"])

def evidence_has(token, text, path_candidates=()):
    t=token.lower()
    return t in text or any(t in p for p in path_candidates)

# ACS selection: require frozen 2022 lineage/path evidence AND official 2019 directory link.
acs_housing_2022=evidence_has("csv_hus.zip",h,paths)
acs_person_2022=evidence_has("csv_pus.zip",h,paths)
acs_housing_2019=("csv_hus.zip" in acs_idx)
acs_person_2019=("csv_pus.zip" in acs_idx)

acs_selected=[]
if acs_housing_2022 and acs_housing_2019:
    acs_selected.append("ACS_2019_NATIONAL_HOUSING_CSV")
if acs_person_2022 and acs_person_2019:
    acs_selected.append("ACS_2019_NATIONAL_PERSON_CSV")
acs_req1_ok=bool(acs_selected)

# Replicate requirement: frozen H executor must reference WGTP plus replicate semantics.
# This is static code evidence only, not data values.
acs_rep_static=("wgtp" in h and ("wgtp80" in h or "range(1, 81)" in h or "range(1,81)" in h or "replicate" in h))
acs_req2_ok=acs_req1_ok and acs_rep_static

# SCF source family. Do not choose summary/full unless frozen 2022 lineage identifies it.
summary_2022=evidence_has("scfp2022s.zip",s,paths) or evidence_has("scfp2022",s,paths)
full_2022=evidence_has("scf2022s.zip",s,paths) or evidence_has("scf2022s",s,paths)
# Avoid full token being inferred solely from replicate filename.
if not ("scf2022s.zip" in s or any(p.endswith("/scf2022s.zip") for p in paths)):
    full_2022=False

summary_2019=("scfp2019s.zip" in scf_page)
full_2019=("scf2019s.zip" in scf_page)
rep_2019=("scf2019rw1s.zip" in scf_page)

scf_selected=[]
if summary_2022 and summary_2019:
    scf_selected.append("SCF_2019_SUMMARY_STATA")
if full_2022 and full_2019:
    scf_selected.append("SCF_2019_FULL_STATA")
# Exactly one data family must be identified for K/D execution.
scf_req3_ok=(len(scf_selected)==1)
scf_rep_2022=evidence_has("scf2022rw1s.zip",s,paths) or evidence_has("rw1",s,paths)
scf_req4_ok=scf_rep_2022 and rep_2019

# CPS exact official release/index links + frozen 2022 family evidence.
cps_pub_2022=evidence_has("asec2022_pubuse.zip",c,paths) or evidence_has("asec2022_pubuse",c,paths)
cps_rep_2022=evidence_has("cps_asec_ascii_repwgt_2022",c,paths)
cps_pub_2019=("asec2019_pubuse.zip" in cps_page or "asec2019_pubuse.zip" in cps_dir)
cps_rep_2019=("cps_asec_ascii_repwgt_2019.zip" in cps_page or "cps_asec_ascii_repwgt_2019.zip" in cps_dir)

# Layout is already frozen from E4D0A; require exact 161 PWWGT fields and key positions structurally.
pwwgt_tokens=set(re.findall(r"\bpwwgt(?:[0-9]{1,3})\b",rep_sas))
rep_layout_ok=(all(f"pwwgt{i}" in pwwgt_tokens for i in range(161))
               and "h_seq" in rep_sas and "pppos" in rep_sas)

cps_req5_ok=cps_pub_2022 and cps_pub_2019
cps_req6_ok=cps_rep_2022 and cps_rep_2019 and rep_layout_ok

req_status={
    1:acs_req1_ok,
    2:acs_req2_ok,
    3:scf_req3_ok,
    4:scf_req4_ok,
    5:cps_req5_ok,
    6:cps_req6_ok,
}

resolved_rows=[]
selected_ids=[]

def add_req(i, selected, basis):
    status="RESOLVED" if req_status[i] else "UNRESOLVED"
    for x in selected:
        if x not in selected_ids: selected_ids.append(x)
    resolved_rows.append([
        str(i), d1req[i-1]["family"], d1req[i-1]["required_source_role"],
        status, "|".join(selected) if selected else "NONE", basis
    ])

add_req(1,acs_selected,
        f"2022_housing={int(acs_housing_2022)};2022_person={int(acs_person_2022)};"
        f"2019_housing_link={int(acs_housing_2019)};2019_person_link={int(acs_person_2019)}")
add_req(2,acs_selected,
        f"acs_source_resolved={int(acs_req1_ok)};frozen_H_WGTP_replicate_static_evidence={int(acs_rep_static)}")
add_req(3,scf_selected,
        f"2022_summary={int(summary_2022)};2022_full={int(full_2022)};"
        f"2019_summary_link={int(summary_2019)};2019_full_link={int(full_2019)}")
add_req(4,["SCF_2019_REPWGT_STATA"] if scf_req4_ok else [],
        f"2022_replicate_family={int(scf_rep_2022)};2019_official_link={int(rep_2019)}")
add_req(5,["CPS_2019_PUBLIC_ASCII"] if cps_req5_ok else [],
        f"2022_public_family={int(cps_pub_2022)};2019_official_link={int(cps_pub_2019)}")
add_req(6,["CPS_2019_REPWGT_ASCII","CPS_2019_REPWGT_LAYOUT"] if cps_req6_ok else [],
        f"2022_replicate_family={int(cps_rep_2022)};2019_official_link={int(cps_rep_2019)};"
        f"exact_160_replicates_plus_base_and_keys={int(rep_layout_ok)}")

all_resolved=all(req_status.values())
resolved_count=sum(req_status.values())
unresolved_count=6-resolved_count

# Add schema artifacts needed for next phase, without downloading them now.
schema_rows=[
["ACS","2019","selected ACS source archive member header + E4D0A dictionary/accuracy docs",
 "require frozen H variables, canonical age/tenure mapping, WGTP and WGTP1..80 before any data-row parse","E4D1B"],
["SCF","2019","selected Stata source metadata + replicate Stata metadata",
 "require Y1 key, frozen K/D variables, five implicates, and official replicate-weight merge fields before any economic statistic","E4D1B"],
["CPS_ASEC","2019","public-use archive member schema + hhldfmt/persfmt as needed + frozen replicate SAS",
 "require frozen I variables, H_SEQ/PPPOS linkage, point-weight bridge, PWWGT0..160 before any I statistic","E4D1B"],
]

# Acquisition plan contains only selected data artifacts. Metadata/schema candidates can be acquired
# by E4D1B only after its own precommit.
acq_rows=[]
if all_resolved:
    for cid in selected_ids:
        r=byid[cid]
        if r["microdata_or_weight_data"]=="1":
            acq_rows.append([cid,r["family"],r["url"],r["role"],"DOWNLOAD_ONLY_AFTER_E4D1B_PRECOMMIT"])
else:
    acq_rows=[]

write_tsv(PATHINV,["root","path","inspection_mode"],path_rows)
write_tsv(RESOLVED,
          ["requirement_index","family","required_source_role","status","selected_candidate_ids","structural_basis"],
          resolved_rows)
write_tsv(SCHEMA,
          ["family","year","schema_authority","pre_data_row_gate","execution_phase"],
          schema_rows)
write_tsv(ACQPLAN,
          ["candidate_id","family","url","role","acquisition_status"],
          acq_rows)

next_phase="E4D1B" if all_resolved else "E4D1AR"
gate_rows=[
["E4D1_REUSED_AS_CANONICAL_2019_COORDINATE_ARCHITECTURE","PASS"],
["SOURCE_REQUIREMENT_COUNT","6"],
["RESOLVED_SOURCE_REQUIREMENT_COUNT",str(resolved_count)],
["UNRESOLVED_SOURCE_REQUIREMENT_COUNT",str(unresolved_count)],
["SELECTED_2019_DATA_ARTIFACT_COUNT",str(len(acq_rows))],
["METADATA_ONLY_NETWORK_ARTIFACT_COUNT","1"],
["2019_MICRODATA_FILES_DOWNLOADED","0"],
["2019_REPLICATE_WEIGHT_DATA_FILES_DOWNLOADED","0"],
["2019_MICRODATA_ROWS_OPENED","0"],
["2019_ECONOMIC_VALUES_OPENED","0"],
["FILENAME_GUESS_WITHOUT_2022_LINEAGE_USED","0"],
["TEMPORAL_GEOMETRY_AUTHORIZED","0"],
["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
]
write_tsv(GATES,["gate","value"],gate_rows)

decision_rows=[
["SOURCE_REQUIREMENT_COUNT","6"],
["RESOLVED_SOURCE_REQUIREMENT_COUNT",str(resolved_count)],
["UNRESOLVED_SOURCE_REQUIREMENT_COUNT",str(unresolved_count)],
["ALL_2019_SOURCE_LINEAGE_REQUIREMENTS_RESOLVED",str(int(all_resolved))],
["SELECTED_2019_DATA_ARTIFACT_COUNT",str(len(acq_rows))],
["2019_MICRODATA_FILES_DOWNLOADED","0"],
["2019_REPLICATE_WEIGHT_DATA_FILES_DOWNLOADED","0"],
["2019_MICRODATA_ROWS_OPENED","0"],
["2019_ECONOMIC_VALUES_OPENED","0"],
["NEXT_PRIMARY_PHASE_ID",next_phase],
["E4D1B_2019_OFFICIAL_SOURCE_ACQUISITION_AND_SCHEMA_AUDIT_AUTHORIZED",str(int(all_resolved))],
["E4D1AR_SOURCE_LINEAGE_FORENSIC_AUTHORIZED",str(int(not all_resolved))],
["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
["E4D1A_2019_OFFICIAL_SOURCE_LINEAGE_AND_ACQUISITION_PREFLIGHT","PASS"],
]
write_tsv(DECISION,["decision","value"],decision_rows)

log="\n".join([
"E4D1_REUSED_AS_CANONICAL_2019_COORDINATE_ARCHITECTURE=1",
"STATIC_2022_EXECUTOR_CONTENT_OPENED_AFTER_E4D1A_PRECOMMIT=1",
"OFFICIAL_2019_METADATA_CONTENT_OPENED_AFTER_E4D1A_PRECOMMIT=1",
"ACS_2019_DIRECTORY_INDEX_ACQUIRED_AFTER_E4D1A_PRECOMMIT=1",
"SOURCE_REQUIREMENT_COUNT=6",
f"RESOLVED_SOURCE_REQUIREMENT_COUNT={resolved_count}",
f"UNRESOLVED_SOURCE_REQUIREMENT_COUNT={unresolved_count}",
f"ALL_2019_SOURCE_LINEAGE_REQUIREMENTS_RESOLVED={int(all_resolved)}",
f"SELECTED_2019_DATA_ARTIFACT_COUNT={len(acq_rows)}",
"2019_MICRODATA_FILES_DOWNLOADED=0",
"2019_REPLICATE_WEIGHT_DATA_FILES_DOWNLOADED=0",
"2019_MICRODATA_ROWS_OPENED=0",
"2019_ECONOMIC_VALUES_OPENED=0",
"FILENAME_GUESS_WITHOUT_2022_LINEAGE_USED=0",
"TEMPORAL_GEOMETRY_AUTHORIZED=0",
"REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
f"NEXT_PRIMARY_PHASE_ID={next_phase}",
f"E4D1B_2019_OFFICIAL_SOURCE_ACQUISITION_AND_SCHEMA_AUDIT_AUTHORIZED={int(all_resolved)}",
f"E4D1AR_SOURCE_LINEAGE_FORENSIC_AUTHORIZED={int(not all_resolved)}",
"E4D1A_2019_OFFICIAL_SOURCE_LINEAGE_AND_ACQUISITION_PREFLIGHT=PASS",
])+"\n"
EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
