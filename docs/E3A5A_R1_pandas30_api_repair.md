# E3A5A R1 — pandas 3.0 StataReader API Repair

## Trigger

E3A5A attempt 1 successfully:

- acquired the official CPS ASEC 2022 archive;
- acquired the official SCF 2022 full archive;
- acquired the official SCF 2022 summary archive;
- inventoried the CPS archive member structure.

It then aborted while inspecting Stata metadata.

Observed exception:

    AttributeError:
    'StataReader' object has no attribute 'close'

pandas 3.0 removed StataReader.close.

---

## Classification

This is:

    SOFTWARE_API_COMPATIBILITY_FAILURE

It is NOT:

    DATA_FAILURE
    SCHEMA_FAILURE
    SUPPORT_FAILURE
    ECONOMIC_RESULT_FAILURE

---

## Disclosure state at failure

The Stata operation performed before failure was:

    variable_labels()

No Stata observation rows were requested.

Therefore:

    DATA_ROWS_PARSED = 0
    SUPPORT_COUNTS_CALCULATED = 0
    PSEUDOCOHORT_COUNTS_OPENED = 0
    ECONOMIC_VALUES_OPENED = 0

---

## Repair

The only code change is to replace explicit:

    reader.close()

with ownership of the underlying file handle through:

    with path.open("rb") as fh:

The StataReader continues to call only:

    variable_labels()

No schema requirement, source, cohort definition, threshold, mapping or
economic rule is changed.

---

## Scientific invariants

Unchanged:

- E3A3 support thresholds;
- E3A4 AGE_BAND × TENURE mapping;
- CEX definitions;
- CPS definitions;
- SCF definitions;
- canonical/fallback cohorts;
- prohibition on support-count opening in E3A5A;
- prohibition on economic-value inspection.

E3A5A R1 remains a metadata-only source/schema inventory.
