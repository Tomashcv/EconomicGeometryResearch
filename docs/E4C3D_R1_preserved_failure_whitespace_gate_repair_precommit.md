# E4C3D R1 — preserved-failure whitespace-gate repair

R0 correctly preserved the exact malformed TSV from Attempt 1, including its trailing tabs.

The R0 wrapper then ran `git diff --cached --check` on that intentionally malformed evidence artifact itself, causing a second packaging failure before any CSV member or ACS economic value was opened.

R1 changes no scientific code, estimator, raw source, or R0 canonical-manifest rebuild logic.

The byte-exact failed TSV is committed as evidence but is the only artifact excluded from whitespace lint. All other valid R0/R1 artifacts and the repaired canonical manifest must pass whitespace lint.

After the repaired source manifest is committed, the unchanged frozen E4C3D parser is allowed to open rows.

Primary H_ACCESS remains `RMSP / NP`.
