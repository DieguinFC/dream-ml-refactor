"""Unit tests for scripts/hooks. Run: python -m unittest discover -s scripts/hooks/tests"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import add_issue_ref  # noqa: E402
import check_push  # noqa: E402

TEMPLATE = "\n# Please enter the commit message for your changes.\n# On branch test/17-x\n"


class IssueFromBranchTests(unittest.TestCase):
    def test_task_branch(self):
        self.assertEqual(add_issue_ref.issue_from_branch("test/17-add-vitest"), "17")

    def test_branches_without_issue(self):
        for branch in ("develop", "main", "", "dependabot/npm/vite-5", "feature/abc"):
            self.assertIsNone(add_issue_ref.issue_from_branch(branch), branch)


class AddRefTests(unittest.TestCase):
    def test_message_from_command_line(self):
        self.assertEqual(
            add_issue_ref.add_ref("test: add tests\n", "17"),
            "test: add tests\n\nRefs #17\n",
        )

    def test_existing_reference_is_kept(self):
        for message in ("test: x\n\nRefs #17\n", "test: x\n\nCloses #17\n"):
            self.assertEqual(add_issue_ref.add_ref(message, "17"), message)

    def test_other_issue_number_is_not_a_match(self):
        self.assertEqual(
            add_issue_ref.add_ref("test: x\n\nRefs #170\n", "17"),
            "test: x\n\nRefs #170\n\nRefs #17\n",
        )

    def test_editor_template_keeps_subject_line_free(self):
        result = add_issue_ref.add_ref(TEMPLATE, "17")
        self.assertTrue(result.startswith("\n\nRefs #17\n\n# Please enter"))

    def test_reference_goes_before_comments(self):
        result = add_issue_ref.add_ref("fix: y\n" + TEMPLATE, "17")
        self.assertEqual(result, "fix: y\n\nRefs #17\n\n" + TEMPLATE.lstrip("\n"))


class AddRefMainTests(unittest.TestCase):
    def run_hook(self, message, source="message", branch="test/17-add-vitest"):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "COMMIT_EDITMSG")
            with open(path, "w", encoding="utf-8", newline="") as handle:
                handle.write(message)
            env = {"PRE_COMMIT_COMMIT_MSG_SOURCE": source}
            with mock.patch.dict(os.environ, env), \
                    mock.patch.object(add_issue_ref, "current_branch", return_value=branch):
                self.assertEqual(add_issue_ref.main(["hook", path]), 0)
            with open(path, encoding="utf-8", newline="") as handle:
                return handle.read()

    def test_adds_reference(self):
        self.assertEqual(self.run_hook("test: x\n"), "test: x\n\nRefs #17\n")

    def test_keeps_line_endings(self):
        self.assertNotIn("\r", self.run_hook("test: x\n"))

    def test_amend_merge_and_squash_are_untouched(self):
        for source in ("commit", "merge", "squash"):
            self.assertEqual(self.run_hook("test: x\n", source=source), "test: x\n", source)

    def test_branch_without_issue_is_untouched(self):
        self.assertEqual(self.run_hook("test: x\n", branch="develop"), "test: x\n")


class CheckPushTests(unittest.TestCase):
    def test_task_branch_is_allowed(self):
        self.assertEqual(check_push.check("refs/heads/ci/20-git-hooks"), [])

    def test_dependabot_and_tags_are_allowed(self):
        self.assertEqual(check_push.check("refs/heads/dependabot/npm/vite-5"), [])
        self.assertEqual(check_push.check("refs/tags/v0.1.0"), [])

    def test_protected_branches_are_blocked(self):
        for branch in ("main", "develop"):
            errors = check_push.check(f"refs/heads/{branch}")
            self.assertEqual(len(errors), 1, branch)
            self.assertIn("open a PR", errors[0])

    def test_bad_names_are_blocked(self):
        for branch in ("my-branch", "docs/NUMERO-freeze", "feature/42_Extract", "init-refactor-documents"):
            self.assertEqual(len(check_push.check(f"refs/heads/{branch}")), 1, branch)

    def test_main_reads_remote_ref(self):
        with mock.patch.dict(os.environ, {"PRE_COMMIT_REMOTE_BRANCH": "refs/heads/develop"}), \
                mock.patch("sys.stderr"):
            self.assertEqual(check_push.main(), 1)
        with mock.patch.dict(os.environ, {"PRE_COMMIT_REMOTE_BRANCH": "refs/heads/ci/20-git-hooks"}):
            self.assertEqual(check_push.main(), 0)


if __name__ == "__main__":
    unittest.main()
