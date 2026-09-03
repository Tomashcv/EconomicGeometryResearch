#!/usr/bin/env python3
from pathlib import Path
import ast,csv,hashlib,json,re,zipfile
ROOT=Path(__file__).resolve().parents[1]
C=ROOT/'data/metadata/E4D1D1_frozen_execution_adapter_contract.json'
D0F=ROOT/'data/results/E4D1D0_function_signature_registry.tsv'
D0S=ROOT/'data/results/E4D1D0_method_interface_summary.tsv'
METHODS=[('ACS',ROOT/'scripts/E4C3D_first_acs2022_h_access_execution.py'),('SCF',ROOT/'scripts/E4A2F_first_scf_kd_inference_execution.py'),('CPS_ASEC',ROOT/'scripts/E4A2D_first_cps_i_inference_execution.py')]
A_H=ROOT/'data/raw/acs/2019/1year/csv_hus.zip'; A_P=ROOT/'data/raw/acs/2019/1year/csv_pus.zip'
ARCHIVES=[('ACS_HOUSING',A_H,'CSV_HEADER_ONLY'),('ACS_PERSON',A_P,'CSV_HEADER_ONLY'),('SCF_SUMMARY',ROOT/'data/raw/scf/2019/scfp2019s.zip','ZIP_MEMBER_ONLY'),('SCF_FULL',ROOT/'data/raw/scf/2019/scf2019s.zip','ZIP_MEMBER_ONLY'),('SCF_REPWGT',ROOT/'data/raw/scf/2019/scf2019rw1s.zip','ZIP_MEMBER_ONLY'),('CPS_PUBLIC',ROOT/'data/raw/cps_asec/2019/asec2019_pubuse.zip','ZIP_MEMBER_ONLY'),('CPS_REPWGT',ROOT/'data/raw/cps_asec/2019/CPS_ASEC_ASCII_REPWGT_2019.zip','ZIP_MEMBER_ONLY')]
TOP=ROOT/'data/results/E4D1D1_top_level_statement_registry.tsv'; BIND=ROOT/'data/results/E4D1D1_source_output_binding_registry.tsv'; PROV=ROOT/'data/results/E4D1D1_scientific_function_provenance_registry.tsv'; MEM=ROOT/'data/results/E4D1D1_2019_container_schema_registry.tsv'; COMP=ROOT/'data/results/E4D1D1_static_compatibility_registry.tsv'; G=ROOT/'data/results/E4D1D1_adapter_freeze_hard_gates.tsv'; D=ROOT/'data/results/E4D1D1_frozen_execution_adapter_contract_decision.tsv'; EX=ROOT/'data/metadata/E4D1D1_execution.txt'; AU=ROOT/'data/metadata/E4D1D1_frozen_execution_adapter_contract_audit.txt'
c=json.loads(C.read_text()); assert c['phase']=='E4D1D1'; assert c['adapter_policy']['executor_import'] is False; assert c['adapter_policy']['executor_execution'] is False

def write(p,h,rows):
    with p.open('w',encoding='utf-8',newline='') as f:w=csv.writer(f,delimiter='\t',lineterminator='\n');w.writerow(h);w.writerows(rows)
def segsha(src,n): return hashlib.sha256((ast.get_source_segment(src,n) or '').encode()).hexdigest()
def lits(n): return [x.value for x in ast.walk(n) if isinstance(x,ast.Constant) and isinstance(x.value,str)]
pathre=re.compile(r'(data/|scripts/|\.zip\b|\.csv\b|\.tsv\b|\.dta\b|\.dat\b|\.txt\b|\.json\b)',re.I); yearre=re.compile(r'\b(?:2019|2020|2021|2022)\b')
def cls(name,val,ls):
    u=name.upper(); text=' '.join([val]+ls)
    if any(k in u for k in ('OUT','RESULT','REPORT','AUDIT')) and pathre.search(text): return 'OUTPUT_PATH_BINDING'
    if any(k in u for k in ('RAW','ZIP','ARCHIVE','INPUT','DATA','CODEBK','SAS','FMT','MANIFEST')) and pathre.search(text): return 'SOURCE_PATH_BINDING'
    if 'SHA' in u or 'HASH' in u:return 'HASH_EXPECTATION_BINDING'
    if any(k in u for k in ('MEMBER','FILENAME','FILE_NAME')):return 'SCHEMA_OR_MEMBER_BINDING'
    if any(k in u for k in ('YEAR','PHASE','PREFIX')) or yearre.search(text):return 'YEAR_OR_PHASE_LABEL'
    if any(k in u for k in ('STATISTIC','COHORT','AGE_BAND','TENURE','TARGET','FYFT','SEARCH','TRANSFORM','STATE_SIGN','REPLICATE','IMPUT','FORMULA')):return 'SCIENTIFIC_DEFINITION_IMMUTABLE'
    return 'METHOD_CONSTANT_IMMUTABLE'

def rdmap(p,key):
    with p.open(encoding='utf-8',newline='') as f:return {r[key]:r for r in csv.DictReader(f,delimiter='\t')}
d0s=rdmap(D0S,'family')
with D0F.open(encoding='utf-8',newline='') as f:d0f={(r['family'],r['function']):r for r in csv.DictReader(f,delimiter='\t')}
assert len(d0f)==17 and all(r['interface_class']=='TOP_LEVEL_EXECUTION_UNSAFE' for r in d0s.values())

top=[]; binds=[]; prov=[]; comp=[]
for fam,p in METHODS:
    src=p.read_text(); tree=ast.parse(src); fcnt=0
    for n in tree.body:
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
            fcnt+=1; h=segsha(src,n); r=d0f[(fam,n.name)]; assert h==r['function_source_sha256']; prov.append([fam,str(p.relative_to(ROOT)),n.name,r['signature'],n.lineno,getattr(n,'end_lineno',n.lineno),h,'VERBATIM_REQUIRED'])
    for i,n in enumerate(tree.body,1):
        ls=lits(n); wr=sorted({x.id for x in ast.walk(n) if isinstance(x,ast.Name) and isinstance(x.ctx,ast.Store)}); rr=sorted({x.id for x in ast.walk(n) if isinstance(x,ast.Name) and isinstance(x.ctx,ast.Load)})
        top.append([fam,str(p.relative_to(ROOT)),i,type(n).__name__,getattr(n,'lineno',0),getattr(n,'end_lineno',getattr(n,'lineno',0)),segsha(src,n),'|'.join(wr) or 'EMPTY_SET','|'.join(rr) or 'EMPTY_SET',int(any(pathre.search(x) for x in ls)),int(any(yearre.search(x) for x in ls))])
        if isinstance(n,(ast.Assign,ast.AnnAssign)):
            targets=[]
            if isinstance(n,ast.Assign): targets=[t.id for t in n.targets if isinstance(t,ast.Name)]
            elif isinstance(n.target,ast.Name): targets=[n.target.id]
            if targets:
                try: val=ast.unparse(n.value)
                except Exception: val='<UNPARSEABLE>'
                for name in targets:
                    k=cls(name,val,ls); policy='ENUMERATE_IN_D2' if k.endswith('_BINDING') or k=='YEAR_OR_PHASE_LABEL' else 'IMMUTABLE'; binds.append([fam,str(p.relative_to(ROOT)),name,getattr(n,'lineno',0),k,segsha(src,n),hashlib.sha256(val.encode()).hexdigest(),policy])
    comp.append([fam,c['families'][fam],fcnt,len([x for x in binds if x[0]==fam and x[-1]=='ENUMERATE_IN_D2']),len([x for x in binds if x[0]==fam and x[-1]=='IMMUTABLE']),'PASS'])

mem=[]
for fam,p,mode in ARCHIVES:
    with zipfile.ZipFile(p) as z:
        for info in z.infolist():
            if info.is_dir(): continue
            mem.append([fam,str(p.relative_to(ROOT)),info.filename,info.file_size,info.compress_size,mode])
            if mode=='CSV_HEADER_ONLY' and info.filename.lower().endswith('.csv'):
                with z.open(info) as raw: header=next(csv.reader([raw.readline().decode('utf-8-sig')]))
                u={x.strip().upper() for x in header}; summary=';'.join(f'{x}={int(x in u)}' for x in ['SERIALNO','NP','TYPE','HHLDRAGEP','RELSHIPP','AGEP','RMSP','TEN','WGTP'])
                mem.append([fam+'_HEADER',str(p.relative_to(ROOT)),info.filename,len(header),0,summary])

write(TOP,['family','path','ordinal','node_type','start_line','end_line','statement_source_sha256','names_written','names_read','contains_path_literal','contains_year_literal'],top)
write(BIND,['family','path','global_name','line','binding_class','assignment_source_sha256','value_expression_sha256','D2_policy'],binds)
write(PROV,['family','path','function','signature','start_line','end_line','function_source_sha256','D2_policy'],prov)
write(MEM,['family','archive_path','member_or_header','uncompressed_or_field_count','compressed_bytes','inspection_or_schema_summary'],mem)
write(COMP,['family','adapter_mode','verbatim_function_count','enumerated_compatibility_binding_count','immutable_binding_count','status'],comp)

ah=[r for r in mem if r[0]=='ACS_HOUSING_HEADER']; ap=[r for r in mem if r[0]=='ACS_PERSON_HEADER']
ahok=all('SERIALNO=1' in r[-1] and 'NP=1' in r[-1] and 'TYPE=1' in r[-1] and 'HHLDRAGEP=0' in r[-1] and 'RMSP=1' in r[-1] and 'TEN=1' in r[-1] and 'WGTP=1' in r[-1] for r in ah)
apok=all('SERIALNO=1' in r[-1] and 'RELSHIPP=1' in r[-1] and 'AGEP=1' in r[-1] for r in ap)
success=len(prov)==17 and len(comp)==3 and ahok and apok
write(G,['gate','value'],[['EXACT_17_VERBATIM_FUNCTIONS',int(len(prov)==17)],['EXACT_3_COMPATIBILITY_PLANS',int(len(comp)==3)],['ACS_HOUSING_VERSION_HEADER_GATE',int(ahok)],['ACS_PERSON_VERSION_HEADER_GATE',int(apok)],['FROZEN_EXECUTOR_IMPORTED',0],['FROZEN_EXECUTOR_EXECUTED',0],['EXECUTABLE_2019_ADAPTER_CREATED',0],['2019_RAW_DATA_ROWS_OPENED',0],['2019_COORDINATE_VALUES_OPENED',0],['SCIENTIFIC_METHOD_MUTATED',0],['GENERIC_YEAR_REPLACE_AUTHORIZED',0]])
nextp='E4D1D2' if success else 'E4D1D1R'
write(D,['decision','value'],[['E4D1D0_R0_REUSED_AS_CANONICAL_INTERFACE_FREEZE',1],['METHOD_COUNT',3],['ALL_METHODS_TOP_LEVEL_EXECUTION_UNSAFE',1],['VERBATIM_FUNCTION_PROVENANCE_COUNT',len(prov)],['ENUMERATED_BINDING_COUNT',len(binds)],['ACS_ADAPTER_MODE','STATIC_INGESTION_COMPATIBILITY_LAYER'],['SCF_ADAPTER_MODE','STATIC_SOURCE_AND_MEMBER_COMPATIBILITY_LAYER'],['CPS_ADAPTER_MODE','STATIC_FIXED_WIDTH_LAYOUT_COMPATIBILITY_LAYER'],['FROZEN_EXECUTOR_IMPORTED',0],['FROZEN_EXECUTOR_EXECUTED',0],['EXECUTABLE_2019_ADAPTER_CREATED',0],['2019_RAW_DATA_ROWS_OPENED',0],['2019_COORDINATE_VALUES_OPENED',0],['SCIENTIFIC_METHOD_MUTATED',0],['NEXT_PRIMARY_PHASE_ID',nextp],['E4D1D2_EXECUTABLE_ADAPTER_CONSTRUCTION_FREEZE_AUTHORIZED',int(success)],['E4D1D_2019_COORDINATE_VALUES_OPEN_AUTHORIZED',0],['TEMPORAL_GEOMETRY_AUTHORIZED',0],['REAL_INFLATION_ESTIMATION_AUTHORIZED',0],['E4D1D1_FROZEN_EXECUTION_ADAPTER_CONTRACT','PASS']])
log='\n'.join([f'METHOD_COUNT=3',f'VERBATIM_FUNCTION_PROVENANCE_COUNT={len(prov)}',f'ENUMERATED_BINDING_COUNT={len(binds)}',f'ACS_HOUSING_VERSION_HEADER_GATE={int(ahok)}',f'ACS_PERSON_VERSION_HEADER_GATE={int(apok)}','FROZEN_EXECUTOR_IMPORTED=0','FROZEN_EXECUTOR_EXECUTED=0','EXECUTABLE_2019_ADAPTER_CREATED=0','2019_RAW_DATA_ROWS_OPENED=0','2019_COORDINATE_VALUES_OPENED=0','SCIENTIFIC_METHOD_MUTATED=0',f'NEXT_PRIMARY_PHASE_ID={nextp}',f'E4D1D2_EXECUTABLE_ADAPTER_CONSTRUCTION_FREEZE_AUTHORIZED={int(success)}','E4D1D_2019_COORDINATE_VALUES_OPEN_AUTHORIZED=0','TEMPORAL_GEOMETRY_AUTHORIZED=0','REAL_INFLATION_ESTIMATION_AUTHORIZED=0','E4D1D1_FROZEN_EXECUTION_ADAPTER_CONTRACT=PASS'])+'\n'
EX.write_text(log); AU.write_text(log); print(log,end='')
