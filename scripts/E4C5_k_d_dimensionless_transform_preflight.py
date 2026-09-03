#!/usr/bin/env python3
from pathlib import Path
import csv,hashlib,json

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"data/metadata/E4C5_k_d_dimensionless_transform_contract.json"
LINEAGE=ROOT/"data/metadata/E4C5_frozen_input_lineage.tsv"
PRIOR=ROOT/"data/metadata/E4C5_prior_k_d_semantic_lineage.tsv"

EXEC=ROOT/"data/metadata/E4C5_execution.txt"
AUDIT=ROOT/"data/metadata/E4C5_k_d_dimensionless_transform_audit.txt"
REGISTRY=ROOT/"data/results/E4C5_k_d_transform_registry.tsv"
DECISION=ROOT/"data/results/E4C5_k_d_current_transform_decision.tsv"
NEXT=ROOT/"data/results/E4C5_post_k_d_sequence.tsv"

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""): h.update(b)
    return h.hexdigest()

def tsv(p):
    with p.open("r",encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f,delimiter="\t"))

c=json.loads(CONTRACT.read_text())
assert c["phase"]=="E4C5"
assert c["input_policy"]["raw_SCF_read"] is False
assert c["common_transform_rules"]["target_8_cell_fitted_scale"] is False
assert c["K"]["record_level_redefinition"] is False
assert c["D"]["transform_family"]=="DOCUMENTED_UNIT_TO_FRACTION_THEN_NEGATE"
assert c["metric_readiness"]["geometry_ready"] is False

for r in tsv(LINEAGE):
    p=ROOT/r["artifact"]
    if not p.exists() or sha(p)!=r["sha256"]:
        raise RuntimeError(f"frozen lineage mismatch: {r['artifact']}")

if len(tsv(PRIOR))<2:
    raise RuntimeError("insufficient K/D semantic lineage")

reg=[
("K","K_FIN_MEAN","FIN","USD","LOG1P_REFERENCE_RATIO","ln(1 + K_FIN_MEAN / K_REF_FIN_USD)","HIGHER_IS_BETTER","PARAMETER_PENDING"),
("D","D_PIRTOTAL_MEAN","PIRTOTAL","DOCUMENTED_RATIO_OR_PERCENT","UNIT_TO_FRACTION_THEN_NEGATE","-PIRTOTAL_FRACTION","HIGHER_IS_BETTER","UNIT_MULTIPLIER_PENDING"),
("D_SENSITIVITY","DEBT2INC","DEBT2INC","DOCUMENTED_RATIO_OR_PERCENT","SIGN_ORIENT_ONLY_AFTER_UNIT_AUDIT","-DEBT2INC_FRACTION","HIGHER_IS_BETTER","PRESERVED_SENSITIVITY"),
]
with REGISTRY.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["component","estimand","raw_variable","raw_units","transform_family","formula","orientation","status"])
    w.writerows(reg)

decision=[
("K_DIMENSIONLESS_TRANSFORM_ARCHITECTURE_FROZEN","1"),
("K_TRANSFORM","LN1P_K_FIN_MEAN_OVER_K_REF_FIN_USD"),
("K_REF_FIN_USD_VALUE_FROZEN","0"),
("K_REF_USES_TARGET_8_CELLS","0"),
("K_RECORD_LEVEL_ESTIMAND_REDEFINED","0"),
("D_DIMENSIONLESS_TRANSFORM_ARCHITECTURE_FROZEN","1"),
("D_TRANSFORM","NEGATIVE_PIRTOTAL_FRACTION"),
("D_EXACT_UNIT_MULTIPLIER_FROZEN","0"),
("D_TARGET_SAMPLE_SCALE_PARAMETER","0"),
("TARGET_8_CELL_ZSCORE_AUTHORIZED","0"),
("TARGET_8_CELL_MINMAX_AUTHORIZED","0"),
("TARGET_8_CELL_RANK_AUTHORIZED","0"),
("TARGET_8_CELL_PCA_WHITENING_AUTHORIZED","0"),
("CROSS_COORDINATE_METRIC_SCALE_FROZEN","0"),
("TRANSFORMED_K_D_VALUES_COMPUTED","0"),
("GEOMETRY_READY","0"),
("E4C5A_K_REFERENCE_SCALE_D_UNIT_SEMANTICS_PREFLIGHT_AUTHORIZED","1"),
]
with DECISION.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["decision","value"]);w.writerows(decision)

seq=[
("1","E4C5A","K_REFERENCE_SCALE_D_UNIT_SEMANTICS_PREFLIGHT","AUTHORIZED_NEXT"),
("2","POST_E4C5A","FIRST_K_D_TRANSFORM_EXECUTION","PENDING"),
("3","POST_TRANSFORM","CROSS_COORDINATE_METRIC_SCALE_READINESS","PENDING"),
("4","POST_METRIC_READINESS","DIMENSIONALITY_GEOMETRY_PREFLIGHT","NOT_AUTHORIZED_YET"),
]
with NEXT.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["order","phase","scope","status"]);w.writerows(seq)

log="\n".join([
"RAW_SCF_DATA_READ=0",
"PRIOR_NUMERIC_K_D_TARGET_RESULTS_OPENED=0",
"NEW_K_D_ECONOMIC_VALUES_OPENED=0",
"REESTIMATION_PERFORMED=0",
"NEW_REPLICATES_COMPUTED=0",
"FROZEN_PRIOR_K_D_SEMANTICS_ONLY=1",
"K_PRIMARY_ESTIMAND=K_FIN_MEAN",
"K_RAW_VARIABLE=FIN",
"K_RAW_ORIENTATION=HIGHER_IS_BETTER",
"K_DIMENSIONLESS_TRANSFORM_ARCHITECTURE_FROZEN=1",
"K_TRANSFORM=LN1P_K_FIN_MEAN_OVER_K_REF_FIN_USD",
"K_REF_FIN_USD_VALUE_FROZEN=0",
"K_REF_USES_TARGET_8_CELLS=0",
"K_REF_USES_OWNER_RENTER_LABELS=0",
"K_REF_USES_AGE_BAND_LABELS=0",
"K_RECORD_LEVEL_ESTIMAND_REDEFINED=0",
"D_PRIMARY_ESTIMAND=D_PIRTOTAL_MEAN",
"D_RAW_VARIABLE=PIRTOTAL",
"D_RAW_BURDEN_ORIENTATION=LOWER_IS_BETTER",
"D_DIMENSIONLESS_TRANSFORM_ARCHITECTURE_FROZEN=1",
"D_TRANSFORM=NEGATIVE_PIRTOTAL_FRACTION",
"D_EXACT_UNIT_MULTIPLIER_FROZEN=0",
"D_TARGET_SAMPLE_SCALE_PARAMETER=0",
"DEBT2INC=PRESERVED_SENSITIVITY_NOT_PRIMARY",
"TARGET_8_CELL_ZSCORE_AUTHORIZED=0",
"TARGET_8_CELL_MINMAX_AUTHORIZED=0",
"TARGET_8_CELL_RANK_AUTHORIZED=0",
"TARGET_8_CELL_PCA_WHITENING_AUTHORIZED=0",
"OWNER_RENTER_DIRECTION_USED_AS_TRANSFORM_GATE=0",
"STATISTICAL_SIGNIFICANCE_USED_AS_TRANSFORM_GATE=0",
"GEOMETRY_USED_AS_TRANSFORM_GATE=0",
"TRANSFORMED_K_D_VALUES_COMPUTED=0",
"CROSS_COORDINATE_METRIC_SCALE_FROZEN=0",
"GEOMETRY_READY=0",
"FIVE_COMPONENT_STATE_VECTOR_AUTHORIZED=0",
"FIVE_COMPONENT_NORMALIZATION_AUTHORIZED=0",
"GEOMETRY_AUTHORIZED=0",
"DIMENSIONALITY_TEST_AUTHORIZED=0",
"REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
"FINAL_SCALAR_AUTHORIZED=0",
"E4C5_K_D_DIMENSIONLESS_TRANSFORM_PREFLIGHT=PASS",
"E4C5A_K_REFERENCE_SCALE_D_UNIT_SEMANTICS_PREFLIGHT_AUTHORIZED=1",
])+"\n"

EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
