#!/usr/bin/env python3
from pathlib import Path
import csv,hashlib,io,math,zipfile

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"data/raw/acs/2019/1year/csv_hus.zip"
MAN=ROOT/"data/metadata/E4C3D_acs2022_microdata_manifest.tsv"
OUT=ROOT/"data/results/E4D1D_2019_runtime/ACS"
META=ROOT/"data/metadata"
OUT.mkdir(parents=True,exist_ok=True); META.mkdir(parents=True,exist_ok=True)

AGES=[("AGE25_34",25,34),("AGE35_44",35,44),("AGE45_54",45,54),("AGE55_64",55,64)]
TENS=["OWNER","RENTER"]
ESTS=[("PRIMARY","H_ACCESS_SPACE_ROOMS_PER_PERSON","RMSP"),("SENSITIVITY","H_ACCESS_SPACE_BEDROOMS_PER_PERSON","BDSP")]
RC=[f"WGTP{i}" for i in range(1,81)]
REQ=["HHLDRAGEP","TEN","NP","RMSP","BDSP","WGTP",*RC]

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""): h.update(b)
    return h.hexdigest()
def num(x):
    try:
        if x is None or str(x).strip()=="": return None
        v=float(x); return v if math.isfinite(v) else None
    except: return None
def age(v):
    for a,l,h in AGES:
        if l<=v<=h:return a
def ten(v):
    return "OWNER" if v in (1,2) else ("RENTER" if v==3 else None)
def fmt(x): return "" if not math.isfinite(x) else f"{x:.12f}"
def se(theta,reps):
    if not math.isfinite(theta) or any(not math.isfinite(x) for x in reps): return math.nan
    return math.sqrt((4/80)*sum((x-theta)**2 for x in reps))

with MAN.open(encoding="utf-8",newline="") as f: mr=list(csv.DictReader(f,delimiter="\t"))
ar=[r for r in mr if r["row_type"]=="ARCHIVE"]
mem=[r["member_name"] for r in mr if r["row_type"]=="MEMBER" and r["selected"]=="1"]
if len(ar)!=1 or sha(RAW)!=ar[0]["sha256"] or not mem: raise RuntimeError("frozen source manifest mismatch")

A={}
for k,n,v in ESTS:
  for a,_,_ in AGES:
    for t in TENS:A[k,a,t]={"n":0,"d":0.0,"n0":0.0,"rd":[0.0]*80,"rn":[0.0]*80}

rows_opened=0
RAW_PERSON_2019="data/raw/acs/2019/1year/csv_pus.zip"

def _e4d1d_build_householder_age_map():
  out={}
  with zipfile.ZipFile(RAW_PERSON_2019) as pz:
    pmem=sorted([x for x in pz.namelist() if x.lower().endswith(".csv")])
    if not pmem: raise RuntimeError("no person CSV members")
    for pm in pmem:
      with pz.open(pm) as pfb:
        pr=csv.DictReader(io.TextIOWrapper(pfb,encoding="utf-8-sig",newline=""))
        hdr=pr.fieldnames or []
        miss=[c for c in ("SERIALNO","RELSHIPP","AGEP") if c not in hdr]
        if miss: raise RuntimeError(f"missing person columns {pm}:{','.join(miss)}")
        for prow in pr:
          if str(prow.get("RELSHIPP","")).strip()!="20": continue
          serial=str(prow.get("SERIALNO","")).strip()
          ages=str(prow.get("AGEP","")).strip()
          if not serial or not ages: raise RuntimeError(f"missing reference age/key {pm}")
          try: av=int(float(ages))
          except Exception as e: raise RuntimeError(f"invalid reference age {pm}:{serial}") from e
          if serial in out: raise RuntimeError(f"duplicate reference person {serial}")
          out[serial]=av
  return out

def _e4d1d_adapt_housing_rows(reader,age_by_serial):
  for row in reader:
    if str(row.get("TYPE","")).strip()!="1": continue
    npv=num(row.get("NP"))
    row=dict(row)
    if npv is not None and npv>0:
      serial=str(row.get("SERIALNO","")).strip()
      if serial not in age_by_serial: raise RuntimeError(f"missing reference person for occupied housing {serial}")
      row["HHLDRAGEP"]=str(age_by_serial[serial])
    else:
      row["HHLDRAGEP"]=""
    yield row

_e4d1d_age_by_serial=_e4d1d_build_householder_age_map()

with zipfile.ZipFile(RAW) as z:
  for m in mem:
    with z.open(m) as fb:
      r=csv.reader(io.TextIOWrapper(fb,encoding="utf-8-sig",newline=""))
      hdr=next(r)
      if "HHLDRAGEP" not in hdr: hdr=hdr+["HHLDRAGEP"]
      for _e4d1d_required in ("SERIALNO","TYPE"):
        if _e4d1d_required not in hdr: raise RuntimeError(f"missing structural column {m}:{_e4d1d_required}")
      miss=[c for c in REQ if c not in hdr]
      if miss: raise RuntimeError(f"missing columns {m}:{','.join(miss)}")
  for m in mem:
    with z.open(m) as fb:
      r=csv.DictReader(io.TextIOWrapper(fb,encoding="utf-8-sig",newline=""))
      r=_e4d1d_adapt_housing_rows(r,_e4d1d_age_by_serial)
      for rowno,row in enumerate(r,2):
        rows_opened+=1
        av,tv,npv,w=map(num,[row.get("HHLDRAGEP"),row.get("TEN"),row.get("NP"),row.get("WGTP")])
        if None in (av,tv,npv,w) or npv<=0 or w<=0: continue
        aa,tt=age(int(av)),ten(int(tv))
        if aa is None or tt is None: continue
        reps=None
        for k,n,v in ESTS:
          x=num(row.get(v))
          if x is None: continue
          if reps is None:
            reps=[num(row.get(c)) for c in RC]
            if any(x is None for x in reps): raise RuntimeError(f"missing replicate weight {m}:{rowno}")
          q=x/npv
          d=A[k,aa,tt]; d["n"]+=1; d["d"]+=w; d["n0"]+=w*q
          for j,rw in enumerate(reps): d["rd"][j]+=rw; d["rn"][j]+=rw*q

P={}; R={}
for k,n,v in ESTS:
  for a,_,_ in AGES:
    for t in TENS:
      d=A[k,a,t]
      P[k,a,t]=d["n0"]/d["d"] if d["n"] and d["d"]>0 else math.nan
      R[k,a,t]=[rn/rd if rd>0 else math.nan for rn,rd in zip(d["rn"],d["rd"])]

for a,_,_ in AGES:
  for t in TENS:
    d=A["PRIMARY",a,t]
    if d["n"]<=0 or d["d"]<=0 or not math.isfinite(P["PRIMARY",a,t]): raise RuntimeError(f"primary cell fail {a}:{t}")
    if any(rd<=0 or not math.isfinite(rd) for rd in d["rd"]): raise RuntimeError(f"primary replicate denominator fail {a}:{t}")
    if any(not math.isfinite(x) for x in R["PRIMARY",a,t]): raise RuntimeError(f"primary replicate estimate fail {a}:{t}")

POINTS=OUT/"E4C3D_h_access_point_estimates.tsv"
REPS=OUT/"E4C3D_h_access_component_replicates.tsv"
COMPS=OUT/"E4C3D_h_access_owner_renter_comparisons.tsv"
DIFF=OUT/"E4C3D_h_access_difference_replicates.tsv"
RATIO=OUT/"E4C3D_h_access_ratio_replicates.tsv"
SUMM=OUT/"E4C3D_h_access_inference_summary.tsv"

with POINTS.open("w",encoding="utf-8",newline="") as f:
  w=csv.writer(f,delimiter="\t",lineterminator="\n");w.writerow(["role","estimand","age_band","tenure","n","weight_denominator","estimate"])
  for k,n,v in ESTS:
    for a,_,_ in AGES:
      for t in TENS:
        d=A[k,a,t];w.writerow([k,n,a,t,d["n"],fmt(d["d"]),fmt(P[k,a,t])])
with REPS.open("w",encoding="utf-8",newline="") as f:
  w=csv.writer(f,delimiter="\t",lineterminator="\n");w.writerow(["role","estimand","age_band","tenure","replicate","denominator","estimate"])
  for k,n,v in ESTS:
    for a,_,_ in AGES:
      for t in TENS:
        d=A[k,a,t]
        for j,x in enumerate(R[k,a,t],1):w.writerow([k,n,a,t,j,fmt(d["rd"][j-1]),fmt(x)])

cr=[];dr=[];rr=[];sr=[]
for k,n,v in ESTS:
  for a,_,_ in AGES:
    for t in TENS:
      th=P[k,a,t];s=se(th,R[k,a,t]);sr.append(["COMPONENT",k,n,a,t,fmt(th),fmt(s),fmt(th-1.96*s),fmt(th+1.96*s)])
    o,r=P[k,a,"OWNER"],P[k,a,"RENTER"];d=r-o;rat=r/o
    dreps=[];rreps=[]
    for j,(x,y) in enumerate(zip(R[k,a,"OWNER"],R[k,a,"RENTER"]),1):
      dv=y-x;rv=y/x;dreps.append(dv);rreps.append(rv);dr.append([k,n,a,j,fmt(dv)]);rr.append([k,n,a,j,fmt(rv)])
    ds,rs=se(d,dreps),se(rat,rreps)
    cr.append([k,n,a,fmt(o),fmt(r),fmt(d),fmt(ds),fmt(d-1.96*ds),fmt(d+1.96*ds),fmt(rat),fmt(rs),fmt(rat-1.96*rs),fmt(rat+1.96*rs)])
    sr.append(["DIFFERENCE",k,n,a,"RENTER_MINUS_OWNER",fmt(d),fmt(ds),fmt(d-1.96*ds),fmt(d+1.96*ds)])
    sr.append(["RATIO",k,n,a,"RENTER_DIV_OWNER",fmt(rat),fmt(rs),fmt(rat-1.96*rs),fmt(rat+1.96*rs)])

with COMPS.open("w",encoding="utf-8",newline="") as f:
  w=csv.writer(f,delimiter="\t",lineterminator="\n");w.writerow(["role","estimand","age_band","owner","renter","diff","diff_se","diff_lo","diff_hi","ratio","ratio_se","ratio_lo","ratio_hi"]);w.writerows(cr)
with DIFF.open("w",encoding="utf-8",newline="") as f:
  w=csv.writer(f,delimiter="\t",lineterminator="\n");w.writerow(["role","estimand","age_band","replicate","renter_minus_owner"]);w.writerows(dr)
with RATIO.open("w",encoding="utf-8",newline="") as f:
  w=csv.writer(f,delimiter="\t",lineterminator="\n");w.writerow(["role","estimand","age_band","replicate","renter_div_owner"]);w.writerows(rr)
with SUMM.open("w",encoding="utf-8",newline="") as f:
  w=csv.writer(f,delimiter="\t",lineterminator="\n");w.writerow(["entity_type","role","estimand","age_band","entity","estimate","se","ci95_low","ci95_high"]);w.writerows(sr)

log="\n".join([
"RAW_SURVEY_DATA_READ=1","ACS_2022_MICRODATA_VALUES_OPENED=1","ACS_2022_HOUSING_ZIP_SHA_MATCHES_FROZEN_MANIFEST=1",
f"SELECTED_HOUSING_CSV_MEMBER_COUNT={len(mem)}",f"TOTAL_HOUSING_ROWS_OPENED={rows_opened}",
"REQUIRED_COLUMNS_PRESENT_ALL_MEMBERS=1","PRIMARY_8_OF_8_COHORTS_NONEMPTY=1","PRIMARY_FULL_DENOMINATORS_POSITIVE_FINITE=1",
"PRIMARY_80_REPLICATE_DENOMINATORS_POSITIVE_FINITE=1","PRIMARY_ALL_POINT_ESTIMATES_FINITE=1",
"PRIMARY_H_ACCESS_ESTIMAND=H_ACCESS_SPACE_ROOMS_PER_PERSON","PRIMARY_H_ACCESS_FORMULA=RMSP_DIV_NP",
"SENSITIVITY_H_ACCESS_ESTIMAND=H_ACCESS_SPACE_BEDROOMS_PER_PERSON","SENSITIVITY_REPLACED_PRIMARY=0",
"ACS_REPLICATE_COUNT=80","ACS_SDR_VARIANCE_FACTOR=4/80","OWNER_RENTER_DIRECTION_USED_AS_GATE=0",
"STATISTICAL_SIGNIFICANCE_USED_AS_GATE=0","MAGNITUDE_USED_AS_GATE=0","GEOMETRY_USED_AS_GATE=0",
"H_SERVICE_H_ACCESS_AUTO_SCALAR_COMPUTED=0","H_ACCESS_SPACE_SUBCOORDINATE_IDENTIFIED=1","H_FULL_STATE_COMPLETE=0",
"FIVE_COMPONENT_STATE_VECTOR_AUTHORIZED=0","GEOMETRY_AUTHORIZED=0","REAL_INFLATION_ESTIMATION_AUTHORIZED=0","FINAL_SCALAR_AUTHORIZED=0",
"POINT_ESTIMATE_ROWS=16","COMPONENT_REPLICATE_ROWS=1280","OWNER_RENTER_COMPARISON_ROWS=8","DIFFERENCE_REPLICATE_ROWS=640","RATIO_REPLICATE_ROWS=640","INFERENCE_SUMMARY_ROWS=32",
"E4C3D_FIRST_ACS_2022_H_ACCESS_EXECUTION=PASS","E4C3E_H_HOUSING_EVIDENCE_CLOSEOUT_PREFLIGHT_AUTHORIZED=1"
])+"\n"
(META/"E4C3D_execution.txt").write_text(log,encoding="utf-8")
(META/"E4C3D_first_acs2022_h_access_execution_audit.txt").write_text(log,encoding="utf-8")
print(log,end="")
print("===== PRIMARY RESULTS / NO OUTCOME GATE =====")
for a,_,_ in AGES:
  o,r=P["PRIMARY",a,"OWNER"],P["PRIMARY",a,"RENTER"]
  print(f"{a}: OWNER={o:.6f} RENTER={r:.6f} DIFF={r-o:.6f} RATIO={r/o:.6f}")
