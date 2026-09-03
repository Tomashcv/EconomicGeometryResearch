# E2D — Precommitted Change-Point Detection

## Purpose

E2C descriptively suggested that the dynamics of consumption purchasing power
and housing access may operate in different temporal regimes.

E2D asks whether a purely data-driven segmentation of annual changes identifies
persistent changes in those dynamics without supplying historical event dates.

No dates such as 1980, 2000, 2008, 2020 or 2022 are provided to the algorithm.

---

## Frozen input

E2D uses only:

    data/processed/E2C_annual_decomposition.csv

Expected SHA256:

    6d3fe1beb27c59ce5771f298e5324fc07dad30173b3e8996944a3c806ad23221

The annual change sample is:

    1976 through 2025

because 1975 is the reference observation and has no prior-year delta.

---

## State-change vector

For each year t:

    z_t = [Delta x_C(t), Delta x_H(t)]

where:

    Delta x_C = annual change in consumption purchasing power
    Delta x_H = annual change in housing-access purchasing power

These first differences are invariant to a change in the arbitrary reference
year.

---

## Model

Within each regime, annual change vectors are modelled as having a constant
two-dimensional mean:

    z_t = mu_r + epsilon_t

for years belonging to regime r.

No smoothing is applied.

No historical labels are used.

---

## Segmentation algorithm

Use exact dynamic programming to minimize total within-segment squared error.

Primary configuration:

    minimum segment length = 5 annual changes
    maximum number of segments = 8

Candidate models contain:

    1, 2, ..., 8 segments

subject to the minimum segment length.

---

## Complexity selection

The primary selected segmentation minimizes BIC.

Let:

    T = number of annual observations
    D = 2 dimensions
    N = T * D
    m = number of segments

For a model with m segments:

    p = 2*m + (m - 1)

The 2*m parameters are the two mean changes for every segment.

The m-1 additional parameters represent break locations.

BIC:

    BIC = N * ln(SSE / N) + p * ln(N)

The segmentation with minimum BIC is selected.

No number of breaks is chosen manually after inspecting results.

---

## Segment interpretation

For each selected segment report:

    mean Delta x_C
    mean Delta x_H

and one descriptive sign label:

    C_UP_H_UP
    C_UP_H_DOWN
    C_DOWN_H_UP
    C_DOWN_H_DOWN

These are descriptions of mean annual dynamics, not causal economic regimes.

---

## Sensitivity

The primary minimum segment length is 5 years.

Two precommitted sensitivity analyses are also run:

    minimum segment length = 4
    minimum segment length = 6

The primary result remains the 5-year specification.

Sensitivity is used only to assess breakpoint stability.

---

## Interpretation

E2D is structural diagnostics.

It does NOT:

- estimate Real Inflation;
- establish H1;
- establish causal regimes;
- prove that any break corresponds to a known historical event;
- authorize fitting later models around manually chosen event dates.

Historical interpretation of detected breaks occurs only after the numerical
break years have been frozen.
