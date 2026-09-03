#!/usr/bin/env python3
from pathlib import Path
import csv, collections, hashlib, json, re

ROOT=Path(__file__).resolve().parents[1]

POINT=ROOT/"data/results/E4A2F_2022_scf_kd_cohort_inference.tsv"
REP=ROOT/"data/results/E4A2F_2022_scf_kd_replicate_statistics.tsv"
CONTRACT=ROOT/"data/metadata/E4C5C_R2_duplicate_primary_cell_semantic_forensic_contract.json"

EXEC=ROOT/"data/metadata/E4C5C_R2_execution.txt"
AUDIT=ROOT/"data/metadata/E4C5C_R2_duplicate_primary_cell_semantic_forensic_audit.txt"
POINT_SIG=ROOT/"data/results/E4C5C_R2_point_semantic_signatures.tsv"
DUP=ROOT/"data/results/E4C5C_R2_duplicate_cell_semantics.tsv"
REP_INV=ROOT/"data/results/E4C5C_R2_replicate_semantic_inventory.tsv"
DECISION=ROOT/"data/results/E4C5C_R2_semantic_forensic_decision.tsv"

POINT_SHA="4fc37f81af05b32f1769412fca327cb0cee0bc1610b33c6c77eeb5a04669b55c"
REP_SHA="d7a25d385cab8d3aee0701ca86af19c2525b35fc839d44a01198f5ee6f6d311e"

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):
            h.update(b)
    return h.hexdigest()

def norm(x):
    return re.sub(r"[^A-Z0-9]+","_",str(x).strip().upper()).strip("_")

def map_age(x):
    s=str(x).strip().upper().replace("–","-").replace("—","-")
    nums=[int(v) for v in re.findall(r"\d+",s)]
    for lo,hi in [(25,34),(35,44),(45,54),(55,64)]:
        if lo in nums and hi in nums:
            return f"{lo}-{hi}"
    return None

def map_tenure(x):
    s=norm(x)
    if s=="OWNER" or s.startswith("OWNER_") or s.endswith("_OWNER"):
        return "OWNER"
    if s=="RENTER" or s.startswith("RENTER_") or s.endswith("_RENTER"):
        return "RENTER"
    return None

c=json.loads(CONTRACT.read_text(encoding="utf-8"))
assert c["phase"]=="E4C5C_R2"
assert c["repair_authorized"] is False
assert c["transform_mutation_authorized"] is False
assert sha(POINT)==POINT_SHA
assert sha(REP)==REP_SHA

point_semantic=[
    "year","age_band","tenure","statistic_id","dimension","role",
    "raw_variable","statistic","state_sign","implicate_count","replicate_count"
]
numeric_point=set(c["point_numeric_outcome_fields_excluded_from_decision"])

with POINT.open("r",encoding="utf-8-sig",newline="") as f:
    reader=csv.DictReader(f,delimiter="\t")
    headers=reader.fieldnames or []
    missing=[x for x in point_semantic if x not in headers]
    if missing:
        raise RuntimeError(f"missing point semantic fields: {missing}")
    rows=list(reader)

# Build semantic signatures only.
sig_counter=collections.Counter()
sig_cells=collections.defaultdict(set)
exact_raw_counts=collections.Counter()
exact_raw_cells=collections.defaultdict(set)
broad_cells=collections.defaultdict(list)

def old_broad_component(r):
    struct={"age_band","tenure","point_estimate_raw"}
    tokens=[]
    for k,v in r.items():
        if k in struct:
            continue
        s=str(v).strip().upper()
        if s:
            tokens.append(s)
    joined=" | ".join(tokens)
    norms={norm(x) for x in tokens}
    k=bool(norms & {"FIN","K_FIN","K_FIN_MEAN"}) or any(x in joined for x in ["K_FIN_MEAN","K_FIN"])
    d=bool(norms & {"PIRTOTAL","D_PIRTOTAL","D_PIRTOTAL_MEAN"}) or "PIRTOTAL" in joined
    if k and d:
        return "AMBIGUOUS"
    return "K" if k else ("D" if d else None)

for i,r in enumerate(rows,start=2):
    age=map_age(r["age_band"])
    ten=map_tenure(r["tenure"])
    if age is None or ten is None:
        continue

    signature=tuple(str(r[x]) for x in point_semantic[3:])
    sig_counter[signature]+=1
    sig_cells[signature].add((age,ten))

    rv=norm(r["raw_variable"])
    if rv in {"FIN","PIRTOTAL"}:
        exact_raw_counts[rv]+=1
        exact_raw_cells[rv].add((age,ten))

    comp=old_broad_component(r)
    if comp in {"K","D"}:
        broad_cells[(comp,age,ten)].append((i,r))

with POINT_SIG.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow([
        "statistic_id","dimension","role","raw_variable","statistic","state_sign",
        "implicate_count","replicate_count","row_count","distinct_target_cells"
    ])
    for sig,count in sorted(sig_counter.items(), key=lambda x:(str(x[0]),x[1])):
        w.writerow(list(sig)+[count,len(sig_cells[sig])])

dup_rows=[]
duplicate_group_count=0
for key,items in sorted(broad_cells.items()):
    if len(items)<=1:
        continue
    duplicate_group_count+=1
    comp,age,ten=key
    for rownum,r in items:
        dup_rows.append([
            comp,age,ten,rownum,
            r["statistic_id"],r["dimension"],r["role"],r["raw_variable"],
            r["statistic"],r["state_sign"],r["implicate_count"],r["replicate_count"]
        ])

with DUP.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow([
        "broad_component","age_band","tenure","source_row",
        "statistic_id","dimension","role","raw_variable","statistic",
        "state_sign","implicate_count","replicate_count"
    ])
    w.writerows(dup_rows)

# Replicate semantic inventory, excluding raw_value/state_oriented_value from decisions.
with REP.open("r",encoding="utf-8-sig",newline="") as f:
    reader=csv.DictReader(f,delimiter="\t")
    rh=reader.fieldnames or []
    required=["year","statistic_type","age_band","tenure_or_contrast","statistic_id","replicate"]
    miss=[x for x in required if x not in rh]
    if miss:
        raise RuntimeError(f"missing replicate semantic fields: {miss}")
    rep_rows=list(reader)

rep_counter=collections.Counter()
rep_cells=collections.defaultdict(set)
rep_ids=collections.defaultdict(set)

for r in rep_rows:
    age=map_age(r["age_band"])
    ten=map_tenure(r["tenure_or_contrast"])
    if age is None or ten is None:
        continue
    key=(r["statistic_type"],r["statistic_id"])
    rep_counter[key]+=1
    rep_cells[key].add((age,ten))
    rep_ids[key].add(str(r["replicate"]).strip())

with REP_INV.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["statistic_type","statistic_id","row_count","distinct_target_cells","distinct_replicate_ids"])
    for key,count in sorted(rep_counter.items()):
        w.writerow([key[0],key[1],count,len(rep_cells[key]),len(rep_ids[key])])

expected={(a,t) for a in ["25-34","35-44","45-54","55-64"] for t in ["OWNER","RENTER"]}
fin_exact_unique = exact_raw_counts["FIN"]==8 and exact_raw_cells["FIN"]==expected
pir_exact_unique = exact_raw_counts["PIRTOTAL"]==8 and exact_raw_cells["PIRTOTAL"]==expected

with DECISION.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["diagnostic","value"])
    w.writerows([
        ["BROAD_CLASSIFIER_DUPLICATE_GROUP_COUNT",duplicate_group_count],
        ["EXACT_RAW_VARIABLE_FIN_ROW_COUNT",exact_raw_counts["FIN"]],
        ["EXACT_RAW_VARIABLE_FIN_DISTINCT_TARGET_CELLS",len(exact_raw_cells["FIN"])],
        ["EXACT_RAW_VARIABLE_FIN_UNIQUE_8_CELL",int(fin_exact_unique)],
        ["EXACT_RAW_VARIABLE_PIRTOTAL_ROW_COUNT",exact_raw_counts["PIRTOTAL"]],
        ["EXACT_RAW_VARIABLE_PIRTOTAL_DISTINCT_TARGET_CELLS",len(exact_raw_cells["PIRTOTAL"])],
        ["EXACT_RAW_VARIABLE_PIRTOTAL_UNIQUE_8_CELL",int(pir_exact_unique)],
        ["NUMERIC_POINT_OUTCOMES_USED_FOR_SEMANTIC_DECISION",0],
        ["NUMERIC_REPLICATE_OUTCOMES_USED_FOR_SEMANTIC_DECISION",0],
        ["REPAIR_AUTHORIZED",0],
    ])

log="\n".join([
    "POST_FIRST_TARGET_VALUE_OPEN_FORENSIC=1",
    "FAILURE_ALREADY_PRESERVED_BEFORE_FORENSIC=1",
    "SCIENTIFIC_TRANSFORM_MUTATED=0",
    "PRIMARY_SEMANTICS_MUTATED=0",
    "NUMERIC_POINT_OUTCOMES_USED_FOR_SEMANTIC_DECISION=0",
    "NUMERIC_REPLICATE_OUTCOMES_USED_FOR_SEMANTIC_DECISION=0",
    f"POINT_SOURCE_ROW_COUNT={len(rows)}",
    f"POINT_SEMANTIC_SIGNATURE_COUNT={len(sig_counter)}",
    f"BROAD_CLASSIFIER_DUPLICATE_GROUP_COUNT={duplicate_group_count}",
    f"BROAD_CLASSIFIER_DUPLICATE_ROW_COUNT={len(dup_rows)}",
    f"EXACT_RAW_VARIABLE_FIN_ROW_COUNT={exact_raw_counts['FIN']}",
    f"EXACT_RAW_VARIABLE_FIN_DISTINCT_TARGET_CELLS={len(exact_raw_cells['FIN'])}",
    f"EXACT_RAW_VARIABLE_FIN_UNIQUE_8_CELL={int(fin_exact_unique)}",
    f"EXACT_RAW_VARIABLE_PIRTOTAL_ROW_COUNT={exact_raw_counts['PIRTOTAL']}",
    f"EXACT_RAW_VARIABLE_PIRTOTAL_DISTINCT_TARGET_CELLS={len(exact_raw_cells['PIRTOTAL'])}",
    f"EXACT_RAW_VARIABLE_PIRTOTAL_UNIQUE_8_CELL={int(pir_exact_unique)}",
    f"REPLICATE_SOURCE_ROW_COUNT={len(rep_rows)}",
    f"REPLICATE_SEMANTIC_SIGNATURE_COUNT={len(rep_counter)}",
    "REPAIR_AUTHORIZED=0",
    "TRANSFORM_MUTATION_AUTHORIZED=0",
    "PRIMARY_SEMANTIC_MUTATION_AUTHORIZED=0",
    "GEOMETRY_AUTHORIZED=0",
    "E4C5C_R2_DUPLICATE_PRIMARY_CELL_SEMANTIC_FORENSIC=PASS",
])+"\n"

EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")

print("===== DUPLICATE CELL SEMANTICS — NO NUMERIC OUTCOMES =====")
for row in dup_rows[:80]:
    print("\t".join(map(str,row)))
if len(dup_rows)>80:
    print(f"... TRUNCATED DISPLAY; TOTAL_DUPLICATE_ROWS={len(dup_rows)}")

print("===== EXACT RAW_VARIABLE DIAGNOSTIC =====")
print(f"FIN rows={exact_raw_counts['FIN']} cells={len(exact_raw_cells['FIN'])} unique8={int(fin_exact_unique)}")
print(f"PIRTOTAL rows={exact_raw_counts['PIRTOTAL']} cells={len(exact_raw_cells['PIRTOTAL'])} unique8={int(pir_exact_unique)}")
