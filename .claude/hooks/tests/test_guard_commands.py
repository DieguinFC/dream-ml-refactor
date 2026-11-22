"""Unit tests for .claude/hooks/guard_commands.py and settings.json. Run: python -m unittest discover -s .claude/hooks/tests"""

import io
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import guard_commands  # noqa: E402

# Each rule: commands that must pass, commands that must be blocked.
GUARD_CASES = {
    "skip checks": (
        ["git commit -m 'fix: x'", "git push -u origin ci/22-claude-hooks"],
        ["git commit --no-verify -m x", "git push --no-verify", "git commit --no-gpg-sign -m x",
         "git -c core.hooksPath=/dev/null commit -m x", "SKIP=gitleaks git commit -m x"],
    ),
    "destructive": (
        ["git reset HEAD file.py", "git reset --soft HEAD~1", "git clean -n", "git push origin ci/22-x"],
        ["git reset --hard origin/develop", "git reset --hard", "git clean -fd", "git clean --force",
         "git push origin --delete ci/22-x", "git push --mirror"],
    ),
    "explicit staging": (
        ["git add CONTRIBUTING.md scripts/hooks/check_push.py", "git add ./CLAUDE.md", "git commit -m 'docs: a'",
         "git commit --amend --no-edit"],
        ["git add -A", "git add .", "git add --all", "git -C repo add -A", "git commit -am 'fix: x'",
         "git commit -a -m x"],
    ),
    "human decisions": (
        ["gh pr view 21", "gh pr checks", "gh pr create --base develop --title t --body-file b.md",
         "gh pr review 21 --comment -b ok"],
        ["gh pr merge 21 --squash", "gh pr merge --auto --squash", "gh pr review 21 --approve",
         r'& "C:\Program Files\GitHub CLI\gh.exe" pr merge 21'],
    ),
    "exceptions": (
        ["gh pr view 21 --json labels", "gh issue list --label exception:coverage"],
        ["gh pr edit 21 --add-label exception:coverage", "gh label create exception:other",
         "gh pr create --label exception:sonar-config --title t --body b"],
    ),
    "repository rules": (
        ["gh api repos/DieguinFC/dream-ml-refactor/rulesets", "gh ruleset list", "gh secret list",
         "gh api repos/o/r/pulls/21/comments -f body=x", "gh repo view"],
        ["gh api -X PUT repos/o/r/branches/develop/protection", "gh api repos/o/r/rulesets -f name=x",
         "gh api --method DELETE repos/o/r/rulesets/1", "gh api -X PATCH repos/o/r", "gh secret set SONAR",
         "gh variable set X", "gh repo edit --enable-issues", "gh ruleset create"],
    ),
    "secrets": (
        ["cat .env.example", "Get-Content .env.dev", "$env:Path", "printenv HOME", "set -e"],
        ["cat .env", "Get-Content ./.env", r"type C:\repo\.env", "git add .env", "echo $SONAR_TOKEN",
         "$env:SONAR_TOKEN", "printenv", "env", "Get-ChildItem env:", "gh auth token"],
    ),
    "baseline tag": (
        ["git tag -l baseline-pre-refactor", "git show baseline-pre-refactor --stat",
         "git diff baseline-pre-refactor..HEAD"],
        ["git tag -d baseline-pre-refactor", "git tag -f baseline-pre-refactor HEAD",
         "git push origin :refs/tags/baseline-pre-refactor", "git push --force origin baseline-pre-refactor"],
    ),
    "nesting and chaining": (
        ["git status && git log --oneline -3", "bash -c 'git status'"],
        ["git status && git add -A", "git status; git reset --hard", "bash -c 'git add -A'",
         "powershell -Command \"git clean -fd\"", "echo x | gh pr merge 1", "pwsh -EncodedCommand ZQBjAGgAbwA="],
    ),
}


class GuardCommandsTests(unittest.TestCase):
    def test_rules(self):
        for rule, (allowed, blocked) in GUARD_CASES.items():
            for command in allowed:
                with self.subTest(rule=rule, allowed=command):
                    self.assertIsNone(guard_commands.check_command(command))
            for command in blocked:
                with self.subTest(rule=rule, blocked=command):
                    self.assertIsNotNone(guard_commands.check_command(command))

    def run_main(self, payload):
        stdin = io.StringIO(payload if isinstance(payload, str) else json.dumps(payload))
        with mock.patch("sys.stdin", stdin), mock.patch("sys.stderr", new_callable=io.StringIO) as err:
            return guard_commands.main(), err.getvalue()

    def test_main_blocks_with_exit_2_and_reason(self):
        code, err = self.run_main({"tool_name": "Bash", "tool_input": {"command": "git add -A"}})
        self.assertEqual(code, 2)
        self.assertIn("Stage explicit paths", err)

    def test_main_checks_powershell_and_allows_safe_commands(self):
        self.assertEqual(self.run_main({"tool_name": "PowerShell", "tool_input": {"command": "git reset --hard"}})[0], 2)
        self.assertEqual(self.run_main({"tool_name": "Bash", "tool_input": {"command": "git status"}})[0], 0)

    def test_main_ignores_other_tools(self):
        self.assertEqual(self.run_main({"tool_name": "Read", "tool_input": {"file_path": ".env"}})[0], 0)

    def test_main_fails_closed(self):
        code, err = self.run_main("not json")
        self.assertEqual(code, 2)
        self.assertIn("guard failed", err)


class SettingsTests(unittest.TestCase):
    def test_hooks_point_to_existing_scripts(self):
        settings_path = Path(__file__).resolve().parents[2] / "settings.json"
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        for entries in settings["hooks"].values():
            for entry in entries:
                for hook in entry["hooks"]:
                    script = hook["command"].split("$CLAUDE_PROJECT_DIR/")[1].rstrip('"')
                    self.assertTrue((settings_path.parents[1] / script).is_file(), script)


if __name__ == "__main__":
    unittest.main()
