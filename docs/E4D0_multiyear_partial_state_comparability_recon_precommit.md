# E4D0 — multiyear partial-state comparability reconnaissance

E4D0 starts the temporal branch without opening any additional-year economic values.

The current frozen numerical state is 2022 only. Its five numerical axes come from three survey families: ACS for H access, SCF for K and D, and CPS ASEC for the two I primary coordinates.

E4D0 performs only two local reconnaissance operations after this precommit:

1. enumerate repository path names and record survey-family/year tokens;
2. inspect static scripts, documentation, and contract JSON for survey-adjacent year references.

No file contents under raw or processed data are opened. No numeric result rows are opened. A year token in a path or source file is only a candidate reference; it is never treated as proof that the year's data are semantically or inferentially comparable.

Before any common temporal grid can be frozen, each candidate year must be verified against official evidence for variable definitions, survey universe, age/tenure mapping, transforms, weight/replicate design, nominal-price comparability where relevant, release vintage, and missing-year policy.

Because local static references are insufficient to prove those properties, E4D0 cannot authorize E4D1 directly. A PASS authorizes E4D0A: acquisition and pinning of official multiyear metadata/design evidence without opening microdata values.
