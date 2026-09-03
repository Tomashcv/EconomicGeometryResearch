# E1B — US Minimal Dataset Semantic Contract

## Status

This contract is frozen before inspection of H1/H2 economic results.

The purpose of E1B is to define what each series means and which mathematical
operations are authorized.

No ML, PCA, crisis prediction, geometry, velocity, acceleration or curvature
is authorized at E1B.

---

## 1. Core observation frequency

The canonical E1/H1/H2 experiment operates at quarterly frequency.

Core window:

    1991Q1 onward

because the canonical FHFA Purchase-Only House Price Index begins in 1991Q1.

Long-run secondary housing analysis may use USSTHPI from 1975 onward.

---

## 2. Core income series

Series:

    A229RC0Q052SBEA

Meaning:

    Nominal disposable personal income per capita.

Units:

    Dollars, seasonally adjusted annual rate.

This is the canonical nominal income numerator.

The real series:

    A229RX0Q048SBEA

is QA only and MUST NOT be divided by another price index.

---

## 3. Core consumer-price series

Canonical:

    PCECTPI

Meaning:

    PCE chain-type price index.

Units:

    Index 2017=100, seasonally adjusted, quarterly.

Robustness:

    CPIAUCSL
    PCEPI

The October 2025 CPIAUCSL observation is officially unavailable because of
the 2025 lapse in federal appropriations.

No synthetic October 2025 CPI value is authorized in E1/E2.

CPI-based quarterly results must mark an incomplete quarter as unavailable
unless a later protocol explicitly freezes another treatment before inspection.

---

## 4. Canonical consumer purchasing-power coordinate

Let

    Y_t = nominal disposable personal income per capita
    P_t = canonical consumer price index

First rebase both series to the same reference quarter r:

    Y*_t = Y_t / Y_r
    P*_t = P_t / P_r

Define:

    CPP_t = Y*_t / P*_t

Therefore:

    CPP_r = 1

and the logarithmic consumption coordinate is:

    x_C(t) = ln(CPP_t)

Interpretation:

    x_C > 0 : consumer purchasing power is above the reference state
    x_C = 0 : equal to reference
    x_C < 0 : below reference

The primary E1/E2 implementation uses PCECTPI.

CPIAUCSL is a robustness definition, not a parameter-selection tool.

---

## 5. Canonical housing series

Primary:

    PONHPIM226S

Meaning:

    FHFA Purchase-Only House Price Index.

Properties:

    quarterly
    seasonally adjusted
    repeat-sales
    single-family properties
    index 1991Q1=100

Secondary long-run series:

    USSTHPI

The all-transactions series is not seasonally adjusted and uses sales-price
and appraisal information.

MSPUS is a secondary dollar-price series for newly sold houses and MUST NOT be
treated as a representative price of the entire US housing stock.

---

## 6. Canonical housing-access coordinate

Let:

    Y_t = nominal disposable personal income per capita
    H_t = canonical house-price index

Rebase:

    Y*_t = Y_t / Y_r
    H*_t = H_t / H_r

Define:

    HA_t = Y*_t / H*_t

and:

    x_H(t) = ln(HA_t)

Interpretation:

    x_H > 0 : housing access improved relative to reference
    x_H = 0 : unchanged
    x_H < 0 : housing access deteriorated

This is a macro affordability proxy, not yet a mortgage-underwriting model.

---

## 7. H2 precommitted divergence test

The primary qualitative prediction is:

    exists t such that:

        Δx_C(t) > 0
        and
        Δx_H(t) < 0

That means consumer purchasing power improved during a period in which
housing purchasing power deteriorated.

The existence of such periods alone does NOT prove H1.

---

## 8. Saving / accumulation capacity

Canonical saving-rate series:

    A072RC1Q156SBEA

Let:

    s_t = saving_rate_t / 100

Then an annual-rate per-capita saving-flow proxy is:

    S_t = Y_t * s_t

This is derived from the official BEA saving-rate definition.

It MUST NOT be replaced by:

    disposable_income - PCE

because personal outlays are not identical to PCE.

A later experiment may define capital-access quantities relative to S_t.

---

## 9. Debt

TDSP is:

    total required household debt payments / disposable personal income.

It is reserved for the later debt coordinate D.

It does not enter the initial H1/H2 minimal test.

---

## 10. Mortgage rate

MORTGAGE30US is a weekly, not-seasonally-adjusted 30-year fixed mortgage rate.

A methodology change occurred in November 2022.

It does not enter the initial price-only housing-access coordinate.

A later financing-access experiment must freeze:

    weekly-to-quarterly aggregation
    down-payment assumption
    mortgage term
    amortization formula
    methodology-break treatment

before looking at financing-access results.

---

## 11. Forbidden operations

E1/E2 MUST NOT:

1. divide real disposable income by CPI/PCEPI/PCECTPI;
2. interpret a house-price index as a dollar house price;
3. use MSPUS as the canonical all-housing price;
4. silently impute October 2025 CPI;
5. mix SA and NSA series without an explicitly frozen transformation;
6. optimize the reference quarter after viewing results;
7. choose CPI vs PCE based on which supports H2 more strongly;
8. add ML, PCA or crisis targets before H1/H2 descriptive tests are frozen;
9. claim causality from any H1/H2 correlation or divergence;
10. claim that CPI is false or manipulated from an observed divergence.

---

## 12. Primary reference quarter

The canonical reference quarter is:

    1991Q1

Reason:

    it is the first observation of the canonical Purchase-Only FHFA HPI.

This choice is structural and was made before viewing H1/H2 results.

---

## 13. Primary H1/H2 outputs

The first authorized economic outputs are ONLY:

    x_C(t)
    x_H(t)
    Δx_C(t)
    Δx_H(t)
    divergence(t) = x_C(t) - x_H(t)

plus descriptive correlation between x_C and x_H.

No PCA is authorized until this minimal experiment has been reported.

---

## 14. Falsification discipline

H2 is weakened if consumption and housing-access coordinates are effectively
collinear over the available sample.

H1 requires evidence beyond a single pair of variables.

No result from E1/E2 is sufficient to establish the full multidimensional
economic-state theory.
