#!/usr/bin/env python3
from pathlib import Path
import csv,hashlib,io,json,zipfile

ROOT=Path(__file__).resolve().parents[1]

CONTRACT=ROOT/"data/metadata/E4D1BR2_acs_2019_header_differential_forensic_contract.json"
BR1_DECISION=ROOT/"data/results/E4D1BR1_targeted_acs_static_lineage_forensic_decision.tsv"
BR1_SCHEMA=ROOT/"data/results/E4D1BR1_updated_2019_schema_audit_registry.tsv"
B1_RAWVAR=ROOT/"data/results/E4D0B1_frozen_raw_variable_bridge_registry.tsv"
ACS19=ROOT/"data/raw/acs/2019/1year/csv_hus.zip"
ACS22=ROOT/"data/raw/acs/2022/1year/csv_hus.zip"

MEMBERS=ROOT/"data/results/E4D1BR2_acs_member_header_differential_registry.tsv"
TOKENS=ROOT/"data/results/E4D1BR2_required_token_presence_registry.tsv"
CLASS=ROOT/"data/results/E4D1BR2_header_failure_classification.tsv"
GATES=ROOT/"data/results/E4D1BR2_forensic_hard_gates.tsv"
DECISION=ROOT/"data/results/E4D1BR2_acs_2019_header_differential_forensic_decision.tsv"
EXEC=ROOT/"data/metadata/E4D1BR2_execution.txt"
AUDIT=ROOT/"data/metadata/E4D1BR2_acs_2019_header_differential_forensic_audit.txt"

c=json.loads(CONTRACT.read_text(encoding="utf-8"))

SUBSTANTIVE={"RMSP","NP","HHLDRAGEP","TEN"}
WEIGHTS={"WGTP"}|{f"WGTP{i}" for i in range(1,81)}
REQUIRED=SUBSTANTIVE|WEIGHTS
assert len(REQUIRED)==85

def read_tsv(p):
    with p.open("r",encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f,delimiter="\t"))

def write_tsv(p,header,rows):
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,delimiter="\t",lineterminator="\n")
        w.writerow(header); w.writerows(rows)

def read_headers(zip_path,year):
    rows=[]
    with zipfile.ZipFile(zip_path,"r") as z:
        infos=[i for i in z.infolist() if not i.is_dir() and i.filename.lower().endswith(".csv")]
        for info in infos:
            with z.open(info,"r") as raw:
                text=io.TextIOWrapper(raw,encoding="utf-8-sig",newline="")
                header=[x.strip().upper() for x in next(csv.reader(text))]
            hset=set(header)
            missing=sorted(REQUIRED-hset)
            extras=sorted(hset-REQUIRED)
            header_sha=hashlib.sha256(("\t".join(header)+"\n").encode()).hexdigest()
            rows.append({
                "year":str(year),
                "member":info.filename,
                "header_count":str(len(header)),
                "unique_header_count":str(len(hset)),
                "header_sha256":header_sha,
                "required_present_count":str(len(REQUIRED&hset)),
                "missing_required_count":str(len(missing)),
                "missing_required_tokens":"|".join(missing) if missing else "EMPTY_SET",
                "missing_substantive_tokens":"|".join(sorted(SUBSTANTIVE-hset)) if (SUBSTANTIVE-hset) else "EMPTY_SET",
                "missing_weight_tokens":"|".join(sorted(WEIGHTS-hset)) if (WEIGHTS-hset) else "EMPTY_SET",
                "extra_header_token_count":str(len(extras)),
                "RMSP_present":str(int("RMSP" in hset)),
                "NP_present":str(int("NP" in hset)),
                "HHLDRAGEP_present":str(int("HHLDRAGEP" in hset)),
                "TEN_present":str(int("TEN" in hset)),
                "WGTP_present":str(int("WGTP" in hset)),
                "WGTP1_80_all_present":str(int({f"WGTP{i}" for i in range(1,81)}<=hset)),
                "_set":hset,
                "_missing":set(missing),
            })
    return rows

r19=read_headers(ACS19,2019)
r22=read_headers(ACS22,2022)
assert len(r19)==2
assert len(r22)==2

member_header=[
    "year","member","header_count","unique_header_count","header_sha256",
    "required_present_count","missing_required_count","missing_required_tokens",
    "missing_substantive_tokens","missing_weight_tokens","extra_header_token_count",
    "RMSP_present","NP_present","HHLDRAGEP_present","TEN_present",
    "WGTP_present","WGTP1_80_all_present"
]
write_tsv(MEMBERS,member_header,[[r[h] for h in member_header] for r in (r19+r22)])

# Frozen docs presence flags from B1, for context only; no substitution.
rawvar=read_tsv(B1_RAWVAR)
doc_flags={}
for tok in ["RMSP","NP"]:
    hits=[r for r in rawvar if r.get("coordinate_or_role")=="H_ACCESS_SPACE_ROOMS_PER_PERSON"
          and r.get("family")=="ACS" and r.get("candidate_token")==tok]
    assert len(hits)==1
    doc_flags[tok]=hits[0]

token_rows=[]
for tok in sorted(REQUIRED):
    role="SUBSTANTIVE_OR_STRUCTURAL" if tok in SUBSTANTIVE else ("POINT_WEIGHT" if tok=="WGTP" else "REPLICATE_WEIGHT")
    p19=sum(tok in r["_set"] for r in r19)
    p22=sum(tok in r["_set"] for r in r22)
    d=doc_flags.get(tok,{})
    token_rows.append([
        tok,role,str(p19),str(len(r19)-p19),str(p22),str(len(r22)-p22),
        d.get("present_in_2019_official_docs","NOT_FROZEN_IN_B1_RAWVAR"),
        d.get("present_in_2022_official_docs","NOT_FROZEN_IN_B1_RAWVAR"),
        d.get("semantic_overlap_gate","NOT_FROZEN_IN_B1_RAWVAR"),
    ])
write_tsv(TOKENS,[
    "token","role","present_2019_member_count","missing_2019_member_count",
    "present_2022_member_count","missing_2022_member_count",
    "b1_present_in_2019_official_docs","b1_present_in_2022_official_docs","b1_semantic_overlap_gate"
],token_rows)

missing_sets=[frozenset(r["_missing"]) for r in r19]
aggregate_missing=set().union(*(set(x) for x in missing_sets))
heterogeneous=len(set(missing_sets))>1

if not aggregate_missing:
    classification="NO_ACTUAL_HEADER_MISMATCH"
    next_phase="E4D1BR2R"
elif heterogeneous:
    classification="MEMBER_HETEROGENEITY"
    next_phase="E4D1BR2H"
else:
    miss_sub=aggregate_missing & SUBSTANTIVE
    miss_wgt=aggregate_missing & WEIGHTS
    unexpected=aggregate_missing-REQUIRED
    if unexpected:
        classification="UNEXPECTED_SCHEMA_MISMATCH"
        next_phase="E4D1BR2X"
    elif miss_sub and miss_wgt:
        classification="MIXED_SCHEMA_MISMATCH"
        next_phase="E4D1BR2M"
    elif miss_wgt:
        classification="WEIGHT_SCHEMA_MISMATCH"
        next_phase="E4D1BR2W"
    elif miss_sub:
        classification="SUBSTANTIVE_SCHEMA_MISMATCH"
        next_phase="E4D1BR2A"
    else:
        classification="UNEXPECTED_SCHEMA_MISMATCH"
        next_phase="E4D1BR2X"

same_header19=len({r["header_sha256"] for r in r19})==1
same_header22=len({r["header_sha256"] for r in r22})==1
all22_pass=all(not r["_missing"] for r in r22)
all19_pass=all(not r["_missing"] for r in r19)

class_rows=[
["HEADER_FAILURE_CLASSIFICATION",classification],
["NEXT_PRIMARY_PHASE_ID",next_phase],
["ACS_2019_MEMBER_COUNT",str(len(r19))],
["ACS_2022_MEMBER_COUNT",str(len(r22))],
["ACS_2019_ALL_MEMBER_HEADERS_IDENTICAL",str(int(same_header19))],
["ACS_2022_ALL_MEMBER_HEADERS_IDENTICAL",str(int(same_header22))],
["ACS_2019_MISSING_SET_HETEROGENEOUS",str(int(heterogeneous))],
["ACS_2019_AGGREGATE_MISSING_REQUIRED_COUNT",str(len(aggregate_missing))],
["ACS_2019_AGGREGATE_MISSING_REQUIRED_TOKENS","|".join(sorted(aggregate_missing)) if aggregate_missing else "EMPTY_SET"],
["ACS_2019_AGGREGATE_MISSING_SUBSTANTIVE_TOKENS","|".join(sorted(aggregate_missing&SUBSTANTIVE)) if (aggregate_missing&SUBSTANTIVE) else "EMPTY_SET"],
["ACS_2019_AGGREGATE_MISSING_WEIGHT_TOKENS","|".join(sorted(aggregate_missing&WEIGHTS)) if (aggregate_missing&WEIGHTS) else "EMPTY_SET"],
]
write_tsv(CLASS,["field","value"],class_rows)

write_tsv(GATES,["gate","value"],[
["EXACT_85_REQUIRED_FIELD_SET",str(int(len(REQUIRED)==85))],
["EXACT_2_2019_CSV_MEMBERS",str(int(len(r19)==2))],
["EXACT_2_2022_CSV_MEMBERS",str(int(len(r22)==2))],
["ACS_2022_REQUIRED_85_ALL_MEMBERS_PASS",str(int(all22_pass))],
["ACS_2019_REQUIRED_85_ALL_MEMBERS_PASS",str(int(all19_pass))],
["HEADER_DIFFERENTIAL_CLASSIFIED",str(int(classification in {
"NO_ACTUAL_HEADER_MISMATCH","MEMBER_HETEROGENEITY","WEIGHT_SCHEMA_MISMATCH",
"SUBSTANTIVE_SCHEMA_MISMATCH","MIXED_SCHEMA_MISMATCH","UNEXPECTED_SCHEMA_MISMATCH"}))],
["SCHEMA_STATUS_MUTATED","0"],
["SOURCE_RESELECTION_PERFORMED","0"],
["REDOWNLOADED_ARTIFACT_COUNT","0"],
["NETWORK_ACCESS_PERFORMED","0"],
["ACS_DATA_ROWS_OPENED","0"],
["NUMERIC_RESULT_ROWS_OPENED","0"],
["2019_ECONOMIC_VALUES_OPENED","0"],
["E4D1C_2019_COORDINATE_EXECUTION_PRECOMMIT_AUTHORIZED","0"],
["TEMPORAL_GEOMETRY_AUTHORIZED","0"],
["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
])

write_tsv(DECISION,["decision","value"],[
["E4D1BR1_REUSED_AS_CANONICAL_UNRESOLVED_ACS_STATE","1"],
["HEADER_FAILURE_CLASSIFICATION",classification],
["ACS_2019_AGGREGATE_MISSING_REQUIRED_COUNT",str(len(aggregate_missing))],
["ACS_2019_AGGREGATE_MISSING_REQUIRED_TOKENS","|".join(sorted(aggregate_missing)) if aggregate_missing else "EMPTY_SET"],
["ACS_2019_MISSING_SET_HETEROGENEOUS",str(int(heterogeneous))],
["ACS_2019_ALL_MEMBER_HEADERS_IDENTICAL",str(int(same_header19))],
["ACS_2022_REQUIRED_85_ALL_MEMBERS_PASS",str(int(all22_pass))],
["ACS_SCHEMA_AUDIT_STATUS","FAIL"],
["SCHEMA_AUDIT_STATUS","BLOCKED"],
["SCHEMA_STATUS_MUTATED","0"],
["SOURCE_RESELECTION_PERFORMED","0"],
["REDOWNLOADED_ARTIFACT_COUNT","0"],
["ACS_DATA_ROWS_OPENED","0"],
["NUMERIC_RESULT_ROWS_OPENED","0"],
["2019_ECONOMIC_VALUES_OPENED","0"],
["NEXT_PRIMARY_PHASE_ID",next_phase],
["E4D1C_2019_COORDINATE_EXECUTION_PRECOMMIT_AUTHORIZED","0"],
["TEMPORAL_GEOMETRY_AUTHORIZED","0"],
["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
["E4D1BR2_ACS_2019_HEADER_DIFFERENTIAL_FORENSIC","PASS"],
])

log="\n".join([
"E4D1BR1_REUSED_AS_CANONICAL_UNRESOLVED_ACS_STATE=1",
f"ACS_2019_MEMBER_COUNT={len(r19)}",
f"ACS_2022_MEMBER_COUNT={len(r22)}",
f"ACS_2019_ALL_MEMBER_HEADERS_IDENTICAL={int(same_header19)}",
f"ACS_2022_ALL_MEMBER_HEADERS_IDENTICAL={int(same_header22)}",
f"ACS_2019_MISSING_SET_HETEROGENEOUS={int(heterogeneous)}",
f"ACS_2019_AGGREGATE_MISSING_REQUIRED_COUNT={len(aggregate_missing)}",
f"ACS_2019_AGGREGATE_MISSING_REQUIRED_TOKENS={'|'.join(sorted(aggregate_missing)) if aggregate_missing else 'EMPTY_SET'}",
f"ACS_2022_REQUIRED_85_ALL_MEMBERS_PASS={int(all22_pass)}",
f"ACS_2019_REQUIRED_85_ALL_MEMBERS_PASS={int(all19_pass)}",
f"HEADER_FAILURE_CLASSIFICATION={classification}",
"SCHEMA_STATUS_MUTATED=0",
"SOURCE_RESELECTION_PERFORMED=0",
"REDOWNLOADED_ARTIFACT_COUNT=0",
"NETWORK_ACCESS_PERFORMED=0",
"ACS_DATA_ROWS_OPENED=0",
"NUMERIC_RESULT_ROWS_OPENED=0",
"2019_ECONOMIC_VALUES_OPENED=0",
f"NEXT_PRIMARY_PHASE_ID={next_phase}",
"E4D1C_2019_COORDINATE_EXECUTION_PRECOMMIT_AUTHORIZED=0",
"TEMPORAL_GEOMETRY_AUTHORIZED=0",
"REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
"E4D1BR2_ACS_2019_HEADER_DIFFERENTIAL_FORENSIC=PASS",
])+"\n"
EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
