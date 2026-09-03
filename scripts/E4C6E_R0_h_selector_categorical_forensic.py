#!/usr/bin/env python3
from pathlib import Path
from collections import Counter
import csv

ROOT=Path(__file__).resolve().parents[1]
H_SRC=ROOT/"data/results/E4C3D_h_access_inference_summary.tsv"
H_WRITER=ROOT/"scripts/E4C3D_first_acs2022_h_access_execution.py"

EXEC=ROOT/"data/metadata/E4C6E_R0_execution.txt"
AUDIT=ROOT/"data/metadata/E4C6E_R0_h_selector_categorical_forensic_audit.txt"
TOKENS=ROOT/"data/results/E4C6E_R0_h_categorical_token_inventory.tsv"
COUNTS=ROOT/"data/results/E4C6E_R0_h_selector_filter_counts.tsv"
SIGNATURES=ROOT/"data/results/E4C6E_R0_h_categorical_row_signatures.tsv"
DECISION=ROOT/"data/results/E4C6E_R0_h_selector_categorical_forensic_decision.tsv"

FIELDS=["entity_type","role","estimand","age_band","entity"]
AGES={"25-34","35-44","45-54","55-64"}

def norm(s):
    return (s or "").strip()

def upper(s):
    return norm(s).upper()

# Parse the header, then split each line and retain only categorical positions.
# Numeric estimate/se/CI strings are neither converted nor emitted.
with H_SRC.open("r",encoding="utf-8-sig",newline="") as f:
    header=f.readline().rstrip("\r\n").split("\t")
    expected=["entity_type","role","estimand","age_band","entity","estimate","se","ci95_low","ci95_high"]
    if header != expected:
        raise RuntimeError(f"unexpected H source header: {header}")
    idx={k:header.index(k) for k in FIELDS}
    cats=[]
    for line_no,line in enumerate(f,start=2):
        parts=line.rstrip("\r\n").split("\t")
        if len(parts)!=len(header):
            raise RuntimeError(f"column count mismatch source line {line_no}")
        r={k:parts[idx[k]] for k in FIELDS}
        r["_line"]=line_no
        cats.append(r)

def count(pred):
    return sum(1 for r in cats if pred(r))

# Token inventory.
with TOKENS.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["field","token","count"])
    for field in FIELDS:
        c=Counter(r[field] for r in cats)
        for token,n in sorted(c.items(),key=lambda x:(x[0])):
            w.writerow([field,token,n])

# Categorical row signatures only.
with SIGNATURES.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["source_line","entity_type","role","estimand","age_band","entity"])
    for r in cats:
        w.writerow([r["_line"],r["entity_type"],r["role"],r["estimand"],r["age_band"],r["entity"]])

role_exact=lambda r:norm(r["role"])=="PRIMARY"
role_norm=lambda r:upper(r["role"])=="PRIMARY"
est_exact=lambda r:norm(r["estimand"])=="H_ACCESS_SPACE_ROOMS_PER_PERSON"
est_room_sem=lambda r:"ROOM" in upper(r["estimand"]) and "PERSON" in upper(r["estimand"])
age_exact=lambda r:norm(r["age_band"]) in AGES
entity_exact=lambda r:upper(r["entity"]) in {"OWNER","RENTER"}
entity_ownerlike=lambda r:("OWNER" in upper(r["entity"]) or "RENT" in upper(r["entity"]))

metrics=[
    ("H_TOTAL_DATA_ROWS",len(cats)),
    ("H_ROLE_PRIMARY_EXACT_COUNT",count(role_exact)),
    ("H_ROLE_PRIMARY_NORMALIZED_COUNT",count(role_norm)),
    ("H_ESTIMAND_EXACT_COUNT",count(est_exact)),
    ("H_ESTIMAND_ROOM_PERSON_SEMANTIC_TOKEN_COUNT",count(est_room_sem)),
    ("H_FROZEN_AGE_TOKEN_COUNT",count(age_exact)),
    ("H_OWNER_RENTER_EXACT_ENTITY_COUNT",count(entity_exact)),
    ("H_OWNER_RENTER_SEMANTIC_ENTITY_COUNT",count(entity_ownerlike)),
    ("H_ROLE_AND_ESTIMAND_EXACT_COUNT",count(lambda r:role_exact(r) and est_exact(r))),
    ("H_ROLE_ESTIMAND_AGE_EXACT_COUNT",count(lambda r:role_exact(r) and est_exact(r) and age_exact(r))),
    ("H_FAILED_SELECTOR_REPRODUCED_COUNT",count(lambda r:role_exact(r) and est_exact(r) and age_exact(r) and entity_exact(r))),
]
with COUNTS.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["diagnostic","count"])
    w.writerows(metrics)

m=dict(metrics)
if m["H_ROLE_PRIMARY_EXACT_COUNT"]==0:
    cause="H_ROLE_TOKEN_MISMATCH"
    candidate="ALIGN_H_ROLE_SELECTOR_TO_FROZEN_SOURCE_CATEGORICAL_ROLE_SEMANTICS"
elif m["H_ESTIMAND_EXACT_COUNT"]==0:
    cause="H_ESTIMAND_TOKEN_MISMATCH"
    candidate="ALIGN_H_ESTIMAND_SELECTOR_TO_FROZEN_SOURCE_CATEGORICAL_ESTIMAND_SEMANTICS"
elif m["H_ROLE_AND_ESTIMAND_EXACT_COUNT"]==0:
    cause="H_ROLE_AND_ESTIMAND_COMBINATION_MISMATCH"
    candidate="ALIGN_H_SELECTOR_TO_FROZEN_ROLE_ESTIMAND_PAIR"
elif m["H_ROLE_ESTIMAND_AGE_EXACT_COUNT"]==0:
    cause="H_AGE_TOKEN_MISMATCH"
    candidate="ALIGN_H_AGE_SELECTOR_TO_FROZEN_SOURCE_CATEGORICAL_AGE_SEMANTICS"
elif m["H_FAILED_SELECTOR_REPRODUCED_COUNT"]==0:
    cause="H_ENTITY_TOKEN_MISMATCH"
    candidate="ALIGN_H_ENTITY_SELECTOR_TO_FROZEN_SOURCE_CATEGORICAL_ENTITY_SEMANTICS"
else:
    cause="H_SELECTOR_SHAPE_UNEXPECTED"
    candidate="REQUIRE_DEEPER_STATIC_SELECTOR_FORENSIC"

writer_text=H_WRITER.read_text(encoding="utf-8",errors="replace")
writer_contains_primary=("PRIMARY" in writer_text)
writer_contains_estimand=("H_ACCESS_SPACE_ROOMS_PER_PERSON" in writer_text)
writer_contains_inference_summary=("h_access_inference_summary" in writer_text.lower())

decisions=[
    ["FAILURE_CAUSE_CLASS",cause],
    ["STRUCTURAL_REPAIR_CANDIDATE",candidate],
    ["FAILED_SELECTOR_REPRODUCED_COUNT",str(m["H_FAILED_SELECTOR_REPRODUCED_COUNT"])],
    ["NUMERIC_FIELDS_INTERPRETED","0"],
    ["NUMERIC_FIELDS_EMITTED","0"],
    ["ESTIMATE_SE_CI_VALUES_EMITTED","0"],
    ["SCIENTIFIC_ESTIMATOR_MUTATED","0"],
    ["TRANSFORM_MUTATED","0"],
    ["COMPONENT_DEFINITION_MUTATED","0"],
    ["E4C6D_FROZEN_SELECTOR_MUTATED","0"],
    ["REPAIR_AUTHORIZED","0"],
    ["E4C6E_REEXECUTION_AUTHORIZED","0"],
    ["GEOMETRY_AUTHORIZED","0"],
]
with DECISION.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["decision","value"])
    w.writerows(decisions)

lines=[
    "POST_E4C6E_FAILURE_FORENSIC=1",
    "PRIOR_E4C6E_FAILURE_PRESERVED=1",
    f"H_TOTAL_DATA_ROWS={m['H_TOTAL_DATA_ROWS']}",
    f"H_ROLE_PRIMARY_EXACT_COUNT={m['H_ROLE_PRIMARY_EXACT_COUNT']}",
    f"H_ROLE_PRIMARY_NORMALIZED_COUNT={m['H_ROLE_PRIMARY_NORMALIZED_COUNT']}",
    f"H_ESTIMAND_EXACT_COUNT={m['H_ESTIMAND_EXACT_COUNT']}",
    f"H_ESTIMAND_ROOM_PERSON_SEMANTIC_TOKEN_COUNT={m['H_ESTIMAND_ROOM_PERSON_SEMANTIC_TOKEN_COUNT']}",
    f"H_FROZEN_AGE_TOKEN_COUNT={m['H_FROZEN_AGE_TOKEN_COUNT']}",
    f"H_OWNER_RENTER_EXACT_ENTITY_COUNT={m['H_OWNER_RENTER_EXACT_ENTITY_COUNT']}",
    f"H_OWNER_RENTER_SEMANTIC_ENTITY_COUNT={m['H_OWNER_RENTER_SEMANTIC_ENTITY_COUNT']}",
    f"H_ROLE_AND_ESTIMAND_EXACT_COUNT={m['H_ROLE_AND_ESTIMAND_EXACT_COUNT']}",
    f"H_ROLE_ESTIMAND_AGE_EXACT_COUNT={m['H_ROLE_ESTIMAND_AGE_EXACT_COUNT']}",
    f"H_FAILED_SELECTOR_REPRODUCED_COUNT={m['H_FAILED_SELECTOR_REPRODUCED_COUNT']}",
    f"H_WRITER_CONTAINS_PRIMARY_TOKEN={int(writer_contains_primary)}",
    f"H_WRITER_CONTAINS_FROZEN_ESTIMAND_TOKEN={int(writer_contains_estimand)}",
    f"H_WRITER_CONTAINS_INFERENCE_SUMMARY_TOKEN={int(writer_contains_inference_summary)}",
    f"FAILURE_CAUSE_CLASS={cause}",
    f"STRUCTURAL_REPAIR_CANDIDATE={candidate}",
    "CATEGORICAL_FIELDS_INSPECTED=entity_type,role,estimand,age_band,entity",
    "NUMERIC_FIELDS_INTERPRETED=0",
    "NUMERIC_FIELDS_EMITTED=0",
    "ESTIMATE_SE_CI_VALUES_EMITTED=0",
    "SIGN_USED_AS_FORENSIC_GATE=0",
    "MAGNITUDE_USED_AS_FORENSIC_GATE=0",
    "STATISTICAL_SIGNIFICANCE_USED_AS_FORENSIC_GATE=0",
    "OWNER_RENTER_OUTCOME_DIRECTION_USED_AS_FORENSIC_GATE=0",
    "SCIENTIFIC_ESTIMATOR_MUTATED=0",
    "TRANSFORM_MUTATED=0",
    "COMPONENT_DEFINITION_MUTATED=0",
    "E4C6D_FROZEN_SELECTOR_MUTATED=0",
    "REPAIR_AUTHORIZED=0",
    "E4C6E_REEXECUTION_AUTHORIZED=0",
    "CROSS_COORDINATE_METRIC_SCALE_FROZEN=0",
    "GEOMETRY_AUTHORIZED=0",
    "E4C6E_R0_H_SELECTOR_CATEGORICAL_FORENSIC=PASS",
]
log="\n".join(lines)+"\n"
EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
print("===== H CATEGORICAL TOKEN INVENTORY =====")
print(TOKENS.read_text(encoding="utf-8"),end="")
print("===== H SELECTOR FILTER COUNTS =====")
print(COUNTS.read_text(encoding="utf-8"),end="")
print("===== H CATEGORICAL ROW SIGNATURES — NO NUMERIC VALUES =====")
print(SIGNATURES.read_text(encoding="utf-8"),end="")
