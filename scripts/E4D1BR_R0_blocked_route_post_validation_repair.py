#!/usr/bin/env python3
from pathlib import Path
import csv,hashlib,json
R=Path(__file__).resolve().parents[1]
H=R/'data/metadata/E4D1BR_R0_preserved_output_hash_lineage.tsv'
C=R/'data/results/E4D1BR_acs_required_column_recovery_registry.tsv'
S=R/'data/results/E4D1BR_2019_schema_audit_registry.tsv'
G=R/'data/results/E4D1BR_schema_repair_hard_gates.tsv'
D=R/'data/results/E4D1BR_acs_column_discovery_schema_repair_decision.tsv'
A=R/'data/metadata/E4D1BR_R0_blocked_route_post_validation_repair_audit.txt'
O=R/'data/results/E4D1BR_R0_blocked_route_post_validation_repair_decision.tsv'
def rd(p):
    with p.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f,delimiter='\t'))
for r in rd(H):
    p=R/r['artifact']; assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']
cols=rd(C); sch=rd(S)
with G.open(newline='',encoding='utf-8') as f:g={r['gate']:r['value'] for r in csv.DictReader(f,delimiter='\t')}
with D.open(newline='',encoding='utf-8') as f:d={r['decision']:r['value'] for r in csv.DictReader(f,delimiter='\t')}
assert len(cols)==83 and sum(r['role_class']=='WEIGHT' for r in cols)==81
assert {r['column'] for r in cols if r['role_class']!='WEIGHT'}=={'HHLDRAGEP','TEN'}
assert len(sch)==6 and sch[0]['status']=='FAIL' and all(r['status']=='PASS' for r in sch[1:])
assert g['ACS_COLUMN_RECOVERY_SUFFICIENT']=='0' and g['ALL_SCHEMA_GATES_PASS']=='0'
assert d['SCHEMA_AUDIT_STATUS']=='BLOCKED' and d['NEXT_PRIMARY_PHASE_ID']=='E4D1BR1'
assert d['E4D1C_2019_COORDINATE_EXECUTION_PRECOMMIT_AUTHORIZED']=='0'
assert d['E4D1BR1_TARGETED_SCHEMA_FORENSIC_AUTHORIZED']=='1'
rows=[
('E4D1BR_FAILURE_PRESERVED_BEFORE_R0','1'),('E4D1BR_R0_REPAIR_SCOPE','POST_EXECUTION_VALIDATION_ONLY'),
('E4D1BR_SCIENTIFIC_EXECUTOR_REEXECUTED','0'),('REDOWNLOADED_ARTIFACT_COUNT','0'),
('PRESERVED_OUTPUT_BYTE_IMMUTABILITY','PASS'),('ACS_RECOVERED_TOTAL_COLUMN_COUNT','83'),
('ACS_RECOVERED_WEIGHT_COLUMN_COUNT','81'),('ACS_RECOVERED_NON_WEIGHT_COLUMN_COUNT','2'),
('ACS_RECOVERED_NON_WEIGHT_COLUMNS','HHLDRAGEP|TEN'),('ACS_COLUMN_RECOVERY_STATUS','UNRESOLVED'),
('ACS_SCHEMA_AUDIT_STATUS','FAIL'),('SCF_SCHEMA_AUDIT_STATUS','PASS'),('CPS_CONTAINER_AUDIT_STATUS','PASS'),
('SCHEMA_AUDIT_STATUS','BLOCKED'),('2019_ECONOMIC_VALUES_OPENED','0'),('NEXT_PRIMARY_PHASE_ID','E4D1BR1'),
('E4D1C_2019_COORDINATE_EXECUTION_PRECOMMIT_AUTHORIZED','0'),('E4D1BR1_TARGETED_SCHEMA_FORENSIC_AUTHORIZED','1'),
('TEMPORAL_GEOMETRY_AUTHORIZED','0'),('REAL_INFLATION_ESTIMATION_AUTHORIZED','0'),
('E4D1BR_R0_BLOCKED_ROUTE_POST_VALIDATION_REPAIR','PASS')]
log='\n'.join(f'{k}={v}' for k,v in rows)+'\n'; A.write_text(log,encoding='utf-8')
with O.open('w',newline='',encoding='utf-8') as f:
    w=csv.writer(f,delimiter='\t',lineterminator='\n'); w.writerow(['decision','value']); w.writerows(rows)
print(log,end='')
