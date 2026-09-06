"""独立小数据验证；临时文件只放在仓库 tests/.tmp 中。"""
import copy
import importlib.util
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMP_ROOT = REPO_ROOT / "tests/.tmp"
SCRIPT = REPO_ROOT / "modeling-team/scripts/result_receipt.py"
spec = importlib.util.spec_from_file_location("result_receipt", SCRIPT)
rr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rr)


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.check_temp_root()
        TEMP_ROOT.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="receipt-test-", dir=str(TEMP_ROOT))
        self.root = Path(self.temp.name).resolve()
        self.addCleanup(self.cleanup)
        self.write("data.csv", "id,demand\n1,10\n2,20\n")
        self.write("model.py", "def cost(x): return sum(x)\n")
        self.write("layout.csv", "id,allocation\n1,10\n2,20\n")
        self.json("result.json", {"result": {"cost": 30, "unit": "CNY"},
                                  "evaluation": {"loss": "sum_cost", "constraints": "meet_all_demand", "tolerance": 0.001},
                                  "run": {"seed": 1, "algorithm": "enumeration"}})
        self.base = {
            "inputs": {"demand": "data.csv"}, "evaluators": {"cost": "model.py"},
            "candidate": {"allocation": "layout.csv"},
            "run": {"record": "result.json"},
            "evaluation": {"contract": {"path": "result.json", "pointer": "/evaluation"}},
            "metrics": {"cost": {"path": "result.json", "pointer": "/result/cost",
                                  "unit": {"path": "result.json", "pointer": "/result/unit"}, "direction": "min"}}}

    def check_temp_root(self):
        for path in [TEMP_ROOT] + list(TEMP_ROOT.parents):
            try:
                info = path.lstat()
            except FileNotFoundError:
                continue
            if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                raise RuntimeError("测试临时路径包含 symlink/junction")

    def cleanup(self):
        self.check_temp_root()
        if self.root.parent != TEMP_ROOT or not self.root.name.startswith("receipt-test-"):
            raise RuntimeError("测试清理路径越界")
        # 测试创建的逃逸符号链接正常在用例中移除；失败时不递归跟随链接。
        for parent, dirs, files in os.walk(str(self.root), followlinks=False):
            for name in dirs + files:
                path = Path(parent) / name
                info = path.lstat()
                if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                    raise RuntimeError("测试目录仍有链接，保留现场")
        self.temp.cleanup()

    def write(self, name, text):
        (self.root / name).write_text(text, encoding="utf-8")

    def json(self, name, obj):
        self.write(name, json.dumps(obj))

    def candidate_b(self, unit="CNY", tolerance=0.001):
        self.write("layout_b.csv", "id,allocation\n1,11\n2,21\n")
        self.json("result_b.json", {"result": {"cost": 32, "unit": unit},
                                    "evaluation": {"loss": "sum_cost", "constraints": "meet_all_demand", "tolerance": tolerance},
                                    "run": {"seed": 200, "algorithm": "greedy"}})
        b = copy.deepcopy(self.base)
        b["candidate"]["allocation"] = "layout_b.csv"
        b["run"]["record"] = "result_b.json"
        b["evaluation"]["contract"]["path"] = "result_b.json"
        b["metrics"]["cost"]["path"] = "result_b.json"
        b["metrics"]["cost"]["unit"]["path"] = "result_b.json"
        return b

    def test_same_scope_different_candidates_and_seed_can_compare(self):
        a, b = rr.seal(self.root, self.base), rr.seal(self.root, self.candidate_b())
        result = rr.compare(self.root, a, self.root, b)
        self.assertTrue(result["comparable_under_declared_scope"])
        self.assertEqual(result["metrics"]["cost"]["better_numeric_value"], "a")

    def test_source_changes_detected_for_every_role(self):
        for filename in ("data.csv", "model.py", "layout.csv", "result.json"):
            with self.subTest(filename=filename):
                original = (self.root / filename).read_text(encoding="utf-8")
                receipt = rr.seal(self.root, self.base)
                self.write(filename, original + "\n")
                with self.assertRaisesRegex(ValueError, "Changed"):
                    rr.check(self.root, receipt)
                self.write(filename, original)

    def test_missing_candidate(self):
        receipt = rr.seal(self.root, self.base)
        (self.root / "layout.csv").unlink()
        with self.assertRaisesRegex(ValueError, "Missing file"):
            rr.check(self.root, receipt)

    def test_units_refuse_ranking(self):
        with self.assertRaisesRegex(ValueError, "cost:unit"):
            rr.compare(self.root, rr.seal(self.root, self.base), self.root,
                       rr.seal(self.root, self.candidate_b(unit="USD")))

    def test_evaluation_accuracy_difference_refuses_ranking(self):
        with self.assertRaisesRegex(ValueError, "evaluation"):
            rr.compare(self.root, rr.seal(self.root, self.base), self.root,
                       rr.seal(self.root, self.candidate_b(tolerance=1)))

    def test_model_and_input_difference_refuses_ranking(self):
        a = rr.seal(self.root, self.base)
        for role in ("inputs", "evaluators"):
            b = self.candidate_b()
            self.write("other.txt", "different scientific content")
            name = next(iter(b[role]))
            b[role][name] = "other.txt"
            with self.assertRaisesRegex(ValueError, role):
                rr.compare(self.root, a, self.root, rr.seal(self.root, b))

    def test_metric_tampering_detected(self):
        a = rr.seal(self.root, self.base)
        a["metrics"]["cost"]["value"] = 1
        with self.assertRaisesRegex(ValueError, "metrics"):
            rr.check(self.root, a)

    def test_comment_change_is_unknown_equivalence_not_proven_scope_change(self):
        a = rr.seal(self.root, self.base)
        b = self.candidate_b()
        self.write("model_comment.py", (self.root / "model.py").read_text() + "# comment only\n")
        b["evaluators"]["cost"] = "model_comment.py"
        with self.assertRaisesRegex(ValueError, "semantic equivalence unknown") as error:
            rr.compare(self.root, a, self.root, rr.seal(self.root, b))
        self.assertNotIn("scope differs", str(error.exception))

    def test_metric_nonfinite_empty_and_wrong_type(self):
        for value in (float("nan"), float("inf"), None, "", True, [], {}):
            with self.subTest(value=value):
                self.json("bad.json", {"value": value})
                spec = copy.deepcopy(self.base)
                spec["metrics"]["cost"].update(path="bad.json", pointer="/value")
                with self.assertRaises(ValueError):
                    rr.seal(self.root, spec)
        spec = copy.deepcopy(self.base)
        spec["metrics"] = {}
        with self.assertRaisesRegex(ValueError, "metrics"):
            rr.seal(self.root, spec)

    def test_no_assumptions_not_silently_accepted(self):
        spec = copy.deepcopy(self.base)
        spec["evaluation"] = {}
        with self.assertRaisesRegex(ValueError, "evaluation"):
            rr.seal(self.root, spec)

    def test_absolute_and_traversal_paths(self):
        for name in ("../escape", "..\\escape", "C:\\Windows\\test", "/tmp/file", "\\server\\test"):
            with self.subTest(path=name):
                spec = copy.deepcopy(self.base)
                spec["inputs"]["demand"] = name
                with self.assertRaisesRegex(ValueError, "forbidden|escapes"):
                    rr.seal(self.root, spec)

    def test_symlink_escape_if_supported(self):
        link = self.root / "escape"
        try:
            link.symlink_to(self.root.parent, target_is_directory=True)
        except OSError:
            self.skipTest("OS does not permit test symlink creation")
        with self.assertRaisesRegex(ValueError, "escapes"):
            rr.local(self.root, "escape/outside.json")
        link.unlink()

    def test_pointer_escapes_array_and_root(self):
        document = {"a/b": {"~key": [8]}}
        self.assertEqual(rr.at_pointer(document, "/a~1b/~0key/0"), 8)
        self.assertEqual(rr.at_pointer(document, ""), document)
        with self.assertRaises(ValueError):
            rr.at_pointer(document, "/a~2b")

    def test_cli_seal_check_compare_no_overwrite(self):
        self.json("spec.json", self.base)
        self.json("spec_b.json", self.candidate_b())
        calls = [(["seal", "spec.json", "--out", "receipt.json"], 0),
                 (["seal", "spec_b.json", "--out", "receipt_b.json"], 0),
                 (["check", "receipt.json"], 0),
                 (["compare", "receipt.json", "--other", "receipt_b.json"], 0),
                 (["seal", "spec.json", "--out", "receipt.json"], 2),
                 (["seal", "spec.json", "--out", "../escape.json"], 2)]
        for args, expected in calls:
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(rr.main(args + ["--root", str(self.root)]), expected)

    def test_cli_unicode_units_with_cp936_pipes(self):
        env = dict(os.environ, PYTHONIOENCODING="cp936")
        for index, unit in enumerate(("kW/m\u00b2", "\u03bcg\u00b7m\u207b\u00b3")):
            with self.subTest(unit=unit):
                b = self.candidate_b(unit=unit)
                document = json.loads((self.root / "result.json").read_text(encoding="utf-8"))
                document["result"]["unit"] = unit
                self.json("result.json", document)
                self.json("spec.json", self.base)
                self.json("spec_b.json", b)
                a_receipt, b_receipt = "unicode_a%d.json" % index, "unicode_b%d.json" % index
                calls = [("seal", "spec.json", "--out", a_receipt),
                         ("seal", "spec_b.json", "--out", b_receipt),
                         ("compare", a_receipt, "--other", b_receipt)]
                for args in calls:
                    completed = subprocess.run([sys.executable, "-B", str(SCRIPT)] + list(args)
                                               + ["--root", str(self.root)], env=env,
                                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8"))
                    output = json.loads(completed.stdout.decode("utf-8"))
                self.assertEqual(output["metrics"]["cost"]["unit"], unit)
        missing = "missing_\u03bcg\u00b7m\u207b\u00b3.json"
        completed = subprocess.run([sys.executable, "-B", str(SCRIPT), "check", missing,
                                   "--root", str(self.root)], env=env,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(completed.returncode, 2)
        self.assertIn(missing, completed.stderr.decode("utf-8"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
