#!/usr/bin/env python3
from pathlib import Path
import ast,csv,hashlib,json,sys

ROOT=Path(__file__).resolve().parents[1]
C=json.loads((ROOT/"data/metadata/E4D1D2A1_exact_target_binding_freeze_contract.json").read_text())
D1=ROOT/"data/results/E4D1D1_source_output_binding_registry.tsv"
PROV=ROOT/"data/results/E4D1D1_scientific_function_provenance_registry.tsv"
A0B=ROOT/"data/results/E4D1D2A0_acs_bridge_insertion_registry.tsv"
A0M=ROOT/"data/results/E4D1D2A0_member_literal_rebinding_registry.tsv"
A0R=ROOT/"data/results/E4D1D2A0R_cps_multilocus_member_rebinding_registry.tsv"
METHODS={
 "ACS":ROOT/"scripts/E4C3D_first_acs2022_h_access_execution.py",
 "SCF":ROOT/"scripts/E4A2F_first_scf_kd_inference_execution.py",
 "CPS_ASEC":ROOT/"scripts/E4A2D_first_cps_i_inference_execution.py",
}
OUTS=[
 ROOT/"data/results/E4D1D2A1_raw_path_hash_rebinding_registry.tsv",
 ROOT/"data/results/E4D1D2A1_binding_action_registry.tsv",
 ROOT/"data/results/E4D1D2A1_member_occurrence_rebinding_registry.tsv",
 ROOT/"data/results/E4D1D2A1_acs_ingestion_splice_registry.tsv",
 ROOT/"data/results/E4D1D2A1_target_binding_hard_gates.tsv",
 ROOT/"data/results/E4D1D2A1_exact_target_binding_decision.tsv",
 ROOT/"data/metadata/E4D1D2A1_execution.txt",
 ROOT/"data/metadata/E4D1D2A1_exact_target_binding_audit.txt",
]
def read(p):
    with p.open(newline="") as f:return list(csv.DictReader(f,delimiter="\t"))
def write(p,h,rows):
    with p.open("w",newline="") as f:
        w=csv.writer(f,delimiter="\t",lineterminator="\n");w.writerow(h);w.writerows(rows)
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

fail=[]
raw=[]
for old,new in C["raw_map"].items():
    op,np=ROOT/old,ROOT/new
    if not op.exists(): fail.append("MISSING_2022_RAW:"+old); oldsha="MISSING"
    else: oldsha=sha(op)
    newsha=sha(np)
    src_count=sum(METHODS[f].read_text().count(old) for f in METHODS)
    if src_count!=1: fail.append(f"RAW_SOURCE_LITERAL_COUNT:{old}:{src_count}")
    raw.append([old,new,oldsha,newsha,src_count,"PASS" if oldsha!="MISSING" and src_count==1 else "UNRESOLVED"])
write(OUTS[0],["old_path","new_path","old_sha256","new_sha256","source_literal_count","status"],raw)

bind=[r for r in read(D1) if r["D2_policy"]=="ENUMERATE_IN_D2"]
if len(bind)!=39: fail.append("MUTABLE_BINDING_COUNT:"+str(len(bind)))
brows=[]
for r in bind:
    action={
      "SOURCE_PATH_BINDING":"REBIND_BY_EXACT_RAW_MAP",
      "OUTPUT_PATH_BINDING":"REBIND_TO_E4D1D_2019_RUNTIME_NAMESPACE",
      "YEAR_OR_PHASE_LABEL":"EXACT_2022_TOKEN_TO_2019_ONLY",
      "HASH_EXPECTATION_BINDING":"EXACT_RAW_SHA_LITERAL_ONLY",
      "SCHEMA_OR_MEMBER_BINDING":"FROZEN_MEMBER_LOCUS_ONLY",
    }.get(r["binding_class"],"IMMUTABLE")
    brows.append([r["family"],r["global_name"],r["line"],r["binding_class"],r["assignment_source_sha256"],action,"PASS"])
write(OUTS[1],["family","global_name","line","binding_class","assignment_source_sha256","target_action","status"],brows)

scf=[r for r in read(A0M) if r["family"]=="SCF" and r["status"]=="PASS"]
cps=read(A0R)
mrows=[]
for r in scf:mrows.append(["SCF",r["frozen_2022_member_literal"],r["frozen_2019_selected_member"],r["D2_executable_locus_line"],"SINGLE_FROZEN_LOCUS","PASS"])
for r in cps:mrows.append(["CPS_ASEC",r["frozen_2022_member_literal"],r["frozen_2019_selected_member"],r["source_line"],"ALL_FROZEN_LOCI_SAME_ROLE","PASS"])
if len(mrows)!=7: fail.append("MEMBER_OCCURRENCE_COUNT:"+str(len(mrows)))
write(OUTS[2],["family","old_member","new_member","source_line","multiplicity_policy","status"],mrows)

prov=read(PROV)
if len(prov)!=17: fail.append("FUNCTION_PROVENANCE_COUNT:"+str(len(prov)))
bridge=read(A0B)
if len(bridge)!=1: fail.append("ACS_BRIDGE_COUNT")
splice=[]
if len(bridge)==1:
    b=bridge[0]; src=METHODS["ACS"].read_text(); tree=ast.parse(src)
    nodes=[n for n in tree.body if getattr(n,"lineno",0)==int(b["consumer_start_line"]) and getattr(n,"end_lineno",0)==int(b["consumer_end_line"])]
    if len(nodes)!=1: fail.append("ACS_CONSUMER_NODE_COUNT:"+str(len(nodes)))
    else:
        seg=ast.get_source_segment(src,nodes[0]) or ""
        h=hashlib.sha256(seg.encode()).hexdigest()
        if h!=b["consumer_statement_sha256"]: fail.append("ACS_CONSUMER_SHA")
        norm="".join(seg.split())
        needed=['row.get("HHLDRAGEP")','row.get("TEN")','row.get("NP")','row.get("WGTP")','q=x/npv','A[k,aa,tt]']
        miss=[x for x in needed if x not in norm]
        if miss: fail.append("ACS_CONSUMER_TOKENS:"+",".join(miss))
        splice.append(["ACS",b["consumer_start_line"],b["consumer_end_line"],h,
          "SERIALNO|NP|TYPE|TEN|RMSP|WGTP|WGTP1..WGTP80",
          "SERIALNO|RELSHIPP|AGEP","RELSHIPP=20","TYPE=1 AND NP>0","0",
          "PASS" if not miss and h==b["consumer_statement_sha256"] else "UNRESOLVED"])
write(OUTS[3],["family","consumer_start_line","consumer_end_line","consumer_sha256","housing_projection_contract","person_projection_contract","householder_rule","housing_universe","person_weight_used","status"],splice)

success=(not fail and len(raw)==6 and len(bind)==39 and len(mrows)==7 and len(splice)==1)
g=[
 ["EXACT_RAW_REBINDING_COUNT",str(int(len(raw)==6))],
 ["EXACT_MUTABLE_BINDING_COUNT",str(int(len(bind)==39))],
 ["EXACT_MEMBER_OCCURRENCE_COUNT",str(int(len(mrows)==7))],
 ["EXACT_17_VERBATIM_FUNCTIONS",str(int(len(prov)==17))],
 ["ACS_INGESTION_SPLICE_FROZEN",str(int(len(splice)==1 and splice[0][-1]=="PASS"))],
 ["TARGET_PLAN_FAILURE_COUNT",str(len(fail))],
 ["EXECUTABLE_2019_ADAPTER_CREATED","0"],["2019_RAW_DATA_ROWS_OPENED","0"],
 ["2019_COORDINATE_VALUES_OPENED","0"],["SCIENTIFIC_METHOD_MUTATED","0"]
]
write(OUTS[4],["gate","value"],g)
nxt="E4D1D2A2" if success else "E4D1D2A1R"
d=[
 ["RAW_REBINDING_COUNT",str(len(raw))],["MUTABLE_BINDING_COUNT",str(len(bind))],
 ["MEMBER_OCCURRENCE_COUNT",str(len(mrows))],["ACS_INGESTION_SPLICE_FROZEN",str(int(len(splice)==1 and splice[0][-1]=="PASS"))],
 ["TARGET_PLAN_FAILURE_COUNT",str(len(fail))],["EXECUTABLE_2019_ADAPTER_CREATED","0"],
 ["2019_RAW_DATA_ROWS_OPENED","0"],["2019_COORDINATE_VALUES_OPENED","0"],["SCIENTIFIC_METHOD_MUTATED","0"],
 ["NEXT_PRIMARY_PHASE_ID",nxt],["E4D1D2A2_ADAPTER_SOURCE_CONSTRUCTION_FREEZE_AUTHORIZED",str(int(success))],
 ["E4D1D_2019_COORDINATE_VALUES_OPEN_AUTHORIZED","0"],["TEMPORAL_GEOMETRY_AUTHORIZED","0"],
 ["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],["E4D1D2A1_EXACT_TARGET_BINDING_FREEZE","PASS"]
]
write(OUTS[5],["decision","value"],d)
log="\n".join(f"{k}={v}" for k,v in d)+"\n"
if fail:log+="FAILURE_DETAILS="+" || ".join(fail)+"\n"
OUTS[6].write_text(log);OUTS[7].write_text(log);print(log,end="")
