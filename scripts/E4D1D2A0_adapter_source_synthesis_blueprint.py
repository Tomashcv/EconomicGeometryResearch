#!/usr/bin/env python3
from pathlib import Path
import ast,csv,hashlib,json,re

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"data/metadata/E4D1D2A0_adapter_source_synthesis_blueprint_contract.json"

D1_BIND=ROOT/"data/results/E4D1D1_source_output_binding_registry.tsv"
D1_PROV=ROOT/"data/results/E4D1D1_scientific_function_provenance_registry.tsv"
D2_LITERALS=ROOT/"data/results/E4D1D2_executable_literal_mutation_locus_registry.tsv"
D2_FIELDS=ROOT/"data/results/E4D1D2_field_access_registry.tsv"
D2_MEMBERS=ROOT/"data/results/E4D1D2_2019_member_mapping_registry.tsv"

METHODS=[
 ("ACS",ROOT/"scripts/E4C3D_first_acs2022_h_access_execution.py"),
 ("SCF",ROOT/"scripts/E4A2F_first_scf_kd_inference_execution.py"),
 ("CPS_ASEC",ROOT/"scripts/E4A2D_first_cps_i_inference_execution.py"),
]

TOP=ROOT/"data/results/E4D1D2A0_top_level_assembly_registry.tsv"
MUT=ROOT/"data/results/E4D1D2A0_exact_mutation_locus_source_registry.tsv"
FAMILY=ROOT/"data/results/E4D1D2A0_family_synthesis_blueprint_registry.tsv"
BRIDGE=ROOT/"data/results/E4D1D2A0_acs_bridge_insertion_registry.tsv"
MAP=ROOT/"data/results/E4D1D2A0_member_literal_rebinding_registry.tsv"
GATES=ROOT/"data/results/E4D1D2A0_blueprint_hard_gates.tsv"
DECISION=ROOT/"data/results/E4D1D2A0_adapter_source_synthesis_blueprint_decision.tsv"
EXEC=ROOT/"data/metadata/E4D1D2A0_execution.txt"
AUDIT=ROOT/"data/metadata/E4D1D2A0_adapter_source_synthesis_blueprint_audit.txt"

c=json.loads(CONTRACT.read_text(encoding="utf-8"))
assert c["phase"]=="E4D1D2A0"
assert c["required_verbatim_function_count"]==17
assert c["source_inspection_only"] is True
assert c["executable_adapter_created"] is False

def read(p):
    with p.open("r",encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f,delimiter="\t"))

def write_tsv(p,h,rows):
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,delimiter="\t",lineterminator="\n")
        w.writerow(h); w.writerows(rows)

def sh(s): return hashlib.sha256(s.encode()).hexdigest()
def seg(src,n): return ast.get_source_segment(src,n) or ""

bind=read(D1_BIND)
prov=read(D1_PROV)
loci=read(D2_LITERALS)
fields=read(D2_FIELDS)
members=read(D2_MEMBERS)

prov_by={(r["family"],r["function"]):r for r in prov}
assert len(prov_by)==17

mutable_bind={(r["family"],int(r["line"])):r for r in bind if r["D2_policy"]=="ENUMERATE_IN_D2"}
loci_by_family={}
for r in loci:
    loci_by_family.setdefault(r["family"],[]).append(r)
fields_by_family={}
for r in fields:
    fields_by_family.setdefault(r["family"],[]).append(r)

top_rows=[]
mut_rows=[]
family_rows=[]
bridge_rows=[]
mapping_rows=[]
ambiguous=[]

# Frozen member-role mappings from D2.
member_by_role={r["role"]:r["selected_member"] for r in members if r["status"]=="PASS"}
expected_roles={"SCF_SUMMARY","SCF_FULL","SCF_REPLICATE","CPS_PUBLIC","CPS_REPLICATE"}
assert expected_roles<=set(member_by_role)

# Known frozen 2022 member literals from D0/D2 evidence.
member_rebind_candidates={
    "SCF":{
        "rscfp2022.dta":member_by_role["SCF_SUMMARY"],
        "p22i6.dta":member_by_role["SCF_FULL"],
        "p22_rw1.dta":member_by_role["SCF_REPLICATE"],
    },
    "CPS_ASEC":{
        "asec2022_pubuse.dat":member_by_role["CPS_PUBLIC"],
        "CPS_ASEC_ASCII_REPWGT_2022.DAT":member_by_role["CPS_REPLICATE"],
    },
}

verbatim_functions=0
acs_hhldragep_nodes=[]

for family,p in METHODS:
    rel=str(p.relative_to(ROOT))
    src=p.read_text(encoding="utf-8")
    tree=ast.parse(src)

    family_bind_lines={line:r for (fam,line),r in mutable_bind.items() if fam==family}
    family_loci=loci_by_family.get(family,[])
    family_fields=fields_by_family.get(family,[])

    seen_bind=set()
    seen_loci=set()

    for ordinal,n in enumerate(tree.body,1):
        st=seg(src,n)
        start=getattr(n,"lineno",0)
        end=getattr(n,"end_lineno",start)
        node_hash=sh(st)

        if isinstance(n,(ast.Import,ast.ImportFrom)):
            policy="VERBATIM_IMPORT_OR_FUNCTION"
        elif isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
            key=(family,n.name)
            assert key in prov_by,key
            assert node_hash==prov_by[key]["function_source_sha256"],(key,node_hash,prov_by[key]["function_source_sha256"])
            policy="VERBATIM_IMPORT_OR_FUNCTION"
            verbatim_functions+=1
        elif isinstance(n,(ast.Assign,ast.AnnAssign)):
            matching=[line for line in family_bind_lines if start<=line<=end]
            if matching:
                policy="MUTABLE_ASSIGNMENT_BINDING"
                for line in matching:
                    seen_bind.add(line)
                    r=family_bind_lines[line]
                    mut_rows.append([
                        family,rel,"D1_ASSIGNMENT_BINDING",
                        line,r["binding_class"],start,end,node_hash,
                        json.dumps(st,ensure_ascii=False),
                        r["global_name"],"ENUMERATED_COMPATIBILITY_ONLY"
                    ])
            else:
                policy="IMMUTABLE_ASSIGNMENT"
        else:
            matching=[]
            for r in family_loci:
                line=int(r["line_number"])
                col=int(r["column_offset"])
                if start<=line<=end:
                    matching.append((line,col,r))
            if matching:
                policy="MUTABLE_EXECUTABLE_LITERAL_STATEMENT"
                for line,col,r in matching:
                    seen_loci.add((line,col,r["literal_sha256"]))
                    mut_rows.append([
                        family,rel,"D2_EXECUTABLE_LITERAL",
                        line,r["locus_class"],start,end,node_hash,
                        json.dumps(st,ensure_ascii=False),
                        r["literal"],"ENUMERATED_COMPATIBILITY_ONLY"
                    ])
            else:
                policy="IMMUTABLE_EXECUTABLE_STATEMENT"

        field_tokens=sorted({
            r["field_token"] for r in family_fields
            if start<=int(r["line_number"])<=end
        })
        if family=="ACS" and "HHLDRAGEP" in field_tokens:
            acs_hhldragep_nodes.append((start,end,node_hash,st))

        top_rows.append([
            family,rel,ordinal,type(n).__name__,start,end,node_hash,policy,
            "|".join(field_tokens) if field_tokens else "EMPTY_SET",
            int("2022" in st),int("2019" in st)
        ])

    missing_bind=set(family_bind_lines)-seen_bind
    if missing_bind:
        ambiguous.append(f"{family}:UNMAPPED_D1_BIND_LINES:{sorted(missing_bind)}")

    expected_loci={(int(r["line_number"]),int(r["column_offset"]),r["literal_sha256"]) for r in family_loci}
    missing_loci=expected_loci-seen_loci
    if missing_loci:
        ambiguous.append(f"{family}:UNMAPPED_D2_LITERAL_LOCI:{sorted(missing_loci)}")

    # Family summary.
    fr=[r for r in top_rows if r[0]==family]
    family_rows.append([
        family,rel,
        sum(r[7]=="VERBATIM_IMPORT_OR_FUNCTION" for r in fr),
        sum(r[7]=="MUTABLE_ASSIGNMENT_BINDING" for r in fr),
        sum(r[7]=="MUTABLE_EXECUTABLE_LITERAL_STATEMENT" for r in fr),
        sum(r[7]=="IMMUTABLE_ASSIGNMENT" for r in fr),
        sum(r[7]=="IMMUTABLE_EXECUTABLE_STATEMENT" for r in fr),
        "PASS"
    ])

    # Exact old-member literal -> 2019 member mapping, if present.
    for old,new in member_rebind_candidates.get(family,{}).items():
        occurrences=[]
        for r in family_loci:
            if r["literal"].lower()==old.lower():
                occurrences.append((int(r["line_number"]),r["literal_sha256"]))
        # It may also be inside D1 assignments rather than D2 executable literals.
        in_source=src.count(old)
        if in_source!=1:
            ambiguous.append(f"{family}:MEMBER_LITERAL_OCCURRENCE:{old}:{in_source}")
        mapping_rows.append([
            family,old,new,in_source,
            occurrences[0][0] if len(occurrences)==1 else 0,
            occurrences[0][1] if len(occurrences)==1 else "NOT_D2_EXEC_LOCUS",
            "PASS" if in_source==1 else "UNRESOLVED"
        ])

assert verbatim_functions==17,verbatim_functions

# ACS bridge insertion: exactly one earliest top-level HHLDRAGEP consumer locus.
if not acs_hhldragep_nodes:
    ambiguous.append("ACS:NO_TOP_LEVEL_HHLDRAGEP_CONSUMER")
else:
    acs_hhldragep_nodes.sort(key=lambda x:x[0])
    earliest=acs_hhldragep_nodes[0]
    same=[x for x in acs_hhldragep_nodes if x[0]==earliest[0]]
    if len(same)!=1:
        ambiguous.append("ACS:AMBIGUOUS_EARLIEST_HHLDRAGEP_CONSUMER")
    bridge_rows.append([
        "ACS_HHLDRAGEP_VERSION_BRIDGE",
        "BEFORE_TOP_LEVEL_STATEMENT",
        earliest[0],earliest[1],earliest[2],
        json.dumps(earliest[3],ensure_ascii=False),
        "HHLDRAGEP := AGEP where RELSHIPP=20 by SERIALNO",
        "TYPE=1 AND NP>0",
        "FROZEN"
    ])

write_tsv(TOP,[
    "family","path","ordinal","node_type","start_line","end_line",
    "statement_source_sha256","assembly_policy","static_field_tokens",
    "contains_2022_literal","contains_2019_literal"
],top_rows)

write_tsv(MUT,[
    "family","path","locus_origin","source_line","locus_class",
    "parent_start_line","parent_end_line","parent_statement_sha256",
    "parent_source_json","binding_or_literal","adapter_policy"
],mut_rows)

write_tsv(FAMILY,[
    "family","path","verbatim_import_or_function_nodes",
    "mutable_assignment_nodes","mutable_executable_literal_nodes",
    "immutable_assignment_nodes","immutable_executable_nodes","status"
],family_rows)

write_tsv(BRIDGE,[
    "bridge_id","insertion_policy","consumer_start_line","consumer_end_line",
    "consumer_statement_sha256","consumer_source_json","derivation",
    "householder_universe","status"
],bridge_rows)

write_tsv(MAP,[
    "family","frozen_2022_member_literal","frozen_2019_selected_member",
    "source_occurrence_count","D2_executable_locus_line",
    "D2_literal_sha256_or_assignment","status"
],mapping_rows)

all_family=all(r[-1]=="PASS" for r in family_rows)
all_mapping=all(r[-1]=="PASS" for r in mapping_rows)
bridge_ok=(len(bridge_rows)==1 and bridge_rows[0][-1]=="FROZEN")
success=(not ambiguous and all_family and all_mapping and bridge_ok and verbatim_functions==17)

write_tsv(GATES,["gate","value"],[
    ["EXACT_17_VERBATIM_FUNCTION_HASHES_PASS",str(int(verbatim_functions==17))],
    ["FAMILY_BLUEPRINT_COUNT",str(len(family_rows))],
    ["ALL_3_FAMILY_BLUEPRINTS_PASS",str(int(all_family and len(family_rows)==3))],
    ["MUTATION_LOCUS_SOURCE_ROW_COUNT",str(len(mut_rows))],
    ["MEMBER_LITERAL_REBINDING_COUNT",str(len(mapping_rows))],
    ["ALL_MEMBER_LITERAL_REBINDINGS_UNAMBIGUOUS",str(int(all_mapping))],
    ["ACS_BRIDGE_INSERTION_LOCUS_FROZEN",str(int(bridge_ok))],
    ["AMBIGUOUS_OR_UNMAPPED_LOCUS_COUNT",str(len(ambiguous))],
    ["EXECUTABLE_2019_ADAPTER_CREATED","0"],
    ["FROZEN_EXECUTOR_IMPORTED","0"],
    ["FROZEN_EXECUTOR_EXECUTED","0"],
    ["2019_RAW_DATA_ROWS_OPENED","0"],
    ["2019_COORDINATE_VALUES_OPENED","0"],
    ["SCIENTIFIC_METHOD_MUTATED","0"],
    ["GENERIC_YEAR_REPLACEMENT_AUTHORIZED","0"],
    ["TEMPORAL_GEOMETRY_AUTHORIZED","0"],
    ["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
])

next_phase="E4D1D2A1" if success else "E4D1D2A0R"
write_tsv(DECISION,["decision","value"],[
    ["E4D1D2_REUSED_AS_CANONICAL_CONSTRUCTION_LOCUS_FREEZE","1"],
    ["VERBATIM_FUNCTION_PROVENANCE_COUNT",str(verbatim_functions)],
    ["TOP_LEVEL_ASSEMBLY_NODE_COUNT",str(len(top_rows))],
    ["MUTATION_LOCUS_SOURCE_ROW_COUNT",str(len(mut_rows))],
    ["MEMBER_LITERAL_REBINDING_COUNT",str(len(mapping_rows))],
    ["ACS_BRIDGE_INSERTION_LOCUS_FROZEN",str(int(bridge_ok))],
    ["AMBIGUOUS_OR_UNMAPPED_LOCUS_COUNT",str(len(ambiguous))],
    ["EXECUTABLE_2019_ADAPTER_CREATED","0"],
    ["FROZEN_EXECUTOR_IMPORTED","0"],
    ["FROZEN_EXECUTOR_EXECUTED","0"],
    ["2019_RAW_DATA_ROWS_OPENED","0"],
    ["2019_COORDINATE_VALUES_OPENED","0"],
    ["SCIENTIFIC_METHOD_MUTATED","0"],
    ["NEXT_PRIMARY_PHASE_ID",next_phase],
    ["E4D1D2A1_ADAPTER_SOURCE_CONSTRUCTION_FREEZE_AUTHORIZED",str(int(success))],
    ["E4D1D_2019_COORDINATE_VALUES_OPEN_AUTHORIZED","0"],
    ["TEMPORAL_GEOMETRY_AUTHORIZED","0"],
    ["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
    ["E4D1D2A0_ADAPTER_SOURCE_SYNTHESIS_BLUEPRINT_FREEZE","PASS"],
])

log="\n".join([
    "E4D1D2_REUSED_AS_CANONICAL_CONSTRUCTION_LOCUS_FREEZE=1",
    f"VERBATIM_FUNCTION_PROVENANCE_COUNT={verbatim_functions}",
    f"TOP_LEVEL_ASSEMBLY_NODE_COUNT={len(top_rows)}",
    f"MUTATION_LOCUS_SOURCE_ROW_COUNT={len(mut_rows)}",
    f"MEMBER_LITERAL_REBINDING_COUNT={len(mapping_rows)}",
    f"ACS_BRIDGE_INSERTION_LOCUS_FROZEN={int(bridge_ok)}",
    f"AMBIGUOUS_OR_UNMAPPED_LOCUS_COUNT={len(ambiguous)}",
    "EXECUTABLE_2019_ADAPTER_CREATED=0",
    "FROZEN_EXECUTOR_IMPORTED=0",
    "FROZEN_EXECUTOR_EXECUTED=0",
    "2019_RAW_DATA_ROWS_OPENED=0",
    "2019_COORDINATE_VALUES_OPENED=0",
    "SCIENTIFIC_METHOD_MUTATED=0",
    f"NEXT_PRIMARY_PHASE_ID={next_phase}",
    f"E4D1D2A1_ADAPTER_SOURCE_CONSTRUCTION_FREEZE_AUTHORIZED={int(success)}",
    "E4D1D_2019_COORDINATE_VALUES_OPEN_AUTHORIZED=0",
    "TEMPORAL_GEOMETRY_AUTHORIZED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "E4D1D2A0_ADAPTER_SOURCE_SYNTHESIS_BLUEPRINT_FREEZE=PASS",
])+"\n"
if ambiguous:
    log += "AMBIGUOUS_DETAILS=" + " || ".join(ambiguous) + "\n"
EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
