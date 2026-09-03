# E3B3A R1 — 2022 Integrated Hierarchy Fixed-Width Repair

## Trigger

Original frozen E3B3A script:

    SHA256
    cc113788eba54130aba8e44487986044371227b2a5582cf251901ee5fbb34579

successfully passed:

    transport
    calendar-year source plan
    Interview schema
    Diary schema

but failed:

    INTEGRATED_HIERARCHY_SOURCE_COVERAGE

The original parser produced:

    source = 1
    factor = C
    section = HARS

for rows whose section is CUCHARS.

Thus the fixed-width offsets were incorrect for the downloaded
CE-HG-Integ-2022.txt archive member.

No economic values were opened.

---

## Forensic

Two layouts were compared against the exact downloaded 2022 hierarchy bytes.

Current BLS web-documentation candidate:

    source position 83
    factor position 86
    section position 89

Year-specific 2022 candidate:

    source position 80
    factor position 83
    section position 86

The repair is authorized only because the metadata-only forensic identified
the latter as the coherent layout with actual Interview and Diary source
codes and recognized data-section labels.

---

## Repair

Only three fixed-width slices are changed:

OLD:

    source  = position 83
    factor  = position 86
    section = position 89

REPAIRED FOR 2022:

    source  = position 80
    factor  = position 83
    section = position 86

No:

- UCC values;
- expenditure observations;
- household income values;
- wealth values;
- debt values;
- cohort economic estimates

were inspected to choose this repair.

---

## Non-mutations

The following remain unchanged:

    required sources
    calendar-year construction
    schema gates
    I/D source-coverage gate
    cohort definitions
    support thresholds
    component semantics
    Real Inflation definition

Therefore this is:

    PARSER_LAYOUT_REPAIR_ONLY = 1
    ECONOMIC_PARAMETER_MUTATION = 0

