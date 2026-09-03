# E4A — K / D / I Household-State Architecture

## Parent

    7ebf3d7

## Upstream state

C/H 2022 is inferentially closed.

Validated facts include:

    C/H household implementation validated
    C/H distinctness evidence strengthened

but:

    FIVE_DIMENSIONALITY_PROVEN = 0
    K_EMPIRICALLY_TESTED = 0
    D_EMPIRICALLY_TESTED = 0
    I_EMPIRICALLY_TESTED = 0

This milestone defines K, D and I before their economic values are opened.

---

# 1. State architecture

Candidate state remains:

    x_g(t) = [C, H, K, D, I]^T

where higher values should ultimately correspond to a better economic
position within each dimension.

The existence of five labels does not prove five-dimensionality.

No final scalar is authorized.

---

# 2. Survey integration principle

CEX, SCF and CPS ASEC are independent samples.

Direct record linkage is prohibited.

The integration layer is:

    estimate_survey(concept | pseudo-cohort g, time t)

followed by cohort/time-level comparison.

No synthetic person-level CEX-SCF-CPS join is authorized.

---

# 3. Frozen pseudo-cohort principle

Primary pseudo-cohort definition remains:

    AGE_BAND x TENURE

Primary age bands:

    25-34
    35-44
    45-54
    55-64

Primary tenure:

    OWNER
    RENTER

OTHER / no-cash-rent is excluded from primary comparisons.

Previously validated headline cohort:

    25-34 OWNER
    25-34 RENTER

The exact already-frozen survey-specific cohort mappings must be reused.

No cohort mutation based on K/D/I outcomes is permitted.

---

# 4. K — capital position

## Construct

K is household access to and ownership of financial capital.

K is deliberately narrower than:

    total wealth
    total assets
    net worth

because those broader objects mechanically mix:

    housing position H
    debt position D
    financial capital K

## Primary K observable

    FIN

Federal Reserve official SCF definition:

    total financial assets

FIN is the primary K level proxy.

## K sensitivity / decomposition observables

    LIQ
    EQUITY
    RETQLIQ

Interpretation:

    LIQ
        liquid transaction-account assets

    EQUITY
        equity exposure through directly and indirectly held equity assets

    RETQLIQ
        quasi-liquid retirement assets

These are not four independent dimensions.

They are alternate views/decompositions of K.

## Prohibited primary K variables

    NETWORTH
    ASSET
    HOMEEQ
    HOUSES

Reason:

    NETWORTH mixes K, H and D
    ASSET mixes financial and housing/nonfinancial assets
    HOMEEQ and HOUSES belong primarily to H_ACCESS

## K direction

    higher = better capital position

No K scalar combining FIN/LIQ/EQUITY/RETQLIQ is authorized yet.

---

# 5. D — debt position

## Construct

D is debt-service and leverage burden, sign-normalized so:

    higher D = better debt position

D is not simply outstanding debt dollars.

A household with more income/resources may sustainably carry more debt.

## Primary D observable

Federal Reserve:

    PIRTOTAL

defined as total monthly debt payments relative to monthly income.

Frozen state orientation:

    D_PRIMARY_RAW = PIRTOTAL
    D_PRIMARY_SIGN = -1

Conceptually:

    D_primary = -PIRTOTAL

so higher is better.

## Secondary D sensitivity

    DEBT2INC

Federal Reserve definition:

    total debt / income

with the official special case for positive debt and zero income.

Frozen state orientation:

    D_SECONDARY_RAW = DEBT2INC
    D_SECONDARY_SIGN = -1

## Diagnostic only

    DEBT

Total debt dollars may be retained for interpretation but is not the primary D
state because it does not scale debt by household resources.

## Prohibited

Do not define:

    D = -DEBT

as the sole primary D dimension.

No weighted combination of PIRTOTAL and DEBT2INC is authorized yet.

---

# 6. I — income/employment security

## Construct

I captures attachment to employment and labor-market security.

I is not household income itself.

Resources and labor security must remain distinct because two households with
similar annual income can have different employment continuity/risk.

## Survey

Primary source:

    CPS ASEC

ASEC is explicitly designed for annual income and work-experience measurement.

## Temporal alignment

Primary I evidence uses previous-year work-experience variables.

Current-week labor-force variables are not primary.

This prevents mixing:

    annual income/resources
    with
    a single-week employment snapshot

## Primary I observables

    WEWKRS
        weeks worked last year
        direction: higher = better

    WEUEMP
        weeks looking for work
        direction: higher raw = worse

Sign-normalized concept:

    I_WORK_ATTACHMENT = WEWKRS
    I_SEARCH_BURDEN   = -WEUEMP

These remain separate observables.

No I scalar is authorized.

## Secondary / diagnostic I observables

    WORKYN
    WTEMP
    WEXP
    HRSWK

Their exact value coding must be audited before use.

No semantic assumption about their numeric codes is authorized at E4A.

---

# 7. Resources are not I

CPS ASEC:

    HTOTVAL

is a candidate household resource/income measure.

It is NOT an I observable.

Frozen distinction:

    RESOURCES != EMPLOYMENT_SECURITY

HTOTVAL may later be used in:

    EP_g(t) = Resources_g(t) / R_g(t; B_g)

but does not define I.

---

# 8. CPS household/reference-person anchor

Primary CPS household pseudo-cohort anchor remains:

    H_SEQ          household identifier
    A_EXPRRP       identify reference person
    A_AGE          reference-person age
    H_TENURE       tenure
    HSUP_WGT       household March supplement weight

Reference person:

    A_EXPRRP in {1,2}

Tenure primary:

    H_TENURE = 1 -> OWNER
    H_TENURE = 2 -> RENTER

No-cash-rent:

    H_TENURE = 3

is excluded from primary owner/renter comparison.

Exact coding is subject to the next source/schema audit before economic values
are opened.

---

# 9. SCF inference architecture

The SCF contains five implicates per underlying family.

Multiple imputation must be respected.

The Federal Reserve warns that ignoring the five implicates and complex sample
design produces incorrect standard errors.

Point-estimate and inference implementation must therefore explicitly handle:

    family identity
    implicate identity
    survey weights
    replicate weights where required

No naïve treatment of five implicates as five independent families is allowed.

## Dollar basis

The official SCF Summary Extract dollar variables are already expressed in:

    2022 dollars

Therefore:

    SECOND_DEFLATION = PROHIBITED

for those real-dollar summary-extract fields.

---

# 10. Dimensionality falsification principle

A variable is not accepted as a separate dimension merely because:

    it has a different name
    it differs across owner/renter cohorts
    it is statistically significant

For K, D or I to strengthen the five-dimensional hypothesis, later evidence
must establish at minimum:

1. construct validity;
2. reliable survey estimation;
3. non-degenerate cohort/time variation;
4. behavior not reducible by definition to an already-existing dimension;
5. non-redundant empirical movement relative to the existing C/H state;
6. robustness to at least one reasonable alternate proxy where available.

Exact numerical distinctness gates must be precommitted only after the
longitudinal cohort x time matrix and support are known, but before those
distinctness outcomes are examined.

No threshold may be retrofitted after observing dimensionality results.

---

# 11. H_ACCESS remains open

H_SERVICE is validated.

H_ACCESS is not yet implemented.

SCF housing/balance-sheet variables may later support H_ACCESS, but they must
not be silently absorbed into K.

In particular:

    HOUSES
    HOMEEQ
    mortgage/access measures

remain reserved primarily for H_ACCESS work.

---

# 12. Real Inflation remains unauthorized

State dimensions are not automatically inflation components.

Still frozen:

    STATE_CHANGE_EQUALS_COST_INFLATION = 0
    OBSERVED_EXPENDITURE_CHANGE_EQUALS_INFLATION = 0
    GE_EQUALS_REAL_INFLATION = 0

Candidate cost-side definition remains:

    pi_real_g(t)
      = Delta ln R_g(t; B_g)

No Real Inflation value is authorized at E4A.

---

# 13. E4A restrictions

This milestone opens no K/D/I economic values.

    SCF_ECONOMIC_VALUES_READ = 0
    CPS_KDI_ECONOMIC_VALUES_READ = 0

    K_EMPIRICALLY_TESTED = 0
    D_EMPIRICALLY_TESTED = 0
    I_EMPIRICALLY_TESTED = 0

    FIVE_DIMENSIONALITY_PROVEN = 0
    FINAL_SCALAR_AUTHORIZED = 0

If E4A passes:

    E4A1_SCF_CPS_KDI_SCHEMA_AUDIT_AUTHORIZED = 1

