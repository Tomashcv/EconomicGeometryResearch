#!/usr/bin/env python3
from pathlib import Path
import ast, csv, hashlib

ROOT=Path(__file__).resolve().parents[1]
PARENT=ROOT/"scripts/E4D1D3_CPSP_cps2019_i_adapter.py"
OUT=ROOT/"scripts/E4D1D3_CPSI_R0_cps2019_i_adapter.py"
REG=ROOT/"data/results/E4D1D3_CPSI_R0_year_label_repair_registry.tsv"
DEC=ROOT/"data/results/E4D1D3_CPSI_R0_year_label_repair_decision.tsv"
AUDIT=ROOT/"data/metadata/E4D1D3_CPSI_R0_year_label_repair_audit.txt"

PARENT_SHA="556b5ae5076b319f45b1bd2261c34193833b1eb45916183c7adae1615c09a7ca"
EXPECTED_OUTPUT_SHA="76acc152a2e122570cab00ac03110763d8e55d8ae8134e65c7206986cecb81d7"
EXPECTED_LINES=(1280,1347,1372,1471,1500)
EXPECTED_CHANGED_CHARACTER_COUNT=10
LEGACY_BASENAMES=(
 "E4A2D_2022_cps_i_cohort_inference.tsv",
 "E4A2D_2022_cps_i_owner_renter_differences.tsv",
 "E4A2D_2022_cps_i_replicate_estimates.tsv",
 "E4A2D_2022_cps_i_cohort_support.tsv",
)

def sha(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def function_hashes(s:str)->dict[str,str]:
    t=ast.parse(s)
    out={}
    for n in t.body:
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
            seg=ast.get_source_segment(s,n)
            out[n.name]=hashlib.sha256(seg.encode("utf-8")).hexdigest()
    return out

parent_bytes=PARENT.read_bytes()
assert sha(parent_bytes)==PARENT_SHA
for p in (OUT,REG,DEC,AUDIT):
    assert not p.exists(), p

src=parent_bytes.decode("utf-8")
tree=ast.parse(src)
lines=src.splitlines(keepends=True)

def byte_offset(lineno:int,col:int)->int:
    return len("".join(lines[:lineno-1]).encode("utf-8")) + len(lines[lineno-1][:col].encode("utf-8"))

loci=[]
for n in ast.walk(tree):
    if isinstance(n,ast.Dict):
        for k,v in zip(n.keys,n.values):
            if isinstance(k,ast.Constant) and k.value=="year":
                assert isinstance(v,ast.Constant) and v.value==2022
                loci.append((v.lineno,byte_offset(v.lineno,v.col_offset),byte_offset(v.end_lineno,v.end_col_offset)))
loci=sorted(loci)
assert tuple(x[0] for x in loci)==EXPECTED_LINES

patched=parent_bytes
for ln,start,end in sorted(loci,key=lambda x:x[1],reverse=True):
    assert patched[start:end]==b"2022"
    patched=patched[:start]+b"2019"+patched[end:]

text=patched.decode("utf-8")
assert sum(a!=b for a,b in zip(src,text))==EXPECTED_CHANGED_CHARACTER_COUNT
changed_lines=[i+1 for i,(a,b) in enumerate(zip(src.splitlines(),text.splitlines())) if a!=b]
assert tuple(changed_lines)==EXPECTED_LINES

pt=ast.parse(text)
post_years=[]
for n in ast.walk(pt):
    if isinstance(n,ast.Dict):
        for k,v in zip(n.keys,n.values):
            if isinstance(k,ast.Constant) and k.value=="year":
                post_years.append(v.value if isinstance(v,ast.Constant) else None)
assert len(post_years)==5 and all(v==2019 for v in post_years)
assert function_hashes(src)==function_hashes(text)

for token in LEGACY_BASENAMES:
    assert src.count(token)==1 and text.count(token)==1

assert '"year": 2022' not in text
assert text.count('"year": 2019')==5
assert sha(patched)==EXPECTED_OUTPUT_SHA

OUT.write_bytes(patched)
REG.parent.mkdir(parents=True,exist_ok=True)

with REG.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["binding","patch_class","old_value","new_value","occurrence_count","locus_lines","changed_character_count","scientific_functions_mutated","legacy_output_basenames_mutated","status"])
    w.writerow(["INTERNAL_OUTPUT_ROW_YEAR","PROVENANCE_LABEL_ONLY","2022","2019","5","|".join(map(str,EXPECTED_LINES)),"10","0","0","PASS"])

with DEC.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["decision","value"])
    w.writerows([
      ("E4D1D3_CPSI_R0_INTERNAL_YEAR_LABEL_REPAIR","PASS"),
      ("PARENT_CPS_I_ADAPTER_SHA256",PARENT_SHA),
      ("OUTPUT_CPS_I_ADAPTER_SHA256",sha(OUT.read_bytes())),
      ("YEAR_LABEL_2022_TO_2019_PATCH_COUNT","5"),
      ("CHANGED_CHARACTER_COUNT","10"),
      ("PATCH_CLASS","PROVENANCE_LABEL_ONLY"),
      ("SCIENTIFIC_FUNCTIONS_MUTATED","0"),
      ("LEGACY_2022_OUTPUT_BASENAMES_MUTATED","0"),
      ("RAW_CPS_DATA_OPENED","0"),
      ("CPS_PWWGT1_160_VALUES_OPENED","0"),
      ("CPS_I_VALUES_OPENED","0"),
      ("SCF_K_D_VALUES_OPENED","0"),
      ("OUTCOME_BASED_GATE","0"),
      ("SCIENTIFIC_METHOD_MUTATED","0"),
      ("NEXT_PRIMARY_PHASE_ID","E4D1D3_CPSI_P0"),
      ("E4D1D3_CPSI_2019_I_EXECUTION_PRECOMMIT_AUTHORIZED","1"),
      ("CPS_I_VALUE_OPEN_AUTHORIZED","0"),
    ])

AUDIT.parent.mkdir(parents=True,exist_ok=True)
AUDIT.write_text("\n".join([
 "E4D1D3_CPSI_R0_INTERNAL_YEAR_LABEL_REPAIR=PASS",
 f"PARENT_CPS_I_ADAPTER_SHA256={PARENT_SHA}",
 f"OUTPUT_CPS_I_ADAPTER_SHA256={sha(OUT.read_bytes())}",
 "YEAR_LABEL_2022_TO_2019_PATCH_COUNT=5",
 "CHANGED_CHARACTER_COUNT=10",
 "PATCH_CLASS=PROVENANCE_LABEL_ONLY",
 "SCIENTIFIC_FUNCTIONS_MUTATED=0",
 "LEGACY_2022_OUTPUT_BASENAMES_MUTATED=0",
 "ADAPTER_EXECUTED=0",
 "RAW_CPS_DATA_OPENED=0",
 "CPS_PWWGT1_160_VALUES_OPENED=0",
 "CPS_I_VALUES_OPENED=0",
 "SCF_K_D_VALUES_OPENED=0",
 "SCIENTIFIC_METHOD_MUTATED=0",
 "NEXT_PRIMARY_PHASE_ID=E4D1D3_CPSI_P0",
 "E4D1D3_CPSI_2019_I_EXECUTION_PRECOMMIT_AUTHORIZED=1",
 "CPS_I_VALUE_OPEN_AUTHORIZED=0",
])+"\n",encoding="utf-8")
print(AUDIT.read_text(encoding="utf-8"),end="")
