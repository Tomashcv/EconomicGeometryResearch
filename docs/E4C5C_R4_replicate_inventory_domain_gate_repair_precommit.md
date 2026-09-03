# E4C5C R4 — replicate-inventory domain-gate repair

R3 correctly repaired primary row selection using frozen categorical semantics and then resumed execution.

The point estimates passed the already-frozen K/D transforms. The run later stopped while inventorying primary K replicate rows because one raw replicate estimate was negative.

That stop was caused by an implementation gate that is inconsistent with the frozen E4C5C scope.

E4C5C explicitly says that replicate handling is inventory-only, transformed replicate values are not computed, and transformed uncertainty is not computed. Therefore E4C5C should not apply the K log-transform domain requirement to raw replicate estimates.

R4 removes only the K-replicate nonnegativity check from the inventory loop. The raw replicate value must still be finite.

The K point-estimate domain gate remains unchanged. The K point transform, D transform, FIN/PIRTOTAL primary semantics, source headers, and all outcome gates remain unchanged.

The negative replicate observed in R3 remains preserved as failure evidence. Its numerical magnitude is not used to choose a replacement transform or uncertainty method.

E4C5D must separately precommit and audit replicate log-domain feasibility before any transformed-replicate inference is attempted. If some replicates are outside that domain, E4C5D must select a defensible uncertainty procedure without retroactively mutating the already-frozen point transform.
