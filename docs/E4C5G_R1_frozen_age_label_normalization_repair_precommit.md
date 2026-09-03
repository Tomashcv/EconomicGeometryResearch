# E4C5G R1 — frozen age-label normalization repair

E4C5G attempt 1 failed because its literal age parser expected canonical labels such as `25-34`, while the frozen E4A2F sources encode the same cohorts with labels such as `AGE25_34`.

R0 proved this categorically: all 16 target statistic rows are present, exact literal age matching retains zero, and the earlier broad semantic age parser retains all 16. No numerical outcome value was used.

Before R1 is written, the same broad age semantics are validated across the combined, implicate, and replicate sources using categorical identifiers only. Required shapes are 16 combined cells, 80 implicate rows, and 15,984 replicate rows.

R1 changes only age-label normalization. Tenure semantics, primary statistic IDs, K/D transforms, pooled-point definition, E4A2E variance engine, domain gates, and geometry boundaries remain unchanged.
