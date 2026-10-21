import unittest
from pathlib import Path
from hiring_funnel import build_report, load_events, render_html

ROOT = Path(__file__).parent

class HiringFunnelTests(unittest.TestCase):
    def test_events_load_and_validate(self):
        rows = load_events(ROOT / "sample_events.jsonl")
        self.assertEqual(len(rows), 8)
        self.assertEqual(rows[0]["candidate_id"], "C-101")

    def test_report_flags_pipeline_quality(self):
        report = build_report(load_events(ROOT / "sample_events.jsonl"), screen_sla_hours=48)
        self.assertEqual(report["total_candidates"], 4)
        self.assertEqual(report["invalid_stage_order"], 1)
        self.assertEqual(report["duplicate_stage_events"], 1)
        self.assertEqual(report["screen_sla_breaches"], 1)

    def test_html_contains_required_columns(self):
        html = render_html(build_report(load_events(ROOT / "sample_events.jsonl")))
        for text in ("Candidate", "Current stage", "Screen hours", "Duplicate stages"):
            self.assertIn(text, html)

if __name__ == "__main__":
    unittest.main()
