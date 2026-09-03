# E4D1BR2A — ACS 2019 householder-age versioned bridge preflight

E4D1BR2 established that the complete 2019 housing header differs from 2022 in exactly one frozen required field: `HHLDRAGEP`. Both 2019 national housing members have identical headers, all frozen housing weights and the H numerator/denominator fields are present, and no source or schema mutation has occurred.

E4D1BR2A freezes a single candidate bridge before opening new official evidence: reconstruct the 2019 householder-age field from the 2019 person file by selecting the reference person and joining that person's age to the housing record by `SERIALNO`.

The candidate is intentionally exact:
- housing/person merge key: `SERIALNO`;
- person role field: `RELSHIPP`;
- reference-person code: `20`;
- age field: `AGEP`;
- derived householder age: `AGEP` from exactly one `RELSHIPP=20` record for the housing `SERIALNO`;
- H numerator/denominator remain `RMSP/NP`;
- tenure remains `TEN`;
- housing point and replicate weights remain `WGTP` and `WGTP1..WGTP80`;
- person weights are prohibited for the housing estimand.

The bridge is only eligible if official documentation proves all semantic pieces. Two new official documents are acquired only after this precommit: the 2021 PUMS variable-change documentation and the Census PUMS handbook. Existing frozen 2019 README, dictionary, AGEP metadata, and directory index are reused.

This phase does not download the 2019 person archive and does not inspect any microdata row. It also does not assume uniqueness or completeness of the reference-person linkage. Those are deferred hard gates.

A successful E4D1BR2A therefore does not make ACS PASS and does not authorize E4D1C. It authorizes only E4D1BR2B, which may acquire the exact official 2019 person archive after its own precommit and perform a schema-only audit.
