# E4D0A R0 — SCF change-document sentinel validation repair

The E4D0A precommit at `b1ba5391592d0f6f8478fe448c3960688361c431` froze 25 official documentation targets before download.

All 25 downloads completed. The original validator then rejected the 2019 SCF change document because its body did not contain the literal string `2019`. A full forensic pass over all 25 already-downloaded artifacts established exactly two failures of that same validation assumption:

- `SCF_2019_CHANGES`
- `SCF_2022_CHANGES`

The exact downloaded bundle and forensic classification were preserved before this repair at:

`29be2d5b82917c4fae29c1878a6dc3b99edbb3c9`

No URL or downloaded byte is changed and no file is re-downloaded.

The repair changes only artifact-identity validation for those two official SCF change-document TXT files. Instead of requiring the year to be repeated inside the body, identity is established by:

1. nonempty text-file structure;
2. the already-downloaded official SCF release page containing the exact label `Changes for YEAR`;
3. the same release page containing the exact year-specific filename.

All other 23 artifacts retain the original PDF-magic or precommitted text-sentinel validation unchanged.

This repair does not adjudicate 2019↔2022 comparability and does not authorize microdata, additional-year economic values, a common year grid, temporal geometry, or real inflation estimation.
