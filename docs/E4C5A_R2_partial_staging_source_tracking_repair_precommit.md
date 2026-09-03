# E4C5A R2 — partial-staging + source-tracking repair

## Why R1 stopped

Attempt 1 used one `git add` command for:

- the generated source manifest;
- the generated source-freeze audit;
- the official Federal Reserve macro.

Git staged the first two paths and then rejected the macro because `data/raw/scf` is covered by an existing ignore rule.

Therefore the failed command legitimately left a **partially staged index**.

R1 incorrectly required an empty index before proceeding and stopped.

## R2 repair

R2 verifies that the index contains exactly those two expected paths and that their staged bytes equal the already-frozen working bytes.

It then performs a targeted reset of exactly those two paths. This changes no file bytes.

After preserving Attempt 1, R0, and R1 failure provenance, R2 precommits a source-tracking-only repair.

The final source freeze:

- stages the two generated metadata files normally;
- force-stages the exact small `bulletin.macro.txt`;
- keeps the 2.2 MB SCF summary ZIP ignored and untracked;
- commits the source freeze before any summary CSV member is opened.

## Scientific parser

The original frozen E4C5A parser already matches the official SAS lexical spelling:

`PIR40=(PIRTOTAL>.4);`

No parser modification is needed or authorized.

K reference-scale estimation and D unit semantics remain exactly those frozen in the E4C5A scientific precommit.
