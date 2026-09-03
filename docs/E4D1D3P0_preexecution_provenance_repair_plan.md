# E4D1D3P0 — pre-execution provenance repair plan

R3 successfully produced the three 2019-bound adapter sources without opening values. A0/A1/A2 static forensics then exposed runtime-provenance gaps that must be resolved before any top-level adapter is executed.

The repair is staged because some predecessor audits are genuinely empirical. Their future SHA256 values cannot be known before their 2019 executions, but the rule for consuming those SHAs can and must be frozen now.

## ACS

The 2019 adapter still reads the historical `E4C3D_acs2022_microdata_manifest.tsv`. That manifest was created specifically for the 2022 archive and is not a valid authority for the rebound 2019 archive. P1 must replace only this ingestion/provenance validation with an exact lookup of the already-frozen `E4D1B_2019_official_data_manifest.tsv` row for `data/raw/acs/2019/1year/csv_hus.zip`, checking local path, SHA256 and byte count before opening CSV member bytes.

ACS also still writes two historical E4C3D metadata files outside the 2019 runtime namespace. P1 must redirect those writes under `data/metadata/E4D1D_2019_runtime/ACS/` and make their value-open labels truthfully identify 2019. The frozen estimator functions and accumulation suffix remain unchanged.

## CPS

The full-weight bridge is empirical. The 2022 E4A2B audit cannot be copied and relabeled. A 2019 bridge must execute first under its own precommit, opening only the exact weight-side fields already frozen by method.

The E4A2C replicate engine audit is synthetic/static and may be mirrored byte-identically as a method authority. It is not 2019 empirical evidence.

Only after the 2019 bridge audit is frozen may the CPS adapter receive the exact predecessor-audit SHA automatically. This patch is precommitted now and cannot depend on I outcomes.

## SCF

The E4A2A replicate schema/design audit is static and may be mirrored as method authority because 2019 structural compatibility has already been separately frozen by E4D1BR.

The CPS predecessor audit is cross-family and must be consumed from the CPS_ASEC runtime namespace.

The E4A2E engine preflight cannot be copied from 2022 because it is chained to the empirical CPS predecessor. It must be rerun after the 2019 CPS PASS using the frozen synthetic engine rules. Only then may the SCF adapter bind the newly frozen predecessor SHAs.

## Outcome independence

No result sign, magnitude, significance, hypothesis agreement or economic interpretation can modify the chain. Any empirical predecessor failure stops the sequence and is preserved.

P0 opens no raw rows and no coordinate values. It authorizes only construction of the static P1 repair layer.
