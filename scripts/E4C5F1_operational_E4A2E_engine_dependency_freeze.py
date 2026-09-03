#!/usr/bin/env python3
from pathlib import Path
import ast,csv,hashlib,json,re,subprocess

ROOT=Path(__file__).resolve().parents[1]
E4A2F=ROOT/"scripts/E4A2F_first_scf_kd_inference_execution.py"
CONTRACT=ROOT/"data/metadata/E4C5F1_operational_E4A2E_engine_dependency_contract.json"

EXEC=ROOT/"data/metadata/E4C5F1_execution.txt"
AUDIT=ROOT/"data/metadata/E4C5F1_operational_E4A2E_engine_audit.txt"
DEPENDENCY=ROOT/"data/metadata/E4C5F1_E4A2E_dependency_manifest.tsv"
FUNCS=ROOT/"data/metadata/E4C5F1_E4A2E_engine_function_manifest.tsv"
FORMULAS=ROOT/"data/metadata/E4C5F1_E4A2E_variance_formula_manifest.tsv"
LITERALS=ROOT/"data/metadata/E4C5F1_E4A2E_engine_literal_manifest.tsv"
DECISION=ROOT/"data/results/E4C5F1_operational_engine_decision.tsv"

E4A2F_SHA="1bba062e5db501ed1dd61435e7bcaafc0310338ac40fcc767b7cd8143ada4292"

KEYWORDS=(
    "imput","implicat","sampling","replicat","variance","combined",
    "standard_error","stderr","combined_se","replicate_mean",
    "between","within","rubin"
)

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):
            h.update(b)
    return h.hexdigest()

def relevant(s):
    u=s.lower()
    return any(k in u for k in KEYWORDS)

def source(text,node):
    s=ast.get_source_segment(text,node)
    return "" if s is None else " ".join(s.strip().split())

def eval_path_expr(node):
    # Resolve ROOT / "a" / "b" AST expressions only.
    if isinstance(node,ast.Name) and node.id=="ROOT":
        return Path(".")
    if isinstance(node,ast.Constant) and isinstance(node.value,str):
        return Path(node.value)
    if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Div):
        left=eval_path_expr(node.left)
        right=eval_path_expr(node.right)
        if left is None or right is None:
            return None
        return left/right
    return None

def derive_dependency(text,name):
    tree=ast.parse(text)
    hits=[]
    for n in ast.walk(tree):
        if not isinstance(n,ast.Assign):
            continue
        targets=[t.id for t in n.targets if isinstance(t,ast.Name)]
        if name not in targets:
            continue
        p=eval_path_expr(n.value)
        if p is None:
            raise RuntimeError(f"{name}: unsupported path expression: {source(text,n.value)}")
        hits.append(p)
    if len(hits)!=1:
        raise RuntimeError(f"{name}: expected exactly one assignment, got {hits}")
    return hits[0]

def enclosing_function(parent,node):
    cur=node
    while cur in parent:
        cur=parent[cur]
        if isinstance(cur,(ast.FunctionDef,ast.AsyncFunctionDef)):
            return cur.name
    return "<module>"

c=json.loads(CONTRACT.read_text(encoding="utf-8"))
assert c["phase"]=="E4C5F1"
assert c["formula_freeze_policy"]["formula_rederivation_allowed"] is False
assert c["authorization_boundary"]["transformed_replicate_values_computed"] is False
assert c["authorization_boundary"]["transformed_uncertainty_computed"] is False
assert c["authorization_boundary"]["E4C5G_transformed_inference_execution_authorized"] is False
assert sha(E4A2F)==E4A2F_SHA

e4a2f_text=E4A2F.read_text(encoding="utf-8")
engine_rel=derive_dependency(e4a2f_text,"E4A2E_ENGINE")
contract_rel=derive_dependency(e4a2f_text,"E4A2E_CONTRACT")

engine=ROOT/engine_rel
engine_contract=ROOT/contract_rel

for p in [engine,engine_contract]:
    if not p.is_file():
        raise RuntimeError(f"delegated dependency missing: {p}")
    subprocess.run(
        ["git","ls-files","--error-unmatch",str(p.relative_to(ROOT))],
        cwd=ROOT,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL
    )

engine_sha=sha(engine)
contract_sha=sha(engine_contract)

with DEPENDENCY.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["dependency_role","path","sha256","derived_from"])
    w.writerow(["E4A2E_ENGINE",str(engine.relative_to(ROOT)),engine_sha,"E4A2F_AST_ASSIGNMENT"])
    w.writerow(["E4A2E_CONTRACT",str(engine_contract.relative_to(ROOT)),contract_sha,"E4A2F_AST_ASSIGNMENT"])

text=engine.read_text(encoding="utf-8")
tree=ast.parse(text)

parent={}
for n in ast.walk(tree):
    for ch in ast.iter_child_nodes(n):
        parent[ch]=n

functions=[]
for n in ast.walk(tree):
    if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
        functions.append([
            n.name,n.lineno,getattr(n,"end_lineno",n.lineno),
            ",".join(a.arg for a in n.args.args),
            int(relevant(source(text,n)))
        ])

formula_rows=[]
statement_types=(ast.Assign,ast.AnnAssign,ast.AugAssign,ast.Return,ast.Expr)
for n in ast.walk(tree):
    if not isinstance(n,statement_types):
        continue
    exact=source(text,n)
    if not exact or not relevant(exact):
        continue

    target=""
    expression=""
    if isinstance(n,ast.Assign):
        target=",".join(source(text,t) for t in n.targets)
        expression=source(text,n.value)
    elif isinstance(n,ast.AnnAssign):
        target=source(text,n.target)
        expression=source(text,n.value) if n.value else ""
    elif isinstance(n,ast.AugAssign):
        target=source(text,n.target)
        expression=source(text,n.value)
    elif isinstance(n,ast.Return):
        target="<return>"
        expression=source(text,n.value) if n.value else ""
    else:
        target="<expr>"
        expression=source(text,n.value)

    formula_rows.append([
        type(n).__name__.upper(),
        enclosing_function(parent,n),
        n.lineno,getattr(n,"end_lineno",n.lineno),
        target,expression,exact
    ])

literal_rows=[]
for r in formula_rows:
    kind,func,lo,hi,target,expression,exact=r
    try:
        parsed=ast.parse(exact)
    except SyntaxError:
        continue
    vals=[]
    for n in ast.walk(parsed):
        if isinstance(n,ast.Constant) and isinstance(n.value,(int,float)) and not isinstance(n.value,bool):
            vals.append(repr(n.value))
    if vals:
        literal_rows.append([func,lo,hi,target,";".join(vals),exact])

with FUNCS.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["function","start_line","end_line","args","contains_inference_keywords"])
    w.writerows(sorted(functions,key=lambda x:(x[1],x[0])))

with FORMULAS.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["node_type","function","start_line","end_line","target","expression","exact_source"])
    w.writerows(sorted(formula_rows,key=lambda x:(x[2],x[0],x[4])))

with LITERALS.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["function","start_line","end_line","target","numeric_literals","exact_source"])
    w.writerows(sorted(literal_rows,key=lambda x:(x[1],x[3])))

joined="\n".join((r[4]+" "+r[5]+" "+r[6]).lower() for r in formula_rows)

families={
    "IMPUTATION_OR_IMPLICATE":("imput","implicat"),
    "SAMPLING_OR_REPLICATE":("sampling","replicat"),
    "COMBINED_VARIANCE":("combined_variance","combined variance","combined"),
    "STANDARD_ERROR":("combined_se","standard_error","stderr","sqrt"),
}

presence={}
for fam,terms in families.items():
    presence[fam]=int(any(t in joined for t in terms))

if not all(presence.values()):
    raise RuntimeError(f"operational E4A2E formula coverage incomplete: {presence}")

# We specifically want the operational engine to contain formula-bearing numeric
# literals, but we do not assert what those coefficients should be.
if not literal_rows:
    raise RuntimeError("no numeric literals captured from operational inference formula nodes")

with DECISION.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["diagnostic","value"])
    w.writerows([
        ["E4A2E_ENGINE_PATH",str(engine.relative_to(ROOT))],
        ["E4A2E_ENGINE_SHA256",engine_sha],
        ["E4A2E_CONTRACT_PATH",str(engine_contract.relative_to(ROOT))],
        ["E4A2E_CONTRACT_SHA256",contract_sha],
        ["ENGINE_FUNCTION_COUNT",len(functions)],
        ["OPERATIONAL_FORMULA_NODE_COUNT",len(formula_rows)],
        ["OPERATIONAL_FORMULA_LITERAL_ROW_COUNT",len(literal_rows)],
        ["HAS_IMPUTATION_OR_IMPLICATE_FORMULA_TERMS",presence["IMPUTATION_OR_IMPLICATE"]],
        ["HAS_SAMPLING_OR_REPLICATE_FORMULA_TERMS",presence["SAMPLING_OR_REPLICATE"]],
        ["HAS_COMBINED_VARIANCE_FORMULA_TERMS",presence["COMBINED_VARIANCE"]],
        ["HAS_STANDARD_ERROR_FORMULA_TERMS",presence["STANDARD_ERROR"]],
        ["FORMULA_REDERIVATION_PERFORMED",0],
        ["TARGET_NUMERIC_RESULT_ROWS_OPENED",0],
        ["TRANSFORMED_REPLICATE_VALUES_COMPUTED",0],
        ["TRANSFORMED_UNCERTAINTY_COMPUTED",0],
        ["E4C5G_EXECUTION_PRECOMMIT_AUTHORIZED",1],
        ["E4C5G_TRANSFORMED_INFERENCE_EXECUTION_AUTHORIZED",0],
    ])

log="\n".join([
    "E4C5F_ORCHESTRATOR_FREEZE_PRESERVED=1",
    "E4A2F_DELEGATED_OPERATIONAL_ENGINE_DISCOVERED=1",
    f"E4A2E_ENGINE_PATH={engine.relative_to(ROOT)}",
    f"E4A2E_ENGINE_SHA256={engine_sha}",
    f"E4A2E_CONTRACT_PATH={engine_contract.relative_to(ROOT)}",
    f"E4A2E_CONTRACT_SHA256={contract_sha}",
    f"ENGINE_FUNCTION_COUNT={len(functions)}",
    f"OPERATIONAL_FORMULA_NODE_COUNT={len(formula_rows)}",
    f"OPERATIONAL_FORMULA_LITERAL_ROW_COUNT={len(literal_rows)}",
    f"HAS_IMPUTATION_OR_IMPLICATE_FORMULA_TERMS={presence['IMPUTATION_OR_IMPLICATE']}",
    f"HAS_SAMPLING_OR_REPLICATE_FORMULA_TERMS={presence['SAMPLING_OR_REPLICATE']}",
    f"HAS_COMBINED_VARIANCE_FORMULA_TERMS={presence['COMBINED_VARIANCE']}",
    f"HAS_STANDARD_ERROR_FORMULA_TERMS={presence['STANDARD_ERROR']}",
    "SOURCE_CODE_IS_OPERATIONAL_ENGINE_AUTHORITY=1",
    "FORMULA_REDERIVATION_PERFORMED=0",
    "TARGET_NUMERIC_RESULT_ROWS_OPENED=0",
    "TRANSFORMED_REPLICATE_VALUES_COMPUTED=0",
    "TRANSFORMED_UNCERTAINTY_COMPUTED=0",
    "POINT_TRANSFORM_MUTATION_AUTHORIZED=0",
    "OWNER_RENTER_TRANSFORMED_CONTRAST_AUTHORIZED=0",
    "K_D_COVARIANCE_COMPUTED=0",
    "CROSS_COORDINATE_METRIC_SCALE_FROZEN=0",
    "GEOMETRY_READY=0",
    "GEOMETRY_AUTHORIZED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "E4C5F1_OPERATIONAL_E4A2E_VARIANCE_ENGINE_FREEZE=PASS",
    "E4C5G_EXECUTION_PRECOMMIT_AUTHORIZED=1",
    "E4C5G_TRANSFORMED_INFERENCE_EXECUTION_AUTHORIZED=0",
])+"\n"

EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")

print(log,end="")
print("===== OPERATIONAL E4A2E FORMULA MANIFEST =====")
for r in sorted(formula_rows,key=lambda x:(x[2],x[0],x[4])):
    print("\t".join(map(str,r)))
