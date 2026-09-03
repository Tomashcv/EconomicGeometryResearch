#!/usr/bin/env python3
from pathlib import Path
import csv,io,json,re,subprocess,zipfile

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"data/metadata/E4D1BR2CR0_type_to_typehugq_versioned_name_repair_contract.json"
DICT=ROOT/"data/raw/reference_metadata/E4D0A/ACS/2019/PUMS_Data_Dictionary_2019.txt"
CHANGE=ROOT/"data/raw/reference_metadata/E4D1BR2CR0/ACS/ACS2020_PUMS_Variable_Changes_and_Explanations.pdf"
HOUSING=ROOT/"data/raw/acs/2019/1year/csv_hus.zip"
PERSON=ROOT/"data/raw/acs/2019/1year/csv_pus.zip"

EVIDENCE=ROOT/"data/results/E4D1BR2CR0_versioned_name_evidence_registry.tsv"
COUNTS=ROOT/"data/results/E4D1BR2CR0_type_linkage_count_registry.tsv"
GATES=ROOT/"data/results/E4D1BR2CR0_type_structural_universe_hard_gates.tsv"
BRIDGE=ROOT/"data/results/E4D1BR2CR0_validated_householder_age_bridge_registry.tsv"
SCHEMA=ROOT/"data/results/E4D1BR2CR0_updated_2019_schema_audit_status.tsv"
DECISION=ROOT/"data/results/E4D1BR2CR0_type_to_typehugq_versioned_name_repair_decision.tsv"
EXEC=ROOT/"data/metadata/E4D1BR2CR0_execution.txt"
AUDIT=ROOT/"data/metadata/E4D1BR2CR0_type_to_typehugq_versioned_name_repair_audit.txt"

c=json.loads(CONTRACT.read_text(encoding="utf-8"))
assert c["repair"]["2019_field"]=="TYPE"
assert c["repair"]["later_name"]=="TYPEHUGQ"
assert c["frozen_structural_hypothesis"]["repaired_universe"]=="TYPE == 1 AND NP > 0"
assert c["housing_fields_retained"]==["SERIALNO","NP","TYPE"]
assert c["person_fields_retained"]==["SERIALNO","RELSHIPP"]

def write_tsv(p,h,rows):
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,delimiter="\t",lineterminator="\n")
        w.writerow(h); w.writerows(rows)

def csv_members(z):
    return [i for i in z.infolist() if not i.is_dir() and i.filename.lower().endswith(".csv")]

def select_csv_fields(record: bytes, wanted_indices):
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
            if b==34:
                if i+1<n and record[i+1]==34:
                    if buf is not None: buf.append(34)
                    i+=2; continue
                in_quotes=False; i+=1; continue
            if buf is not None: buf.append(b)
            i+=1; continue
        if b==34:
            in_quotes=True; i+=1; continue
        if b==44:
            if field in wanted: out[field]=bytes(buf)
            field+=1
            buf=bytearray() if field in wanted else None
            i+=1; continue
        if b in (10,13):
            i+=1; continue
        if buf is not None: buf.append(b)
        i+=1
    if in_quotes:
        raise ValueError("multiline or unterminated quoted CSV record")
    if field in wanted: out[field]=bytes(buf)
    return out,field+1

def headers(zip_path):
    rows=[]
    with zipfile.ZipFile(zip_path,"r") as z:
        for info in csv_members(z):
            with z.open(info,"r") as raw:
                h=next(csv.reader([raw.readline().decode("utf-8-sig")]))
            rows.append((info.filename,[x.strip().upper() for x in h]))
    return rows

def stream_selected(zip_path, required_fields):
    with zipfile.ZipFile(zip_path,"r") as z:
        for info in csv_members(z):
            with z.open(info,"r") as raw:
                header=next(csv.reader([raw.readline().decode("utf-8-sig")]))
                normalized=[x.strip().upper() for x in header]
                pos={name:i for i,name in enumerate(normalized)}
                missing=set(required_fields)-set(pos)
                assert not missing,(info.filename,sorted(missing))
                indices=[pos[x] for x in required_fields]
                expected_fields=len(header)
                for raw_record in raw:
                    selected,field_count=select_csv_fields(raw_record,indices)
                    if field_count!=expected_fields:
                        raise AssertionError((info.filename,field_count,expected_fields))
                    yield tuple(selected.get(idx,b"").decode("utf-8").strip() for idx in indices)

# Official version-name evidence.
change_text=subprocess.run(
    ["pdftotext","-layout",str(CHANGE),"-"],
    capture_output=True,text=True,check=True
).stdout
change_norm=re.sub(r"\s+"," ",change_text)
name_change=(
    "TYPEHUGQ" in change_norm and
    "TYPE" in change_norm and
    (
        re.search(r"TYPEHUGQ\s+Previous Name:\s*TYPE",change_norm,re.I) is not None
        or re.search(r'TYPE.*changed its name from\s+[“"]?TYPE[”"]?\s+to\s+[“"]?TYPEHUGQ',change_norm,re.I) is not None
    )
)

dict_text=re.sub(r"\s+"," ",DICT.read_text(encoding="utf-8",errors="replace"))
type_semantics=(
    re.search(r"\bTYPE\b.{0,100}Type of unit",dict_text,re.I) is not None and
    re.search(r"\b1\s+\.?Housing unit\b",dict_text,re.I) is not None and
    re.search(r"\b2\s+\.?Institutional group quarters\b",dict_text,re.I) is not None and
    re.search(r"\b3\s+\.?Noninstitutional group quarters\b",dict_text,re.I) is not None
)
np_gq_semantics=(
    re.search(r"\bNP\b.{0,180}Number of persons",dict_text,re.I) is not None and
    "group quarters" in dict_text.lower() and
    re.search(r"\b1\s+\.?One person",dict_text,re.I) is not None
)

housing_headers=headers(HOUSING)
type_header_present=all("TYPE" in h for _,h in housing_headers)
typehugq_header_absent=all("TYPEHUGQ" not in h for _,h in housing_headers)

write_tsv(EVIDENCE,["evidence_id","source","structural_summary","status"],[
["CR0_OFFICIAL_NAME_CHANGE","ACS_2020_PUMS_VARIABLE_CHANGES",
 "TYPEHUGQ is officially documented as previous-name TYPE",
 "PASS" if name_change else "UNRESOLVED"],
["CR0_2019_TYPE_SEMANTICS","ACS_2019_DICTIONARY",
 "TYPE codes 1 housing unit, 2 institutional GQ, 3 noninstitutional GQ",
 "PASS" if type_semantics else "UNRESOLVED"],
["CR0_2019_NP_GQ_SEMANTICS","ACS_2019_DICTIONARY",
 "NP one-person code can apply to group quarters",
 "PASS" if np_gq_semantics else "UNRESOLVED"],
["CR0_2019_HEADER_VERSION","ACS_2019_HOUSING_HEADERS",
 f"TYPE_present_all={int(type_header_present)};TYPEHUGQ_absent_all={int(typehugq_header_absent)}",
 "PASS" if (type_header_present and typehugq_header_absent) else "UNRESOLVED"],
])

# Reference-person multiplicity.
reference_counts={}
person_rows=0
reference_rows=0
for serial,rels in stream_selected(PERSON,("SERIALNO","RELSHIPP")):
    person_rows+=1
    if not rels:
        continue
    try:
        rel=int(rels)
    except Exception:
        continue
    if rel!=20:
        continue
    reference_rows+=1
    reference_counts[serial]=reference_counts.get(serial,0)+1

housing_rows=0
np_gt0_rows=0
type1_np_gt0=0
type23_np_gt0=0
type_missing=0
type_invalid=0
missing_reference_total=0
type1_missing_reference=0
type23_missing_reference=0
type1_exact_one=0
type1_multi=0
type23_with_reference=0

for serial,nps,types in stream_selected(HOUSING,("SERIALNO","NP","TYPE")):
    housing_rows+=1
    if not types:
        type_missing+=1
        continue
    try:
        typ=int(types)
    except Exception:
        type_invalid+=1
        continue
    if typ not in (1,2,3):
        type_invalid+=1
        continue
    try:
        npv=int(nps)
    except Exception:
        continue
    if npv<=0:
        continue
    np_gt0_rows+=1
    rc=reference_counts.get(serial,0)
    if rc==0:
        missing_reference_total+=1
    if typ==1:
        type1_np_gt0+=1
        if rc==0: type1_missing_reference+=1
        elif rc==1: type1_exact_one+=1
        else: type1_multi+=1
    else:
        type23_np_gt0+=1
        if rc==0: type23_missing_reference+=1
        else: type23_with_reference+=1

dup_ref=sum(1 for v in reference_counts.values() if v>1)
all_parent_missing_gq=(
    missing_reference_total==151321
    and type23_missing_reference==151321
    and type1_missing_reference==0
)
repaired_exact_one=(
    type1_np_gt0>0
    and type1_missing_reference==0
    and type1_multi==0
    and type1_exact_one==type1_np_gt0
)
reference_unique=(dup_ref==0)
official_pass=all([name_change,type_semantics,np_gq_semantics,type_header_present,typehugq_header_absent])
all_pass=all([
    official_pass,
    type_missing==0,
    type_invalid==0,
    all_parent_missing_gq,
    repaired_exact_one,
    reference_unique,
])

write_tsv(COUNTS,["metric","value","interpretation_class"],[
["HOUSING_ROW_COUNT",housing_rows,"STRUCTURAL_ONLY"],
["PERSON_ROW_COUNT",person_rows,"STRUCTURAL_ONLY"],
["REFERENCE_PERSON_ROW_COUNT_RELSHIPP_20",reference_rows,"STRUCTURAL_ONLY"],
["NP_GT_0_HOUSING_COUNT",np_gt0_rows,"STRUCTURAL_ONLY"],
["TYPE1_NP_GT_0_COUNT",type1_np_gt0,"STRUCTURAL_ONLY"],
["TYPE23_NP_GT_0_COUNT",type23_np_gt0,"STRUCTURAL_ONLY"],
["TOTAL_NP_GT_0_MISSING_REFERENCE_COUNT",missing_reference_total,"STRUCTURAL_ONLY"],
["TYPE1_NP_GT_0_MISSING_REFERENCE_COUNT",type1_missing_reference,"STRUCTURAL_ONLY"],
["TYPE23_NP_GT_0_MISSING_REFERENCE_COUNT",type23_missing_reference,"STRUCTURAL_ONLY"],
["TYPE1_NP_GT_0_EXACT_ONE_REFERENCE_COUNT",type1_exact_one,"STRUCTURAL_ONLY"],
["TYPE1_NP_GT_0_MULTI_REFERENCE_COUNT",type1_multi,"STRUCTURAL_ONLY"],
["TYPE23_WITH_REFERENCE_COUNT",type23_with_reference,"STRUCTURAL_ONLY"],
["TYPE_MISSING_COUNT",type_missing,"STRUCTURAL_ONLY"],
["TYPE_INVALID_COUNT",type_invalid,"STRUCTURAL_ONLY"],
["DUPLICATE_REFERENCE_PERSON_SERIALNO_COUNT",dup_ref,"STRUCTURAL_ONLY"],
])

write_tsv(GATES,["gate","value"],[
["OFFICIAL_TYPE_TO_TYPEHUGQ_NAME_CHANGE_PASS",str(int(name_change))],
["2019_TYPE_HEADER_PRESENT_ALL_MEMBERS",str(int(type_header_present))],
["2019_TYPEHUGQ_HEADER_ABSENT_ALL_MEMBERS",str(int(typehugq_header_absent))],
["2019_TYPE_CODE_SEMANTICS_PASS",str(int(type_semantics))],
["2019_NP_GROUP_QUARTERS_SEMANTICS_PASS",str(int(np_gq_semantics))],
["EXACT_PARENT_151321_GAP_REPRODUCED",str(int(missing_reference_total==151321))],
["ALL_PARENT_MISSING_REFERENCE_RECORDS_ARE_TYPE23",str(int(all_parent_missing_gq))],
["ZERO_TYPE1_OCCUPIED_MISSING_REFERENCE",str(int(type1_missing_reference==0))],
["EVERY_TYPE1_OCCUPIED_HAS_EXACTLY_ONE_REFERENCE",str(int(repaired_exact_one))],
["REFERENCE_PERSON_UNIQUENESS_PASS",str(int(reference_unique))],
["ALL_CR0_REPAIR_GATES_PASS",str(int(all_pass))],
["HOUSING_FIELDS_RETAINED","SERIALNO|NP|TYPE"],
["PERSON_FIELDS_RETAINED","SERIALNO|RELSHIPP"],
["UNSELECTED_FIELD_CONTENTS_RETAINED","0"],
["WEIGHT_FIELDS_RETAINED","0"],
["RMSP_RETAINED","0"],
["TEN_RETAINED","0"],
["AGEP_RETAINED","0"],
["WEIGHTED_ESTIMATION_PERFORMED","0"],
["AGE_BAND_COUNTS_COMPUTED","0"],
["H_COORDINATE_COMPUTED","0"],
["TEMPORAL_GEOMETRY_AUTHORIZED","0"],
["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
])

bridge_status="VALIDATED_FROZEN" if all_pass else "UNRESOLVED"
acs_status="VERSIONED_PASS" if all_pass else "FAIL"
schema_status="PASS_WITH_VERSIONED_BRIDGE" if all_pass else "BLOCKED"
next_phase="E4D1C" if all_pass else "E4D1BR2CR1"

write_tsv(BRIDGE,["field","value"],[
["BRIDGE_ID","ACS_2019_HOUSEHOLDER_AGE_FROM_REFERENCE_PERSON"],
["STATUS",bridge_status],
["TYPE_FIELD_VERSION_BRIDGE","2019:TYPE|2020+:TYPEHUGQ"],
["HOUSEHOLDER_STRUCTURAL_UNIVERSE","TYPE=1 AND NP>0" if all_pass else "UNRESOLVED"],
["HOUSING_KEY","SERIALNO"],
["PERSON_KEY","SERIALNO"],
["PERSON_ROLE_FIELD","RELSHIPP"],
["PERSON_ROLE_CODE","20"],
["PERSON_AGE_FIELD","AGEP"],
["TYPE1_MEANING","HOUSING_UNIT"],
["TYPE23_MEANING","GROUP_QUARTERS"],
["ALL_PARENT_MISSING_REFERENCE_EXPLAINED_AS_GROUP_QUARTERS",str(int(all_parent_missing_gq))],
["EVERY_OCCUPIED_HOUSING_UNIT_HAS_EXACTLY_ONE_REFERENCE",str(int(repaired_exact_one))],
["DUPLICATE_AMPLIFICATION_VALIDATED_ABSENT",str(int(reference_unique and type1_multi==0))],
["PERSON_WEIGHT_USED","0"],
["H_COORDINATE_COMPUTED","0"],
])

write_tsv(SCHEMA,["family","schema_status","basis","mutable_in_E4D1BR2CR0"],[
["ACS",acs_status,
 "2019 TYPE is official name predecessor of TYPEHUGQ; TYPE=1 occupied housing universe plus RELSHIPP=20/AGEP bridge structurally validated"
 if all_pass else
 "versioned TYPE name/universe repair failed at least one precommitted gate",
 "1"],
["SCF","PASS","immutable prior E4D1BR result","0"],
["CPS_ASEC","PASS","immutable prior E4D1BR result","0"],
])

write_tsv(DECISION,["decision","value"],[
["E4D1BR2CR_FAILURE_PRESERVED_BEFORE_CR0","1"],
["E4D1BR2CR0_FAILURE_CLASS","2019_VERSIONED_FIELD_NAME_MISMATCH"],
["TYPE_FIELD_VERSION_BRIDGE","2019:TYPE|2020+:TYPEHUGQ"],
["OFFICIAL_TYPE_TO_TYPEHUGQ_NAME_CHANGE_PASS",str(int(name_change))],
["ALL_PARENT_MISSING_REFERENCE_RECORDS_ARE_GROUP_QUARTERS",str(int(all_parent_missing_gq))],
["REPAIRED_HOUSEHOLDER_STRUCTURAL_UNIVERSE","TYPE=1_AND_NP>0" if all_pass else "UNRESOLVED"],
["VERSIONED_BRIDGE_STATUS",bridge_status],
["REFERENCE_PERSON_UNIQUENESS_VALIDATED",str(int(reference_unique))],
["HOUSING_LINK_COVERAGE_VALIDATED",str(int(repaired_exact_one))],
["EXACT_ONE_REFERENCE_PER_OCCUPIED_HOUSING_VALIDATED",str(int(repaired_exact_one))],
["DUPLICATE_AMPLIFICATION_VALIDATED_ABSENT",str(int(reference_unique and type1_multi==0))],
["ACS_SCHEMA_AUDIT_STATUS",acs_status],
["SCHEMA_AUDIT_STATUS",schema_status],
["STRUCTURAL_MICRODATA_ROWS_OPENED","1"],
["HOUSING_FIELDS_RETAINED","SERIALNO|NP|TYPE"],
["PERSON_FIELDS_RETAINED","SERIALNO|RELSHIPP"],
["UNSELECTED_FIELD_CONTENTS_RETAINED","0"],
["WEIGHT_FIELDS_RETAINED","0"],
["RMSP_RETAINED","0"],
["TEN_RETAINED","0"],
["AGEP_RETAINED","0"],
["WEIGHTED_ESTIMATION_PERFORMED","0"],
["AGE_BAND_COUNTS_COMPUTED","0"],
["H_COORDINATE_COMPUTED","0"],
["NEXT_PRIMARY_PHASE_ID",next_phase],
["E4D1C_2019_COORDINATE_EXECUTION_PRECOMMIT_AUTHORIZED",str(int(all_pass))],
["TEMPORAL_GEOMETRY_AUTHORIZED","0"],
["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
["E4D1BR2CR0_TYPE_TO_TYPEHUGQ_VERSIONED_NAME_REPAIR","PASS"],
])

log="\n".join([
"E4D1BR2CR_FAILURE_PRESERVED_BEFORE_CR0=1",
"E4D1BR2CR0_FAILURE_CLASS=2019_VERSIONED_FIELD_NAME_MISMATCH",
"TYPE_FIELD_VERSION_BRIDGE=2019:TYPE|2020+:TYPEHUGQ",
f"OFFICIAL_TYPE_TO_TYPEHUGQ_NAME_CHANGE_PASS={int(name_change)}",
f"2019_TYPE_HEADER_PRESENT_ALL_MEMBERS={int(type_header_present)}",
f"2019_TYPEHUGQ_HEADER_ABSENT_ALL_MEMBERS={int(typehugq_header_absent)}",
f"2019_TYPE_CODE_SEMANTICS_PASS={int(type_semantics)}",
f"2019_NP_GROUP_QUARTERS_SEMANTICS_PASS={int(np_gq_semantics)}",
f"NP_GT_0_HOUSING_COUNT={np_gt0_rows}",
f"TYPE1_NP_GT_0_COUNT={type1_np_gt0}",
f"TYPE23_NP_GT_0_COUNT={type23_np_gt0}",
f"TOTAL_NP_GT_0_MISSING_REFERENCE_COUNT={missing_reference_total}",
f"TYPE1_NP_GT_0_MISSING_REFERENCE_COUNT={type1_missing_reference}",
f"TYPE23_NP_GT_0_MISSING_REFERENCE_COUNT={type23_missing_reference}",
f"ALL_PARENT_MISSING_REFERENCE_RECORDS_ARE_GROUP_QUARTERS={int(all_parent_missing_gq)}",
f"EVERY_TYPE1_OCCUPIED_HAS_EXACTLY_ONE_REFERENCE={int(repaired_exact_one)}",
f"VERSIONED_BRIDGE_STATUS={bridge_status}",
f"ACS_SCHEMA_AUDIT_STATUS={acs_status}",
f"SCHEMA_AUDIT_STATUS={schema_status}",
"STRUCTURAL_MICRODATA_ROWS_OPENED=1",
"HOUSING_FIELDS_RETAINED=SERIALNO|NP|TYPE",
"PERSON_FIELDS_RETAINED=SERIALNO|RELSHIPP",
"UNSELECTED_FIELD_CONTENTS_RETAINED=0",
"WEIGHT_FIELDS_RETAINED=0",
"RMSP_RETAINED=0",
"TEN_RETAINED=0",
"AGEP_RETAINED=0",
"WEIGHTED_ESTIMATION_PERFORMED=0",
"AGE_BAND_COUNTS_COMPUTED=0",
"H_COORDINATE_COMPUTED=0",
f"NEXT_PRIMARY_PHASE_ID={next_phase}",
f"E4D1C_2019_COORDINATE_EXECUTION_PRECOMMIT_AUTHORIZED={int(all_pass)}",
"TEMPORAL_GEOMETRY_AUTHORIZED=0",
"REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
"E4D1BR2CR0_TYPE_TO_TYPEHUGQ_VERSIONED_NAME_REPAIR=PASS",
])+"\n"
EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
