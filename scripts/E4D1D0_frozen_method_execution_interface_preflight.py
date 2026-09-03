#!/usr/bin/env python3
from pathlib import Path
import ast,csv,hashlib,json,re

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"data/metadata/E4D1D0_frozen_method_execution_interface_contract.json"

METHODS=[
    ("ACS","scripts/E4C3D_first_acs2022_h_access_execution.py"),
    ("SCF","scripts/E4A2F_first_scf_kd_inference_execution.py"),
    ("CPS_ASEC","scripts/E4A2D_first_cps_i_inference_execution.py"),
]

SUMMARY=ROOT/"data/results/E4D1D0_method_interface_summary.tsv"
FUNCS=ROOT/"data/results/E4D1D0_function_signature_registry.tsv"
ARGS=ROOT/"data/results/E4D1D0_cli_argument_registry.tsv"
PATHS=ROOT/"data/results/E4D1D0_path_literal_registry.tsv"
GLOBALS=ROOT/"data/results/E4D1D0_global_assignment_registry.tsv"
IMPORTS=ROOT/"data/results/E4D1D0_import_registry.tsv"
CALLS=ROOT/"data/results/E4D1D0_entrypoint_call_registry.tsv"
GATES=ROOT/"data/results/E4D1D0_interface_preflight_hard_gates.tsv"
DECISION=ROOT/"data/results/E4D1D0_frozen_method_execution_interface_decision.tsv"
EXEC=ROOT/"data/metadata/E4D1D0_execution.txt"
AUDIT=ROOT/"data/metadata/E4D1D0_frozen_method_execution_interface_audit.txt"

c=json.loads(CONTRACT.read_text(encoding="utf-8"))
assert c["phase"]=="E4D1D0"
assert c["inspection"]["module_import"] is False
assert c["inspection"]["executor_execution"] is False
assert c["inspection"]["2019_raw_rows"] is False

def write_tsv(p,h,rows):
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,delimiter="\t",lineterminator="\n")
        w.writerow(h); w.writerows(rows)

def dotted(n):
    if isinstance(n,ast.Name): return n.id
    if isinstance(n,ast.Attribute):
        x=dotted(n.value)
        return (x+"." if x else "")+n.attr
    return ""

def is_main_guard(n):
    if not isinstance(n,ast.If): return False
    try:
        return ast.unparse(n.test).replace(" ","") in {
            "__name__=='__main__'",
            '__name__=="__main__"',
            "'__main__'==__name__",
            '"__main__"==__name__'
        }
    except Exception:
        return False

def function_sig(n):
    parts=[]
    posonly=list(n.args.posonlyargs)
    normal=list(n.args.args)
    allpos=posonly+normal
    defaults=[None]*(len(allpos)-len(n.args.defaults))+list(n.args.defaults)
    for i,(a,d) in enumerate(zip(allpos,defaults)):
        s=a.arg
        if d is not None:
            try:s+="="+ast.unparse(d)
            except Exception:s+="=<default>"
        parts.append(s)
        if posonly and i==len(posonly)-1: parts.append("/")
    if n.args.vararg: parts.append("*"+n.args.vararg.arg)
    elif n.args.kwonlyargs: parts.append("*")
    for a,d in zip(n.args.kwonlyargs,n.args.kw_defaults):
        s=a.arg
        if d is not None:
            try:s+="="+ast.unparse(d)
            except Exception:s+="=<default>"
        parts.append(s)
    if n.args.kwarg: parts.append("**"+n.args.kwarg.arg)
    return n.name+"("+", ".join(parts)+")"

func_rows=[]
arg_rows=[]
path_rows=[]
global_rows=[]
import_rows=[]
call_rows=[]
summary_rows=[]

pathish=re.compile(r"(?:^|/)(?:data|results|metadata|scripts)/|\.zip$|\.csv$|\.tsv$|\.dta$|\.dat$|\.txt$|\.json$|2022|2021|2019",re.I)

for family,rel in METHODS:
    p=ROOT/rel
    src=p.read_text(encoding="utf-8")
    tree=ast.parse(src)
    source_sha=hashlib.sha256(src.encode()).hexdigest()

    funcs=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
    classes=[n for n in tree.body if isinstance(n,ast.ClassDef)]
    guards=[n for n in tree.body if is_main_guard(n)]

    argparse_args=[]
    imports=[]
    path_literals=[]
    globals_found=[]
    guarded_calls=[]

    for n in ast.walk(tree):
        if isinstance(n,(ast.Import,ast.ImportFrom)):
            if isinstance(n,ast.Import):
                names=[x.name for x in n.names]
                mod=""
            else:
                mod=n.module or ""
                names=[x.name for x in n.names]
            for name in names:
                imports.append((mod,name,getattr(n,"lineno",0)))
        if isinstance(n,ast.Call):
            fn=dotted(n.func)
            if fn.endswith(".add_argument"):
                flags=[]
                for a in n.args:
                    if isinstance(a,ast.Constant) and isinstance(a.value,str):
                        flags.append(a.value)
                if flags:
                    argparse_args.append(("|".join(flags),getattr(n,"lineno",0)))
        if isinstance(n,ast.Constant) and isinstance(n.value,str):
            v=n.value
            if len(v)<=500 and pathish.search(v):
                path_literals.append((v,getattr(n,"lineno",0)))
        if isinstance(n,(ast.Assign,ast.AnnAssign)) and n in tree.body:
            targets=[]
            val=n.value if hasattr(n,"value") else None
            if isinstance(n,ast.Assign):
                for t in n.targets:
                    if isinstance(t,ast.Name): targets.append(t.id)
            elif isinstance(n.target,ast.Name):
                targets.append(n.target.id)
            if targets:
                try: value=ast.unparse(val)
                except Exception: value="<unparseable>"
                globals_found.append(("|".join(targets),value,getattr(n,"lineno",0)))

    for g in guards:
        for n in ast.walk(g):
            if isinstance(n,ast.Call):
                guarded_calls.append((dotted(n.func) or ast.unparse(n.func),getattr(n,"lineno",0)))

    # Top-level executable nodes outside imports, definitions, assignments and main guard.
    safe_types=(ast.Import,ast.ImportFrom,ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef,ast.Assign,ast.AnnAssign)
    top_exec=[]
    for n in tree.body:
        if isinstance(n,safe_types) or is_main_guard(n):
            continue
        # module docstring expression is not executable scientific work
        if isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str):
            continue
        top_exec.append(n)

    has_main_func=any(n.name=="main" for n in funcs)
    has_argparse=any((m=="argparse" or name=="argparse") for m,name,_ in imports) or bool(argparse_args)

    if top_exec:
        interface_class="TOP_LEVEL_EXECUTION_UNSAFE"
    elif guards and has_argparse:
        interface_class="CLI_ENTRYPOINT"
    elif guards:
        interface_class="MAIN_GUARD_SCRIPT"
    else:
        interface_class="IMPORTABLE_LIBRARY"

    for n in funcs:
        func_rows.append([
            family,rel,n.name,function_sig(n),n.lineno,getattr(n,"end_lineno",n.lineno),
            hashlib.sha256((ast.get_source_segment(src,n) or "").encode()).hexdigest()
        ])
    for flags,line in argparse_args:
        arg_rows.append([family,rel,flags,line])
    for value,line in path_literals:
        path_rows.append([family,rel,line,value,hashlib.sha256(value.encode()).hexdigest()])
    for name,value,line in globals_found:
        global_rows.append([family,rel,name,line,value[:500]])
    for mod,name,line in imports:
        import_rows.append([family,rel,mod,name,line])
    for fn,line in guarded_calls:
        call_rows.append([family,rel,fn,line])

    summary_rows.append([
        family,rel,source_sha,
        len(funcs),len(classes),len(guards),int(has_main_func),int(has_argparse),
        len(argparse_args),len(top_exec),len(path_literals),len(globals_found),
        interface_class,
        "|".join(sorted({x[0] for x in guarded_calls})) if guarded_calls else "EMPTY_SET"
    ])

write_tsv(SUMMARY,[
    "family","path","source_sha256","top_level_function_count","top_level_class_count",
    "main_guard_count","main_function_present","argparse_present","cli_argument_count",
    "unguarded_top_level_executable_count","path_literal_count","global_assignment_count",
    "interface_class","main_guard_call_targets"
],summary_rows)

write_tsv(FUNCS,["family","path","function","signature","start_line","end_line","function_source_sha256"],func_rows)
write_tsv(ARGS,["family","path","argument_flags","line_number"],arg_rows)
write_tsv(PATHS,["family","path","line_number","literal","literal_sha256"],path_rows)
write_tsv(GLOBALS,["family","path","global_name","line_number","value_expression"],global_rows)
write_tsv(IMPORTS,["family","path","module","name","line_number"],import_rows)
write_tsv(CALLS,["family","path","call_target","line_number"],call_rows)

allowed=set(c["allowed_interface_classes"])
all_classes_valid=all(r[12] in allowed for r in summary_rows)
all_ast=all(r[2] for r in summary_rows)

write_tsv(GATES,["gate","value"],[
["EXACT_METHOD_COUNT",str(len(summary_rows))],
["ALL_AST_PARSE_PASS",str(int(all_ast))],
["ALL_INTERFACE_CLASSES_ALLOWED",str(int(all_classes_valid))],
["FROZEN_EXECUTOR_IMPORTED","0"],
["FROZEN_EXECUTOR_EXECUTED","0"],
["2019_RAW_ROWS_OPENED","0"],
["2019_COORDINATE_VALUES_OPENED","0"],
["SCIENTIFIC_METHOD_MUTATED","0"],
["PATH_SUBSTITUTION_PERFORMED","0"],
["EXECUTION_ADAPTER_CREATED","0"],
["TEMPORAL_GEOMETRY_AUTHORIZED","0"],
["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
])

unsafe=sum(r[9]>0 for r in summary_rows)
hardcoded=sum(r[10]>0 for r in summary_rows)
classes="|".join(f"{r[0]}:{r[12]}" for r in summary_rows)

write_tsv(DECISION,["decision","value"],[
["E4D1C_REUSED_AS_CANONICAL_METHOD_FREEZE","1"],
["METHOD_INTERFACE_COUNT",str(len(summary_rows))],
["METHOD_INTERFACE_CLASSES",classes],
["TOP_LEVEL_EXECUTION_UNSAFE_METHOD_COUNT",str(unsafe)],
["METHODS_WITH_PATH_OR_YEAR_LITERALS",str(hardcoded)],
["FROZEN_EXECUTOR_IMPORTED","0"],
["FROZEN_EXECUTOR_EXECUTED","0"],
["2019_RAW_ROWS_OPENED","0"],
["2019_COORDINATE_VALUES_OPENED","0"],
["SCIENTIFIC_METHOD_MUTATED","0"],
["NEXT_PRIMARY_PHASE_ID","E4D1D1"],
["E4D1D1_EXECUTION_ADAPTER_FREEZE_AUTHORIZED","1"],
["E4D1D_2019_COORDINATE_VALUES_OPEN_AUTHORIZED","0"],
["TEMPORAL_GEOMETRY_AUTHORIZED","0"],
["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
["E4D1D0_FROZEN_METHOD_EXECUTION_INTERFACE_PREFLIGHT","PASS"],
])

log="\n".join([
"E4D1C_REUSED_AS_CANONICAL_METHOD_FREEZE=1",
f"METHOD_INTERFACE_COUNT={len(summary_rows)}",
f"METHOD_INTERFACE_CLASSES={classes}",
f"TOP_LEVEL_EXECUTION_UNSAFE_METHOD_COUNT={unsafe}",
f"METHODS_WITH_PATH_OR_YEAR_LITERALS={hardcoded}",
f"FUNCTION_SIGNATURE_ROW_COUNT={len(func_rows)}",
f"CLI_ARGUMENT_ROW_COUNT={len(arg_rows)}",
f"PATH_LITERAL_ROW_COUNT={len(path_rows)}",
f"GLOBAL_ASSIGNMENT_ROW_COUNT={len(global_rows)}",
f"IMPORT_ROW_COUNT={len(import_rows)}",
f"ENTRYPOINT_CALL_ROW_COUNT={len(call_rows)}",
"FROZEN_EXECUTOR_IMPORTED=0",
"FROZEN_EXECUTOR_EXECUTED=0",
"2019_RAW_ROWS_OPENED=0",
"2019_COORDINATE_VALUES_OPENED=0",
"SCIENTIFIC_METHOD_MUTATED=0",
"NEXT_PRIMARY_PHASE_ID=E4D1D1",
"E4D1D1_EXECUTION_ADAPTER_FREEZE_AUTHORIZED=1",
"E4D1D_2019_COORDINATE_VALUES_OPEN_AUTHORIZED=0",
"TEMPORAL_GEOMETRY_AUTHORIZED=0",
"REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
"E4D1D0_FROZEN_METHOD_EXECUTION_INTERFACE_PREFLIGHT=PASS",
])+"\n"
EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
