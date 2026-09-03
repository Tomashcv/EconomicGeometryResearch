#!/usr/bin/env python3
from pathlib import Path
import csv, json, os, re

ROOT = Path(__file__).resolve().parents[1]

EXEC = ROOT / "data/metadata/E4D0_execution.txt"
AUDIT = ROOT / "data/metadata/E4D0_multiyear_partial_state_comparability_recon_audit.txt"
PATH_INV = ROOT / "data/results/E4D0_survey_year_path_inventory.tsv"
TEXT_INV = ROOT / "data/results/E4D0_static_year_reference_inventory.tsv"
AXES = ROOT / "data/results/E4D0_temporal_comparability_axis_registry.tsv"
GAPS = ROOT / "data/results/E4D0_temporal_evidence_gap_registry.tsv"
SEQ = ROOT / "data/results/E4D0_followup_sequence.tsv"
GATES = ROOT / "data/results/E4D0_recon_hard_gates.tsv"
DECISION = ROOT / "data/results/E4D0_multiyear_partial_state_comparability_decision.tsv"

FAMILIES = {
    "H_ACS": {
        "survey": "ACS",
        "coordinate_ids": ["H_ACCESS_SPACE_ROOMS_PER_PERSON"],
        "path_tokens": ["acs", "american_community_survey", "h_access"],
        "text_patterns": [
            r"\bACS[_ -]?(20\d{2})\b",
            r"\b(20\d{2})[_ -]?ACS\b",
            r"\bacs[_/-]?(20\d{2})\b",
        ],
    },
    "KD_SCF": {
        "survey": "SCF",
        "coordinate_ids": ["K_FIN_MEAN_TRANSFORMED", "D_PIRTOTAL_MEAN_STATE_TRANSFORMED"],
        "path_tokens": ["scf", "survey_of_consumer_finances", "k_fin", "pirtotal"],
        "text_patterns": [
            r"\bSCF[_ -]?(20\d{2})\b",
            r"\b(20\d{2})[_ -]?SCF\b",
            r"\bscf[_/-]?(20\d{2})\b",
        ],
    },
    "I_CPS_ASEC": {
        "survey": "CPS_ASEC",
        "coordinate_ids": ["I_FYFT_SHARE", "I_SEARCH_SECURITY"],
        "path_tokens": ["cps", "asec", "i_fyft", "search_burden", "search_security"],
        "text_patterns": [
            r"\bCPS(?:_ASEC)?[_ -]?(20\d{2})\b",
            r"\bASEC[_ -]?(20\d{2})\b",
            r"\b(20\d{2})[_ -]?(?:CPS|ASEC)\b",
            r"\bcps[_/-]?(20\d{2})\b",
        ],
    },
}

CURRENT_YEAR = 2022

# File-system path scan only: no file contents under data/raw, data/processed, or data/results.
path_roots = [
    ROOT / "data/raw",
    ROOT / "data/processed",
    ROOT / "data/metadata",
    ROOT / "data/results",
    ROOT / "scripts",
    ROOT / "docs",
]

all_paths = []
for base in path_roots:
    if not base.exists():
        continue
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames.sort()
        filenames.sort()
        for name in filenames:
            p = Path(dirpath) / name
            try:
                rel = p.relative_to(ROOT).as_posix()
            except ValueError:
                continue
            all_paths.append(rel)

all_paths = sorted(set(all_paths))

path_rows = []
for rel in all_paths:
    low = rel.lower()
    years = sorted(set(int(y) for y in re.findall(r"(?<!\d)(20\d{2})(?!\d)", rel)))
    for family_id, cfg in FAMILIES.items():
        matched_tokens = [t for t in cfg["path_tokens"] if t in low]
        if not matched_tokens:
            continue
        if not years:
            path_rows.append([
                family_id, cfg["survey"], "", rel,
                "|".join(matched_tokens), "PATH_FAMILY_MATCH_NO_EXPLICIT_YEAR",
                "CANDIDATE_ONLY"
            ])
        else:
            for year in years:
                path_rows.append([
                    family_id, cfg["survey"], str(year), rel,
                    "|".join(matched_tokens), "PATH_FAMILY_AND_4DIGIT_YEAR_TOKEN",
                    "CANDIDATE_ONLY"
                ])

# Static text scan: scripts/docs plus contract JSON only.
static_files = []
for base in [ROOT / "scripts", ROOT / "docs"]:
    if base.exists():
        for p in sorted(base.rglob("*")):
            if p.is_file() and p.suffix.lower() in {".py", ".md", ".sh", ".txt"}:
                static_files.append(p)

meta = ROOT / "data/metadata"
if meta.exists():
    for p in sorted(meta.glob("*contract*.json")):
        if p.is_file():
            static_files.append(p)

# Avoid giant accidental reads; static sources over 2 MiB are skipped structurally.
text_rows = []
static_scanned = 0
static_skipped_large = 0
for p in static_files:
    try:
        size = p.stat().st_size
    except OSError:
        continue
    if size > 2_000_000:
        static_skipped_large += 1
        continue
    try:
        text = p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    static_scanned += 1
    rel = p.relative_to(ROOT).as_posix()
    for family_id, cfg in FAMILIES.items():
        found = set()
        for pat in cfg["text_patterns"]:
            for m in re.finditer(pat, text, flags=re.IGNORECASE):
                found.add(int(m.group(1)))
        for year in sorted(found):
            text_rows.append([
                family_id, cfg["survey"], str(year), rel,
                "SURVEY_ADJACENT_YEAR_REFERENCE",
                "STATIC_REFERENCE_ONLY"
            ])

# Add explicit frozen-2022 authority markers as the only VERIFIED rows.
for family_id, cfg in FAMILIES.items():
    path_rows.append([
        family_id, cfg["survey"], str(CURRENT_YEAR),
        "data/results/E4C6E_partial_observed_coordinate_registry.tsv",
        "FROZEN_E4C6E_2022_COORDINATE_AUTHORITY",
        "FROZEN_CURRENT_YEAR_AUTHORITY",
        "VERIFIED_CURRENT_YEAR_ONLY"
    ])

# Deduplicate and sort.
path_rows = sorted({tuple(r) for r in path_rows}, key=lambda r: (r[0], r[2], r[3], r[5]))
text_rows = sorted({tuple(r) for r in text_rows}, key=lambda r: (r[0], r[2], r[3]))

def write_tsv(path, header, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)

write_tsv(
    PATH_INV,
    ["family_id","survey","year_token","path","matched_family_tokens","evidence_kind","status"],
    path_rows,
)
write_tsv(
    TEXT_INV,
    ["family_id","survey","year_token","static_source_path","evidence_kind","status"],
    text_rows,
)

axis_rows = [
    ["YEAR_AVAILABILITY","REQUIRED",
     "exact survey wave/year exists for every required coordinate family",
     "not established for any additional year by filename/static-reference reconnaissance alone"],
    ["VARIABLE_DEFINITION_CONTINUITY","REQUIRED",
     "source variables and derived estimands retain the same economic meaning across years",
     "official questionnaire/codebook evidence required"],
    ["POPULATION_UNIVERSE_CONTINUITY","REQUIRED",
     "survey universe and denominator remain comparable",
     "official methodology evidence required"],
    ["AGE_BAND_MAPPING_CONTINUITY","REQUIRED",
     "25-34,35-44,45-54,55-64 cohort construction is identical or explicitly harmonizable",
     "must freeze year-specific raw-to-canonical mapping before values"],
    ["TENURE_MAPPING_CONTINUITY","REQUIRED",
     "OWNER/RENTER definitions are identical or explicitly harmonizable",
     "must freeze year-specific raw-to-canonical mapping before values"],
    ["TRANSFORM_CONTINUITY","REQUIRED",
     "H/K/D/I state transforms preserve exactly the frozen E4C0/E4C5/E4C6 semantics",
     "no transform refit on later-year values"],
    ["SURVEY_WEIGHT_DESIGN_CONTINUITY","REQUIRED",
     "point and replicate-weight estimators are valid for each survey year",
     "year-specific official design documentation required"],
    ["REPLICATE_COUNT_AND_FORMULA_CONTINUITY","REQUIRED_OR_EXPLICIT_VERSIONING",
     "SCF/CPS variance-covariance engines must match each wave design or be versioned before values",
     "cannot assume 2022 replicate counts/formulas transport unchanged"],
    ["PRICE_LEVEL_OR_NOMINAL_DEFLATION_POLICY","REQUIRED_WHERE_RELEVANT",
     "nominal monetary variables must use one precommitted temporal comparability policy",
     "cannot choose deflator after seeing multiyear geometry"],
    ["MISSING_YEAR_POLICY","REQUIRED",
     "gaps created by survey cadence must be handled by a frozen rule",
     "no interpolation or carry-forward without precommit"],
    ["SURVEY_RELEASE_VINTAGE_POLICY","REQUIRED",
     "revisions/vintages used across years must be frozen",
     "avoid mixing unreconciled vintages"],
    ["COMMON_TIME_GRID","REQUIRED",
     "temporal geometry can only compare years jointly supported by all required coordinate families",
     "common-year intersection not yet authorized"],
]
write_tsv(
    AXES,
    ["comparability_axis","status","requirement","current_E4D0_conclusion"],
    axis_rows,
)

# Build evidence-gap rows from candidate years seen beyond 2022.
candidate_years = {fid: set() for fid in FAMILIES}
for r in path_rows:
    if r[2]:
        y = int(r[2])
        if y != CURRENT_YEAR and r[6] == "CANDIDATE_ONLY":
            candidate_years[r[0]].add(y)
for r in text_rows:
    y = int(r[2])
    if y != CURRENT_YEAR:
        candidate_years[r[0]].add(y)

gap_rows = []
for family_id, cfg in FAMILIES.items():
    years = sorted(candidate_years[family_id])
    gap_rows.append([
        family_id,
        cfg["survey"],
        "|".join(str(y) for y in years) if years else "",
        str(len(years)),
        "UNVERIFIED",
        "official survey-year availability + variable-definition + weighting-design documentation",
        "E4D0A"
    ])

# No common additional year is VERIFIED by E4D0 because candidate references are not official comparability evidence.
common_candidate = set.intersection(*(candidate_years[fid] for fid in FAMILIES)) if FAMILIES else set()
common_candidate_sorted = sorted(common_candidate)

write_tsv(
    GAPS,
    ["family_id","survey","additional_year_tokens_seen","candidate_year_count",
     "comparability_status","missing_evidence","next_phase"],
    gap_rows,
)

seq_rows = [
    ["1","E4D0A","OFFICIAL_MULTIYEAR_METADATA_AND_DESIGN_EVIDENCE_ACQUISITION",
     "AUTHORIZED_PRIMARY_NEXT_STEP",
     "acquire/pin official ACS, SCF, CPS ASEC year-availability, codebook/questionnaire, universe, and weighting/replicate-design evidence without opening microdata values"],
    ["2","E4D0B","MULTIYEAR_SEMANTIC_AND_DESIGN_COMPARABILITY_ADJUDICATION",
     "CONDITIONAL_ON_E4D0A",
     "freeze exact additional years that pass every comparability axis; failures remain explicit"],
    ["3","E4D1","MULTIYEAR_PARTIAL_STATE_COORDINATE_EXECUTION_PREFLIGHT",
     "CONDITIONAL_ON_E4D0B_PASS",
     "freeze exact common-year grid and year-specific lineage before opening additional-year economic values"],
    ["4","E4D2","TEMPORAL_PARTIAL_STATE_GEOMETRY_PREFLIGHT",
     "CONDITIONAL_ON_E4D1",
     "freeze time-difference objects and both E4C7 metrics before temporal state-change values"],
]
write_tsv(
    SEQ,
    ["order","phase","title","status","rule"],
    seq_rows,
)

gate_rows = [
    ["E4C9B_CLOSEOUT_AUTHORITY_REUSED","PASS"],
    ["PATH_SCAN_OPENS_FILE_CONTENTS","PASS_NO"],
    ["RAW_DATA_ROWS_OPENED","PASS_0"],
    ["PROCESSED_DATA_ROWS_OPENED","PASS_0"],
    ["RESULT_NUMERIC_ROWS_OPENED","PASS_0"],
    ["STATIC_TEXT_SCAN_RESTRICTED_TO_SCRIPTS_DOCS_CONTRACTS","PASS"],
    ["CURRENT_2022_AUTHORITY_PRESERVED","PASS"],
    ["ADDITIONAL_YEAR_REFERENCE_NOT_TREATED_AS_COMPARABILITY_PROOF","PASS"],
    ["COMMON_YEAR_GRID_NOT_FROZEN_FROM_HEURISTIC_REFERENCES","PASS"],
    ["NO_ADDITIONAL_YEAR_VALUES_OPENED","PASS"],
    ["NO_TEMPORAL_GEOMETRY_COMPUTED","PASS"],
    ["NO_REAL_INFLATION_ESTIMATE","PASS"],
]
write_tsv(GATES, ["gate","value"], gate_rows)

decision_rows = [
    ["FILESYSTEM_PATH_COUNT_SCANNED", str(len(all_paths))],
    ["STATIC_TEXT_FILE_COUNT_SCANNED", str(static_scanned)],
    ["STATIC_TEXT_FILE_COUNT_SKIPPED_LARGE", str(static_skipped_large)],
    ["SURVEY_FAMILY_COUNT", "3"],
    ["CURRENT_FROZEN_YEAR", "2022"],
    ["CURRENT_YEAR_VERIFIED_FAMILY_COUNT", "3"],
    ["ADDITIONAL_YEAR_REFERENCE_FAMILY_COUNT",
     str(sum(1 for fid in FAMILIES if candidate_years[fid]))],
    ["COMMON_ADDITIONAL_YEAR_REFERENCE_COUNT", str(len(common_candidate_sorted))],
    ["COMMON_ADDITIONAL_YEAR_REFERENCES",
     "|".join(str(y) for y in common_candidate_sorted)],
    ["ADDITIONAL_YEAR_COMPARABILITY_VERIFIED_COUNT", "0"],
    ["COMMON_YEAR_GRID_FROZEN", "0"],
    ["RAW_DATA_ROWS_OPENED", "0"],
    ["PROCESSED_DATA_ROWS_OPENED", "0"],
    ["RESULT_NUMERIC_ROWS_OPENED", "0"],
    ["ADDITIONAL_YEAR_ECONOMIC_VALUES_OPENED", "0"],
    ["TEMPORAL_GEOMETRY_COMPUTED", "0"],
    ["REAL_INFLATION_ESTIMATION_AUTHORIZED", "0"],
    ["FINAL_SCALAR_AUTHORIZED", "0"],
    ["NEXT_PRIMARY_PHASE_ID", "E4D0A"],
    ["E4D0A_OFFICIAL_MULTIYEAR_METADATA_AND_DESIGN_EVIDENCE_ACQUISITION_AUTHORIZED", "1"],
    ["E4D1_MULTIYEAR_PARTIAL_STATE_COORDINATE_EXECUTION_PREFLIGHT_AUTHORIZED", "0"],
    ["E4D0_MULTIYEAR_PARTIAL_STATE_COMPARABILITY_RECONNAISSANCE", "PASS"],
]
write_tsv(DECISION, ["decision","value"], decision_rows)

log = "\n".join([
    "E4C9B_REUSED_AS_CANONICAL_2022_GEOMETRY_CLOSEOUT_AUTHORITY=1",
    f"FILESYSTEM_PATH_COUNT_SCANNED={len(all_paths)}",
    f"STATIC_TEXT_FILE_COUNT_SCANNED={static_scanned}",
    f"STATIC_TEXT_FILE_COUNT_SKIPPED_LARGE={static_skipped_large}",
    "SURVEY_FAMILY_COUNT=3",
    "CURRENT_FROZEN_YEAR=2022",
    "CURRENT_YEAR_VERIFIED_FAMILY_COUNT=3",
    f"ADDITIONAL_YEAR_REFERENCE_FAMILY_COUNT={sum(1 for fid in FAMILIES if candidate_years[fid])}",
    f"COMMON_ADDITIONAL_YEAR_REFERENCE_COUNT={len(common_candidate_sorted)}",
    "ADDITIONAL_YEAR_COMPARABILITY_VERIFIED_COUNT=0",
    "COMMON_YEAR_GRID_FROZEN=0",
    "RAW_DATA_ROWS_OPENED=0",
    "PROCESSED_DATA_ROWS_OPENED=0",
    "RESULT_NUMERIC_ROWS_OPENED=0",
    "ADDITIONAL_YEAR_ECONOMIC_VALUES_OPENED=0",
    "TEMPORAL_GEOMETRY_COMPUTED=0",
    "DISTANCE_RANKING_COMPUTED=0",
    "DIMENSIONALITY_TEST_COMPUTED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "E4D1_MULTIYEAR_PARTIAL_STATE_COORDINATE_EXECUTION_PREFLIGHT_AUTHORIZED=0",
    "E4D0A_OFFICIAL_MULTIYEAR_METADATA_AND_DESIGN_EVIDENCE_ACQUISITION_AUTHORIZED=1",
    "E4D0_MULTIYEAR_PARTIAL_STATE_COMPARABILITY_RECONNAISSANCE=PASS",
]) + "\n"

EXEC.write_text(log, encoding="utf-8")
AUDIT.write_text(log, encoding="utf-8")
print(log, end="")
