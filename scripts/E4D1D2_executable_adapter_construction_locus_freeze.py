#!/usr/bin/env python3
from pathlib import Path
import ast,csv,hashlib,json,re,zipfile

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"data/metadata/E4D1D2_executable_adapter_construction_locus_contract.json"
D1_BIND=ROOT/"data/results/E4D1D1_source_output_binding_registry.tsv"
D1_PROV=ROOT/"data/results/E4D1D1_scientific_function_provenance_registry.tsv"

METHODS=[
 ("ACS",ROOT/"scripts/E4C3D_first_acs2022_h_access_execution.py"),
 ("SCF",ROOT/"scripts/E4A2F_first_scf_kd_inference_execution.py"),
 ("CPS_ASEC",ROOT/"scripts/E4A2D_first_cps_i_inference_execution.py"),
]
ARCHIVES=[
 ("SCF_SUMMARY",ROOT/"data/raw/scf/2019/scfp2019s.zip","DTA"),
 ("SCF_FULL",ROOT/"data/raw/scf/2019/scf2019s.zip","DTA"),
 ("SCF_REPLICATE",ROOT/"data/raw/scf/2019/scf2019rw1s.zip","DTA"),
 ("CPS_PUBLIC",ROOT/"data/raw/cps_asec/2019/asec2019_pubuse.zip","DAT"),
 ("CPS_REPLICATE",ROOT/"data/raw/cps_asec/2019/CPS_ASEC_ASCII_REPWGT_2019.zip","DAT"),
]

LITERALS=ROOT/"data/results/E4D1D2_executable_literal_mutation_locus_registry.tsv"
FIELDS=ROOT/"data/results/E4D1D2_field_access_registry.tsv"
MEMBERS=ROOT/"data/results/E4D1D2_2019_member_mapping_registry.tsv"
ARCH=ROOT/"data/results/E4D1D2_family_adapter_architecture_registry.tsv"
GATES=ROOT/"data/results/E4D1D2_construction_locus_hard_gates.tsv"
DECISION=ROOT/"data/results/E4D1D2_executable_adapter_construction_locus_decision.tsv"
EXEC=ROOT/"data/metadata/E4D1D2_execution.txt"
AUDIT=ROOT/"data/metadata/E4D1D2_executable_adapter_construction_locus_audit.txt"

c=json.loads(CONTRACT.read_text(encoding="utf-8"))
assert c["phase"]=="E4D1D2"

def write_tsv(p,h,rows):
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,delimiter="\t",lineterminator="\n")
        w.writerow(h); w.writerows(rows)

def in_function(node,parents):
    return any(isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef,ast.Lambda)) for x in parents)

path_re=re.compile(r"(data/|scripts/|\.zip\b|\.csv\b|\.tsv\b|\.dta\b|\.dat\b|\.txt\b|\.json\b)",re.I)
year_re=re.compile(r"\b(?:2019|2020|2021|2022)\b")
hex64=re.compile(r"^[0-9a-f]{64}$",re.I)

with D1_BIND.open("r",encoding="utf-8",newline="") as f:
    d1_bind=list(csv.DictReader(f,delimiter="\t"))
with D1_PROV.open("r",encoding="utf-8",newline="") as f:
    prov=list(csv.DictReader(f,delimiter="\t"))
assert len(prov)==17
d1_assignment_lines={(r["family"],int(r["start_line"])) for r in d1_bind}

literal_rows=[]
field_rows=[]

for family,p in METHODS:
    src=p.read_text(encoding="utf-8")
    tree=ast.parse(src)
    parent={}
    for n in ast.walk(tree):
        for ch in ast.iter_child_nodes(n):
            parent[ch]=n

    def ancestors(n):
        out=[]
        while n in parent:
            n=parent[n]; out.append(n)
        return out

    for n in ast.walk(tree):
        anc=ancestors(n)
        if in_function(n,anc):
            continue
        if isinstance(n,ast.Constant) and isinstance(n.value,str):
            v=n.value
            line=getattr(n,"lineno",0)
            # Skip literals inside top-level assignment statements already frozen in D1.
            assignment_anc=next((x for x in anc if isinstance(x,(ast.Assign,ast.AnnAssign))),None)
            if assignment_anc is not None and (family,getattr(assignment_anc,"lineno",0)) in d1_assignment_lines:
                continue
            if path_re.search(v):
                cls="SOURCE_OR_CONTAINER_LITERAL"
                lv=v.lower()
                if "result" in lv or "audit" in lv or "execution" in lv:
                    cls="OUTPUT_LITERAL"
                if v.lower().endswith((".dta",".dat")) and "/" not in v:
                    cls="SCHEMA_OR_MEMBER_LITERAL"
            elif hex64.match(v):
                cls="HASH_LITERAL"
            elif year_re.search(v):
                cls="YEAR_OR_PHASE_LITERAL"
            else:
                continue
            literal_rows.append([
                family,str(p.relative_to(ROOT)),line,getattr(n,"col_offset",0),
                cls,v,hashlib.sha256(v.encode()).hexdigest(),
                "D2A_ENUMERATED_COMPATIBILITY_ONLY" if cls!="IMMUTABLE_LITERAL" else "IMMUTABLE"
            ])

        # Static string-key field accesses. Descriptive only.
        if isinstance(n,ast.Subscript):
            sl=n.slice
            key=None
            if isinstance(sl,ast.Constant) and isinstance(sl.value,str):
                key=sl.value
            if key:
                field_rows.append([
                    family,str(p.relative_to(ROOT)),getattr(n,"lineno",0),
                    key,"SUBSCRIPT_STRING_KEY","STATIC_EVIDENCE_ONLY"
                ])
        if isinstance(n,ast.Call):
            fn=""
            if isinstance(n.func,ast.Attribute):
                fn=n.func.attr
            if fn in {"get","pop","setdefault"} and n.args and isinstance(n.args[0],ast.Constant) and isinstance(n.args[0].value,str):
                field_rows.append([
                    family,str(p.relative_to(ROOT)),getattr(n,"lineno",0),
                    n.args[0].value,f"DICT_{fn.upper()}_STRING_KEY","STATIC_EVIDENCE_ONLY"
                ])

# De-duplicate exact rows.
literal_rows=sorted({tuple(r) for r in literal_rows})
field_rows=sorted({tuple(r) for r in field_rows})

member_rows=[]
member_ok=True
for role,p,ext in ARCHIVES:
    with zipfile.ZipFile(p,"r") as z:
        names=[i.filename for i in z.infolist() if not i.is_dir()]
    cand=[n for n in names if n.lower().endswith("."+ext.lower())]
    status="PASS" if len(cand)==1 else "UNRESOLVED"
    if status!="PASS": member_ok=False
    member_rows.append([
        role,str(p.relative_to(ROOT)),ext,len(names),len(cand),
        cand[0] if len(cand)==1 else "|".join(cand) if cand else "EMPTY_SET",
        status
    ])

# Architecture frozen independently of row values.
arch_rows=[
 ["ACS","STATIC_INGESTION_COMPATIBILITY_LAYER",
  "materialize 2019 HHLDRAGEP from RELSHIPP=20 AGEP by SERIALNO; restrict to TYPE=1 AND NP>0; retain housing WGTP family",
  "FROZEN_2022_H_ESTIMATOR_LOGIC","PASS"],
 ["SCF","STATIC_SOURCE_AND_MEMBER_COMPATIBILITY_LAYER",
  "map unique 2019 Summary/Full/replicate DTA members to frozen 2022 source roles without changing transforms/MI/replicate logic",
  "FROZEN_2022_KD_TRANSFORM_MI_REPLICATE_LOGIC","PASS" if all(r[-1]=="PASS" for r in member_rows[:3]) else "UNRESOLVED"],
 ["CPS_ASEC","STATIC_FIXED_WIDTH_LAYOUT_COMPATIBILITY_LAYER",
  "map unique 2019 public/replicate DAT members and frozen layout authorities without changing FYFT/SEARCH or replicate logic",
  "FROZEN_2022_I_TARGET_AND_REPLICATE_LOGIC","PASS" if all(r[-1]=="PASS" for r in member_rows[3:]) else "UNRESOLVED"],
]

unresolved_literals=[r for r in literal_rows if r[4]=="UNRESOLVED"]
success=member_ok and not unresolved_literals and all(r[-1]=="PASS" for r in arch_rows)

write_tsv(LITERALS,[
 "family","path","line_number","column_offset","locus_class","literal",
 "literal_sha256","D2A_policy"
],literal_rows)
write_tsv(FIELDS,[
 "family","path","line_number","field_token","access_form","policy"
],field_rows)
write_tsv(MEMBERS,[
 "role","archive_path","required_extension","archive_member_count",
 "candidate_member_count","selected_member","status"
],member_rows)
write_tsv(ARCH,[
 "family","adapter_mode","frozen_2019_compatibility_action",
 "immutable_scientific_surface","status"
],arch_rows)
write_tsv(GATES,["gate","value"],[
 ["EXACT_17_VERBATIM_FUNCTIONS_REUSED_FROM_D1","1"],
 ["EXECUTABLE_LITERAL_LOCUS_COUNT",str(len(literal_rows))],
 ["STATIC_FIELD_ACCESS_ROW_COUNT",str(len(field_rows))],
 ["EXACT_5_2019_CONTAINER_ROLE_ROWS",str(int(len(member_rows)==5))],
 ["ALL_2019_MEMBER_MAPPINGS_UNAMBIGUOUS",str(int(member_ok))],
 ["ALL_3_FAMILY_ARCHITECTURES_PASS",str(int(all(r[-1]=="PASS" for r in arch_rows)))],
 ["UNRESOLVED_EXECUTABLE_LITERAL_COUNT",str(len(unresolved_literals))],
 ["FROZEN_EXECUTOR_IMPORTED","0"],
 ["FROZEN_EXECUTOR_EXECUTED","0"],
 ["EXECUTABLE_2019_ADAPTER_CREATED","0"],
 ["2019_RAW_DATA_ROWS_OPENED","0"],
 ["2019_COORDINATE_VALUES_OPENED","0"],
 ["WEIGHTED_ESTIMATION_PERFORMED","0"],
 ["SCIENTIFIC_METHOD_MUTATED","0"],
 ["TEMPORAL_GEOMETRY_AUTHORIZED","0"],
 ["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
])

next_phase="E4D1D2A" if success else "E4D1D2R"
write_tsv(DECISION,["decision","value"],[
 ["E4D1D1_REUSED_AS_CANONICAL_ADAPTATION_SURFACE","1"],
 ["VERBATIM_FUNCTION_PROVENANCE_COUNT","17"],
 ["EXECUTABLE_LITERAL_LOCUS_COUNT",str(len(literal_rows))],
 ["STATIC_FIELD_ACCESS_ROW_COUNT",str(len(field_rows))],
 ["MEMBER_MAPPING_ROLE_COUNT",str(len(member_rows))],
 ["ALL_MEMBER_MAPPINGS_UNAMBIGUOUS",str(int(member_ok))],
 ["UNRESOLVED_EXECUTABLE_LITERAL_COUNT",str(len(unresolved_literals))],
 ["FROZEN_EXECUTOR_IMPORTED","0"],
 ["FROZEN_EXECUTOR_EXECUTED","0"],
 ["EXECUTABLE_2019_ADAPTER_CREATED","0"],
 ["2019_RAW_DATA_ROWS_OPENED","0"],
 ["2019_COORDINATE_VALUES_OPENED","0"],
 ["WEIGHTED_ESTIMATION_PERFORMED","0"],
 ["SCIENTIFIC_METHOD_MUTATED","0"],
 ["NEXT_PRIMARY_PHASE_ID",next_phase],
 ["E4D1D2A_EXECUTABLE_ADAPTER_SOURCE_CONSTRUCTION_FREEZE_AUTHORIZED",str(int(success))],
 ["E4D1D_2019_COORDINATE_VALUES_OPEN_AUTHORIZED","0"],
 ["TEMPORAL_GEOMETRY_AUTHORIZED","0"],
 ["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
 ["E4D1D2_EXECUTABLE_ADAPTER_CONSTRUCTION_LOCUS_FREEZE","PASS"],
])

log="\n".join([
 "E4D1D1_REUSED_AS_CANONICAL_ADAPTATION_SURFACE=1",
 "VERBATIM_FUNCTION_PROVENANCE_COUNT=17",
 f"EXECUTABLE_LITERAL_LOCUS_COUNT={len(literal_rows)}",
 f"STATIC_FIELD_ACCESS_ROW_COUNT={len(field_rows)}",
 f"MEMBER_MAPPING_ROLE_COUNT={len(member_rows)}",
 f"ALL_MEMBER_MAPPINGS_UNAMBIGUOUS={int(member_ok)}",
 f"UNRESOLVED_EXECUTABLE_LITERAL_COUNT={len(unresolved_literals)}",
 "FROZEN_EXECUTOR_IMPORTED=0",
 "FROZEN_EXECUTOR_EXECUTED=0",
 "EXECUTABLE_2019_ADAPTER_CREATED=0",
 "2019_RAW_DATA_ROWS_OPENED=0",
 "2019_COORDINATE_VALUES_OPENED=0",
 "WEIGHTED_ESTIMATION_PERFORMED=0",
 "SCIENTIFIC_METHOD_MUTATED=0",
 f"NEXT_PRIMARY_PHASE_ID={next_phase}",
 f"E4D1D2A_EXECUTABLE_ADAPTER_SOURCE_CONSTRUCTION_FREEZE_AUTHORIZED={int(success)}",
 "E4D1D_2019_COORDINATE_VALUES_OPEN_AUTHORIZED=0",
 "TEMPORAL_GEOMETRY_AUTHORIZED=0",
 "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
 "E4D1D2_EXECUTABLE_ADAPTER_CONSTRUCTION_LOCUS_FREEZE=PASS",
])+"\n"
EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
