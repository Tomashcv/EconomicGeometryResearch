# E4C5C R3 — exact primary statistic-id repair

R1 was the first E4C5C attempt to open target K/D values. It stopped on a duplicate K cell and preserved that failure before any repair.

R2 then froze a categorical semantic forensic without using numerical outcomes to choose a repair rule.

The forensic showed that each K target cell contains both a primary mean row and a robustness median row, and both use `raw_variable = FIN`. Therefore FIN alone is not a unique primary key.

The frozen categorical primary K signature is:

- `statistic_id = K_FIN_MEAN`
- `dimension = K`
- `role = PRIMARY`
- `raw_variable = FIN`
- `statistic = MEAN`

The frozen categorical primary D signature is:

- `statistic_id = D_PIRTOTAL_MEAN`
- `dimension = D`
- `role = PRIMARY`
- `raw_variable = PIRTOTAL`
- `statistic = MEAN`

The repair is semantic, not outcome-dependent. Direction, magnitude, significance, and transformed values are not used to choose these rows.

Replicate inventory uses the same exact primary statistic IDs. Existing age/tenure mapping continues to exclude contrast rows.

The transforms remain unchanged:

`K_STATE = ln(1 + K_FIN_MEAN / 38640)`

`D_STATE = -PIRTOTAL_MEAN`

Transformed replicate inference remains deferred to E4C5D. No cross-coordinate metric or geometry is authorized.
