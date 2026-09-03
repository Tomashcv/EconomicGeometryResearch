# E4D1D3 CPSP P0 — exact empirical bridge-audit SHA input freeze

Parent: `a960fcc998063ce9c2d1cb8c78e6b0f37155f3b5`.

This precommit freezes a provenance-only, deterministic, single-locus replacement in the
2019 CPS I adapter **before** executing the patcher.

Frozen replacement:

- old E4A2B audit expected SHA: `962b727559808c389afac33060a4562bead5099be6000b951af796a1ac37be2e`
- new 2019 empirical E4A2B audit SHA: `1434529f38aa100f3cb85ae2e13385a135415bcc0dd2a489ffe476916b1a76b2`
- exact replacement count: `1`
- E4A2B summary binding SHA remains: `475ba266f163b2e08fff3256567bd563c3cc17c4826240a8429275cdb2fc62bb`
- expected patched adapter SHA: `556b5ae5076b319f45b1bd2261c34193833b1eb45916183c7adae1615c09a7ca`

The prefrozen patcher computes the new SHA from the already-frozen 2019 runtime bridge
audit and replaces only the old expected audit SHA. No scientific function body changes.
No CPS raw data are opened, no CPS values are parsed, no CPS I values are opened, and
the patcher is not executed during this precommit.

The next authorized action after this precommit is the exact CPSP provenance patch
execution only. CPS I remains closed.
