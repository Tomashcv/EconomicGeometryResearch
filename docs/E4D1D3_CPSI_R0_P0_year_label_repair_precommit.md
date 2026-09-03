# E4D1D3 CPSI R0 P0 — direct-adapter 2019 year-label repair precommit

The canonical 2019 CPS I adapter contains exactly five internal row-level
`year=2022` values at lines 1280, 1347, 1372, 1471, and 1500.

Prior P0 attempts failed only in wrapper/report validation before any repository
write, repair execution, adapter execution, raw CPS opening, PWWGT1..160 opening,
or I-value opening. Their file identities are preserved for provenance, but F4
does not use their source semantics as repair authority.

The repair authority is now only:

1. canonical CPS I adapter SHA256 `556b5ae5076b319f45b1bd2261c34193833b1eb45916183c7adae1615c09a7ca`;
2. final A1 static forensic SHA256 `2f94b46b573554350e4f94f111f3dd6364ddd4732a24b84689db34b5a654bc3d`;
3. an independent AST + exact source-diff proof over the canonical adapter.

That proof freezes exactly:
- 5 changed AST loci;
- 5 changed lines;
- 10 changed characters;
- only `"year": 2022` -> `"year": 2019`;
- 6/6 top-level function hashes unchanged;
- all four legacy `E4A2D_2022_...` basenames unchanged;
- expected repaired adapter SHA256 `76acc152a2e122570cab00ac03110763d8e55d8ae8134e65c7206986cecb81d7`.

This precommit does not execute the repair patcher and does not open empirical CPS I values.
