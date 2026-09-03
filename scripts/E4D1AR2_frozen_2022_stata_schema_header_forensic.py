#!/usr/bin/env python3
from pathlib import Path
import csv,hashlib,json,zipfile
from pandas.io.stata import StataReader

ROOT=Path(__file__).resolve().parents[1]

CONTRACT=ROOT/"data/metadata/E4D1AR2_frozen_2022_stata_schema_header_forensic_contract.json"
LINEAGE=ROOT/"data/metadata/E4D1AR2_frozen_2022_archive_hash_lineage.tsv"
RULES=ROOT/"data/metadata/E4D1AR2_schema_source_role_resolution_rules.tsv"

SUMMARY_ZIP=ROOT/"data/raw/scf/2022/scfp2022s.zip"
FULL_ZIP=ROOT/"data/raw/scf/2022/scf2022s.zip"

AR1_BINDINGS=ROOT/"data/results/E4D1AR1_candidate_binding_registry.tsv"
AR1_COMBOS=ROOT/"data/results/E4D1AR1_joint_combination_ledger.tsv"
AR1_UPDATED=ROOT/"data/results/E4D1AR1_updated_2019_source_lineage.tsv"
B1_RAWVAR=ROOT/"data/results/E4D0B1_frozen_raw_variable_bridge_registry.tsv"
CANDPLAN=ROOT/"data/metadata/E4D1A_official_2019_source_candidate_plan.tsv"

MEMBERS=ROOT/"data/results/E4D1AR2_archive_member_registry.tsv"
SCHEMA=ROOT/"data/results/E4D1AR2_stata_schema_role_registry.tsv"
PROVENANCE=ROOT/"data/results/E4D1AR2_schema_source_provenance_resolution.tsv"
UPDATED=ROOT/"data/results/E4D1AR2_updated_2019_source_lineage.tsv"
ACQPLAN=ROOT/"data/results/E4D1AR2_2019_microdata_acquisition_plan.tsv"
GATES=ROOT/"data/results/E4D1AR2_forensic_hard_gates.tsv"
DECISION=ROOT/"data/results/E4D1AR2_frozen_2022_stata_schema_header_forensic_decision.tsv"
EXEC=ROOT/"data/metadata/E4D1AR2_execution.txt"
AUDIT=ROOT/"data/metadata/E4D1AR2_frozen_2022_stata_schema_header_forensic_audit.txt"

c=json.loads(CONTRACT.read_text(encoding="utf-8"))

def read_tsv(p):
    with p.open("r",encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f,delimiter="\t"))

def write_tsv(p,header,rows):
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,delimiter="\t",lineterminator="\n")
        w.writerow(header); w.writerows(rows)

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

lineage=read_tsv(LINEAGE)
assert len(lineage)==2
for r in lineage:
    p=ROOT/r["path"]
    assert sha(p)==r["sha256"],(p,sha(p),r["sha256"])

member_rows=[]
schema_info={}

for role,p in [("SUMMARY",SUMMARY_ZIP),("FULL",FULL_ZIP)]:
    with zipfile.ZipFile(p,"r") as z:
        members=[i.filename for i in z.infolist() if not i.is_dir()]
        dta=[m for m in members if m.lower().endswith(".dta")]
        for m in members:
            member_rows.append([role,m,"DTA" if m.lower().endswith(".dta") else "OTHER"])
        if len(dta)!=1:
            schema_info[role]={
                "member_status":"UNRESOLVED_DTA_MEMBER_COUNT",
                "dta_member_count":len(dta),
                "member":"NONE",
                "variables":set(),
                "variable_count":0,
                "variable_names_sha256":"NONE",
            }
            continue

        member=dta[0]
        with z.open(member,"r") as fh:
            reader=StataReader(fh,convert_categoricals=False)
            labels=reader.variable_labels()
            names=list(labels.keys())

        upper={x.upper() for x in names}
        names_hash=hashlib.sha256(
            ("\n".join(sorted(upper))+"\n").encode("utf-8")
        ).hexdigest()

        schema_info[role]={
            "member_status":"EXACT_ONE_DTA_MEMBER",
            "dta_member_count":1,
            "member":member,
            "variables":upper,
            "variable_count":len(upper),
            "variable_names_sha256":names_hash,
        }

summary=schema_info["SUMMARY"]
full=schema_info["FULL"]

def has(info,name):
    return name.upper() in info["variables"]

summary_fin=has(summary,"FIN")
summary_pirtotal=has(summary,"PIRTOTAL")
full_fin=has(full,"FIN")
full_pirtotal=has(full,"PIRTOTAL")
summary_x42001=has(summary,"X42001")
full_x42001=has(full,"X42001")
summary_y1=has(summary,"Y1")
full_y1=has(full,"Y1")
summary_yy1=has(summary,"YY1")
full_yy1=has(full,"YY1")

# Reconfirm frozen X42001 role structurally.
rawvar=read_tsv(B1_RAWVAR)
xrows=[r for r in rawvar if r.get("candidate_token","").upper()=="X42001" and r.get("family","").upper()=="SCF"]
assert xrows, "frozen SCF X42001 point-weight row missing"

# Reconfirm frozen joint provenance from E4D1AR1 outputs.
bindings=read_tsv(AR1_BINDINGS)
bmap={r["binding"]:r for r in bindings}
required_joint=["joined","value_matrices","full_weights","age_matrix"]
joint_binding_gate=all(
    name in bmap and
    bmap[name]["candidate_dependencies"]=="SCF_FULL_STATA|SCF_SUMMARY_STATA"
    for name in required_joint
)

combos=read_tsv(AR1_COMBOS)
joined_merge_gate=any(
    r["binding"]=="joined" and
    r["explicit_merge_join_concat"]=="1" and
    "merge" in r["combination_operator"].lower()
    for r in combos
)

member_gate=(
    summary["member_status"]=="EXACT_ONE_DTA_MEMBER" and
    full["member_status"]=="EXACT_ONE_DTA_MEMBER"
)

summary_target_role=summary_fin and summary_pirtotal
full_target_role=full_fin and full_pirtotal
full_weight_role=full_x42001
summary_weight_role=summary_x42001
key_gate=summary_y1 and full_y1

joint_rule=(
    member_gate and
    summary_target_role and
    not full_target_role and
    full_weight_role and
    not summary_weight_role and
    key_gate and
    joined_merge_gate and
    joint_binding_gate
)

summary_only_rule=(
    member_gate and
    summary_target_role and
    summary_weight_role and
    not full_target_role and
    not full_weight_role
)

full_only_rule=(
    member_gate and
    full_target_role and
    full_weight_role and
    not summary_target_role and
    not summary_weight_role
)

proven=[]
if joint_rule:
    proven.append("JOINT_SUMMARY_PLUS_FULL")
if summary_only_rule:
    proven.append("SUMMARY_ONLY")
if full_only_rule:
    proven.append("FULL_ONLY")

selected=proven[0] if len(proven)==1 else "NONE"
status="RESOLVED" if selected!="NONE" else "UNRESOLVED"

if selected=="JOINT_SUMMARY_PLUS_FULL":
    selected_2019="SCF_2019_SUMMARY_STATA|SCF_2019_FULL_STATA"
elif selected=="SUMMARY_ONLY":
    selected_2019="SCF_2019_SUMMARY_STATA"
elif selected=="FULL_ONLY":
    selected_2019="SCF_2019_FULL_STATA"
else:
    selected_2019="NONE"

prior=read_tsv(AR1_UPDATED)
assert len(prior)==6
updated=[]
for r in prior:
    q=dict(r)
    if q["requirement_index"]=="3" and status=="RESOLVED":
        q["status"]="RESOLVED"
        q["selected_candidate_ids"]=selected_2019
        q["structural_basis"]=f"E4D1AR2 Stata schema roles uniquely prove {selected}"
    updated.append(q)

for a,b in zip(prior,updated):
    if a["requirement_index"]!="3":
        assert a==b

resolved_count=sum(r["status"]=="RESOLVED" for r in updated)
unresolved_count=6-resolved_count
all_resolved=(resolved_count==6)

plan=read_tsv(CANDPLAN)
pby={r["candidate_id"]:r for r in plan}
acq_ids=[]
if all_resolved:
    for r in updated:
        for cid in r["selected_candidate_ids"].split("|"):
            if cid in pby and pby[cid]["microdata_or_weight_data"]=="1" and cid not in acq_ids:
                acq_ids.append(cid)

acq_rows=[]
for cid in acq_ids:
    r=pby[cid]
    acq_rows.append([cid,r["family"],r["url"],r["role"],"DOWNLOAD_ONLY_AFTER_E4D1B_PRECOMMIT"])

write_tsv(MEMBERS,["archive_role","member_name","member_class"],member_rows)

schema_rows=[]
for role,info in [("SUMMARY",summary),("FULL",full)]:
    schema_rows.append([
        role,info["member_status"],str(info["dta_member_count"]),info["member"],
        str(info["variable_count"]),info["variable_names_sha256"],
        str(int(has(info,"FIN"))),str(int(has(info,"PIRTOTAL"))),
        str(int(has(info,"X42001"))),str(int(has(info,"Y1"))),str(int(has(info,"YY1")))
    ])
write_tsv(SCHEMA,
          ["archive_role","member_status","dta_member_count","dta_member",
           "variable_count","variable_names_sha256","FIN_present","PIRTOTAL_present",
           "X42001_present","Y1_present","YY1_present"],
          schema_rows)

write_tsv(PROVENANCE,["test","value","status"],[
["SUMMARY_FIN_PRESENT",str(int(summary_fin)),"PASS" if summary_fin else "FAIL"],
["SUMMARY_PIRTOTAL_PRESENT",str(int(summary_pirtotal)),"PASS" if summary_pirtotal else "FAIL"],
["FULL_FIN_PRESENT",str(int(full_fin)),"OBSERVED"],
["FULL_PIRTOTAL_PRESENT",str(int(full_pirtotal)),"OBSERVED"],
["FULL_X42001_PRESENT",str(int(full_x42001)),"PASS" if full_x42001 else "FAIL"],
["SUMMARY_X42001_PRESENT",str(int(summary_x42001)),"OBSERVED"],
["BOTH_Y1_PRESENT",str(int(key_gate)),"PASS" if key_gate else "FAIL"],
["E4D1AR1_JOINED_EXPLICIT_MERGE",str(int(joined_merge_gate)),"PASS" if joined_merge_gate else "FAIL"],
["E4D1AR1_REQUIRED_DOWNSTREAM_JOINT_BINDINGS",str(int(joint_binding_gate)),"PASS" if joint_binding_gate else "FAIL"],
["JOINT_SUMMARY_PLUS_FULL_RULE",str(int(joint_rule)),"PASS" if joint_rule else "NOT_PROVEN"],
["SUMMARY_ONLY_RULE",str(int(summary_only_rule)),"PASS" if summary_only_rule else "NOT_PROVEN"],
["FULL_ONLY_RULE",str(int(full_only_rule)),"PASS" if full_only_rule else "NOT_PROVEN"],
])

write_tsv(UPDATED,list(prior[0].keys()),[[r[k] for k in prior[0].keys()] for r in updated])
write_tsv(ACQPLAN,["candidate_id","family","url","role","acquisition_status"],acq_rows)

next_phase="E4D1B" if all_resolved else "E4D1AR2R"

write_tsv(GATES,["gate","value"],[
["FORENSIC_TARGET_REQUIREMENT_INDEX","3"],
["SUMMARY_DTA_MEMBER_COUNT",str(summary["dta_member_count"])],
["FULL_DTA_MEMBER_COUNT",str(full["dta_member_count"])],
["STATA_OBSERVATION_ROWS_READ","0"],
["NUMERIC_RESULT_ROWS_OPENED","0"],
["2019_DATA_FILES_DOWNLOADED","0"],
["2019_MICRODATA_ROWS_OPENED","0"],
["2019_ECONOMIC_VALUES_OPENED","0"],
["FROZEN_X42001_ROLE_REUSED","1"],
["E4D1AR1_JOINT_PROVENANCE_REUSED",str(int(joined_merge_gate and joint_binding_gate))],
["PROVEN_SOURCE_SET_COUNT",str(len(proven))],
["NON_REQUIREMENT3_SOURCE_ROWS_MUTATED","0"],
["RESOLVED_SOURCE_REQUIREMENT_COUNT",str(resolved_count)],
["UNRESOLVED_SOURCE_REQUIREMENT_COUNT",str(unresolved_count)],
["TEMPORAL_GEOMETRY_AUTHORIZED","0"],
["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
])

write_tsv(DECISION,["decision","value"],[
["REQUIREMENT_3_STATUS",status],
["SELECTED_EFFECTIVE_SOURCE_SET",selected],
["SELECTED_2019_CANDIDATES",selected_2019],
["SUMMARY_DTA_MEMBER",summary["member"]],
["FULL_DTA_MEMBER",full["member"]],
["SUMMARY_FIN_PRESENT",str(int(summary_fin))],
["SUMMARY_PIRTOTAL_PRESENT",str(int(summary_pirtotal))],
["FULL_FIN_PRESENT",str(int(full_fin))],
["FULL_PIRTOTAL_PRESENT",str(int(full_pirtotal))],
["SUMMARY_X42001_PRESENT",str(int(summary_x42001))],
["FULL_X42001_PRESENT",str(int(full_x42001))],
["BOTH_Y1_PRESENT",str(int(key_gate))],
["PROVEN_SOURCE_SET_COUNT",str(len(proven))],
["RESOLVED_SOURCE_REQUIREMENT_COUNT",str(resolved_count)],
["UNRESOLVED_SOURCE_REQUIREMENT_COUNT",str(unresolved_count)],
["ALL_2019_SOURCE_LINEAGE_REQUIREMENTS_RESOLVED",str(int(all_resolved))],
["SELECTED_2019_DATA_ARTIFACT_COUNT",str(len(acq_rows))],
["STATA_OBSERVATION_ROWS_READ","0"],
["2019_DATA_FILES_DOWNLOADED","0"],
["2019_MICRODATA_ROWS_OPENED","0"],
["2019_ECONOMIC_VALUES_OPENED","0"],
["NEXT_PRIMARY_PHASE_ID",next_phase],
["E4D1B_2019_OFFICIAL_SOURCE_ACQUISITION_AND_SCHEMA_AUDIT_AUTHORIZED",str(int(all_resolved))],
["E4D1AR2R_TARGETED_SCHEMA_FORENSIC_AUTHORIZED",str(int(not all_resolved))],
["TEMPORAL_GEOMETRY_AUTHORIZED","0"],
["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
["E4D1AR2_FROZEN_2022_STATA_SCHEMA_HEADER_FORENSIC","PASS"],
])

log="\n".join([
"E4D1AR1_REUSED_AS_CANONICAL_JOINT_SOURCE_AMBIGUITY_STATE=1",
"FORENSIC_TARGET_REQUIREMENT_INDEX=3",
"ARCHIVE_MEMBER_LISTING_OPENED_AFTER_E4D1AR2_PRECOMMIT=1",
"STATA_SCHEMA_METADATA_OPENED_AFTER_E4D1AR2_PRECOMMIT=1",
f"SUMMARY_DTA_MEMBER_COUNT={summary['dta_member_count']}",
f"FULL_DTA_MEMBER_COUNT={full['dta_member_count']}",
f"SUMMARY_FIN_PRESENT={int(summary_fin)}",
f"SUMMARY_PIRTOTAL_PRESENT={int(summary_pirtotal)}",
f"FULL_FIN_PRESENT={int(full_fin)}",
f"FULL_PIRTOTAL_PRESENT={int(full_pirtotal)}",
f"SUMMARY_X42001_PRESENT={int(summary_x42001)}",
f"FULL_X42001_PRESENT={int(full_x42001)}",
f"SUMMARY_Y1_PRESENT={int(summary_y1)}",
f"FULL_Y1_PRESENT={int(full_y1)}",
f"SUMMARY_YY1_PRESENT={int(summary_yy1)}",
f"FULL_YY1_PRESENT={int(full_yy1)}",
f"E4D1AR1_JOINED_EXPLICIT_MERGE={int(joined_merge_gate)}",
f"E4D1AR1_REQUIRED_DOWNSTREAM_JOINT_BINDINGS={int(joint_binding_gate)}",
f"PROVEN_SOURCE_SET_COUNT={len(proven)}",
f"REQUIREMENT_3_STATUS={status}",
f"SELECTED_EFFECTIVE_SOURCE_SET={selected}",
f"SELECTED_2019_CANDIDATES={selected_2019}",
f"RESOLVED_SOURCE_REQUIREMENT_COUNT={resolved_count}",
f"UNRESOLVED_SOURCE_REQUIREMENT_COUNT={unresolved_count}",
f"ALL_2019_SOURCE_LINEAGE_REQUIREMENTS_RESOLVED={int(all_resolved)}",
f"SELECTED_2019_DATA_ARTIFACT_COUNT={len(acq_rows)}",
"STATA_OBSERVATION_ROWS_READ=0",
"NUMERIC_RESULT_ROWS_OPENED=0",
"2019_DATA_FILES_DOWNLOADED=0",
"2019_MICRODATA_ROWS_OPENED=0",
"2019_ECONOMIC_VALUES_OPENED=0",
"NON_REQUIREMENT3_SOURCE_ROWS_MUTATED=0",
"TEMPORAL_GEOMETRY_AUTHORIZED=0",
"REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
f"NEXT_PRIMARY_PHASE_ID={next_phase}",
f"E4D1B_2019_OFFICIAL_SOURCE_ACQUISITION_AND_SCHEMA_AUDIT_AUTHORIZED={int(all_resolved)}",
f"E4D1AR2R_TARGETED_SCHEMA_FORENSIC_AUTHORIZED={int(not all_resolved)}",
"E4D1AR2_FROZEN_2022_STATA_SCHEMA_HEADER_FORENSIC=PASS",
])+"\n"
EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
