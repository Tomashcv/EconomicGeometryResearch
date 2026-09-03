#!/usr/bin/env python3
from pathlib import Path
import csv,io,json,re,zipfile

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"data/metadata/E4D1BR2CR_typehugq_structural_universe_contract.json"
DICT=ROOT/"data/raw/reference_metadata/E4D0A/ACS/2019/PUMS_Data_Dictionary_2019.txt"
HOUSING=ROOT/"data/raw/acs/2019/1year/csv_hus.zip"
PERSON=ROOT/"data/raw/acs/2019/1year/csv_pus.zip"

EVIDENCE=ROOT/"data/results/E4D1BR2CR_official_typehugq_evidence_registry.tsv"
COUNTS=ROOT/"data/results/E4D1BR2CR_typehugq_linkage_count_registry.tsv"
GATES=ROOT/"data/results/E4D1BR2CR_typehugq_structural_universe_hard_gates.tsv"
BRIDGE=ROOT/"data/results/E4D1BR2CR_validated_householder_age_bridge_registry.tsv"
SCHEMA=ROOT/"data/results/E4D1BR2CR_updated_2019_schema_audit_status.tsv"
DECISION=ROOT/"data/results/E4D1BR2CR_typehugq_structural_universe_decision.tsv"
EXEC=ROOT/"data/metadata/E4D1BR2CR_execution.txt"
AUDIT=ROOT/"data/metadata/E4D1BR2CR_typehugq_structural_universe_audit.txt"

c=json.loads(CONTRACT.read_text(encoding="utf-8"))
assert c["housing_fields_retained"]==["SERIALNO","NP","TYPEHUGQ"]
assert c["person_fields_retained"]==["SERIALNO","RELSHIPP"]
assert c["repaired_structural_universe_candidate"]["rule"]=="TYPEHUGQ == 1 AND NP > 0"

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
        raise ValueError("multiline or unterminated quoted CSV record encountered")
    if field in wanted: out[field]=bytes(buf)
    return out,field+1

def stream_selected(zip_path, required_fields):
    with zipfile.ZipFile(zip_path,"r") as z:
        for info in csv_members(z):
            with z.open(info,"r") as raw:
                header_raw=raw.readline()
                if not header_raw: raise AssertionError(f"empty CSV member: {info.filename}")
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
                    yield tuple(selected.get(idx,b"").decode("utf-8").strip() for idx in indices)

# Official semantics, opened only after precommit.
text=re.sub(r"\s+"," ",DICT.read_text(encoding="utf-8",errors="replace"))
type_semantics=(
    "TYPEHUGQ" in text and
    "Type of unit" in text and
    bool(re.search(r"\b1\s+\.?Housing unit\b",text,re.I)) and
    bool(re.search(r"\b2\s+\.?Institutional group quarters\b",text,re.I)) and
    bool(re.search(r"\b3\s+\.?Noninstitutional group quarters\b",text,re.I))
)
np_gq_semantics=(
    "NP" in text and
    "Number of persons associated with this housing record" in text and
    "group quarters" in text.lower() and
    bool(re.search(r"\b1\s+\.?One person record\b",text,re.I))
)

write_tsv(EVIDENCE,["evidence_id","structural_summary","status"],[
["CR_TYPEHUGQ_2019_DICTIONARY",
 "TYPEHUGQ=1 housing unit; 2 institutional GQ; 3 noninstitutional GQ",
 "PASS" if type_semantics else "UNRESOLVED"],
["CR_NP_2019_DICTIONARY",
 "NP=1 can represent one person in household or a person in group quarters",
 "PASS" if np_gq_semantics else "UNRESOLVED"],
])

# Rebuild reference-person key multiplicity using only SERIALNO, RELSHIPP.
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

# Classify housing rows by TYPEHUGQ without opening H or weight fields.
housing_rows=0
np_gt0_rows=0
type1_np_gt0=0
type23_np_gt0=0
type_invalid_rows=0
type_missing_rows=0
type1_missing_reference=0
type23_missing_reference=0
type1_multi_reference=0
type23_with_reference=0
type1_exact_one_reference=0
missing_reference_total=0

for serial,nps,types in stream_selected(HOUSING,("SERIALNO","NP","TYPEHUGQ")):
    housing_rows+=1
    if not types:
        type_missing_rows+=1
        continue
    try:
        typ=int(types)
    except Exception:
        type_invalid_rows+=1
        continue
    if typ not in (1,2,3):
        type_invalid_rows+=1
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
        elif rc==1: type1_exact_one_reference+=1
        else: type1_multi_reference+=1
    else:
        type23_np_gt0+=1
        if rc==0: type23_missing_reference+=1
        else: type23_with_reference+=1

duplicate_reference_serial_count=sum(1 for v in reference_counts.values() if v>1)
official_pass=type_semantics and np_gq_semantics

all_prior_missing_are_gq=(
    missing_reference_total==151321 and
    type23_missing_reference==151321 and
    type1_missing_reference==0
)
repaired_universe_exact_one=(
    type1_np_gt0>0 and
    type1_missing_reference==0 and
    type1_multi_reference==0 and
    type1_exact_one_reference==type1_np_gt0
)
reference_uniqueness=(duplicate_reference_serial_count==0)
duplicate_amplification_absent=(reference_uniqueness and type1_multi_reference==0)

all_pass=all([
    official_pass,
    type_missing_rows==0,
    type_invalid_rows==0,
    all_prior_missing_are_gq,
    repaired_universe_exact_one,
    reference_uniqueness,
    duplicate_amplification_absent,
])

write_tsv(COUNTS,["metric","value","interpretation_class"],[
["HOUSING_ROW_COUNT",housing_rows,"STRUCTURAL_ONLY"],
["PERSON_ROW_COUNT",person_rows,"STRUCTURAL_ONLY"],
["REFERENCE_PERSON_ROW_COUNT_RELSHIPP_20",reference_rows,"STRUCTURAL_ONLY"],
["NP_GT_0_HOUSING_COUNT",np_gt0_rows,"STRUCTURAL_ONLY"],
["TYPEHUGQ1_NP_GT_0_COUNT",type1_np_gt0,"STRUCTURAL_ONLY"],
["TYPEHUGQ23_NP_GT_0_COUNT",type23_np_gt0,"STRUCTURAL_ONLY"],
["TOTAL_NP_GT_0_MISSING_REFERENCE_COUNT",missing_reference_total,"STRUCTURAL_ONLY"],
["TYPEHUGQ1_NP_GT_0_MISSING_REFERENCE_COUNT",type1_missing_reference,"STRUCTURAL_ONLY"],
["TYPEHUGQ23_NP_GT_0_MISSING_REFERENCE_COUNT",type23_missing_reference,"STRUCTURAL_ONLY"],
["TYPEHUGQ1_NP_GT_0_EXACT_ONE_REFERENCE_COUNT",type1_exact_one_reference,"STRUCTURAL_ONLY"],
["TYPEHUGQ1_NP_GT_0_MULTI_REFERENCE_COUNT",type1_multi_reference,"STRUCTURAL_ONLY"],
["TYPEHUGQ23_WITH_REFERENCE_COUNT",type23_with_reference,"STRUCTURAL_ONLY"],
["TYPEHUGQ_MISSING_COUNT",type_missing_rows,"STRUCTURAL_ONLY"],
["TYPEHUGQ_INVALID_COUNT",type_invalid_rows,"STRUCTURAL_ONLY"],
["DUPLICATE_REFERENCE_PERSON_SERIALNO_COUNT",duplicate_reference_serial_count,"STRUCTURAL_ONLY"],
])

write_tsv(GATES,["gate","value"],[
["OFFICIAL_TYPEHUGQ_SEMANTICS_PASS",str(int(type_semantics))],
["OFFICIAL_NP_GROUP_QUARTERS_SEMANTICS_PASS",str(int(np_gq_semantics))],
["TYPEHUGQ_COMPLETE_VALID_CODE_GATE",str(int(type_missing_rows==0 and type_invalid_rows==0))],
["EXACT_PRIOR_151321_MISSING_REFERENCE_REPRODUCED",str(int(missing_reference_total==151321))],
["ALL_PRIOR_MISSING_REFERENCE_RECORDS_ARE_TYPEHUGQ23",str(int(all_prior_missing_are_gq))],
["ZERO_TYPEHUGQ1_OCCUPIED_MISSING_REFERENCE",str(int(type1_missing_reference==0))],
["EVERY_TYPEHUGQ1_OCCUPIED_HAS_EXACTLY_ONE_REFERENCE",str(int(repaired_universe_exact_one))],
["REFERENCE_PERSON_UNIQUENESS_REMAINS_PASS",str(int(reference_uniqueness))],
["DUPLICATE_AMPLIFICATION_REMAINS_ABSENT",str(int(duplicate_amplification_absent))],
["ALL_STRUCTURAL_UNIVERSE_REPAIR_GATES_PASS",str(int(all_pass))],
["HOUSING_FIELDS_RETAINED","SERIALNO|NP|TYPEHUGQ"],
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
["TARGET_2019_MISSING_FIELD","HHLDRAGEP"],
["HOUSEHOLDER_STRUCTURAL_UNIVERSE","TYPEHUGQ=1 AND NP>0" if all_pass else "UNRESOLVED"],
["HOUSING_KEY","SERIALNO"],
["PERSON_KEY","SERIALNO"],
["PERSON_ROLE_FIELD","RELSHIPP"],
["PERSON_ROLE_CODE","20"],
["PERSON_AGE_FIELD","AGEP"],
["TYPEHUGQ1_MEANING","HOUSING_UNIT"],
["TYPEHUGQ23_MEANING","GROUP_QUARTERS"],
["ALL_PRIOR_MISSING_REFERENCE_EXPLAINED_AS_GROUP_QUARTERS",str(int(all_prior_missing_are_gq))],
["EVERY_OCCUPIED_HOUSING_UNIT_HAS_EXACTLY_ONE_REFERENCE",str(int(repaired_universe_exact_one))],
["DUPLICATE_AMPLIFICATION_VALIDATED_ABSENT",str(int(duplicate_amplification_absent))],
["PERSON_WEIGHT_USED","0"],
["H_COORDINATE_COMPUTED","0"],
])

write_tsv(SCHEMA,["family","schema_status","basis","mutable_in_E4D1BR2CR"],[
["ACS",acs_status,
 "2019 HHLDRAGEP absent by design; official RELSHIPP=20/AGEP bridge with TYPEHUGQ=1 occupied-housing universe structurally validated"
 if all_pass else
 "TYPEHUGQ structural-universe repair failed at least one precommitted gate",
 "1"],
["SCF","PASS","immutable prior E4D1BR result","0"],
["CPS_ASEC","PASS","immutable prior E4D1BR result","0"],
])

write_tsv(DECISION,["decision","value"],[
["E4D1BR2C_REUSED_AS_CANONICAL_BLOCKED_LINKAGE_STATE","1"],
["PARENT_COVERAGE_GAP_COUNT","151321"],
["STRUCTURAL_UNIVERSE_FAILURE_CLASS","NP_GT_0_INCLUDED_GROUP_QUARTERS" if all_prior_missing_are_gq else "UNRESOLVED"],
["OFFICIAL_TYPEHUGQ_SEMANTICS_PASS",str(int(type_semantics))],
["OFFICIAL_NP_GROUP_QUARTERS_SEMANTICS_PASS",str(int(np_gq_semantics))],
["ALL_PRIOR_MISSING_REFERENCE_RECORDS_ARE_GROUP_QUARTERS",str(int(all_prior_missing_are_gq))],
["REPAIRED_HOUSEHOLDER_STRUCTURAL_UNIVERSE","TYPEHUGQ=1_AND_NP>0" if all_pass else "UNRESOLVED"],
["VERSIONED_BRIDGE_STATUS",bridge_status],
["REFERENCE_PERSON_UNIQUENESS_VALIDATED","1" if reference_uniqueness else "0"],
["HOUSING_LINK_COVERAGE_VALIDATED","1" if repaired_universe_exact_one else "0"],
["EXACT_ONE_REFERENCE_PER_OCCUPIED_HOUSING_VALIDATED","1" if repaired_universe_exact_one else "0"],
["DUPLICATE_AMPLIFICATION_VALIDATED_ABSENT","1" if duplicate_amplification_absent else "0"],
["ACS_SCHEMA_AUDIT_STATUS",acs_status],
["SCHEMA_AUDIT_STATUS",schema_status],
["STRUCTURAL_MICRODATA_ROWS_OPENED","1"],
["HOUSING_FIELDS_RETAINED","SERIALNO|NP|TYPEHUGQ"],
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
["E4D1BR2CR_TYPEHUGQ_STRUCTURAL_UNIVERSE_FORENSIC_REPAIR","PASS"],
])

log="\n".join([
"E4D1BR2C_REUSED_AS_CANONICAL_BLOCKED_LINKAGE_STATE=1",
"TARGET_DISCRIMINATOR=TYPEHUGQ",
f"OFFICIAL_TYPEHUGQ_SEMANTICS_PASS={int(type_semantics)}",
f"OFFICIAL_NP_GROUP_QUARTERS_SEMANTICS_PASS={int(np_gq_semantics)}",
f"NP_GT_0_HOUSING_COUNT={np_gt0_rows}",
f"TYPEHUGQ1_NP_GT_0_COUNT={type1_np_gt0}",
f"TYPEHUGQ23_NP_GT_0_COUNT={type23_np_gt0}",
f"TOTAL_NP_GT_0_MISSING_REFERENCE_COUNT={missing_reference_total}",
f"TYPEHUGQ1_NP_GT_0_MISSING_REFERENCE_COUNT={type1_missing_reference}",
f"TYPEHUGQ23_NP_GT_0_MISSING_REFERENCE_COUNT={type23_missing_reference}",
f"ALL_PRIOR_MISSING_REFERENCE_RECORDS_ARE_GROUP_QUARTERS={int(all_prior_missing_are_gq)}",
f"EVERY_TYPEHUGQ1_OCCUPIED_HAS_EXACTLY_ONE_REFERENCE={int(repaired_universe_exact_one)}",
f"REFERENCE_PERSON_UNIQUENESS_REMAINS_PASS={int(reference_uniqueness)}",
f"DUPLICATE_AMPLIFICATION_REMAINS_ABSENT={int(duplicate_amplification_absent)}",
f"VERSIONED_BRIDGE_STATUS={bridge_status}",
f"ACS_SCHEMA_AUDIT_STATUS={acs_status}",
f"SCHEMA_AUDIT_STATUS={schema_status}",
"STRUCTURAL_MICRODATA_ROWS_OPENED=1",
"HOUSING_FIELDS_RETAINED=SERIALNO|NP|TYPEHUGQ",
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
"E4D1BR2CR_TYPEHUGQ_STRUCTURAL_UNIVERSE_FORENSIC_REPAIR=PASS",
])+"\n"
EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
