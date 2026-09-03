#!/usr/bin/env python3
from pathlib import Path
import csv,hashlib,json,subprocess

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"data/metadata/E4D1D0_R0_post_execution_whitespace_repair_contract.json"
LINEAGE=ROOT/"data/metadata/E4D1D0_R0_preserved_output_hash_lineage.tsv"

GLOBALS=ROOT/"data/results/E4D1D0_global_assignment_registry.tsv"
SUMMARY=ROOT/"data/results/E4D1D0_method_interface_summary.tsv"
GATES=ROOT/"data/results/E4D1D0_interface_preflight_hard_gates.tsv"
DECISION=ROOT/"data/results/E4D1D0_frozen_method_execution_interface_decision.tsv"

c=json.loads(CONTRACT.read_text(encoding="utf-8"))
assert c["phase"]=="E4D1D0_R0"
assert c["repair_scope"]["D0_reexecution"] is False
assert c["repair_scope"]["scientific_outcome_mutation"] is False
assert c["repair_scope"]["method_mutation"] is False
assert c["repair_scope"]["expected_changed_line_numbers"]==[103,148]

with LINEAGE.open("r",encoding="utf-8",newline="") as f:
    lin=list(csv.DictReader(f,delimiter="\t"))
assert len(lin)==11
by={r["artifact"]:r for r in lin}

# Read exact preserved target blob from the failure-preservation commit.
preserve=c["parent_failure_head"]
rel=str(GLOBALS.relative_to(ROOT))
orig=subprocess.run(
    ["git","show",f"{preserve}:{rel}"],
    capture_output=True,check=True
).stdout
assert hashlib.sha256(orig).hexdigest()==by[rel]["sha256"]

# Normalize only horizontal trailing whitespace immediately before line endings.
parts=orig.splitlines(keepends=True)
changed=[]
norm=[]
for i,line in enumerate(parts,1):
    if line.endswith(b"\r\n"):
        body,eol=line[:-2],b"\r\n"
    elif line.endswith(b"\n"):
        body,eol=line[:-1],b"\n"
    else:
        body,eol=line,b""
    newbody=body.rstrip(b" \t")
    if newbody!=body:
        changed.append(i)
    norm.append(newbody+eol)
normalized=b"".join(norm)
assert changed==[103,148],changed
assert GLOBALS.read_bytes()==normalized

# Every non-target preserved output remains byte-identical.
for rel,r in by.items():
    p=ROOT/rel
    if rel==str(GLOBALS.relative_to(ROOT)):
        continue
    assert hashlib.sha256(p.read_bytes()).hexdigest()==r["sha256"],rel

# Existing scientific/source-only outcome remains unchanged.
def read(p):
    with p.open("r",encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f,delimiter="\t"))

summary=read(SUMMARY)
g={r["gate"]:r["value"] for r in read(GATES)}
d={r["decision"]:r["value"] for r in read(DECISION)}
assert len(summary)==3
assert all(r["interface_class"]=="TOP_LEVEL_EXECUTION_UNSAFE" for r in summary)
assert d["METHOD_INTERFACE_COUNT"]=="3"
assert d["TOP_LEVEL_EXECUTION_UNSAFE_METHOD_COUNT"]=="3"
assert d["FROZEN_EXECUTOR_IMPORTED"]=="0"
assert d["FROZEN_EXECUTOR_EXECUTED"]=="0"
assert d["2019_RAW_ROWS_OPENED"]=="0"
assert d["2019_COORDINATE_VALUES_OPENED"]=="0"
assert d["SCIENTIFIC_METHOD_MUTATED"]=="0"
assert d["NEXT_PRIMARY_PHASE_ID"]=="E4D1D1"
assert d["E4D1D1_EXECUTION_ADAPTER_FREEZE_AUTHORIZED"]=="1"
assert d["E4D1D_2019_COORDINATE_VALUES_OPEN_AUTHORIZED"]=="0"
assert g["ALL_AST_PARSE_PASS"]=="1"
assert g["ALL_INTERFACE_CLASSES_ALLOWED"]=="1"

print("PRESERVED_OUTPUT_HASH_LINEAGE=PASS")
print("EXACT_NORMALIZED_LINE_COUNT=2")
print("EXACT_NORMALIZED_LINES=103|148")
print("OTHER_10_D0_OUTPUTS_BYTE_IMMUTABLE=PASS")
print("D0_SCIENTIFIC_OUTCOME_IMMUTABLE=PASS")
print("E4D1D0_R0_POST_EXECUTION_WHITESPACE_REPAIR=PASS")
