from __future__ import annotations

from pathlib import Path
import csv
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def read_kv_tsv(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8", newline="") as f:
        rows = csv.DictReader(f, delimiter="\t")
        return {row["decision"]: row["value"] for row in rows}


class PublicReleaseIntegrityTests(unittest.TestCase):
    def test_raw_data_is_not_bundled(self) -> None:
        raw = ROOT / "data" / "raw"
        self.assertFalse(raw.exists())

    def test_svg_is_valid_xml(self) -> None:
        ET.parse(ROOT / "docs" / "assets" / "research_pipeline.svg")

    def test_e2b_negative_robustness_result_is_preserved(self) -> None:
        text = (ROOT / "results" / "selected" / "E2B_robustness_summary.txt").read_text(encoding="utf-8")
        self.assertIn("E2B_ROBUSTNESS_SURVIVES=0", text)
        self.assertIn("H1 multidimensionality is not established", text)

    def test_partial_geometry_stays_pre_scalar(self) -> None:
        d = read_kv_tsv(
            ROOT / "results" / "selected" /
            "E4C9A_partial_state_descriptive_geometry_execution_decision.tsv"
        )
        self.assertEqual(d["E4C9A_PARTIAL_STATE_DESCRIPTIVE_GEOMETRY_EXECUTION"], "PASS")
        self.assertEqual(d["REAL_INFLATION_ESTIMATION_AUTHORIZED"], "0")
        self.assertEqual(d["FINAL_SCALAR_AUTHORIZED"], "0")
        self.assertEqual(d["PCA_COMPUTED"], "0")

    def test_multiyear_snapshot_stays_pre_temporal_geometry(self) -> None:
        d = read_kv_tsv(
            ROOT / "results" / "selected" /
            "E4D1D3_CPSI_R1_P0_precommit_decision.tsv"
        )
        self.assertEqual(d["E4D1D3_CPSI_R1_P0_REPLICATE_ZIP_CASE_REPAIR_PRECOMMIT"], "PASS")
        self.assertEqual(d["TEMPORAL_GEOMETRY_AUTHORIZED"], "0")
        self.assertEqual(d["FINAL_SCALAR_AUTHORIZED"], "0")


if __name__ == "__main__":
    unittest.main()
