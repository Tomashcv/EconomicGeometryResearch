# E4D1BR2 — ACS 2019 header differential forensic

E4D1BR1 proved the frozen H-access lineage for RMSP and NP from pre-existing E4D0B1 authorities and confirmed that the complete 85-field requirement is present in every frozen 2022 ACS housing header. The same all-member gate failed for the downloaded 2019 housing archive.

E4D1BR2 does not repair, remap, substitute, or reselect anything. It freezes a pure header-differential forensic before opening the detailed 2019 header mismatch.

The exact required set is fixed at:
- RMSP, NP, HHLDRAGEP, TEN;
- WGTP;
- WGTP1 through WGTP80.

For every 2019 and 2022 CSV member, E4D1BR2 records header size, header hash, exact missing required tokens, and target-field presence. It also records per-token presence counts and whether all 2019 members share the same missing set.

Routing is deterministic:
- no actual mismatch -> implementation forensic;
- heterogeneous member missing sets -> member-role/container forensic;
- weight-only mismatch -> weight-schema forensic;
- substantive-only mismatch -> variable/source-version forensic;
- mixed mismatch -> mixed forensic.

No branch authorizes E4D1C. A later phase may change schema status only after the exact mismatch has been classified under a separately precommitted repair rule.
