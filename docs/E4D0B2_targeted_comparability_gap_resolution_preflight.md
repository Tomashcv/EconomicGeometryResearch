# E4D0B2 — targeted comparability gap-resolution preflight

E4D0B1 froze 40 adjudication objects: 31 PASS, 2 VERSIONED_PASS, 0 FAIL, and exactly 7 UNRESOLVED objects (4, 10, 12, 28, 29, 32, 37).

E4D0B2 does not resolve those objects. It freezes the exact evidence acquisition and decision rules that E4D0B2A may use.

Five new official metadata/program-documentation artifacts are precommitted:

1. the Federal Reserve SCF summary-extract variable-definition macro;
2. Census API metadata for ACS AGEP in 2019;
3. Census API metadata for ACS AGEP in 2022;
4. Census API metadata for CPS ASEC A_AGE in 2019;
5. Census API metadata for CPS ASEC A_AGE in 2022.

No microdata URL is authorized.

The two age gaps are treated as validator-resolution problems rather than scientific-method changes. E4D0B1 already established that AGEP and A_AGE are present in the frozen 2022 authority and in both year-specific official dictionaries. The generic nearby-text Jaccard gate is therefore not reused. E4D0B2A must instead require exact official variable identity, age semantics, integer typing, and—for ACS—the documented range covering every target age from 25 through 64.

The SCF gaps use the Federal Reserve's own common summary-extract program. D/PIRTOTAL may pass only if the program defines one common PIRTOTAL formula for both 2019 and 2022. K/FIN reference-period comparability may receive VERSIONED_PASS only if FIN has one common definition and the official program applies its documented CPI-U-RS real-dollar transport across the 2019 and 2022 branches.

The K price bridge is frozen conditionally before any 2019 K value. If the official macro and already hash-pinned SCF release pages jointly validate the current summary-extract convention, the canonical transport is the Federal Reserve SCF summary-extract real-dollar convention to the 2022-dollar basis, followed by reuse of the already-frozen K reference scale. The reference scale may not be refit using 2019 observations and no alternative deflator may be selected after values are opened.

The common time grid remains unresolved until every substantive gap is PASS or VERSIONED_PASS. Only then may the exact two-wave grid 2019|2022 freeze. There is no interpolation, carry-forward, or synthetic 2020/2021 state.

Acquisition failure, parser failure, or insufficient official evidence maps to UNRESOLVED, not FAIL. Explicit documentary incompatibility is required for FAIL.
