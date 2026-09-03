# E4D1D3P1 — static provenance repair precommit

P0 froze the complete pre-value execution order and authorized P1 as a static-only provenance repair layer.

## ACS

P1 replaces the inherited 2022 ACS archive manifest with the frozen E4D1B 2019 authority. The future adapter must require the exact 2019 housing archive identity: candidate `ACS_2019_NATIONAL_HOUSING_CSV`, local path `data/raw/acs/2019/1year/csv_hus.zip`, SHA256 `82b1b11747a1259698db0254af0a8ca3064f83c22b028377d0f93e46f01c27e7`, bytes `236656453`.

The historical method selected exactly `psam_husa.csv` and `psam_husb.csv`. P1 freezes those two basenames literally before any 2019 values are observed. Future execution may verify those exact members exist, but may not discover or substitute alternatives.

ACS metadata writes move to `data/metadata/E4D1D_2019_runtime/ACS`, and historical 2022 execution/value-open labels are replaced with truthful 2019 labels. Scientific result paths and every function body remain unchanged.

## CPS and SCF

P1 creates only two byte-identical static method-authority mirrors: E4A2C into CPS_ASEC runtime metadata and E4A2A into SCF runtime metadata. No empirical predecessor audit is copied.

P1 itself opens no raw rows or coordinate values and executes no adapter. Success authorizes only preparation of the ACS 2019 H-access execution precommit.
