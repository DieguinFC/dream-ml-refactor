"""Unit tests for the edit and session hooks in .claude/hooks. Run: python -m unittest discover -s .claude/hooks/tests"""

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import guard_tests  # noqa: E402
import ruff_after_edit  # noqa: E402
import session_context  # noqa: E402

class GuardTestsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        tests_dir = self.root / "DREAM-ML-backend" / "GEML" / "tests" / "api_tests"
        tests_dir.mkdir(parents=True)
        (tests_dir / "test_views.py").write_text("x = 1\n", encoding="utf-8")
        (self.root / "app.py").write_text("x = 1\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def decide(self, tool, file_path):
        return guard_tests.decision({"tool_name": tool, "tool_input": {"file_path": str(file_path)}}, self.root)

    def test_existing_test_asks(self):
        for tool in ("Edit", "Write", "MultiEdit"):
            output = self.decide(tool, self.root / "DREAM-ML-backend/GEML/tests/api_tests/test_views.py")
            self.assertEqual(output["hookSpecificOutput"]["permissionDecision"], "ask", tool)

    def test_relative_path_is_resolved(self):
        output = self.decide("Edit", "DREAM-ML-backend/GEML/tests/api_tests/test_views.py")
        self.assertEqual(output["hookSpecificOutput"]["permissionDecision"], "ask")

    def test_new_test_and_code_files_pass(self):
        self.assertIsNone(self.decide("Write", self.root / "DREAM-ML-backend/GEML/tests/api_tests/test_new.py"))
        self.assertIsNone(self.decide("Edit", self.root / "app.py"))
        self.assertIsNone(self.decide("Read", self.root / "DREAM-ML-backend/GEML/tests/api_tests/test_views.py"))

    def test_main_fails_towards_asking(self):
        with mock.patch("sys.stdin", io.StringIO("not json")), \
                mock.patch("sys.stdout", new_callable=io.StringIO) as out:
            self.assertEqual(guard_tests.main(), 0)
        self.assertEqual(json.loads(out.getvalue())["hookSpecificOutput"]["permissionDecision"], "ask")


class RuffAfterEditTests(unittest.TestCase):
    def test_only_backend_python_files(self):
        root = Path(tempfile.gettempdir())
        payload = lambda tool, path: {"tool_name": tool, "tool_input": {"file_path": str(root / path)}}  # noqa: E731
        self.assertEqual(ruff_after_edit.backend_file(payload("Edit", "DREAM-ML-backend/GEML/api/views.py"), root),
                         "DREAM-ML-backend/GEML/api/views.py")
        self.assertIsNone(ruff_after_edit.backend_file(payload("Edit", "scripts/hooks/check_push.py"), root))
        self.assertIsNone(ruff_after_edit.backend_file(payload("Edit", "DREAM-ML-backend/GEML/README.md"), root))
        self.assertIsNone(ruff_after_edit.backend_file(payload("Read", "DREAM-ML-backend/GEML/api/views.py"), root))

    def test_errors_exit_2_with_output(self):
        stdin = io.StringIO(json.dumps({"tool_name": "Edit", "tool_input": {"file_path": "DREAM-ML-backend/x.py"}}))
        with mock.patch("sys.stdin", stdin), \
                mock.patch.object(ruff_after_edit, "run_ruff", return_value=(True, "F821 Undefined name")), \
                mock.patch("sys.stderr", new_callable=io.StringIO) as err:
            self.assertEqual(ruff_after_edit.main(), 2)
        self.assertIn("F821", err.getvalue())

    def test_clean_file_passes(self):
        stdin = io.StringIO(json.dumps({"tool_name": "Edit", "tool_input": {"file_path": "DREAM-ML-backend/x.py"}}))
        with mock.patch("sys.stdin", stdin), mock.patch.object(ruff_after_edit, "run_ruff", return_value=(False, "")):
            self.assertEqual(ruff_after_edit.main(), 0)


class SessionContextTests(unittest.TestCase):
    def test_task_branch_with_changes(self):
        text = session_context.build_context("ci/22-claude-hooks", "origin/ci/22-claude-hooks", 2, False,
                                             [" M CLAUDE.md"])
        self.assertIn("ci/22-claude-hooks (issue #22)", text)
        self.assertIn("2 commit(s) not pushed", text)
        self.assertIn(" M CLAUDE.md", text)

    def test_merged_branch_is_flagged(self):
        text = session_context.build_context("test/17-add-vitest", "origin/test/17-add-vitest", 0, True, [])
        self.assertIn("no longer exists", text)

    def test_protected_branch_and_clean_tree(self):
        text = session_context.build_context("develop", "origin/develop", 0, False, [])
        self.assertIn("protected branch", text)
        self.assertIn("Working tree clean", text)

    def test_long_status_is_truncated(self):
        text = session_context.build_context("develop", None, 0, False, [f"?? f{i}" for i in range(25)])
        self.assertIn("... and 5 more", text)


if __name__ == "__main__":
    unittest.main()
