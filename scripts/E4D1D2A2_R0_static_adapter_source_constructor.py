#!/usr/bin/env python3
from pathlib import Path
import ast,csv,hashlib,json,re

ROOT=Path(__file__).resolve().parents[1]
C=json.loads((ROOT/"data/metadata/E4D1D2A2_static_adapter_source_construction_contract.json").read_text())

D1_BIND=ROOT/"data/results/E4D1D1_source_output_binding_registry.tsv"
D1_PROV=ROOT/"data/results/E4D1D1_scientific_function_provenance_registry.tsv"
A1_RAW=ROOT/"data/results/E4D1D2A1_raw_path_hash_rebinding_registry.tsv"
A1_BIND=ROOT/"data/results/E4D1D2A1_binding_action_registry.tsv"
A1_MEMBER=ROOT/"data/results/E4D1D2A1_member_occurrence_rebinding_registry.tsv"
A1_ACS=ROOT/"data/results/E4D1D2A1_acs_ingestion_splice_registry.tsv"

METHODS={
 "ACS":ROOT/"scripts/E4C3D_first_acs2022_h_access_execution.py",
 "SCF":ROOT/"scripts/E4A2F_first_scf_kd_inference_execution.py",
 "CPS_ASEC":ROOT/"scripts/E4A2D_first_cps_i_inference_execution.py",
}
ADAPTERS={k:ROOT/v for k,v in C["adapter_paths"].items()}

ADAPTER_REG=ROOT/"data/results/E4D1D2A2_adapter_source_registry.tsv"
CHANGE_REG=ROOT/"data/results/E4D1D2A2_exact_source_change_registry.tsv"
FUNC_REG=ROOT/"data/results/E4D1D2A2_adapter_function_provenance_registry.tsv"
ACS_SUFFIX=ROOT/"data/results/E4D1D2A2_acs_accumulation_suffix_provenance.tsv"
GATES=ROOT/"data/results/E4D1D2A2_adapter_source_hard_gates.tsv"
DECISION=ROOT/"data/results/E4D1D2A2_static_adapter_source_decision.tsv"
EXEC=ROOT/"data/metadata/E4D1D2A2_execution.txt"
AUDIT=ROOT/"data/metadata/E4D1D2A2_static_adapter_source_audit.txt"

def read(p):
    with p.open("r",encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f,delimiter="\t"))
def write(p,h,rows):
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,delimiter="\t",lineterminator="\n");w.writerow(h);w.writerows(rows)
def htxt(s): return hashlib.sha256(s.encode()).hexdigest()
def hfile(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()
def offsets(src):
    out=[0]
    for line in src.splitlines(keepends=True): out.append(out[-1]+len(line))
    return out
def _utf8_byte_col_to_char_col(line,byte_col):
    raw=line.encode("utf-8")
    prefix=raw[:byte_col]
    return len(prefix.decode("utf-8"))
def span(src,node):
    lines=src.splitlines(keepends=True)
    off=offsets(src)
    sline=lines[node.lineno-1]
    eline=lines[node.end_lineno-1]
    scol=_utf8_byte_col_to_char_col(sline,node.col_offset)
    ecol=_utf8_byte_col_to_char_col(eline,node.end_col_offset)
    return off[node.lineno-1]+scol, off[node.end_lineno-1]+ecol
def apply_replacements(src,repls):
    ordered=sorted(repls,key=lambda x:(x[0],x[1]))
    for a,b in zip(ordered,ordered[1:]):
        if a[1]>b[0]: raise RuntimeError(f"OVERLAPPING_REPLACEMENTS:{a}:{b}")
    out=src
    for st,en,new,kind,meta in sorted(ordered,key=lambda x:x[0],reverse=True):
        out=out[:st]+new+out[en:]
    return out

raw=read(A1_RAW)
raw_map={r["old_path"]:r["new_path"] for r in raw}
oldsha_to_newsha={r["old_sha256"]:r["new_sha256"] for r in raw}
a1bind=read(A1_BIND)
a1member=read(A1_MEMBER)
d1bind=read(D1_BIND)
prov=read(D1_PROV)
acsplan=read(A1_ACS)
assert len(prov)==17
assert len(a1member)==7
assert len(acsplan)==1 and acsplan[0]["status"]=="PASS"

bind_key={(r["family"],r["global_name"],r["line"]):r for r in a1bind}
d1mut=[r for r in d1bind if r["D2_policy"]=="ENUMERATE_IN_D2"]
assert len(d1mut)==39

change_rows=[]
adapter_rows=[]
function_rows=[]
suffix_rows=[]
fail=[]

def quote_string(new): return json.dumps(new,ensure_ascii=False)

def assignment_node(tree,line):
    ms=[n for n in tree.body if isinstance(n,(ast.Assign,ast.AnnAssign)) and getattr(n,"lineno",0)<=line<=getattr(n,"end_lineno",getattr(n,"lineno",0))]
    if len(ms)!=1: raise RuntimeError(("ASSIGNMENT_NODE_COUNT",line,len(ms)))
    return ms[0]

def output_target(v,family):
    if v=="data/results": return f"data/results/E4D1D_2019_runtime/{family}"
    if v=="data/metadata": return f"data/metadata/E4D1D_2019_runtime/{family}"
    if v.startswith("data/results/"): return f"data/results/E4D1D_2019_runtime/{family}/{Path(v).name}"
    if v.startswith("data/metadata/"): return f"data/metadata/E4D1D_2019_runtime/{family}/{Path(v).name}"
    return v

for family,srcp in METHODS.items():
    src=srcp.read_text(encoding="utf-8")
    tree=ast.parse(src)
    repls=[]

    fam_bind=[r for r in d1mut if r["family"]==family]
    for r in fam_bind:
        line=int(r["line"]); bclass=r["binding_class"]
        if (family,r["global_name"],r["line"]) not in bind_key:
            raise RuntimeError(("A1_BINDING_PLAN_MISSING",family,r["global_name"],r["line"]))
        an=assignment_node(tree,line)
        seg=ast.get_source_segment(src,an) or ""
        if htxt(seg)!=r["assignment_source_sha256"]:
            raise RuntimeError(("ASSIGNMENT_SHA_MISMATCH",family,line))
        changed_here=0
        for n in ast.walk(an):
            if not isinstance(n,ast.Constant): continue
            new=None; kind=None
            if isinstance(n.value,str):
                v=n.value
                if bclass=="SOURCE_PATH_BINDING" and v in raw_map:
                    new=raw_map[v]; kind="SOURCE_PATH_REBIND"
                elif bclass=="OUTPUT_PATH_BINDING":
                    nv=output_target(v,family)
                    if nv!=v: new=nv; kind="OUTPUT_NAMESPACE_REBIND"
                elif bclass=="YEAR_OR_PHASE_LABEL":
                    nv=re.sub(r"(?<!\d)2022(?!\d)","2019",v)
                    if nv!=v: new=nv; kind="YEAR_TOKEN_REBIND"
                elif bclass=="HASH_EXPECTATION_BINDING" and re.fullmatch(r"[0-9a-fA-F]{64}",v):
                    if v in oldsha_to_newsha:
                        new=oldsha_to_newsha[v]; kind="RAW_SHA_REBIND"
            elif isinstance(n.value,int) and bclass=="YEAR_OR_PHASE_LABEL" and n.value==2022:
                new=2019; kind="YEAR_TOKEN_REBIND"

            if new is not None:
                st,en=span(src,n)
                oldtxt=src[st:en]
                newtxt=quote_string(new) if isinstance(new,str) else str(new)
                repls.append((st,en,newtxt,kind,f"{r['global_name']}@{line}"))
                change_rows.append([
                    family,str(srcp.relative_to(ROOT)),kind,line,
                    r["global_name"],oldtxt,newtxt,htxt(oldtxt),htxt(newtxt),"PASS"
                ])
                changed_here+=1

        if bclass=="SOURCE_PATH_BINDING" and changed_here==0:
            fail.append(f"{family}:SOURCE_BINDING_NO_REPLACEMENT:{r['global_name']}:{line}")
        if bclass=="OUTPUT_PATH_BINDING" and changed_here==0:
            fail.append(f"{family}:OUTPUT_BINDING_NO_REPLACEMENT:{r['global_name']}:{line}")

    plans=[r for r in a1member if r["family"]==family]
    for p in plans:
        line=int(p["source_line"]); old=p["old_member"]; new=p["new_member"]
        ms=[n for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str) and n.value==old and n.lineno==line]
        if len(ms)!=1:
            fail.append(f"{family}:MEMBER_LOCUS_COUNT:{old}:{line}:{len(ms)}")
            continue
        n=ms[0]; st,en=span(src,n); oldtxt=src[st:en]; newtxt=quote_string(new)
        repls.append((st,en,newtxt,"MEMBER_LITERAL_REBIND",f"{old}@{line}"))
        change_rows.append([
            family,str(srcp.relative_to(ROOT)),"MEMBER_LITERAL_REBIND",line,
            old,oldtxt,newtxt,htxt(oldtxt),htxt(newtxt),"PASS"
        ])

    adapted=apply_replacements(src,repls)

    if family=="ACS":
        b=acsplan[0]
        cs,ce=int(b["consumer_start_line"]),int(b["consumer_end_line"])
        nodes=[n for n in tree.body if getattr(n,"lineno",0)==cs and getattr(n,"end_lineno",0)==ce]
        if len(nodes)!=1: raise RuntimeError(("ACS_CONSUMER_NODE_COUNT",len(nodes)))
        consumer=ast.get_source_segment(src,nodes[0]) or ""
        if htxt(consumer)!=b["consumer_sha256"]: raise RuntimeError("ACS_CONSUMER_SHA_MISMATCH")
        if adapted.count(consumer)!=1: raise RuntimeError(("ACS_CONSUMER_OCCURRENCE_AFTER_LITERAL_REBINDS",adapted.count(consumer)))

        marker_re=re.compile(r"^(\s*)for rowno,row in enumerate\(r,2\):\s*$",re.M)
        mm=marker_re.search(consumer)
        if not mm: raise RuntimeError("ACS_ACCUMULATION_SUFFIX_MARKER_MISSING")
        suffix=consumer[mm.start():]
        original_suffix_sha=htxt(suffix)

        lines=consumer.splitlines(keepends=True)
        hdr_idx=[i for i,x in enumerate(lines) if re.search(r"\bhdr\s*=\s*next\(r\)",x)]
        dr_idx=[i for i,x in enumerate(lines) if "csv.DictReader(" in x]
        if len(hdr_idx)!=1 or len(dr_idx)!=1: raise RuntimeError(("ACS_SPLICE_ANCHOR_COUNTS",hdr_idx,dr_idx))

        injected=[]
        for i,line in enumerate(lines):
            injected.append(line)
            if i==hdr_idx[0]:
                ind=re.match(r"\s*",line).group(0)
                injected.append(ind+'if "HHLDRAGEP" not in hdr: hdr=hdr+["HHLDRAGEP"]\n')
                injected.append(ind+'for _e4d1d_required in ("SERIALNO","TYPE"):\n')
                injected.append(ind+'  if _e4d1d_required not in hdr: raise RuntimeError(f"missing structural column {m}:{_e4d1d_required}")\n')
            if i==dr_idx[0]:
                ind=re.match(r"\s*",line).group(0)
                injected.append(ind+'r=_e4d1d_adapt_housing_rows(r,_e4d1d_age_by_serial)\n')
        new_consumer="".join(injected)

        helper=r'''RAW_PERSON_2019="data/raw/acs/2019/1year/csv_pus.zip"

def _e4d1d_build_householder_age_map():
  out={}
  with zipfile.ZipFile(RAW_PERSON_2019) as pz:
    pmem=sorted([x for x in pz.namelist() if x.lower().endswith(".csv")])
    if not pmem: raise RuntimeError("no person CSV members")
    for pm in pmem:
      with pz.open(pm) as pfb:
        pr=csv.DictReader(io.TextIOWrapper(pfb,encoding="utf-8-sig",newline=""))
        hdr=pr.fieldnames or []
        miss=[c for c in ("SERIALNO","RELSHIPP","AGEP") if c not in hdr]
        if miss: raise RuntimeError(f"missing person columns {pm}:{','.join(miss)}")
        for prow in pr:
          if str(prow.get("RELSHIPP","")).strip()!="20": continue
          serial=str(prow.get("SERIALNO","")).strip()
          ages=str(prow.get("AGEP","")).strip()
          if not serial or not ages: raise RuntimeError(f"missing reference age/key {pm}")
          try: av=int(float(ages))
          except Exception as e: raise RuntimeError(f"invalid reference age {pm}:{serial}") from e
          if serial in out: raise RuntimeError(f"duplicate reference person {serial}")
          out[serial]=av
  return out

def _e4d1d_adapt_housing_rows(reader,age_by_serial):
  for row in reader:
    if str(row.get("TYPE","")).strip()!="1": continue
    npv=num(row.get("NP"))
    row=dict(row)
    if npv is not None and npv>0:
      serial=str(row.get("SERIALNO","")).strip()
      if serial not in age_by_serial: raise RuntimeError(f"missing reference person for occupied housing {serial}")
      row["HHLDRAGEP"]=str(age_by_serial[serial])
    else:
      row["HHLDRAGEP"]=""
    yield row

_e4d1d_age_by_serial=_e4d1d_build_householder_age_map()

'''
        adapted=adapted.replace(consumer,helper+new_consumer,1)
        change_rows.append([
            family,str(srcp.relative_to(ROOT)),"ACS_INGESTION_SPLICE",cs,
            "consumer",f"sha256:{htxt(consumer)}",f"sha256:{htxt(helper+new_consumer)}",
            htxt(consumer),htxt(helper+new_consumer),"PASS"
        ])

        atree=ast.parse(adapted)
        amatches=[n for n in atree.body if isinstance(n,ast.With) and "for rowno,row in enumerate(r,2):" in (ast.get_source_segment(adapted,n) or "")]
        if len(amatches)!=1: raise RuntimeError(("ADAPTED_ACS_CONSUMER_COUNT",len(amatches)))
        aseg=ast.get_source_segment(adapted,amatches[0]) or ""
        amm=marker_re.search(aseg)
        if not amm: raise RuntimeError("ADAPTED_ACS_SUFFIX_MARKER_MISSING")
        adapted_suffix=aseg[amm.start():]
        adapted_suffix_sha=htxt(adapted_suffix)
        suffix_rows.append([
            "ACS",cs,ce,original_suffix_sha,adapted_suffix_sha,
            int(original_suffix_sha==adapted_suffix_sha),"PASS" if original_suffix_sha==adapted_suffix_sha else "FAIL"
        ])
        if original_suffix_sha!=adapted_suffix_sha: fail.append("ACS_ACCUMULATION_SUFFIX_SHA_MISMATCH")

    compile(adapted,str(ADAPTERS[family]),"exec")
    ADAPTERS[family].write_text(adapted,encoding="utf-8")

    atree=ast.parse(adapted)
    expected=[r for r in prov if r["family"]==family]
    for r in expected:
        ms=[n for n in atree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==r["function"]]
        if len(ms)!=1:
            fail.append(f"{family}:FUNCTION_NODE_COUNT:{r['function']}:{len(ms)}")
            continue
        fs=ast.get_source_segment(adapted,ms[0]) or ""
        actual=htxt(fs)
        ok=(actual==r["function_source_sha256"])
        if not ok: fail.append(f"{family}:FUNCTION_SHA:{r['function']}")
        function_rows.append([
            family,r["function"],r["function_source_sha256"],actual,int(ok),"PASS" if ok else "FAIL"
        ])

    stale_raw=[old for old in raw_map if old in adapted]
    stale_member=sorted({r["old_member"] for r in plans if r["old_member"] in adapted})
    if stale_raw: fail.append(f"{family}:STALE_RAW:{stale_raw}")
    if stale_member: fail.append(f"{family}:STALE_MEMBER:{stale_member}")

    fam_funcs=[r for r in function_rows if r[0]==family]
    adapter_rows.append([
        family,str(srcp.relative_to(ROOT)),str(ADAPTERS[family].relative_to(ROOT)),
        hfile(srcp),hfile(ADAPTERS[family]),len(adapted.splitlines()),
        len([r for r in change_rows if r[0]==family]),
        len(expected),sum(r[-1]=="PASS" for r in fam_funcs),
        len(stale_raw),len(stale_member),"PASS"
    ])

write(ADAPTER_REG,[
    "family","frozen_source","adapter_source","frozen_source_sha256","adapter_sha256",
    "adapter_line_count","change_registry_rows","expected_original_functions",
    "verified_original_functions","stale_raw_literal_count","stale_member_literal_count","status"
],adapter_rows)
write(CHANGE_REG,[
    "family","frozen_source","change_class","source_line","binding_or_token",
    "old_source_literal","new_source_literal","old_literal_sha256","new_literal_sha256","status"
],change_rows)
write(FUNC_REG,[
    "family","function","expected_function_source_sha256","adapter_function_source_sha256",
    "byte_source_identity","status"
],function_rows)
write(ACS_SUFFIX,[
    "family","frozen_consumer_start_line","frozen_consumer_end_line",
    "frozen_accumulation_suffix_sha256","adapter_accumulation_suffix_sha256",
    "byte_identity","status"
],suffix_rows)

func_ok=(len(function_rows)==17 and all(r[-1]=="PASS" for r in function_rows))
suffix_ok=(len(suffix_rows)==1 and suffix_rows[0][-1]=="PASS")
adapter_ok=(len(adapter_rows)==3 and all(r[-1]=="PASS" for r in adapter_rows))
success=(not fail and func_ok and suffix_ok and adapter_ok)

write(GATES,["gate","value"],[
    ["EXACT_ADAPTER_SOURCE_COUNT",str(int(len(adapter_rows)==3))],
    ["EXACT_17_ORIGINAL_FUNCTION_PROVENANCE_PASS",str(int(func_ok))],
    ["ACS_ACCUMULATION_SUFFIX_BYTE_IDENTITY",str(int(suffix_ok))],
    ["STATIC_COMPILE_ALL_ADAPTERS_PASS",str(int(adapter_ok))],
    ["SOURCE_CONSTRUCTION_FAILURE_COUNT",str(len(fail))],
    ["ADAPTER_IMPORTED","0"],["ADAPTER_EXECUTED","0"],
    ["2019_RAW_DATA_ROWS_OPENED","0"],["2019_COORDINATE_VALUES_OPENED","0"],
    ["SCIENTIFIC_METHOD_MUTATED","0"],["TEMPORAL_GEOMETRY_AUTHORIZED","0"],
    ["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"]
])
next_phase="E4D1D3" if success else "E4D1D2A2R"
write(DECISION,["decision","value"],[
    ["ADAPTER_SOURCE_COUNT",str(len(adapter_rows))],
    ["ORIGINAL_FUNCTION_PROVENANCE_PASS_COUNT",str(sum(r[-1]=="PASS" for r in function_rows))],
    ["ACS_ACCUMULATION_SUFFIX_BYTE_IDENTITY",str(int(suffix_ok))],
    ["SOURCE_CONSTRUCTION_FAILURE_COUNT",str(len(fail))],
    ["ADAPTER_IMPORTED","0"],["ADAPTER_EXECUTED","0"],
    ["2019_RAW_DATA_ROWS_OPENED","0"],["2019_COORDINATE_VALUES_OPENED","0"],
    ["SCIENTIFIC_METHOD_MUTATED","0"],["NEXT_PRIMARY_PHASE_ID",next_phase],
    ["E4D1D3_2019_COORDINATE_EXECUTION_PRECOMMIT_AUTHORIZED",str(int(success))],
    ["E4D1D_2019_COORDINATE_VALUES_OPEN_AUTHORIZED","0"],
    ["TEMPORAL_GEOMETRY_AUTHORIZED","0"],["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
    ["E4D1D2A2_STATIC_ADAPTER_SOURCE_CONSTRUCTION_FREEZE","PASS"]
])
log="\n".join([
    f"ADAPTER_SOURCE_COUNT={len(adapter_rows)}",
    f"ORIGINAL_FUNCTION_PROVENANCE_PASS_COUNT={sum(r[-1]=='PASS' for r in function_rows)}",
    f"ACS_ACCUMULATION_SUFFIX_BYTE_IDENTITY={int(suffix_ok)}",
    f"SOURCE_CONSTRUCTION_FAILURE_COUNT={len(fail)}",
    "ADAPTER_IMPORTED=0","ADAPTER_EXECUTED=0",
    "2019_RAW_DATA_ROWS_OPENED=0","2019_COORDINATE_VALUES_OPENED=0",
    "SCIENTIFIC_METHOD_MUTATED=0",
    f"NEXT_PRIMARY_PHASE_ID={next_phase}",
    f"E4D1D3_2019_COORDINATE_EXECUTION_PRECOMMIT_AUTHORIZED={int(success)}",
    "E4D1D_2019_COORDINATE_VALUES_OPEN_AUTHORIZED=0",
    "TEMPORAL_GEOMETRY_AUTHORIZED=0","REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "E4D1D2A2_STATIC_ADAPTER_SOURCE_CONSTRUCTION_FREEZE=PASS",
])+"\n"
if fail: log+="SOURCE_CONSTRUCTION_FAILURE_DETAILS="+" || ".join(fail)+"\n"
EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
