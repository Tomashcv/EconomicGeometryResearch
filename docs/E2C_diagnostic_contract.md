# E2C — Temporal Decomposition and Regime Diagnostics

## Status

Exploratory diagnostic analysis.

E2A and E2B remain immutable.

E2C has no PASS/FAIL criterion.

Its purpose is to understand why endpoint conclusions depend on the reference
state and whether the trajectory contains materially different temporal regimes.

---

## Data

Annual analysis using complete calendar years only.

Income:
    A229RC0Q052SBEA

Consumer prices:
    PCECTPI

Housing:
    USSTHPI

Window:
    1975 through latest complete year.

Annual observations are arithmetic means of all four quarterly values.

---

## Decomposition

Relative to 1975:

    y(t) = ln(Y_t / Y_1975)

    p(t) = ln(P_t / P_1975)

    h(t) = ln(H_t / H_1975)

Consumption purchasing-power coordinate:

    x_C(t) = y(t) - p(t)

Housing-access coordinate:

    x_H(t) = y(t) - h(t)

Relative housing-vs-consumption price gap:

    G(t) = h(t) - p(t)

Identity:

    G(t) = x_C(t) - x_H(t)

---

## Origin-invariant dynamics

Changing the reference year adds constants to level coordinates but does not
change their first differences.

Therefore E2C emphasizes:

    Delta x_C(t)

    Delta x_H(t)

    Delta G(t)

These describe annual changes independent of the arbitrary coordinate origin.

---

## Trailing slopes

For exploratory regime diagnostics, E2C calculates causal trailing linear
slopes using:

    5-year windows
    10-year windows

Only observations available up to year t are used.

No centered or future-looking smoothing is authorized.

---

## Regime signatures

For each year with valid 5-year trailing slopes:

    C_UP_H_UP
    C_UP_H_DOWN
    C_DOWN_H_UP
    C_DOWN_H_DOWN

based only on the signs of the trailing x_C and x_H slopes.

These labels are descriptive and are NOT claimed to be true economic regimes.

Formal regime/change-point modelling must be precommitted separately after E2C.

---

## Outputs

E2C reports:

- annual y, p, h;
- x_C and x_H;
- housing-consumption relative-price gap G;
- annual changes;
- 5-year and 10-year causal slopes;
- zero crossings of x_H;
- five-year checkpoint table;
- contiguous descriptive 5-year-slope sign regimes.

No causal interpretation is authorized.
