#!/usr/bin/env python3
from pathlib import Path
import csv
from decimal import Decimal, InvalidOperation

ROOT=Path(__file__).resolve().parents[1]

H_SRC=ROOT/"data/results/E4C3D_h_access_inference_summary.tsv"
KD_SRC=ROOT/"data/results/E4C5I_k_d_component_inference_registry.tsv"
I_SRC=ROOT/"data/results/E4A2D_2022_cps_i_cohort_inference.tsv"

EXEC=ROOT/"data/metadata/E4C6E_execution.txt"
AUDIT=ROOT/"data/metadata/E4C6E_partial_observed_coordinate_registry_execution_audit.txt"
REGISTRY=ROOT/"data/results/E4C6E_partial_observed_coordinate_registry.tsv"
SOURCE_LEDGER=ROOT/"data/results/E4C6E_selected_source_row_lineage.tsv"
HARD=ROOT/"data/results/E4C6E_execution_hard_gates.tsv"
DECISION=ROOT/"data/results/E4C6E_partial_observed_coordinate_registry_decision.tsv"

AGES=["25-34","35-44","45-54","55-64"]
TENURES=["OWNER","RENTER"]
COORD_ORDER=[
    "H_ACCESS_SPACE_ROOMS_PER_PERSON",
    "K_FIN_MEAN_TRANSFORMED",
    "D_PIRTOTAL_MEAN_STATE_TRANSFORMED",
    "I_FYFT_SHARE",
    "I_SEARCH_SECURITY",
]
AGE_IDX={v:i for i,v in enumerate(AGES)}
TEN_IDX={v:i for i,v in enumerate(TENURES)}
COORD_IDX={v:i for i,v in enumerate(COORD_ORDER)}

def norm(s):
    return (s or "").strip()

def norm_upper(s):
    return norm(s).upper()

def norm_tenure(s):
    x=norm_upper(s)
    if x=="OWNER":
        return "OWNER"
    if x=="RENTER":
        return "RENTER"
    return None

H_AGE_TOKEN_TO_CANONICAL={
    "AGE25_34":"25-34",
    "AGE35_44":"35-44",
    "AGE45_54":"45-54",
    "AGE55_64":"55-64",
}

def norm_h_age(s):
    return H_AGE_TOKEN_TO_CANONICAL.get(norm_upper(s))

def dec(s, field, source_row):
    raw=norm(s)
    if raw=="":
        raise RuntimeError(f"empty decimal field={field} source_row={source_row}")
    try:
        d=Decimal(raw)
    except InvalidOperation as e:
        raise RuntimeError(f"invalid decimal field={field} value={raw!r} source_row={source_row}") from e
    if not d.is_finite():
        raise RuntimeError(f"nonfinite decimal field={field} value={raw!r} source_row={source_row}")
    return d

def canon(d):
    if d == 0:
        return "0"
    return format(d, "f")

def read_tsv(path):
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f,delimiter="\t"))

registry=[]
ledger=[]

def add_row(year,age,tenure,component,coordinate_id,scope,point,se,source_survey,source_phase,
            source_path, source_row_number, source_estimand, source_point_field, source_se_field,
            source_point_string, source_se_string, state_sign, operation):
    if age not in AGE_IDX:
        raise RuntimeError(f"unexpected age {age}")
    if tenure not in TEN_IDX:
        raise RuntimeError(f"unexpected tenure {tenure}")
    if se < 0:
        raise RuntimeError(f"negative standard error coordinate={coordinate_id} age={age} tenure={tenure}")
    registry.append({
        "year":str(year),
        "age_band":age,
        "tenure":tenure,
        "component":component,
        "coordinate_id":coordinate_id,
        "coordinate_scope":scope,
        "point_state":canon(point),
        "se_state":canon(se),
        "units":"DIMENSIONLESS",
        "orientation":"HIGHER_IS_BETTER",
        "source_survey":source_survey,
        "source_phase":source_phase,
    })
    ledger.append({
        "coordinate_id":coordinate_id,
        "age_band":age,
        "tenure":tenure,
        "source_path":source_path,
        "source_data_row_number":str(source_row_number),
        "source_estimand_or_statistic":source_estimand,
        "source_point_field":source_point_field,
        "source_se_field":source_se_field,
        "source_point_string":source_point_string,
        "source_se_string":source_se_string,
        "frozen_state_sign":str(state_sign),
        "state_operation":operation,
    })

# H: only primary H_ACCESS owner/renter cells.
hrows=read_tsv(H_SRC)
h_selected=0
for n,r in enumerate(hrows,start=2):
    if norm_upper(r.get("role"))!="PRIMARY":
        continue
    if norm(r.get("estimand"))!="H_ACCESS_SPACE_ROOMS_PER_PERSON":
        continue
    age=norm_h_age(r.get("age_band"))
    tenure=norm_tenure(r.get("entity"))
    if age not in AGE_IDX or tenure is None:
        continue
    p=dec(r.get("estimate"),"estimate",n)
    se=dec(r.get("se"),"se",n)
    add_row(
        2022,age,tenure,"H","H_ACCESS_SPACE_ROOMS_PER_PERSON",
        "PRIMARY_OBSERVED_SUBCOORDINATE_NOT_FULL_H_STATE",
        p,se,"ACS2022","E4C3D",
        str(H_SRC.relative_to(ROOT)),n,"H_ACCESS_SPACE_ROOMS_PER_PERSON","estimate","se",
        norm(r.get("estimate")),norm(r.get("se")),1,"IDENTITY"
    )
    h_selected+=1

# K and D: already state-oriented transformed cells in E4C5I.
kdrows=read_tsv(KD_SRC)
kd_selected={"K":0,"D":0}
for n,r in enumerate(kdrows,start=2):
    if norm_upper(r.get("inference_role"))!="CELL":
        continue
    comp=norm_upper(r.get("component"))
    if comp not in {"K","D"}:
        continue
    expected_stat="K_FIN_MEAN" if comp=="K" else "D_PIRTOTAL_MEAN"
    if norm(r.get("statistic_id"))!=expected_stat:
        continue
    if norm(r.get("year"))!="2022":
        continue
    age=norm(r.get("age_band"))
    tenure=norm_tenure(r.get("tenure"))
    if age not in AGE_IDX or tenure is None:
        continue
    p=dec(r.get("point_state"),"point_state",n)
    se=dec(r.get("combined_se_state"),"combined_se_state",n)
    cid="K_FIN_MEAN_TRANSFORMED" if comp=="K" else "D_PIRTOTAL_MEAN_STATE_TRANSFORMED"
    operation="IDENTITY_ALREADY_TRANSFORMED" if comp=="K" else "IDENTITY_ALREADY_STATE_ORIENTED"
    add_row(
        2022,age,tenure,comp,cid,"FULL_COMPONENT_SCALAR_COORDINATE",
        p,se,"SCF2022","E4C5I",
        str(KD_SRC.relative_to(ROOT)),n,expected_stat,"point_state","combined_se_state",
        norm(r.get("point_state")),norm(r.get("combined_se_state")),1,operation
    )
    kd_selected[comp]+=1

# I: two PRIMARY estimands; exact frozen sign orientation.
irows=read_tsv(I_SRC)
i_selected={"I_FYFT_SHARE":0,"I_SEARCH_SECURITY":0}
for n,r in enumerate(irows,start=2):
    if norm_upper(r.get("role"))!="PRIMARY":
        continue
    if norm(r.get("year"))!="2022":
        continue
    est=norm(r.get("estimand"))
    if est=="I_FYFT_SHARE":
        cid="I_FYFT_SHARE"
        expected_sign=Decimal("1")
    elif est=="I_SEARCH_BURDEN_SHARE":
        cid="I_SEARCH_SECURITY"
        expected_sign=Decimal("-1")
    else:
        continue
    age=norm(r.get("age_band"))
    tenure=norm_tenure(r.get("tenure"))
    if age not in AGE_IDX or tenure is None:
        continue
    sgn=dec(r.get("state_sign"),"state_sign",n)
    if sgn != expected_sign:
        raise RuntimeError(f"frozen I state_sign mismatch estimand={est} row={n}: {sgn}")
    rawp=dec(r.get("point_estimate"),"point_estimate",n)
    se=dec(r.get("replicate_se"),"replicate_se",n)
    p=rawp*sgn
    add_row(
        2022,age,tenure,"I",cid,"PRIMARY_OBSERVED_SUBCOORDINATE",
        p,se,"CPS_ASEC_2022","E4A2D+E4C4",
        str(I_SRC.relative_to(ROOT)),n,est,"point_estimate","replicate_se",
        norm(r.get("point_estimate")),norm(r.get("replicate_se")),canon(sgn),
        "EXACT_DECIMAL_MULTIPLY_BY_STATE_SIGN"
    )
    i_selected[cid]+=1

# Exact precommitted selection counts.
if h_selected != 8:
    raise RuntimeError(f"H selected row count {h_selected} != 8")
if kd_selected != {"K":8,"D":8}:
    raise RuntimeError(f"K/D selected row counts {kd_selected} != {{'K':8,'D':8}}")
if i_selected != {"I_FYFT_SHARE":8,"I_SEARCH_SECURITY":8}:
    raise RuntimeError(f"I selected row counts {i_selected} incorrect")

# Unique exact 5 x 4 x 2 grid.
if len(registry)!=40:
    raise RuntimeError(f"registry row count {len(registry)} != 40")
keys=[(r["coordinate_id"],r["age_band"],r["tenure"]) for r in registry]
if len(set(keys))!=40:
    raise RuntimeError("duplicate coordinate-age-tenure keys")
expected={(c,a,t) for c in COORD_ORDER for a in AGES for t in TENURES}
if set(keys)!=expected:
    missing=sorted(expected-set(keys))
    extra=sorted(set(keys)-expected)
    raise RuntimeError(f"registry grid mismatch missing={missing} extra={extra}")

registry.sort(key=lambda r:(COORD_IDX[r["coordinate_id"]],AGE_IDX[r["age_band"]],TEN_IDX[r["tenure"]]))
ledger.sort(key=lambda r:(COORD_IDX[r["coordinate_id"]],AGE_IDX[r["age_band"]],TEN_IDX[r["tenure"]]))

registry_fields=[
    "year","age_band","tenure","component","coordinate_id","coordinate_scope",
    "point_state","se_state","units","orientation","source_survey","source_phase"
]
with REGISTRY.open("w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=registry_fields,delimiter="\t",lineterminator="\n")
    w.writeheader()
    w.writerows(registry)

ledger_fields=[
    "coordinate_id","age_band","tenure","source_path","source_data_row_number",
    "source_estimand_or_statistic","source_point_field","source_se_field",
    "source_point_string","source_se_string","frozen_state_sign","state_operation"
]
with SOURCE_LEDGER.open("w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=ledger_fields,delimiter="\t",lineterminator="\n")
    w.writeheader()
    w.writerows(ledger)

hard=[
    ["E4C6E_SOURCE_SELECTION_COUNTS","PASS"],
    ["E4C6E_EXACT_5_X_4_X_2_GRID","PASS"],
    ["E4C6E_UNIQUE_CELL_KEYS","PASS"],
    ["E4C6E_FINITE_DECIMAL_VALUES","PASS"],
    ["E4C6E_NONNEGATIVE_SOURCE_SE_DEFINITION","PASS"],
    ["E4C6E_I_FROZEN_STATE_SIGN_IDENTITY","PASS"],
    ["E4C6E_SEMANTIC_BOUNDARIES","PASS"],
]
with HARD.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["gate","value"])
    w.writerows(hard)

decisions=[
    ["PARTIAL_OBSERVED_COORDINATE_REGISTRY_ROW_COUNT","40"],
    ["PARTIAL_OBSERVED_COORDINATE_COUNT","5"],
    ["NUMERICALLY_REPRESENTED_CONCEPT_COUNT","4"],
    ["H_SELECTED_CELL_ROWS","8"],
    ["K_SELECTED_CELL_ROWS","8"],
    ["D_SELECTED_CELL_ROWS","8"],
    ["I_FYFT_SELECTED_CELL_ROWS","8"],
    ["I_SEARCH_SECURITY_SELECTED_CELL_ROWS","8"],
    ["C_INCLUDED_IN_PARTIAL_REGISTRY","0"],
    ["H_ACCESS_PROMOTED_TO_FULL_H_STATE","0"],
    ["I_SENSITIVITY_ROWS_INCLUDED","0"],
    ["I_SCALAR_FORCED","0"],
    ["PARTIAL_REGISTRY_IS_FULL_CHKDI_STATE_VECTOR","0"],
    ["PARTIAL_REGISTRY_IS_FINAL_MODEL","0"],
    ["SOURCE_STANDARD_ERRORS_REUSED","1"],
    ["NEW_UNCERTAINTY_ESTIMATOR_INTRODUCED","0"],
    ["CROSS_SURVEY_INDEPENDENCE_ASSUMED","0"],
    ["CROSS_COORDINATE_COVARIANCE_COMPUTED","0"],
    ["CROSS_COORDINATE_METRIC_SCALE_FROZEN","0"],
    ["GEOMETRY_AUTHORIZED","0"],
    ["E4C7_CROSS_COORDINATE_METRIC_SCALE_ARCHITECTURE_PREFLIGHT_AUTHORIZED","1"],
]
with DECISION.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["decision","value"])
    w.writerows(decisions)

log="\n".join([
    "E4C6D_FROZEN_SELECTORS_REUSED=1",
    "ECONOMIC_SOURCE_ROWS_OPENED_AFTER_PRECOMMIT=1",
    "H_SELECTED_CELL_ROWS=8",
    "K_SELECTED_CELL_ROWS=8",
    "D_SELECTED_CELL_ROWS=8",
    "I_FYFT_SELECTED_CELL_ROWS=8",
    "I_SEARCH_SECURITY_SELECTED_CELL_ROWS=8",
    "PARTIAL_OBSERVED_COORDINATE_COUNT=5",
    "PARTIAL_OBSERVED_COORDINATE_REGISTRY_ROW_COUNT=40",
    "NUMERICALLY_REPRESENTED_CONCEPT_COUNT=4",
    "EXACT_5_X_4_X_2_GRID_PASS=1",
    "UNIQUE_COORDINATE_AGE_TENURE_KEYS_PASS=1",
    "DECIMAL_SOURCE_PARSING_PASS=1",
    "BINARY_FLOAT_ROUNDTRIP_USED_FOR_REGISTRY_VALUES=0",
    "SOURCE_STANDARD_ERRORS_REUSED=1",
    "NEW_UNCERTAINTY_ESTIMATOR_INTRODUCED=0",
    "C_INCLUDED_IN_PARTIAL_REGISTRY=0",
    "H_ACCESS_PROMOTED_TO_FULL_H_STATE=0",
    "I_PRIMARY_COORDINATE_COUNT=2",
    "I_SENSITIVITY_ROWS_INCLUDED=0",
    "I_SCALAR_FORCED=0",
    "PARTIAL_REGISTRY_IS_FULL_CHKDI_STATE_VECTOR=0",
    "PARTIAL_REGISTRY_IS_FINAL_MODEL=0",
    "SIGN_USED_AS_EXECUTION_GATE=0",
    "MAGNITUDE_USED_AS_EXECUTION_GATE=0",
    "STATISTICAL_SIGNIFICANCE_USED_AS_EXECUTION_GATE=0",
    "OWNER_RENTER_DIRECTION_USED_AS_EXECUTION_GATE=0",
    "COMPONENT_DEFINITION_MUTATED=0",
    "TRANSFORM_MUTATED=0",
    "NEW_ESTIMATOR_INTRODUCED=0",
    "NEW_INFERENCE_COMPUTED=0",
    "CROSS_SURVEY_INDEPENDENCE_ASSUMED=0",
    "CROSS_COORDINATE_COVARIANCE_COMPUTED=0",
    "CROSS_COORDINATE_METRIC_SCALE_FROZEN=0",
    "GEOMETRY_READY=0",
    "GEOMETRY_AUTHORIZED=0",
    "DIMENSIONALITY_TEST_AUTHORIZED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "E4C6E_PARTIAL_OBSERVED_COORDINATE_REGISTRY_EXECUTION=PASS",
    "E4C7_CROSS_COORDINATE_METRIC_SCALE_ARCHITECTURE_PREFLIGHT_AUTHORIZED=1",
])+"\n"

EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")

print(log,end="")
print("===== PARTIAL OBSERVED-COORDINATE REGISTRY — NO OUTCOME GATE =====")
for r in registry:
    print("\t".join(r[k] for k in registry_fields))
