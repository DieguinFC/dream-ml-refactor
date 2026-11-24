"""Unit tests for the push refspec rules in .claude/hooks/guard_commands.py (issue #38)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import guard_commands  # noqa: E402

ALLOWED = [
    "git push",
    "git push -u origin fix/38-x",
    "git push origin HEAD:refs/heads/fix/38-x",
    "git push origin +HEAD:fix/38-x",
    "git push origin $branch",
    "git push git@github.com:o/r.git fix/38-x",
    "git push https://github.com/o/r.git fix/38-x",
    'git push origin "fix/${issue}-x:fix/38-x"',
]

# Each rule: the start of its reason, and the commands it must block.
BLOCKED = {
    "Destructive: a refspec without a source": [
        "git push origin :main",
        "git push origin :refs/heads/develop",
        "git push origin :fix/38-x",
        "git push origin +:main",
        "git push origin :",
        "git push origin fix/38-x :main",
        "git push --dry-run origin ':main'",
        "bash -c 'git push origin :main'",
        "git status && git push origin :main",
    ],
    "Destructive: an empty variable": [
        'git push origin "${m}:refs/heads/main"',
        "git push origin $m:main",
        "git push origin +${m}:fix/38-x",
        'git push origin "$a$b:main"',
        'git push origin "$env:SHA:main"',
        'git push origin "$(git rev-parse x):main"',
    ],
    "Protected history": [
        "git push origin +HEAD:main",
        "git push origin +HEAD:refs/heads/develop",
        "git push origin +develop",
        "git push origin +refs/heads/main",
    ],
}


class PushRefspecTests(unittest.TestCase):
    def test_allowed(self):
        for command in ALLOWED:
            with self.subTest(allowed=command):
                self.assertIsNone(guard_commands.check_command(command))

    def test_blocked_with_the_expected_reason(self):
        for reason, commands in BLOCKED.items():
            for command in commands:
                with self.subTest(blocked=command):
                    self.assertTrue((guard_commands.check_command(command) or "").startswith(reason))


if __name__ == "__main__":
    unittest.main()
