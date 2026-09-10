"""Run with python -m unittest discover -s evals -p 'test_*.py'.

These tests check counting/error invariants; they do not certify paper depth.
"""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "audit_manuscript.py"
spec = importlib.util.spec_from_file_location("audit_manuscript", MODULE)
audit_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_module)


class LengthAuditTests(unittest.TestCase):
    def run_audit(self, **kwargs):
        # 1 abstract + 15 body + 17 appendix pages, with different text per scope.
        pages = ["摘要 关键词"] + ["正文推导"] * 15 + ["附录代码"] * 17
        with patch.object(audit_module, "read_text", return_value=("\n".join(pages), {"pages": 33})), \
             patch.object(audit_module, "read_pdf_pages", return_value=(pages, "fixture")):
            return audit_module.audit(Path("paper.pdf"), [], **kwargs)

    def test_short_body_is_not_hidden_by_long_appendix(self):
        report = self.run_audit(full_draft=True, body_start_page=2, body_end_page=16, target_body_pages=(24, 28))
        diag = report["length_diagnostics"]
        self.assertEqual(diag["body_pages"], 15)
        self.assertEqual(diag["body_han_characters"], 60)
        self.assertEqual(diag["status"], "below_target")
        self.assertFalse(any(f["severity"] == "hard_violation" for f in report["findings"]))

    def test_within_range_still_requires_depth_review(self):
        report = self.run_audit(full_draft=True, body_start_page=2, body_end_page=16, target_body_pages=(15, 15))
        self.assertEqual(report["length_diagnostics"]["status"], "within_target")
        self.assertTrue(any(f["category"] == "draft_depth" and f["severity"] == "manual" for f in report["findings"]))

    def test_no_page_range_does_not_invent_body_count(self):
        diag = self.run_audit(full_draft=True, target_body_pages=(24, 28))["length_diagnostics"]
        self.assertIsNone(diag["body_pages"])
        self.assertEqual(diag["status"], "unmeasured")

    def test_format_only_has_no_expansion_diagnostics(self):
        report = self.run_audit()
        self.assertEqual(report["length_diagnostics"], {})
        self.assertFalse(any(f["category"] == "draft_depth" for f in report["findings"]))

    def test_above_target_is_not_an_official_violation(self):
        report = self.run_audit(body_start_page=2, body_end_page=16, target_body_pages=(10, 12))
        self.assertEqual(report["length_diagnostics"]["status"], "above_target")
        self.assertFalse(any(f["severity"] == "hard_violation" for f in report["findings"]))

    def test_invalid_boundaries_are_rejected(self):
        for kwargs in [dict(body_start_page=2), dict(body_start_page=0, body_end_page=3),
                       dict(body_start_page=5, body_end_page=4), dict(body_start_page=2, body_end_page=34),
                       dict(target_body_pages=(28, 24)), dict(target_body_pages=(0, 10))]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.run_audit(**kwargs)

    def test_physical_page_ranges_require_pdf(self):
        with self.assertRaises(ValueError):
            audit_module.audit(Path("paper.tex"), [], body_start_page=2, body_end_page=10)


if __name__ == "__main__":
    unittest.main()
