#!/usr/bin/env python3
from pathlib import Path
import csv
from collections import Counter

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"data/results/E4A2D_2022_cps_i_cohort_inference.tsv"
EXEC=ROOT/"data/metadata/E4C6E_R1R0_execution.txt"
AUDIT=ROOT/"data/metadata/E4C6E_R1R0_i_selector_categorical_forensic_audit.txt"
TOKENS=ROOT/"data/results/E4C6E_R1R0_i_categorical_token_inventory.tsv"
COUNTS=ROOT/"data/results/E4C6E_R1R0_i_selector_filter_counts.tsv"
SIGS=ROOT/"data/results/E4C6E_R1R0_i_categorical_row_signatures.tsv"
DEC=ROOT/"data/results/E4C6E_R1R0_i_selector_categorical_forensic_decision.tsv"

CAT_FIELDS=["year","age_band","tenure","estimand","role","state_sign"]
NUMERIC_FORBIDDEN=["unweighted_n","point_estimate","replicate_variance","replicate_se","replicate_count"]

def norm(s):
    return (s or "").strip()

def upper(s):
    return norm(s).upper()

AGE_MAP={
    "25-34":"25-34",
    "35-44":"35-44",
    "45-54":"45-54",
    "55-64":"55-64",
    "AGE25_34":"25-34",
    "AGE35_44":"35-44",
    "AGE45_54":"45-54",
    "AGE55_64":"55-64",
}
CANON_AGES={"25-34","35-44","45-54","55-64"}

def semantic_age(s):
    return AGE_MAP.get(upper(s))

def sign_semantic(s):
    x=upper(s).replace(" ","")
    if x in {"1","+1","1.0","+1.0"}:
        return "+1"
    if x in {"-1","-1.0"}:
        return "-1"
    return None

with SRC.open("r",encoding="utf-8",newline="") as f:
    rd=csv.reader(f,delimiter="\t")
    header=next(rd)
    idx={name:i for i,name in enumerate(header)}
    missing=[x for x in CAT_FIELDS+NUMERIC_FORBIDDEN if x not in idx]
    if missing:
        raise RuntimeError(f"missing required source columns {missing}")
    rows=[]
    for source_line,parts in enumerate(rd,start=2):
        if len(parts)!=len(header):
            raise RuntimeError(f"row width mismatch at source line {source_line}")
        # Deliberately retain only categorical cells.
        r={k:parts[idx[k]] for k in CAT_FIELDS}
        r["_source_line"]=str(source_line)
        rows.append(r)

if not rows:
    raise RuntimeError("I source has zero data rows")

token_counts={}
for field in CAT_FIELDS:
    token_counts[field]=Counter(norm(r[field]) for r in rows)

with TOKENS.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["field","token","count"])
    for field in CAT_FIELDS:
        for token,count in sorted(token_counts[field].items()):
            w.writerow([field,token,count])

with SIGS.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["source_line"]+CAT_FIELDS)
    for r in rows:
        w.writerow([r["_source_line"]]+[r[k] for k in CAT_FIELDS])

def count(pred):
    return sum(1 for r in rows if pred(r))

is_primary=lambda r: upper(r["role"])=="PRIMARY"
is_fyft=lambda r: upper(r["estimand"])=="I_FYFT_SHARE"
is_search=lambda r: upper(r["estimand"])=="I_SEARCH_BURDEN_SHARE"
age_exact=lambda r: norm(r["age_band"]) in CANON_AGES
age_sem=lambda r: semantic_age(r["age_band"]) in CANON_AGES
tenure_exact=lambda r: upper(r["tenure"]) in {"OWNER","RENTER"}
fyft_sign=lambda r: sign_semantic(r["state_sign"])=="+1"
search_sign=lambda r: sign_semantic(r["state_sign"])=="-1"

metrics={
    "I_TOTAL_DATA_ROWS":len(rows),
    "I_ROLE_PRIMARY_EXACT_COUNT":count(is_primary),
    "I_FYFT_ESTIMAND_EXACT_COUNT":count(is_fyft),
    "I_SEARCH_BURDEN_ESTIMAND_EXACT_COUNT":count(is_search),
    "I_CANONICAL_AGE_EXACT_COUNT":count(age_exact),
    "I_AGE_SEMANTIC_MAPPABLE_COUNT":count(age_sem),
    "I_OWNER_RENTER_EXACT_TENURE_COUNT":count(tenure_exact),
    "I_STATE_SIGN_PLUS1_SEMANTIC_COUNT":count(lambda r: sign_semantic(r["state_sign"])=="+1"),
    "I_STATE_SIGN_MINUS1_SEMANTIC_COUNT":count(lambda r: sign_semantic(r["state_sign"])=="-1"),
    "I_PRIMARY_FYFT_COUNT":count(lambda r:is_primary(r) and is_fyft(r)),
    "I_PRIMARY_SEARCH_COUNT":count(lambda r:is_primary(r) and is_search(r)),
    "I_PRIMARY_FYFT_EXACT_AGE_COUNT":count(lambda r:is_primary(r) and is_fyft(r) and age_exact(r)),
    "I_PRIMARY_SEARCH_EXACT_AGE_COUNT":count(lambda r:is_primary(r) and is_search(r) and age_exact(r)),
    "I_PRIMARY_FYFT_SEMANTIC_AGE_COUNT":count(lambda r:is_primary(r) and is_fyft(r) and age_sem(r)),
    "I_PRIMARY_SEARCH_SEMANTIC_AGE_COUNT":count(lambda r:is_primary(r) and is_search(r) and age_sem(r)),
    "I_PRIMARY_FYFT_EXACT_AGE_TENURE_COUNT":count(lambda r:is_primary(r) and is_fyft(r) and age_exact(r) and tenure_exact(r)),
    "I_PRIMARY_SEARCH_EXACT_AGE_TENURE_COUNT":count(lambda r:is_primary(r) and is_search(r) and age_exact(r) and tenure_exact(r)),
    "I_PRIMARY_FYFT_SEMANTIC_AGE_TENURE_COUNT":count(lambda r:is_primary(r) and is_fyft(r) and age_sem(r) and tenure_exact(r)),
    "I_PRIMARY_SEARCH_SEMANTIC_AGE_TENURE_COUNT":count(lambda r:is_primary(r) and is_search(r) and age_sem(r) and tenure_exact(r)),
    "I_FAILED_SELECTOR_FYFT_REPRODUCED_COUNT":count(lambda r:is_primary(r) and is_fyft(r) and age_exact(r) and tenure_exact(r) and fyft_sign(r)),
    "I_FAILED_SELECTOR_SEARCH_REPRODUCED_COUNT":count(lambda r:is_primary(r) and is_search(r) and age_exact(r) and tenure_exact(r) and search_sign(r)),
    "I_SEMANTIC_SELECTOR_FYFT_DIAGNOSTIC_COUNT":count(lambda r:is_primary(r) and is_fyft(r) and age_sem(r) and tenure_exact(r) and fyft_sign(r)),
    "I_SEMANTIC_SELECTOR_SEARCH_DIAGNOSTIC_COUNT":count(lambda r:is_primary(r) and is_search(r) and age_sem(r) and tenure_exact(r) and search_sign(r)),
}

with COUNTS.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["diagnostic","count"])
    for k,v in metrics.items():
        w.writerow([k,v])

# Classification is based strictly on categorical filter structure.
if metrics["I_ROLE_PRIMARY_EXACT_COUNT"]==0:
    cause="I_ROLE_TOKEN_MISMATCH"
    candidate="ALIGN_I_ROLE_SELECTOR_TO_FROZEN_SOURCE_CATEGORICAL_ROLE_SEMANTICS"
elif metrics["I_PRIMARY_FYFT_COUNT"]==0 or metrics["I_PRIMARY_SEARCH_COUNT"]==0:
    cause="I_ESTIMAND_TOKEN_MISMATCH"
    candidate="ALIGN_I_ESTIMAND_SELECTOR_TO_FROZEN_SOURCE_CATEGORICAL_ESTIMAND_SEMANTICS"
elif (metrics["I_PRIMARY_FYFT_EXACT_AGE_COUNT"]==0 and metrics["I_PRIMARY_FYFT_SEMANTIC_AGE_COUNT"]>0
      and metrics["I_PRIMARY_SEARCH_EXACT_AGE_COUNT"]==0 and metrics["I_PRIMARY_SEARCH_SEMANTIC_AGE_COUNT"]>0):
    cause="I_AGE_TOKEN_MISMATCH"
    candidate="ALIGN_I_AGE_SELECTOR_TO_FROZEN_SOURCE_CATEGORICAL_AGE_SEMANTICS"
elif metrics["I_PRIMARY_FYFT_EXACT_AGE_TENURE_COUNT"]==0 or metrics["I_PRIMARY_SEARCH_EXACT_AGE_TENURE_COUNT"]==0:
    cause="I_TENURE_TOKEN_MISMATCH"
    candidate="ALIGN_I_TENURE_SELECTOR_TO_FROZEN_SOURCE_CATEGORICAL_TENURE_SEMANTICS"
elif (metrics["I_FAILED_SELECTOR_FYFT_REPRODUCED_COUNT"]==0 or metrics["I_FAILED_SELECTOR_SEARCH_REPRODUCED_COUNT"]==0) and (
      metrics["I_PRIMARY_FYFT_SEMANTIC_AGE_TENURE_COUNT"]>0 and metrics["I_PRIMARY_SEARCH_SEMANTIC_AGE_TENURE_COUNT"]>0):
    cause="I_STATE_SIGN_TOKEN_MISMATCH_OR_SELECTOR_SIGN_REPRESENTATION"
    candidate="ALIGN_I_STATE_SIGN_SELECTOR_TO_FROZEN_SOURCE_CATEGORICAL_STATE_SIGN_SEMANTICS"
else:
    cause="I_SELECTOR_SHAPE_UNEXPECTED"
    candidate="NO_REPAIR_UNTIL_MORE_STRUCTURAL_FORENSIC"

log_lines=[
    "POST_E4C6E_R1_FAILURE_FORENSIC=1",
    "PRIOR_E4C6E_R1_FAILURE_PRESERVED=1",
]
log_lines += [f"{k}={v}" for k,v in metrics.items()]
log_lines += [
    f"FAILURE_CAUSE_CLASS={cause}",
    f"STRUCTURAL_REPAIR_CANDIDATE={candidate}",
    "CATEGORICAL_FIELDS_INSPECTED=year,age_band,tenure,estimand,role,state_sign",
    "NUMERIC_ECONOMIC_FIELDS_INTERPRETED=0",
    "NUMERIC_ECONOMIC_FIELDS_EMITTED=0",
    "ESTIMATE_SE_VARIANCE_VALUES_EMITTED=0",
    "SIGN_USED_AS_OUTCOME_GATE=0",
    "MAGNITUDE_USED_AS_FORENSIC_GATE=0",
    "STATISTICAL_SIGNIFICANCE_USED_AS_FORENSIC_GATE=0",
    "OWNER_RENTER_OUTCOME_DIRECTION_USED_AS_FORENSIC_GATE=0",
    "SCIENTIFIC_ESTIMATOR_MUTATED=0",
    "TRANSFORM_MUTATED=0",
    "COMPONENT_DEFINITION_MUTATED=0",
    "E4C6D_FROZEN_SELECTOR_MUTATED=0",
    "E4C6E_R1_EXECUTOR_MUTATED=0",
    "REPAIR_AUTHORIZED=0",
    "E4C6E_R2_REEXECUTION_AUTHORIZED=0",
    "CROSS_COORDINATE_METRIC_SCALE_FROZEN=0",
    "GEOMETRY_AUTHORIZED=0",
    "E4C6E_R1R0_I_SELECTOR_CATEGORICAL_FORENSIC=PASS",
]
text="\n".join(log_lines)+"\n"
EXEC.write_text(text,encoding="utf-8")
AUDIT.write_text(text,encoding="utf-8")

with DEC.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["decision","value"])
    w.writerow(["FAILURE_CAUSE_CLASS",cause])
    w.writerow(["STRUCTURAL_REPAIR_CANDIDATE",candidate])
    w.writerow(["REPAIR_AUTHORIZED","0"])
    w.writerow(["E4C6E_R2_REEXECUTION_AUTHORIZED","0"])
    w.writerow(["GEOMETRY_AUTHORIZED","0"])

print(text,end="")
