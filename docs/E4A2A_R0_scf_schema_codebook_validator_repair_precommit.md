# E4A2A R0 — SCF Replicate-Schema + Codebook Validator Repair

## Parent

    ea9fd3b

## Original E4A2A result

The first E4A2A audit produced:

    SCF_REPLICATE_VARIABLE_COUNT=2000
    SCF_WT1B_COUNT=999
    SCF_MM_COUNT=999
    SCF_WT1B_1_TO_999=PASS
    SCF_MM_1_TO_999=PASS
    SCF_EXACT_REPLICATE_SCHEMA=FAIL
    SCF_OFFICIAL_CODEBOOK_REPLICATE_CONTRACT=FAIL

while all CPS schema, layout, documentation and merge gates passed.

No K, D or I economic values were opened.
No SCF or CPS replicate-weight values were parsed.

---

# Root cause 1 — official YY1 omitted from exact-set validator

Metadata-only inspection of the single official SCF Stata member established
exactly 2000 variables:

    Y1
    YY1
    WT1B1 ... WT1B999
    MM1 ... MM999

The original E4A2A exact-set validator required only:

    Y1
    WT1B1 ... WT1B999
    MM1 ... MM999

and therefore expected 1999 variables implicitly.

The sole extra official variable is:

    YY1

YY1 is not an economic outcome or replicate-weight value. It is already used
by the official SCF codebook logic for the case/implicate identity relation:

    IMPLIC = Y1 - 10*YY1

The failure is therefore a validator-schema omission, not a replicate-weight
schema failure.

---

# Root cause 2 — whitespace-sensitive official-codebook anchor

The validator required the literal single-line string:

    Replicate weights were computed only for the first implicate

The frozen official codebook contains the same sentence with a physical line
break between:

    Replicate
    weights

The following stronger structural anchors already passed exactly:

    WT1B1-WT1B999
    MM1-MM999
    xxx.rep_wgts(KEEP=Y1
    WGTS{I}=MAX(0,MULT{I})*MAX(0,RWGT{I})

The repair retains those exact anchors and makes only the prose sentence
whitespace-tolerant.

---

# Repair principle

Require the SCF replicate file to equal exactly:

    {Y1, YY1, WT1B1..WT1B999, MM1..MM999}

Thus:

    total variables = 2000
    Y1 required
    YY1 required
    exactly 999 WT1B variables
    exactly 999 MM variables
    no unspecified extra variables allowed

For the official-codebook contract:

    retain all four exact structural anchors
    allow arbitrary whitespace only between words of the first-implicate prose anchor

This does not weaken the scientific gate.

---

# No scientific contract mutation

Unchanged:

    SCF replicate count = 999
    effective replicate weight r = max(0,WT1B_r) * max(0,MM_r)
    SCF replicate merge key = Y1

    CPS replicate count = 160
    CPS replicate merge keys = H_SEQ, PPPOS

    CPS E4A2 household point weight = HSUP_WGT
    CPS replicate base weight = PWWGT0
    documented person counterpart = MARSUPWT

Still pending:

    CPS_HOUSEHOLD_FULL_WEIGHT_BRIDGE=PENDING

No identity between HSUP_WGT and reference-person MARSUPWT/PWWGT0 is assumed.

---

# Scientific boundary

Still prohibited at E4A2A R0:

    reading FIN
    reading LIQ/EQUITY/RETQLIQ
    reading PIRTOTAL/DEBT2INC
    reading WEWKRS/WEUEMP outcomes

    parsing SCF replicate-weight values
    parsing CPS replicate-weight values

    calculating K
    calculating D
    calculating I

    dimensionality analysis
    Real Inflation estimation
    final scalar estimation

The repair uses metadata/schema/document text only.

---

# Attempt preservation

The original E4A2A FAIL is retained as:

    E4A2A_attempt1_scf_schema_codebook_validator_failure_execution.txt
    E4A2A_attempt1_scf_schema_codebook_validator_failure_audit.txt
    E4A2A_attempt1_scf_schema_codebook_validator_failure_schema.tsv
    E4A2A_attempt1_scf_schema_codebook_validator_failure_official_acquisition_hashes.tsv

They must not be deleted or rewritten.

---

# Authorization rule

Only if the repaired E4A2A audit passes all original SCF and CPS gates may it
produce:

    E4A2B_WEIGHT_BRIDGE_AUDIT_AUTHORIZED=1

That authorizes only the dedicated values-only CPS weight-bridge audit.
It does not authorize opening I outcomes or K/D values.
