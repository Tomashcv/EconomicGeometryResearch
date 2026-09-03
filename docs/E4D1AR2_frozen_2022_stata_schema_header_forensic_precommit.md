# E4D1AR2 — frozen-2022 SCF Stata schema/header forensic

E4D1AR1 established that both 2022 SCF archives are directly read and that the merged downstream graph is heavily joint-tainted, but static AST analysis could not attribute FIN/PIRTOTAL to one archive. E4D1AR2 therefore opens only archive member names and Stata schema metadata after precommit.

The scientific question is source role, not values. The frozen coordinate targets are FIN and PIRTOTAL. The frozen SCF point-weight role is X42001. E4D1AR2 asks which 2022 schema supplies those named roles.

A joint source set is resolved only if the Summary Extract schema supplies FIN and PIRTOTAL, the Full Public schema does not supply that joint target role, the Full Public schema supplies X42001 while the Summary Extract does not, both schemas expose Y1 for the frozen merge, and the already-frozen E4D1AR1 provenance confirms that joined/value_matrices/full_weights/age_matrix are downstream dependencies of both sources.

No observation row is read. `pandas.io.stata.StataReader` is used only to initialize the Stata header reader and obtain variable-label metadata, whose keys are the schema variable names. `StataReader.read()` is prohibited.

If each ZIP does not contain exactly one DTA member, or the role pattern is not uniquely decisive under the frozen rules, requirement 3 remains unresolved and E4D1AR2R is the only authorized route.

If the joint rule passes, requirement 3 becomes resolved to both official 2019 source candidates. The other five E4D1A source requirements remain unchanged and E4D1B becomes authorized. E4D1AR2 itself performs no 2019 download.
