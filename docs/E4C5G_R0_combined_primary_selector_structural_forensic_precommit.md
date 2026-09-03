# E4C5G R0 — combined primary selector structural forensic

The first E4C5G execution was correctly precommitted and then failed before any transformed output was written because the combined primary selector returned zero K/D cells.

R0 is diagnostic only. It reads only categorical/identifier fields from the already-frozen E4A2F combined table and applies the E4C5G selector one predicate at a time.

No point estimate, variance, replicate mean, standard error, or other numerical outcome field is read or used.

The forensic records:

- semantic signatures for `K_FIN_MEAN` and `D_PIRTOTAL_MEAN`;
- counts remaining after statistic-id, age, tenure, role, dimension, raw-variable, and statistic predicates;
- whether exact age equality is the failing predicate while the earlier frozen broad age parser succeeds;
- whether normalized exact OWNER/RENTER tenure semantics succeed.

R0 does not modify the E4C5G parser and does not authorize a repair. A subsequent repair may be written only from the frozen categorical result of this forensic.
