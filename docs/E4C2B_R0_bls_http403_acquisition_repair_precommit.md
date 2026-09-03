# E4C2B R0 — BLS HTTP 403 Acquisition Repair Precommit

## Failure classification

E4C2B Attempt 1 successfully froze and pushed the scientific metadata-audit
precommit, then failed on the **first** official workbook request with HTTP 403
(`curl` exit 22).  The frozen Python audit was never executed and no successful
XLSX package was opened before the failure.

This is classified as a transport/access-policy failure, not a scientific
failure and not a source-lineage failure.  The three predeclared URLs remain the
same official BLS workbook links.

## Repair scope

R0 changes **only** the HTTP acquisition layer.  It does not modify:

- `scripts/E4C2B_c_concordance_category_coverage_audit.py`;
- the frozen 435-UCC `C_COST` universe;
- UCC→ELI or UCC→PCE parsing logic;
- coverage definitions;
- architecture-selection boundaries;
- any price, expenditure, quantity, coordinate, geometry, or Real Inflation
  calculation.

The repaired downloader first visits each official landing page, uses a
same-origin `Referer`, rate-limits requests, and requires a local contact email
for automated BLS access.  The email is supplied interactively or through
`BLS_CONTACT_EMAIL`, is **not printed**, and is **not persisted** in the repo.
A second transport strategy may use a browser user-agent plus the HTTP `From`
header, but the source URL and downloaded bytes remain unchanged.

## Chronology

The R0 repair artifacts and exact acquisition executor are committed and pushed
**before** any post-repair workbook bytes are requested.  Only after that
precommit may the downloader retrieve and hash the three official workbooks and
run the already-frozen E4C2B Python audit.

If transport fails again, the attempt is preserved and no parser or estimator
mutation is authorized.
