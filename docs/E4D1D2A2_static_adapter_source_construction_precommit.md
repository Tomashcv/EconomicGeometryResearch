# E4D1D2A2 — static 2019 adapter source construction

A1 froze the exact 2019 targets. A2 may therefore write static adapter source, but not execute it.

SCF and CPS are generated from their frozen 2022 sources by exact AST-located changes to the already enumerated binding and member loci.

ACS uses the same mechanism for path/output bindings, then adds one ingestion-only schema bridge before the frozen 2022 H consumer. The adapter builds a SERIALNO-to-AGEP map from RELSHIPP=20 person records, filters housing rows to TYPE=1, injects HHLDRAGEP for occupied housing rows, and then feeds the original row accumulation loop. The accumulation suffix itself must remain byte-identical to the frozen source.

All 17 original functions retain exact source hashes. Generated adapters are compile-checked only; import or execution is prohibited.

No 2019 semantic row or coordinate value is opened in A2.
