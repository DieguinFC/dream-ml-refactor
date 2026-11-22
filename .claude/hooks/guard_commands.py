"""PreToolUse hook: block shell commands an AI agent must never run on its own.

Claude Code sends the tool call as JSON on stdin. For Bash and PowerShell calls this
checks tool_input.command and exits with code 2 and a reason when a rule matches,
which stops the command and shows the reason to Claude.

Git hooks already reject commits and pushes to main or develop, so those rules are
not repeated here. This guard covers what would get around the git hooks or what
only the author may decide. Pattern matching can be evaded; it prevents accidents,
and GitHub rulesets remain the real boundary. Any internal error blocks the command.
"""

import json
import re
import shlex
import sys

BOM = chr(0xFEFF)
PUNCTUATION = ";&|()\n"
SHELLS = {"bash", "sh", "zsh", "powershell", "pwsh", "cmd"}
# git options that take a separate value before the subcommand.
GIT_OPTIONS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}
BASELINE_TAG = "baseline-pre-refactor"
GH_ADMIN_PATH_RE = re.compile(
    r"(^|/)(rulesets|branches/[^/]+/protection|secrets|variables|environments|collaborators"
    r"|hooks|keys|actions/permissions)(/|$)|^/?repos/[^/]+/[^/]+/?$|^/?orgs/"
)
ENV_FILE_RE = re.compile(r"(^|[\\/])\.env$")
ENV_DUMP_COMMANDS = {"env", "printenv", "set"}

# Checked on the raw command too, so quoting or nesting does not hide them.
RAW_RULES = [
    (re.compile(r"--no-verify\b|--no-gpg-sign\b"), "Do not skip checks: --no-verify and --no-gpg-sign are not allowed."),
    (re.compile(r"core\.hookspath", re.IGNORECASE), "Do not skip checks: changing core.hooksPath disables the git hooks."),
    (re.compile(r"SONAR_TOKEN"), "Secrets: do not read or print SONAR_TOKEN."),
    (re.compile(r"\bgh(\.exe)?\W+auth\s+token\b"), "Secrets: do not print the GitHub token."),
]


def tokenize(command):
    """Split a command into tokens, keeping ; & | ( ) and newlines as separate tokens."""
    lexer = shlex.shlex(command, posix=False, punctuation_chars=PUNCTUATION)
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        tokens = list(lexer)
    except ValueError:  # unbalanced quotes
        tokens = command.split()
    return [strip_quotes(token) for token in tokens]


def strip_quotes(token):
    if len(token) >= 2 and token[0] == token[-1] and token[0] in "'\"":
        return token[1:-1]
    return token


def segments(tokens):
    """Yield the simple commands between separators."""
    current = []
    for token in tokens:
        if token and all(char in PUNCTUATION for char in token):
            if current:
                yield current
            current = []
        else:
            current.append(token)
    if current:
        yield current


def program_name(token):
    name = re.split(r"[\\/]", token)[-1].lower()
    return name[:-4] if name.endswith(".exe") else name


def short_flags(args):
    """Letters of clustered short options, such as -am -> {'a', 'm'}."""
    letters = set()
    for arg in args:
        if re.fullmatch(r"-[A-Za-z]+", arg):
            letters.update(arg[1:])
    return letters


def check_git(args, env_vars):
    if any(name in ("SKIP", "PRE_COMMIT_ALLOW_NO_CONFIG") for name in env_vars):
        return "Do not skip checks: SKIP disables pre-commit hooks."
    index = 0
    while index < len(args) and args[index].startswith("-"):
        index += 2 if args[index] in GIT_OPTIONS_WITH_VALUE else 1
    if index >= len(args):
        return None
    sub, rest = args[index], args[index + 1:]
    flags = short_flags(rest)

    if sub == "reset" and "--hard" in rest:
        return "Destructive: git reset --hard discards work. Ask the author."
    if sub == "clean" and ("f" in flags or "--force" in rest):
        return "Destructive: git clean deletes untracked files. Ask the author."
    if sub == "add" and ("A" in flags or "--all" in rest or "." in rest or "--no-ignore-removal" in rest):
        return "Stage explicit paths: git add -A, git add . and git add --all are not allowed."
    if sub == "commit" and ("a" in flags or "--all" in rest):
        return "Stage explicit paths: git commit -a is not allowed."
    if any(BASELINE_TAG in arg for arg in rest):
        if sub == "tag" and not ({"l", "v", "n"} & flags or "--list" in rest or "--verify" in rest):
            return f"Frozen: the {BASELINE_TAG} tag must not change."
        if sub in ("push", "update-ref"):
            return f"Frozen: the {BASELINE_TAG} tag must not change."
    if sub == "push" and ("--mirror" in rest or "--delete" in rest or "d" in flags):
        return "Destructive: deleting or mirroring remote refs is not allowed. Ask the author."
    return None


def gh_method(rest):
    for i, arg in enumerate(rest):
        if arg in ("-X", "--method") and i + 1 < len(rest):
            return rest[i + 1].upper()
        if arg.startswith("--method="):
            return arg.split("=", 1)[1].upper()
        if re.fullmatch(r"-X[A-Za-z]+", arg):
            return arg[2:].upper()
    sends_data = any(
        arg in ("-f", "-F", "--field", "--raw-field", "--input") or arg.startswith(("--field=", "--raw-field="))
        for arg in rest
    )
    return "POST" if sends_data else "GET"


def check_gh(args):
    if not args:
        return None
    group, rest = args[0], args[1:]
    action = rest[0] if rest else ""

    if group == "pr" and action == "merge":
        return "Human decision: the author merges PRs."
    if group == "pr" and action == "review" and ("--approve" in rest or "a" in short_flags(rest[1:])):
        return "Human decision: AI tools never approve PRs."
    if group in ("pr", "issue", "label", "api") and action not in ("list", "view", "status", "checks", "diff") \
            and any("exception:" in arg for arg in rest):
        return "Only the author grants exceptions: do not add or create exception:* labels."
    if group in ("secret", "variable") and action not in ("list", ""):
        return "Protects the rules: secrets and variables are changed by the author."
    if group == "repo" and action in ("edit", "delete", "rename", "archive", "unarchive", "set-default"):
        return "Protects the rules: repository settings are changed by the author."
    if group == "ruleset" and action not in ("list", "view", "check", ""):
        return "Protects the rules: rulesets are changed by the author."
    if group == "api":
        path = next((arg for arg in rest if not arg.startswith("-") and "/" in arg), "")
        if gh_method(rest) != "GET" and GH_ADMIN_PATH_RE.search(path.split("?")[0]):
            return "Protects the rules: do not change rulesets, branch protection, secrets or repo settings."
    return None


def check_segment(segment):
    env_vars = []
    index = 0
    while index < len(segment) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", segment[index]):
        env_vars.append(segment[index].split("=", 1)[0])
        index += 1
    if index >= len(segment):
        return None
    program, args = program_name(segment[index]), segment[index + 1:]

    if any(ENV_FILE_RE.search(arg) for arg in args) or ENV_FILE_RE.search(segment[index]):
        return "Secrets: do not read, print, copy or stage .env."
    if (program in ENV_DUMP_COMMANDS and not args) or \
            (program in ("get-childitem", "gci", "ls", "dir") and any(arg.lower().startswith("env:") for arg in args)):
        return "Secrets: do not print all environment variables."
    if program in SHELLS:
        for i, arg in enumerate(args):
            if arg.lower() in ("-c", "-command", "/c", "-encodedcommand") and i + 1 < len(args):
                if arg.lower() == "-encodedcommand":
                    return "Encoded commands cannot be checked; run the command directly."
                return check_command(" ".join(args[i + 1:]))
        return None
    if program == "git":
        return check_git(args, env_vars)
    if program == "gh":
        return check_gh(args)
    return None


def check_command(command):
    """Return the reason to block the command, or None."""
    for pattern, reason in RAW_RULES:
        if pattern.search(command):
            return reason
    for segment in segments(tokenize(command)):
        reason = check_segment(segment)
        if reason:
            return reason
    return None


def read_payload():
    """Read the hook input; tolerate a byte order mark, which PowerShell pipes add."""
    return json.loads(sys.stdin.read().lstrip(BOM))


def main():
    try:
        payload = read_payload()
        if payload.get("tool_name") not in ("Bash", "PowerShell"):
            return 0
        reason = check_command(payload.get("tool_input", {}).get("command", ""))
    except Exception as error:  # fail closed
        reason = f"The command guard failed ({error!r}), so the command was blocked."
    if reason:
        print(f"Blocked by .claude/hooks/guard_commands.py: {reason}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
