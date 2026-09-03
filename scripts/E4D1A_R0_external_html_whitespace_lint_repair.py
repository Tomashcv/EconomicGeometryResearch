#!/usr/bin/env python3
from pathlib import Path
import csv,hashlib,json,sys

ROOT=Path(__file__).resolve().parents[1]

RAW=ROOT/"data/raw/reference_metadata/E4D1A/ACS/2019/acs_2019_1year_pums_directory_index.html"
PATHINV=ROOT/"data/results/E4D1A_2022_source_path_reference_inventory.tsv"
RESOLVED=ROOT/"data/results/E4D1A_resolved_2019_source_lineage.tsv"
SCHEMA=ROOT/"data/results/E4D1A_2019_schema_validation_plan.tsv"
ACQPLAN=ROOT/"data/results/E4D1A_2019_microdata_acquisition_plan.tsv"
GATES=ROOT/"data/results/E4D1A_preflight_hard_gates.tsv"
DECISION=ROOT/"data/results/E4D1A_2019_official_source_lineage_acquisition_decision.tsv"
EXEC=ROOT/"data/metadata/E4D1A_execution.txt"
AUDIT=ROOT/"data/metadata/E4D1A_2019_official_source_lineage_acquisition_preflight_audit.txt"

R0_AUDIT=ROOT/"data/metadata/E4D1A_R0_external_html_whitespace_lint_repair_audit.txt"
R0_DECISION=ROOT/"data/results/E4D1A_R0_external_html_whitespace_lint_repair_decision.tsv"

EXPECTED={
 RAW:"8a012605a17d3b1fa88c58dd08c589f8bfed7e78c5896ac07c01aac902fa7c68",
 PATHINV:"41039a6484536f5b8c9691d25e8370d45f7082c7002772a79904607d8c497354",
 RESOLVED:"c90d59485b39d18d4b38cdfe49af4ce4acf31b7940adc426ceac427a5128432d",
 SCHEMA:"022da1127b7b03ce4c258ed8a58389d24fa90ca2101d7f2dd867bc16ec07b1b9",
 ACQPLAN:"96b8d767e37e065fd80d303cf961b99008651d5c97c8faab1f887d038f68e6b2",
 GATES:"edb7ddb45cbbf28530cb58db599a3ccab418666ba96958d2695c2e3f00545845",
 DECISION:"18469f8614dedb5d916ce16b8deb888bc67a6d3e9e331f0079667e798bc64521",
 EXEC:"96aa8cff536eacb2dba0979b7c9cad2cc5454df557502dee5ff89618c83dde6f",
 AUDIT:"96aa8cff536eacb2dba0979b7c9cad2cc5454df557502dee5ff89618c83dde6f",
}

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

for p,h in EXPECTED.items():
    assert p.is_file(), p
    assert sha(p)==h, (p,sha(p),h)

# Generated artifacts only: upstream raw HTML is deliberately excluded from style lint.
generated=[PATHINV,RESOLVED,SCHEMA,ACQPLAN,GATES,DECISION,EXEC,AUDIT]
viol=[]
for p in generated:
    b=p.read_bytes()
    for i,line in enumerate(b.splitlines(keepends=True),1):
        body=line.rstrip(b"\r\n")
        if body.endswith((b" ",b"\t")):
            viol.append((str(p.relative_to(ROOT)),i))
assert not viol, viol

# Confirm the external object genuinely contains upstream whitespace, so exemption is scoped to reality.
raw_lines=RAW.read_bytes().splitlines(keepends=True)
raw_ws=sum(
    1 for line in raw_lines
    if line.rstrip(b"\r\n").endswith((b" ",b"\t")) or line.endswith(b"\r\n")
)
assert raw_ws>0

with DECISION.open("r",encoding="utf-8",newline="") as f:
    d={r["decision"]:r["value"] for r in csv.DictReader(f,delimiter="\t")}
assert d["RESOLVED_SOURCE_REQUIREMENT_COUNT"]=="5"
assert d["UNRESOLVED_SOURCE_REQUIREMENT_COUNT"]=="1"
assert d["ALL_2019_SOURCE_LINEAGE_REQUIREMENTS_RESOLVED"]=="0"
assert d["NEXT_PRIMARY_PHASE_ID"]=="E4D1AR"
assert d["E4D1B_2019_OFFICIAL_SOURCE_ACQUISITION_AND_SCHEMA_AUDIT_AUTHORIZED"]=="0"
assert d["E4D1AR_SOURCE_LINEAGE_FORENSIC_AUTHORIZED"]=="1"
assert d["2019_MICRODATA_FILES_DOWNLOADED"]=="0"
assert d["2019_REPLICATE_WEIGHT_DATA_FILES_DOWNLOADED"]=="0"
assert d["2019_MICRODATA_ROWS_OPENED"]=="0"
assert d["2019_ECONOMIC_VALUES_OPENED"]=="0"

with RESOLVED.open("r",encoding="utf-8",newline="") as f:
    rows=list(csv.DictReader(f,delimiter="\t"))
assert len(rows)==6
un=[r for r in rows if r["status"]=="UNRESOLVED"]
assert len(un)==1
assert un[0]["requirement_index"]=="3"
assert un[0]["family"]=="SCF"
assert un[0]["selected_candidate_ids"]=="SCF_2019_SUMMARY_STATA|SCF_2019_FULL_STATA"

log="\n".join([
"E4D1A_FAILURE_PRESERVED_BEFORE_R0=1",
"E4D1A_R0_REPAIR_SCOPE=VALIDATION_HYGIENE_ONLY",
"EXTERNAL_RAW_HTML_BYTE_IDENTITY_VERIFIED=1",
"EXTERNAL_RAW_HTML_WHITESPACE_NORMALIZED=0",
"EXTERNAL_RAW_HTML_REDOWNLOADED=0",
"GENERATED_E4D1A_ARTIFACT_WHITESPACE_LINT=PASS",
"E4D1A_LINEAGE_RESOLVER_REEXECUTED=0",
"E4D1A_SOURCE_RESELECTION_PERFORMED=0",
"RESOLVED_SOURCE_REQUIREMENT_COUNT=5",
"UNRESOLVED_SOURCE_REQUIREMENT_COUNT=1",
"UNRESOLVED_REQUIREMENT_INDEX=3",
"UNRESOLVED_FAMILY=SCF",
"NEXT_PRIMARY_PHASE_ID=E4D1AR",
"E4D1B_2019_OFFICIAL_SOURCE_ACQUISITION_AND_SCHEMA_AUDIT_AUTHORIZED=0",
"E4D1AR_SOURCE_LINEAGE_FORENSIC_AUTHORIZED=1",
"2019_MICRODATA_FILES_DOWNLOADED=0",
"2019_REPLICATE_WEIGHT_DATA_FILES_DOWNLOADED=0",
"2019_MICRODATA_ROWS_OPENED=0",
"2019_ECONOMIC_VALUES_OPENED=0",
"TEMPORAL_GEOMETRY_AUTHORIZED=0",
"REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
"E4D1A_R0_EXTERNAL_HTML_WHITESPACE_LINT_REPAIR=PASS",
])+"\n"
R0_AUDIT.write_text(log,encoding="utf-8")

with R0_DECISION.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["decision","value"])
    for line in log.strip().splitlines():
        k,v=line.split("=",1)
        w.writerow([k,v])

print(log,end="")
