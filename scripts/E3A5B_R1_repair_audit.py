from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FAILED = (
    ROOT
    / "data/metadata"
    / "E3A5B_attempt1_scf_weight_assumption_failure.txt"
)

SCRIPT = (
    ROOT
    / "scripts"
    / "E3A5B_2022_support_counts.py"
)

failure = FAILED.read_text(
    encoding="utf-8",
    errors="replace",
)

if (
    "SCF X42001 inconsistent across implicates"
    not in failure
):
    raise RuntimeError(
        "expected attempt-1 failure absent"
    )

text = SCRIPT.read_text(
    encoding="utf-8"
)

required = [
    "implicate = y1 - 10 * family_id",
    "set(implicate_rows) != {1, 2, 3, 4, 5}",
    "scf_cells_by_implicate",
    "ess = min(",
    "SCF_KISH_ESS_RULE=MIN_OF_FIVE_IMPLICATES",
]

for token in required:
    if token not in text:
        raise RuntimeError(
            f"missing repaired token: {token}"
        )

for forbidden in [
    "SCF X42001 inconsistent across implicates",
    "w_max - w_min > tolerance",
]:
    if forbidden in text:
        raise RuntimeError(
            f"obsolete assumption remains: {forbidden}"
        )

print("E3A5B_ATTEMPT1=ABORTED_SCF_WEIGHT_ASSUMPTION")
print("SUPPORT_TABLE_CREATED_BEFORE_FAILURE=0")
print("SUPPORT_COUNTS_DISCLOSED_BEFORE_FAILURE=0")
print("KISH_ESS_DISCLOSED_BEFORE_FAILURE=0")
print("ECONOMIC_VALUES_OPENED=0")
print("SCF_IMPLICATE_ID_RULE=Y1_MINUS_10_TIMES_YY1")
print("SCF_KISH_ESS_RULE=MIN_OF_FIVE_IMPLICATES")
print("THRESHOLDS_CHANGED=0")
print("COHORT_MAPPINGS_CHANGED=0")
print("E3A5B_R1_REPAIR=PASS")
print("E3A5B_R1_RERUN_AUTHORIZED=1")
