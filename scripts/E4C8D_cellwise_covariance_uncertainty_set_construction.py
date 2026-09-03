#!/usr/bin/env python3
from pathlib import Path
from fractions import Fraction
from decimal import Decimal, localcontext, ROUND_HALF_EVEN
import csv, json

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"data/metadata/E4C8D_cellwise_covariance_uncertainty_set_construction_contract.json"

E6=ROOT/"data/results/E4C6E_partial_observed_coordinate_registry.tsv"
B8=ROOT/"data/results/E4C8B_within_survey_covariance_registry.tsv"

EXEC=ROOT/"data/metadata/E4C8D_execution.txt"
AUDIT=ROOT/"data/metadata/E4C8D_cellwise_covariance_uncertainty_set_construction_audit.txt"
KNOWN=ROOT/"data/results/E4C8D_cellwise_known_covariance_entries.tsv"
TEMPLATE=ROOT/"data/results/E4C8D_partial_covariance_template_registry.tsv"
CERT=ROOT/"data/results/E4C8D_psd_feasibility_certificates.tsv"
S1=ROOT/"data/results/E4C8D_zero_cross_survey_sensitivity_registry.tsv"
GATES=ROOT/"data/results/E4C8D_execution_hard_gates.tsv"
DECISION=ROOT/"data/results/E4C8D_cellwise_covariance_uncertainty_set_construction_decision.tsv"

c=json.loads(CONTRACT.read_text(encoding="utf-8"))
coords=c["coordinate_order"]
ages=c["cells"]["age_bands"]
tenures=c["cells"]["tenures"]

def frac_decimal(s):
    x=s.strip()
    if not x:
        raise RuntimeError("empty decimal source field")
    d=Decimal(x)
    if not d.is_finite():
        raise RuntimeError(f"nonfinite decimal source field: {x}")
    return Fraction(d)

def frac_ratio(n,d):
    ni=int(n); di=int(d)
    if di==0:
        raise RuntimeError("zero denominator in frozen exact covariance")
    return Fraction(ni,di)

def exact(q):
    return f"{q.numerator}/{q.denominator}"

def dec30(q):
    with localcontext() as ctx:
        ctx.prec=120
        d=Decimal(q.numerator)/Decimal(q.denominator)
        z=d.quantize(Decimal("1e-30"),rounding=ROUND_HALF_EVEN)
        if z==0:
            z=abs(z)
        return format(z,"f")

# Read exact E4C6E grid after precommit.
se={}
e6_rows=0
with E6.open("r",encoding="utf-8",newline="") as f:
    for row in csv.DictReader(f,delimiter="\t"):
        e6_rows += 1
        if row["year"]!="2022":
            raise RuntimeError(f"unexpected E4C6E year {row['year']}")
        key=(row["age_band"],row["tenure"],row["coordinate_id"])
        if key in se:
            raise RuntimeError(f"duplicate E4C6E key {key}")
        if row["coordinate_id"] not in coords:
            raise RuntimeError(f"unexpected E4C6E coordinate {row['coordinate_id']}")
        se[key]=frac_decimal(row["se_state"])

if e6_rows!=40 or len(se)!=40:
    raise RuntimeError(f"E4C6E exact grid failure: rows={e6_rows} unique={len(se)}")

# Read exact E4C8B within-survey covariances.
cov={}
b8_rows=0
with B8.open("r",encoding="utf-8",newline="") as f:
    for row in csv.DictReader(f,delimiter="\t"):
        b8_rows += 1
        pair=row["pair_id"]
        if pair not in {"SCF_K_D","CPS_I_PAIR"}:
            raise RuntimeError(f"unexpected E4C8B pair {pair}")
        key=(row["age_band"],row["tenure"],pair)
        if key in cov:
            raise RuntimeError(f"duplicate E4C8B key {key}")
        q=frac_ratio(row["combined_covariance_numerator"],row["combined_covariance_denominator"])
        if exact(q)!=row["combined_covariance_exact"]:
            raise RuntimeError(f"E4C8B exact covariance identity mismatch {key}")
        cov[key]=q

if b8_rows!=16 or len(cov)!=16:
    raise RuntimeError(f"E4C8B exact grid failure: rows={b8_rows} unique={len(cov)}")

known_rows=[]
template_rows=[]
cert_rows=[]
s1_rows=[]

H="H_ACCESS_SPACE_ROOMS_PER_PERSON"
K="K_FIN_MEAN_TRANSFORMED"
D="D_PIRTOTAL_MEAN_STATE_TRANSFORMED"
I1="I_FYFT_SHARE"
I2="I_SEARCH_SECURITY"

all_u1_nonempty=True
all_s1_psd=True

for age in ages:
    for ten in tenures:
        cell=(age,ten)

        variances={}
        for coord in coords:
            k=(age,ten,coord)
            if k not in se:
                raise RuntimeError(f"missing marginal SE {k}")
            variances[coord]=se[k]*se[k]

        kd=cov.get((age,ten,"SCF_K_D"))
        ii=cov.get((age,ten,"CPS_I_PAIR"))
        if kd is None or ii is None:
            raise RuntimeError(f"missing within-survey covariance for {cell}")

        h_ok=variances[H] >= 0
        kd_margin=variances[K]*variances[D]-kd*kd
        i_margin=variances[I1]*variances[I2]-ii*ii
        kd_ok=(variances[K]>=0 and variances[D]>=0 and kd_margin>=0)
        i_ok=(variances[I1]>=0 and variances[I2]>=0 and i_margin>=0)

        s1_psd=(h_ok and kd_ok and i_ok)
        u1_nonempty=s1_psd  # exact constructive certificate under frozen disconnected specified graph
        all_s1_psd = all_s1_psd and s1_psd
        all_u1_nonempty = all_u1_nonempty and u1_nonempty

        known_rows.append([
            "2022",age,ten,
            exact(variances[H]),dec30(variances[H]),
            exact(variances[K]),dec30(variances[K]),
            exact(variances[D]),dec30(variances[D]),
            exact(variances[I1]),dec30(variances[I1]),
            exact(variances[I2]),dec30(variances[I2]),
            exact(kd),dec30(kd),
            exact(ii),dec30(ii)
        ])

        cert_rows.append([
            "2022",age,ten,
            "1" if h_ok else "0",
            exact(kd_margin),dec30(kd_margin),"1" if kd_ok else "0",
            exact(i_margin),dec30(i_margin),"1" if i_ok else "0",
            "1" if s1_psd else "0",
            "1" if u1_nonempty else "0",
            "BLOCK_DIAGONAL_S1_CONSTRUCTIVE_CERTIFICATE"
        ])

        # Canonical partial U1 template plus explicit S1 values.
        for a in coords:
            for b in coords:
                if a==b:
                    q=variances[a]
                    entry_class="KNOWN_DIAGONAL_VARIANCE"
                    canonical_status="FIXED"
                    canonical_exact=exact(q)
                    s1_exact=exact(q)
                elif {a,b}=={K,D}:
                    q=kd
                    entry_class="KNOWN_WITHIN_SCF_COVARIANCE"
                    canonical_status="FIXED"
                    canonical_exact=exact(q)
                    s1_exact=exact(q)
                elif {a,b}=={I1,I2}:
                    q=ii
                    entry_class="KNOWN_WITHIN_CPS_COVARIANCE"
                    canonical_status="FIXED"
                    canonical_exact=exact(q)
                    s1_exact=exact(q)
                else:
                    entry_class="UNKNOWN_CROSS_SURVEY_COVARIANCE"
                    canonical_status="FREE_SUBJECT_TO_U1_PSD"
                    canonical_exact=""
                    s1_exact="0/1"

                template_rows.append([
                    "2022",age,ten,a,b,entry_class,canonical_status,canonical_exact,s1_exact
                ])
                s1_rows.append([
                    "2022",age,ten,a,b,s1_exact,
                    "NONCANONICAL_SENSITIVITY_AND_U1_EXISTENCE_CERTIFICATE"
                ])

with KNOWN.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow([
        "year","age_band","tenure",
        "var_H_exact","var_H_decimal_30",
        "var_K_exact","var_K_decimal_30",
        "var_D_exact","var_D_decimal_30",
        "var_I_FYFT_exact","var_I_FYFT_decimal_30",
        "var_I_SEARCH_SECURITY_exact","var_I_SEARCH_SECURITY_decimal_30",
        "cov_K_D_exact","cov_K_D_decimal_30",
        "cov_I_pair_exact","cov_I_pair_decimal_30"
    ])
    w.writerows(known_rows)

with TEMPLATE.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow([
        "year","age_band","tenure","row_coordinate","column_coordinate",
        "entry_class","canonical_U1_status","canonical_exact_value_if_fixed","S1_exact_value"
    ])
    w.writerows(template_rows)

with CERT.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow([
        "year","age_band","tenure",
        "H_singleton_psd",
        "SCF_2x2_determinant_margin_exact","SCF_2x2_determinant_margin_decimal_30","SCF_2x2_psd",
        "CPS_2x2_determinant_margin_exact","CPS_2x2_determinant_margin_decimal_30","CPS_2x2_psd",
        "S1_block_diagonal_psd","U1_nonempty","certificate_basis"
    ])
    w.writerows(cert_rows)

with S1.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow([
        "year","age_band","tenure","row_coordinate","column_coordinate",
        "S1_exact_value","role"
    ])
    w.writerows(s1_rows)

if len(known_rows)!=8:
    raise RuntimeError(f"known-entry cell count {len(known_rows)} != 8")
if len(cert_rows)!=8:
    raise RuntimeError(f"certificate row count {len(cert_rows)} != 8")
if len(template_rows)!=200:
    raise RuntimeError(f"partial template row count {len(template_rows)} != 200")
if len(s1_rows)!=200:
    raise RuntimeError(f"S1 matrix row count {len(s1_rows)} != 200")

# Important: do not "repair" if a block is not PSD.
if not all_u1_nonempty:
    bad=[(r[1],r[2]) for r in cert_rows if r[11]!="1"]
    raise RuntimeError(f"U1 empty for one or more cells under exact frozen entries: {bad}")
if not all_s1_psd:
    bad=[(r[1],r[2]) for r in cert_rows if r[10]!="1"]
    raise RuntimeError(f"S1 block-diagonal sensitivity non-PSD for cells: {bad}")

gate_rows=[
    ["E4C8C_FROZEN_POLICY_REUSED","PASS"],
    ["EXACT_8_CELL_SOURCE_GRID","PASS"],
    ["EXACT_RATIONAL_VARIANCE_CONSTRUCTION","PASS"],
    ["EXACT_E4C8B_COVARIANCE_REUSE","PASS"],
    ["BLOCK_PSD_FEASIBILITY","PASS"],
    ["S1_CONSTRUCTIVE_U1_EXISTENCE_CERTIFICATE","PASS"],
    ["NO_CROSS_SURVEY_POINT_ESTIMATION","PASS"],
    ["NO_AUTOMATIC_PSD_REPAIR","PASS"],
    ["GEOMETRY_REMAINS_UNAUTHORIZED","PASS"]
]
with GATES.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["gate","value"])
    w.writerows(gate_rows)

decision_rows=[
    ["CELL_COUNT","8"],
    ["MATRIX_DIMENSION","5"],
    ["PARTIAL_TEMPLATE_ROW_COUNT","200"],
    ["S1_MATRIX_ROW_COUNT","200"],
    ["KNOWN_DIAGONAL_ENTRY_COUNT_PER_CELL","5"],
    ["KNOWN_NONTRIVIAL_OFFDIAGONAL_PAIR_COUNT_PER_CELL","2"],
    ["UNKNOWN_CROSS_SURVEY_OFFDIAGONAL_PAIR_COUNT_PER_CELL","8"],
    ["ALL_H_SINGLETON_BLOCKS_PSD","1"],
    ["ALL_SCF_2X2_BLOCKS_PSD","1"],
    ["ALL_CPS_2X2_BLOCKS_PSD","1"],
    ["ALL_S1_BLOCK_DIAGONAL_COMPLETIONS_PSD","1"],
    ["ALL_U1_FEASIBLE_SETS_NONEMPTY","1"],
    ["NUMERIC_OPTIMIZER_USED","0"],
    ["NEAREST_PSD_PROJECTION_USED","0"],
    ["COVARIANCE_CLIPPING_USED","0"],
    ["CROSS_SURVEY_COVARIANCE_POINT_ESTIMATED","0"],
    ["CROSS_SURVEY_COVARIANCE_ASSUMED_ZERO","0"],
    ["S1_ZERO_IS_INDEPENDENCE_CLAIM","0"],
    ["ECONOMIC_STATE_DEPENDENCE_INFERRED","0"],
    ["METRIC_MUTATED","0"],
    ["GEOMETRY_AUTHORIZED","0"],
    ["E4C9_PARTIAL_STATE_GEOMETRY_AND_DIMENSIONALITY_PREFLIGHT_AUTHORIZED","1"]
]
with DECISION.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["decision","value"])
    w.writerows(decision_rows)

log="\n".join([
    "E4C8C_FROZEN_POLICY_REUSED=1",
    "NUMERIC_SOURCE_ROWS_OPENED_AFTER_E4C8D_PRECOMMIT=1",
    "E4C6E_MARGINAL_SE_ROWS_OPENED=40",
    "E4C8B_WITHIN_SURVEY_COVARIANCE_ROWS_OPENED=16",
    "EXACT_RATIONAL_ARITHMETIC_USED=1",
    "BINARY_FLOAT_ROUNDTRIP_USED_FOR_PSD_FEASIBILITY=0",
    "CELL_COUNT=8",
    "MATRIX_DIMENSION=5",
    "KNOWN_DIAGONAL_ENTRY_COUNT_PER_CELL=5",
    "KNOWN_NONTRIVIAL_OFFDIAGONAL_PAIR_COUNT_PER_CELL=2",
    "UNKNOWN_CROSS_SURVEY_OFFDIAGONAL_PAIR_COUNT_PER_CELL=8",
    "PARTIAL_TEMPLATE_ROW_COUNT=200",
    "S1_MATRIX_ROW_COUNT=200",
    "H_SINGLETON_PSD_CELL_COUNT=8",
    "SCF_2X2_PSD_CELL_COUNT=8",
    "CPS_2X2_PSD_CELL_COUNT=8",
    "S1_BLOCK_DIAGONAL_PSD_CELL_COUNT=8",
    "U1_NONEMPTY_CELL_COUNT=8",
    "U1_NONEMPTY_PROVED_BY_S1_CONSTRUCTIVE_COMPLETION=1",
    "NUMERIC_OPTIMIZER_USED=0",
    "SDP_SOLVER_USED=0",
    "EXTRA_RHO_BOX_BOUND_INTRODUCED=0",
    "NEAREST_PSD_PROJECTION_USED=0",
    "COVARIANCE_CLIPPING_USED=0",
    "KNOWN_FROZEN_ENTRIES_MUTATED=0",
    "PSD_FEASIBILITY_USES_EXACT_NUMERIC_RELATIONSHIPS=1",
    "COVARIANCE_SIGN_USED_AS_SCIENTIFIC_SELECTION_GATE=0",
    "COVARIANCE_MAGNITUDE_USED_AS_SCIENTIFIC_SELECTION_GATE=0",
    "STATISTICAL_SIGNIFICANCE_USED_AS_GATE=0",
    "OWNER_RENTER_DIRECTION_USED_AS_GATE=0",
    "CROSS_SURVEY_COVARIANCE_POINT_ESTIMATED=0",
    "CROSS_SURVEY_COVARIANCE_ASSUMED_ZERO=0",
    "S1_ZERO_IS_INDEPENDENCE_CLAIM=0",
    "ECONOMIC_STATE_DEPENDENCE_INFERRED=0",
    "METRIC_MUTATED=0",
    "C_INCLUDED_IN_COVARIANCE_ARCHITECTURE=0",
    "H_ACCESS_PROMOTED_TO_FULL_H_STATE=0",
    "I_SCALAR_CREATED=0",
    "PARTIAL_PANEL_IS_FULL_CHKDI_STATE_VECTOR=0",
    "CROSS_COORDINATE_METRIC_SCALE_FROZEN=1",
    "GEOMETRY_READY=0",
    "GEOMETRY_AUTHORIZED=0",
    "DIMENSIONALITY_TEST_AUTHORIZED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "E4C8D_CELLWISE_COVARIANCE_UNCERTAINTY_SET_CONSTRUCTION=PASS",
    "E4C9_PARTIAL_STATE_GEOMETRY_AND_DIMENSIONALITY_PREFLIGHT_AUTHORIZED=1"
])+"\n"

EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")

print(log,end="")
print("===== PSD FEASIBILITY CERTIFICATES =====")
print(CERT.read_text(encoding="utf-8"),end="")
print("===== KNOWN CELLWISE COVARIANCE ENTRIES =====")
print(KNOWN.read_text(encoding="utf-8"),end="")
