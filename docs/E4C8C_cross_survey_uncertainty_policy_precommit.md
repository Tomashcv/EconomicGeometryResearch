# E4C8C — cross-survey uncertainty policy precommit

E4C8B identified 16 within-survey covariance cells but the eight cross-survey off-diagonals of each 5×5 sampling covariance matrix remain unidentified from the current unlinked survey architecture.

E4C8C does not replace those unknown entries with zero. The canonical policy is set identification.

For each age×tenure cell, define the feasible covariance set U1 as every symmetric positive-semidefinite 5×5 matrix Sigma satisfying the frozen known entries:

- all five diagonal marginal sampling variances are fixed to exact `se_state^2` from E4C6E;
- the SCF K-D covariance is fixed to E4C8B;
- the CPS I_FYFT-I_SEARCH_SECURITY covariance is fixed to E4C8B;
- the remaining eight cross-survey off-diagonals are unknown and free subject only to the fixed entries and positive semidefiniteness.

No arbitrary correlation cap narrower than what PSD already implies is introduced. No "best" completion, data-fit completion, nearest-PSD projection, or silent zero completion is authorized.

A block-diagonal matrix that sets all eight unknown cross-survey entries to zero is mandatory only as a named noncanonical sensitivity S1, and only if that matrix is itself PSD. Its use must never be described as evidence that the surveys or economic concepts are independent.

A covariance-sensitive downstream qualitative claim is robust only when it holds across the entire feasible U1 set. If a result holds only under S1, it must be labeled zero-cross-survey sensitivity.

If U1 is empty for any cell, execution halts for forensic review. No clipping, projection, or formula mutation is allowed automatically.

E4C8C is structural only. It does not open numeric covariance or marginal-SE rows and does not authorize geometry.
