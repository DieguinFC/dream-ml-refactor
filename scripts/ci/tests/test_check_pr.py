"""Unit tests for scripts/ci/check_pr.py. Run: python -m unittest discover -s scripts/ci/tests"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import check_pr  # noqa: E402

GOOD_BODY = """## What and why
Something.

Refs #12

## Manual verification
- [x] Checked it

## AI usage
- Assisted tasks: none
- [x] I reviewed and understand the whole diff
"""


class MetadataTests(unittest.TestCase):
    def check(self, title="docs(process): add rules", body=GOOD_BODY, head="docs/12-add-rules"):
        return check_pr.check_metadata(title, body, head)

    def test_valid_pr_passes(self):
        self.assertEqual(self.check(), [])

    def test_bad_title_fails(self):
        self.assertTrue(any("Title" in e for e in self.check(title="Fixed stuff")))

    def test_title_too_long_fails(self):
        self.assertTrue(self.check(title="docs: " + "x" * 73))

    def test_breaking_change_title_passes(self):
        self.assertEqual(self.check(title="refactor(api)!: rename endpoint"), [])

    def test_bad_branch_fails(self):
        self.assertTrue(any("Branch" in e for e in self.check(head="my-branch")))

    def test_branch_without_issue_number_fails(self):
        self.assertTrue(self.check(head="docs/add-rules"))

    def test_dependabot_branch_is_exempt(self):
        self.assertEqual(self.check(head="dependabot/pip/django-4.2.8"), [])

    def test_missing_issue_reference_fails(self):
        body = GOOD_BODY.replace("Refs #12", "")
        self.assertTrue(any("issue" in e for e in self.check(body=body)))

    def test_closes_reference_passes(self):
        self.assertEqual(self.check(body=GOOD_BODY.replace("Refs #12", "Closes #12")), [])

    def test_unchecked_manual_box_fails(self):
        body = GOOD_BODY.replace("- [x] Checked it", "- [x] Checked it\n- [ ] Not yet")
        self.assertTrue(any("unchecked" in e for e in self.check(body=body)))

    def test_unchecked_box_outside_section_is_ignored(self):
        body = GOOD_BODY.replace("## What and why", "## What and why\n- [ ] Refactor")
        self.assertEqual(self.check(body=body), [])

    def test_manual_none_without_boxes_passes(self):
        body = GOOD_BODY.replace("- [x] Checked it", "None: documentation only.")
        self.assertEqual(self.check(body=body), [])

    def test_box_inside_html_comment_is_ignored(self):
        body = GOOD_BODY.replace("- [x] Checked it", "- [x] Checked it\n<!-- - [ ] example -->")
        self.assertEqual(self.check(body=body), [])

    def test_missing_manual_section_fails(self):
        body = GOOD_BODY.replace("## Manual verification", "## Notes")
        self.assertTrue(any("missing" in e for e in self.check(body=body)))

    def test_unreviewed_ai_box_fails(self):
        body = GOOD_BODY.replace("- [x] I reviewed", "- [ ] I reviewed")
        self.assertTrue(any("AI usage" in e for e in self.check(body=body)))

    def test_release_pr_from_develop_needs_no_issue(self):
        body = "## Manual verification\nNone: release.\n"
        self.assertEqual(self.check(title="chore(release): v0.1.0", body=body, head="develop"), [])


class FileTests(unittest.TestCase):
    def test_new_baseline_file_is_allowed(self):
        self.assertEqual(check_pr.check_files([("A", "Docs/baseline/new.json")]).errors, [])

    def test_modified_baseline_file_fails(self):
        self.assertTrue(check_pr.check_files([("M", "Docs/baseline/manifest.json")]).errors)

    def test_deleted_baseline_file_fails(self):
        self.assertTrue(check_pr.check_files([("D", "Docs/baseline/README.md")]).errors)

    def test_manifest_note_added_is_allowed(self):
        versions = ('{"a": 1, "b": {"c": [1]}}', '{"a": 1, "b": {"c": [1, 2], "note": "x"}}')
        result = check_pr.check_files([("M", check_pr.BASELINE_MANIFEST)], versions)
        self.assertEqual(result.errors, [])

    def test_manifest_value_changed_fails(self):
        versions = ('{"a": 1}', '{"a": 2}')
        self.assertTrue(check_pr.check_files([("M", check_pr.BASELINE_MANIFEST)], versions).errors)

    def test_manifest_key_removed_fails(self):
        versions = ('{"a": 1, "b": 2}', '{"a": 1}')
        self.assertTrue(check_pr.check_files([("M", check_pr.BASELINE_MANIFEST)], versions).errors)

    def test_manifest_list_item_replaced_fails(self):
        versions = ('{"a": [1, 2]}', '{"a": [1, 3]}')
        self.assertTrue(check_pr.check_files([("M", check_pr.BASELINE_MANIFEST)], versions).errors)

    def test_modified_test_file_is_flagged(self):
        result = check_pr.check_files([("M", "DREAM-ML-backend/GEML/tests/api_tests/test_views.py")])
        self.assertIn(check_pr.FLAG_TEST, result.labels)

    def test_new_test_file_is_not_flagged(self):
        result = check_pr.check_files([("A", "DREAM-ML-backend/GEML/tests/api_tests/test_new.py")])
        self.assertNotIn(check_pr.FLAG_TEST, result.labels)

    def test_workflow_change_is_flagged(self):
        result = check_pr.check_files([("M", ".github/workflows/ci.yml")])
        self.assertIn(check_pr.FLAG_CONFIG, result.labels)

    def test_coveragerc_change_is_flagged(self):
        result = check_pr.check_files([("M", "DREAM-ML-backend/GEML/.coveragerc")])
        self.assertIn(check_pr.FLAG_CONFIG, result.labels)

    def test_app_code_is_not_flagged(self):
        result = check_pr.check_files([("M", "DREAM-ML-backend/GEML/api/views.py")])
        self.assertEqual(result.labels, set())


class AddedLineTests(unittest.TestCase):
    @staticmethod
    def patch(*lines, path="DREAM-ML-backend/GEML/tests/test_x.py"):
        return "\n".join([f"--- a/{path}", f"+++ b/{path}", "@@ -1 +1 @@", *lines])

    def test_skip_without_issue_fails(self):
        result = check_pr.check_added_lines(self.patch('+    pytest.skip("flaky")'))
        self.assertTrue(result.errors)
        self.assertIn(check_pr.FLAG_TEST, result.labels)

    def test_skip_with_issue_passes_but_flags(self):
        result = check_pr.check_added_lines(self.patch('+    pytest.skip("flaky, see #31")'))
        self.assertEqual(result.errors, [])
        self.assertIn(check_pr.FLAG_TEST, result.labels)

    def test_xfail_decorator_is_detected(self):
        self.assertTrue(check_pr.check_added_lines(self.patch("+@pytest.mark.xfail")).errors)

    def test_no_cover_pragma_is_detected(self):
        patch = self.patch("+    return x  # pragma: no cover", path="DREAM-ML-backend/GEML/api/views.py")
        self.assertTrue(check_pr.check_added_lines(patch).errors)

    def test_vitest_skip_is_detected(self):
        patch = self.patch("+it.skip('renders', () => {})", path="DREAM-ML-frontend/frontend/tests/a.test.jsx")
        self.assertTrue(check_pr.check_added_lines(patch).errors)

    def test_removed_skip_is_ignored(self):
        self.assertEqual(check_pr.check_added_lines(self.patch('-    pytest.skip("old")')).errors, [])

    def test_markdown_mentioning_skip_is_ignored(self):
        patch = self.patch("+Never use `pytest.skip(` without an issue.", path="CONTRIBUTING.md")
        self.assertEqual(check_pr.check_added_lines(patch).errors, [])

    def test_checker_tests_are_ignored(self):
        patch = self.patch('+    "pytest.skip(\\"x\\")"', path="scripts/ci/tests/test_check_pr.py")
        self.assertEqual(check_pr.check_added_lines(patch).errors, [])

    def test_deleted_file_header_is_ignored(self):
        patch = "--- a/x.py\n+++ /dev/null\n@@ -1 +0,0 @@\n+pytest.skip('x')"
        self.assertEqual(check_pr.check_added_lines(patch).errors, [])


class LabelTests(unittest.TestCase):
    def test_json_list(self):
        self.assertEqual(check_pr.parse_labels('["a", "exception:coverage"]'), {"a", "exception:coverage"})

    def test_empty_json_list(self):
        self.assertEqual(check_pr.parse_labels("[]"), set())

    def test_lines(self):
        self.assertEqual(check_pr.parse_labels("a\nb\n"), {"a", "b"})


class SonarConfigTests(unittest.TestCase):
    def test_exclusion_change_fails(self):
        self.assertTrue(check_pr.check_sonar_config("+sonar.exclusions=**/foo/**", set()))

    def test_exclusion_change_with_exception_passes(self):
        self.assertEqual(check_pr.check_sonar_config("+sonar.exclusions=**/foo/**", {check_pr.EXCEPTION_SONAR}), [])

    def test_sources_change_fails(self):
        self.assertTrue(check_pr.check_sonar_config("-sonar.sources=a\n+sonar.sources=a,b", set()))

    def test_issue_rule_change_fails(self):
        self.assertTrue(check_pr.check_sonar_config("+sonar.issue.ignore.multicriteria=e1", set()))

    def test_report_path_change_is_allowed(self):
        patch = "+sonar.javascript.lcov.reportPaths=DREAM-ML-frontend/frontend/coverage/lcov.info"
        self.assertEqual(check_pr.check_sonar_config(patch, set()), [])


if __name__ == "__main__":
    unittest.main()
