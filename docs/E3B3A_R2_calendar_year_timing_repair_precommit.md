# E3B3A R2 — Calendar-Year Interview Timing Repair

## Trigger

E3B3A R1 correctly established:

    canonical CEX archives;
    Interview and Diary schemas;
    integrated hierarchy layout;
    Interview/Diary source metadata.

However its calendar-year Interview source plan included only:

    2022Q1
    2022Q2
    2022Q3
    2022Q4

This is incomplete for calendar-year expenditure estimation.

No household economic values have yet been opened.

---

# 1. Official timing logic

An Interview Survey quarter identifies when the interview occurred.

Interview respondents report expenditures for approximately the preceding
three months.

Therefore an annual calendar-year expenditure estimate requires data from:

    Q1 of year Y
    Q2 of year Y
    Q3 of year Y
    Q4 of year Y
    Q1 of year Y+1

and expenditure observations are restricted using their own reference month
and reference year.

For calendar year 2022:

    2022Q1 = 221
    2022Q2 = 222
    2022Q3 = 223
    2022Q4 = 224
    2023Q1 = 231

Thus:

    INTERVIEW_CALENDAR_2022_REQUIRED_QUARTERS
        = 221,222,223,224,231

---

# 2. Release packages

Beginning in 2020, Interview release packages contain:

    Q2
    Q3
    Q4

of the named year plus:

    Q1 of the following year.

Therefore:

    intrvw21.zip
        supplies 221

and:

    intrvw22.zip
        supplies 222
        supplies 223
        supplies 224
        supplies 231

Both release packages are required for calendar-year 2022.

---

# 3. Future MTBI calendar filter

When economic values are later authorized, Interview MTBI observations must
be restricted using expenditure reference period fields.

For the 2022 anchor:

    REF_YR = 2022
    REF_MO in {1,...,12}

The interview-quarter filename itself must NOT be treated as the expenditure
calendar quarter.

This rule is frozen before COST values are opened.

---

# 4. Diary timing remains unchanged

Diary observations are recorded contemporaneously over survey weeks.

For calendar-year 2022 the required collection quarters remain:

    221
    222
    223
    224

No 231 Diary file is required for the primary 2022 calendar estimate.

---

# 5. What was wrong in E3B3A R1

The following statement is superseded:

    INTERVIEW_2022Q1_FROM_RELEASE_2021=PASS
    INTERVIEW_2022Q2_Q3_Q4_FROM_RELEASE_2022=PASS
    CALENDAR_YEAR_2022_SOURCE_PLAN=PASS

The archive assignments themselves were correct for 221-224.

The error was omission of:

    231

from the annual Interview source window.

Therefore:

    E3B3A_R1_TRANSPORT_RESULT = PRESERVED
    E3B3A_R1_SCHEMA_RESULT = PRESERVED
    E3B3A_R1_HIERARCHY_RESULT = PRESERVED

but:

    E3B3A_R1_CALENDAR_SOURCE_PLAN = SUPERSEDED

---

# 6. E3B3B impact

E3B3B reconstructed only official hierarchy metadata from:

    stubs.zip

It did not depend on Interview expenditure-window selection.

Therefore:

    E3B3B_HIERARCHY_RESULT_AFFECTED = 0

The frozen E3B3B PASS remains valid.

---

# 7. Disclosure state

E3B3A R2 may inspect:

    ZIP member names
    CSV first-record headers

It may NOT inspect:

    COST
    expenditure observations
    income values
    cohort economic values

Therefore:

    MICRODATA_DATA_ROWS_PARSED = 0
    COST_VALUES_READ = 0
    ECONOMIC_VALUES_OPENED = 0
    REAL_INFLATION_ESTIMATED = 0

