# E4D1B — 2019 official source acquisition and schema-only audit

E4D1AR2/R0 resolved all six 2019 source-lineage requirements. The SCF estimator is jointly sourced: the Summary Extract supplies FIN/PIRTOTAL while the Full Public file supplies X42001/structural information, with Y1-compatible merge lineage.

E4D1B freezes the exact six official data URLs and local destinations before any download. Raw files must live under git-ignored paths and are never committed to Git; only URL/SHA256/byte manifests and schema evidence are committed.

After precommit, E4D1B may download exactly those six artifacts. It may inspect ZIP member names, CSV headers, and Stata variable metadata. It may not parse any ACS CSV data row, Stata observation row, CPS ASCII record, numeric result row, or 2019 economic statistic.

The ACS schema gate derives required field names from the frozen 2022 H executor and the frozen 2022 housing-source header, then requires those fields in every 2019 housing CSV member. This avoids guessing AGEP versus householder-age source tokens.

The SCF gate is role-specific and precommitted: Summary must expose FIN/PIRTOTAL/Y1; Full must expose X42001/Y1; replicate metadata must expose Y1 plus exactly 999 WT1B* and 999 MM* fields.

CPS public/replicate archives are audited at container/member level only. Their variable/layout semantics remain governed by the already-frozen 2019 official dictionary/SAS-layout evidence; no ASCII data line is opened in E4D1B.

A successful E4D1B freezes the six downloaded byte identities and authorizes E4D1C, a separate precommit for row parsers/estimators. It does not authorize opening 2019 economic values by itself.
