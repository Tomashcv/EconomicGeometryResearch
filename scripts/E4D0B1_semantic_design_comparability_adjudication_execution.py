#!/usr/bin/env python3
from pathlib import Path
import csv,hashlib,json,re,subprocess,tempfile

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"data/metadata/E4D0B1_semantic_design_comparability_adjudication_execution_contract.json"
PLAN=ROOT/"data/metadata/E4D0B1_adjudication_object_plan.tsv"
A_MANIFEST=ROOT/"data/results/E4D0A_official_evidence_manifest.tsv"
B_LINEAGE=ROOT/"data/metadata/E4D0B_frozen_semantic_authority_lineage.tsv"

EXEC=ROOT/"data/metadata/E4D0B1_execution.txt"
AUDIT=ROOT/"data/metadata/E4D0B1_semantic_design_comparability_adjudication_execution_audit.txt"
EVIDENCE_OUT=ROOT/"data/results/E4D0B1_semantic_evidence_registry.tsv"
RAWVAR=ROOT/"data/results/E4D0B1_frozen_raw_variable_bridge_registry.tsv"
ADJ=ROOT/"data/results/E4D0B1_adjudication_registry.tsv"
GAPS=ROOT/"data/results/E4D0B1_unresolved_gap_registry.tsv"
GATES=ROOT/"data/results/E4D0B1_execution_hard_gates.tsv"
DECISION=ROOT/"data/results/E4D0B1_semantic_design_comparability_adjudication_decision.tsv"

c=json.loads(CONTRACT.read_text(encoding="utf-8"))

with PLAN.open("r",encoding="utf-8",newline="") as f:
    plan=list(csv.DictReader(f,delimiter="\t"))
assert len(plan)==40
assert [int(r["object_index"]) for r in plan]==list(range(1,41))

with A_MANIFEST.open("r",encoding="utf-8",newline="") as f:
    manifest=list(csv.DictReader(f,delimiter="\t"))
assert len(manifest)==25
by_id={r["artifact_id"]:r for r in manifest}

with B_LINEAGE.open("r",encoding="utf-8",newline="") as f:
    lineage=list(csv.DictReader(f,delimiter="\t"))
assert len(lineage)==9

# Content opening begins here, after E4D0B1 precommit.
opened_document_count=0
opened_static_authority_count=0

def read_bytes_verified(row):
    global opened_document_count
    p=ROOT/row["local_path"]
    b=p.read_bytes()
    assert hashlib.sha256(b).hexdigest()==row["sha256"],p
    assert str(len(b))==row["bytes"],p
    opened_document_count+=1
    return b

def normalize(s):
    return re.sub(r"\s+"," ",s).strip()

def text_from_artifact(artifact_id,tmpdir):
    r=by_id[artifact_id]
    b=read_bytes_verified(r)
    if r["content_class"]=="PDF":
        src=ROOT/r["local_path"]
        out=tmpdir/(artifact_id+".txt")
        subprocess.run(
            ["pdftotext","-layout","-enc","UTF-8",str(src),str(out)],
            check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL
        )
        return out.read_text(encoding="utf-8",errors="replace")
    return b.decode("utf-8",errors="replace")

static_text={}
for r in lineage:
    p=ROOT/r["artifact"]
    b=p.read_bytes()
    assert hashlib.sha256(b).hexdigest()==r["sha256"],p
    static_text[r["role"]]=b.decode("utf-8",errors="replace")
    opened_static_authority_count+=1

with tempfile.TemporaryDirectory(prefix="E4D0B1_") as td:
    td=Path(td)
    # Read each of 25 evidence artifacts exactly once into semantic text.
    doc_text={}
    for r in manifest:
        aid=r["artifact_id"]
        doc_text[aid]=text_from_artifact(aid,td)

assert opened_document_count==25
assert opened_static_authority_count==9

# -------- evidence helpers --------

evidence_rows=[]
def ev(evidence_id,family,year,object_id,source_ids,criterion,observed,status):
    evidence_rows.append([
        evidence_id,family,year,object_id,"|".join(source_ids),
        criterion,normalize(observed)[:500],status
    ])

def contains_all(text,tokens):
    low=text.lower()
    return all(t.lower() in low for t in tokens)

def snippets(text,token,window=180):
    low=text.lower(); tok=token.lower()
    i=low.find(tok)
    if i<0: return ""
    lo=max(0,i-window); hi=min(len(text),i+len(token)+window)
    return normalize(text[lo:hi])

def definition_signature(text,token):
    s=snippets(text,token,260).lower()
    # Keep semantic words, discard punctuation/year/positions.
    words=re.findall(r"[a-z]+",s)
    stop={"the","a","an","of","to","and","or","in","is","are","for","this","that",
          "variable","record","length","position","range","values","value","universe",
          "not","required","int","string","year","years"}
    return {w for w in words if len(w)>2 and w not in stop}

def semantic_overlap(text_a,text_b,token,min_jaccard=0.30):
    if token.lower() not in text_a.lower() or token.lower() not in text_b.lower():
        return False,0.0
    a=definition_signature(text_a,token)
    b=definition_signature(text_b,token)
    if not a or not b:
        return False,0.0
    j=len(a&b)/len(a|b)
    return j>=min_jaccard,j

# Core document texts.
acs19=doc_text["ACS_2019_DATA_DICTIONARY"]
acs22=doc_text["ACS_2022_DATA_DICTIONARY"]
acs19read=doc_text["ACS_2019_README"]
acs22guide=doc_text["ACS_2022_USER_GUIDE"]
acs19page=doc_text["ACS_2019_RELEASE_PAGE"]
acs22page=doc_text["ACS_2022_RELEASE_PAGE"]

scf19=doc_text["SCF_2019_CODEBOOK"]
scf22=doc_text["SCF_2022_CODEBOOK"]
scf19page=doc_text["SCF_2019_RELEASE_PAGE"]
scf22page=doc_text["SCF_2022_RELEASE_PAGE"]
scfse=doc_text["SCF_SHARED_STANDARD_ERROR"]

cps19=doc_text["CPS_2019_DATA_DICTIONARY"]
cps22=doc_text["CPS_2022_DATA_DICTIONARY"]
cps19tech=doc_text["CPS_2019_TECHDOC"]
cps22tech=doc_text["CPS_2022_TECHDOC"]
cps19page=doc_text["CPS_2019_RELEASE_PAGE"]
cps22page=doc_text["CPS_2022_RELEASE_PAGE"]
cps19sas=doc_text["CPS_2019_REPWGT_SAS"]
cps22sas=doc_text["CPS_2022_REPWGT_SAS"]

# Combine frozen implementation authority text by family.
h_auth="\n".join(v for k,v in static_text.items() if k.startswith("H_") or "PARTIAL_STATE" in k)
scf_auth="\n".join(v for k,v in static_text.items() if k.startswith("KD_") or "K_REFERENCE" in k or "PARTIAL_STATE" in k)
cps_auth="\n".join(v for k,v in static_text.items() if k.startswith("I_") or "PARTIAL_STATE" in k)

# Recover actual frozen raw-variable candidates conservatively.
raw_rows=[]

def bridge(coord,family,candidates,auth,doc19,doc22):
    used=[]
    for tok in candidates:
        auth_present=tok.lower() in auth.lower()
        d19=tok.lower() in doc19.lower()
        d22=tok.lower() in doc22.lower()
        overlap,j=semantic_overlap(doc19,doc22,tok) if d19 and d22 else (False,0.0)
        if auth_present:
            used.append(tok)
        raw_rows.append([
            coord,family,tok,str(int(auth_present)),str(int(d19)),str(int(d22)),
            f"{j:.6f}",str(int(overlap))
        ])
    return used

h_core=bridge("H_ACCESS_SPACE_ROOMS_PER_PERSON","ACS",
              ["RMSP","NP"],h_auth,acs19,acs22)
h_age=bridge("H_AGE_MAPPING","ACS",["AGEP"],h_auth,acs19,acs22)
h_ten=bridge("H_TENURE_MAPPING","ACS",["TEN"],h_auth,acs19,acs22)
bridge("H_WEIGHT","ACS",["WGTP","WGTP1","WGTP80"],h_auth,acs19+"\n"+acs19read,acs22+"\n"+acs22guide)

k_core=bridge("K_FIN_MEAN_TRANSFORMED","SCF",["FIN"],scf_auth,scf19,scf22)
d_core=bridge("D_PIRTOTAL_MEAN_STATE_TRANSFORMED","SCF",["PIRTOTAL"],scf_auth,scf19,scf22)
scf_weight=bridge("SCF_WEIGHT","SCF",["X42001"],scf_auth,scf19,scf22)

fyft_pool=c["coordinate_source_evidence"]["I_FYFT_SHARE"]["candidate_pool"]
search_pool=c["coordinate_source_evidence"]["I_SEARCH_SECURITY"]["candidate_pool"]
fyft_used=bridge("I_FYFT_SHARE","CPS_ASEC",fyft_pool,cps_auth,cps19,cps22)
search_used=bridge("I_SEARCH_SECURITY","CPS_ASEC",search_pool,cps_auth,cps19,cps22)
cps_age=bridge("I_AGE_MAPPING","CPS_ASEC",["A_AGE"],cps_auth,cps19,cps22)
cps_ten=bridge("I_TENURE_MAPPING","CPS_ASEC",["H_TENURE"],cps_auth,cps19,cps22)
bridge("I_POINT_WEIGHT","CPS_ASEC",["HSUP_WGT","MARSUPWT"],cps_auth,cps19,cps22)

def write_tsv(path,header,rows):
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,delimiter="\t",lineterminator="\n")
        w.writerow(header); w.writerows(rows)

write_tsv(
    RAWVAR,
    ["coordinate_or_role","family","candidate_token",
     "present_in_frozen_2022_authority","present_in_2019_official_docs",
     "present_in_2022_official_docs","definition_signature_jaccard",
     "semantic_overlap_gate"],
    raw_rows
)

# -------- deterministic adjudication evidence --------

statuses={}

def set_status(idx,status,basis,evidence_ids):
    assert status in {"PASS","VERSIONED_PASS","FAIL","UNRESOLVED"}
    statuses[int(idx)]=(status,basis,"|".join(evidence_ids))

# 1 year availability
release_ok=all(x in by_id for x in [
    "ACS_2019_RELEASE_PAGE","ACS_2022_RELEASE_PAGE",
    "SCF_2019_RELEASE_PAGE","SCF_2022_RELEASE_PAGE",
    "CPS_2019_RELEASE_PAGE","CPS_2022_RELEASE_PAGE"
])
ev("EV001","ALL","2019|2022","YEAR_AVAILABILITY",
   ["ACS_2019_RELEASE_PAGE","ACS_2022_RELEASE_PAGE","SCF_2019_RELEASE_PAGE",
    "SCF_2022_RELEASE_PAGE","CPS_2019_RELEASE_PAGE","CPS_2022_RELEASE_PAGE"],
   "hash-pinned official release evidence exists for all family-year pairs",
   f"release_pairs_present={int(release_ok)}","PASS" if release_ok else "UNRESOLVED")
set_status(1,"PASS" if release_ok else "UNRESOLVED",
           "official release evidence exists for all three families in both years",
           ["EV001"])

# H variable continuity: require frozen RMSP and NP, both years, semantic overlap.
h_req=["RMSP","NP"]
h_auth_ok=all(t.lower() in h_auth.lower() for t in h_req)
h_docs=[]
h_over=[]
for t in h_req:
    ok,j=semantic_overlap(acs19,acs22,t)
    h_docs.append(t.lower() in acs19.lower() and t.lower() in acs22.lower())
    h_over.append(ok)
    ev("EVH_"+t,"ACS","2019|2022","H_ACCESS_SPACE_ROOMS_PER_PERSON",
       ["ACS_2019_DATA_DICTIONARY","ACS_2022_DATA_DICTIONARY"],
       f"{t} exists in both dictionaries with overlapping nearby definition semantics",
       f"present_both={int(h_docs[-1])};semantic_overlap={int(ok)}",
       "PASS" if ok else "UNRESOLVED")
h_var_pass=h_auth_ok and all(h_docs) and all(h_over)
set_status(2,"PASS" if h_var_pass else "UNRESOLVED",
           "frozen H numerator/denominator variables must exist with compatible official definitions",
           ["EVH_RMSP","EVH_NP"])

# SCF K/D summary variables. Full-survey codebooks may not document summary-extract aliases.
for idx,coord,tok in [
    (3,"K_FIN_MEAN_TRANSFORMED","FIN"),
    (4,"D_PIRTOTAL_MEAN_STATE_TRANSFORMED","PIRTOTAL")
]:
    auth_present=tok.lower() in scf_auth.lower()
    d19=tok.lower() in scf19.lower()
    d22=tok.lower() in scf22.lower()
    ok,j=semantic_overlap(scf19,scf22,tok) if d19 and d22 else (False,0.0)
    eid="EVSCF_"+tok
    ev(eid,"SCF","2019|2022",coord,
       ["SCF_2019_CODEBOOK","SCF_2022_CODEBOOK"],
       f"frozen {tok} implementation identity must be supported by year-specific official semantics",
       f"frozen_authority_mentions={int(auth_present)};2019_codebook={int(d19)};2022_codebook={int(d22)};semantic_overlap={int(ok)}",
       "PASS" if (auth_present and ok) else "UNRESOLVED")
    set_status(idx,"PASS" if (auth_present and ok) else "UNRESOLVED",
               "current E4D0A bundle must directly document the frozen SCF summary-variable semantics; absence is unresolved, not failure",
               [eid])

# CPS coordinate continuity from candidates actually used by frozen source.
def cps_coord_status(idx,coord,used):
    eid="EV_"+coord
    if not used:
        ev(eid,"CPS_ASEC","2019|2022",coord,
           ["CPS_2019_DATA_DICTIONARY","CPS_2022_DATA_DICTIONARY"],
           "recover at least one candidate raw variable from frozen 2022 implementation",
           "frozen_candidate_match_count=0","UNRESOLVED")
        set_status(idx,"UNRESOLVED","no bounded candidate token was recoverable from frozen 2022 implementation",[eid])
        return
    checks=[]
    detail=[]
    for tok in used:
        ok,j=semantic_overlap(cps19,cps22,tok)
        checks.append(ok)
        detail.append(f"{tok}:{int(ok)}")
    ev(eid,"CPS_ASEC","2019|2022",coord,
       ["CPS_2019_DATA_DICTIONARY","CPS_2022_DATA_DICTIONARY"],
       "all raw-variable candidates actually referenced by frozen 2022 implementation exist with compatible official definitions",
       "used="+"|".join(used)+";overlap="+"|".join(detail),
       "PASS" if all(checks) else "UNRESOLVED")
    set_status(idx,"PASS" if all(checks) else "UNRESOLVED",
               "same frozen raw-variable implementation must be semantically supported in both year dictionaries",
               [eid])

cps_coord_status(5,"I_FYFT_SHARE",fyft_used)
cps_coord_status(6,"I_SEARCH_SECURITY",search_used)

# Population universe family + coordinate crosschecks.
acs_univ=contains_all((acs19page+"\n"+acs19read).lower(),["pums"]) and contains_all((acs22page+"\n"+acs22guide).lower(),["pums"])
scf_univ=("famil" in scf19page.lower()) and ("famil" in scf22page.lower())
cps_univ=("annual social and economic" in cps19page.lower()) and ("annual social and economic" in cps22page.lower())

for eid,fam,ok,sources,obs in [
    ("EVU_ACS","ACS",acs_univ,["ACS_2019_RELEASE_PAGE","ACS_2019_README","ACS_2022_RELEASE_PAGE","ACS_2022_USER_GUIDE"],"PUMS family evidence"),
    ("EVU_SCF","SCF",scf_univ,["SCF_2019_RELEASE_PAGE","SCF_2022_RELEASE_PAGE"],"family-survey evidence"),
    ("EVU_CPS","CPS_ASEC",cps_univ,["CPS_2019_RELEASE_PAGE","CPS_2022_RELEASE_PAGE"],"ASEC release evidence"),
]:
    ev(eid,fam,"2019|2022","POPULATION_UNIVERSE_CONTINUITY",sources,
       "same survey-family target universe must be identifiable in both years",
       f"{obs};gate={int(ok)}","PASS" if ok else "UNRESOLVED")

set_status(7,"PASS" if acs_univ else "UNRESOLVED","ACS PUMS universe evidence must support both years",["EVU_ACS"])
set_status(8,"PASS" if scf_univ else "UNRESOLVED","SCF family universe evidence must support both years",["EVU_SCF"])
set_status(9,"PASS" if cps_univ else "UNRESOLVED","CPS ASEC universe evidence must support both years",["EVU_CPS"])

# Age mappings.
def token_pair_gate(auth,doc19,doc22,tok):
    auth_ok=tok.lower() in auth.lower()
    sem,j=semantic_overlap(doc19,doc22,tok)
    return auth_ok and sem,auth_ok,sem,j

acs_age_ok,_,_,_=token_pair_gate(h_auth,acs19,acs22,"AGEP")
cps_age_ok,_,_,_=token_pair_gate(cps_auth,cps19,cps22,"A_AGE")

# SCF age: recover AGE token only if frozen authority actually names it and year codebooks support it.
scf_age_candidates=["AGE","X14","X8021"]
scf_age_used=[t for t in scf_age_candidates if t.lower() in scf_auth.lower()]
scf_age_ok=False
for t in scf_age_used:
    ok,_=semantic_overlap(scf19,scf22,t)
    scf_age_ok=scf_age_ok or ok

ev("EVA_ACS","ACS","2019|2022","AGE_BAND_MAPPING_CONTINUITY",
   ["ACS_2019_DATA_DICTIONARY","ACS_2022_DATA_DICTIONARY"],
   "frozen AGEP age source exists with compatible semantics",
   f"gate={int(acs_age_ok)}","PASS" if acs_age_ok else "UNRESOLVED")
ev("EVA_SCF","SCF","2019|2022","AGE_BAND_MAPPING_CONTINUITY",
   ["SCF_2019_CODEBOOK","SCF_2022_CODEBOOK"],
   "frozen SCF age source can be identified and documented in both years",
   f"candidate_used={'|'.join(scf_age_used) if scf_age_used else 'NONE'};gate={int(scf_age_ok)}",
   "PASS" if scf_age_ok else "UNRESOLVED")
ev("EVA_CPS","CPS_ASEC","2019|2022","AGE_BAND_MAPPING_CONTINUITY",
   ["CPS_2019_DATA_DICTIONARY","CPS_2022_DATA_DICTIONARY"],
   "frozen A_AGE source exists with compatible semantics",
   f"gate={int(cps_age_ok)}","PASS" if cps_age_ok else "UNRESOLVED")

set_status(10,"PASS" if acs_age_ok else "UNRESOLVED","25-64 bands require same ACS age source semantics",["EVA_ACS"])
set_status(11,"PASS" if scf_age_ok else "UNRESOLVED","25-64 bands require recoverable same SCF age source semantics",["EVA_SCF"])
set_status(12,"PASS" if cps_age_ok else "UNRESOLVED","25-64 bands require same CPS age source semantics",["EVA_CPS"])

# Tenure mappings.
acs_ten_ok,_,_,_=token_pair_gate(h_auth,acs19,acs22,"TEN")
cps_ten_ok,_,_,_=token_pair_gate(cps_auth,cps19,cps22,"H_TENURE")
scf_ten_candidates=["HHOUSES","OWN","HOMEOWN","HOUSES"]
scf_ten_used=[t for t in scf_ten_candidates if t.lower() in scf_auth.lower()]
scf_ten_ok=False
for t in scf_ten_used:
    ok,_=semantic_overlap(scf19,scf22,t)
    scf_ten_ok=scf_ten_ok or ok

ev("EVT_ACS","ACS","2019|2022","TENURE_MAPPING_CONTINUITY",
   ["ACS_2019_DATA_DICTIONARY","ACS_2022_DATA_DICTIONARY"],
   "frozen TEN tenure source exists with compatible semantics",
   f"gate={int(acs_ten_ok)}","PASS" if acs_ten_ok else "UNRESOLVED")
ev("EVT_SCF","SCF","2019|2022","TENURE_MAPPING_CONTINUITY",
   ["SCF_2019_CODEBOOK","SCF_2022_CODEBOOK"],
   "frozen SCF owner/renter source can be identified and documented in both years",
   f"candidate_used={'|'.join(scf_ten_used) if scf_ten_used else 'NONE'};gate={int(scf_ten_ok)}",
   "PASS" if scf_ten_ok else "UNRESOLVED")
ev("EVT_CPS","CPS_ASEC","2019|2022","TENURE_MAPPING_CONTINUITY",
   ["CPS_2019_DATA_DICTIONARY","CPS_2022_DATA_DICTIONARY"],
   "frozen H_TENURE source exists with compatible semantics",
   f"gate={int(cps_ten_ok)}","PASS" if cps_ten_ok else "UNRESOLVED")

set_status(13,"PASS" if acs_ten_ok else "UNRESOLVED","owner/renter mapping requires same ACS tenure semantics",["EVT_ACS"])
set_status(14,"PASS" if scf_ten_ok else "UNRESOLVED","owner/renter mapping requires recoverable same SCF tenure semantics",["EVT_SCF"])
set_status(15,"PASS" if cps_ten_ok else "UNRESOLVED","owner/renter mapping requires same CPS tenure semantics",["EVT_CPS"])

# Frozen transforms are reused unchanged; this is a method continuity statement, not a value result.
for idx,coord in [(16,"H_ACCESS_SPACE_ROOMS_PER_PERSON"),(17,"K_FIN_MEAN_TRANSFORMED"),
                  (18,"D_PIRTOTAL_MEAN_STATE_TRANSFORMED"),(19,"I_FYFT_SHARE"),
                  (20,"I_SEARCH_SECURITY")]:
    eid="EVTR_"+str(idx)
    ev(eid,"METHOD","2019|2022",coord,
       [],"reuse exact frozen 2022 transform/orientation formula with no later-year refit",
       "frozen_transform_reuse=1;2019_value_refit=0","PASS")
    set_status(idx,"PASS","same pre-existing transform/orientation formula is mandated for later years",[eid])

# Survey-weight and replicate design.
acs_weight = (
    contains_all(acs19read,["80 replicate"]) and
    contains_all(acs22guide,["80 replicate"]) and
    ("4/80" in acs19read.replace(" ","")) and
    ("4/80" in acs22guide.replace(" ",""))
)
ev("EVW_ACS","ACS","2019|2022","SURVEY_WEIGHT_DESIGN_CONTINUITY",
   ["ACS_2019_README","ACS_2022_USER_GUIDE"],
   "both years document 80 replicate weights and the SDR 4/80 variance architecture",
   f"gate={int(acs_weight)}","PASS" if acs_weight else "UNRESOLVED")
set_status(21,"PASS" if acs_weight else "UNRESOLVED",
           "ACS point/replicate weighting architecture must be documented in both years",["EVW_ACS"])

scf_weight_id=("x42001" in scf19.lower() and "x42001" in scf22.lower())
scf_release_rep=("replicate weight" in scf19page.lower() and "replicate weight" in scf22page.lower())
scf_five=("five" in scf19page.lower() and "implicat" in scf19page.lower()
          and "five" in scf22page.lower() and "implicat" in scf22page.lower())
scf_design_valid=scf_weight_id and scf_release_rep and scf_five and len(scfse)>100
ev("EVW_SCF","SCF","2019|2022","SURVEY_WEIGHT_DESIGN_CONTINUITY",
   ["SCF_2019_CODEBOOK","SCF_2022_CODEBOOK","SCF_2019_RELEASE_PAGE",
    "SCF_2022_RELEASE_PAGE","SCF_SHARED_STANDARD_ERROR"],
   "both waves expose X42001, replicate-weight files, five implicates, and shared official standard-error documentation",
   f"x42001_both={int(scf_weight_id)};replicate_pages={int(scf_release_rep)};five_implicates={int(scf_five)}",
   "VERSIONED_PASS" if scf_design_valid else "UNRESOLVED")
set_status(22,"VERSIONED_PASS" if scf_design_valid else "UNRESOLVED",
           "wave-specific SCF sample design is permitted only under official valid weight/replicate architecture; no equality-of-design claim",
           ["EVW_SCF"])

# CPS replicate layout exact indexed-token coverage.
def has_indexed_tokens(text,prefix,n):
    low=text.lower()
    return all(f"{prefix}{i}".lower() in low for i in range(1,n+1))
cps_rep19=has_indexed_tokens(cps19sas,"PWWGT",160)
cps_rep22=has_indexed_tokens(cps22sas,"PWWGT",160)
cps_weight_tokens=(
    ("hsup_wgt" in cps19.lower() or "marsupwt" in cps19.lower()) and
    ("hsup_wgt" in cps22.lower() or "marsupwt" in cps22.lower())
)
cps_weight_ok=cps_rep19 and cps_rep22 and cps_weight_tokens
ev("EVW_CPS","CPS_ASEC","2019|2022","SURVEY_WEIGHT_DESIGN_CONTINUITY",
   ["CPS_2019_REPWGT_SAS","CPS_2022_REPWGT_SAS",
    "CPS_2019_DATA_DICTIONARY","CPS_2022_DATA_DICTIONARY"],
   "both years expose the full 160-replicate PWWGT layout and a March supplement point-weight field",
   f"rep2019={int(cps_rep19)};rep2022={int(cps_rep22)};point_weight={int(cps_weight_tokens)}",
   "PASS" if cps_weight_ok else "UNRESOLVED")
set_status(23,"PASS" if cps_weight_ok else "UNRESOLVED",
           "CPS ASEC year-specific point and replicate weighting architecture must be documented",["EVW_CPS"])

# Replicate/formula continuity rows.
set_status(24,"PASS" if acs_weight else "UNRESOLVED",
           "ACS 80-replicate SDR architecture is documented identically enough for the frozen estimator",["EVW_ACS"])
set_status(25,"VERSIONED_PASS" if scf_design_valid else "UNRESOLVED",
           "SCF five-implicate plus official replicate-weight architecture remains valid wave-by-wave; exact sample designs need not be identical",["EVW_SCF"])
set_status(26,"PASS" if (cps_rep19 and cps_rep22) else "UNRESOLVED",
           "CPS ASEC exact 160-replicate layout is present in both year-specific SAS layouts",["EVW_CPS"])

# Reference-period alignment.
# H uses contemporaneous household stock variables; same identifiers/definitions in annual ACS.
h_ref=h_var_pass
ev("EVR_H","ACS","2019|2022","H_ACCESS_SPACE_ROOMS_PER_PERSON",
   ["ACS_2019_DATA_DICTIONARY","ACS_2022_DATA_DICTIONARY"],
   "same rooms/person household-stock variables are used in both annual ACS waves",
   f"same_core_semantics={int(h_ref)}","PASS" if h_ref else "UNRESOLVED")
set_status(27,"PASS" if h_ref else "UNRESOLVED",
           "H annual-wave interpretation is permitted only if the same household-stock variables retain semantics",["EVR_H"])

# SCF K/D reference periods require summary-variable semantic documentation in the bundle.
for idx,coord,tok,var_idx in [
    (28,"K_FIN_MEAN_TRANSFORMED","FIN",3),
    (29,"D_PIRTOTAL_MEAN_STATE_TRANSFORMED","PIRTOTAL",4)
]:
    source_status=statuses[var_idx][0]
    eid="EVR_"+tok
    ev(eid,"SCF","2019|2022",coord,
       ["SCF_2019_CODEBOOK","SCF_2022_CODEBOOK"],
       "year-specific official semantics must identify the economic timing of the frozen SCF summary variable",
       f"variable_continuity_status={source_status}",
       "UNRESOLVED" if source_status!="PASS" else "UNRESOLVED")
    # Even if name continuity happens to pass, codebook-only timing evidence is not enough for summary aliases.
    set_status(idx,"UNRESOLVED",
               "current bundle does not precommit a summary-extract reference-period bridge for this SCF coordinate",
               [eid])

# CPS reference classes from actual frozen candidates.
prior=set(c["reference_period_classes"]["CPS_PRIOR_YEAR_WORK_EXPERIENCE"])
def cps_ref(idx,coord,used):
    eid="EVR_"+coord
    if not used:
        ev(eid,"CPS_ASEC","2019|2022",coord,
           ["CPS_2019_DATA_DICTIONARY","CPS_2022_DATA_DICTIONARY"],
           "recover frozen raw variables before classifying reference period",
           "used=NONE","UNRESOLVED")
        set_status(idx,"UNRESOLVED","reference period cannot be assigned until frozen raw variables are recovered",[eid])
        return
    classes=[]
    for t in used:
        if t in prior:
            classes.append("PRIOR_CALENDAR_YEAR_WORK_EXPERIENCE")
        elif t.startswith("A_"):
            classes.append("CURRENT_SURVEY_STATUS")
        else:
            classes.append("OTHER")
    semantic_ok=all(semantic_overlap(cps19,cps22,t)[0] for t in used)
    ok=semantic_ok and "OTHER" not in classes
    ev(eid,"CPS_ASEC","2019|2022",coord,
       ["CPS_2019_DATA_DICTIONARY","CPS_2022_DATA_DICTIONARY"],
       "same frozen variable mix must map to the same explicit current-status/prior-year timing classes in both years",
       "used="+"|".join(used)+";classes="+"|".join(classes)+f";semantic_gate={int(semantic_ok)}",
       "PASS" if ok else "UNRESOLVED")
    set_status(idx,"PASS" if ok else "UNRESOLVED",
               "mixed timing is allowed only when the same documented raw-variable timing composition is preserved across years",
               [eid])

cps_ref(30,"I_FYFT_SHARE",fyft_used)
cps_ref(31,"I_SEARCH_SECURITY",search_used)

# K price bridge deliberately unresolved before values.
ev("EVPRICE_K","SCF","2019|2022","K_FIN_MEAN_TRANSFORMED",
   [],"nominal K requires a separate pre-value price-level/reference-scale bridge",
   "bridge_frozen=0;2019_K_values_opened=0","UNRESOLVED")
set_status(32,"UNRESOLVED",
           "E4D0B1 intentionally does not choose the K deflator/reference-scale transport rule",
           ["EVPRICE_K"])

# Missing-year policy and hash-pinned vintages.
ev("EVMISS","GLOBAL","2019|2022","MISSING_YEAR_POLICY",
   [],"no 2020/2021 interpolation, carry-forward, or synthetic state",
   "interpolation=0;carry_forward=0;synthetic_intermediate_state=0","PASS")
set_status(33,"PASS","2019→2022 is treated as an observed-wave interval only",["EVMISS"])

for idx,fam in [(34,"ACS"),(35,"SCF"),(36,"CPS_ASEC")]:
    family_rows=[r for r in manifest if r["family"]==fam]
    ok=bool(family_rows) and all(len(r["sha256"])==64 for r in family_rows)
    eid="EVV_"+fam
    ev(eid,fam,"2019|2022","SURVEY_RELEASE_VINTAGE_POLICY",
       [r["artifact_id"] for r in family_rows],
       "all official evidence artifacts for the family are hash-pinned",
       f"artifact_count={len(family_rows)};hash_gate={int(ok)}",
       "PASS" if ok else "UNRESOLVED")
    set_status(idx,"PASS" if ok else "UNRESOLVED",
               "exact acquired official-document bytes define the frozen evidence vintage",[eid])

# Crosscheck coordinate universes mirror their family status.
set_status(38,statuses[7][0],"H coordinate inherits ACS universe adjudication; no narrower contradictory evidence identified",["EVU_ACS"])
set_status(39,statuses[8][0],"K/D coordinates inherit SCF family universe adjudication; summary-variable semantics remain separate",["EVU_SCF"])
set_status(40,statuses[9][0],"I coordinates inherit CPS ASEC family universe adjudication",["EVU_CPS"])

# COMMON_TIME_GRID is dependency-based and must remain unresolved unless every preceding required object is resolved.
pre_common=[statuses[i][0] for i in range(1,37)]
blocking=sum(s in {"FAIL","UNRESOLVED"} for s in pre_common)
common_status="PASS" if blocking==0 else "UNRESOLVED"
ev("EVGRID","GLOBAL","2019|2022","COMMON_TIME_GRID",
   [],"grid can freeze only when every earlier required object is PASS or VERSIONED_PASS",
   f"blocking_pre_grid_object_count={blocking}",common_status)
set_status(37,common_status,
           "common grid is a downstream dependency, never evidence that can cure unresolved comparability",
           ["EVGRID"])

assert len(statuses)==40

adj_rows=[]
for r in plan:
    i=int(r["object_index"])
    status,basis,eids=statuses[i]
    adj_rows.append([
        str(i),r["axis"],r["scope_type"],r["scope_id"],r["family"],
        status,basis,eids
    ])

write_tsv(
    EVIDENCE_OUT,
    ["evidence_id","family","year","object_id","source_artifact_ids",
     "criterion","observed_summary","evidence_status"],
    evidence_rows
)
write_tsv(
    ADJ,
    ["object_index","axis","scope_type","scope_id","family",
     "status","basis","evidence_ids"],
    adj_rows
)

fail_rows=[r for r in adj_rows if r[5]=="FAIL"]
unresolved_rows=[r for r in adj_rows if r[5]=="UNRESOLVED"]
pass_rows=[r for r in adj_rows if r[5]=="PASS"]
vpass_rows=[r for r in adj_rows if r[5]=="VERSIONED_PASS"]

gap_rows=[]
for r in unresolved_rows:
    axis,scope_id,fam=r[1],r[3],r[4]
    if axis in {"VARIABLE_DEFINITION_CONTINUITY","AGE_BAND_MAPPING_CONTINUITY","TENURE_MAPPING_CONTINUITY","REFERENCE_PERIOD_ALIGNMENT"} and fam=="SCF":
        gap_type="SCF_SUMMARY_EXTRACT_OR_VARIABLE_MAP_EVIDENCE"
        next_action="acquire/pin official SCF summary-extract variable map or macro documentation for the exact frozen coordinate lineage"
    elif axis=="PRICE_LEVEL_OR_NOMINAL_DEFLATION_POLICY":
        gap_type="K_PRICE_LEVEL_BRIDGE"
        next_action="freeze canonical and robustness price-level/reference-scale bridge before any 2019 K value"
    elif axis=="COMMON_TIME_GRID":
        gap_type="DEPENDENCY_BLOCK"
        next_action="resolve all upstream FAIL/UNRESOLVED objects first"
    else:
        gap_type="OFFICIAL_DOCUMENT_SEMANTIC_GAP"
        next_action="acquire/pin only the official documentation needed for this exact unresolved object"
    gap_rows.append([r[0],axis,scope_id,fam,gap_type,next_action])

write_tsv(
    GAPS,
    ["object_index","axis","scope_id","family","gap_type","next_action"],
    gap_rows
)

fail_count=len(fail_rows)
unresolved_count=len(unresolved_rows)
pass_count=len(pass_rows)
vpass_count=len(vpass_rows)

if fail_count>0:
    panel_status="REJECTED_FOR_CURRENT_2019_2022_PANEL"
    next_phase="NONE_2019_REJECTED"
    b2_auth=0
elif unresolved_count>0:
    panel_status="BLOCKED_UNRESOLVED"
    next_phase="E4D0B2"
    b2_auth=1
else:
    panel_status="SEMANTICALLY_ELIGIBLE_PENDING_VERSIONED_BRIDGE_FREEZE"
    next_phase="E4D0B2"
    b2_auth=1

grid_frozen=1 if statuses[37][0]=="PASS" and fail_count==0 and unresolved_count==0 else 0
comparability_verified=1 if fail_count==0 and unresolved_count==0 else 0

gate_rows=[
["E4D0B_PREFLIGHT_REUSED","PASS"],
["OFFICIAL_DOCUMENT_CONTENT_OPENED_AFTER_E4D0B1_PRECOMMIT","PASS"],
["OFFICIAL_DOCUMENT_CONTENT_OPENED_COUNT","25"],
["STATIC_2022_AUTHORITY_CONTENT_OPENED_COUNT","9"],
["MICRODATA_ROWS_OPENED","0"],
["NUMERIC_RESULT_ROWS_OPENED","0"],
["ADDITIONAL_YEAR_ECONOMIC_VALUES_OPENED","0"],
["EXACT_40_ADJUDICATION_OBJECTS","PASS"],
["FAIL_REQUIRES_EXPLICIT_INCOMPATIBILITY","PASS"],
["MISSING_EVIDENCE_TREATED_AS_FAIL","PASS_NO"],
["K_PRICE_BRIDGE_SELECTED_AFTER_2019_VALUES","PASS_NO"],
["COMMON_GRID_USED_TO_CURE_UNRESOLVED","PASS_NO"],
["TEMPORAL_GEOMETRY_COMPUTED","0"],
["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
]
write_tsv(GATES,["gate","value"],gate_rows)

decision_rows=[
["TARGET_YEAR_PAIR","2019_TO_2022"],
["ADJUDICATION_OBJECT_COUNT","40"],
["PASS_OBJECT_COUNT",str(pass_count)],
["VERSIONED_PASS_OBJECT_COUNT",str(vpass_count)],
["FAIL_OBJECT_COUNT",str(fail_count)],
["UNRESOLVED_OBJECT_COUNT",str(unresolved_count)],
["PANEL_STATUS",panel_status],
["ADDITIONAL_YEAR_COMPARABILITY_VERIFIED_COUNT",str(comparability_verified)],
["COMMON_YEAR_GRID_FROZEN",str(grid_frozen)],
["OFFICIAL_DOCUMENT_CONTENT_OPENED_COUNT","25"],
["STATIC_2022_AUTHORITY_CONTENT_OPENED_COUNT","9"],
["MICRODATA_ROWS_OPENED","0"],
["NUMERIC_RESULT_ROWS_OPENED","0"],
["ADDITIONAL_YEAR_ECONOMIC_VALUES_OPENED","0"],
["TEMPORAL_GEOMETRY_COMPUTED","0"],
["REAL_INFLATION_ESTIMATION_AUTHORIZED","0"],
["E4D1_MULTIYEAR_PARTIAL_STATE_COORDINATE_EXECUTION_PREFLIGHT_AUTHORIZED","0"],
["NEXT_PRIMARY_PHASE_ID",next_phase],
["E4D0B2_TARGETED_COMPARABILITY_GAP_RESOLUTION_PREFLIGHT_AUTHORIZED",str(b2_auth)],
["E4D0B1_SEMANTIC_AND_DESIGN_COMPARABILITY_ADJUDICATION_EXECUTION","PASS"],
]
write_tsv(DECISION,["decision","value"],decision_rows)

log="\n".join([
"E4D0B_REUSED_AS_CANONICAL_ADJUDICATION_POLICY=1",
"TARGET_YEAR_PAIR=2019_TO_2022",
"OFFICIAL_DOCUMENT_CONTENT_OPENED_AFTER_E4D0B1_PRECOMMIT=1",
f"OFFICIAL_DOCUMENT_CONTENT_OPENED_COUNT={opened_document_count}",
f"STATIC_2022_AUTHORITY_CONTENT_OPENED_COUNT={opened_static_authority_count}",
"MICRODATA_ROWS_OPENED=0",
"NUMERIC_RESULT_ROWS_OPENED=0",
"ADDITIONAL_YEAR_ECONOMIC_VALUES_OPENED=0",
"ADJUDICATION_OBJECT_COUNT=40",
f"PASS_OBJECT_COUNT={pass_count}",
f"VERSIONED_PASS_OBJECT_COUNT={vpass_count}",
f"FAIL_OBJECT_COUNT={fail_count}",
f"UNRESOLVED_OBJECT_COUNT={unresolved_count}",
f"PANEL_STATUS={panel_status}",
f"ADDITIONAL_YEAR_COMPARABILITY_VERIFIED_COUNT={comparability_verified}",
f"COMMON_YEAR_GRID_FROZEN={grid_frozen}",
"TEMPORAL_GEOMETRY_COMPUTED=0",
"REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
"E4D1_MULTIYEAR_PARTIAL_STATE_COORDINATE_EXECUTION_PREFLIGHT_AUTHORIZED=0",
f"NEXT_PRIMARY_PHASE_ID={next_phase}",
f"E4D0B2_TARGETED_COMPARABILITY_GAP_RESOLUTION_PREFLIGHT_AUTHORIZED={b2_auth}",
"E4D0B1_SEMANTIC_AND_DESIGN_COMPARABILITY_ADJUDICATION_EXECUTION=PASS",
])+"\n"

EXEC.write_text(log,encoding="utf-8")
AUDIT.write_text(log,encoding="utf-8")
print(log,end="")
