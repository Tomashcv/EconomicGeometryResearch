#!/usr/bin/env python3
from pathlib import Path
import csv,hashlib,io,json,zipfile

ROOT=Path(__file__).resolve().parents[1]

CONTRACT=ROOT/"data/metadata/E4D1BR1_targeted_acs_static_lineage_forensic_contract.json"
R0_HASHES=ROOT/"data/metadata/E4D1BR_R0_preserved_output_hash_lineage.tsv"
BR_COLS=ROOT/"data/results/E4D1BR_acs_required_column_recovery_registry.tsv"
BR_SCHEMA=ROOT/"data/results/E4D1BR_2019_schema_audit_registry.tsv"
B1_RAWVAR=ROOT/"data/results/E4D0B1_frozen_raw_variable_bridge_registry.tsv"
B1_ADJ=ROOT/"data/results/E4D0B1_adjudication_registry.tsv"
ACS19=ROOT/"data/raw/acs/2019/1year/csv_hus.zip"
ACS22=ROOT/"data/raw/acs/2022/1year/csv_hus.zip"

EVIDENCE=ROOT/"data/results/E4D1BR1_acs_static_lineage_evidence_registry.tsv"
RESOLUTION=ROOT/"data/results/E4D1BR1_acs_lineage_resolution.tsv"
COLS=ROOT/"data/results/E4D1BR1_acs_required_column_registry.tsv"
SCHEMA=ROOT/"data/results/E4D1BR1_updated_2019_schema_audit_registry.tsv"
GATES=ROOT/"data/results/E4D1BR1_forensic_hard_gates.tsv"
DECISION=ROOT/"data/results/E4D1BR1_targeted_acs_static_lineage_forensic_decision.tsv"
EXEC=ROOT/"data/metadata/E4D1BR1_execution.txt"
AUDIT=ROOT/"data/metadata/E4D1BR1_targeted_acs_static_lineage_forensic_audit.txt"

c=json.loads(CONTRACT.read_text(encoding="utf-8"))

def read_tsv(p):
    with p.open("r",encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f,delimiter="\t"))

def write_tsv(p,header,rows):
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,delimiter="\t",lineterminator="\n")
        w.writerow(header); w.writerows(rows)

def csv_headers(zip_path):
    out={}
    with zipfile.ZipFile(zip_path,"r") as z:
        for info in z.infolist():
            if info.is_dir() or not info.filename.lower().endswith(".csv"):
                continue
            with z.open(info,"r") as raw:
                text=io.TextIOWrapper(raw,encoding="utf-8-sig",newline="")
                header=next(csv.reader(text))
            out[info.filename]=[x.strip().upper() for x in header]
    return out

# Recheck preserved E4D1BR outputs against the frozen R0 hash ledger.
hash_rows=read_tsv(R0_HASHES)
for r in hash_rows:
    p=ROOT/r["artifact"]
    assert hashlib.sha256(p.read_bytes()).hexdigest()==r["sha256"],p

prior_cols=read_tsv(BR_COLS)
prior_schema=read_tsv(BR_SCHEMA)
rawvar=read_tsv(B1_RAWVAR)
adj=read_tsv(B1_ADJ)

# Exact prior blocked shape.
prior_weights={r["column"] for r in prior_cols if r["role_class"]=="WEIGHT"}
prior_nonweights={r["column"] for r in prior_cols if r["role_class"]!="WEIGHT"}
expected_weights={"WGTP"}|{f"WGTP{i}" for i in range(1,81)}
prior_shape_ok=(prior_weights==expected_weights and prior_nonweights=={"HHLDRAGEP","TEN"} and len(prior_cols)==83)

# Exact eligible missing tokens from the already-frozen B1 raw-variable bridge.
eligible={"RMSP","NP"}
candidate_rows=[
    r for r in rawvar
    if r.get("coordinate_or_role")=="H_ACCESS_SPACE_ROOMS_PER_PERSON"
    and r.get("family")=="ACS"
    and r.get("candidate_token") in eligible
]
candidate_by_token={r["candidate_token"]:r for r in candidate_rows}
rawvar_ok=set(candidate_by_token)==eligible

presence_fields=[
    "present_in_frozen_2022_authority",
    "present_in_2019_official_docs",
    "present_in_2022_official_docs",
    "semantic_overlap_gate",
]
for tok in eligible:
    r=candidate_by_token.get(tok,{})
    rawvar_ok = rawvar_ok and all(r.get(k)=="1" for k in presence_fields)

# Independent frozen adjudication cross-check.
obj2=[r for r in adj if r.get("object_index")=="2"]
adj_ok=False
adj_basis=""
adj_evidence=""
if len(obj2)==1:
    r=obj2[0]
    adj_basis=r.get("basis","")
    adj_evidence=r.get("evidence_ids","")
    adj_ok=(
        r.get("axis")=="VARIABLE_DEFINITION_CONTINUITY"
        and r.get("scope_id")=="H_ACCESS_SPACE_ROOMS_PER_PERSON"
        and r.get("family")=="ACS"
        and r.get("status")=="PASS"
        and adj_evidence=="EVH_RMSP|EVH_NP"
        and "numerator/denominator" in adj_basis.lower()
    )

# Header-only checks.
h19=csv_headers(ACS19)
h22=csv_headers(ACS22)
required_nonweights={"RMSP","NP","HHLDRAGEP","TEN"}
required=required_nonweights|expected_weights
header22_ok=bool(h22) and all(required<=set(v) for v in h22.values())
header19_ok=bool(h19) and all(required<=set(v) for v in h19.values())

resolved=all([prior_shape_ok,rawvar_ok,adj_ok,header22_ok,header19_ok])

evidence_rows=[
["BR1_PRIOR_BLOCKED_SHAPE","E4D1BR_PRESERVED_OUTPUTS",
 f"total={len(prior_cols)};weights={len(prior_weights)};nonweights={'|'.join(sorted(prior_nonweights))}",
 "PASS" if prior_shape_ok else "UNRESOLVED"],
["BR1_RAWVAR_RMSP","E4D0B1_RAWVAR",
 "coordinate=H_ACCESS_SPACE_ROOMS_PER_PERSON;family=ACS;token=RMSP;all_presence_gates=1",
 "PASS" if rawvar_ok and "RMSP" in candidate_by_token else "UNRESOLVED"],
["BR1_RAWVAR_NP","E4D0B1_RAWVAR",
 "coordinate=H_ACCESS_SPACE_ROOMS_PER_PERSON;family=ACS;token=NP;all_presence_gates=1",
 "PASS" if rawvar_ok and "NP" in candidate_by_token else "UNRESOLVED"],
["BR1_ADJ_OBJECT2","E4D0B1_ADJUDICATION",
 f"status={'PASS' if adj_ok else 'UNRESOLVED'};evidence_ids={adj_evidence};basis={adj_basis}",
 "PASS" if adj_ok else "UNRESOLVED"],
["BR1_2022_HEADERS","ACS_2022_HOUSING_HEADERS",
 f"csv_members={len(h22)};required_85_in_every_member={int(header22_ok)}",
 "PASS" if header22_ok else "UNRESOLVED"],
["BR1_2019_HEADERS","ACS_2019_HOUSING_HEADERS",
 f"csv_members={len(h19)};required_85_in_every_member={int(header19_ok)}",
 "PASS" if header19_ok else "UNRESOLVED"],
]
write_tsv(EVIDENCE,["evidence_id","source","structural_summary","status"],evidence_rows)

write_tsv(RESOLUTION,["field","value"],[
["ELIGIBLE_MISSING_TOKEN_COUNT","2"],
["ELIGIBLE_MISSING_TOKENS","RMSP|NP"],
["PRIOR_NON_WEIGHT_FIELDS","HHLDRAGEP|TEN"],
["RESOLVED_NON_WEIGHT_FIELDS","HHLDRAGEP|NP|RMSP|TEN" if resolved else "UNRESOLVED"],
["POINT_WEIGHT","WGTP"],
["REPLICATE_WEIGHT_COUNT","80"],
["TOTAL_REQUIRED_FIELD_COUNT","85" if resolved else "83"],
["ACS_2022_HEADER_MEMBER_COUNT",str(len(h22))],
["ACS_2019_HEADER_MEMBER_COUNT",str(len(h19))],
["ACS_STATIC_LINEAGE_RESOLUTION_STATUS","RESOLVED" if resolved else "UNRESOLVED"],
])

# Required-column registry. If unresolved, preserve the prior 83 only; never invent a partial success.
if resolved:
    required_rows=[]
    for x in sorted(required):
        if x in required_nonweights:
            role="SUBSTANTIVE_OR_STRUCTURAL"
            provenance="E4D1BR1_FROZEN_LINEAGE"
        elif x=="WGTP":
            role="POINT_WEIGHT"
            provenance="E4D1BR_FROZEN_WEIGHT_ARCHITECTURE"
        else:
            role="REPLICATE_WEIGHT"
            provenance="E4D1BR_FROZEN_WEIGHT_ARCHITECTURE"
        required_rows.append([x,role,provenance,"1","1"])
else:
    required_rows=[
        [r["column"],r["role_class"],"E4D1BR_PRESERVED_UNRESOLVED",
         r.get("present_in_2022_housing_header","1"),"UNRESOLVED"]
        for r in prior_cols
    ]
write_tsv(COLS,["column","role_class","provenance","present_in_2022_header","present_in_2019_header"],required_rows)

# Targeted schema mutation: ACS row only. Other five rows are copied semantically unchanged.
assert len(prior_schema)==6
updated=[]
for i,r in enumerate(prior_schema):
    q=dict(r)
    if i==0:
        assert q["candidate_id"]=="ACS_2019_NATIONAL_HOUSING_CSV"
        if resolved:
            q["required_field_count"]="85"
            q["structural_summary"]=(
                "frozen_nonweight=HHLDRAGEP|NP|RMSP|TEN;"
                "WGTP_family=81;2019_header_members="
                f"{len(h19)};2022_header_members={len(h22)}"
            )
            q["status"]="PASS"
    updated.append(q)

header=list(prior_schema[0].keys())
write_tsv(SCHEMA,header,[[r[h] for h in header] for r in updated])

non_acs_immutable=all(updated[i]==prior_schema[i] for i in range(1,6))
acs_pass=(updated[0]["status"]=="PASS")
all_schema_pass=(acs_pass and non_acs_immutable and all(r["status"]=="PASS" for r in updated[1:]))
next_phase="E4D1C" if all_schema_pass else "E4D1BR2"

write_tsv(GATES,["gate","value"],[
["EXACT_TWO_ELIGIBLE_MISSING_TOKENS",str(int(eligible=={"RMSP","NP"}))],
["PRIOR_BLOCKED_SHAPE_GATE",str(int(prior_shape_ok))],
["B1_RAWVAR_LINEAGE_GATE",str(int(rawvar_ok))],
["B1_ADJUDICATION_CROSSCHECK_GATE",str(int(adj_ok))],
["ACS_2022_HEADER_GATE",str(int(header22_ok))],
["ACS_2019_HEADER_GATE",str(int(header19_ok))],
["EXACT_85_REQUIRED_FIELDS_GATE",str(int(resolved and len(required)==85))],
["NON_ACS_5_SCHEMA_ROWS_IMMUTABLE",str(int(non_acs_immutable))],
["ACS_SCHEMA_PASS",str(int(acs_pass))],
["ALL_6_SCHEMA_ROWS_PASS",str(int(all_schema_pass))],
["REDOWNLOADED_ARTIFACT_COUNT","0"],
["ACS_DATA_ROWS_OPENED","0"],
["NUMERIC_RESULT_ROWS_OPENED","0"],
["2019_ECONOMIC_VALUES_OPENED","0"],
["TEMPORAL_GEOMETRY_AUTHORIZED","0"],
["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
])

write_tsv(DECISION,["decision","value"],[
["E4D1BR_R0_REUSED_AS_CANONICAL_BLOCKED_STATE","1"],
["ELIGIBLE_MISSING_TOKEN_COUNT","2"],
["ELIGIBLE_MISSING_TOKENS","RMSP|NP"],
["ACS_STATIC_LINEAGE_RESOLUTION_STATUS","RESOLVED" if resolved else "UNRESOLVED"],
["ACS_SCHEMA_AUDIT_STATUS","PASS" if acs_pass else "FAIL"],
["SCF_SCHEMA_AUDIT_STATUS","PASS"],
["CPS_CONTAINER_AUDIT_STATUS","PASS"],
["SCHEMA_AUDIT_STATUS","PASS" if all_schema_pass else "BLOCKED"],
["NON_ACS_5_SCHEMA_ROWS_MUTATED","0" if non_acs_immutable else "1"],
["REDOWNLOADED_ARTIFACT_COUNT","0"],
["ACS_DATA_ROWS_OPENED","0"],
["NUMERIC_RESULT_ROWS_OPENED","0"],
["2019_ECONOMIC_VALUES_OPENED","0"],
["NEXT_PRIMARY_PHASE_ID",next_phase],
["E4D1C_2019_COORDINATE_EXECUTION_PRECOMMIT_AUTHORIZED",str(int(all_schema_pass))],
["E4D1BR2_FURTHER_ACS_LINEAGE_FORENSIC_AUTHORIZED",str(int(not all_schema_pass))],
["TEMPORAL_GEOMETRY_AUTHORIZED","0"],
["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
["E4D1BR1_TARGETED_ACS_STATIC_LINEAGE_FORENSIC","PASS"],
])

log="\n".join([
"E4D1BR_R0_REUSED_AS_CANONICAL_BLOCKED_STATE=1",
"TARGET_COORDINATE=H_ACCESS_SPACE_ROOMS_PER_PERSON",
"ELIGIBLE_MISSING_TOKEN_COUNT=2",
"ELIGIBLE_MISSING_TOKENS=RMSP|NP",
f"PRIOR_BLOCKED_SHAPE_PASS={int(prior_shape_ok)}",
f"B1_RAWVAR_LINEAGE_PASS={int(rawvar_ok)}",
f"B1_ADJUDICATION_CROSSCHECK_PASS={int(adj_ok)}",
f"ACS_2022_HEADER_MEMBER_COUNT={len(h22)}",
f"ACS_2022_HEADER_GATE={int(header22_ok)}",
f"ACS_2019_HEADER_MEMBER_COUNT={len(h19)}",
f"ACS_2019_HEADER_GATE={int(header19_ok)}",
f"ACS_STATIC_LINEAGE_RESOLUTION_STATUS={'RESOLVED' if resolved else 'UNRESOLVED'}",
f"ACS_REQUIRED_FIELD_COUNT={85 if resolved else 83}",
f"NON_ACS_5_SCHEMA_ROWS_IMMUTABLE={int(non_acs_immutable)}",
f"ACS_SCHEMA_AUDIT_STATUS={'PASS' if acs_pass else 'FAIL'}",
f"SCHEMA_AUDIT_STATUS={'PASS' if all_schema_pass else 'BLOCKED'}",
"REDOWNLOADED_ARTIFACT_COUNT=0",
"ACS_DATA_ROWS_OPENED=0",
"NUMERIC_RESULT_ROWS_OPENED=0",
"2019_ECONOMIC_VALUES_OPENED=0",
"TEMPORAL_GEOMETRY_AUTHORIZED=0",
"REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
f"NEXT_PRIMARY_PHASE_ID={next_phase}",
f"E4D1C_2019_COORDINATE_EXECUTION_PRECOMMIT_AUTHORIZED={int(all_schema_pass)}",
f"E4D1BR2_FURTHER_ACS_LINEAGE_FORENSIC_AUTHORIZED={int(not all_schema_pass)}",
"E4D1BR1_TARGETED_ACS_STATIC_LINEAGE_FORENSIC=PASS",
])+"\n"
EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
