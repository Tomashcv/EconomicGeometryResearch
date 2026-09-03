# E4C3B R0 — Static 2022 ACS Subject Definitions parser repair

## Preserved failure

E4C3B was scientifically precommitted before official metadata acquisition.

Attempt 1 successfully acquired the 2022 PUMS dictionary, both Census glossary URLs, and the PUMS user guide. The frozen parser then failed while searching the raw Gross Rent glossary HTML for definition text.

The failure is representational, not scientific: the Census glossary page renders the selected glossary term dynamically, while the downloaded raw HTML shell does not embed that rendered definition.

No ACS microdata, H_ACCESS values, OWNER/RENTER outcomes, transformations, or geometry were opened.

## R0 repair

R0 leaves the original E4C3B contract, source plan, architecture, and parser bytes untouched.

It adds one static, same-year, official Census source:

**2022 American Community Survey Subject Definitions**

This document directly defines both Gross Rent and Selected Monthly Owner Costs and is suitable for deterministic text extraction.

The semantic claims are unchanged:

- renter gross rent includes contract rent plus renter-paid utilities/fuels;
- selected monthly owner costs include mortgage/property-debt payments, taxes, insurance, utilities/fuels, and applicable fees;
- therefore tenure-specific affordability measures are not promoted to the primary H_ACCESS architecture;
- the precommitted primary remains `RMSP / NP`.

## Boundary

This is a source-representation/parser repair only.

No H_ACCESS value may be computed in R0.
