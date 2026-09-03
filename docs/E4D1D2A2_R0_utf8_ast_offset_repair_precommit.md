# E4D1D2A2 R0 — UTF-8 AST offset repair

The A2 precommit was already frozen and pushed. Construction then created the ACS adapter source and stopped before SCF adapter construction because the constructor explicitly rejected any non-ASCII frozen source.

This is a constructor plumbing failure, not a scientific failure. The frozen SCF method source is valid UTF-8 Python and remains immutable.

R0 preserves the original constructor and the partially generated ACS adapter in Git history. It creates a repaired constructor copy with exactly two plumbing changes: remove the ASCII-only rejection guard, and translate Python AST UTF-8 byte-column offsets into Python string-column offsets before exact source-literal replacement.

No method source, function body, target definition, parser, transform, replicate rule, member choice, raw source, or A1 target map may change.

The repaired constructor is still source-construction only. Generated adapters may be compile-checked but are not imported or executed, and no 2019 data row or coordinate value is opened.
