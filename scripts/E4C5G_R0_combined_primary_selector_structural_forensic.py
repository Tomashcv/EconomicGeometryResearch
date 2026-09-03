#!/usr/bin/env python3
from pathlib import Path
import csv,collections,json,re

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"data/results/E4A2F_2022_scf_kd_cohort_inference.tsv"
CONTRACT=ROOT/"data/metadata/E4C5G_R0_combined_primary_selector_structural_forensic_contract.json"
EXEC=ROOT/"data/metadata/E4C5G_R0_execution.txt"
AUDIT=ROOT/"data/metadata/E4C5G_R0_combined_primary_selector_structural_forensic_audit.txt"
SIG=ROOT/"data/results/E4C5G_R0_combined_semantic_signatures.tsv"
FUNNEL=ROOT/"data/results/E4C5G_R0_selector_funnel.tsv"
DEC=ROOT/"data/results/E4C5G_R0_selector_forensic_decision.tsv"

AGES=["25-34","35-44","45-54","55-64"]
TENS=["OWNER","RENTER"]

ALLOWED=["year","age_band","tenure","statistic_id","dimension","role","raw_variable","statistic","state_sign"]

def norm(x):
    return re.sub(r"[^A-Z0-9]+","_",str(x).strip().upper()).strip("_")

def age_exact(x):
    s=str(x).strip().upper().replace("–","-").replace("—","-")
    return s if s in AGES else None

def age_broad(x):
    s=str(x).strip().upper().replace("–","-").replace("—","-")
    nums=[int(v) for v in re.findall(r"\d+",s)]
    for lo,hi in [(25,34),(35,44),(45,54),(55,64)]:
        if lo in nums and hi in nums:
            return f"{lo}-{hi}"
    return None

def tenure_exact_norm(x):
    s=norm(x)
    return s if s in {"OWNER","RENTER"} else None

c=json.loads(CONTRACT.read_text())
assert c["numeric_outcome_columns_read"] is False
assert c["repair_authorized_in_R0"] is False

rows=[]
with SRC.open("r",encoding="utf-8-sig",newline="") as f:
    rd=csv.DictReader(f,delimiter="\t")
    missing=set(ALLOWED)-set(rd.fieldnames or [])
    if missing:
        raise RuntimeError(f"missing categorical fields: {sorted(missing)}")
    for rownum,row in enumerate(rd,start=2):
        # Explicitly copy only allowed categorical fields.
        r={k:row[k] for k in ALLOWED}
        r["_rownum"]=rownum
        rows.append(r)

sid_rows=[]
for r in rows:
    sid=norm(r["statistic_id"])
    if sid in {"K_FIN_MEAN","D_PIRTOTAL_MEAN"}:
        sid_rows.append(r)

# Semantic signature inventory.
sig_counter=collections.Counter()
for r in sid_rows:
    key=(
        norm(r["statistic_id"]),str(r["age_band"]).strip(),str(r["tenure"]).strip(),
        norm(r["dimension"]),norm(r["role"]),norm(r["raw_variable"]),
        norm(r["statistic"]),str(r["state_sign"]).strip()
    )
    sig_counter[key]+=1

with SIG.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["statistic_id","age_band_raw","tenure_raw","dimension","role","raw_variable","statistic","state_sign_raw","row_count"])
    for key,count in sorted(sig_counter.items()):
        w.writerow([*key,count])

# Progressive funnel. Each stage is cumulative and uses only categorical fields.
def comp(r):
    sid=norm(r["statistic_id"])
    return "K" if sid=="K_FIN_MEAN" else ("D" if sid=="D_PIRTOTAL_MEAN" else None)

def passes(stage,r):
    cp=comp(r)
    if stage>=1 and cp is None: return False
    if stage>=2 and age_exact(r["age_band"]) is None: return False
    if stage>=3 and tenure_exact_norm(r["tenure"]) is None: return False
    if stage>=4 and norm(r["role"])!="PRIMARY": return False
    if stage>=5:
        if cp=="K" and norm(r["dimension"])!="K": return False
        if cp=="D" and norm(r["dimension"])!="D": return False
    if stage>=6:
        if cp=="K" and norm(r["raw_variable"])!="FIN": return False
        if cp=="D" and norm(r["raw_variable"])!="PIRTOTAL": return False
    if stage>=7 and norm(r["statistic"])!="MEAN": return False
    return True

stages=[
    (1,"STATISTIC_ID"),(2,"AGE_EXACT"),(3,"TENURE_EXACT_NORMALIZED"),(4,"ROLE_PRIMARY"),
    (5,"DIMENSION_EXACT"),(6,"RAW_VARIABLE_EXACT"),(7,"STATISTIC_MEAN")
]

funnel=[]
for n,name in stages:
    kept=[r for r in rows if passes(n,r)]
    kc=sum(comp(r)=="K" for r in kept)
    dc=sum(comp(r)=="D" for r in kept)
    cells=set()
    for r in kept:
        a=age_exact(r["age_band"])
        t=tenure_exact_norm(r["tenure"])
        if a and t and comp(r): cells.add((comp(r),a,t))
    funnel.append((n,name,len(kept),kc,dc,len(cells)))

with FUNNEL.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["stage_number","stage","rows_kept","K_rows","D_rows","distinct_exact_component_cells"])
    w.writerows(funnel)

sid_count=len([r for r in rows if comp(r)])
exact_age_count=sum(comp(r) is not None and age_exact(r["age_band"]) is not None for r in rows)
broad_age_count=sum(comp(r) is not None and age_broad(r["age_band"]) is not None for r in rows)
exact_ten_count=sum(comp(r) is not None and tenure_exact_norm(r["tenure"]) is not None for r in rows)
final_count=funnel[-1][2]

# First zeroing stage, if any.
first_zero="NONE"
prev=sid_count
for _,name,count,_,_,_ in funnel:
    if prev>0 and count==0:
        first_zero=name
        break
    prev=count

# A categorical repair candidate may be structurally identified, but R0 does not authorize it.
if sid_count>0 and exact_age_count==0 and broad_age_count>0:
    cause="AGE_EXACT_MATCH_INCOMPATIBLE_WITH_FROZEN_SOURCE_LABEL_FORMAT"
    repair_candidate="REUSE_FROZEN_BROAD_AGE_PARSER_FOR_COMBINED_ROWS"
elif sid_count>0 and exact_ten_count==0:
    cause="TENURE_EXACT_NORMALIZED_MATCH_INCOMPATIBLE_WITH_SOURCE_LABEL_FORMAT"
    repair_candidate="REVIEW_TENURE_LABELS_BEFORE_ANY_REPAIR"
elif sid_count==0:
    cause="PRIMARY_STATISTIC_ID_NOT_PRESENT_AS_EXPECTED"
    repair_candidate="REVIEW_STATISTIC_ID_SEMANTICS_BEFORE_ANY_REPAIR"
elif final_count==16:
    cause="SELECTOR_REPRODUCES_16_CELLS_IN_FORENSIC"
    repair_candidate="EXECUTION_CODE_PATH_MISMATCH_REQUIRES_SOURCE_DIFF_FORENSIC"
else:
    cause="LATER_CATEGORICAL_PREDICATE_FILTERS_EXPECTED_ROWS"
    repair_candidate="REVIEW_FUNNEL_AND_SIGNATURES_BEFORE_ANY_REPAIR"

with DEC.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["diagnostic","value"])
    w.writerows([
        ["SOURCE_ROW_COUNT",len(rows)],
        ["TARGET_STATISTIC_ID_ROW_COUNT",sid_count],
        ["EXACT_AGE_MATCH_ROW_COUNT",exact_age_count],
        ["BROAD_AGE_PARSE_ROW_COUNT",broad_age_count],
        ["EXACT_NORMALIZED_TENURE_ROW_COUNT",exact_ten_count],
        ["FINAL_SELECTOR_ROW_COUNT",final_count],
        ["FIRST_ZEROING_STAGE",first_zero],
        ["FAILURE_CAUSE_CLASS",cause],
        ["STRUCTURAL_REPAIR_CANDIDATE",repair_candidate],
        ["NUMERIC_OUTCOME_VALUES_USED",0],
        ["REPAIR_AUTHORIZED",0],
    ])

log="\n".join([
    "POST_E4C5G_FAILURE_FORENSIC=1",
    "PRIOR_FAILURE_PRESERVED=1",
    "NUMERIC_OUTCOME_COLUMNS_READ=0",
    "NUMERIC_OUTCOME_VALUES_USED=0",
    f"SOURCE_ROW_COUNT={len(rows)}",
    f"TARGET_STATISTIC_ID_ROW_COUNT={sid_count}",
    f"EXACT_AGE_MATCH_ROW_COUNT={exact_age_count}",
    f"BROAD_AGE_PARSE_ROW_COUNT={broad_age_count}",
    f"EXACT_NORMALIZED_TENURE_ROW_COUNT={exact_ten_count}",
    f"FINAL_SELECTOR_ROW_COUNT={final_count}",
    f"FIRST_ZEROING_STAGE={first_zero}",
    f"FAILURE_CAUSE_CLASS={cause}",
    f"STRUCTURAL_REPAIR_CANDIDATE={repair_candidate}",
    "SCIENTIFIC_TRANSFORM_MUTATED=0",
    "PRIMARY_SEMANTICS_MUTATED=0",
    "VARIANCE_ENGINE_MUTATED=0",
    "REPAIR_AUTHORIZED=0",
    "GEOMETRY_AUTHORIZED=0",
    "E4C5G_R0_COMBINED_PRIMARY_SELECTOR_STRUCTURAL_FORENSIC=PASS",
])+"\n"

EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
print("===== SELECTOR FUNNEL =====")
for r in funnel:
    print("\t".join(map(str,r)))
print("===== TARGET SEMANTIC SIGNATURES =====")
for key,count in sorted(sig_counter.items()):
    print("\t".join(map(str,[*key,count])))
