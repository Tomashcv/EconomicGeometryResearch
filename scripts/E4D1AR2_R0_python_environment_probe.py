#!/usr/bin/env python3
from pathlib import Path
import csv, hashlib, sys
ROOT=Path(__file__).resolve().parents[1]
assert Path(sys.executable).resolve()==(ROOT/'.venv/bin/python').resolve()
assert sys.version.split()[0]=='3.12.3'
import pandas
import pandas.io.stata as stata_mod
from pandas.io.stata import StataReader

def h(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
py=Path(sys.executable).resolve(); pi=Path(pandas.__file__).resolve(); sm=Path(stata_mod.__file__).resolve()
rows=[
('python_executable',str(py)),('python_version',sys.version.split()[0]),('python_executable_sha256',h(py)),
('pandas_version',pandas.__version__),('pandas_init_path',str(pi)),('pandas_init_sha256',h(pi)),
('pandas_stata_module_path',str(sm)),('pandas_stata_module_sha256',h(sm)),('StataReader_import','PASS'),
('archive_member_listing_opened_during_probe','0'),('stata_schema_metadata_opened_during_probe','0'),('observation_rows_read_during_probe','0')]
out=ROOT/'data/metadata/E4D1AR2_R0_environment_fingerprint.tsv'
with out.open('w',encoding='utf-8',newline='') as f:
    w=csv.writer(f,delimiter='\t',lineterminator='\n'); w.writerow(['field','value']); w.writerows(rows)
print('VENV_PYTHON_VERSION='+sys.version.split()[0])
print('PANDAS_VERSION='+pandas.__version__)
print('STATAREADER_IMPORT=PASS')
