#!/usr/bin/env python3
from pathlib import Path
import ast, csv, hashlib, json, re

ROOT=Path(__file__).resolve().parents[1]
ENGINE=ROOT/"scripts/E4A2F_first_scf_kd_inference_execution.py"
CONTRACT=ROOT/"data/metadata/E4C5F_exact_E4A2F_variance_engine_contract.json"

EXEC=ROOT/"data/metadata/E4C5F_execution.txt"
AUDIT=ROOT/"data/metadata/E4C5F_exact_E4A2F_variance_engine_audit.txt"
FORMULAS=ROOT/"data/metadata/E4C5F_E4A2F_variance_formula_manifest.tsv"
FUNCS=ROOT/"data/metadata/E4C5F_E4A2F_engine_function_manifest.tsv"
LITERALS=ROOT/"data/metadata/E4C5F_E4A2F_engine_literal_manifest.tsv"
DECISION=ROOT/"data/results/E4C5F_exact_engine_freeze_decision.tsv"

ENGINE_SHA="1bba062e5db501ed1dd61435e7bcaafc0310338ac40fcc767b7cd8143ada4292"

KEYWORDS=(
    "implicat","imput","sampling","replicat","variance","var_","_var",
    "combined","combine","standard_error","stderr","se_","_se",
    "rubin","within","between"
)

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):
            h.update(b)
    return h.hexdigest()

def srcseg(text,node):
    s=ast.get_source_segment(text,node)
    return "" if s is None else " ".join(s.strip().split())

def relevant(text):
    s=text.lower()
    return any(k in s for k in KEYWORDS)

c=json.loads(CONTRACT.read_text(encoding="utf-8"))
assert c["phase"]=="E4C5F"
assert c["engine"]["sha256"]==ENGINE_SHA
assert c["engine"]["formula_rederivation_allowed"] is False
assert c["freeze_scope"]["target_numeric_result_rows_opened"] is False
assert c["freeze_scope"]["transformed_replicate_values_computed"] is False
assert c["freeze_scope"]["transformed_uncertainty_computed"] is False
assert sha(ENGINE)==ENGINE_SHA

text=ENGINE.read_text(encoding="utf-8")
tree=ast.parse(text)

parent={}
for n in ast.walk(tree):
    for ch in ast.iter_child_nodes(n):
        parent[ch]=n

def enclosing_function(node):
    cur=node
    while cur in parent:
        cur=parent[cur]
        if isinstance(cur,(ast.FunctionDef,ast.AsyncFunctionDef)):
            return cur.name
    return "<module>"

functions=[]
for n in ast.walk(tree):
    if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
        functions.append([
            n.name,n.lineno,getattr(n,"end_lineno",n.lineno),
            ",".join(a.arg for a in n.args.args),
            int(relevant(srcseg(text,n)))
        ])

formula_rows=[]
literal_rows=[]

for n in ast.walk(tree):
    if isinstance(n,ast.Assign):
        targets=",".join(srcseg(text,t) for t in n.targets)
        expr=srcseg(text,n.value)
        whole=targets+" = "+expr
        if relevant(whole):
            formula_rows.append([
                "ASSIGN",enclosing_function(n),n.lineno,getattr(n,"end_lineno",n.lineno),
                targets,expr,srcseg(text,n)
            ])
    elif isinstance(n,ast.AnnAssign):
        target=srcseg(text,n.target)
        expr=srcseg(text,n.value) if n.value is not None else ""
        whole=target+" = "+expr
        if relevant(whole):
            formula_rows.append([
                "ANNASSIGN",enclosing_function(n),n.lineno,getattr(n,"end_lineno",n.lineno),
                target,expr,srcseg(text,n)
            ])
    elif isinstance(n,ast.AugAssign):
        target=srcseg(text,n.target)
        expr=srcseg(text,n.value)
        whole=target+" "+type(n.op).__name__+"= "+expr
        if relevant(whole):
            formula_rows.append([
                "AUGASSIGN",enclosing_function(n),n.lineno,getattr(n,"end_lineno",n.lineno),
                target,expr,srcseg(text,n)
            ])
    elif isinstance(n,ast.Return):
        expr=srcseg(text,n.value) if n.value is not None else ""
        if relevant(expr) or relevant(enclosing_function(n)):
            formula_rows.append([
                "RETURN",enclosing_function(n),n.lineno,getattr(n,"end_lineno",n.lineno),
                "<return>",expr,srcseg(text,n)
            ])

# Numeric literals nested inside formula-bearing AST nodes.
for row in formula_rows:
    kind,func,lo,hi,target,expr,source=row
    try:
        node=ast.parse(source).body[0]
    except Exception:
        continue
    vals=[]
    for sub in ast.walk(node):
        if isinstance(sub,ast.Constant) and isinstance(sub.value,(int,float)) and not isinstance(sub.value,bool):
            vals.append(repr(sub.value))
    if vals:
        literal_rows.append([func,lo,hi,target,";".join(vals),source])

# Hard structural evidence that the source is actually the raw engine used for
# all three layers. We do not assert coefficients yet; the manifest freezes them.
joined="\n".join(r[6].lower() for r in formula_rows)
has_imp=("imput" in joined or "implicat" in joined)
has_sampling=("sampling" in joined or "replicat" in joined)
has_variance=("variance" in joined or "var" in joined)
has_combined=("combined" in joined or "combine" in joined)
if not (has_imp and has_sampling and has_variance and has_combined):
    raise RuntimeError(
        f"engine formula inventory incomplete: imp={has_imp} sampling={has_sampling} "
        f"variance={has_variance} combined={has_combined}"
    )

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

# Summarize common formula signatures without choosing or changing any formula.
source_upper=text.upper()
literal_999_count=len(re.findall(r"(?<!\d)999(?!\d)",text))
literal_5_count=len(re.findall(r"(?<!\d)5(?:\.0)?(?!\d)",text))
six_fifths_forms=[
    token for token in ["6/5","6.0/5.0","6 / 5","6.0 / 5.0","1.2"]
    if token in text
]

with DECISION.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["diagnostic","value"])
    w.writerows([
        ["ENGINE_PATH","scripts/E4A2F_first_scf_kd_inference_execution.py"],
        ["ENGINE_SHA256",ENGINE_SHA],
        ["FUNCTION_COUNT",len(functions)],
        ["INFERENCE_FORMULA_NODE_COUNT",len(formula_rows)],
        ["FORMULA_LITERAL_ROW_COUNT",len(literal_rows)],
        ["HAS_IMPUTATION_OR_IMPLICATE_FORMULA_TERMS",int(has_imp)],
        ["HAS_SAMPLING_OR_REPLICATE_FORMULA_TERMS",int(has_sampling)],
        ["HAS_VARIANCE_FORMULA_TERMS",int(has_variance)],
        ["HAS_COMBINED_FORMULA_TERMS",int(has_combined)],
        ["LITERAL_999_OCCURRENCE_COUNT",literal_999_count],
        ["LITERAL_5_OR_5P0_OCCURRENCE_COUNT",literal_5_count],
        ["SIX_FIFTHS_LITERAL_FORMS",";".join(six_fifths_forms) if six_fifths_forms else "NONE_EXPLICIT"],
        ["SOURCE_CODE_IS_ENGINE_AUTHORITY",1],
        ["FORMULA_REDERIVATION_PERFORMED",0],
        ["TARGET_NUMERIC_RESULT_ROWS_OPENED",0],
        ["TRANSFORMED_REPLICATE_VALUES_COMPUTED",0],
        ["TRANSFORMED_UNCERTAINTY_COMPUTED",0],
        ["E4C5G_EXECUTION_PRECOMMIT_AUTHORIZED",1],
        ["E4C5G_TRANSFORMED_INFERENCE_EXECUTION_AUTHORIZED",0],
    ])

log="\n".join([
    f"E4A2F_ENGINE_PATH=scripts/E4A2F_first_scf_kd_inference_execution.py",
    f"E4A2F_ENGINE_SHA256={ENGINE_SHA}",
    f"ENGINE_FUNCTION_COUNT={len(functions)}",
    f"INFERENCE_FORMULA_NODE_COUNT={len(formula_rows)}",
    f"FORMULA_LITERAL_ROW_COUNT={len(literal_rows)}",
    f"HAS_IMPUTATION_OR_IMPLICATE_FORMULA_TERMS={int(has_imp)}",
    f"HAS_SAMPLING_OR_REPLICATE_FORMULA_TERMS={int(has_sampling)}",
    f"HAS_VARIANCE_FORMULA_TERMS={int(has_variance)}",
    f"HAS_COMBINED_FORMULA_TERMS={int(has_combined)}",
    f"LITERAL_999_OCCURRENCE_COUNT={literal_999_count}",
    f"LITERAL_5_OR_5P0_OCCURRENCE_COUNT={literal_5_count}",
    f"SIX_FIFTHS_LITERAL_FORMS={';'.join(six_fifths_forms) if six_fifths_forms else 'NONE_EXPLICIT'}",
    "SOURCE_CODE_IS_ENGINE_AUTHORITY=1",
    "FORMULA_REDERIVATION_PERFORMED=0",
    "TARGET_NUMERIC_RESULT_ROWS_OPENED=0",
    "TRANSFORMED_REPLICATE_VALUES_COMPUTED=0",
    "TRANSFORMED_UNCERTAINTY_COMPUTED=0",
    "OWNER_RENTER_CONTRAST_COMPUTED=0",
    "K_D_COVARIANCE_COMPUTED=0",
    "CROSS_COORDINATE_METRIC_SCALE_FROZEN=0",
    "GEOMETRY_READY=0",
    "GEOMETRY_AUTHORIZED=0",
    "DIMENSIONALITY_TEST_AUTHORIZED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "E4C5F_EXACT_E4A2F_VARIANCE_ENGINE_FREEZE=PASS",
    "E4C5G_EXECUTION_PRECOMMIT_AUTHORIZED=1",
    "E4C5G_TRANSFORMED_INFERENCE_EXECUTION_AUTHORIZED=0",
])+"\n"

EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")

print("===== EXACT VARIANCE-ENGINE FORMULA MANIFEST =====")
for r in sorted(formula_rows,key=lambda x:(x[2],x[0],x[4])):
    print("\t".join(map(str,r)))
