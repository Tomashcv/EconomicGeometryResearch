# E4D1D0 — frozen-method execution interface preflight

E4D1C froze the 2019 coordinate contract, all seven 2019 raw byte identities, the validated ACS version adapter, the SCF/CPS source policies, and the exact 2022 methodological authorities before any 2019 coordinate value was opened.

E4D1D0 does not execute those methods. It freezes their executable interface shape so the 2019 adapter can be constructed without guessing or importing scripts with possible top-level side effects.

D0 is source-only. It AST-parses the exact frozen ACS, SCF, and CPS executor files and records:
- top-level function signatures;
- imports;
- argparse/CLI declarations;
- `if __name__ == "__main__"` entrypoint calls;
- relevant global assignments;
- path-like and year-specific string literals.

Each method is mechanically classified as a CLI entrypoint, guarded script, importable library, or unsafe top-level execution unit. No classification changes scientific content.

D0 is forbidden from importing or executing the frozen executors, opening 2019 raw rows, substituting paths, creating an execution adapter, calculating weighted estimates, or opening coordinate values.

A successful D0 authorizes only E4D1D1, where the exact execution adapter will be frozen against this interface registry before any 2019 coordinate values are opened.
