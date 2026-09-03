# E4D1BR2CR — TYPEHUGQ structural-universe forensic and conditional repair

E4D1BR2C produced a valid blocked result. The versioned HHLDRAGEP bridge has unique reference-person keys, no duplicate amplification, no orphan reference-person keys, and valid reference-person ages, but the precommitted structural universe `NP>0` contains 151,321 housing records with no `RELSHIPP=20` reference person.

Before opening any new housing field, E4D1BR2CR freezes one exact hypothesis: the `NP>0` rule unintentionally includes group-quarters placeholder housing records.

The only eligible discriminator is `TYPEHUGQ`. Official 2019 ACS documentation must establish:
- `TYPEHUGQ=1`: housing unit;
- `TYPEHUGQ=2`: institutional group quarters;
- `TYPEHUGQ=3`: noninstitutional group quarters;
- `NP>0` can describe a person associated with a group-quarters record.

The only eligible repaired structural universe is frozen before row values:
`TYPEHUGQ=1 AND NP>0`.

This phase may retain only `SERIALNO`, `NP`, and `TYPEHUGQ` from housing and `SERIALNO`, `RELSHIPP` from person records. It does not retain or interpret RMSP, TEN, housing weights, replicate weights, or AGEP.

Success requires the complete prior coverage gap to be explained structurally: every prior missing-reference record must be group quarters, zero occupied `TYPEHUGQ=1` housing units may lack a reference person, and every occupied housing unit must have exactly one reference person.

Only a full precommitted success may validate the versioned bridge and authorize E4D1C.
