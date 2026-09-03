# E4D1D3 CPSP R0 F1 — wrapper static-token assertion repair

The first CPSP R0 wrapper stopped before patcher execution because its static
boundary check prohibited the substring `PWWGT1` anywhere in the frozen patcher
source. That lexical rule is too broad: a field-name token may appear in
zero-state/provenance metadata without implying raw-data access or value parsing.

This is a wrapper-validation failure, not a scientific gate failure and not a
failure of the prefrozen CPSP patch algorithm.

F1 therefore preserves the failed attempt and changes only the wrapper proof:
the exact prefrozen patcher SHA remains mandatory; its authorized file bindings
are inspected structurally; the patch algorithm must still be exactly one
`src.replace(OLD,new,1)`; raw CPS data paths remain absent; and the produced
adapter must equal the precomputed byte-exact output SHA with all scientific
function source hashes unchanged.

No patcher source, adapter function, empirical method, or value-open scope is
changed by F1.
