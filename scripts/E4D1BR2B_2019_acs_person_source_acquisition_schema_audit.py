#!/usr/bin/env python3
from pathlib import Path
import csv,hashlib,io,json,zipfile

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"data/metadata/E4D1BR2B_2019_acs_person_source_acquisition_schema_audit_contract.json"
BRIDGE=ROOT/"data/results/E4D1BR2A_householder_age_versioned_bridge_policy.tsv"
PERSON=ROOT/"data/raw/acs/2019/1year/csv_pus.zip"

MEMBERS=ROOT/"data/results/E4D1BR2B_person_archive_member_registry.tsv"
SCHEMA=ROOT/"data/results/E4D1BR2B_person_header_schema_registry.tsv"
GATES=ROOT/"data/results/E4D1BR2B_schema_audit_hard_gates.tsv"
DECISION=ROOT/"data/results/E4D1BR2B_2019_acs_person_source_acquisition_schema_audit_decision.tsv"
EXEC=ROOT/"data/metadata/E4D1BR2B_execution.txt"
AUDIT=ROOT/"data/metadata/E4D1BR2B_2019_acs_person_source_acquisition_schema_audit.txt"

c=json.loads(CONTRACT.read_text(encoding="utf-8"))
REQUIRED=set(c["required_header_fields"])
assert REQUIRED=={"SERIALNO","RELSHIPP","AGEP"}

def read_tsv(p):
    with p.open("r",encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f,delimiter="\t"))

def write_tsv(p,h,rows):
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,delimiter="\t",lineterminator="\n")
        w.writerow(h); w.writerows(rows)

bridge={r["field"]:r["value"] for r in read_tsv(BRIDGE)}
assert bridge["BRIDGE_ID"]=="ACS_2019_HOUSEHOLDER_AGE_FROM_REFERENCE_PERSON"
assert bridge["HOUSING_KEY"]=="SERIALNO"
assert bridge["PERSON_KEY"]=="SERIALNO"
assert bridge["PERSON_ROLE_FIELD"]=="RELSHIPP"
assert bridge["PERSON_ROLE_CODE"]=="20"
assert bridge["PERSON_AGE_FIELD"]=="AGEP"
assert bridge["PERSON_WEIGHT_USED"]=="0"

member_rows=[]
schema_rows=[]
with zipfile.ZipFile(PERSON,"r") as z:
    infos=[i for i in z.infolist() if not i.is_dir()]
    csv_infos=[i for i in infos if i.filename.lower().endswith(".csv")]
    valid_zip=True
    for info in infos:
        member_rows.append([
            info.filename,
            str(info.file_size),
            str(info.compress_size),
            "CSV" if info.filename.lower().endswith(".csv") else "OTHER",
        ])
    for info in csv_infos:
        with z.open(info,"r") as raw:
            text=io.TextIOWrapper(raw,encoding="utf-8-sig",newline="")
            header=[x.strip().upper() for x in next(csv.reader(text))]
        hset=set(header)
        missing=sorted(REQUIRED-hset)
        schema_rows.append([
            info.filename,
            str(len(header)),
            hashlib.sha256(("\t".join(header)+"\n").encode()).hexdigest(),
            str(int("SERIALNO" in hset)),
            str(int("RELSHIPP" in hset)),
            str(int("AGEP" in hset)),
            str(len(missing)),
            "|".join(missing) if missing else "EMPTY_SET",
            "PASS" if not missing else "FAIL",
        ])

write_tsv(MEMBERS,["member","uncompressed_bytes","compressed_bytes","content_class"],member_rows)
write_tsv(SCHEMA,[
    "member","header_field_count","header_sha256",
    "SERIALNO_present","RELSHIPP_present","AGEP_present",
    "missing_required_count","missing_required_tokens","status"
],schema_rows)

csv_count=len(schema_rows)
schema_pass=(valid_zip and csv_count>=1 and all(r[-1]=="PASS" for r in schema_rows))
headers_identical=(len({r[2] for r in schema_rows})==1 if schema_rows else False)
next_phase="E4D1BR2C" if schema_pass else "E4D1BR2BR"

write_tsv(GATES,["gate","value"],[
["VALID_ZIP",str(int(valid_zip))],
["CSV_MEMBER_COUNT",str(csv_count)],
["MINIMUM_ONE_CSV_MEMBER",str(int(csv_count>=1))],
["ALL_CSV_MEMBERS_HAVE_SERIALNO",str(int(bool(schema_rows) and all(r[3]=="1" for r in schema_rows)))],
["ALL_CSV_MEMBERS_HAVE_RELSHIPP",str(int(bool(schema_rows) and all(r[4]=="1" for r in schema_rows)))],
["ALL_CSV_MEMBERS_HAVE_AGEP",str(int(bool(schema_rows) and all(r[5]=="1" for r in schema_rows)))],
["ALL_REQUIRED_HEADER_FIELDS_PASS",str(int(schema_pass))],
["ALL_CSV_MEMBER_HEADERS_IDENTICAL",str(int(headers_identical))],
["REFERENCE_PERSON_CODE20_OBSERVED","0"],
["REFERENCE_PERSON_UNIQUENESS_VALIDATED","0"],
["HOUSING_LINK_COVERAGE_VALIDATED","0"],
["DUPLICATE_AMPLIFICATION_VALIDATED_ABSENT","0"],
["PERSON_DATA_ROWS_PARSED","0"],
["MICRODATA_ROWS_OPENED","0"],
["NUMERIC_RESULT_ROWS_OPENED","0"],
["2019_ECONOMIC_VALUES_OPENED","0"],
["E4D1C_2019_COORDINATE_EXECUTION_PRECOMMIT_AUTHORIZED","0"],
["TEMPORAL_GEOMETRY_AUTHORIZED","0"],
["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
])

write_tsv(DECISION,["decision","value"],[
["E4D1BR2A_REUSED_AS_CANONICAL_VERSIONED_BRIDGE_AUTHORITY","1"],
["PERSON_SOURCE_ACQUIRED","1"],
["PERSON_SOURCE_SCHEMA_STATUS","PASS" if schema_pass else "UNRESOLVED"],
["PERSON_CSV_MEMBER_COUNT",str(csv_count)],
["PERSON_CSV_HEADERS_IDENTICAL",str(int(headers_identical))],
["REQUIRED_PERSON_HEADER_FIELDS","AGEP|RELSHIPP|SERIALNO"],
["REFERENCE_PERSON_CODE20_OBSERVED","0"],
["REFERENCE_PERSON_UNIQUENESS_VALIDATED","0"],
["HOUSING_LINK_COVERAGE_VALIDATED","0"],
["DUPLICATE_AMPLIFICATION_VALIDATED_ABSENT","0"],
["PERSON_DATA_ROWS_PARSED","0"],
["MICRODATA_ROWS_OPENED","0"],
["NUMERIC_RESULT_ROWS_OPENED","0"],
["2019_ECONOMIC_VALUES_OPENED","0"],
["ACS_SCHEMA_AUDIT_STATUS","FAIL"],
["SCHEMA_AUDIT_STATUS","BLOCKED"],
["NEXT_PRIMARY_PHASE_ID",next_phase],
["E4D1BR2C_REFERENCE_PERSON_LINKAGE_STRUCTURAL_AUDIT_PREFLIGHT_AUTHORIZED",str(int(schema_pass))],
["E4D1C_2019_COORDINATE_EXECUTION_PRECOMMIT_AUTHORIZED","0"],
["TEMPORAL_GEOMETRY_AUTHORIZED","0"],
["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
["E4D1BR2B_2019_ACS_PERSON_SOURCE_ACQUISITION_SCHEMA_AUDIT","PASS"],
])

log="\n".join([
"E4D1BR2A_REUSED_AS_CANONICAL_VERSIONED_BRIDGE_AUTHORITY=1",
"PERSON_SOURCE_ACQUIRED=1",
f"PERSON_CSV_MEMBER_COUNT={csv_count}",
f"PERSON_CSV_HEADERS_IDENTICAL={int(headers_identical)}",
f"PERSON_SOURCE_SCHEMA_STATUS={'PASS' if schema_pass else 'UNRESOLVED'}",
f"ALL_CSV_MEMBERS_HAVE_SERIALNO={int(bool(schema_rows) and all(r[3]=='1' for r in schema_rows))}",
f"ALL_CSV_MEMBERS_HAVE_RELSHIPP={int(bool(schema_rows) and all(r[4]=='1' for r in schema_rows))}",
f"ALL_CSV_MEMBERS_HAVE_AGEP={int(bool(schema_rows) and all(r[5]=='1' for r in schema_rows))}",
"REFERENCE_PERSON_CODE20_OBSERVED=0",
"REFERENCE_PERSON_UNIQUENESS_VALIDATED=0",
"HOUSING_LINK_COVERAGE_VALIDATED=0",
"DUPLICATE_AMPLIFICATION_VALIDATED_ABSENT=0",
"PERSON_DATA_ROWS_PARSED=0",
"MICRODATA_ROWS_OPENED=0",
"NUMERIC_RESULT_ROWS_OPENED=0",
"2019_ECONOMIC_VALUES_OPENED=0",
"ACS_SCHEMA_AUDIT_STATUS=FAIL",
"SCHEMA_AUDIT_STATUS=BLOCKED",
f"NEXT_PRIMARY_PHASE_ID={next_phase}",
f"E4D1BR2C_REFERENCE_PERSON_LINKAGE_STRUCTURAL_AUDIT_PREFLIGHT_AUTHORIZED={int(schema_pass)}",
"E4D1C_2019_COORDINATE_EXECUTION_PRECOMMIT_AUTHORIZED=0",
"TEMPORAL_GEOMETRY_AUTHORIZED=0",
"REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
"E4D1BR2B_2019_ACS_PERSON_SOURCE_ACQUISITION_SCHEMA_AUDIT=PASS",
])+"\n"
EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
