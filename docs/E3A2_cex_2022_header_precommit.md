# E3A2 — CEX 2022 Exact Header Audit

## Purpose

Resolve the header-verification item deferred by E3A1R1.

This experiment inspects the official 2022 CEX Interview CSV archive.

No data-row values may be read.

No row counts may be calculated.

No cohort counts may be calculated.

No weighted statistics may be calculated.

No Real Inflation estimate may be calculated.

---

## Official anchor

Survey:

    Consumer Expenditure Survey — Interview PUMD

Release:

    2022

Format:

    CSV / comma-delimited

Expected official archive naming convention:

    intrvw22.zip

Official BLS documentation states that the 2022 CSV Interview archive exists
and that Interview PUMD releases beginning in 2020 contain:

    Q2 of release year
    Q3 of release year
    Q4 of release year
    Q1 of following year

Therefore this archive is a schema anchor, NOT by itself a complete
calendar-year-2022 expenditure dataset.

---

## Files of interest

FMLI:
    consumer-unit level summary/demographics/weights

MTBI:
    monthly expenditure records

MEMI:
    member-level characteristics/income

Only archive member names and the first CSV record (header) are authorized.

---

## Required FMLI variables

Every discovered 2022-release FMLI header must contain:

    NEWID
    AGE_REF
    FAM_SIZE
    PERSLT18
    CUTENURE
    FINLWT21

These were selected before opening the exact 2022 headers.

---

## Required structural MTBI variables

Every discovered MTBI header must contain:

    NEWID
    UCC

No expenditure amount is inspected.

---

## Required structural MEMI variables

Every discovered MEMI header must contain:

    NEWID
    MEMBNO

No member-level value is inspected.

---

## Hard gates

PASS requires:

1. downloaded object is a valid ZIP;
2. at least one FMLI CSV exists;
3. at least one MTBI CSV exists;
4. at least one MEMI CSV exists;
5. all FMLI headers contain all required FMLI variables;
6. all MTBI headers contain required structural variables;
7. all MEMI headers contain required structural variables;
8. zero data rows are parsed.

No fallback variable substitution is allowed after header inspection.

---

## Next step

If E3A2 passes:

    E3A3_SAMPLE_SUPPORT_GATE_PRECOMMIT_AUTHORIZED=1

Before any pseudo-cohort count is opened, E3A3 must freeze:

- candidate cohort families;
- minimum unweighted support;
- effective-sample-size rule;
- required cross-wave coverage;
- pooling/fallback policy.

