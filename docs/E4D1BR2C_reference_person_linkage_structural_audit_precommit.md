# E4D1BR2C — ACS 2019 reference-person linkage structural audit (R0-repaired precommit)

E4D1BR2A froze and officially supported the 2019 versioned bridge for HHLDRAGEP. E4D1BR2B acquired the official 2019 person archive after precommit and verified the required person schema.

The first E4D1BR2C wrapper failed before commit and before any row read because a source-substring validator incorrectly treated the diagnostic label `HOUSING_RMSP_OPENED=0` as evidence of prohibited RMSP access.

R0 preserves that failed attempt by hash and replaces the validator with projection-aware AST checks. R0 also narrows the parser: it no longer uses `csv.DictReader`, which materializes every column. A selective RFC4180 scanner retains only the frozen structural fields.

Housing retained fields:
- SERIALNO;
- NP, solely to define occupied housing as NP>0.

Person retained fields:
- SERIALNO;
- RELSHIPP, solely to select code 20;
- AGEP, solely to validate selected reference-person age.

No H coordinate, weighted estimate, age-band count, temporal geometry, or real-inflation statistic is computed.

The structural bridge passes only if housing keys are unique, code 20 is observed, each occupied housing key has exactly one reference person, no linkage can duplicate a housing record, and selected reference-person ages are present and integer-parseable.

Only a full structural pass maps ACS to VERSIONED_PASS and authorizes E4D1C.
