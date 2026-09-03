#!/usr/bin/env python3
from pathlib import Path
import argparse,csv,hashlib,json,math,re,sys

ROOT=Path(__file__).resolve().parents[1]

POINT=ROOT/"data/results/E4A2F_2022_scf_kd_cohort_inference.tsv"
REP=ROOT/"data/results/E4A2F_2022_scf_kd_replicate_statistics.tsv"
CONTRACT=ROOT/"data/metadata/E4C5C_first_k_d_transform_execution_contract.json"

HEADER_MANIFEST=ROOT/"data/metadata/E4C5C_source_header_manifest.tsv"
HEADER_EXEC=ROOT/"data/metadata/E4C5C_header_freeze_execution.txt"

EXEC=ROOT/"data/metadata/E4C5C_execution.txt"
AUDIT=ROOT/"data/metadata/E4C5C_first_k_d_transform_execution_audit.txt"
SELECT=ROOT/"data/metadata/E4C5C_target_source_selection.tsv"
POINTS=ROOT/"data/results/E4C5C_k_d_transformed_point_estimates.tsv"
REP_INV=ROOT/"data/results/E4C5C_primary_replicate_inventory.tsv"
HARD=ROOT/"data/results/E4C5C_execution_hard_gates.tsv"

POINT_SHA="4fc37f81af05b32f1769412fca327cb0cee0bc1610b33c6c77eeb5a04669b55c"
REP_SHA="d7a25d385cab8d3aee0701ca86af19c2525b35fc839d44a01198f5ee6f6d311e"
KREF=38640.0

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()

def norm_header(s):
    return re.sub(r"[^A-Z0-9]+","_",s.strip().upper()).strip("_")

def header_only(path):
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        line=f.readline()
        if not line:
            raise RuntimeError(f"empty source: {path}")
        # Strictly no second readline in header-only mode.
        hdr=next(csv.reader([line],delimiter="\t"))
    if not hdr or len(set(hdr))!=len(hdr):
        raise RuntimeError(f"invalid/duplicate header: {path}")
    return hdr

def resolve(headers,kind):
    nh={h:norm_header(h) for h in headers}

    age=[h for h,n in nh.items() if n in {"AGE_BAND","AGE_GROUP","AGEBAND","AGEGROUP"} or ("AGE" in n and ("BAND" in n or "GROUP" in n))]
    ten=[h for h,n in nh.items() if n=="TENURE" or "TENURE" in n]

    # R0 repair: role-aware raw-estimate precedence.
    # E4C5C applies orientation/transformation itself, so a pre-oriented point
    # estimate or sampling-replicate summary is not an admissible substitute.
    if kind=="POINT":
        priority=[
            {"POINT_ESTIMATE_RAW"},
            {"RAW_POINT_ESTIMATE","ESTIMATE_RAW"},
            {"POINT_ESTIMATE","ESTIMATE","THETA","MI_ESTIMATE","COMBINED_ESTIMATE","ESTIMATE_MI","VALUE"},
        ]
    else:
        priority=[
            {"RAW_VALUE"},
            {"REPLICATE_ESTIMATE_RAW"},
            {"REPLICATE_STATISTIC_RAW"},
            {"ESTIMATE_RAW"},
            {"STATISTIC_RAW"},
            {"POINT_ESTIMATE_RAW"},
            {"ESTIMATE","THETA","VALUE"},
        ]

    est=[]
    for names in priority:
        xs=[h for h,n in nh.items() if n in names]
        if len(xs)>1:
            raise RuntimeError(f"{kind}: ambiguous estimate priority group {sorted(names)}, candidates={xs}, headers={headers}")
        if len(xs)==1:
            est=xs
            break

    if not est:
        est=[
            h for h,n in nh.items()
            if (
                ("RAW" in n)
                and any(x in n for x in ["ESTIM","STATISTIC","THETA","MEAN"])
                and not any(x in n for x in [
                    "STATE_ORIENTED","ORIENTED","SAMPLING_REPLICATE_MEAN",
                    "SE","STD","VAR","CI","LOW","HIGH","LCL","UCL","DIFF","RATIO"
                ])
            )
        ]

    rep=[]
    if kind=="REPLICATE":
        rep=[h for h,n in nh.items() if n in {"REP","R","REPLICATE","REPLICATE_ID","REPLICATE_NUMBER","REPLICATE_INDEX"} or "REPLICATE_ID" in n or n.startswith("REPLICATE")]

    def one(xs,label):
        if len(xs)!=1:
            raise RuntimeError(f"{kind}: expected exactly one {label} column, candidates={xs}, headers={headers}")
        return xs[0]

    out={"age_col":one(age,"age"),"tenure_col":one(ten,"tenure"),"estimate_col":one(est,"estimate")}
    if kind=="REPLICATE":
        out["replicate_col"]=one(rep,"replicate-id")
    else:
        out["replicate_col"]="NA"
    return out

def map_age(x):
    s=str(x).strip().upper().replace("–","-").replace("—","-")
    nums=[int(v) for v in re.findall(r"\d+",s)]
    for lo,hi in [(25,34),(35,44),(45,54),(55,64)]:
        if lo in nums and hi in nums:
            return f"{lo}-{hi}"
    return None

def map_tenure(x):
    s=re.sub(r"[^A-Z]+","_",str(x).strip().upper()).strip("_")
    if s=="OWNER" or s.startswith("OWNER_") or s.endswith("_OWNER"):return "OWNER"
    if s=="RENTER" or s.startswith("RENTER_") or s.endswith("_RENTER"):return "RENTER"
    return None

def row_component(row,struct_cols):
    # R3 exact semantic repair frozen from E4C5C R2 categorical forensic.
    sid=norm_header(row.get("statistic_id",""))

    if "raw_variable" in row:
        dim=norm_header(row.get("dimension",""))
        role=norm_header(row.get("role",""))
        rawvar=norm_header(row.get("raw_variable",""))
        stat=norm_header(row.get("statistic",""))

        if sid=='K_FIN_MEAN' and dim=="K" and role=="PRIMARY" and rawvar=="FIN" and stat=="MEAN":
            return "K"
        if sid=='D_PIRTOTAL_MEAN' and dim=="D" and role=="PRIMARY" and rawvar=="PIRTOTAL" and stat=="MEAN":
            return "D"
        return None

    if sid=='K_FIN_MEAN':
        return "K"
    if sid=='D_PIRTOTAL_MEAN':
        return "D"
    return None

def finite_float(x):
    try:v=float(str(x).strip())
    except Exception:return None
    return v if math.isfinite(v) else None

def load_header_manifest():
    with HEADER_MANIFEST.open("r",encoding="utf-8",newline="") as f:
        rows=list(csv.DictReader(f,delimiter="\t"))
    if len(rows)!=2:
        raise RuntimeError("header manifest must have exactly two source rows")
    return {r["source_role"]:r for r in rows}

def execute():
    hm=load_header_manifest()
    if sha(POINT)!=POINT_SHA or sha(REP)!=REP_SHA:
        raise RuntimeError("source SHA drift")

    # Verify first lines and mappings still exactly match committed header manifest.
    for role,path in [("POINT",POINT),("REPLICATE",REP)]:
        hdr=header_only(path)
        r=hm[role]
        if "\x1f".join(hdr)!=r["header_us_joined"]:
            raise RuntimeError(f"{role}: header drift")
        m=resolve(hdr,role)
        for key in ["age_col","tenure_col","estimate_col","replicate_col"]:
            if m[key]!=r[key]:
                raise RuntimeError(f"{role}: mapping drift {key}")

    pm=hm["POINT"]
    struct={pm["age_col"],pm["tenure_col"],pm["estimate_col"]}
    point_rows=[]
    selected_source_rows=[]
    seen=set()
    scanned=0

    with POINT.open("r",encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f,delimiter="\t")
        for idx,row in enumerate(reader, start=2):
            scanned+=1
            comp=row_component(row,struct)
            if comp is None:continue
            age=map_age(row[pm["age_col"]]);ten=map_tenure(row[pm["tenure_col"]])
            if age is None or ten is None:continue
            raw=finite_float(row[pm["estimate_col"]])
            if raw is None:
                raise RuntimeError(f"nonfinite primary point estimate row {idx}")
            key=(comp,age,ten)
            if key in seen:
                raise RuntimeError(f"duplicate primary point cell: {key}")
            seen.add(key)
            if comp=="K":
                if raw<0:raise RuntimeError(f"K domain fail {key}: {raw}")
                transformed=math.log1p(raw/KREF)
                formula="LN1P_RAW_OVER_38640"
                raw_estimand="K_FIN_MEAN"
            else:
                transformed=-raw
                formula="NEGATIVE_PIRTOTAL_FRACTION"
                raw_estimand="D_PIRTOTAL_MEAN"
            if not math.isfinite(transformed):
                raise RuntimeError(f"nonfinite transformed value {key}")
            point_rows.append([comp,raw_estimand,age,ten,f"{raw:.12f}",formula,f"{transformed:.12f}","HIGHER_IS_BETTER"])
            selected_source_rows.append(["POINT",str(idx),comp,age,ten])

    expected={(c,a,t) for c in ["K","D"] for a in ["25-34","35-44","45-54","55-64"] for t in ["OWNER","RENTER"]}
    if seen!=expected:
        missing=sorted(expected-seen);extra=sorted(seen-expected)
        raise RuntimeError(f"primary point universe mismatch missing={missing} extra={extra}")

    # Replicate architecture inventory only. Numeric replicate estimates are parsed
    # for finiteness/domain audit but no transformed replicate value is emitted.
    rm=hm["REPLICATE"]
    rstruct={rm["age_col"],rm["tenure_col"],rm["estimate_col"],rm["replicate_col"]}
    rep_counts={"K":0,"D":0}
    rep_ids={"K":set(),"D":set()}
    rep_cells={"K":set(),"D":set()}
    rep_scanned=0
    rep_primary=0

    with REP.open("r",encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f,delimiter="\t")
        for idx,row in enumerate(reader,start=2):
            rep_scanned+=1
            comp=row_component(row,rstruct)
            if comp is None:continue
            age=map_age(row[rm["age_col"]]);ten=(norm_header(row[rm["tenure_col"]]) if norm_header(row[rm["tenure_col"]]) in {"OWNER","RENTER"} else None)
            if age is None or ten is None:continue
            value=finite_float(row[rm["estimate_col"]])
            if value is None:
                raise RuntimeError(f"nonfinite primary replicate estimate row {idx}")
            rid=str(row[rm["replicate_col"]]).strip()
            if rid=="":
                raise RuntimeError(f"blank replicate id row {idx}")
            rep_primary+=1
            rep_counts[comp]+=1
            rep_ids[comp].add(rid)
            rep_cells[comp].add((age,ten))
            selected_source_rows.append(["REPLICATE_INVENTORY",str(idx),comp,age,ten])

    for comp in ["K","D"]:
        if len(rep_cells[comp])!=8:
            raise RuntimeError(f"{comp} replicate inventory has {len(rep_cells[comp])} cells, expected 8")
        if rep_counts[comp]<=0 or len(rep_ids[comp])<=0:
            raise RuntimeError(f"{comp} empty primary replicate inventory")

    with POINTS.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,delimiter="\t",lineterminator="\n")
        w.writerow(["component","raw_estimand","age_band","tenure","raw_point_estimate","transform","state_value","orientation"])
        w.writerows(sorted(point_rows,key=lambda r:(r[0],r[2],r[3])))

    with SELECT.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,delimiter="\t",lineterminator="\n")
        w.writerow(["source_role","source_row_number","component","age_band","tenure"])
        w.writerows(selected_source_rows)

    with REP_INV.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,delimiter="\t",lineterminator="\n")
        w.writerow(["component","primary_replicate_row_count","distinct_primary_cells","distinct_replicate_ids","transformed_replicates_computed"])
        for comp in ["K","D"]:
            w.writerow([comp,rep_counts[comp],len(rep_cells[comp]),len(rep_ids[comp]),0])

    with HARD.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,delimiter="\t",lineterminator="\n")
        w.writerow(["gate","value"])
        w.writerows([
            ["PRIMARY_K_CELL_COUNT","8"],
            ["PRIMARY_D_CELL_COUNT","8"],
            ["TRANSFORMED_POINT_ROW_COUNT","16"],
            ["K_DOMAIN_PASS","1"],
            ["D_DOMAIN_PASS","1"],
            ["PRIMARY_REPLICATE_K_CELLS","8"],
            ["PRIMARY_REPLICATE_D_CELLS","8"],
            ["TRANSFORMED_REPLICATE_VALUES_COMPUTED","0"],
            ["TRANSFORMED_UNCERTAINTY_COMPUTED","0"],
            ["GEOMETRY_AUTHORIZED","0"],
        ])

    log="\n".join([
        "RAW_SCF_DATA_READ=0",
        "TARGET_RESULT_FILE_CONTENT_PARSED=1",
        "TARGET_NUMERIC_K_D_VALUES_OPENED=1",
        "SOURCE_HEADERS_FROZEN_BEFORE_TARGET_VALUE_OPEN=1",
        f"POINT_SOURCE_SHA256={POINT_SHA}",
        f"REPLICATE_SOURCE_SHA256={REP_SHA}",
        f"POINT_SOURCE_DATA_ROWS_SCANNED={scanned}",
        f"REPLICATE_SOURCE_DATA_ROWS_SCANNED={rep_scanned}",
        "PRIMARY_K_CELL_COUNT=8",
        "PRIMARY_D_CELL_COUNT=8",
        "TRANSFORMED_POINT_ROW_COUNT=16",
        "K_REF_FIN_USD=38640.000000000000",
        "K_TRANSFORM=LN1P_K_FIN_MEAN_OVER_38640",
        "D_PIRTOTAL_UNIT=FRACTION",
        "D_EXACT_UNIT_MULTIPLIER=1.0",
        "D_TRANSFORM=NEGATIVE_PIRTOTAL_FRACTION",
        "K_DOMAIN_PASS=1",
        "D_DOMAIN_PASS=1",
        f"PRIMARY_K_REPLICATE_ROW_COUNT={rep_counts['K']}",
        f"PRIMARY_D_REPLICATE_ROW_COUNT={rep_counts['D']}",
        f"PRIMARY_K_DISTINCT_REPLICATE_ID_COUNT={len(rep_ids['K'])}",
        f"PRIMARY_D_DISTINCT_REPLICATE_ID_COUNT={len(rep_ids['D'])}",
        "PRIMARY_K_REPLICATE_CELL_COUNT=8",
        "PRIMARY_D_REPLICATE_CELL_COUNT=8",
        "TRANSFORMED_REPLICATE_VALUES_COMPUTED=0",
        "TRANSFORMED_UNCERTAINTY_COMPUTED=0",
        "OWNER_RENTER_DIRECTION_USED_AS_TRANSFORM_GATE=0",
        "STATISTICAL_SIGNIFICANCE_USED_AS_TRANSFORM_GATE=0",
        "MAGNITUDE_USED_AS_TRANSFORM_GATE=0",
        "GEOMETRY_USED_AS_TRANSFORM_GATE=0",
        "CROSS_COORDINATE_METRIC_SCALE_FROZEN=0",
        "GEOMETRY_READY=0",
        "GEOMETRY_AUTHORIZED=0",
        "DIMENSIONALITY_TEST_AUTHORIZED=0",
        "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
        "FINAL_SCALAR_AUTHORIZED=0",
        "E4C5C_FIRST_K_D_TRANSFORM_EXECUTION=PASS",
        "E4C5D_K_D_REPLICATE_TRANSFORM_INFERENCE_PREFLIGHT_AUTHORIZED=1",
    ])+"\n"

    EXEC.write_text(log,encoding="utf-8")
    AUDIT.write_text(log,encoding="utf-8")
    print(log,end="")
    print("===== PRIMARY TRANSFORMED K/D POINT VALUES — NO OUTCOME GATE =====")
    for r in sorted(point_rows,key=lambda x:(x[0],x[2],x[3])):
        print(f"{r[0]} {r[2]} {r[3]} RAW={float(r[4]):.6f} STATE={float(r[6]):.6f}")

def do_header():
    if sha(POINT)!=POINT_SHA or sha(REP)!=REP_SHA:
        raise RuntimeError("source SHA drift before header freeze")

    rows=[]
    for role,path in [("POINT",POINT),("REPLICATE",REP)]:
        hdr=header_only(path)
        m=resolve(hdr,role)
        rows.append([
            role,str(path.relative_to(ROOT)),sha(path),
            "\x1f".join(hdr),str(len(hdr)),
            m["age_col"],m["tenure_col"],m["estimate_col"],m["replicate_col"]
        ])
        print(f"{role}_HEADER_COLUMN_COUNT={len(hdr)}")
        print(f"{role}_AGE_COL={m['age_col']}")
        print(f"{role}_TENURE_COL={m['tenure_col']}")
        print(f"{role}_ESTIMATE_COL={m['estimate_col']}")
        if role=="REPLICATE":print(f"{role}_ID_COL={m['replicate_col']}")

    with HEADER_MANIFEST.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,delimiter="\t",lineterminator="\n")
        w.writerow(["source_role","artifact","sha256","header_us_joined","header_column_count","age_col","tenure_col","estimate_col","replicate_col"])
        w.writerows(rows)

    text="\n".join([
        "SOURCE_FILE_FIRST_LINES_OPENED=1",
        "SOURCE_DATA_ROWS_OPENED=0",
        "TARGET_NUMERIC_K_D_VALUES_OPENED=0",
        "POINT_HEADER_MAPPING_RESOLVED=1",
        "REPLICATE_HEADER_MAPPING_RESOLVED=1",
        "HEADER_MANIFEST_FROZEN_BEFORE_TARGET_VALUE_OPEN=1",
        "E4C5C_HEADER_FREEZE=PASS",
    ])+"\n"
    HEADER_EXEC.write_text(text,encoding="utf-8")
    print(text,end="")

ap=argparse.ArgumentParser()
ap.add_argument("--mode",choices=["header","execute"],required=True)
args=ap.parse_args()

if args.mode=="header":do_header()
else:execute()
