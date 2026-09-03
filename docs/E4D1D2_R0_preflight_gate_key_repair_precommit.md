# E4D1D2 R0 — pre-precommit D1 gate-key reference repair

The first E4D1D2 wrapper failed before writing or committing any D2 precommit artifact. It attempted to read the nonexistent D1 gate key `EXACT_17_VERBATIM_FUNCTION_PROVENANCE_ROWS`.

The frozen D1 gate registry uses `EXACT_17_VERBATIM_FUNCTIONS=1`, while the frozen D1 decision independently records `VERBATIM_FUNCTION_PROVENANCE_COUNT=17` and authorizes E4D1D2.

R0 changes only this static preflight reference. It does not change D1, the 17 function hashes, the 218 frozen bindings, any 2019 source, any adapter rule, or any scientific definition.

Because the failure occurred before any repository mutation, R0 preserves the exact failed wrapper SHA and canonical D1 gate/decision hashes in the repaired D2 precommit itself, then resumes the already designed D2 source/container-metadata-only freeze.
