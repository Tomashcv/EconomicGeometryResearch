# E4D1D2A2 R2F1 — post-execution validator repair

R2 completed its static authority acquisition/verifier stage and produced six output artifacts before the wrapper's post-execution validator failed.

R2F0 preserved those exact outputs and classified the failure. R2F1 does not redownload or rerun the verifier. It validates only the already-frozen R2 artifacts.

The repaired success criterion is frozen before validation: exactly three official authority rows must pass, with exact basename/non-HTML/static-role checks and exact local-byte SHA identities. The already-produced R2 decision must report zero unresolved authorities and route to E4D1D2A2R3 while keeping coordinate execution closed.

No parent R2 output, adapter source, scientific method, 2019 data row, or coordinate value may change.
