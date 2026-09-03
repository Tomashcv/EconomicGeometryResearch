#!/usr/bin/env python3
from pathlib import Path
import ast, csv, hashlib

ROOT=Path(__file__).resolve().parents[1]
PARENT=ROOT/"scripts/E4D1D3_CPSI_R0_cps2019_i_adapter.py"
OUT=ROOT/"scripts/E4D1D3_CPSI_R1_cps2019_i_adapter.py"
REG=ROOT/"data/results/E4D1D3_CPSI_R1_replicate_zip_case_repair_registry.tsv"
DEC=ROOT/"data/results/E4D1D3_CPSI_R1_replicate_zip_case_repair_decision.tsv"
AUDIT=ROOT/"data/metadata/E4D1D3_CPSI_R1_replicate_zip_case_repair_audit.txt"

PARENT_SHA="76acc152a2e122570cab00ac03110763d8e55d8ae8134e65c7206986cecb81d7"
OLD_PATH="data/raw/cps_asec/2019/CPS_ASEC_ASCII_REPWGT_2019.ZIP"
NEW_PATH="data/raw/cps_asec/2019/CPS_ASEC_ASCII_REPWGT_2019.zip"
ARCHIVE_SHA="6281a4dee146bf72d5547a12b952ac51a07c83794c9ebe00433631030dab14de"
EXPECTED_OUTPUT_SHA="51e08a8cfdf48ad3b98feacacd4ba861eb55611d700f353e8765a72eebd85094"

def sha(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def function_hashes(s:str)->dict[str,str]:
    t=ast.parse(s)
    d={}
    for n in t.body:
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
            seg=ast.get_source_segment(s,n)
            d[n.name]=hashlib.sha256(seg.encode("utf-8")).hexdigest()
    return d

parent_bytes=PARENT.read_bytes()
assert sha(parent_bytes)==PARENT_SHA
for p in (OUT,REG,DEC,AUDIT):
    assert not p.exists(), p

src=parent_bytes.decode("utf-8")
assert src.count(OLD_PATH)==1
assert src.count(NEW_PATH)==0
assert src.count(ARCHIVE_SHA)==1

patched=src.replace(OLD_PATH,NEW_PATH,1)
assert patched.count(OLD_PATH)==0
assert patched.count(NEW_PATH)==1
assert patched.count(ARCHIVE_SHA)==1
assert len(src)==len(patched)

changed_lines=[i+1 for i,(a,b) in enumerate(zip(src.splitlines(),patched.splitlines())) if a!=b]
assert changed_lines==[86]
assert sum(a!=b for a,b in zip(src,patched))==3
assert function_hashes(src)==function_hashes(patched)
assert src.count('"year": 2019')==patched.count('"year": 2019')==5
assert sha(patched.encode("utf-8"))==EXPECTED_OUTPUT_SHA

OUT.write_text(patched,encoding="utf-8")
REG.parent.mkdir(parents=True,exist_ok=True)

with REG.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["binding","patch_class","old_path","new_path","occurrence_count","changed_lines","changed_character_count","archive_sha_binding_mutated","scientific_functions_mutated","status"])
    w.writerow(["CPS_REP","PATH_CASE_ONLY",OLD_PATH,NEW_PATH,"1","86","3","0","0","PASS"])

with DEC.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["decision","value"])
    w.writerows([
      ("E4D1D3_CPSI_R1_REPLICATE_ZIP_CASE_REPAIR","PASS"),
      ("PATCH_CLASS","PATH_CASE_ONLY"),
      ("PARENT_CPS_I_ADAPTER_SHA256",PARENT_SHA),
      ("OUTPUT_CPS_I_ADAPTER_SHA256",sha(OUT.read_bytes())),
      ("CPS_REP_PATH_PATCH_COUNT","1"),
      ("CHANGED_LINE_COUNT","1"),
      ("CHANGED_CHARACTER_COUNT","3"),
      ("ARCHIVE_SHA_BINDING_MUTATED","0"),
      ("SCIENTIFIC_FUNCTIONS_MUTATED","0"),
      ("CPS_I_ADAPTER_EXECUTED","0"),
      ("RAW_CPS_ARCHIVE_CONTENT_OPENED","0"),
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
 "E4D1D3_CPSI_R1_REPLICATE_ZIP_CASE_REPAIR=PASS",
 "PATCH_CLASS=PATH_CASE_ONLY",
 f"PARENT_CPS_I_ADAPTER_SHA256={PARENT_SHA}",
 f"OUTPUT_CPS_I_ADAPTER_SHA256={sha(OUT.read_bytes())}",
 "CPS_REP_PATH_PATCH_COUNT=1",
 "CHANGED_LINE_COUNT=1",
 "CHANGED_CHARACTER_COUNT=3",
 "ARCHIVE_SHA_BINDING_MUTATED=0",
 "SCIENTIFIC_FUNCTIONS_MUTATED=0",
 "CPS_I_ADAPTER_EXECUTED=0",
 "RAW_CPS_ARCHIVE_CONTENT_OPENED=0",
 "CPS_PWWGT1_160_VALUES_OPENED=0",
 "CPS_I_VALUES_OPENED=0",
 "SCF_K_D_VALUES_OPENED=0",
 "SCIENTIFIC_METHOD_MUTATED=0",
 "NEXT_PRIMARY_PHASE_ID=E4D1D3_CPSI_P0",
 "E4D1D3_CPSI_2019_I_EXECUTION_PRECOMMIT_AUTHORIZED=1",
 "CPS_I_VALUE_OPEN_AUTHORIZED=0",
])+"\n",encoding="utf-8")
print(AUDIT.read_text(encoding="utf-8"),end="")
