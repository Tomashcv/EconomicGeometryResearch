# E2B — Robustness Attack Precommit

## Status

Written after E2A was frozen and before E2B robustness outputs are opened.

E2A remains immutable.

No E2B result may be used to redefine E2A.

---

## Purpose

E2A found that consumption purchasing power and housing-access purchasing
power can diverge.

E2B asks whether that qualitative result depends materially on:

1. the chosen consumer-price index;
2. the chosen housing-price index;
3. the 1991 starting point.

---

## Test A — CPI robustness

Income:

    A229RC0Q052SBEA

Consumer price:

    CPIAUCSL

Housing:

    PONHPIM226S

Window:

    1991Q1 onward.

CPIAUCSL is converted from monthly to quarterly using the arithmetic mean of
the three monthly observations in each quarter.

A quarter is valid only if all three monthly CPI observations are present.

No missing CPI value is imputed.

A quarterly delta is calculated only between genuinely consecutive calendar
quarters. A missing quarter may not be bridged.

Reference:

    1991Q1

Coordinates:

    x_C_CPI(t) = ln[(Y_t/Y_r)/(CPI_t/CPI_r)]

    x_H_CORE(t) = ln[(Y_t/Y_r)/(H_t/H_r)]

Precommitted directional replication:

    endpoint x_C_CPI > 0
    endpoint x_H_CORE < 0

Discordance replication:

    count(Δx_C > 0 and Δx_H < 0)
        >
    count(Δx_C < 0 and Δx_H > 0)

This is a robustness replication, not an independent statistical test,
because it uses the same US time period and housing series as E2A.

---

## Test B — Long-run housing robustness

Income:

    A229RC0Q052SBEA

Consumer price:

    PCECTPI

Housing:

    USSTHPI

Because USSTHPI is not seasonally adjusted, the long-run experiment operates
at annual frequency.

Annual values are arithmetic means of all four quarterly observations.

A year is valid only if all four quarters exist.

Window:

    1975 through the latest complete calendar year.

Reference:

    1975

Coordinates:

    x_C_LONG(y) = ln[(Y_y/Y_1975)/(P_y/P_1975)]

    x_H_LONG(y) = ln[(Y_y/Y_1975)/(H_y/H_1975)]

Precommitted directional replication:

    endpoint x_C_LONG > 0
    endpoint x_H_LONG < 0

Discordance replication:

    count(Δx_C_LONG > 0 and Δx_H_LONG < 0)
        >
    count(Δx_C_LONG < 0 and Δx_H_LONG > 0)

---

## E2B survival criterion

E2B_ROBUSTNESS_SURVIVES = 1 only if all four conditions hold:

1. CPI endpoint consumption coordinate > 0;
2. CPI endpoint housing coordinate < 0;
3. long-run endpoint consumption coordinate > 0;
4. long-run endpoint housing coordinate < 0.

Discordance-count asymmetry is reported separately and is not required for
the endpoint survival criterion.

No p-value from E2B will be interpreted as confirmatory because the US sample
overlaps E2A.

A truly independent test requires a new country/cohort/held-out dataset.

---

## Forbidden

E2B must not:

- alter the E2A formulas;
- choose a CPI aggregation after seeing results;
- impute October 2025 CPI;
- bridge missing quarters when computing quarterly deltas;
- seasonally adjust USSTHPI using a fitted method;
- choose the 1975 reference based on results;
- optimize endpoint dates;
- claim causal effects;
- claim H1 is established.
