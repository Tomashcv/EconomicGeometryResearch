from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FAILED = (
    ROOT
    / "data"
    / "metadata"
    / "E3A5A_attempt1_pandas30_api_failure.txt"
)

SCRIPT = (
    ROOT
    / "scripts"
    / "E3A5A_source_schema_inventory.py"
)

if not FAILED.exists():
    raise RuntimeError("attempt-1 failure log missing")

failure = FAILED.read_text(
    encoding="utf-8",
    errors="replace",
)

required_failure = [
    "AttributeError",
    "StataReader",
    "close",
]

for token in required_failure:
    if token not in failure:
        raise RuntimeError(
            f"missing failure evidence: {token}"
        )

text = SCRIPT.read_text(encoding="utf-8")

if "reader.close()" in text:
    raise RuntimeError(
        "removed pandas API call still present"
    )

required_repair = [
    'with path.open("rb") as fh:',
    "pd.io.stata.StataReader(",
    "reader.variable_labels()",
]

for token in required_repair:
    if token not in text:
        raise RuntimeError(
            f"repair token missing: {token}"
        )

print("E3A5A_ATTEMPT1=ABORTED_PANDAS30_API")
print("DATA_ROWS_PARSED_BEFORE_FAILURE=0")
print("SUPPORT_COUNTS_OPENED=0")
print("ECONOMIC_VALUES_OPENED=0")
print("PANDAS30_STATA_READER_REPAIR=PASS")
print("E3A5A_R1_RERUN_AUTHORIZED=1")
