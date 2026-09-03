# E4C6E R0 — H selector categorical forensic

The failed E4C6E execution is preserved byte-for-byte. It reached the value-open stage only after the E4C6E precommit and failed before any registry output was created because the frozen H selector selected zero rows.

This R0 is diagnostic only. It does not repair or relax the selector.

It inspects only the categorical H source fields `entity_type`, `role`, `estimand`, `age_band`, and `entity`. Numeric estimate, standard-error, and confidence-interval fields are not interpreted or emitted by the forensic. The H writer source may be inspected only as static code evidence.

The diagnostic compares the source categorical representation against the already frozen E4C6D selector and reports progressive counts. Any future repair must be justified by categorical/source-schema semantics, not by economic values, signs, magnitudes, significance, or owner-renter results.

R0 itself authorizes no repair and no E4C6E re-execution.
