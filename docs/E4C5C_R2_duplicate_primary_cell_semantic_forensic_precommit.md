# E4C5C R2 — duplicate primary-cell semantic forensic

The R1 header repair succeeded and both source schemas were committed before target values were opened.

The first target-row pass then stopped on:

`duplicate primary point cell: ('K', '25-34', 'OWNER')`

That failure is now post-value-open and has already been preserved in Git.

R2 is diagnostic only. It does not repair the parser and does not alter FIN, PIRTOTAL, the K reference, the D sign, or the cohort universe.

The forensic deliberately bases its diagnosis on categorical row semantics rather than the numerical outcomes.

For the point table it inspects:

- age and tenure identifiers;
- `statistic_id`;
- `dimension`;
- `role`;
- `raw_variable`;
- `statistic`;
- `state_sign`;
- implicate/replicate structural counts.

It does not use point estimates, variances, standard errors, or confidence information to choose a rule.

For the replicate table it inventories `statistic_type`, `statistic_id`, age/tenure labels, and replicate identifiers without using `raw_value` or `state_oriented_value` to choose semantics.

The key question is whether the broad R1 classifier produced duplicates because it searched every non-structural field for FIN/PIRTOTAL strings, while the source already contains a more exact frozen semantic key such as `raw_variable == FIN` and `raw_variable == PIRTOTAL`.

No repair is authorized by R2 itself. Any repair must be precommitted after this forensic is frozen.
