# E4D1A — 2019 official source lineage + acquisition preflight

E4D1A resolves exact 2019 official source URLs and schema roles before any 2019 microdata or replicate-weight values are downloaded.

The candidate universe is frozen before reading the frozen 2022 executor text or acquiring the one missing official metadata index. Candidates are restricted to official Census and Federal Reserve endpoints already structurally identified from official release/directory pages.

Resolution is lineage-based, not filename-guess based. The frozen 2022 H/K/D/I implementation determines which source family is required; the corresponding 2019 file is eligible only when the official 2019 release/directory metadata confirms the exact file.

ACS may resolve to the national housing CSV, national person CSV, or both, but only if the frozen 2022 H implementation structurally requires those source families. SCF summary-extract vs full-public choice is not made by convenience: the frozen 2022 K/D source family controls. The official Stata replicate-weight source remains separate. CPS ASEC public-use and replicate-weight sources must match the exact 2019 release-page entries and frozen 160-replicate layout.

E4D1A may acquire only the ACS 2019 directory-index HTML after its precommit. It may not download microdata, public-use data archives, SCF data, or replicate-weight data.

If all six E4D1 source requirements resolve, E4D1B becomes authorized to precommit and then acquire the exact selected bytes for a schema-only audit. Otherwise E4D1AR forensic is the only authorized route.
