#!/usr/bin/env python3
"""Offline validation for the Multi-Agent Model Advisor development workflow.

The validator checks four things without network access or credentials:

1. the project agent configuration and its permission boundaries, including
   the RTK mirror policy, the Go quality-toolchain allows, the credential-path
   denials, the ask rules for infrastructure tools and paths outside the
   worktree, and the human-only merge enforcement. Compound shell samples are
   split into subcommands so the per-agent expectations follow OpenCode's
   scanner-based shell permission model;
2. ADR baseline handling when an open pull request declares an ADR accepted,
   including reference and identifier validation for the ADR links;
3. feedback reconciliation with synthetic reports, including an omitted
   criterion, an unverified criterion and a proposed ADR conflict, asserted
   against the exact expected gap and escalation sets;
4. permission fixtures that reject over-broad agent allow rules.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = ROOT / ".opencode" / "agents"
ADR_DIR = ROOT / "docs" / "adr"
FIXTURES = ROOT / "docs" / "validation" / "fixtures"

REQUIRED_AGENTS = {
    "orchestrator": "primary",
    "planner": "subagent",
    "reviewer": "subagent",
    "implementer": "subagent",
    "tester": "subagent",
    "git-manager": "subagent",
}

# Agents other than the Git Manager may only allow the edit and subagent
# actions; shell, webfetch, websearch and read allows are reserved for the Git
# Manager's write role or belong at the project level.
NON_GIT_MANAGER_ALLOW_ACTIONS = {"edit", "subagent"}

REPORT_FIELDS = [
    "agent",
    "issue",
    "task_id",
    "status",
    "completed_work",
    "acceptance_criteria_coverage",
    "missing_requirements",
    "findings",
    "assumptions",
    "dependencies",
    "adr_alignment",
    "recommended_next_actions",
    "feedback",
]

REPORT_STATUSES = {"Completed", "Partial", "Blocked", "Needs Decision"}
COVERAGE_VALUES = {"covered", "partial", "unverified", "missing", "not_applicable"}

# Read-only Git and GitHub commands that must stay allowed in plain and RTK
# form for every agent.
GIT_READ_COMMANDS = [
    "status",
    "diff",
    "log",
    "show",
    "rev-parse",
    "ls-files",
    "blame",
    "grep",
    "describe",
    "shortlog",
    "merge-base",
]
GH_READ_COMMANDS = [
    "pr view",
    "pr diff",
    "pr checks",
    "pr list",
    "issue view",
    "issue list",
    "run view",
    "run list",
    "workflow view",
    "workflow list",
    "repo view",
    "release view",
    "release list",
]
RTK_REPORT_TOOLS = [
    "read",
    "smart",
    "grep",
    "rg",
    "ast-grep",
    "find",
    "ls",
    "tree",
    "wc",
    "diff",
    "log",
    "json",
    "deps",
    "gain",
    "methods",
]

# Go quality toolchain and the filtered RTK runs of the same tools.
GO_QUALITY_SAMPLES = [
    "go test ./...",
    "govulncheck ./...",
    "golangci-lint run ./...",
    "jactionlint",
]
RTK_FILTERED_QUALITY_SAMPLES = [
    "rtk test govulncheck ./...",
    "rtk test golangci-lint run ./...",
    "rtk test jactionlint",
]

INFRA_ASK_SAMPLES = [
    "docker ps",
    "kubectl get pods",
    "oc get pods",
    "aws s3 ls",
    "psql -l",
    "wget https://example.com",
]
INFRA_ASK_RTK_SAMPLES = [f"rtk {command}" for command in INFRA_ASK_SAMPLES]

# Outside-worktree RTK reads require approval. A generic "rtk * /*" ask rule is
# deliberately absent.
OUTSIDE_WORKTREE_ASK_SAMPLES = [
    "rtk read ~/x",
    "rtk read /Users/x",
    "rtk read ../x",
]

# Credential, secret and env locations. Read, edit and external_directory deny
# the home-relative paths; shell command strings are blocked through the
# leading-wildcard mirrors in the project policy.
SENSITIVE_PATH_SAMPLES = [
    "~/.ssh/id_rsa",
    "~/.aws/credentials",
    "~/.gnupg/secring.gpg",
    "~/.config/gh/hosts.yml",
    "~/.kube/config",
    "~/.docker/config.json",
    "~/.netrc",
    "~/.git-credentials",
    "~/.npmrc",
    "~/.pypirc",
    "~/.local/share/opencode/auth.json",
    "~/.local/share/opencode/opencode.db",
    "~/.local/share/opencode/log/session.log",
    "~/Library/Keychains/login.keychain-db",
]
SENSITIVE_SHELL_SAMPLES = [
    "cat ~/.ssh/id_rsa",
    "rtk read ~/.ssh/id_rsa",
    "cp ~/.aws/credentials x",
    "git add ~/.ssh/id_rsa",
    "cat ~/.config/gh/hosts.yml",
    "cat ~/.kube/config",
    "cat ~/.docker/config.json",
    "cat ~/.netrc",
    "cat ~/.git-credentials",
    "cp ~/.npmrc x",
    "cp ~/.pypirc x",
    "cat ~/.netrc | head",
    "cat ~/.local/share/opencode/auth.json",
    "cat ~/.local/share/opencode/opencode.db",
    "cat ~/.local/share/opencode/log/session.log",
    "cp ~/Library/Keychains/login.keychain-db x",
    "cat .env",
    "cat config/.env.local",
]
# Env templates are not tracked in the repository, but the policy re-enables
# an `*.env.example` template if one is present, so the shell allow must stay
# proven. Dead-code guard: every sample in this list must be asserted.
ENV_ALLOW_SHELL_SAMPLES = ["cat .env.example", "cat config/.env.example"]

TOOLCHAIN_DENY_SAMPLES = ["pnpm install", "rtk pnpm install", "dotnet build", "rtk dotnet build"]
WRAPPER_DENY_SAMPLES = ["rtk test pytest", "rtk err ls", "rtk summary ls"]
WRAPPER_ASK_SAMPLES = ["rtk bypass ls", "rtk proxy ls"]

# Compound commands that hide a write must resolve to deny for every agent,
# including the narrow Go quality-tool rkt test filters.
NESTED_WRITE_DENY_SAMPLES = [
    'rtk test "govulncheck ./...; git push origin main"',
    'rtk test "golangci-lint run ./... ; git commit -m x"',
    'rtk test "jactionlint && git push origin main"',
    "echo ok && git push origin main",
    "echo ok && gh api repos/x/y",
    "sh -c 'git commit -m test'",
]

# gh api and pull-request merges are denied for every agent; merging a pull
# request is reserved for the human user.
GH_API_DENY_SAMPLES = [
    "gh api",
    "gh api repos/x/y",
    "gh api -X PUT repos/o/r/pulls/1/merge",
    "gh api graphql -f query=query{viewer{login}}",
    "rtk gh api repos/x/y",
    "gh pr merge 1 --merge",
    "gh pr merge 1",
    "rtk gh pr merge 1",
    "gh workflow run test.yml",
]

# Compound commands with a protected operation. OpenCode's shell scanner
# produces one command string per subcommand, so the protected operation is
# denied in direct and compound invocations and these samples resolve to deny
# for every agent under the per-subcommand model.
COMPOUND_PROTECTED_DENY_SAMPLES = [
    "git fetch origin && gh pr merge 1",
    "git commit -m x && gh api -X PUT repos/o/r/pulls/1/merge",
    "git stash && git push origin main",
]

# Compounds every extracted subcommand of which resolves to allow: read-only
# inspection for all agents, and for the Git Manager a legitimate chained write
# that must not break (git add/commit followed by a push to a feature branch).
HARMLESS_COMPOUND_ALLOW_SAMPLES = ["git status --short && git diff"]
COMPOUND_GIT_MANAGER_ALLOW_SAMPLES = [
    "git add . && git push origin HEAD",
    "git commit -m x && git push -u origin issue-30-multi-agent-development-workflow",
]

# The personal OpenCode configuration is reachable from shell arguments too.
# The mirror rule asks, never denies, so the location stays approval-only for
# every agent.
OPENCODE_CONFIG_SHELL_SAMPLE = "cat ~/.config/opencode/opencode.json"

# Direct pushes to main are denied even for the Git Manager.
PUSH_TO_MAIN_DENY_SAMPLES = [
    "git push origin main",
    "git push -u origin main",
    "git push origin HEAD:main",
    "git push origin HEAD:refs/heads/main",
    "rtk git push origin main",
    "rtk git push -u origin main",
    "rtk git push origin HEAD:main",
]

# Write commands the Git Manager owns, in plain and RTK form. Other agents are
# denied; pushes to main are handled by PUSH_TO_MAIN_DENY_SAMPLES above and are
# therefore excluded here.
GIT_MANAGER_WRITE_COMMANDS = [
    "git add .",
    "git commit -m test",
    "git push origin HEAD",
    "git push -u origin issue-30-multi-agent-development-workflow",
    "git merge main",
    "git rebase main",
    "git checkout -b feature",
    "git branch feature",
    "git switch -c feature",
    "gh pr create --title test",
    "gh pr create --title x --body-file .tmp/pr.md",
    "rtk git add .",
    "rtk git branch feature",
    "rtk git checkout -b feature",
    "rtk git commit -m test",
    "rtk git push origin issue-30-multi-agent-development-workflow",
    "rtk git switch -c feature",
    "rtk gh pr create --title test",
]

# Deny rules that must appear in the Git Manager frontmatter after every allow
# rule, so they win under last-match-wins resolution.
GIT_MANAGER_REQUIRED_TRAILING_DENIES = [
    "gh api*",
    "gh pr merge*",
    "rtk gh api*",
    "rtk gh pr merge*",
    "git push * main*",
    "git push *:main*",
    "git push *heads/main*",
    "rtk git push * main*",
    "rtk git push *:main*",
    "rtk git push *heads/main*",
    "*/.ssh/*",
    "*/.aws/*",
    "*/.gnupg/*",
    "*/.config/gh/*",
    "*/.kube/*",
    "*/.docker/config.json*",
    "*/.netrc*",
    "*/.git-credentials*",
    "*/.npmrc*",
    "*/.pypirc*",
    "*/.local/share/opencode/auth.json*",
    "*/.local/share/opencode/opencode.db*",
    "*/.local/share/opencode/log/*",
    "*Library/Keychains/*",
    "*.env*",
]


class CheckError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CheckError(message)


def strip_jsonc(text: str) -> str:
    """Remove // and /* */ comments while preserving string contents."""
    out: list[str] = []
    i = 0
    in_string = False
    escaped = False
    while i < len(text):
        char = text[i]
        if in_string:
            out.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            i += 1
            continue
        if char == '"':
            in_string = True
            out.append(char)
            i += 1
            continue
        if char == "/" and i + 1 < len(text) and text[i + 1] == "/":
            i += 2
            while i < len(text) and text[i] not in "\r\n":
                i += 1
            continue
        if char == "/" and i + 1 < len(text) and text[i + 1] == "*":
            i += 2
            while i + 1 < len(text) and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
            continue
        out.append(char)
        i += 1
    return remove_trailing_commas("".join(out))


def remove_trailing_commas(text: str) -> str:
    out: list[str] = []
    i = 0
    in_string = False
    escaped = False
    while i < len(text):
        char = text[i]
        if in_string:
            out.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            i += 1
            continue
        if char == '"':
            in_string = True
            out.append(char)
            i += 1
            continue
        if char == ",":
            j = i + 1
            while j < len(text) and text[j] in " \t\r\n":
                j += 1
            if j < len(text) and text[j] in "]}":
                i += 1
                continue
        out.append(char)
        i += 1
    return "".join(out)


def load_jsonc(path: Path) -> Any:
    return json.loads(strip_jsonc(path.read_text(encoding="utf-8")))


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [parse_scalar(part) for part in inner.split(",")]
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    if value in {"null", "~"}:
        return None
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    return value


def split_markdown(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        raise CheckError("frontmatter is not closed")
    frontmatter = text[3:end].strip("\n")
    body = text[end + 4 :].lstrip("\n")
    values: dict[str, Any] = {}
    for raw in frontmatter.splitlines():
        if not raw or raw[0].isspace() or raw.lstrip().startswith("#"):
            continue
        if ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        values[key.strip()] = parse_scalar(value)
    return values, body


def read_markdown(path: Path) -> tuple[dict[str, Any], str]:
    return split_markdown(path.read_text(encoding="utf-8"))


def adr_from_text(text: str, path: str, source: str) -> dict[str, Any]:
    frontmatter, body = split_markdown(text)
    adr = dict(frontmatter)
    adr["body_sha256"] = hashlib.sha256(body.encode("utf-8")).hexdigest()
    adr["path"] = path
    adr["source"] = source
    adr.setdefault("id", Path(path).stem.split("-")[0] + "-" + Path(path).stem.split("-")[1])
    adr.setdefault("title", "Untitled")
    adr.setdefault("status", "Proposed")
    adr.setdefault("issues", [])
    adr.setdefault("supersedes", [])
    adr.setdefault("superseded-by", None)
    adr.setdefault("conflicts-with", [])
    return adr


def adrs_from_dir(directory: Path, source: str) -> list[dict[str, Any]]:
    result = []
    for path in sorted(directory.glob("ADR-*.md")):
        result.append(adr_from_text(path.read_text(encoding="utf-8"), str(path), source))
    return result


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False
    )


def adrs_from_ref(ref: str) -> list[dict[str, Any]]:
    listing = git("ls-tree", "-r", "--name-only", ref, "--", "docs/adr")
    if listing.returncode != 0:
        raise CheckError(f"cannot read ADRs from git ref {ref!r}")
    result = []
    for path in listing.stdout.splitlines():
        if not path.endswith(".md"):
            continue
        if not Path(path).name.startswith("ADR-"):
            continue
        shown = git("show", f"{ref}:{path}")
        if shown.returncode != 0:
            raise CheckError(f"cannot read {path} from {ref!r}")
        result.append(adr_from_text(shown.stdout, path, "merged"))
    return result


def effective_status(adr: dict[str, Any]) -> str:
    if adr["source"] == "merged":
        return str(adr["status"])
    if adr["status"] == "In Review":
        return "In Review"
    return "Proposed"


def evaluate_adrs(
    baseline: list[dict[str, Any]], open_pr: list[dict[str, Any]]
) -> tuple[set[str], list[dict[str, Any]], list[dict[str, str]]]:
    merged_by_id = {adr["id"]: adr for adr in baseline}
    accepted_baseline_ids = {
        adr_id for adr_id, adr in merged_by_id.items() if adr["status"] == "Accepted"
    }
    proposals = [
        {
            "id": adr["id"],
            "title": adr["title"],
            "declared_status": adr["status"],
            "effective_status": effective_status(adr),
            "path": adr["path"],
        }
        for adr in open_pr
    ]
    proposal_ids = {proposal["id"] for proposal in proposals}
    # References are validated against every known ADR: merged records of any
    # status plus the open proposals. Only accepted merged records form the
    # baseline used for conflict escalation.
    known_ids = set(merged_by_id) | proposal_ids

    conflicts: list[dict[str, str]] = []
    for adr in open_pr:
        references = list(adr.get("supersedes", [])) + list(
            adr.get("conflicts-with", [])
        )
        superseded_by = adr.get("superseded-by")
        if superseded_by is not None:
            references.append(superseded_by)
        for reference in references:
            require(
                reference in known_ids,
                f"{adr['id']} references unknown ADR {reference}",
            )
        for conflicting in adr.get("conflicts-with", []):
            if conflicting in merged_by_id:
                conflicts.append(
                    {
                        "proposal": str(adr["id"]),
                        "baseline": str(conflicting),
                        "decision": "Open pull-request ADR conflicts with a merged ADR",
                    }
                )

    for adr in open_pr:
        merged = merged_by_id.get(adr["id"])
        if merged is not None and merged["status"] != "Accepted":
            raise CheckError(
                f"proposal {adr['id']} collides with merged ADR {adr['id']} "
                f"(status {merged['status']}); a new decision needs a new identifier"
            )

    for proposal in proposals:
        require(
            proposal["effective_status"] != "Accepted",
            f"{proposal['id']} is treated as accepted while still in an open pull request",
        )
        if proposal["declared_status"] == "Accepted":
            require(
                proposal["effective_status"] == "Proposed",
                f"{proposal['id']} declares Accepted and must be demoted to Proposed",
            )

    for conflict in conflicts:
        require(
            conflict["baseline"] in accepted_baseline_ids,
            f"conflict references a non-accepted ADR: {conflict['baseline']}",
        )
    return accepted_baseline_ids, proposals, conflicts


def parse_permissions(path: Path) -> list[dict[str, Any]]:
    """Parse the top-level permissions list from an agent Markdown file."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return []
    end = text.find("\n---", 3)
    if end == -1:
        raise CheckError(f"{path}: frontmatter is not closed")
    frontmatter = text[3:end]
    rules: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    in_permissions = False
    for raw in frontmatter.splitlines():
        if not raw.strip():
            continue
        if not raw[0].isspace():
            if current is not None:
                rules.append(current)
                current = None
            in_permissions = raw.strip().startswith("permissions:")
            continue
        if not in_permissions:
            continue
        stripped = raw.strip()
        if stripped.startswith("#"):
            continue
        if stripped.startswith("- "):
            if current is not None:
                rules.append(current)
            current = {}
            stripped = stripped[2:].strip()
        if current is not None and ":" in stripped:
            key, value = stripped.split(":", 1)
            current[key.strip()] = parse_scalar(value)
    if current is not None:
        rules.append(current)
    return rules


def rule_matches(rule: dict[str, Any], action: str, value: str) -> bool:
    rule_action = str(rule.get("action", ""))
    if rule_action not in {"*", action}:
        return False
    resource = str(rule.get("resource", ""))
    return fnmatch.fnmatchcase(value, resource)


def resolve_last_match(
    rules: list[dict[str, Any]], action: str, value: str
) -> str:
    """Resolve one value with ordered rules and last-match-wins semantics."""
    effect = "allow"
    for rule in rules:
        if rule_matches(rule, action, value):
            effect = str(rule.get("effect", "allow"))
    return effect


def split_shell_subcommands(command: str) -> list[str]:
    """Split a shell command on top-level separators, best-effort.

    This approximates OpenCode's shell scanner (see the "Scanner" section of
    https://opencode.ai/docs/permissions): shell permission checks run on
    scanner-produced command strings and compound commands may produce several.
    Separators inside single or double quotes or after a backslash escape do
    not split, so a hidden write inside a quoted wrapper argument such as
    'rtk test "govulncheck ./...; git push origin main"' stays one subcommand.
    Constructs this model cannot analyse resolve as one string and rely on the
    runtime scanner with its fail-closed behaviour for unanalyzable commands.
    """
    parts: list[str] = []
    current: list[str] = []
    quote: str | None = None
    escaped = False
    index = 0
    while index < len(command):
        char = command[index]
        if escaped:
            current.append(char)
            escaped = False
            index += 1
            continue
        if quote:
            current.append(char)
            if quote == '"' and char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
            current.append(char)
            index += 1
            continue
        if char == "\\":
            current.append(char)
            escaped = True
            index += 1
            continue
        if command[index : index + 2] in {"&&", "||"}:
            parts.append("".join(current))
            current = []
            index += 2
            continue
        if char in {";", "|", "\n"}:
            parts.append("".join(current))
            current = []
            index += 1
            continue
        current.append(char)
        index += 1
    parts.append("".join(current))
    cleaned = [part.strip() for part in parts if part.strip()]
    return cleaned


def effective_effect(rules: list[dict[str, Any]], action: str, value: str) -> str:
    """Resolve one sample against the ordered rules.

    Shell samples are compound-aware: a command with top-level separators is
    split into subcommands, each is resolved with last-match-wins semantics and
    the results combine as any deny -> deny, else any ask -> ask, else allow.
    This models OpenCode's per-subcommand scanner evaluation at a best-effort
    level; unanalyzable constructs rely on the scanner's fail-closed behaviour.
    Non-shell actions and separator-free commands resolve as one string.
    """
    if action == "shell":
        subcommands = split_shell_subcommands(value)
        if len(subcommands) > 1:
            effects = [
                resolve_last_match(rules, action, subcommand)
                for subcommand in subcommands
            ]
            if "deny" in effects:
                return "deny"
            if "ask" in effects:
                return "ask"
            return "allow"
    return resolve_last_match(rules, action, value)


def reject_dangerous_rules(scope: str, rules: list[dict[str, Any]]) -> None:
    """Reject any action-'*' rule whose effect would allow commands."""
    for rule in rules:
        if rule.get("action") == "*" and rule.get("effect", "allow") == "allow":
            raise CheckError(
                f"{scope}: an action '*' rule with effect 'allow' for resource "
                f"{rule.get('resource')!r} would override every project restriction"
            )


def check_agent_rules(agent: str, mode: Any, rules: list[dict[str, Any]]) -> None:
    """Validate one agent's own permission rules against the role policy."""
    require(mode is not None, f"{agent}: agent file must declare a mode")
    require(
        mode == REQUIRED_AGENTS.get(agent),
        f"{agent}: expected mode {REQUIRED_AGENTS.get(agent)!r}, got {mode!r}",
    )
    for rule in rules:
        if rule.get("action") == "*" and rule.get("effect", "allow") == "allow":
            raise CheckError(
                f"{agent}: a broad allow rule (action '*') for resource "
                f"{rule.get('resource')!r} would override the project "
                "write restrictions"
            )
    if agent != "git-manager":
        for rule in rules:
            if rule.get("effect", "allow") == "allow" and str(
                rule.get("action", "")
            ) not in NON_GIT_MANAGER_ALLOW_ACTIONS:
                raise CheckError(
                    f"{agent}: allow rules for action {rule.get('action')!r} are "
                    "reserved for the Git Manager; use deny or ask instead"
                )


def policy_expectations(agent: str) -> list[tuple[str, str, str]]:
    """Samples every agent must resolve to, under last-match-wins semantics."""
    expectations: list[tuple[str, str, str]] = []
    add = expectations.append

    for command in GIT_READ_COMMANDS:
        add(("shell", f"git {command}", "allow"))
        add(("shell", f"rtk git {command}", "allow"))
    for command in GH_READ_COMMANDS:
        add(("shell", f"gh {command}", "allow"))
        add(("shell", f"rtk gh {command}", "allow"))
    for tool in RTK_REPORT_TOOLS:
        add(("shell", f"rtk {tool}", "allow"))
    add(("shell", "rtk read src/x.ts", "allow"))
    add(("shell", "rtk tree src", "allow"))
    for command in GO_QUALITY_SAMPLES + RTK_FILTERED_QUALITY_SAMPLES:
        add(("shell", command, "allow"))

    for command in (
        INFRA_ASK_SAMPLES
        + INFRA_ASK_RTK_SAMPLES
        + WRAPPER_ASK_SAMPLES
        + OUTSIDE_WORKTREE_ASK_SAMPLES
    ):
        add(("shell", command, "ask"))

    for command in (
        SENSITIVE_SHELL_SAMPLES
        + PUSH_TO_MAIN_DENY_SAMPLES
        + GH_API_DENY_SAMPLES
        + NESTED_WRITE_DENY_SAMPLES
        + COMPOUND_PROTECTED_DENY_SAMPLES
        + TOOLCHAIN_DENY_SAMPLES
        + WRAPPER_DENY_SAMPLES
    ):
        add(("shell", command, "deny"))

    for command in HARMLESS_COMPOUND_ALLOW_SAMPLES + ENV_ALLOW_SHELL_SAMPLES:
        add(("shell", command, "allow"))
    add(("shell", OPENCODE_CONFIG_SHELL_SAMPLE, "ask"))

    for path in SENSITIVE_PATH_SAMPLES:
        add(("read", path, "deny"))
        add(("edit", path, "deny"))
        add(("external_directory", path, "deny"))
    add(("external_directory", "~/Library/Fonts/Test.ttf", "deny"))
    add(("external_directory", "/tmp/outside.md", "ask"))
    add(("read", "~/.config/opencode/opencode.json", "ask"))
    add(("external_directory", "~/.config/opencode/opencode.json", "ask"))
    for path in (".env", "src/.env", "config/.env.local"):
        add(("read", path, "deny"))
        add(("edit", path, "deny"))
    for path in (".env.example", "config/.env.example"):
        add(("read", path, "allow"))

    # Edit access to .env.example and the personal OpenCode configuration is
    # decided by the project ask rules only for agents without a blanket edit
    # deny. The Orchestrator, Planner, Reviewer, Tester and Git Manager deny
    # edits themselves; that role boundary wins under last-match-wins.
    blanket_edit_deny = agent != "implementer"
    for path in (".env.example", "config/.env.example"):
        add(("edit", path, "deny" if blanket_edit_deny else "allow"))
    add(
        (
            "edit",
            "~/.config/opencode/opencode.json",
            "deny" if blanket_edit_deny else "ask",
        )
    )

    wanted = "allow" if agent == "git-manager" else "deny"
    for command in GIT_MANAGER_WRITE_COMMANDS + COMPOUND_GIT_MANAGER_ALLOW_SAMPLES:
        add(("shell", command, wanted))
    return expectations


def check_project_rules(rules: list[dict[str, Any]]) -> None:
    """Validate the project-wide policy in opencode.jsonc on its own."""
    def expect(action: str, value: str, wanted: str) -> None:
        actual = effective_effect(rules, action, value)
        require(
            actual == wanted,
            f"project permissions: {action} {value!r} resolves to "
            f"{actual}, expected {wanted}",
        )

    for command in GIT_READ_COMMANDS:
        expect("shell", f"git {command}", "allow")
        expect("shell", f"rtk git {command}", "allow")
    for command in GH_READ_COMMANDS:
        expect("shell", f"gh {command}", "allow")
        expect("shell", f"rtk gh {command}", "allow")
    for tool in RTK_REPORT_TOOLS:
        expect("shell", f"rtk {tool}", "allow")
    for command in GO_QUALITY_SAMPLES + RTK_FILTERED_QUALITY_SAMPLES:
        expect("shell", command, "allow")

    for command in (
        ["git add .", "git commit -m test", "git push origin HEAD"]
        + PUSH_TO_MAIN_DENY_SAMPLES
        + ["git merge main", "git rebase main", "git reset --hard HEAD", "git filter-branch --force"]
        + ["gh pr create --title test", "rtk git add .", "rtk git commit -m test", "rtk gh pr create --title test"]
        + GH_API_DENY_SAMPLES
        + NESTED_WRITE_DENY_SAMPLES
        + COMPOUND_PROTECTED_DENY_SAMPLES
        + TOOLCHAIN_DENY_SAMPLES
        + WRAPPER_DENY_SAMPLES
    ):
        expect("shell", command, "deny")

    for command in HARMLESS_COMPOUND_ALLOW_SAMPLES + ENV_ALLOW_SHELL_SAMPLES:
        expect("shell", command, "allow")
    expect("shell", OPENCODE_CONFIG_SHELL_SAMPLE, "ask")

    for command in (
        INFRA_ASK_SAMPLES
        + INFRA_ASK_RTK_SAMPLES
        + WRAPPER_ASK_SAMPLES
        + OUTSIDE_WORKTREE_ASK_SAMPLES
    ):
        expect("shell", command, "ask")

    for path in SENSITIVE_PATH_SAMPLES:
        expect("read", path, "deny")
        expect("edit", path, "deny")
        expect("external_directory", path, "deny")
    expect("external_directory", "~/Library/Fonts/Test.ttf", "deny")
    expect("external_directory", "/tmp/outside.md", "ask")
    expect("read", "~/.config/opencode/opencode.json", "ask")
    expect("edit", "~/.config/opencode/opencode.json", "ask")
    expect("external_directory", "~/.config/opencode/opencode.json", "ask")
    for path in (".env", "src/.env", "config/.env.local"):
        expect("read", path, "deny")
        expect("edit", path, "deny")
    for path in (".env.example", "config/.env.example"):
        expect("read", path, "allow")
        expect("edit", path, "allow")


def check_config() -> None:
    config = load_jsonc(ROOT / "opencode.jsonc")
    require(config.get("default_agent") == "orchestrator", "default_agent must be orchestrator")
    instructions = config.get("instructions", [])
    require(
        "docs/workflow/feedback-contract.md" in instructions,
        "opencode.jsonc must load the shared feedback contract",
    )

    global_rules = config.get("permissions", [])
    reject_dangerous_rules("project permissions", global_rules)
    check_project_rules(global_rules)

    files = sorted(AGENTS_DIR.glob("*.md"))
    found = {path.stem for path in files}
    require(
        found == set(REQUIRED_AGENTS),
        f".opencode/agents must contain exactly {sorted(REQUIRED_AGENTS)}, "
        f"found {sorted(found)}",
    )

    agent_rules: dict[str, list[dict[str, Any]]] = {}
    combined_by_agent: dict[str, list[dict[str, Any]]] = {}
    for path in files:
        agent = path.stem
        frontmatter, body = read_markdown(path)
        require(bool(frontmatter.get("description")), f"{agent}: description is required")
        require(len(body.strip()) > 200, f"{agent}: system prompt is unexpectedly short")

        rules = parse_permissions(path)
        agent_rules[agent] = rules
        reject_dangerous_rules(agent, rules)
        check_agent_rules(agent, frontmatter.get("mode"), rules)

        combined = list(global_rules) + rules
        combined_by_agent[agent] = combined
        for action, value, wanted in policy_expectations(agent):
            actual = effective_effect(combined, action, value)
            require(
                actual == wanted,
                f"{agent}: {action} {value!r} resolves to {actual}, expected {wanted}",
            )

        def expect_edit(target: str, expected: str) -> None:
            actual = effective_effect(combined, "edit", target)
            require(
                actual == expected,
                f"{agent}: edit {target!r} resolves to {actual}, expected {expected}",
            )

        if agent == "orchestrator":
            expect_edit("docs/workflow/ledgers/issue-30.md", "allow")
            expect_edit("src/main.go", "deny")
        elif agent == "planner":
            expect_edit("docs/adr/ADR-0003-test.md", "allow")
            expect_edit("src/main.go", "deny")
        elif agent == "implementer":
            expect_edit("src/main.go", "allow")
        else:
            expect_edit("src/main.go", "deny")
            expect_edit("docs/workflow/ledgers/issue-30.md", "deny")

        if agent == "orchestrator":
            for launched in ["planner", "reviewer", "implementer", "tester", "git-manager"]:
                require(
                    effective_effect(combined, "subagent", launched) == "allow",
                    f"orchestrator must be allowed to launch {launched}",
                )
            require(
                effective_effect(combined, "subagent", "general") == "deny",
                "orchestrator must not launch agents outside the workflow",
            )
        else:
            require(
                effective_effect(combined, "subagent", "planner") == "deny",
                f"{agent}: subagent delegation belongs to the orchestrator",
            )

    git_manager_rules = agent_rules["git-manager"]
    git_manager_allows = [
        rule
        for rule in git_manager_rules
        if rule.get("action") == "shell"
        and rule.get("effect") == "allow"
        and str(rule.get("resource", "")).startswith(("git ", "gh ", "rtk git ", "rtk gh "))
    ]
    require(bool(git_manager_allows), "git-manager must have Git/GitHub write allow rules")
    for forbidden in ("gh api", "gh pr merge", "rtk gh api", "rtk gh pr merge"):
        require(
            not any(
                str(rule.get("resource", "")).startswith(forbidden)
                for rule in git_manager_allows
            ),
            f"git-manager must not have an allow rule for {forbidden!r}: it is "
            "reserved for the human user",
        )
    trailing_deny_positions: dict[str, int] = {}
    for index, rule in enumerate(git_manager_rules):
        if rule.get("effect") == "deny" and rule.get("action") == "shell":
            trailing_deny_positions[str(rule.get("resource", ""))] = index
    for resource in GIT_MANAGER_REQUIRED_TRAILING_DENIES:
        position = trailing_deny_positions.get(resource)
        require(
            position is not None,
            f"git-manager: deny rule {resource!r} must exist in the frontmatter",
        )
        later_write_allows = [
            str(rule.get("resource", ""))
            for rule in git_manager_rules[position + 1 :]
            if rule.get("action") == "shell"
            and rule.get("effect") == "allow"
            # The project policy re-enables *.env.example after its own env
            # deny; the mirrored allow may follow the deny block for the same
            # reason and is not a Git write.
            and str(rule.get("resource", "")) != "*.env.example"
        ]
        require(
            not later_write_allows,
            f"git-manager: allow rule(s) {later_write_allows} appear after the "
            f"deny rule {resource!r}; the denials must stay last",
        )

    for agent, rules in agent_rules.items():
        combined = combined_by_agent[agent]
        if agent == "git-manager":
            for rule in git_manager_allows:
                resource = str(rule.get("resource", ""))
                sample = resource.replace("*", "sample").strip()
                require(
                    effective_effect(combined, "shell", sample) == "allow",
                    f"git-manager: derived write command {sample!r} is not allowed",
                )
            continue
        shell_allows = [
            rule
            for rule in rules
            if rule.get("action") == "shell" and rule.get("effect") == "allow"
        ]
        require(
            not shell_allows,
            f"{agent}: shell allow rules could override the project write restrictions",
        )
        for rule in git_manager_allows:
            resource = str(rule.get("resource", ""))
            sample = resource.replace("*", "sample").strip()
            require(
                effective_effect(combined, "shell", sample) == "deny",
                f"{agent}: derived write command {sample!r} is not denied",
            )

    agents_md = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    require("feedback-contract.md" in agents_md, "AGENTS.md must point to the feedback contract")
    require("ADR" in agents_md, "AGENTS.md must describe the ADR baseline")
    require(".tmp/" in agents_md, "AGENTS.md must document the .tmp/ scratch convention")
    require("RTK" in agents_md, "AGENTS.md must document the RTK usage rules")
    require(
        "govulncheck" in agents_md and "golangci-lint" in agents_md and "jactionlint" in agents_md,
        "AGENTS.md must list the enabled Go quality tools",
    )

    contract = (ROOT / "docs" / "workflow" / "feedback-contract.md").read_text(
        encoding="utf-8"
    )
    for field in REPORT_FIELDS:
        require(field in contract, f"feedback contract is missing field {field}")

    print(
        "PASS config: six agents, resolved permission boundaries, shared "
        "instructions, Git ownership and human-only merge are consistent"
    )


def check_adr(
    baseline: list[dict[str, Any]], open_pr: list[dict[str, Any]]
) -> tuple[set[str], list[dict[str, Any]], list[dict[str, str]]]:
    baseline_ids, proposals, conflicts = evaluate_adrs(baseline, open_pr)
    print(f"ADR baseline (merged, accepted): {sorted(baseline_ids) or '[]'}")
    for proposal in proposals:
        print(
            "ADR proposal: "
            f"{proposal['id']} declared={proposal['declared_status']} "
            f"effective={proposal['effective_status']}"
        )
    for conflict in conflicts:
        print(
            "ADR escalation: "
            f"{conflict['proposal']} conflicts with {conflict['baseline']}"
        )
    print("PASS adr: open pull-request ADRs remain proposals and do not change the baseline")
    return baseline_ids, proposals, conflicts


def current_branch() -> str:
    result = git("rev-parse", "--abbrev-ref", "HEAD")
    return result.stdout.strip() if result.returncode == 0 else ""


def adr_signature(adr: dict[str, Any]) -> str:
    keys = (
        "id",
        "title",
        "status",
        "date",
        "issues",
        "supersedes",
        "superseded-by",
        "conflicts-with",
        "body_sha256",
    )
    return json.dumps({key: adr.get(key) for key in keys}, sort_keys=True)


def resolve_baseline_ref() -> str | None:
    for ref in ("main", "origin/main"):
        result = git("rev-parse", "--verify", ref)
        if result.returncode == 0:
            return ref
    return None


def check_adr_actual() -> None:
    ref = resolve_baseline_ref()
    if ref is None:
        print(
            "SKIP adr: no local main or origin/main ref; "
            "the fixture still validates baseline handling"
        )
        return
    baseline = adrs_from_ref(ref)
    worktree = adrs_from_dir(ADR_DIR, "open_pr")
    if current_branch() == "main":
        baseline_by_id = {adr["id"]: adr for adr in baseline}
        proposals = []
        for adr in worktree:
            existing = baseline_by_id.get(adr["id"])
            if existing is None or adr_signature(existing) != adr_signature(adr):
                proposals.append(adr)
    else:
        proposals = worktree
    baseline_ids, proposals, conflicts = check_adr(baseline, proposals)
    for proposal in proposals:
        require(
            proposal["effective_status"] != "Accepted",
            f"{proposal['id']} is accepted in the working tree",
        )
    for conflict in conflicts:
        require(
            conflict["baseline"] in baseline_ids,
            f"conflict baseline is not accepted: {conflict['baseline']}",
        )


def validate_report(report: dict[str, Any]) -> None:
    missing = [field for field in REPORT_FIELDS if field not in report]
    require(not missing, f"report {report.get('agent', '<unknown>')} misses fields: {missing}")
    require(report["status"] in REPORT_STATUSES, f"invalid report status: {report['status']}")
    for entry in report["acceptance_criteria_coverage"]:
        require("criterion_id" in entry, "coverage entry misses criterion_id")
        require(entry.get("coverage") in COVERAGE_VALUES, f"invalid coverage: {entry}")


def reconcile(
    criteria: list[dict[str, Any]], reports: list[dict[str, Any]]
) -> tuple[dict[str, dict[str, Any]], list[str], list[str]]:
    ledger: dict[str, dict[str, Any]] = {}
    gaps: list[str] = []
    for criterion in criteria:
        criterion_id = criterion["id"]
        delegated = list(criterion.get("delegated_to", []))
        entries = []
        for report in reports:
            for entry in report["acceptance_criteria_coverage"]:
                if entry["criterion_id"] == criterion_id:
                    entries.append({**entry, "agent": report["agent"]})
        coverage_values = {entry["coverage"] for entry in entries}
        if "covered" in coverage_values:
            status = "covered"
        elif "partial" in coverage_values:
            status = "partial"
        elif "unverified" in coverage_values:
            status = "unverified"
        elif coverage_values == {"not_applicable"}:
            status = "not_applicable"
        else:
            status = "missing"

        criterion_gaps: list[str] = []
        if not delegated:
            criterion_gaps.append("not_delegated")
        for agent in delegated:
            if not any(entry["agent"] == agent for entry in entries):
                criterion_gaps.append(f"delegated_unreported:{agent}")

        evidence = sorted(
            {item for entry in entries for item in entry.get("evidence", [])}
        )
        ledger[criterion_id] = {
            "title": criterion.get("title", ""),
            "delegated_to": delegated,
            "status": status,
            "evidence": evidence,
            "reports": sorted({entry["agent"] for entry in entries}),
            "gaps": criterion_gaps,
        }
        for gap in criterion_gaps:
            gaps.append(f"{criterion_id}:{gap}")
        if status != "covered":
            gaps.append(f"follow_up:{criterion_id}")

    escalations: list[str] = []
    for report in reports:
        if report["status"] == "Needs Decision":
            escalations.append(f"report:{report['agent']}:Needs Decision")
        alignment = report.get("adr_alignment", {})
        for conflict in alignment.get("conflicts", []):
            escalations.append(
                f"adr:{conflict.get('proposal')}:conflicts:{conflict.get('baseline')}"
            )
        for proposal in alignment.get("proposals", []):
            if (
                proposal.get("declared_status") == "Accepted"
                and proposal.get("effective_status") != "Accepted"
            ):
                escalations.append(
                    f"adr:{proposal.get('id')}:declared-accepted-in-open-pr"
                )
    return ledger, gaps, sorted(set(escalations))


def print_ledger(
    ledger: dict[str, dict[str, Any]], gaps: list[str], escalations: list[str]
) -> None:
    print("Acceptance-criteria ledger:")
    print(f"{'Criterion':<10} {'Status':<14} {'Gaps':<38} Delegated to")
    for criterion_id, entry in ledger.items():
        gap_text = ", ".join(entry["gaps"]) or "-"
        print(
            f"{criterion_id:<10} {entry['status']:<14} {gap_text:<38} "
            f"{', '.join(entry['delegated_to']) or '-'}"
        )
    print("Gaps:")
    for gap in gaps:
        print(f"  - {gap}")
    print("Escalations:")
    for escalation in escalations:
        print(f"  - {escalation}")


def check_reports(scenario_path: Path) -> None:
    scenario = json.loads(scenario_path.read_text(encoding="utf-8"))
    base = scenario_path.parent
    criteria = json.loads((base / scenario["criteria_file"]).read_text(encoding="utf-8"))[
        "criteria"
    ]
    reports = []
    for relative in scenario["reports"]:
        report = json.loads((base / relative).read_text(encoding="utf-8"))
        validate_report(report)
        reports.append(report)

    ledger, gaps, escalations = reconcile(criteria, reports)
    print_ledger(ledger, gaps, escalations)

    expected = scenario["expected"]
    actual_status = {criterion_id: entry["status"] for criterion_id, entry in ledger.items()}
    require(
        actual_status == expected["ledger"],
        f"ledger status mismatch: expected {expected['ledger']}, got {actual_status}",
    )
    if "gaps" in expected:
        require(
            set(gaps) == set(expected["gaps"]),
            f"gap set mismatch: expected {sorted(expected['gaps'])}, got {sorted(gaps)}",
        )
    else:
        for expected_gap in expected.get("gaps_include", []):
            require(expected_gap in gaps, f"expected gap not found: {expected_gap}")
    if "escalations" in expected:
        require(
            set(escalations) == set(expected["escalations"]),
            "escalation set mismatch: expected "
            f"{sorted(expected['escalations'])}, got {sorted(escalations)}",
        )
    else:
        for expected_escalation in expected.get("escalations_include", []):
            require(
                expected_escalation in escalations,
                f"expected escalation not found: {expected_escalation}",
            )
    print("PASS reports: synthetic reports reconcile with the exact expected gaps and escalations")


def check_adr_fixture() -> None:
    base = FIXTURES / "adr"
    baseline = adrs_from_dir(base / "baseline", "merged")
    open_pr = adrs_from_dir(base / "open-pr", "open_pr")
    baseline_ids, proposals, conflicts = check_adr(baseline, open_pr)
    require(baseline_ids == {"ADR-0001"}, "fixture baseline mismatch")
    require(len(proposals) == 1, "fixture must contain one open-pull-request proposal")
    require(proposals[0]["id"] == "ADR-0002", "fixture proposal mismatch")
    require(
        proposals[0]["declared_status"] == "Accepted"
        and proposals[0]["effective_status"] == "Proposed",
        "declared Accepted in an open pull request must be an effective proposal",
    )
    require(
        any(conflict["proposal"] == "ADR-0002" for conflict in conflicts),
        "fixture conflict with the baseline must be escalated",
    )


def synthetic_adr(adr_id: str, status: str, source: str, **overrides: Any) -> dict[str, Any]:
    """Build an in-memory ADR record for the self-test fixture.

    The fields mirror the dictionary produced by adr_from_text so the
    evaluation logic is exercised without new repository files.
    """
    adr = {
        "id": adr_id,
        "title": f"{adr_id} synthetic workflow decision",
        "status": status,
        "date": "2026-01-01",
        "issues": ["30"],
        "supersedes": [],
        "superseded-by": None,
        "conflicts-with": [],
        "body_sha256": hashlib.sha256(f"# {adr_id} body".encode("utf-8")).hexdigest(),
        "path": f"docs/adr/{adr_id}-synthetic.md",
        "source": source,
    }
    adr.update(overrides)
    return adr


def check_adr_in_memory_fixture() -> None:
    """Self-test the ADR evaluation helpers with records built in code."""
    unchanged = synthetic_adr("ADR-0100", "Accepted", "merged")
    same_body = synthetic_adr("ADR-0100", "Accepted", "merged")
    edited_body = synthetic_adr("ADR-0100", "Accepted", "merged", body_sha256="0" * 64)
    require(
        adr_signature(unchanged) == adr_signature(same_body),
        "adr_signature must be stable for an unchanged ADR body",
    )
    require(
        adr_signature(unchanged) != adr_signature(edited_body),
        "adr_signature must change when the ADR body changes",
    )

    def expect_error(label: str, call: Any, needle: str) -> None:
        try:
            call()
        except CheckError as error:
            require(
                needle in str(error),
                f"{label}: expected error containing {needle!r}, got: {error}",
            )
            return
        raise CheckError(f"{label}: expected CheckError containing {needle!r}")

    merged_accepted = [synthetic_adr("ADR-0101", "Accepted", "merged")]
    expect_error(
        "unknown superseded-by",
        lambda: evaluate_adrs(
            merged_accepted,
            [
                synthetic_adr(
                    "ADR-0102", "Proposed", "open_pr", **{"superseded-by": "ADR-0999"}
                )
            ],
        ),
        "references unknown ADR ADR-0999",
    )

    merged_rejected = [synthetic_adr("ADR-0103", "Rejected", "merged")]
    expect_error(
        "identifier collision",
        lambda: evaluate_adrs(
            merged_rejected,
            [synthetic_adr("ADR-0103", "Proposed", "open_pr")],
        ),
        "collides with merged ADR ADR-0103",
    )

    merged_mixed = [
        synthetic_adr("ADR-0104", "Accepted", "merged"),
        synthetic_adr("ADR-0105", "Superseded", "merged"),
    ]
    expect_error(
        "conflict with merged non-accepted ADR",
        lambda: evaluate_adrs(
            merged_mixed,
            [
                synthetic_adr(
                    "ADR-0106", "Proposed", "open_pr", **{"conflicts-with": ["ADR-0105"]}
                )
            ],
        ),
        "conflict references a non-accepted ADR: ADR-0105",
    )

    proposed = evaluate_adrs(
        merged_accepted,
        [
            synthetic_adr("ADR-0108", "Accepted", "open_pr"),
            synthetic_adr("ADR-0109", "Rejected", "open_pr"),
            synthetic_adr("ADR-0110", "Superseded", "open_pr"),
            synthetic_adr("ADR-0111", "In Review", "open_pr"),
        ],
    )[1]
    mapping = {
        proposal["id"]: (proposal["declared_status"], proposal["effective_status"])
        for proposal in proposed
    }
    require(
        mapping
        == {
            "ADR-0108": ("Accepted", "Proposed"),
            "ADR-0109": ("Rejected", "Proposed"),
            "ADR-0110": ("Superseded", "Proposed"),
            "ADR-0111": ("In Review", "In Review"),
        },
        f"open pull-request status mapping mismatch: {mapping}",
    )
    print(
        "PASS adr in-memory fixtures: body-signature stability, unknown "
        "references, identifier collisions, non-accepted conflicts and "
        "open pull-request status mapping are enforced"
    )


def check_permissions_fixture() -> None:
    base = FIXTURES / "permissions"
    broad_rules = parse_permissions(base / "planner-broad-allow.md")
    try:
        check_agent_rules("planner", "subagent", broad_rules)
    except CheckError as error:
        require(
            "broad allow" in str(error),
            f"planner fixture must fail on the broad allow rule, got: {error}",
        )
    else:
        raise CheckError("planner fixture with an action '*' allow rule must be rejected")
    compliant_rules = parse_permissions(base / "reviewer-valid.md")
    check_agent_rules("reviewer", "subagent", compliant_rules)
    print(
        "PASS permissions fixtures: over-broad allow rules are rejected and "
        "compliant agent rules pass"
    )


def check_fixtures() -> None:
    check_adr_fixture()
    check_adr_in_memory_fixture()
    check_permissions_fixture()
    check_reports(FIXTURES / "workflow" / "scenario.json")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=["config", "adr", "reports", "fixtures", "all"],
        nargs="?",
        default="all",
    )
    parser.add_argument(
        "--scenario",
        default=str(FIXTURES / "workflow" / "scenario.json"),
        help="feedback reconciliation scenario",
    )
    args = parser.parse_args()
    try:
        if args.command in {"config", "all"}:
            check_config()
        if args.command == "adr":
            check_adr_actual()
        if args.command == "reports":
            check_reports(Path(args.scenario))
        if args.command in {"fixtures", "all"}:
            check_fixtures()
        if args.command == "all":
            check_adr_actual()
        print("All workflow checks passed.")
        return 0
    except CheckError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
