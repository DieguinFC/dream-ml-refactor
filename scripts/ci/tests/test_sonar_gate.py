"""Unit tests for scripts/ci/sonar_gate.py. Run: python -m unittest discover -s scripts/ci/tests"""

import io
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import sonar_gate  # noqa: E402

LABEL = "exception:coverage"


def condition(metric, status="ERROR", value="0.0"):
    return {"status": status, "metricKey": metric, "comparator": "LT", "errorThreshold": "80", "actualValue": value}


def gate(status, *conditions):
    return {"status": status, "conditions": list(conditions)}


class DecideTests(unittest.TestCase):
    def test_green_gate_passes_with_and_without_the_label(self):
        for exception in (False, True):
            self.assertTrue(sonar_gate.decide(gate("OK", condition("new_coverage", "OK")), exception)[0])

    def test_coverage_failure_without_the_label_fails(self):
        passes, message = sonar_gate.decide(gate("ERROR", condition("new_coverage")), False)
        self.assertFalse(passes)
        self.assertIn("new_coverage = 0.0 (threshold 80)", message)

    def test_coverage_failure_with_the_label_passes_and_shows_the_value(self):
        passes, message = sonar_gate.decide(
            gate("ERROR", condition("new_security_rating", "OK"), condition("new_coverage")), True
        )
        self.assertTrue(passes)
        self.assertIn(LABEL, message)
        self.assertIn("new_coverage = 0.0 (threshold 80)", message)

    def test_any_other_failing_condition_fails_with_the_label(self):
        for conditions in (
            [condition("new_security_rating", value="3")],
            [condition("new_coverage"), condition("new_duplicated_lines_density", value="9.1")],
            [condition("new_coverage"), condition("new_security_hotspots_reviewed", status="UNKNOWN")],
        ):
            with self.subTest(conditions=conditions):
                self.assertFalse(sonar_gate.decide(gate("ERROR", *conditions), True)[0])

    def test_unexpected_status_or_no_failing_condition_fails_with_the_label(self):
        self.assertFalse(sonar_gate.decide(gate("NONE"), True)[0])
        self.assertFalse(sonar_gate.decide(gate("ERROR"), True)[0])


class WaitTests(unittest.TestCase):
    def wait(self, *tasks, clock=lambda: 0):
        responses = iter(tasks)
        sleep = mock.Mock()
        result = sonar_gate.wait_for_analysis("T1", lambda path, **params: {"task": next(responses)}, sleep, clock)
        return result, sleep

    def test_polls_until_success(self):
        result, sleep = self.wait({"status": "PENDING"}, {"status": "IN_PROGRESS"},
                                  {"status": "SUCCESS", "analysisId": "A1"})
        self.assertEqual(result, "A1")
        self.assertEqual(sleep.call_count, 2)

    def test_failed_or_canceled_analysis(self):
        for status in ("FAILED", "CANCELED", "OTHER"):
            with self.subTest(status=status), self.assertRaises(sonar_gate.GateError):
                self.wait({"status": status})

    def test_timeout(self):
        times = iter([0, sonar_gate.TIMEOUT_SECONDS])
        with self.assertRaisesRegex(sonar_gate.GateError, "did not finish"):
            self.wait({"status": "PENDING"}, clock=lambda: next(times))


class RunTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.report = Path(self.tmp.name) / "report-task.txt"
        self.report.write_text("projectKey=p\nserverUrl=https://example.org\nceTaskId=T1\n", encoding="utf-8")

    def run_gate(self, status=None, labels="", token="t", get=None):
        self.calls = []

        def fake_get(path, **params):
            self.calls.append((path, params))
            if path == "ce/task":
                return {"task": {"status": "SUCCESS", "analysisId": "A1"}}
            return {"projectStatus": status}

        return sonar_gate.run({"SONAR_TOKEN": token, "LABELS": labels}, get or fake_get, self.report)

    def test_reads_the_gate_of_this_analysis(self):
        self.assertTrue(self.run_gate(gate("OK"))[0])
        self.assertEqual(self.calls, [("ce/task", {"id": "T1"}),
                                      ("qualitygates/project_status", {"analysisId": "A1"})])

    def test_label_must_match_exactly(self):
        failing = gate("ERROR", condition("new_coverage"))
        self.assertTrue(self.run_gate(failing, f"flag:test-changed\n{LABEL}")[0])
        for labels in ("", "exception:coverage-other", "exception:sonar-config", f"x {LABEL}"):
            with self.subTest(labels=labels):
                self.assertFalse(self.run_gate(failing, labels)[0])

    def test_fails_closed(self):
        def unavailable(path, **params):
            raise urllib.error.URLError("down")

        cases = {
            "api error": {"get": unavailable},
            "no status": {"status": None},
            "no conditions": {"status": {"status": "ERROR"}},
            "no token": {"status": gate("OK"), "token": ""},
        }
        for name, kwargs in cases.items():
            with self.subTest(name):
                self.assertFalse(self.run_gate(labels=LABEL, **kwargs)[0])

    def test_missing_or_incomplete_report_fails(self):
        self.report.write_text("projectKey=p\nceTaskId=\n", encoding="utf-8")
        self.assertFalse(self.run_gate(gate("OK"), LABEL)[0])
        self.report.unlink()
        self.assertFalse(self.run_gate(gate("OK"), LABEL)[0])


class FetchAndMainTests(unittest.TestCase):
    def test_fetch_sends_the_token_only_to_sonarcloud(self):
        with mock.patch.object(sonar_gate.urllib.request, "urlopen") as urlopen:
            urlopen.return_value.__enter__.return_value = io.StringIO('{"task": {}}')
            self.assertEqual(sonar_gate.fetch("ce/task", "t", id="T 1"), {"task": {}})
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://sonarcloud.io/api/ce/task?id=T+1")
        self.assertEqual(request.get_header("Authorization"), "Bearer t")

    def test_main_exit_code_and_annotation(self):
        cases = [
            ((True, "Quality gate passed."), 0, "::notice::"),
            ((True, f"{LABEL} is set; x"), 0, "::warning::"),
            ((False, "Quality gate failed: x"), 1, "::error::"),
        ]
        for result, code, prefix in cases:
            with self.subTest(result=result), mock.patch.object(sonar_gate, "run", return_value=result), \
                    mock.patch.dict(sonar_gate.os.environ, {"GITHUB_STEP_SUMMARY": ""}), \
                    mock.patch("sys.stdout", new_callable=io.StringIO) as out:
                self.assertEqual(sonar_gate.main(), code)
                self.assertTrue(out.getvalue().startswith(prefix))


if __name__ == "__main__":
    unittest.main()
