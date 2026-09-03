# E4D1D3 ACS R0 — first empirical execution harness

The E4D1D3 ACS P0 F3 precommit authorized exactly one value-opening scope: ACS H 2019.

R0 executes only the frozen canonical adapter `scripts/E4D1D3P1_acs2019_h_access_adapter.py`. No CPS or SCF executor is called.

The post-execution validator was frozen before values. It accepts the empirical run only on the structural gates already frozen by F3: exact output surface, fixed row cardinalities, required PASS flags, finite/positive denominator gates, and prohibition of outcome-direction/significance/magnitude/geometry gates.

If the adapter exits nonzero or the frozen validator fails, the attempt is preserved and the adapter must not be rerun before failure classification.
