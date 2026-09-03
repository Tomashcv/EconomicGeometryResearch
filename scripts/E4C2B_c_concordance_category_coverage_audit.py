#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "data/metadata/E4C2B_c_concordance_category_coverage_audit_contract.json"
LINEAGE = ROOT / "data/metadata/E4C2B_frozen_input_lineage.tsv"
C_MAP = ROOT / "data/metadata/E3B3C1_component_ucc_map.tsv"
RAW = ROOT / "data/raw/reference_metadata/E4C2B"
CPI = RAW / "ce-cpi-concordance-2022.xlsx"
PUB = RAW / "index-publication-level-current.xlsx"
PCE = RAW / "pce_concordance-current.xlsx"
MANIFEST = ROOT / "data/metadata/E4C2B_official_source_manifest.tsv"
EXEC = ROOT / "data/metadata/E4C2B_execution.txt"
AUDIT = ROOT / "data/metadata/E4C2B_c_concordance_category_coverage_audit.txt"
COVERAGE = ROOT / "data/results/E4C2B_2022_c_ucc_concordance_coverage.tsv"
SUMMARY = ROOT / "data/results/E4C2B_c_category_coverage_summary.tsv"
CONSTRAINTS = ROOT / "data/results/E4C2B_c_identification_constraints.tsv"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def norm_text(x: object) -> str:
    s = "" if x is None else str(x)
    s = s.replace("\xa0", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def norm_header(x: object) -> str:
    s = norm_text(x).upper()
    s = re.sub(r"[^A-Z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def norm_ucc(x: object) -> str:
    s = norm_text(x)
    if re.fullmatch(r"\d+(?:\.0+)?", s):
        s = s.split(".", 1)[0]
    s = re.sub(r"\D", "", s)
    return s.zfill(6) if 1 <= len(s) <= 6 else ""


def col_index(cell_ref: str) -> int:
    m = re.match(r"([A-Z]+)", cell_ref)
    if not m:
        return 0
    n = 0
    for ch in m.group(1):
        n = n * 26 + (ord(ch) - 64)
    return n - 1


class XlsxTextReader:
    NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    RNS = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}
    DOC_R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"

    def __init__(self, path: Path):
        self.path = path
        self.z = zipfile.ZipFile(path)
        if "[Content_Types].xml" not in self.z.namelist():
            raise RuntimeError(f"not a valid XLSX package: {path}")
        self.shared = self._shared_strings()
        self.sheets = self._sheet_paths()

    def _shared_strings(self) -> list[str]:
        if "xl/sharedStrings.xml" not in self.z.namelist():
            return []
        root = ET.fromstring(self.z.read("xl/sharedStrings.xml"))
        out = []
        for si in root.findall("m:si", self.NS):
            parts = [t.text or "" for t in si.iterfind(".//m:t", self.NS)]
            out.append("".join(parts))
        return out

    def _sheet_paths(self) -> list[tuple[str, str]]:
        wb = ET.fromstring(self.z.read("xl/workbook.xml"))
        rel = ET.fromstring(self.z.read("xl/_rels/workbook.xml.rels"))
        relmap = {r.attrib["Id"]: r.attrib["Target"] for r in rel}
        out = []
        for s in wb.findall("m:sheets/m:sheet", self.NS):
            name = s.attrib.get("name", "")
            rid = s.attrib[self.DOC_R]
            target = relmap[rid]
            if target.startswith("/"):
                target = target.lstrip("/")
            elif not target.startswith("xl/"):
                target = "xl/" + target
            target = os.path.normpath(target).replace("\\", "/")
            out.append((name, target))
        return out

    def rows(self, sheet_path: str) -> list[list[str]]:
        root = ET.fromstring(self.z.read(sheet_path))
        out: list[list[str]] = []
        for row in root.findall(".//m:sheetData/m:row", self.NS):
            vals: dict[int, str] = {}
            maxc = -1
            for c in row.findall("m:c", self.NS):
                ref = c.attrib.get("r", "A1")
                ci = col_index(ref)
                maxc = max(maxc, ci)
                t = c.attrib.get("t", "")
                v = c.find("m:v", self.NS)
                if t == "inlineStr":
                    parts = [x.text or "" for x in c.iterfind(".//m:t", self.NS)]
                    val = "".join(parts)
                elif v is None:
                    val = ""
                elif t == "s":
                    idx = int(v.text or 0)
                    val = self.shared[idx] if 0 <= idx < len(self.shared) else ""
                else:
                    val = v.text or ""
                vals[ci] = norm_text(val)
            if maxc >= 0:
                out.append([vals.get(i, "") for i in range(maxc + 1)])
        return out

    def all_sheets(self) -> list[tuple[str, list[list[str]]]]:
        return [(name, self.rows(path)) for name, path in self.sheets]


def find_header(sheets, required_groups):
    """Return sheet, row-index, row, and a mapping of group->column index."""
    for sname, rows in sheets:
        for ri, row in enumerate(rows[:80]):
            nh = [norm_header(x) for x in row]
            found = {}
            ok = True
            for group, patterns in required_groups.items():
                idx = None
                for i, h in enumerate(nh):
                    if any((p == h) or (p in h) for p in patterns):
                        idx = i
                        break
                if idx is None:
                    ok = False
                    break
                found[group] = idx
            if ok:
                return sname, ri, row, found
    raise RuntimeError(f"could not locate header groups={required_groups}")


def parse_cpi(path: Path):
    r = XlsxTextReader(path)
    sheets = r.all_sheets()
    sname, ri, header, cols = find_header(
        sheets,
        {
            "ucc": ["UCC", "UCC CODE"],
            "eli": ["ELI", "ELI CODE"],
        },
    )
    rows = dict(sheets)[sname]
    out = defaultdict(set)
    for row in rows[ri + 1 :]:
        if cols["ucc"] >= len(row) or cols["eli"] >= len(row):
            continue
        ucc = norm_ucc(row[cols["ucc"]])
        eli = norm_text(row[cols["eli"]]).upper().replace(" ", "")
        if re.fullmatch(r"\d{6}", ucc) and re.fullmatch(r"[A-Z0-9]{4,8}", eli):
            out[ucc].add(eli)
    return out, sname, norm_text(" | ".join(header))


def parse_publication(path: Path):
    r = XlsxTextReader(path)
    sheets = r.all_sheets()
    sname, ri, header, cols = find_header(
        sheets,
        {
            "code": ["ITEM CODE"],
            "title": ["ITEM TITLE"],
            "us": ["PUBLISHED FOR U S CITY AVERAGE", "U S CITY AVERAGE"],
        },
    )
    rows = dict(sheets)[sname]
    out = {}
    for row in rows[ri + 1 :]:
        if cols["code"] >= len(row):
            continue
        code = norm_text(row[cols["code"]]).upper().replace(" ", "")
        if not code:
            continue
        us = row[cols["us"]] if cols["us"] < len(row) else ""
        title = row[cols["title"]] if cols["title"] < len(row) else ""
        out[code] = {"us": norm_text(us).upper(), "title": norm_text(title)}
    return out, sname, norm_text(" | ".join(header))


def parse_pce_uccs(path: Path):
    r = XlsxTextReader(path)
    sheets = r.all_sheets()
    found = Counter()
    header_records = []
    for sname, rows in sheets:
        header_idx = None
        ucc_col = None
        for ri, row in enumerate(rows[:100]):
            nh = [norm_header(x) for x in row]
            for i, h in enumerate(nh):
                if h == "UCC" or "UCC CODE" in h or h.startswith("UCC "):
                    header_idx = ri
                    ucc_col = i
                    header_records.append((sname, ri, norm_text(" | ".join(row))))
                    break
            if header_idx is not None:
                break
        if header_idx is None or ucc_col is None:
            continue
        for row in rows[header_idx + 1 :]:
            if ucc_col >= len(row):
                continue
            u = norm_ucc(row[ucc_col])
            if re.fullmatch(r"\d{6}", u):
                found[u] += 1
    if not header_records:
        raise RuntimeError("no UCC column located in PCE concordance workbook")
    return found, header_records


def read_tsv(path: Path):
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
lineage = read_tsv(LINEAGE)
for row in lineage:
    p = ROOT / row["artifact"]
    if not p.exists() or sha256(p) != row["sha256"]:
        raise RuntimeError(f"frozen input lineage mismatch: {row['artifact']}")

for p in (CPI, PUB, PCE, MANIFEST):
    if not p.exists():
        raise RuntimeError(f"missing post-precommit official source: {p}")

cmap = read_tsv(C_MAP)
crows = [r for r in cmap if r.get("primary_component") == "C_COST"]
cuccs = [norm_ucc(r.get("ucc", "")) for r in crows]
if len(crows) != 435 or len(set(cuccs)) != 435 or any(not re.fullmatch(r"\d{6}", u) for u in cuccs):
    raise RuntimeError("frozen C_COST universe is not exactly 435 unique six-digit UCCs")
if any(norm_text(r.get("broad_category", "")).upper() == "HOUSING" for r in crows):
    raise RuntimeError("housing unexpectedly present in primary C_COST")

cpi_map, cpi_sheet, cpi_header = parse_cpi(CPI)
pub_map, pub_sheet, pub_header = parse_publication(PUB)
pce_counts, pce_headers = parse_pce_uccs(PCE)

coverage_rows = []
for r in sorted(crows, key=lambda x: norm_ucc(x["ucc"])):
    u = norm_ucc(r["ucc"])
    elis = sorted(cpi_map.get(u, set()))
    derived = sorted({"SE" + e[:4] for e in elis if len(e) >= 4})
    pub_matches = [code for code in derived if code in pub_map]
    pub_us_yes = any(pub_map[code]["us"] in {"Y", "YES"} for code in pub_matches)
    coverage_rows.append({
        "ucc": u,
        "source": r.get("source", ""),
        "factor": r.get("factor", ""),
        "broad_category": r.get("broad_category", ""),
        "subcategory": r.get("subcategory", ""),
        "cpi_2022_eli_mapped": "YES" if elis else "NO",
        "cpi_2022_eli_count": str(len(elis)),
        "cpi_2022_eli_codes": ";".join(elis),
        "derived_item_stratum_codes": ";".join(derived),
        "current_publication_metadata_match": "YES" if pub_matches else "NO",
        "current_us_city_average_published_any": "YES" if pub_us_yes else "NO",
        "publication_temporal_status": "CURRENT_METADATA_NOT_2022_ARCHIVE",
        "pce_concordance_mapped": "YES" if pce_counts.get(u, 0) else "NO",
        "pce_concordance_row_count": str(pce_counts.get(u, 0)),
    })

COVERAGE.parent.mkdir(parents=True, exist_ok=True)
with COVERAGE.open("w", encoding="utf-8", newline="") as f:
    fields = list(coverage_rows[0].keys())
    w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
    w.writeheader(); w.writerows(coverage_rows)

cats = sorted({r["broad_category"] for r in coverage_rows})
summary_rows = []
for cat in ["ALL"] + cats:
    sub = coverage_rows if cat == "ALL" else [r for r in coverage_rows if r["broad_category"] == cat]
    summary_rows.append({
        "scope": cat,
        "frozen_c_uccs": str(len(sub)),
        "cpi_2022_eli_mapped_uccs": str(sum(r["cpi_2022_eli_mapped"] == "YES" for r in sub)),
        "current_publication_metadata_matched_uccs": str(sum(r["current_publication_metadata_match"] == "YES" for r in sub)),
        "pce_concordance_mapped_uccs": str(sum(r["pce_concordance_mapped"] == "YES" for r in sub)),
        "both_cpi_and_pce_mapped_uccs": str(sum((r["cpi_2022_eli_mapped"] == "YES") and (r["pce_concordance_mapped"] == "YES") for r in sub)),
    })
with SUMMARY.open("w", encoding="utf-8", newline="") as f:
    fields = list(summary_rows[0].keys())
    w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
    w.writeheader(); w.writerows(summary_rows)

constraints = [
    ("FROZEN_C_COST_UCC_UNIVERSE", "435_UNIQUE_UCCS_PASS", "The audit uses the previously frozen C_COST UCC set without mutation."),
    ("CPI_2022_CONCORDANCE_ROLE", "CLASSIFICATION_LINEAGE_ONLY", "The January-2022 concordance maps CE UCCs to CPI ELIs; it supplies no authorized price levels here."),
    ("CPI_INDEX_LEVEL_AS_CROSS_CATEGORY_PRICE_LEVEL", "PROHIBITED", "CPI index-number levels across different item strata are not a physical cross-category price vector."),
    ("CURRENT_CPI_PUBLICATION_METADATA_AS_2022_ARCHIVE", "PROHIBITED", "The current publication-level workbook is not silently treated as a 2022 publication archive."),
    ("PCE_CONCORDANCE_ROLE", "CLASSIFICATION_LINEAGE_ONLY", "UCC-to-PCE mapping does not by itself identify age-by-tenure real quantities."),
    ("C_A_COMPLETE_REFERENCE_PRICE_VECTOR_RESOLVED", "NO", "Average-price coverage was already known incomplete and E4C2B opens no price values."),
    ("C_B_REAL_QUANTITY_CROSS_SECTIONAL_IDENTIFICATION_RESOLVED", "NO", "Classification coverage alone does not define a cross-category real-quantity aggregator for the eight cells."),
    ("C_C_K_D_I_OVERLAP_RESOLVED", "NO", "No resource denominator is selected in this audit."),
    ("EQUIVALENCE_SCALE_PLACEMENT_SELECTED", "NO", "Household composition adjustment remains a later ex-ante semantic decision."),
    ("C_ARCHITECTURE_SELECTED", "NO", "No C architecture is selected from mapping coverage or outcomes."),
]
with CONSTRAINTS.open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t", lineterminator="\n")
    w.writerow(["constraint", "status", "interpretation"])
    w.writerows(constraints)

all_summary = summary_rows[0]
lines = [
    "================================================================================",
    "ECONOMIC GEOMETRY RESEARCH — E4C2B",
    "C CONCORDANCE + CATEGORY COVERAGE AUDIT",
    "OFFICIAL CLASSIFICATION METADATA ONLY",
    "================================================================================",
    "",
    "RAW_SURVEY_DATA_READ=0",
    "NEW_CEX_ECONOMIC_VALUES_OPENED=0",
    "CPI_INDEX_VALUES_OPENED=0",
    "CPI_AVERAGE_PRICE_VALUES_OPENED=0",
    "PCE_EXPENDITURE_VALUES_OPENED=0",
    "PCE_PRICE_INDEX_VALUES_OPENED=0",
    "PCE_QUANTITY_INDEX_VALUES_OPENED=0",
    "REGIONAL_PRICE_PARITY_VALUES_OPENED=0",
    "C_COORDINATE_VALUES_COMPUTED=0",
    "TRANSFORMED_VALUES_COMPUTED=0",
    "GEOMETRY_PERFORMED=0",
    "",
    "===== FROZEN C UNIVERSE =====",
    "FROZEN_C_COST_UCCS=435",
    "FROZEN_C_COST_UNIQUE_UCCS=435",
    "HOUSING_UCCS_IN_PRIMARY_C_COST=0",
    "FROZEN_C_COST_UNIVERSE=PASS",
    "",
    "===== OFFICIAL WORKBOOK SCHEMA DISCOVERY =====",
    f"CPI_2022_WORKBOOK_SHEET={cpi_sheet}",
    f"CPI_2022_HEADER_DISCOVERED={int(bool(cpi_header))}",
    f"CURRENT_PUBLICATION_WORKBOOK_SHEET={pub_sheet}",
    f"CURRENT_PUBLICATION_HEADER_DISCOVERED={int(bool(pub_header))}",
    f"PCE_UCC_HEADER_SHEETS={len(pce_headers)}",
    "WORKBOOK_SCHEMA_DISCOVERY=PASS",
    "",
    "===== MAPPING COVERAGE — DIAGNOSTIC NOT OUTCOME GATE =====",
    f"CPI_2022_ELI_MAPPED_UCCS_OF_435={all_summary['cpi_2022_eli_mapped_uccs']}",
    f"CURRENT_PUBLICATION_METADATA_MATCHED_UCCS_OF_435={all_summary['current_publication_metadata_matched_uccs']}",
    f"PCE_CONCORDANCE_MAPPED_UCCS_OF_435={all_summary['pce_concordance_mapped_uccs']}",
    f"BOTH_CPI_AND_PCE_MAPPED_UCCS_OF_435={all_summary['both_cpi_and_pce_mapped_uccs']}",
    "MAPPING_COVERAGE_USED_AS_ARCHITECTURE_OUTCOME_GATE=0",
    "",
    "===== IDENTIFICATION BOUNDARY =====",
    "CPI_INDEX_LEVEL_AS_CROSS_CATEGORY_PRICE_LEVEL_AUTHORIZED=0",
    "CURRENT_PUBLICATION_METADATA_EQUALS_2022_ARCHIVE=0",
    "C_A_COMPLETE_REFERENCE_PRICE_VECTOR_RESOLVED=0",
    "C_B_REAL_QUANTITY_CROSS_SECTIONAL_IDENTIFICATION_RESOLVED=0",
    "C_C_K_D_I_OVERLAP_RESOLVED=0",
    "EQUIVALENCE_SCALE_PLACEMENT_SELECTED=0",
    "C_ARCHITECTURE_SELECTED=0",
    "",
    "===== HARD BOUNDARY =====",
    "C_COORDINATE_VALUES_AUTHORIZED=0",
    "FIVE_COMPONENT_STATE_VECTOR_AUTHORIZED=0",
    "FIVE_COMPONENT_NORMALIZATION_AUTHORIZED=0",
    "DIMENSIONALITY_TEST_AUTHORIZED=0",
    "REAL_INFLATION_ESTIMATION_AUTHORIZED=0",
    "FINAL_SCALAR_AUTHORIZED=0",
    "",
    "E4C2B_C_CONCORDANCE_AND_CATEGORY_COVERAGE_AUDIT=PASS",
    "E4C2C_C_IDENTIFICATION_AND_ARCHITECTURE_DECISION_PREFLIGHT_AUTHORIZED=1",
]
text = "\n".join(lines) + "\n"
EXEC.write_text(text, encoding="utf-8")
AUDIT.write_text(text, encoding="utf-8")
print(text, end="")
