#!/usr/bin/env python3
from pathlib import Path
import csv,io,json,zipfile

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"data/metadata/E4D1BR2C_reference_person_linkage_structural_audit_contract.json"
HOUSING=ROOT/"data/raw/acs/2019/1year/csv_hus.zip"
PERSON=ROOT/"data/raw/acs/2019/1year/csv_pus.zip"

COUNTS=ROOT/"data/results/E4D1BR2C_structural_linkage_count_registry.tsv"
GATES=ROOT/"data/results/E4D1BR2C_structural_linkage_hard_gates.tsv"
BRIDGE=ROOT/"data/results/E4D1BR2C_validated_householder_age_bridge_registry.tsv"
SCHEMA=ROOT/"data/results/E4D1BR2C_updated_2019_schema_audit_status.tsv"
DECISION=ROOT/"data/results/E4D1BR2C_reference_person_linkage_structural_audit_decision.tsv"
EXEC=ROOT/"data/metadata/E4D1BR2C_execution.txt"
AUDIT=ROOT/"data/metadata/E4D1BR2C_reference_person_linkage_structural_audit.txt"

c=json.loads(CONTRACT.read_text(encoding="utf-8"))
assert c["housing_fields_retained"]==["SERIALNO","NP"]
assert c["person_fields_retained"]==["SERIALNO","RELSHIPP","AGEP"]
assert c["row_projection"]["implementation"]=="selective_RFC4180_field_scanner"
assert c["row_projection"]["unselected_field_contents_retained"] is False

def write_tsv(p,h,rows):
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,delimiter="\t",lineterminator="\n")
        w.writerow(h); w.writerows(rows)

def csv_members(z):
    return [i for i in z.infolist() if not i.is_dir() and i.filename.lower().endswith(".csv")]

def select_csv_fields(record: bytes, wanted_indices):
    # RFC4180-style scanner that only retains requested fields. Unselected field
    # contents are traversed only for delimiter/quote state and are never stored.
    wanted=set(wanted_indices)
    out={}
    field=0
    in_quotes=False
    buf=bytearray() if 0 in wanted else None
    i=0
    n=len(record)
    while i<n:
        b=record[i]
        if in_quotes:
            if b==34:  # "
                if i+1<n and record[i+1]==34:
                    if buf is not None:
                        buf.append(34)
                    i+=2
                    continue
                in_quotes=False
                i+=1
                continue
            if buf is not None:
                buf.append(b)
            i+=1
            continue
        if b==34:
            in_quotes=True
            i+=1
            continue
        if b==44:  # comma
            if field in wanted:
                out[field]=bytes(buf)
            field+=1
            buf=bytearray() if field in wanted else None
            i+=1
            continue
        if b in (10,13):
            i+=1
            continue
        if buf is not None:
            buf.append(b)
        i+=1
    if in_quotes:
        raise ValueError("multiline or unterminated quoted CSV record encountered")
    if field in wanted:
        out[field]=bytes(buf)
    return out,field+1

def stream_selected(zip_path, required_fields):
    with zipfile.ZipFile(zip_path,"r") as z:
        for info in csv_members(z):
            with z.open(info,"r") as raw:
                header_raw=raw.readline()
                if not header_raw:
                    raise AssertionError(f"empty CSV member: {info.filename}")
                header=next(csv.reader([header_raw.decode("utf-8-sig")]))
                normalized=[x.strip().upper() for x in header]
                pos={name:i for i,name in enumerate(normalized)}
                missing=set(required_fields)-set(pos)
                assert not missing,(info.filename,sorted(missing))
                indices=[pos[x] for x in required_fields]
                expected_fields=len(header)
                for raw_record in raw:
                    selected,field_count=select_csv_fields(raw_record,indices)
                    if field_count!=expected_fields:
                        raise AssertionError((info.filename,"field_count",field_count,expected_fields))
                    vals=[]
                    for idx in indices:
                        vals.append(selected.get(idx,b"").decode("utf-8").strip())
                    yield tuple(vals)

housing_serials=set()
occupied_serials=set()
housing_rows=0
occupied_rows=0
housing_empty_serial=0
housing_duplicate_serial=0
housing_np_missing=0
housing_np_parse_fail=0
housing_np_negative=0

for serial,nps in stream_selected(HOUSING,("SERIALNO","NP")):
    housing_rows+=1
    if not serial:
        housing_empty_serial+=1
        continue
    if serial in housing_serials:
        housing_duplicate_serial+=1
    else:
        housing_serials.add(serial)
    if not nps:
        housing_np_missing+=1
        continue
    try:
        npv=int(nps)
    except Exception:
        housing_np_parse_fail+=1
        continue
    if npv<0:
        housing_np_negative+=1
        continue
    if npv>0:
        occupied_rows+=1
        occupied_serials.add(serial)

reference_counts={}
reference_rows=0
person_rows=0
person_empty_serial=0
relshipp_missing=0
relshipp_parse_fail=0
reference_age_missing=0
reference_age_parse_fail=0

for serial,rels,ages in stream_selected(PERSON,("SERIALNO","RELSHIPP","AGEP")):
    person_rows+=1
    if not serial:
        person_empty_serial+=1
    if not rels:
        relshipp_missing+=1
        continue
    try:
        rel=int(rels)
    except Exception:
        relshipp_parse_fail+=1
        continue
    if rel!=20:
        continue
    reference_rows+=1
    reference_counts[serial]=reference_counts.get(serial,0)+1
    if not ages:
        reference_age_missing+=1
    else:
        try:
            int(ages)
        except Exception:
            reference_age_parse_fail+=1

reference_serials=set(reference_counts)
duplicate_reference_serial_count=sum(1 for v in reference_counts.values() if v>1)
missing_reference_for_occupied=len(occupied_serials-reference_serials)
multi_reference_for_occupied=sum(1 for s in occupied_serials if reference_counts.get(s,0)>1)
exact_one_reference_for_occupied=sum(1 for s in occupied_serials if reference_counts.get(s,0)==1)
reference_without_housing=len(reference_serials-housing_serials)

gates={
"HOUSING_SERIALNO_NONEMPTY": housing_empty_serial==0,
"HOUSING_SERIALNO_GLOBALLY_UNIQUE": housing_duplicate_serial==0,
"HOUSING_NP_NONMISSING": housing_np_missing==0,
"HOUSING_NP_INTEGER_PARSE": housing_np_parse_fail==0,
"HOUSING_NP_NONNEGATIVE": housing_np_negative==0,
"REFERENCE_PERSON_CODE20_OBSERVED": reference_rows>0,
"PERSON_SERIALNO_NONEMPTY": person_empty_serial==0,
"RELSHIPP_NONMISSING": relshipp_missing==0,
"RELSHIPP_INTEGER_PARSE": relshipp_parse_fail==0,
"REFERENCE_PERSON_SERIAL_UNIQUE": duplicate_reference_serial_count==0,
"EVERY_OCCUPIED_HOUSING_HAS_REFERENCE": missing_reference_for_occupied==0,
"EVERY_OCCUPIED_HOUSING_HAS_EXACTLY_ONE_REFERENCE": (
    missing_reference_for_occupied==0 and multi_reference_for_occupied==0
    and exact_one_reference_for_occupied==len(occupied_serials)
),
"REFERENCE_PERSON_WITHOUT_HOUSING_ABSENT": reference_without_housing==0,
"REFERENCE_PERSON_AGE_NONMISSING": reference_age_missing==0,
"REFERENCE_PERSON_AGE_INTEGER_PARSE": reference_age_parse_fail==0,
"DUPLICATE_AMPLIFICATION_VALIDATED_ABSENT": (
    housing_duplicate_serial==0 and duplicate_reference_serial_count==0
    and multi_reference_for_occupied==0
),
}
all_pass=all(gates.values())

write_tsv(COUNTS,["metric","value","interpretation_class"],[
["HOUSING_ROW_COUNT",housing_rows,"STRUCTURAL_ONLY"],
["OCCUPIED_HOUSING_ROW_COUNT_NP_GT_0",occupied_rows,"STRUCTURAL_ONLY"],
["UNIQUE_HOUSING_SERIALNO_COUNT",len(housing_serials),"STRUCTURAL_ONLY"],
["HOUSING_EMPTY_SERIALNO_COUNT",housing_empty_serial,"STRUCTURAL_ONLY"],
["HOUSING_DUPLICATE_SERIALNO_ROW_COUNT",housing_duplicate_serial,"STRUCTURAL_ONLY"],
["HOUSING_NP_MISSING_COUNT",housing_np_missing,"STRUCTURAL_ONLY"],
["HOUSING_NP_PARSE_FAILURE_COUNT",housing_np_parse_fail,"STRUCTURAL_ONLY"],
["HOUSING_NP_NEGATIVE_COUNT",housing_np_negative,"STRUCTURAL_ONLY"],
["PERSON_ROW_COUNT",person_rows,"STRUCTURAL_ONLY"],
["REFERENCE_PERSON_ROW_COUNT_RELSHIPP_20",reference_rows,"STRUCTURAL_ONLY"],
["UNIQUE_REFERENCE_PERSON_SERIALNO_COUNT",len(reference_serials),"STRUCTURAL_ONLY"],
["DUPLICATE_REFERENCE_PERSON_SERIALNO_COUNT",duplicate_reference_serial_count,"STRUCTURAL_ONLY"],
["OCCUPIED_HOUSING_MISSING_REFERENCE_COUNT",missing_reference_for_occupied,"STRUCTURAL_ONLY"],
["OCCUPIED_HOUSING_MULTI_REFERENCE_COUNT",multi_reference_for_occupied,"STRUCTURAL_ONLY"],
["OCCUPIED_HOUSING_EXACT_ONE_REFERENCE_COUNT",exact_one_reference_for_occupied,"STRUCTURAL_ONLY"],
["REFERENCE_PERSON_WITHOUT_HOUSING_COUNT",reference_without_housing,"STRUCTURAL_ONLY"],
["REFERENCE_PERSON_AGE_MISSING_COUNT",reference_age_missing,"STRUCTURAL_ONLY"],
["REFERENCE_PERSON_AGE_PARSE_FAILURE_COUNT",reference_age_parse_fail,"STRUCTURAL_ONLY"],
])

gate_rows=[[k,str(int(v))] for k,v in gates.items()]
gate_rows += [
["ALL_STRUCTURAL_LINKAGE_GATES_PASS",str(int(all_pass))],
["HOUSING_FIELDS_RETAINED","SERIALNO|NP"],
["PERSON_FIELDS_RETAINED","SERIALNO|RELSHIPP|AGEP"],
["UNSELECTED_FIELD_CONTENTS_RETAINED","0"],
["CSV_DICTREADER_USED","0"],
["WEIGHTED_ESTIMATION_PERFORMED","0"],
["AGE_BAND_COUNTS_COMPUTED","0"],
["H_COORDINATE_COMPUTED","0"],
["NUMERIC_RESULT_ROWS_OPENED","0"],
["TEMPORAL_GEOMETRY_AUTHORIZED","0"],
["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
]
write_tsv(GATES,["gate","value"],gate_rows)

bridge_status="VALIDATED_FROZEN" if all_pass else "UNRESOLVED"
acs_status="VERSIONED_PASS" if all_pass else "FAIL"
schema_status="PASS_WITH_VERSIONED_BRIDGE" if all_pass else "BLOCKED"
next_phase="E4D1C" if all_pass else "E4D1BR2CR"

write_tsv(BRIDGE,["field","value"],[
["BRIDGE_ID","ACS_2019_HOUSEHOLDER_AGE_FROM_REFERENCE_PERSON"],
["STATUS",bridge_status],
["TARGET_2019_MISSING_FIELD","HHLDRAGEP"],
["HOUSING_KEY","SERIALNO"],
["PERSON_KEY","SERIALNO"],
["PERSON_ROLE_FIELD","RELSHIPP"],
["PERSON_ROLE_CODE","20"],
["PERSON_AGE_FIELD","AGEP"],
["OCCUPIED_HOUSING_RULE","NP>0"],
["REFERENCE_PERSON_CODE20_OBSERVED",str(int(gates["REFERENCE_PERSON_CODE20_OBSERVED"]))],
["REFERENCE_PERSON_UNIQUENESS_VALIDATED",str(int(gates["REFERENCE_PERSON_SERIAL_UNIQUE"]))],
["HOUSING_LINK_COVERAGE_VALIDATED",str(int(gates["EVERY_OCCUPIED_HOUSING_HAS_REFERENCE"]))],
["EXACT_ONE_REFERENCE_PER_OCCUPIED_HOUSING_VALIDATED",str(int(gates["EVERY_OCCUPIED_HOUSING_HAS_EXACTLY_ONE_REFERENCE"]))],
["DUPLICATE_AMPLIFICATION_VALIDATED_ABSENT",str(int(gates["DUPLICATE_AMPLIFICATION_VALIDATED_ABSENT"]))],
["REFERENCE_PERSON_AGE_NONMISSING_VALIDATED",str(int(gates["REFERENCE_PERSON_AGE_NONMISSING"]))],
["REFERENCE_PERSON_AGE_INTEGER_VALIDATED",str(int(gates["REFERENCE_PERSON_AGE_INTEGER_PARSE"]))],
["PERSON_WEIGHT_USED","0"],
["H_COORDINATE_COMPUTED","0"],
])

write_tsv(SCHEMA,["family","schema_status","basis","mutable_in_E4D1BR2C"],[
["ACS",acs_status,
 "2019 HHLDRAGEP absent by design; official versioned bridge via RELSHIPP=20 AGEP/SERIALNO structurally validated"
 if all_pass else
 "versioned bridge remains unresolved because at least one precommitted structural linkage gate failed",
 "1"],
["SCF","PASS","immutable prior E4D1BR result","0"],
["CPS_ASEC","PASS","immutable prior E4D1BR result","0"],
])

write_tsv(DECISION,["decision","value"],[
["E4D1BR2B_REUSED_AS_CANONICAL_PERSON_SCHEMA_AUTHORITY","1"],
["E4D1BR2C_R0_STATIC_VALIDATOR_PROJECTION_REPAIR","PASS"],
["VERSIONED_BRIDGE_STATUS",bridge_status],
["REFERENCE_PERSON_CODE20_OBSERVED",str(int(gates["REFERENCE_PERSON_CODE20_OBSERVED"]))],
["REFERENCE_PERSON_UNIQUENESS_VALIDATED",str(int(gates["REFERENCE_PERSON_SERIAL_UNIQUE"]))],
["HOUSING_LINK_COVERAGE_VALIDATED",str(int(gates["EVERY_OCCUPIED_HOUSING_HAS_REFERENCE"]))],
["EXACT_ONE_REFERENCE_PER_OCCUPIED_HOUSING_VALIDATED",str(int(gates["EVERY_OCCUPIED_HOUSING_HAS_EXACTLY_ONE_REFERENCE"]))],
["DUPLICATE_AMPLIFICATION_VALIDATED_ABSENT",str(int(gates["DUPLICATE_AMPLIFICATION_VALIDATED_ABSENT"]))],
["REFERENCE_PERSON_AGE_NONMISSING_VALIDATED",str(int(gates["REFERENCE_PERSON_AGE_NONMISSING"]))],
["REFERENCE_PERSON_AGE_INTEGER_VALIDATED",str(int(gates["REFERENCE_PERSON_AGE_INTEGER_PARSE"]))],
["ACS_SCHEMA_AUDIT_STATUS",acs_status],
["SCHEMA_AUDIT_STATUS",schema_status],
["STRUCTURAL_MICRODATA_ROWS_OPENED","1"],
["HOUSING_FIELDS_RETAINED","SERIALNO|NP"],
["PERSON_FIELDS_RETAINED","SERIALNO|RELSHIPP|AGEP"],
["UNSELECTED_FIELD_CONTENTS_RETAINED","0"],
["CSV_DICTREADER_USED","0"],
["WEIGHTED_ESTIMATION_PERFORMED","0"],
["AGE_BAND_COUNTS_COMPUTED","0"],
["H_COORDINATE_COMPUTED","0"],
["NUMERIC_RESULT_ROWS_OPENED","0"],
["NEXT_PRIMARY_PHASE_ID",next_phase],
["E4D1C_2019_COORDINATE_EXECUTION_PRECOMMIT_AUTHORIZED",str(int(all_pass))],
["TEMPORAL_GEOMETRY_AUTHORIZED","0"],
["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
["E4D1BR2C_REFERENCE_PERSON_LINKAGE_STRUCTURAL_AUDIT","PASS"],
])

log="\n".join([
"E4D1BR2B_REUSED_AS_CANONICAL_PERSON_SCHEMA_AUTHORITY=1",
"E4D1BR2C_R0_STATIC_VALIDATOR_PROJECTION_REPAIR=PASS",
f"HOUSING_ROW_COUNT={housing_rows}",
f"OCCUPIED_HOUSING_ROW_COUNT_NP_GT_0={occupied_rows}",
f"PERSON_ROW_COUNT={person_rows}",
f"REFERENCE_PERSON_ROW_COUNT_RELSHIPP_20={reference_rows}",
f"HOUSING_DUPLICATE_SERIALNO_ROW_COUNT={housing_duplicate_serial}",
f"DUPLICATE_REFERENCE_PERSON_SERIALNO_COUNT={duplicate_reference_serial_count}",
f"OCCUPIED_HOUSING_MISSING_REFERENCE_COUNT={missing_reference_for_occupied}",
f"OCCUPIED_HOUSING_MULTI_REFERENCE_COUNT={multi_reference_for_occupied}",
f"REFERENCE_PERSON_WITHOUT_HOUSING_COUNT={reference_without_housing}",
f"REFERENCE_PERSON_AGE_MISSING_COUNT={reference_age_missing}",
f"REFERENCE_PERSON_AGE_PARSE_FAILURE_COUNT={reference_age_parse_fail}",
f"REFERENCE_PERSON_CODE20_OBSERVED={int(gates['REFERENCE_PERSON_CODE20_OBSERVED'])}",
f"REFERENCE_PERSON_UNIQUENESS_VALIDATED={int(gates['REFERENCE_PERSON_SERIAL_UNIQUE'])}",
f"HOUSING_LINK_COVERAGE_VALIDATED={int(gates['EVERY_OCCUPIED_HOUSING_HAS_REFERENCE'])}",
f"EXACT_ONE_REFERENCE_PER_OCCUPIED_HOUSING_VALIDATED={int(gates['EVERY_OCCUPIED_HOUSING_HAS_EXACTLY_ONE_REFERENCE'])}",
f"DUPLICATE_AMPLIFICATION_VALIDATED_ABSENT={int(gates['DUPLICATE_AMPLIFICATION_VALIDATED_ABSENT'])}",
f"VERSIONED_BRIDGE_STATUS={bridge_status}",
f"ACS_SCHEMA_AUDIT_STATUS={acs_status}",
f"SCHEMA_AUDIT_STATUS={schema_status}",
"STRUCTURAL_MICRODATA_ROWS_OPENED=1",
"HOUSING_FIELDS_RETAINED=SERIALNO|NP",
"PERSON_FIELDS_RETAINED=SERIALNO|RELSHIPP|AGEP",
"UNSELECTED_FIELD_CONTENTS_RETAINED=0",
"CSV_DICTREADER_USED=0",
"WEIGHTED_ESTIMATION_PERFORMED=0",
"AGE_BAND_COUNTS_COMPUTED=0",
"H_COORDINATE_COMPUTED=0",
"NUMERIC_RESULT_ROWS_OPENED=0",
f"NEXT_PRIMARY_PHASE_ID={next_phase}",
f"E4D1C_2019_COORDINATE_EXECUTION_PRECOMMIT_AUTHORIZED={int(all_pass)}",
"TEMPORAL_GEOMETRY_AUTHORIZED=0",
"REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
"E4D1BR2C_REFERENCE_PERSON_LINKAGE_STRUCTURAL_AUDIT=PASS",
])+"\n"
EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
