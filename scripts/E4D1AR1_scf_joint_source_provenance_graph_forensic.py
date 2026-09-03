#!/usr/bin/env python3
from pathlib import Path
import ast,csv,json

ROOT=Path(__file__).resolve().parents[1]
KD=ROOT/"scripts/E4A2F_first_scf_kd_inference_execution.py"
PRIOR=ROOT/"data/results/E4D1AR_updated_2019_source_lineage.tsv"
PLAN=ROOT/"data/metadata/E4D1A_official_2019_source_candidate_plan.tsv"

BIND=ROOT/"data/results/E4D1AR1_candidate_binding_registry.tsv"
USES=ROOT/"data/results/E4D1AR1_target_variable_use_ledger.tsv"
COMBOS=ROOT/"data/results/E4D1AR1_joint_combination_ledger.tsv"
SOURCESET=ROOT/"data/results/E4D1AR1_effective_source_set_resolution.tsv"
UPDATED=ROOT/"data/results/E4D1AR1_updated_2019_source_lineage.tsv"
ACQ=ROOT/"data/results/E4D1AR1_2019_microdata_acquisition_plan.tsv"
GATES=ROOT/"data/results/E4D1AR1_forensic_hard_gates.tsv"
DEC=ROOT/"data/results/E4D1AR1_scf_joint_source_provenance_graph_decision.tsv"
EXEC=ROOT/"data/metadata/E4D1AR1_execution.txt"
AUDIT=ROOT/"data/metadata/E4D1AR1_scf_joint_source_provenance_graph_forensic_audit.txt"

SUMMARY="SCF_SUMMARY_STATA"; FULL="SCF_FULL_STATA"
TOK={SUMMARY:"scfp2022s.zip",FULL:"scf2022s.zip"}
TARGET={"FIN","PIRTOTAL"}
STRUCT=("Y1","YY1","X42001","WGT","WEIGHT","AGE","AGECL","HOUSE","HOME","TENURE")

def readtsv(p):
    with p.open("r",encoding="utf-8",newline="") as f: return list(csv.DictReader(f,delimiter="\t"))
def writetsv(p,h,rows):
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,delimiter="\t",lineterminator="\n"); w.writerow(h); w.writerows(rows)

prior=readtsv(PRIOR)
assert len(prior)==6 and [x["requirement_index"] for x in prior if x["status"]=="UNRESOLVED"]==["3"]

src=KD.read_text(encoding="utf-8")
lines=src.splitlines()
tree=ast.parse(src)

def callname(n):
    if isinstance(n,ast.Name): return n.id
    if isinstance(n,ast.Attribute):
        a=callname(n.value); return (a+"."+n.attr) if a else n.attr
    return ""
def names(t):
    if isinstance(t,ast.Name): return [t.id]
    if isinstance(t,(ast.Tuple,ast.List)): return sum((names(x) for x in t.elts),[])
    return []
def literals(node):
    d=set()
    for n in ast.walk(node):
        if isinstance(n,ast.Constant) and isinstance(n.value,str):
            low=n.value.lower()
            for cid,t in TOK.items():
                if t in low: d.add(cid)
    return d

deps={}
orig={}
assign=[]
for n in ast.walk(tree):
    if isinstance(n,ast.Assign):
        for t in n.targets: assign.append((n,names(t),n.value))
    elif isinstance(n,ast.AnnAssign):
        assign.append((n,names(n.target),n.value))
    elif isinstance(n,ast.NamedExpr):
        assign.append((n,names(n.target),n.value))
    elif isinstance(n,ast.With):
        for it in n.items:
            if it.optional_vars is not None: assign.append((n,names(it.optional_vars),it.context_expr))

def exprdeps(node):
    d=literals(node)
    for n in ast.walk(node):
        if isinstance(n,ast.Name): d |= deps.get(n.id,set())
    return d

for _ in range(64):
    changed=False
    for n,ns,v in assign:
        d=exprdeps(v)
        for x in ns:
            nd=deps.get(x,set())|d
            if nd!=deps.get(x,set()):
                deps[x]=nd; changed=True
            if d: orig.setdefault(x,[]).append((getattr(n,"lineno",0),callname(v.func) if isinstance(v,ast.Call) else type(v).__name__))
    if not changed: break

bindrows=[]
for x in sorted(deps):
    if deps[x]:
        bindrows.append([x,"|".join(sorted(deps[x])),str(min([z[0] for z in orig.get(x,[]) if z[0]] or [0])),
                         "|".join(sorted(set(z[1] for z in orig.get(x,[]))))[:500]])

def slicevals(node):
    out=[]
    for n in ast.walk(node):
        if isinstance(n,ast.Constant) and isinstance(n.value,str): out.append(n.value.upper())
    return out

use=[]
target_sets=[]
target_count={SUMMARY:0,FULL:0}
struct_count={SUMMARY:0,FULL:0}
joint_target=0

for n in ast.walk(tree):
    if isinstance(n,ast.Subscript):
        d=exprdeps(n.value)
        if not d: continue
        vals=slicevals(n.slice)
        th=sorted(set(vals)&TARGET)
        sh=sorted({v for v in vals if any(k in v for k in STRUCT)})
        if th or sh:
            cls="TARGET" if th else "STRUCTURAL"
            use.append([str(getattr(n,"lineno",0)),cls,"|".join(th or sh),"|".join(sorted(d)),
                        lines[getattr(n,"lineno",1)-1].strip()[:500]])
            if th:
                target_sets.append(frozenset(d))
                for cid in d: target_count[cid]+=1
                if d=={SUMMARY,FULL}: joint_target+=1
            else:
                for cid in d: struct_count[cid]+=1
    elif isinstance(n,ast.Attribute) and n.attr.upper() in TARGET:
        d=exprdeps(n.value)
        if d:
            use.append([str(getattr(n,"lineno",0)),"TARGET",n.attr.upper(),"|".join(sorted(d)),
                        lines[getattr(n,"lineno",1)-1].strip()[:500]])
            target_sets.append(frozenset(d))
            for cid in d: target_count[cid]+=1
            if d=={SUMMARY,FULL}: joint_target+=1

combo=[]
joint_names=[]
for n,ns,v in assign:
    d=exprdeps(v)
    if d!={SUMMARY,FULL}: continue
    op=callname(v.func).lower() if isinstance(v,ast.Call) else type(v).__name__
    explicit=any(k in op for k in ("merge","join","concat","combine"))
    for x in ns:
        combo.append([x,str(getattr(n,"lineno",0)),op,str(int(explicit)),
                      lines[getattr(n,"lineno",1)-1].strip()[:500]])
        joint_names.append(x)

summary_target_only=any(x==frozenset({SUMMARY}) for x in target_sets)
full_target_only=any(x==frozenset({FULL}) for x in target_sets)
has_joint=bool(joint_names)
distinct_joint=has_joint and ((summary_target_only and struct_count[FULL]>0) or (full_target_only and struct_count[SUMMARY]>0))
joint_proven=(joint_target>0 or distinct_joint)
summary_only=(target_count[SUMMARY]>0 and target_count[FULL]==0 and struct_count[FULL]==0 and not has_joint)
full_only=(target_count[FULL]>0 and target_count[SUMMARY]==0 and struct_count[SUMMARY]==0 and not has_joint)

proved=[]
if joint_proven: proved.append("JOINT_SUMMARY_PLUS_FULL")
if summary_only: proved.append("SUMMARY_ONLY")
if full_only: proved.append("FULL_ONLY")

sel=proved[0] if len(proved)==1 else "NONE"
status="RESOLVED" if sel!="NONE" else "UNRESOLVED"
sel2019={"JOINT_SUMMARY_PLUS_FULL":"SCF_2019_SUMMARY_STATA|SCF_2019_FULL_STATA",
         "SUMMARY_ONLY":"SCF_2019_SUMMARY_STATA",
         "FULL_ONLY":"SCF_2019_FULL_STATA"}.get(sel,"NONE")

updated=[]
for r in prior:
    q=dict(r)
    if q["requirement_index"]=="3" and status=="RESOLVED":
        q["status"]="RESOLVED"; q["selected_candidate_ids"]=sel2019
        q["structural_basis"]=f"E4D1AR1 provenance graph uniquely proves {sel}"
    updated.append(q)

for a,b in zip(prior,updated):
    if a["requirement_index"]!="3": assert a==b

resolved=sum(r["status"]=="RESOLVED" for r in updated)
unresolved=6-resolved
allres=unresolved==0

plan=readtsv(PLAN); pby={r["candidate_id"]:r for r in plan}
ids=[]
if allres:
    for r in updated:
        for cid in r["selected_candidate_ids"].split("|"):
            if cid in pby and pby[cid]["microdata_or_weight_data"]=="1" and cid not in ids: ids.append(cid)
acq=[[cid,pby[cid]["family"],pby[cid]["url"],pby[cid]["role"],"DOWNLOAD_ONLY_AFTER_E4D1B_PRECOMMIT"] for cid in ids]

writetsv(BIND,["binding","candidate_dependencies","first_origin_line","origin_expression_kinds"],bindrows)
writetsv(USES,["line_number","use_class","field_tokens","candidate_dependencies","source_excerpt"],use)
writetsv(COMBOS,["binding","line_number","combination_operator","explicit_merge_join_concat","source_excerpt"],combo)
writetsv(SOURCESET,["candidate_source_set","proven","evidence_summary"],[
["JOINT_SUMMARY_PLUS_FULL",str(int(joint_proven)),f"joint_target={joint_target};joint_bindings={len(joint_names)};distinct_role_joint={int(distinct_joint)}"],
["SUMMARY_ONLY",str(int(summary_only)),f"summary_target={target_count[SUMMARY]};full_target={target_count[FULL]};full_structural={struct_count[FULL]};joint_bindings={len(joint_names)}"],
["FULL_ONLY",str(int(full_only)),f"full_target={target_count[FULL]};summary_target={target_count[SUMMARY]};summary_structural={struct_count[SUMMARY]};joint_bindings={len(joint_names)}"],
])
writetsv(UPDATED,list(prior[0].keys()),[[r[k] for k in prior[0].keys()] for r in updated])
writetsv(ACQ,["candidate_id","family","url","role","acquisition_status"],acq)
writetsv(GATES,["gate","value"],[
["FORENSIC_TARGET_REQUIREMENT_INDEX","3"],["SOURCE_SET_CANDIDATE_COUNT","3"],
["RAW_ARCHIVE_CONTENT_OPENED","0"],["ARCHIVE_MEMBER_LISTING_OPENED","0"],
["NUMERIC_RESULT_ROWS_OPENED","0"],["2019_DATA_FILES_DOWNLOADED","0"],
["2019_MICRODATA_ROWS_OPENED","0"],["2019_ECONOMIC_VALUES_OPENED","0"],
["FILESYSTEM_EXISTENCE_SELECTION_WEIGHT","0"],["NON_REQUIREMENT3_SOURCE_ROWS_MUTATED","0"],
["PROVEN_SOURCE_SET_COUNT",str(len(proved))],["RESOLVED_SOURCE_REQUIREMENT_COUNT",str(resolved)],
["UNRESOLVED_SOURCE_REQUIREMENT_COUNT",str(unresolved)],["TEMPORAL_GEOMETRY_AUTHORIZED","0"],
["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"]])

nextp="E4D1B" if allres else "E4D1AR2"
writetsv(DEC,["decision","value"],[
["REQUIREMENT_3_STATUS",status],["SELECTED_EFFECTIVE_SOURCE_SET",sel],["SELECTED_2019_CANDIDATES",sel2019],
["JOINT_TARGET_USE_COUNT",str(joint_target)],["JOINT_BINDING_COUNT",str(len(joint_names))],
["SUMMARY_TARGET_USE_COUNT",str(target_count[SUMMARY])],["FULL_TARGET_USE_COUNT",str(target_count[FULL])],
["SUMMARY_STRUCTURAL_USE_COUNT",str(struct_count[SUMMARY])],["FULL_STRUCTURAL_USE_COUNT",str(struct_count[FULL])],
["PROVEN_SOURCE_SET_COUNT",str(len(proved))],["RESOLVED_SOURCE_REQUIREMENT_COUNT",str(resolved)],
["UNRESOLVED_SOURCE_REQUIREMENT_COUNT",str(unresolved)],["ALL_2019_SOURCE_LINEAGE_REQUIREMENTS_RESOLVED",str(int(allres))],
["SELECTED_2019_DATA_ARTIFACT_COUNT",str(len(acq))],["2019_DATA_FILES_DOWNLOADED","0"],
["2019_MICRODATA_ROWS_OPENED","0"],["2019_ECONOMIC_VALUES_OPENED","0"],["NEXT_PRIMARY_PHASE_ID",nextp],
["E4D1B_2019_OFFICIAL_SOURCE_ACQUISITION_AND_SCHEMA_AUDIT_AUTHORIZED",str(int(allres))],
["E4D1AR2_HEADER_ONLY_FROZEN_2022_SCHEMA_FORENSIC_AUTHORIZED",str(int(not allres))],
["TEMPORAL_GEOMETRY_AUTHORIZED","0"],["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
["E4D1AR1_SCF_JOINT_SOURCE_PROVENANCE_GRAPH_FORENSIC","PASS"]])

log="\n".join([
"E4D1AR_REUSED_AS_CANONICAL_SCF_SOURCE_AMBIGUITY_STATE=1",
"FORENSIC_TARGET_REQUIREMENT_INDEX=3","SOURCE_SET_CANDIDATE_COUNT=3",
"DEEP_STATIC_PROVENANCE_OPENED_AFTER_E4D1AR1_PRECOMMIT=1",
f"CANDIDATE_TAINTED_BINDING_COUNT={len(bindrows)}",f"TARGET_OR_STRUCTURAL_USE_LEDGER_COUNT={len(use)}",
f"JOINT_TARGET_USE_COUNT={joint_target}",f"JOINT_BINDING_COUNT={len(joint_names)}",
f"DISTINCT_ROLE_JOINT_PROVEN={int(distinct_joint)}",f"SUMMARY_TARGET_USE_COUNT={target_count[SUMMARY]}",
f"FULL_TARGET_USE_COUNT={target_count[FULL]}",f"SUMMARY_STRUCTURAL_USE_COUNT={struct_count[SUMMARY]}",
f"FULL_STRUCTURAL_USE_COUNT={struct_count[FULL]}",f"PROVEN_SOURCE_SET_COUNT={len(proved)}",
f"REQUIREMENT_3_STATUS={status}",f"SELECTED_EFFECTIVE_SOURCE_SET={sel}",
f"SELECTED_2019_CANDIDATES={sel2019}",f"RESOLVED_SOURCE_REQUIREMENT_COUNT={resolved}",
f"UNRESOLVED_SOURCE_REQUIREMENT_COUNT={unresolved}",f"ALL_2019_SOURCE_LINEAGE_REQUIREMENTS_RESOLVED={int(allres)}",
f"SELECTED_2019_DATA_ARTIFACT_COUNT={len(acq)}","RAW_ARCHIVE_CONTENT_OPENED=0","ARCHIVE_MEMBER_LISTING_OPENED=0",
"NUMERIC_RESULT_ROWS_OPENED=0","2019_DATA_FILES_DOWNLOADED=0","2019_MICRODATA_ROWS_OPENED=0",
"2019_ECONOMIC_VALUES_OPENED=0","FILESYSTEM_EXISTENCE_SELECTION_WEIGHT=0","NON_REQUIREMENT3_SOURCE_ROWS_MUTATED=0",
"TEMPORAL_GEOMETRY_AUTHORIZED=0","REAL_INFLATION_ESTIMATION_AUTHORIZED=0",f"NEXT_PRIMARY_PHASE_ID={nextp}",
f"E4D1B_2019_OFFICIAL_SOURCE_ACQUISITION_AND_SCHEMA_AUDIT_AUTHORIZED={int(allres)}",
f"E4D1AR2_HEADER_ONLY_FROZEN_2022_SCHEMA_FORENSIC_AUTHORIZED={int(not allres)}",
"E4D1AR1_SCF_JOINT_SOURCE_PROVENANCE_GRAPH_FORENSIC=PASS",
])+"\n"
EXEC.write_text(log,encoding="utf-8"); AUDIT.write_text(log,encoding="utf-8"); print(log,end="")
