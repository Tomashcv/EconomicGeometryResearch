# E3A1R1 — BLS Documentation Transport Repair

## Trigger

The first execution of E3A1 was aborted before any economic values or
pseudo-cohort counts were opened.

Failure occurred during acquisition of the official BLS CEX PUMD XLSX
dictionary.

Observed transport result:

    HTTP 403

The downloaded response was HTML rather than a valid XLSX ZIP container.

This is classified as:

    TRANSPORT_FAILURE

not:

    SCHEMA_FAILURE
    ECONOMIC_RESULT_FAILURE

The failed execution log is preserved as:

    data/metadata/E3A1_attempt1_transport_403.txt

---

## Scientific invariants

E3A1R1 does NOT change:

- project objective;
- Real Inflation definition target;
- survey roles;
- candidate cohort variables;
- timing rules;
- prohibition on cross-survey record joins;
- prohibition on economic value inspection;
- prohibition on cohort-count inspection.

No variable was added or removed because of observed economic data.

---

## CEX evidence repair

The official BLS PUMD documentation page continues to advertise:

    Dictionary for Interview and Diary Surveys (XLSX)

but direct automated transport returned HTTP 403.

E3A1R1 therefore uses other official BLS documentation as provenance.

Current official PUMD Getting Started Guide documents:

    NEWID
    FINLWT21

and the population-weight methodology.

BLS Working Paper 544, Appendix A.2, documents the Interview FMLI variables:

    AGE_REF
    FAM_SIZE
    PERSLT18
    CUTENURE
    FINLWT21

These sources establish that the candidate concepts/variable names are genuine
CEX variables.

They do NOT substitute for exact 2022-header verification.

---

## Exact 2022 CEX schema rule

Because the cross-year XLSX dictionary could not be archived automatically:

    CEX_2022_EXACT_HEADER_VERIFICATION = DEFERRED

The exact presence of required variables in the 2022 anchor release must be
verified directly from the official 2022 CSV microdata archive before:

- calculating a statistic;
- opening a pseudo-cohort count;
- defining a final cohort.

Only file names and CSV header rows may be inspected during that verification.

---

## Timing evidence

Current BLS documentation states that beginning with the 2020 Interview PUMD
release, package Y contains:

    Q2(Y)
    Q3(Y)
    Q4(Y)
    Q1(Y+1)

Therefore package labels must not be equated with calendar-year expenditure
periods.

---

## Result semantics

E3A1 original execution:

    ABORTED_TRANSPORT_403

E3A1R1 may pass only as a transport/provenance repair.

It must NOT relabel the original E3A1 attempt as PASS.

Next authorized operation after E3A1R1:

    header-only anchor-file reconnaissance

No cohort counts are authorized until the sample-support gate is separately
precommitted.
