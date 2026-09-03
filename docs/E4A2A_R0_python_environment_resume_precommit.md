# E4A2A R0 — Python Environment Resume Precommit

## Parent

    906aa12

## Classification

The SCF schema/codebook validator repair was already frozen in the repair
precommit at parent 906aa12.

The first repaired execution did not enter the scientific validator because the
terminal wrapper invoked the system command:

    python3

and that interpreter did not provide pandas.

Observed failure:

    ModuleNotFoundError: No module named 'pandas'

This is an execution-environment failure, not a scientific gate failure.

## Frozen project environment

The existing project environment is used without installation or mutation:

    .venv/bin/python
    numpy==2.5.2
    pandas==3.0.5

The package contract remains:

    requirements-e3a5.txt
    SHA256=c8edd2d7d9122c977baab769f21c27c414460d24c59e5997b3ee8a17360c279b

No pip install, package upgrade, package downgrade or environment rebuild is
authorized by this resume.

## Failure preservation

The failed system-Python execution is preserved before rerun as:

    data/metadata/E4A2A_R0_attempt1_system_python_missing_pandas_execution.txt
    SHA256=13999c219348cf24a581161d9240b1c20189d6959f0dbf7122f1bb281e93d466

The original E4A2A Attempt 1 scientific/schema failure remains separately
preserved by the 906aa12 repair precommit.

## Scientific boundary

Still prohibited during this resume:

    reading K values
    reading D values
    reading I outcomes
    parsing SCF replicate-weight values
    parsing CPS replicate-weight values
    dimensionality analysis
    Real Inflation estimation
    final scalar estimation

The rerun is the already-precommitted E4A2A R0 metadata/schema/document audit
only.

## Authorization

Only a complete repaired E4A2A PASS may produce:

    E4A2B_WEIGHT_BRIDGE_AUDIT_AUTHORIZED=1

That authorization does not itself open K, D or I outcomes.
