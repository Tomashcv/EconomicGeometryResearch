# E4C2B R1 — Frozen lineage TSV literal-tab serialization repair

## Failure classification

The E4C2B R0 transport repair successfully acquired and validated the three
official BLS XLSX metadata packages. The frozen E4C2B audit then failed before
concordance/category parsing with `KeyError: 'artifact'`.

The cause is serialization-only: `E4C2B_frozen_input_lineage.tsv` was committed
with eight literal `\t` character pairs rather than eight actual tab bytes.
The frozen audit correctly reads TSV with `delimiter="\t"`, so the entire header
was interpreted as one field.

`SCIENTIFIC_FAILURE = NO`.

## Repair boundary

Only the serialization of the already-predeclared three lineage rows changes.

- before SHA-256:
  `813f9b8838e096548b42d982334234be8dbd5956879716d2be31f31e27d79898`
- after SHA-256:
  `a07494f85081d3be52c3d82f8e4e5843c3aac297c2b32b0fb03e26c1e6e8bfee`
- semantic lineage rows changed: **NO**
- frozen scientific Python audit changed: **NO**
- source selection changed: **NO**
- estimator changed: **NO**
- official metadata redownloaded: **NO**

## Preserved official metadata

The already-acquired R0 XLSX bytes are frozen before the audit resumes:

- CE↔CPI 2022 concordance:
  `e9c01b9cca48b5d0210a4d549e5a71c2548a2df47d37fc0810d9420001461f16`
- CPI publication-level metadata:
  `9011d21ad9255153e75d8e689908490eca00df0eed71222c7af3e2011e9ddc93`
- CE↔PCE concordance:
  `cdca67e45885a533881b011957481fd988a7e1c321a77e9fbbda9f79a0680463`

R0 execution SHA-256: `c5711d13d7230bc0adddb16a3f44a3ecbda3f9434816c72cf0f1ff44cd41eb9b`

R0 source-manifest SHA-256: `de2efd02e09c416d6a3e1e5091089915a54278e77fd928dcd31c11329f994445`

## Chronology

This R1 repair is committed and pushed before rerunning the unchanged E4C2B
scientific metadata audit. No CPI index values, PCE expenditure values,
coordinate values, transformed values, or geometry are authorized here.

If the unchanged audit fails again, the new failure is preserved and no
scientific mutation is performed.
