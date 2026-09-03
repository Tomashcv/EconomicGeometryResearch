# E4D1BR2B — 2019 ACS person source acquisition and header-only schema audit

E4D1BR2A froze and semantically validated a single versioned bridge for the missing 2019 housing field HHLDRAGEP: obtain the age of the reference person from the ACS person PUMS and join it to the housing record by SERIALNO.

E4D1BR2B freezes the exact official person-source acquisition and schema rules before downloading any person microdata.

The source is exactly the official 2019 1-year national person CSV archive `csv_pus.zip`. The archive must not already exist before this precommit and is downloaded exactly once afterward to the already ignored destination.

This phase is header-only. It may list ZIP members and read only the first CSV record as a header. Every CSV member must contain exactly the three bridge fields required by the already frozen policy:
- `SERIALNO`: housing/person join key;
- `RELSHIPP`: relationship/reference-person role field;
- `AGEP`: age field.

No alternative token is eligible. Person weights are not part of the bridge and may not replace the frozen housing weight architecture `WGTP/WGTP1..WGTP80`.

A header pass does not validate the crucial row-level linkage assumptions. In particular, it does not prove that reference-person code 20 is present as expected, that there is exactly one reference person per eligible housing key, that every estimator-eligible housing row links, or that the join cannot duplicate housing weights.

Therefore a successful E4D1BR2B authorizes only E4D1BR2C, a separately precommitted structural linkage audit. E4D1C coordinate execution remains prohibited.
