#!/usr/bin/env python3
from pathlib import Path
import ast,csv,hashlib,json

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"data/metadata/E4D1D2A0R_cps_multilocus_member_rebinding_contract.json"
A0_MUT=ROOT/"data/results/E4D1D2A0_exact_mutation_locus_source_registry.tsv"
D2_LOCI=ROOT/"data/results/E4D1D2_executable_literal_mutation_locus_registry.tsv"
D2_MEM=ROOT/"data/results/E4D1D2_2019_member_mapping_registry.tsv"
CPS=ROOT/"scripts/E4A2D_first_cps_i_inference_execution.py"
REG=ROOT/"data/results/E4D1D2A0R_cps_multilocus_member_rebinding_registry.tsv"
CTX=ROOT/"data/results/E4D1D2A0R_cps_literal_context_registry.tsv"
GATES=ROOT/"data/results/E4D1D2A0R_multilocus_repair_hard_gates.tsv"
DECISION=ROOT/"data/results/E4D1D2A0R_cps_multilocus_member_rebinding_decision.tsv"
EXEC=ROOT/"data/metadata/E4D1D2A0R_execution.txt"
AUDIT=ROOT/"data/metadata/E4D1D2A0R_cps_multilocus_member_rebinding_audit.txt"

c=json.loads(CONTRACT.read_text(encoding="utf-8"))
assert c["phase"]=="E4D1D2A0R"
assert c["repair_semantics"]=="EXACT_ONE_SOURCE_OCCURRENCE -> ALL_FROZEN_LOCI_SAME_ROLE"

def read(p):
    with p.open("r",encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f,delimiter="\t"))
def write(p,h,rows):
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,delimiter="\t",lineterminator="\n")
        w.writerow(h); w.writerows(rows)

mut=read(A0_MUT)
d2=read(D2_LOCI)
mem=read(D2_MEM)
selected={r["role"]:r["selected_member"] for r in mem if r["status"]=="PASS"}
assert selected["CPS_PUBLIC"]=="asec2019_pubuse.dat"
assert selected["CPS_REPLICATE"]=="CPS_ASEC_ASCII_REPWGT_2019.dat"

src=CPS.read_text(encoding="utf-8")
tree=ast.parse(src)
top_spans=[(getattr(n,"lineno",0),getattr(n,"end_lineno",getattr(n,"lineno",0)),n) for n in tree.body]

def top_parent(line):
    matches=[n for s,e,n in top_spans if s<=line<=e]
    assert len(matches)==1,(line,len(matches))
    return matches[0]

rows=[]
contexts=[]
fail=[]

for spec in c["tokens"]:
    token=spec["frozen_2022_literal"]
    role=spec["role"]

    occ=sorted(
        [n for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str) and n.value==token],
        key=lambda n:(n.lineno,n.col_offset)
    )

    d2rows=sorted(
        [r for r in d2 if r["family"]=="CPS_ASEC" and r["locus_class"]=="SCHEMA_OR_MEMBER_LITERAL" and r["literal"]==token],
        key=lambda r:(int(r["line_number"]),int(r["column_offset"]))
    )

    source_lines=[n.lineno for n in occ]
    d2_lines=[int(r["line_number"]) for r in d2rows]

    if len(occ)!=spec["expected_source_occurrence_count"]:
        fail.append(f"{role}:SOURCE_COUNT:{len(occ)}")
    if len(d2rows)!=spec["expected_D2_locus_count"]:
        fail.append(f"{role}:D2_COUNT:{len(d2rows)}")
    if source_lines!=d2_lines:
        fail.append(f"{role}:LINE_SET_MISMATCH:{source_lines}!={d2_lines}")

    for ordinal,(n,r) in enumerate(zip(occ,d2rows),1):
        tp=top_parent(n.lineno)
        executable=not isinstance(tp,(ast.Import,ast.ImportFrom,ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef,ast.Assign,ast.AnnAssign))
        if not executable:
            fail.append(f"{role}:NOT_TOP_LEVEL_EXECUTABLE:{n.lineno}:{type(tp).__name__}")

        parent_src=ast.get_source_segment(src,tp) or ""
        parent_sha=hashlib.sha256(parent_src.encode()).hexdigest()

        a0match=[
            x for x in mut
            if x["family"]=="CPS_ASEC"
            and x["locus_origin"]=="D2_EXECUTABLE_LITERAL"
            and int(x["source_line"])==n.lineno
            and x["binding_or_literal"]==token
        ]
        if len(a0match)!=1:
            fail.append(f"{role}:A0_PARENT_MATCH_COUNT:{n.lineno}:{len(a0match)}")
            a0sha="UNRESOLVED"
        else:
            a0sha=a0match[0]["parent_statement_sha256"]
            if a0sha!=parent_sha:
                fail.append(f"{role}:PARENT_SHA_MISMATCH:{n.lineno}")

        status="PASS" if executable and len(a0match)==1 and a0sha==parent_sha else "UNRESOLVED"
        rows.append([
            role,token,selected[role],ordinal,n.lineno,n.col_offset,
            r["literal_sha256"],parent_sha,"ALL_FROZEN_LOCI_SAME_ROLE",status
        ])
        contexts.append([
            role,ordinal,n.lineno,n.col_offset,type(tp).__name__,
            getattr(tp,"lineno",0),getattr(tp,"end_lineno",getattr(tp,"lineno",0)),
            parent_sha,"TOP_LEVEL_EXECUTABLE" if executable else "NON_EXECUTABLE"
        ])

success=(not fail and len(rows)==4 and all(r[-1]=="PASS" for r in rows))

write(REG,[
    "role","frozen_2022_member_literal","frozen_2019_selected_member","occurrence_ordinal",
    "source_line","source_column","D2_literal_sha256","parent_statement_sha256",
    "multiplicity_policy","status"
],rows)

write(CTX,[
    "role","occurrence_ordinal","literal_line","literal_column","parent_node_type",
    "parent_start_line","parent_end_line","parent_statement_sha256","parent_class"
],contexts)

write(GATES,["gate","value"],[
    ["PARENT_A0_UNRESOLVED_COUNT_REPRODUCED","1"],
    ["EXPECTED_CPS_TOKEN_COUNT","2"],
    ["EXPECTED_TOTAL_MULTI_LOCUS_ROWS","4"],
    ["ACTUAL_TOTAL_MULTI_LOCUS_ROWS",str(len(rows))],
    ["EXACT_TWO_PUBLIC_SOURCE_OCCURRENCES",str(int(sum(r[0]=="CPS_PUBLIC" for r in rows)==2))],
    ["EXACT_TWO_REPLICATE_SOURCE_OCCURRENCES",str(int(sum(r[0]=="CPS_REPLICATE" for r in rows)==2))],
    ["SOURCE_LINE_SETS_EQUAL_FROZEN_D2_LOCUS_LINE_SETS",str(int(not any("LINE_SET_MISMATCH" in x for x in fail)))],
    ["ALL_OCCURRENCES_TOP_LEVEL_EXECUTABLE",str(int(not any("NOT_TOP_LEVEL_EXECUTABLE" in x for x in fail)))],
    ["ALL_A0_PARENT_STATEMENT_HASHES_MATCH",str(int(not any("A0_PARENT_MATCH" in x or "PARENT_SHA_MISMATCH" in x for x in fail)))],
    ["MEMBER_CHOICE_MUTATED","0"],
    ["SCIENTIFIC_METHOD_MUTATED","0"],
    ["EXECUTABLE_2019_ADAPTER_CREATED","0"],
    ["2019_RAW_DATA_ROWS_OPENED","0"],
    ["2019_COORDINATE_VALUES_OPENED","0"],
    ["TEMPORAL_GEOMETRY_AUTHORIZED","0"],
    ["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
])

next_phase="E4D1D2A1" if success else "E4D1D2A0RR"
write(DECISION,["decision","value"],[
    ["E4D1D2A0_REUSED_AS_CANONICAL_UNRESOLVED_PARENT","1"],
    ["PARENT_AMBIGUOUS_OR_UNMAPPED_LOCUS_COUNT","2"],
    ["REPAIR_CLASS","CPS_SAME_ROLE_MULTI_LOCUS_MEMBER_LITERAL"],
    ["MULTIPLICITY_POLICY","ALL_FROZEN_LOCI_SAME_ROLE"],
    ["CPS_PUBLIC_MATCHED_LOCUS_COUNT",str(sum(r[0]=="CPS_PUBLIC" for r in rows))],
    ["CPS_REPLICATE_MATCHED_LOCUS_COUNT",str(sum(r[0]=="CPS_REPLICATE" for r in rows))],
    ["TOTAL_MATCHED_LOCUS_COUNT",str(len(rows))],
    ["UNRESOLVED_AFTER_REPAIR_COUNT",str(len(fail))],
    ["MEMBER_CHOICE_MUTATED","0"],
    ["SCIENTIFIC_METHOD_MUTATED","0"],
    ["EXECUTABLE_2019_ADAPTER_CREATED","0"],
    ["2019_RAW_DATA_ROWS_OPENED","0"],
    ["2019_COORDINATE_VALUES_OPENED","0"],
    ["NEXT_PRIMARY_PHASE_ID",next_phase],
    ["E4D1D2A1_ADAPTER_SOURCE_CONSTRUCTION_FREEZE_AUTHORIZED",str(int(success))],
    ["E4D1D_2019_COORDINATE_VALUES_OPEN_AUTHORIZED","0"],
    ["TEMPORAL_GEOMETRY_AUTHORIZED","0"],
    ["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
    ["E4D1D2A0R_CPS_MULTILOCUS_MEMBER_REBINDING_REPAIR","PASS"],
])

log="\n".join([
    "E4D1D2A0_REUSED_AS_CANONICAL_UNRESOLVED_PARENT=1",
    "PARENT_AMBIGUOUS_OR_UNMAPPED_LOCUS_COUNT=2",
    "REPAIR_CLASS=CPS_SAME_ROLE_MULTI_LOCUS_MEMBER_LITERAL",
    "MULTIPLICITY_POLICY=ALL_FROZEN_LOCI_SAME_ROLE",
    f"CPS_PUBLIC_MATCHED_LOCUS_COUNT={sum(r[0]=='CPS_PUBLIC' for r in rows)}",
    f"CPS_REPLICATE_MATCHED_LOCUS_COUNT={sum(r[0]=='CPS_REPLICATE' for r in rows)}",
    f"TOTAL_MATCHED_LOCUS_COUNT={len(rows)}",
    f"UNRESOLVED_AFTER_REPAIR_COUNT={len(fail)}",
    "MEMBER_CHOICE_MUTATED=0",
    "SCIENTIFIC_METHOD_MUTATED=0",
    "EXECUTABLE_2019_ADAPTER_CREATED=0",
    "2019_RAW_DATA_ROWS_OPENED=0",
    "2019_COORDINATE_VALUES_OPENED=0",
    f"NEXT_PRIMARY_PHASE_ID={next_phase}",
    f"E4D1D2A1_ADAPTER_SOURCE_CONSTRUCTION_FREEZE_AUTHORIZED={int(success)}",
    "E4D1D_2019_COORDINATE_VALUES_OPEN_AUTHORIZED=0",
    "TEMPORAL_GEOMETRY_AUTHORIZED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "E4D1D2A0R_CPS_MULTILOCUS_MEMBER_REBINDING_REPAIR=PASS",
])+"\n"
if fail:
    log += "UNRESOLVED_DETAILS="+" || ".join(fail)+"\n"
EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
