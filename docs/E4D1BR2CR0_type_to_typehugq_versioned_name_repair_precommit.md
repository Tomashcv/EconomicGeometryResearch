# E4D1BR2CR0 — 2019 TYPE to TYPEHUGQ versioned-name repair

The preserved E4D1BR2CR attempt failed at the first 2019 housing header because `TYPEHUGQ` is not a 2019 field. No TYPEHUGQ row value and no housing row was opened in that CR attempt. The already-known structural parent outcome remains unchanged.

CR0 freezes a single repair candidate before opening any 2019 `TYPE` row value: the 2019 field `TYPE` is the versioned predecessor of later `TYPEHUGQ`.

The repair is eligible only if official Census documentation proves that `TYPEHUGQ` is a name change from `TYPE`, and the frozen 2019 dictionary independently proves the same Type-of-unit code semantics:
1 = Housing unit;
2 = Institutional group quarters;
3 = Noninstitutional group quarters.

No source is reselected and no alternative structural universe is introduced. The previously precommitted hypothesis remains exactly the same, expressed in the correct 2019 schema:
`TYPE == 1 AND NP > 0`.

The runtime projection remains narrow:
housing retains only SERIALNO, NP, TYPE;
person retains only SERIALNO, RELSHIPP.

Success still requires every one of the parent's 151,321 missing-reference NP>0 records to be TYPE 2/3 and zero occupied TYPE 1 housing units to lack a reference person.

No weights, RMSP, TEN, AGEP, H coordinate, cohort values, or temporal geometry are opened or computed.
