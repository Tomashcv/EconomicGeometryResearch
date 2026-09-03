# E4D1D2A2 R3 — official CPS 2019 static binding patch freeze

R2/R2F1 resolved the three remaining CPS static authorities and froze their exact official 2019 bytes. R3 applies the already-defined static repair surface to a new CPS adapter source without executing it.

The immutable parent is `scripts/E4D1D2A2_cps2019_i_adapter.py`. Exactly three top-level path bindings are changed: `CPS_SAS`, `PERSON_LAYOUT`, and `HOUSE_LAYOUT`. Exactly three linked 2022 SHA literals are changed to the exact R2-frozen 2019 authority SHAs. No other source span may differ.

All CPS function definitions must remain byte-identical to the parent adapter, preserving the frozen D1 scientific functions. ACS and SCF adapters remain byte-identical and are not rewritten.

R3 performs source/AST/hash/provenance validation only. It does not import or execute any adapter, does not open any 2019 semantic microdata row, and does not open any 2019 coordinate value.

A complete R3 PASS may authorize only the E4D1D3 coordinate-execution precommit. It does not itself authorize coordinate execution or value opening.
