# E4C5C — first K/D transform execution

E4C5B froze a 15-file target source pool without reading target numerical values.

All semantic role hints were unresolved, so E4C5C does **not** infer the primary source from observed values.

Before opening values it selects the two exact E4A2F SCF K/D artifacts whose filenames encode their role:

- `E4A2F_2022_scf_kd_cohort_inference.tsv` for frozen cohort point inference;
- `E4A2F_2022_scf_kd_replicate_statistics.tsv` for replicate-architecture inventory.

Both files were already SHA-256 frozen in E4C5B.

## Additional schema barrier

Because E4C5B intentionally did not parse file contents, E4C5C adds one more barrier.

After the scientific precommit, it opens only the first header line of each TSV, freezes the exact headers and resolved structural columns, commits that schema, and only then opens data rows.

No economic target value is read during header freeze.

## Primary row selection

K primary rows must identify `FIN` / `K_FIN`.

D primary rows must identify `PIRTOTAL`.

`LIQ`, `EQUITY`, `RETQLIQ`, and `DEBT2INC` remain sensitivities and may not replace the primary based on observed outcomes.

The required primary universe is 8 K cells and 8 D cells across the four frozen age bands and OWNER/RENTER.

## Transform

`K_STATE = ln(1 + K_FIN_MEAN / 38640)`

`D_STATE = -PIRTOTAL_MEAN`

Both are higher-is-better and dimensionless.

## Replicates

E4C5C only inventories the primary K/D replicate architecture. It does not transform replicate estimates and does not produce transformed standard errors or confidence intervals.

That requires a new precommit after the actual frozen replicate structure is known.

No cross-coordinate metric scale or geometry is authorized.
