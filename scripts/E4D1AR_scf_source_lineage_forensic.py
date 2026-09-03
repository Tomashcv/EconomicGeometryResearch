#!/usr/bin/env python3
from pathlib import Path
import ast,csv,json,re

ROOT=Path(__file__).resolve().parents[1]

CONTRACT=ROOT/"data/metadata/E4D1AR_scf_source_lineage_forensic_contract.json"
CANDIDATES=ROOT/"data/metadata/E4D1AR_scf_candidate_source_registry.tsv"
METHOD=ROOT/"data/metadata/E4D1AR_static_evidence_hierarchy.tsv"
A_RESOLVED=ROOT/"data/results/E4D1A_resolved_2019_source_lineage.tsv"
A_DECISION=ROOT/"data/results/E4D1A_2019_official_source_lineage_acquisition_decision.tsv"
KD_EXEC=ROOT/"scripts/E4A2F_first_scf_kd_inference_execution.py"

STATICINV=ROOT/"data/results/E4D1AR_scf_static_lineage_evidence_inventory.tsv"
CANDREG=ROOT/"data/results/E4D1AR_scf_candidate_effective_use_registry.tsv"
REQ3=ROOT/"data/results/E4D1AR_requirement3_resolution.tsv"
UPDATED=ROOT/"data/results/E4D1AR_updated_2019_source_lineage.tsv"
ACQPLAN=ROOT/"data/results/E4D1AR_2019_microdata_acquisition_plan.tsv"
GATES=ROOT/"data/results/E4D1AR_forensic_hard_gates.tsv"
DECISION=ROOT/"data/results/E4D1AR_scf_source_lineage_forensic_decision.tsv"
EXEC=ROOT/"data/metadata/E4D1AR_execution.txt"
AUDIT=ROOT/"data/metadata/E4D1AR_scf_source_lineage_forensic_audit.txt"

c=json.loads(CONTRACT.read_text(encoding="utf-8"))

def read_tsv(p):
    with p.open("r",encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f,delimiter="\t"))

def write_tsv(p,header,rows):
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,delimiter="\t",lineterminator="\n")
        w.writerow(header); w.writerows(rows)

cands=read_tsv(CANDIDATES)
assert len(cands)==2
prior=read_tsv(A_RESOLVED)
assert len(prior)==6
un=[r for r in prior if r["status"]=="UNRESOLVED"]
assert len(un)==1 and un[0]["requirement_index"]=="3"

tokens={
    "SCF_SUMMARY_STATA":"scfp2022s.zip",
    "SCF_FULL_STATA":"scf2022s.zip",
}

allowed_files=[]
for root_name in ["scripts","docs","data/metadata"]:
    rr=ROOT/root_name
    for p in sorted(rr.rglob("*")):
        if not p.is_file():
            continue
        if "E4D1AR_" in p.name:
            continue
        if p.stat().st_size > 5_000_000:
            continue
        if p.suffix.lower() not in {".py",".md",".txt",".tsv",".json",".sas",".csv"}:
            continue
        allowed_files.append(p)

inventory=[]
content_cache={}
for p in allowed_files:
    try:
        text=p.read_text(encoding="utf-8",errors="strict")
    except UnicodeDecodeError:
        continue
    content_cache[p]=text
    low=text.lower()
    for cid,tok in tokens.items():
        if tok in low:
            for lineno,line in enumerate(text.splitlines(),1):
                if tok in line.lower():
                    inventory.append([
                        cid,str(p.relative_to(ROOT)),str(lineno),
                        "TOKEN_OCCURRENCE",line.strip()[:500]
                    ])
    for lineno,line in enumerate(text.splitlines(),1):
        ll=line.lower()
        if "fin" in ll and "pirtotal" in ll:
            for cid,tok in tokens.items():
                stems=["scfp2022","scfp2022s"] if cid=="SCF_SUMMARY_STATA" else ["scf2022s","rscfp2022"]
                if tok in ll or any(st in ll for st in stems):
                    inventory.append([
                        cid,str(p.relative_to(ROOT)),str(lineno),
                        "FIN_PIRTOTAL_SOURCE_COOCCURRENCE",line.strip()[:500]
                    ])

exec_text=KD_EXEC.read_text(encoding="utf-8")
tree=ast.parse(exec_text)

def full_call_name(node):
    if isinstance(node,ast.Name): return node.id
    if isinstance(node,ast.Attribute):
        left=full_call_name(node.value)
        return (left+"."+node.attr) if left else node.attr
    return ""

def const_candidate_deps(node, env):
    deps=set()
    for n in ast.walk(node):
        if isinstance(n,ast.Constant) and isinstance(n.value,str):
            lv=n.value.lower()
            for cid,tok in tokens.items():
                if tok in lv:
                    deps.add(cid)
        elif isinstance(n,ast.Name):
            deps |= env.get(n.id,set())
    return deps

assign_nodes=[n for n in ast.walk(tree) if isinstance(n,(ast.Assign,ast.AnnAssign))]
env={}
for _ in range(20):
    changed=False
    for n in assign_nodes:
        deps=const_candidate_deps(n.value,env)
        targets=[]
        if isinstance(n,ast.Assign):
            targets=[t.id for t in n.targets if isinstance(t,ast.Name)]
        elif isinstance(n.target,ast.Name):
            targets=[n.target.id]
        for name in targets:
            old=env.get(name,set()); new=old|deps
            if new!=old:
                env[name]=new; changed=True
    if not changed: break

strong_read_names={
    "zipfile.ZipFile","ZipFile","pd.read_stata","pandas.read_stata",
    "pd.read_sas","pandas.read_sas","pd.read_csv","pandas.read_csv",
    "read_stata","read_sas","read_csv"
}
direct_calls={cid:[] for cid in tokens}
weak_calls={cid:[] for cid in tokens}

for n in ast.walk(tree):
    if not isinstance(n,ast.Call):
        continue
    deps=set()
    for a in n.args: deps |= const_candidate_deps(a,env)
    for kw in n.keywords: deps |= const_candidate_deps(kw.value,env)
    if not deps: continue
    name=full_call_name(n.func)
    line=getattr(n,"lineno",0)
    for cid in deps:
        if name in strong_read_names or any(x in name.lower() for x in ["zipfile","read_stata","read_sas","read_csv"]):
            direct_calls[cid].append((line,name))
        else:
            weak_calls[cid].append((line,name))

exec_literal={cid:(tok in exec_text.lower()) for cid,tok in tokens.items()}

phase_local={cid:[] for cid in tokens}
for p,text in content_cache.items():
    if "e4a2f" not in p.name.lower():
        continue
    for cid,tok in tokens.items():
        for lineno,line in enumerate(text.splitlines(),1):
            ll=line.lower()
            if tok in ll:
                positive=any(k in ll for k in ["source","input","path","archive","zip","raw"])
                negative=any(k in ll for k in ["candidate","alternative","either","or full","or summary"])
                if positive and not negative:
                    phase_local[cid].append((str(p.relative_to(ROOT)),lineno,line.strip()[:500]))

schema_hits={cid:[] for cid in tokens}
for p,text in content_cache.items():
    rel=str(p.relative_to(ROOT)).lower()
    if not any(k in rel for k in ["schema","lineage","source","contract","manifest","audit"]):
        continue
    for lineno,line in enumerate(text.splitlines(),1):
        ll=line.lower()
        for cid,tok in tokens.items():
            if tok in ll and ("fin" in ll or "pirtotal" in ll):
                schema_hits[cid].append((str(p.relative_to(ROOT)),lineno,line.strip()[:500]))

schema_both={}
for cid,hits in schema_hits.items():
    joined=" ".join(x[2].lower() for x in hits)
    schema_both[cid]=("fin" in joined and "pirtotal" in joined)

strong_yes=[cid for cid in tokens if direct_calls[cid]]
phase_yes=[cid for cid in tokens if phase_local[cid]]
schema_yes=[cid for cid in tokens if schema_both[cid]]

selected=None
selection_basis="NONE"
if len(strong_yes)==1:
    selected=strong_yes[0]
    selection_basis="DIRECT_EFFECTIVE_EXECUTOR_SOURCE"
elif len(strong_yes)==0 and len(phase_yes)==1:
    selected=phase_yes[0]
    selection_basis="PHASE_LOCAL_STATIC_LINEAGE"
elif len(strong_yes)==0 and len(phase_yes)==0 and len(schema_yes)==1:
    selected=schema_yes[0]
    selection_basis="TARGET_VARIABLE_SOURCE_SCHEMA"

status="RESOLVED" if selected else "UNRESOLVED"

cand_rows=[]
for cid in ["SCF_SUMMARY_STATA","SCF_FULL_STATA"]:
    cand_rows.append([
        cid,str(int(exec_literal[cid])),str(len(direct_calls[cid])),
        str(len(weak_calls[cid])),str(len(phase_local[cid])),
        str(len(schema_hits[cid])),str(int(schema_both[cid])),
        "SELECTED" if cid==selected else ("NOT_SELECTED" if selected else "AMBIGUOUS"),
    ])

for cid,arr in direct_calls.items():
    for line,name in arr:
        inventory.append([cid,str(KD_EXEC.relative_to(ROOT)),str(line),"DIRECT_EFFECTIVE_EXECUTOR_SOURCE",name])
for cid,arr in weak_calls.items():
    for line,name in arr:
        inventory.append([cid,str(KD_EXEC.relative_to(ROOT)),str(line),"EXECUTOR_NONSELECTING_REFERENCE",name])
for cid,arr in phase_local.items():
    for p,line,text in arr:
        inventory.append([cid,p,str(line),"PHASE_LOCAL_STATIC_LINEAGE",text])
for cid,arr in schema_hits.items():
    for p,line,text in arr:
        inventory.append([cid,p,str(line),"TARGET_VARIABLE_SOURCE_SCHEMA",text])

updated=[]
for row in prior:
    q=dict(row)
    if q["requirement_index"]=="3" and selected:
        chosen_2019="SCF_2019_SUMMARY_STATA" if selected=="SCF_SUMMARY_STATA" else "SCF_2019_FULL_STATA"
        q["status"]="RESOLVED"
        q["selected_candidate_ids"]=chosen_2019
        q["structural_basis"]=f"E4D1AR unique effective 2022 lineage via {selection_basis}"
    updated.append(q)

for old,new in zip(prior,updated):
    if old["requirement_index"]!="3":
        assert old==new

all_resolved=all(r["status"]=="RESOLVED" for r in updated)
resolved_count=sum(r["status"]=="RESOLVED" for r in updated)
unresolved_count=6-resolved_count

candidate_plan=read_tsv(ROOT/"data/metadata/E4D1A_official_2019_source_candidate_plan.tsv")
cby={r["candidate_id"]:r for r in candidate_plan}
acq_ids=[]
if all_resolved:
    for r in updated:
        for cid in r["selected_candidate_ids"].split("|"):
            if not cid or cid=="NONE": continue
            if cid in cby and cby[cid]["microdata_or_weight_data"]=="1" and cid not in acq_ids:
                acq_ids.append(cid)

acq_rows=[]
for cid in acq_ids:
    r=cby[cid]
    acq_rows.append([cid,r["family"],r["url"],r["role"],"DOWNLOAD_ONLY_AFTER_E4D1B_PRECOMMIT"])

write_tsv(STATICINV,["candidate_id","static_path","line_number","evidence_class","evidence_excerpt"],inventory)
write_tsv(CANDREG,
          ["candidate_id","executor_literal_present","direct_effective_read_call_count",
           "executor_nonselecting_reference_count","phase_local_lineage_count",
           "target_schema_hit_count","target_schema_both_FIN_PIRTOTAL",
           "forensic_disposition"],cand_rows)
write_tsv(REQ3,
          ["requirement_index","family","prior_status","new_status","selected_2022_source_family",
           "selected_2019_candidate","selection_basis"],
          [["3","SCF","UNRESOLVED",status,
            selected if selected else "NONE",
            "SCF_2019_SUMMARY_STATA" if selected=="SCF_SUMMARY_STATA" else "SCF_2019_FULL_STATA" if selected=="SCF_FULL_STATA" else "NONE",
            selection_basis]])
write_tsv(UPDATED,list(prior[0].keys()),[[r[k] for k in prior[0].keys()] for r in updated])
write_tsv(ACQPLAN,["candidate_id","family","url","role","acquisition_status"],acq_rows)

next_phase="E4D1B" if all_resolved else "E4D1AR1"
write_tsv(GATES,["gate","value"],[
["EXACT_ONE_PRIOR_UNRESOLVED_REQUIREMENT","PASS"],
["FORENSIC_TARGET_REQUIREMENT_INDEX","3"],
["CANDIDATE_COUNT","2"],
["FILESYSTEM_EXISTENCE_SELECTION_WEIGHT","0"],
["RAW_DATA_CONTENT_OPENED","0"],
["NUMERIC_RESULT_ROWS_OPENED","0"],
["2019_DATA_FILES_DOWNLOADED","0"],
["2019_MICRODATA_ROWS_OPENED","0"],
["2019_ECONOMIC_VALUES_OPENED","0"],
["NON_REQUIREMENT3_SOURCE_ROWS_MUTATED","0"],
["RESOLVED_SOURCE_REQUIREMENT_COUNT",str(resolved_count)],
["UNRESOLVED_SOURCE_REQUIREMENT_COUNT",str(unresolved_count)],
["TEMPORAL_GEOMETRY_AUTHORIZED","0"],
["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
])

write_tsv(DECISION,["decision","value"],[
["REQUIREMENT_3_STATUS",status],
["SELECTED_2022_SOURCE_FAMILY",selected if selected else "NONE"],
["SELECTED_2019_CANDIDATE","SCF_2019_SUMMARY_STATA" if selected=="SCF_SUMMARY_STATA" else "SCF_2019_FULL_STATA" if selected=="SCF_FULL_STATA" else "NONE"],
["SELECTION_BASIS",selection_basis],
["RESOLVED_SOURCE_REQUIREMENT_COUNT",str(resolved_count)],
["UNRESOLVED_SOURCE_REQUIREMENT_COUNT",str(unresolved_count)],
["ALL_2019_SOURCE_LINEAGE_REQUIREMENTS_RESOLVED",str(int(all_resolved))],
["SELECTED_2019_DATA_ARTIFACT_COUNT",str(len(acq_rows))],
["2019_DATA_FILES_DOWNLOADED","0"],
["2019_MICRODATA_ROWS_OPENED","0"],
["2019_ECONOMIC_VALUES_OPENED","0"],
["NEXT_PRIMARY_PHASE_ID",next_phase],
["E4D1B_2019_OFFICIAL_SOURCE_ACQUISITION_AND_SCHEMA_AUDIT_AUTHORIZED",str(int(all_resolved))],
["E4D1AR1_DEEPER_STATIC_PROVENANCE_FORENSIC_AUTHORIZED",str(int(not all_resolved))],
["TEMPORAL_GEOMETRY_AUTHORIZED","0"],
["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
["E4D1AR_SCF_SOURCE_LINEAGE_FORENSIC","PASS"],
])

log="\n".join([
"E4D1A_R0_REUSED_AS_CANONICAL_SOURCE_LINEAGE_STATE=1",
"FORENSIC_TARGET_REQUIREMENT_INDEX=3",
"CANDIDATE_COUNT=2",
"STATIC_2022_LINEAGE_CONTENT_OPENED_AFTER_E4D1AR_PRECOMMIT=1",
f"SUMMARY_DIRECT_EFFECTIVE_READ_CALL_COUNT={len(direct_calls['SCF_SUMMARY_STATA'])}",
f"FULL_DIRECT_EFFECTIVE_READ_CALL_COUNT={len(direct_calls['SCF_FULL_STATA'])}",
f"SUMMARY_PHASE_LOCAL_LINEAGE_COUNT={len(phase_local['SCF_SUMMARY_STATA'])}",
f"FULL_PHASE_LOCAL_LINEAGE_COUNT={len(phase_local['SCF_FULL_STATA'])}",
f"SUMMARY_TARGET_SCHEMA_BOTH_FIN_PIRTOTAL={int(schema_both['SCF_SUMMARY_STATA'])}",
f"FULL_TARGET_SCHEMA_BOTH_FIN_PIRTOTAL={int(schema_both['SCF_FULL_STATA'])}",
f"REQUIREMENT_3_STATUS={status}",
f"SELECTED_2022_SOURCE_FAMILY={selected if selected else 'NONE'}",
f"SELECTION_BASIS={selection_basis}",
f"RESOLVED_SOURCE_REQUIREMENT_COUNT={resolved_count}",
f"UNRESOLVED_SOURCE_REQUIREMENT_COUNT={unresolved_count}",
f"ALL_2019_SOURCE_LINEAGE_REQUIREMENTS_RESOLVED={int(all_resolved)}",
f"SELECTED_2019_DATA_ARTIFACT_COUNT={len(acq_rows)}",
"RAW_DATA_CONTENT_OPENED=0",
"NUMERIC_RESULT_ROWS_OPENED=0",
"2019_DATA_FILES_DOWNLOADED=0",
"2019_MICRODATA_ROWS_OPENED=0",
"2019_ECONOMIC_VALUES_OPENED=0",
"NON_REQUIREMENT3_SOURCE_ROWS_MUTATED=0",
"TEMPORAL_GEOMETRY_AUTHORIZED=0",
"REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
f"NEXT_PRIMARY_PHASE_ID={next_phase}",
f"E4D1B_2019_OFFICIAL_SOURCE_ACQUISITION_AND_SCHEMA_AUDIT_AUTHORIZED={int(all_resolved)}",
f"E4D1AR1_DEEPER_STATIC_PROVENANCE_FORENSIC_AUTHORIZED={int(not all_resolved)}",
"E4D1AR_SCF_SOURCE_LINEAGE_FORENSIC=PASS",
])+"\n"
EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
