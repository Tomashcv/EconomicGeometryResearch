#!/usr/bin/env python3
from pathlib import Path
from html.parser import HTMLParser
import csv, hashlib, json, re

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"data/metadata/E4C3B_acs2022_metadata_harmonization_contract.json"
LINEAGE=ROOT/"data/metadata/E4C3B_frozen_input_lineage.tsv"
MANIFEST=ROOT/"data/metadata/E4C3B_official_metadata_manifest.tsv"
DICT=ROOT/"data/raw/reference_metadata/E4C3B/PUMS_Data_Dictionary_2022.txt"
GROSS=ROOT/"data/raw/reference_metadata/E4C3B/census_glossary_gross_rent.html"
OWNER=ROOT/"data/raw/reference_metadata/E4C3B/census_glossary_selected_monthly_owner_costs.html"
GUIDE=ROOT/"data/raw/reference_metadata/E4C3B/2018_2022ACS_PUMS_User_Guide.pdf"

EXEC=ROOT/"data/metadata/E4C3B_execution.txt"
AUDIT=ROOT/"data/metadata/E4C3B_acs2022_metadata_harmonization_audit.txt"
CODES=ROOT/"data/results/E4C3B_acs2022_exact_code_universe.tsv"
ARCH=ROOT/"data/results/E4C3B_h_access_architecture_decision.tsv"
BLOCKERS=ROOT/"data/results/E4C3B_h_access_post_harmonization_blockers.tsv"

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""):
            h.update(c)
    return h.hexdigest()

def read_tsv(p):
    with p.open("r",encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f,delimiter="\t"))

class H(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts=[]
    def handle_data(self,d): self.parts.append(d)

def html_text(p):
    h=H(); h.feed(p.read_text(encoding="utf-8",errors="replace"))
    return re.sub(r"\s+"," "," ".join(h.parts)).casefold()

c=json.loads(CONTRACT.read_text(encoding="utf-8"))
if c["phase"]!="E4C3B": raise RuntimeError("wrong phase")
if c["hard_boundaries"]["microdata_values_opened"]: raise RuntimeError("microdata forbidden")
if c["primary_H_ACCESS_architecture"]["selection_status"]!="SELECTED_BEFORE_MICRODATA_VALUES":
    raise RuntimeError("architecture selection timing invalid")

for r in read_tsv(LINEAGE):
    p=ROOT/r["artifact"]
    if not p.exists() or sha(p)!=r["sha256"]:
        raise RuntimeError(f"frozen lineage mismatch: {r['artifact']}")

for r in read_tsv(MANIFEST):
    p=ROOT/r["artifact"]
    if not p.exists() or sha(p)!=r["sha256"]:
        raise RuntimeError(f"official metadata hash mismatch: {r['artifact']}")

d=DICT.read_text(encoding="utf-8",errors="strict")
required_dict_fragments=[
    "HHLDRAGEP   Numeric     2",
    "Age of the householder",
    "15..99 .15 to 99 years (Top-coded)",
    "TEN         Character   1",
    "1    .Owned with mortgage or loan (include home equity loans)",
    "2    .Owned free and clear",
    "3    .Rented",
    "4    .Occupied without payment of rent",
    "NP          Numeric     2",
    "Number of persons in this household",
    "RMSP        Numeric     2",
    "Number of rooms",
    "BDSP        Numeric     2",
    "Number of bedrooms",
    "GRPIP       Numeric     3",
    "Gross rent as a percentage of household income past 12 months",
    "OCPIP       Numeric     3",
    "Selected monthly owner costs as a percentage of household income during the past 12 months",
    "PLM         Character   1",
    "Complete plumbing facilities",
    "KIT         Character   1",
    "Complete kitchen facilities",
    "WGTP        Numeric     5",
    "Housing Unit Weight",
    "WGTP1       Numeric     5",
    "Housing Weight replicate 1",
    "WGTP80      Numeric     5",
    "Housing Weight replicate 80",
]
for x in required_dict_fragments:
    if x not in d:
        raise RuntimeError(f"dictionary semantic fragment absent: {x}")

g=html_text(GROSS)
o=html_text(OWNER)

for x in [
    "contract rent plus the estimated average monthly cost of utilities",
    "gross rent is intended to eliminate differentials",
]:
    if x not in g:
        raise RuntimeError(f"gross-rent semantic fragment absent: {x}")

for group in [
    ("mortgages", "mortgage"),
    ("real estate taxes",),
    ("insurance",),
    ("utilities",),
]:
    if not any(x in o for x in group):
        raise RuntimeError(f"owner-cost semantic fragment absent: {group}")

if not GUIDE.read_bytes().startswith(b"%PDF"):
    raise RuntimeError("ACS PUMS user guide is not a PDF")

code_rows=[
("HHLDRAGEP","15..99","AGE_OF_HOUSEHOLDER","age bands 25-34,35-44,45-54,55-64"),
("TEN","1","OWNER","owned with mortgage or loan"),
("TEN","2","OWNER","owned free and clear"),
("TEN","3","RENTER","rented"),
("TEN","4","EXCLUDED_PRIMARY","occupied without payment of rent"),
("NP","1..20","H_ACCESS_DENOMINATOR","positive household persons"),
("RMSP","1..99","PRIMARY_H_ACCESS_NUMERATOR","rooms top-coded as released"),
("BDSP","0..99","SENSITIVITY_NUMERATOR","bedrooms top-coded as released"),
("GRPIP","1..101","AFFORDABILITY_NOT_PRIMARY","renter burden; N/A no household income"),
("OCPIP","1..101","AFFORDABILITY_NOT_PRIMARY","owner burden; N/A no household income"),
("PLM","1/2","SECONDARY_ADEQUACY","complete plumbing yes/no"),
("KIT","1/2","SECONDARY_ADEQUACY","complete kitchen yes/no"),
("WGTP","1..9999","FULL_WEIGHT","housing-unit weight"),
("WGTP1-WGTP80","released_integer_weights","REPLICATE_WEIGHTS","no clipping"),
]
with CODES.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["variable","released_codes","role","policy"])
    w.writerows(code_rows)

arch_rows=[
("PRIMARY_H_ACCESS_FAMILY","SPACE_CROWDING_ADEQUACY"),
("PRIMARY_H_ACCESS_ESTIMAND","H_ACCESS_SPACE_ROOMS_PER_PERSON"),
("PRIMARY_H_ACCESS_FORMULA","RMSP_DIV_NP"),
("PRIMARY_H_ACCESS_AGGREGATION","WGTP_WEIGHTED_MEAN_HOUSEHOLD_RATIO"),
("PRIMARY_H_ACCESS_ORIENTATION","HIGHER_IS_BETTER"),
("PRIMARY_H_ACCESS_SELECTED_BEFORE_VALUES","1"),
("SENSITIVITY_H_ACCESS_ESTIMAND","BDSP_DIV_NP"),
("AFFORDABILITY_PRIMARY","0"),
("AFFORDABILITY_D_OVERLAP_BLOCKER","1"),
("PHYSICAL_ADEQUACY_PRIMARY","0"),
("STABILITY_IDENTIFIED_IN_2022_ACS","0"),
("H_SERVICE_IS_COMPLETE_H_STATE","0"),
("H_ACCESS_VALUES_AUTHORIZED","0"),
("H_FULL_STATE_COMPLETE","0"),
]
with ARCH.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["decision","value"])
    w.writerows(arch_rows)

blocker_rows=[
("ACS_2022_MICRODATA_BYTES","NOT_OPENED"),
("ALL_8_COHORT_CELL_SUPPORT","UNTESTED_UNTIL_EXECUTION"),
("PRIMARY_H_ACCESS_POINT_ESTIMATES","NOT_COMPUTED"),
("PRIMARY_H_ACCESS_REPLICATE_ESTIMATES","NOT_COMPUTED"),
("OWNER_RENTER_CONTRASTS","NOT_COMPUTED"),
("H_FULL_SECURITY_STATE","INCOMPLETE_SPACE_ACCESS_ONLY"),
("AHS_2023_RICH_SECURITY_SENSITIVITY","PRESERVED_YEAR_MISMATCH"),
]
with BLOCKERS.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["blocker","status"])
    w.writerows(blocker_rows)

log="\n".join([
"================================================================================",
"ECONOMIC GEOMETRY RESEARCH — E4C3B",
"ACS 2022 EXACT METADATA + H_ACCESS HARMONIZATION",
"================================================================================",
"RAW_SURVEY_DATA_READ=0",
"ACS_2022_MICRODATA_VALUES_OPENED=0",
"NEW_HOUSING_ECONOMIC_VALUES_OPENED=0",
"OWNER_RENTER_OUTCOME_VALUES_OPENED=0",
"H_ACCESS_VALUES_COMPUTED=0",
"TRANSFORMED_VALUES_COMPUTED=0",
"GEOMETRY_PERFORMED=0",
"OFFICIAL_CENSUS_METADATA_OPENED=1",
"ACS_2022_EXACT_DICTIONARY_VALIDATED=1",
"ACS_HOUSEHOLDER_AGE_FIELD=HHLDRAGEP",
"ACS_OWNER_CODES=1,2",
"ACS_RENTER_CODE=3",
"ACS_NO_RENT_CODE_EXCLUDED=4",
"PERSON_LEVEL_JOIN_REQUIRED=0",
"PRIMARY_H_ACCESS_FAMILY=SPACE_CROWDING_ADEQUACY",
"PRIMARY_H_ACCESS_ESTIMAND=H_ACCESS_SPACE_ROOMS_PER_PERSON",
"PRIMARY_H_ACCESS_FORMULA=RMSP_DIV_NP",
"PRIMARY_H_ACCESS_AGGREGATION=WGTP_WEIGHTED_MEAN_HOUSEHOLD_RATIO",
"PRIMARY_H_ACCESS_ORIENTATION=HIGHER_IS_BETTER",
"PRIMARY_H_ACCESS_SELECTED_BEFORE_VALUES=1",
"SENSITIVITY_H_ACCESS_ESTIMAND=BDSP_DIV_NP",
"AFFORDABILITY_PRIMARY=0",
"AFFORDABILITY_D_OVERLAP_BLOCKER=1",
"PHYSICAL_ADEQUACY_PRIMARY=0",
"STABILITY_IDENTIFIED_IN_2022_ACS=0",
"ACS_FULL_WEIGHT=WGTP",
"ACS_REPLICATE_WEIGHTS=WGTP1-WGTP80",
"ACS_REPLICATE_COUNT=80",
"ACS_SDR_VARIANCE_FACTOR=4/80",
"REPLICATE_WEIGHT_CLIPPING_AUTHORIZED=0",
"ROOMS_TOPCODE_PRESERVED_AS_RELEASED=1",
"BEDROOMS_TOPCODE_PRESERVED_AS_RELEASED=1",
"WINSORIZATION_AUTHORIZED=0",
"OUTCOME_BASED_FILTERING_AUTHORIZED=0",
"H_SERVICE_IS_COMPLETE_H_STATE=0",
"H_ACCESS_VALUES_AUTHORIZED=0",
"H_FULL_STATE_COMPLETE=0",
"FIVE_COMPONENT_STATE_VECTOR_AUTHORIZED=0",
"FIVE_COMPONENT_NORMALIZATION_AUTHORIZED=0",
"GEOMETRY_AUTHORIZED=0",
"DIMENSIONALITY_TEST_AUTHORIZED=0",
"REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
"FINAL_SCALAR_AUTHORIZED=0",
"OWNER_RENTER_DIRECTION_USED_AS_SELECTION_GATE=0",
"STATISTICAL_SIGNIFICANCE_USED_AS_SELECTION_GATE=0",
"GEOMETRY_USED_AS_SELECTION_GATE=0",
"E4C3B_ACS_2022_METADATA_HARMONIZATION=PASS",
"E4C3C_FIRST_ACS_2022_H_ACCESS_EXECUTION_PREFLIGHT_AUTHORIZED=1",
])+"\n"
EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
