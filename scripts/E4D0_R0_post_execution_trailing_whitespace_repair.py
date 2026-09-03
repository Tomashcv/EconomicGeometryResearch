#!/usr/bin/env python3
from pathlib import Path
import hashlib

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"data/results/E4D0_multiyear_partial_state_comparability_decision.tsv"

EXPECTED_SHA="44a9ca8b76e035d75f2d73f93362585df45834a7d087cb23f24db383e9a7a98f"
b=P.read_bytes()
assert hashlib.sha256(b).hexdigest()==EXPECTED_SHA

old=b"COMMON_ADDITIONAL_YEAR_REFERENCES\t\n"
new=b"COMMON_ADDITIONAL_YEAR_REFERENCES\tNONE\n"

assert b.count(old)==1
assert b.count(new)==0

repaired=b.replace(old,new,1)

# No byte other than the exact terminal empty-field representation is changed.
assert len(repaired)==len(b)+4
assert repaired.replace(new,old,1)==b

P.write_bytes(repaired)
print("E4D0_R0_EXACT_ONE_FIELD_SERIALIZATION_REPAIR=PASS")
print("E4D0_RECON_REEXECUTED=0")
print("E4D0_FILESYSTEM_RESCANNED=0")
print("E4D0_STATIC_TEXT_RESCANNED=0")
print("E4D0_SCIENTIFIC_METHOD_MUTATED=0")
