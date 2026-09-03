#!/usr/bin/env python3
from pathlib import Path
import csv, hashlib, io, json, math, re, zipfile

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"data/metadata/E4C5A_k_reference_scale_d_unit_semantics_contract.json"
LINEAGE=ROOT/"data/metadata/E4C5A_frozen_input_lineage.tsv"
MANIFEST=ROOT/"data/metadata/E4C5A_official_source_manifest.tsv"

ZIP=ROOT/"data/raw/scf/2022/reference/scfp2022excel.zip"
MACRO=ROOT/"data/raw/scf/2022/reference/bulletin.macro.txt"

EXEC=ROOT/"data/metadata/E4C5A_execution.txt"
AUDIT=ROOT/"data/metadata/E4C5A_k_reference_scale_d_unit_semantics_audit.txt"
KREF=ROOT/"data/results/E4C5A_k_reference_scale.tsv"
DUNIT=ROOT/"data/results/E4C5A_d_unit_semantics.tsv"
DECISION=ROOT/"data/results/E4C5A_k_d_parameter_decision.tsv"

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""): h.update(b)
    return h.hexdigest()

def tsv(p):
    with p.open("r",encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f,delimiter="\t"))

def num(x):
    try:
        if x is None or str(x).strip()=="":
            return None
        v=float(x)
        return v if math.isfinite(v) else None
    except Exception:
        return None

def weighted_median(pairs):
    pairs=sorted(pairs,key=lambda z:z[0])
    tw=sum(w for _,w in pairs)
    if not math.isfinite(tw) or tw<=0:
        raise RuntimeError("nonpositive total eligible weight")
    threshold=0.5*tw
    c=0.0
    for value,w in pairs:
        c+=w
        if c>=threshold:
            return value,tw
    raise RuntimeError("weighted median traversal failure")

c=json.loads(CONTRACT.read_text(encoding="utf-8"))
assert c["phase"]=="E4C5A"
assert c["K_reference"]["target_8_cell_values_used"] is False
assert c["D_semantics"]["target_D_values_required"] is False
assert c["hard_boundaries"]["target_K_D_values_opened"] is False

for r in tsv(LINEAGE):
    p=ROOT/r["artifact"]
    if not p.exists() or sha(p)!=r["sha256"]:
        raise RuntimeError(f"lineage mismatch: {r['artifact']}")

man=tsv(MANIFEST)
for r in man:
    if r["row_type"]=="FILE":
        p=ROOT/r["artifact"]
        if not p.exists() or sha(p)!=r["sha256"]:
            raise RuntimeError(f"source hash mismatch: {r['artifact']}")

# D semantics from official Federal Reserve macro. No target values involved.
macro=MACRO.read_text(encoding="utf-8",errors="strict")
compact=re.sub(r"\s+","",macro)
if "PIRTOTAL=(TPAY/MAX((INCOME/12),(100/&CPIADJ89)));" not in compact:
    raise RuntimeError("official PIRTOTAL ratio formula not found")
if "PIR40=(PIRTOTAL>.4);" not in compact:
    raise RuntimeError("official PIR40 threshold cross-check not found")
if "WGT=X42001/5;" not in compact:
    raise RuntimeError("official public-summary WGT construction not found")

d_unit="FRACTION"
d_multiplier=1.0

# Find exactly one CSV member already frozen in central-directory manifest.
members=[r["member_name"] for r in man if r["row_type"]=="ZIP_MEMBER" and r["selected"]=="1"]
if len(members)!=1:
    raise RuntimeError(f"expected exactly one selected CSV member, got {members}")
member=members[0]

# First opening of reference-population values. No target age/tenure fields are accessed.
by_imp={i:[] for i in range(1,6)}
rows_total=0
with zipfile.ZipFile(ZIP,"r") as z:
    with z.open(member,"r") as fb:
        text=io.TextIOWrapper(fb,encoding="utf-8-sig",newline="")
        reader=csv.reader(text)
        header=next(reader)
        cmap={name.strip().upper():idx for idx,name in enumerate(header)}
        for req in ["Y1","WGT","FIN"]:
            if req not in cmap:
                raise RuntimeError(f"required reference field absent: {req}")
        iy,iw,ifin=cmap["Y1"],cmap["WGT"],cmap["FIN"]

        for row in reader:
            rows_total+=1
            if len(row)<=max(iy,iw,ifin):
                raise RuntimeError("short CSV row")
            ys=str(row[iy]).strip()
            # Accept integer-like CSV representation only.
            try:
                yi=int(float(ys))
            except Exception:
                raise RuntimeError(f"invalid Y1: {ys!r}")
            imp=yi%10
            if imp not in by_imp:
                raise RuntimeError(f"unexpected implicate digit: {imp}")
            w=num(row[iw]); fin=num(row[ifin])
            if w is None or fin is None or w<=0 or fin<=0:
                continue
            by_imp[imp].append((fin,w))

if rows_total!=22975:
    raise RuntimeError(f"unexpected SCF summary row count: {rows_total}, expected 22975")

medians=[]
k_rows=[]
for imp in range(1,6):
    pairs=by_imp[imp]
    if not pairs:
        raise RuntimeError(f"empty eligible K reference population implicate {imp}")
    med,tw=weighted_median(pairs)
    if not math.isfinite(med) or med<=0:
        raise RuntimeError(f"invalid weighted median implicate {imp}")
    medians.append(med)
    k_rows.append([str(imp),str(len(pairs)),f"{tw:.12f}",f"{med:.12f}"])

k_ref=sum(medians)/5.0
if not math.isfinite(k_ref) or k_ref<=0:
    raise RuntimeError("invalid K_REF_FIN_USD")

with KREF.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["implicate","eligible_fin_positive_n","eligible_weight_sum","weighted_median_fin_usd"])
    w.writerows(k_rows)
    w.writerow(["MI_ARITHMETIC_MEAN","NA","NA",f"{k_ref:.12f}"])

with DUNIT.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["field","value"])
    w.writerows([
        ["PIRTOTAL_SEMANTIC","RATIO_OF_MONTHLY_DEBT_PAYMENTS_TO_MONTHLY_INCOME_DENOMINATOR"],
        ["PIRTOTAL_UNIT",d_unit],
        ["PIRTOTAL_MULTIPLIER_TO_FRACTION",f"{d_multiplier:.12f}"],
        ["PIR40_THRESHOLD","0.4"],
        ["D_STATE_FORMULA","-PIRTOTAL"],
        ["TARGET_D_VALUES_USED_TO_INFER_UNIT","0"],
    ])

with DECISION.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["decision","value"])
    w.writerows([
        ["K_REF_FIN_USD",f"{k_ref:.12f}"],
        ["K_REF_FIN_USD_VALUE_FROZEN","1"],
        ["K_REF_IMPLICATE_MEDIAN_COUNT","5"],
        ["K_REF_USES_TARGET_8_CELLS","0"],
        ["K_REF_USES_OWNER_RENTER_LABELS","0"],
        ["K_REF_USES_AGE_BAND_LABELS","0"],
        ["D_PIRTOTAL_UNIT","FRACTION"],
        ["D_EXACT_UNIT_MULTIPLIER","1.0"],
        ["D_EXACT_UNIT_MULTIPLIER_FROZEN","1"],
        ["TARGET_K_D_VALUES_OPENED","0"],
        ["TRANSFORMED_TARGET_K_D_VALUES_COMPUTED","0"],
        ["E4C5B_FIRST_K_D_TRANSFORM_EXECUTION_PREFLIGHT_AUTHORIZED","1"],
    ])

log="\n".join([
"RAW_SCF_REFERENCE_SUMMARY_DATA_READ=1",
"REFERENCE_POPULATION_VALUE_OPENED=1",
"TARGET_NUMERIC_K_D_RESULT_TABLES_OPENED=0",
"TARGET_AGE_FIELD_ACCESSED=0",
"TARGET_TENURE_FIELD_ACCESSED=0",
"OWNER_RENTER_LABELS_USED_FOR_K_REF=0",
"TARGET_8_CELL_VALUES_USED_FOR_K_REF=0",
f"SCF_SUMMARY_ROWS_OPENED={rows_total}",
"SCF_EXPECTED_IMPLICATE_COUNT=5",
"K_REF_IMPLICATE_WEIGHTED_MEDIAN_COUNT=5",
f"K_REF_FIN_USD={k_ref:.12f}",
"K_REF_FIN_USD_VALUE_FROZEN=1",
"K_REF_FIN_USD_POSITIVE_FINITE=1",
"D_OFFICIAL_PIRTOTAL_RATIO_FORMULA_VALIDATED=1",
"D_OFFICIAL_PIR40_0P4_THRESHOLD_VALIDATED=1",
"D_PIRTOTAL_UNIT=FRACTION",
"D_EXACT_UNIT_MULTIPLIER=1.0",
"D_EXACT_UNIT_MULTIPLIER_FROZEN=1",
"K_TRANSFORM=LN1P_K_FIN_MEAN_OVER_K_REF_FIN_USD",
"D_TRANSFORM=NEGATIVE_PIRTOTAL_FRACTION",
"K_RECORD_LEVEL_ESTIMAND_REDEFINED=0",
"D_TARGET_SAMPLE_SCALE_PARAMETER=0",
"OWNER_RENTER_DIRECTION_USED_AS_PARAMETER_GATE=0",
"STATISTICAL_SIGNIFICANCE_USED_AS_PARAMETER_GATE=0",
"GEOMETRY_USED_AS_PARAMETER_GATE=0",
"TRANSFORMED_TARGET_K_D_VALUES_COMPUTED=0",
"CROSS_COORDINATE_METRIC_SCALE_FROZEN=0",
"GEOMETRY_READY=0",
"GEOMETRY_AUTHORIZED=0",
"DIMENSIONALITY_TEST_AUTHORIZED=0",
"REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
"FINAL_SCALAR_AUTHORIZED=0",
"E4C5A_K_REFERENCE_SCALE_D_UNIT_SEMANTICS=PASS",
"E4C5B_FIRST_K_D_TRANSFORM_EXECUTION_PREFLIGHT_AUTHORIZED=1",
])+"\n"

EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
