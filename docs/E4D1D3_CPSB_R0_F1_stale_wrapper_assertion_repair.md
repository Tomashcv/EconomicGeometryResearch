# E4D1D3 CPSB R0 F1 — stale wrapper assertion repair

The first 2019 CPS full-weight bridge execution completed under the exact
precommitted executor. The exact precommitted post-execution validator then
returned PASS and recorded the runtime audit/summary hashes.

The orchestration shell subsequently exited non-zero only because an additional
wrapper invariant required the obsolete literal
`E4A2C_CPS_REPLICATE_ENGINE_PREFLIGHT_AUTHORIZED=1`.

The 2019 runtime audit truthfully emits
`E4D1D3_CPSP_PREDECESSOR_SHA_PATCH_AUTHORIZED=1` instead.

This F1 repair does not rerun the executor, reopen CPS raw data, parse any new
weight values, open CPS I, open SCF K/D, execute CPSP, or mutate scientific
method. The repair rule is fixed to the already-prefrozen validator outcome and
the exact already-produced runtime hashes.
