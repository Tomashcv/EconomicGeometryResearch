# E4D1D2 R1 — D1 binding line-column accessor repair

The R0-repaired E4D1D2 precommit was successfully frozen at `e9c855d2024171355b6600ad1f271bbbb11a61dd`. The subsequent source/container-metadata-only executor failed before writing any D2 result artifact because it requested the nonexistent D1 binding-registry column `start_line`.

The canonical frozen D1 binding registry uses `line` as its line-location column. This is a plumbing/schema mismatch in a previously generated metadata registry, not a scientific incompatibility.

The failed post-precommit execution is preserved before this repair. R1 creates a new executor from the exact precommitted D2 script and changes exactly one accessor:
`r["start_line"]` -> `r["line"]`.

No D1 result, frozen function, adapter architecture, source/member rule, scientific definition, 2019 raw row, or coordinate value is changed or opened.

R1 then resumes the original D2 locus freeze. Any subsequent failure is preserved rather than triggering another blind mutation.
