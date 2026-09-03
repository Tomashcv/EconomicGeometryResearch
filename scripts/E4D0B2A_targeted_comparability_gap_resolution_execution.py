#!/usr/bin/env python3
from pathlib import Path
import csv,hashlib,json,re,sys

ROOT=Path(__file__).resolve().parents[1]

B2_TARGETS=ROOT/"data/metadata/E4D0B2_official_gap_evidence_acquisition_plan.tsv"
B2_PLAN=ROOT/"data/metadata/E4D0B2_gap_resolution_plan.tsv"
B2_BRIDGE=ROOT/"data/results/E4D0B2_k_price_reference_bridge_policy.tsv"
B1_ADJ=ROOT/"data/results/E4D0B1_adjudication_registry.tsv"
B1_RAWVAR=ROOT/"data/results/E4D0B1_frozen_raw_variable_bridge_registry.tsv"
A_MANIFEST=ROOT/"data/results/E4D0A_official_evidence_manifest.tsv"
CONTRACT=ROOT/"data/metadata/E4D0B2A_targeted_comparability_gap_resolution_execution_contract.json"
REFROOT=ROOT/"data/raw/reference_metadata/E4D0B2A"

MANIFEST=ROOT/"data/results/E4D0B2A_targeted_official_evidence_manifest.tsv"
EVIDENCE=ROOT/"data/results/E4D0B2A_gap_resolution_evidence_registry.tsv"
RESOLUTION=ROOT/"data/results/E4D0B2A_gap_resolution_registry.tsv"
ADJ=ROOT/"data/results/E4D0B2A_updated_adjudication_registry.tsv"
BRIDGE=ROOT/"data/results/E4D0B2A_k_price_reference_bridge_freeze.tsv"
GRID=ROOT/"data/results/E4D0B2A_common_time_grid_registry.tsv"
GATES=ROOT/"data/results/E4D0B2A_execution_hard_gates.tsv"
DECISION=ROOT/"data/results/E4D0B2A_targeted_comparability_gap_resolution_decision.tsv"
EXEC=ROOT/"data/metadata/E4D0B2A_execution.txt"
AUDIT=ROOT/"data/metadata/E4D0B2A_targeted_comparability_gap_resolution_execution_audit.txt"

c=json.loads(CONTRACT.read_text(encoding="utf-8"))

with B2_TARGETS.open("r",encoding="utf-8",newline="") as f:
    targets=list(csv.DictReader(f,delimiter="\t"))
assert len(targets)==5

with B2_PLAN.open("r",encoding="utf-8",newline="") as f:
    plan=list(csv.DictReader(f,delimiter="\t"))
assert [int(r["object_index"]) for r in plan]==[4,10,12,28,29,32,37]

with B1_ADJ.open("r",encoding="utf-8",newline="") as f:
    b1=list(csv.DictReader(f,delimiter="\t"))
assert len(b1)==40
assert sum(r["status"]=="PASS" for r in b1)==31
assert sum(r["status"]=="VERSIONED_PASS" for r in b1)==2
assert sum(r["status"]=="FAIL" for r in b1)==0
assert sum(r["status"]=="UNRESOLVED" for r in b1)==7

with B1_RAWVAR.open("r",encoding="utf-8",newline="") as f:
    raw=list(csv.DictReader(f,delimiter="\t"))

with A_MANIFEST.open("r",encoding="utf-8",newline="") as f:
    old_manifest=list(csv.DictReader(f,delimiter="\t"))
old_by_id={r["artifact_id"]:r for r in old_manifest}

with B2_BRIDGE.open("r",encoding="utf-8",newline="") as f:
    b2_bridge={r["field"]:r["value"] for r in csv.DictReader(f,delimiter="\t")}
assert b2_bridge["BRIDGE_ID"]=="FED_SCF_SUMMARY_EXTRACT_REAL_2022_DOLLAR_BASIS"
assert b2_bridge["STATUS_AT_E4D0B2"]=="CONDITIONAL_NOT_YET_VALIDATED"

def write_tsv(path,header,rows):
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,delimiter="\t",lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)

def sha256(b):
    return hashlib.sha256(b).hexdigest()

def new_path(target):
    return REFROOT/target["relative_path"]

def load_new(target):
    p=new_path(target)
    b=p.read_bytes()
    return p,b

def norm(s):
    return re.sub(r"\s+"," ",s).strip()

# Exact five acquired bytes.
manifest_rows=[]
new_bytes={}
for t in targets:
    p,b=load_new(t)
    assert b
    new_bytes[t["artifact_id"]]=b
    manifest_rows.append([
        t["artifact_id"],t["family"],t["year"],t["evidence_role"],
        t["url"],str(p.relative_to(ROOT)),sha256(b),str(len(b)),
        t["content_class"]
    ])
assert len(manifest_rows)==5

# Parse JSON metadata.
def parse_json(aid):
    return json.loads(new_bytes[aid].decode("utf-8"))

acs19=parse_json("ACS_2019_AGEP_API")
acs22=parse_json("ACS_2022_AGEP_API")
cps19=parse_json("CPS_2019_A_AGE_API")
cps22=parse_json("CPS_2022_A_AGE_API")

def range_covers_age(obj,lo,hi):
    ranges=obj.get("values",{}).get("range",[])
    for r in ranges:
        try:
            mn=int(r["min"]); mx=int(r["max"])
        except Exception:
            continue
        if mn <= lo and mx >= hi:
            return True
    return False

acs19_ok=(acs19.get("name")=="AGEP" and acs19.get("label")=="Age"
          and acs19.get("predicateType")=="int" and range_covers_age(acs19,25,64))
acs22_ok=(acs22.get("name")=="AGEP" and acs22.get("label")=="Age"
          and acs22.get("predicateType")=="int" and range_covers_age(acs22,25,64))
acs_age_ok=acs19_ok and acs22_ok

def cps_age_obj_ok(o):
    label=o.get("label","")
    return (o.get("name")=="A_AGE" and
            o.get("predicateType")=="int" and
            "demographics" in label.lower() and "age" in label.lower())

cps19_ok=cps_age_obj_ok(cps19)
cps22_ok=cps_age_obj_ok(cps22)

# Frozen B1 dictionary-presence condition remains required.
rr=[r for r in raw if r["family"]=="CPS_ASEC" and r["candidate_token"]=="A_AGE"]
assert len(rr)==1
rra=rr[0]
cps_b1_presence=(rra["present_in_frozen_2022_authority"]=="1" and
                 rra["present_in_2019_official_docs"]=="1" and
                 rra["present_in_2022_official_docs"]=="1")
cps_age_ok=cps19_ok and cps22_ok and cps_b1_presence

# Parse official SCF common summary-extract macro.
macro=new_bytes["SCF_SUMMARY_EXTRACT_MACRO"].decode("utf-8",errors="strict")
macro_upper=macro.upper()

macro_bullit=("%MACRO BULLIT" in macro_upper)
year2019_branch=bool(re.search(r"%ELSE\s+%IF\s*\(\s*&YEAR\s*=\s*2019\s*\)",macro,re.I))
year2022_branch=bool(re.search(r"%ELSE\s+%IF\s*\(\s*&YEAR\s*=\s*2022\s*\)",macro,re.I))
cpi_rs=("CPI-U-RS" in macro_upper)

fin_assign=re.findall(r"(?mi)^\s*FIN\s*=\s*([^;]+);",macro)
pirtotal_assign=re.findall(r"(?mi)^\s*PIRTOTAL\s*=\s*([^;]+);",macro)
fin_one=(len(fin_assign)==1)
pirtotal_one=(len(pirtotal_assign)==1)

expected_fin="LIQ+CDS+NMMF+STOCKS+BOND+RETQLIQ+SAVBND+CASHLI+OTHMA+OTHFIN"
fin_formula_ok=fin_one and re.sub(r"\s+","",fin_assign[0]).upper()==expected_fin

pirtotal_formula_text=re.sub(r"\s+","",pirtotal_assign[0]).upper() if pirtotal_one else ""
pirtotal_formula_ok=(pirtotal_one and
                     "TPAY/MAX((INCOME/12)" in pirtotal_formula_text and
                     "100/&CPIADJ89" in pirtotal_formula_text)

# Exactly one effective assignment means one executable assignment line in the common macro.
pirtotal_common_ok=macro_bullit and pirtotal_formula_ok
fin_common_ok=macro_bullit and fin_formula_ok

# Extract real-dollar VALUE array and require FIN.
m=re.search(r"(?is)ARRAY\s+VALUE\{\*\}(.*?);",macro)
value_array=(m.group(1) if m else "")
fin_in_value_array=bool(re.search(r"\bFIN\b",value_array,re.I))

real2019=c["k_bridge"]["2019_real_call_required"] in macro
real2022=c["k_bridge"]["2022_real_call_required"] in macro

# Require explicit note that PIRTOTAL uses monthly payments/income and same-dollar basis under ADJINC.
payment_ratio_note=("compute ratio of monthly payments to monthly income" in macro.lower())
same_dollar_note=("income already inflated to same dollars as" in macro.lower()
                  and "payments" in macro.lower())
pirtotal_timing_ok=pirtotal_common_ok and payment_ratio_note and same_dollar_note

# Existing hash-pinned SCF release pages.
def old_text(aid):
    r=old_by_id[aid]
    p=ROOT/r["local_path"]
    b=p.read_bytes()
    assert sha256(b)==r["sha256"]
    return b.decode("utf-8",errors="replace")

scf19_page=old_text("SCF_2019_RELEASE_PAGE")
scf22_page=old_text("SCF_2022_RELEASE_PAGE")

def release_2022_dollar_gate(s):
    low=norm(s).lower()
    return ("summary extract" in low and
            "2022 dollars" in low and
            ("inflation-adjusted" in low or "inflation adjusted" in low))

release19_ok=release_2022_dollar_gate(scf19_page)
release22_ok=release_2022_dollar_gate(scf22_page)

k_real_bridge_ok=all([
    macro_bullit,year2019_branch,year2022_branch,cpi_rs,
    fin_common_ok,fin_in_value_array,real2019,real2022,
    release19_ok,release22_ok
])

# Evidence ledger.
evidence_rows=[
["EVB2A_AGE_ACS_2019","10","ACS_2019_AGEP_API",
 f"name={acs19.get('name')};label={acs19.get('label')};type={acs19.get('predicateType')};covers_25_64={int(range_covers_age(acs19,25,64))}",
 "PASS" if acs19_ok else "UNRESOLVED"],
["EVB2A_AGE_ACS_2022","10","ACS_2022_AGEP_API",
 f"name={acs22.get('name')};label={acs22.get('label')};type={acs22.get('predicateType')};covers_25_64={int(range_covers_age(acs22,25,64))}",
 "PASS" if acs22_ok else "UNRESOLVED"],
["EVB2A_AGE_CPS_2019","12","CPS_2019_A_AGE_API",
 f"name={cps19.get('name')};label={cps19.get('label')};type={cps19.get('predicateType')}",
 "PASS" if cps19_ok else "UNRESOLVED"],
["EVB2A_AGE_CPS_2022","12","CPS_2022_A_AGE_API",
 f"name={cps22.get('name')};label={cps22.get('label')};type={cps22.get('predicateType')}",
 "PASS" if cps22_ok else "UNRESOLVED"],
["EVB2A_AGE_CPS_B1","12","E4D0B1_RAWVAR",
 f"frozen2022={rra['present_in_frozen_2022_authority']};2019docs={rra['present_in_2019_official_docs']};2022docs={rra['present_in_2022_official_docs']}",
 "PASS" if cps_b1_presence else "UNRESOLVED"],
["EVB2A_SCF_PIRTOTAL_DEF","4","SCF_SUMMARY_EXTRACT_MACRO",
 f"bullit={int(macro_bullit)};assignment_count={len(pirtotal_assign)};formula_gate={int(pirtotal_formula_ok)}",
 "PASS" if pirtotal_common_ok else "UNRESOLVED"],
["EVB2A_SCF_FIN_DEF","28","SCF_SUMMARY_EXTRACT_MACRO",
 f"bullit={int(macro_bullit)};assignment_count={len(fin_assign)};formula_gate={int(fin_formula_ok)}",
 "PASS" if fin_common_ok else "UNRESOLVED"],
["EVB2A_SCF_CPI_BRANCHES","28|32","SCF_SUMMARY_EXTRACT_MACRO",
 f"2019_branch={int(year2019_branch)};2022_branch={int(year2022_branch)};CPI_U_RS={int(cpi_rs)};real2019={int(real2019)};real2022={int(real2022)};FIN_in_VALUE_array={int(fin_in_value_array)}",
 "PASS" if all([year2019_branch,year2022_branch,cpi_rs,real2019,real2022,fin_in_value_array]) else "UNRESOLVED"],
["EVB2A_SCF_RELEASE_2019","28|32","SCF_2019_RELEASE_PAGE",
 f"summary_extract_2022_dollar_gate={int(release19_ok)}",
 "PASS" if release19_ok else "UNRESOLVED"],
["EVB2A_SCF_RELEASE_2022","28|32","SCF_2022_RELEASE_PAGE",
 f"summary_extract_2022_dollar_gate={int(release22_ok)}",
 "PASS" if release22_ok else "UNRESOLVED"],
["EVB2A_SCF_PIRTOTAL_TIMING","29","SCF_SUMMARY_EXTRACT_MACRO",
 f"formula_gate={int(pirtotal_common_ok)};monthly_ratio_note={int(payment_ratio_note)};same_dollar_ADJINC_note={int(same_dollar_note)}",
 "PASS" if pirtotal_timing_ok else "UNRESOLVED"],
["EVB2A_K_BRIDGE","32","SCF_SUMMARY_EXTRACT_MACRO|SCF_2019_RELEASE_PAGE|SCF_2022_RELEASE_PAGE|E4D0B2_K_REFERENCE_POLICY",
 f"bridge_id={c['k_bridge']['bridge_id']};gate={int(k_real_bridge_ok)};reference_scale_refit=0",
 "VERSIONED_PASS" if k_real_bridge_ok else "UNRESOLVED"],
]

# Apply only frozen seven resolutions.
resolved={}
resolved[4]="PASS" if pirtotal_common_ok else "UNRESOLVED"
resolved[10]="PASS" if acs_age_ok else "UNRESOLVED"
resolved[12]="PASS" if cps_age_ok else "UNRESOLVED"
resolved[28]="VERSIONED_PASS" if k_real_bridge_ok else "UNRESOLVED"
resolved[29]="PASS" if pirtotal_timing_ok else "UNRESOLVED"
resolved[32]="VERSIONED_PASS" if k_real_bridge_ok else "UNRESOLVED"

# Start from B1, mutate only 4,10,12,28,29,32; grid 37 after dependency check.
updated=[]
for row in b1:
    q=dict(row)
    i=int(q["object_index"])
    if i in resolved:
        q["status"]=resolved[i]
        q["basis"]="E4D0B2A targeted official-evidence rule result"
        q["evidence_ids"]="E4D0B2A"
    updated.append(q)

non_grid=[r["status"] for r in updated if int(r["object_index"])!=37]
grid_ok=all(s in {"PASS","VERSIONED_PASS"} for s in non_grid)
resolved[37]="PASS" if grid_ok else "UNRESOLVED"

for q in updated:
    if int(q["object_index"])==37:
        q["status"]=resolved[37]
        q["basis"]="E4D0B2A dependency rule: exact 2019|2022 grid freezes only if all other objects resolve"
        q["evidence_ids"]="E4D0B2A_DEPENDENCY"

# Verify no non-target mutation relative to B1.
b1_by={int(r["object_index"]):r for r in b1}
for q in updated:
    i=int(q["object_index"])
    if i not in {4,10,12,28,29,32,37}:
        old=b1_by[i]
        for k in old:
            assert q[k]==old[k],(i,k,q[k],old[k])

pass_count=sum(r["status"]=="PASS" for r in updated)
vpass_count=sum(r["status"]=="VERSIONED_PASS" for r in updated)
fail_count=sum(r["status"]=="FAIL" for r in updated)
unres_count=sum(r["status"]=="UNRESOLVED" for r in updated)

all_resolved=(fail_count==0 and unres_count==0)
if all_resolved:
    assert (pass_count,vpass_count,fail_count,unres_count)==(36,4,0,0)
    panel="SEMANTIC_AND_DESIGN_COMPARABILITY_RESOLVED"
    grid_status="FROZEN"
    grid_value="2019|2022"
    next_phase="E4D1"
    e4d1_auth=1
    forensic_auth=0
else:
    panel="BLOCKED_UNRESOLVED"
    grid_status="NOT_FROZEN"
    grid_value="NONE"
    next_phase="E4D0B2R"
    e4d1_auth=0
    forensic_auth=1

resolution_rows=[]
for i in [4,10,12,28,29,32,37]:
    p=next(r for r in plan if int(r["object_index"])==i)
    resolution_rows.append([
        str(i),p["axis"],p["scope_id"],"UNRESOLVED",
        resolved[i],p["precommitted_success_status"],p["failure_status"]
    ])

bridge_status="VALIDATED_FROZEN" if k_real_bridge_ok else "UNRESOLVED"
bridge_rows=[
["BRIDGE_ID",c["k_bridge"]["bridge_id"]],
["VALIDATION_STATUS",bridge_status],
["COMMON_BASIS","2022 dollars"],
["CPIBASE_2022_INTEGER","4376"],
["MACRO_COMMON_BULLIT",str(int(macro_bullit))],
["YEAR_2019_CPI_BRANCH",str(int(year2019_branch))],
["YEAR_2022_CPI_BRANCH",str(int(year2022_branch))],
["CPI_U_RS_METHOD_DOCUMENTED",str(int(cpi_rs))],
["FIN_SINGLE_COMMON_DEFINITION",str(int(fin_common_ok))],
["FIN_IN_REAL_DOLLAR_VALUE_ARRAY",str(int(fin_in_value_array))],
["REAL_2019_CALL_CPIBASE_4376",str(int(real2019))],
["REAL_2022_CALL_CPIBASE_4376",str(int(real2022))],
["SCF_2019_RELEASE_SUMMARY_EXTRACT_2022_DOLLARS",str(int(release19_ok))],
["SCF_2022_RELEASE_SUMMARY_EXTRACT_2022_DOLLARS",str(int(release22_ok))],
["EXISTING_FROZEN_K_REFERENCE_SCALE_REUSED","1"],
["K_REFERENCE_SCALE_REFIT_ON_2019_VALUES","0"],
["ALTERNATIVE_DEFLATOR_SELECTION_AFTER_VALUES","0"],
]

grid_rows=[
["GRID_ID","SCF_ANCHORED_OBSERVED_WAVE_GRID_2019_2022"],
["STATUS",grid_status],
["GRID",grid_value],
["INTERPOLATION","0"],
["CARRY_FORWARD","0"],
["SYNTHETIC_2020_STATE","0"],
["SYNTHETIC_2021_STATE","0"],
["SEMANTIC_NOTE","survey-wave grid only; underlying coordinate reference periods remain governed by frozen per-coordinate timing policies"],
]

write_tsv(MANIFEST,
    ["artifact_id","family","year","evidence_role","url","local_path","sha256","bytes","content_class"],
    manifest_rows)
write_tsv(EVIDENCE,
    ["evidence_id","object_ids","source","observed_structural_summary","status"],
    evidence_rows)
write_tsv(RESOLUTION,
    ["object_index","axis","scope_id","prior_status","new_status","allowed_success_status","fallback_status"],
    resolution_rows)
write_tsv(ADJ,
    list(b1[0].keys()),
    [[r[k] for k in b1[0].keys()] for r in updated])
write_tsv(BRIDGE,["field","value"],bridge_rows)
write_tsv(GRID,["field","value"],grid_rows)

gate_rows=[
["EXACT_5_NEW_OFFICIAL_ARTIFACTS_ACQUIRED","PASS"],
["EXACT_7_TARGET_OBJECTS_ONLY_MUTABLE","PASS"],
["NON_TARGET_B1_OBJECT_COUNT_BYTE_SEMANTICALLY_PRESERVED","33"],
["MICRODATA_FILES_DOWNLOADED","0"],
["MICRODATA_ROWS_OPENED","0"],
["NUMERIC_RESULT_ROWS_OPENED","0"],
["ADDITIONAL_YEAR_ECONOMIC_VALUES_OPENED","0"],
["AGE_FUZZY_JACCARD_USED","0"],
["K_REFERENCE_SCALE_REFIT_ON_2019_VALUES","0"],
["ALTERNATIVE_DEFLATOR_SELECTED_AFTER_VALUES","0"],
["TEMPORAL_GEOMETRY_COMPUTED","0"],
["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
]
write_tsv(GATES,["gate","value"],gate_rows)

decision_rows=[
["TARGET_YEAR_PAIR","2019_TO_2022"],
["NEW_OFFICIAL_ARTIFACT_COUNT","5"],
["PASS_OBJECT_COUNT",str(pass_count)],
["VERSIONED_PASS_OBJECT_COUNT",str(vpass_count)],
["FAIL_OBJECT_COUNT",str(fail_count)],
["UNRESOLVED_OBJECT_COUNT",str(unres_count)],
["PANEL_STATUS",panel],
["K_PRICE_REFERENCE_BRIDGE_STATUS",bridge_status],
["COMMON_YEAR_GRID_FROZEN",str(int(grid_status=="FROZEN"))],
["COMMON_YEAR_GRID",grid_value],
["MICRODATA_FILES_DOWNLOADED","0"],
["MICRODATA_ROWS_OPENED","0"],
["NUMERIC_RESULT_ROWS_OPENED","0"],
["ADDITIONAL_YEAR_ECONOMIC_VALUES_OPENED","0"],
["TEMPORAL_GEOMETRY_COMPUTED","0"],
["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
["NEXT_PRIMARY_PHASE_ID",next_phase],
["E4D1_MULTIYEAR_PARTIAL_STATE_COORDINATE_EXECUTION_PREFLIGHT_AUTHORIZED",str(e4d1_auth)],
["E4D0B2R_TARGETED_GAP_FORENSIC_AUTHORIZED",str(forensic_auth)],
["E4D0B2A_TARGETED_COMPARABILITY_GAP_RESOLUTION_EXECUTION","PASS"],
]
write_tsv(DECISION,["decision","value"],decision_rows)

log="\n".join([
"E4D0B2_REUSED_AS_CANONICAL_TARGETED_GAP_RESOLUTION_POLICY=1",
"TARGET_YEAR_PAIR=2019_TO_2022",
"NEW_OFFICIAL_ARTIFACT_COUNT=5",
"NEW_OFFICIAL_CONTENT_OPENED_AFTER_E4D0B2A_PRECOMMIT=1",
"MICRODATA_FILES_DOWNLOADED=0",
"MICRODATA_ROWS_OPENED=0",
"NUMERIC_RESULT_ROWS_OPENED=0",
"ADDITIONAL_YEAR_ECONOMIC_VALUES_OPENED=0",
f"OBJECT_4_STATUS={resolved[4]}",
f"OBJECT_10_STATUS={resolved[10]}",
f"OBJECT_12_STATUS={resolved[12]}",
f"OBJECT_28_STATUS={resolved[28]}",
f"OBJECT_29_STATUS={resolved[29]}",
f"OBJECT_32_STATUS={resolved[32]}",
f"OBJECT_37_STATUS={resolved[37]}",
f"PASS_OBJECT_COUNT={pass_count}",
f"VERSIONED_PASS_OBJECT_COUNT={vpass_count}",
f"FAIL_OBJECT_COUNT={fail_count}",
f"UNRESOLVED_OBJECT_COUNT={unres_count}",
f"PANEL_STATUS={panel}",
f"K_PRICE_REFERENCE_BRIDGE_STATUS={bridge_status}",
f"COMMON_YEAR_GRID_FROZEN={int(grid_status=='FROZEN')}",
f"COMMON_YEAR_GRID={grid_value}",
"TEMPORAL_GEOMETRY_COMPUTED=0",
"REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
f"NEXT_PRIMARY_PHASE_ID={next_phase}",
f"E4D1_MULTIYEAR_PARTIAL_STATE_COORDINATE_EXECUTION_PREFLIGHT_AUTHORIZED={e4d1_auth}",
f"E4D0B2R_TARGETED_GAP_FORENSIC_AUTHORIZED={forensic_auth}",
"E4D0B2A_TARGETED_COMPARABILITY_GAP_RESOLUTION_EXECUTION=PASS",
])+"\n"
EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
