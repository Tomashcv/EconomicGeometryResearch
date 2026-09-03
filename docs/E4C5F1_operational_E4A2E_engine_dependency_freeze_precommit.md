# E4C5F1 — operational E4A2E variance-engine dependency freeze

E4C5F passed and is preserved. Its source manifest correctly froze the E4A2F orchestration script and exposed an important dependency:

- `E4A2E_CONTRACT`
- `E4A2E_ENGINE`

The E4A2F script therefore cannot be treated as the final operational variance formula authority by itself. It delegates the SCF replicate/multiple-imputation engine to an E4A2E dependency.

E4C5F1 follows that dependency before any transformed inference execution.

The E4A2E engine path and contract path are derived from the frozen E4A2F AST rather than guessed. Both files must already be tracked in Git. Their SHA-256 hashes are frozen after the E4C5F1 precommit.

The E4A2E engine source is then inspected structurally. E4C5F1 freezes:

- all function definitions;
- source statements containing imputation/implicate, sampling/replicate, variance/combined, or standard-error semantics;
- exact source spans;
- numeric literals nested within those operational formula statements.

No target result-table data row is read. No transformed replicate or uncertainty is computed.

The K/D method family remains unchanged from E4C5E. The point transforms remain unchanged.

Only after the delegated operational engine has been frozen successfully may E4C5G be written as a transformed-inference execution precommit.
