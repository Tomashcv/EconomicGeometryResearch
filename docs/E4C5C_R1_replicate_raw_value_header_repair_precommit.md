# E4C5C R1 — replicate `raw_value` header repair

R0 successfully resolved the point header to `point_estimate_raw`, still without opening any data row.

It then opened only the replicate-source header:

`year, statistic_type, age_band, tenure_or_contrast, statistic_id, replicate, raw_value, state_oriented_value`

and stopped because its raw-estimate priority list did not include the exact generic field name `raw_value`.

No replicate data row and no target numerical K/D value was opened.

The correct source is determined from semantics alone. E4C5C applies the frozen state transforms itself, so replicate inventory must use `raw_value`, not the already-oriented `state_oriented_value`.

R1 therefore makes exactly one parser change relative to the frozen R0 parser: it adds exact `RAW_VALUE` as the first replicate estimate-column priority.

All scientific choices remain unchanged: FIN primary for K, PIRTOTAL primary for D, K reference 38,640 USD, D sign flip, `point_estimate_raw` for point input, no outcome gate, no transformed replicate inference, and no geometry.
