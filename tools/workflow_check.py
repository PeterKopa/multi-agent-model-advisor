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
3. feedback reconciliation with synthetic reports — scenario identity (issue
   and task per agent), ``covered`` claims backed by evidence whose vacuous
   sentinel items (``none`` and friends) count as absent, a note for
   ``not_applicable``, disagreement gaps for contradictory coverage values,
   supersession scoped to the same agent's declared tasks and required to be
   acyclic, and invalid negative fixtures, asserted against the exact
   expected gap and escalation sets;
4. permission fixtures that reject over-broad agent allow rules.

Every ``all`` run starts by auditing this file: ``check_self_audit()`` loads
the sibling ``tools/audit_validator.py`` and statically bounds the constructs
this module may use before any result is trusted.
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
    "rev-list",
    "ls-files",
    "ls-tree",
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
# leading-wildcard mirrors in the project policy. The mirrors use a prefix
# form so the directory itself cannot be enumerated either (ls ~/.ssh).
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
    "ls ~/.ssh",
]
# Env templates are not tracked in the repository, but the policy re-enables
# an `*.env.example` template if one is present, so the shell allow must stay
# proven. Dead-code guard: every sample in this list must be asserted.
ENV_ALLOW_SHELL_SAMPLES = ["cat .env.example", "cat config/.env.example"]

# Plain `ls` is an explicitly allowed read-only convenience; `cat` asks for
# approval because it can also copy files with a redirect and reach arbitrary
# paths. The credential shell mirrors sit later in the rule list and still win
# by last-match (cat ~/.ssh/id_rsa and ls ~/.ssh deny; *.env.example stays
# explicitly readable), so these samples pin the full ladder.
READONLY_SHELL_UTILITY_SAMPLES = ["ls -la"]
ASK_SHELL_UTILITY_SAMPLES = ["cat opencode.json"]

# "echo ok" resolves to default allow, no explicit rule. The sample documents
# that honest boundary — echo is a write primitive through > and >> and is
# deliberately not presented as read-only.
DEFAULT_ALLOW_SHELL_SAMPLES = ["echo ok"]

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
# that must not break (git add/commit followed by an explicit remote-and-
# refspec push to a feature branch — no upstream option, per the push model).
HARMLESS_COMPOUND_ALLOW_SAMPLES = ["git status --short && git diff"]
COMPOUND_GIT_MANAGER_ALLOW_SAMPLES = [
    "git add . && git push origin HEAD",
    "git commit -m x && git push origin issue-30-multi-agent-development-workflow",
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

# Unsafe push forms stay denied even for the Git Manager, in plain and RTK
# form. The base layer is the Git Manager's narrow allow ("git push origin ?*"
# only): remote and refspec separated by exactly one space, at least one
# further character required, so pushes that do not name "origin" with a
# single-space-separated refspec cannot match it. For
# option-bearing pushes the deny model is one shape: every option-bearing push
# (an argument starting with "-", wherever it sits after the verb, which
# subsumes all force spellings, mirror, --all, --delete and the quiet/dry-run
# forms) denies in the agent layer as the second line; the pinned long
# spellings and the measured bypass spellings (-ud, -vd, -uvqf, -q, --quiet,
# --dry-run) pin the regression that motivated the model. The remote-only and
# other-remote shapes are proven below as fall-through cases: they match no
# Git Manager allow, so the project-level "git *" deny decides them. The
# double-space refspec spellings are the measured exception: they match the
# allow (the "?" absorbs the second space) and are re-denied by the agent's
# double-space deny rules as the last match.
UNSAFE_PUSH_DENY_SAMPLES = [
    "git push",
    "git push origin",
    "git push --force origin main",
    "git push --force-with-lease origin main",
    "git push --mirror",
    "git push --all",
    "git push --delete origin feature",
    "git push --follow-tags",
    "git push --dry-run",
    "git push --quiet",
    "git push -q",
    "git push -f",
    "git push -f origin HEAD",
    "git push origin -f HEAD",
    "git push -uf origin issue-42-fix",
    "git push -vf HEAD",
    "git push -qf origin feature",
    "git push origin -qf feature",
    "git push -dv origin feature",
    "git push -ud origin feature",
    "git push -vd origin feature",
    "git push -uvqf origin feature",
    "git push :feature",
    "git push origin :feature",
    "git push origin +main",
    "git push origin +HEAD",
    # Option-after-refspec orderings under the narrow origin allow: the
    # allowlist cannot match these (an option inside the arguments), and both
    # deny shapes must still win with allow-then-deny ordering.
    "git push origin --force feature",
    "git push origin feature+1",
    # Double-space refspec spelling: the narrow allow matches it — the "?"
    # absorbs the second space — so the agent's double-space deny rule
    # re-denies it as the last match; a second space is never part of a
    # legitimate "git push origin <refspec>" handover command.
    "git push origin  HEAD",
    "rtk git push",
    "rtk git push origin",
    "rtk git push --force origin main",
    "rtk git push --force-with-lease origin main",
    "rtk git push --mirror",
    "rtk git push --all",
    "rtk git push --delete origin feature",
    "rtk git push --follow-tags",
    "rtk git push --dry-run",
    "rtk git push --quiet",
    "rtk git push -q",
    "rtk git push -f",
    "rtk git push -f origin HEAD",
    "rtk git push origin -f HEAD",
    "rtk git push -uf origin issue-42-fix",
    "rtk git push -vf HEAD",
    "rtk git push -qf origin feature",
    "rtk git push origin -qf feature",
    "rtk git push -dv origin feature",
    "rtk git push -ud origin feature",
    "rtk git push -vd origin feature",
    "rtk git push -uvqf origin feature",
    "rtk git push :feature",
    "rtk git push origin :feature",
    "rtk git push origin +main",
    "rtk git push origin +HEAD",
    # RTK mirror of the double-space refspec spelling above.
    "rtk git push origin  HEAD",
]

# Non-origin remotes and the whitespace-tail shapes. Under the narrow
# "git push origin ?*" allow the other-remote shapes match no Git Manager
# allow rule at all, so the project-level "git *" deny decides them; those
# samples pin the fall-through instead of an agent deny rule, which the
# narrow allow makes unreachable as a deciding rule for these shapes. The
# whitespace-tail spellings pin the edge of the allow:
# - "git push origin " ends remote-only: the allow separates remote and
#   refspec with exactly one space and demands one further character, so a
#   single trailing space does not complete the match and the project deny
#   decides;
# - "git push origin  " (two trailing spaces) completes the match — the "?"
#   absorbs the second space — so the agent's double-space deny rules
#   "git push origin  *" and its RTK mirror decide them as the last match;
#   three or more spaces share the two-space prefix and fall under the same
#   rules.
NON_ORIGIN_REMOTE_PUSH_DENY_SAMPLES = [
    "git push upstream",
    "git push github",
    "git push upstream main",
    "git push origin ",
    # Two-space whitespace-only tail: completes the narrow allow, re-denied
    # by the agent's double-space deny rule.
    "git push origin  ",
    "rtk git push upstream",
    "rtk git push github",
    "rtk git push origin ",
    # RTK mirror of the two-space whitespace-only tail above.
    "rtk git push origin  ",
]

# Read-only commit enumeration stays available for every agent in both forms.
REV_LIST_ALLOW_SAMPLES = ["git rev-list HEAD", "rtk git rev-list HEAD"]

# Write commands the Git Manager owns, in plain and RTK form. Other agents are
# denied; pushes to main are handled by PUSH_TO_MAIN_DENY_SAMPLES above and are
# therefore excluded here, and push shapes outside the allowlist are handled by
# UNSAFE_PUSH_DENY_SAMPLES and NON_ORIGIN_REMOTE_PUSH_DENY_SAMPLES. Every push
# in this list names origin with an explicit, non-empty refspec — the single
# shape the narrow "git push origin ?*" allow admits: remote and refspec
# separated by exactly one space, at least one further character required —
# without any option (the model denies option-bearing pushes, and the
# double-space spellings are pinned as denies elsewhere). The samples include
# the preserved-allow cases from the model change: a refspec with a
# leading-dash-free branch name, a colon refspec to a feature branch, and a
# branch name containing an internal dash and the letter f.
GIT_MANAGER_WRITE_COMMANDS = [
    "git add .",
    "git commit -m test",
    "git push origin HEAD",
    "git push origin issue-30-multi-agent-development-workflow",
    "git push origin feature-f",
    "git push origin HEAD:refs/heads/feature",
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
    "rtk git push origin HEAD",
    "rtk git push origin issue-30-multi-agent-development-workflow",
    "rtk git push origin feature-f",
    "rtk git push origin HEAD:refs/heads/feature",
    "rtk git switch -c feature",
    "rtk gh pr create --title test",
]

# Deny rules that must appear in the Git Manager frontmatter after every allow
# rule, so they win under last-match-wins resolution. The push denies follow
# the narrow-allow model: option-bearing pushes ("git push -*" and
# "git push * -*" catch any argument starting with "-", plain and RTK) are the
# agent-level second layer; the main/heads-main rules and the blanket
# "+"/":" rules deny force and delete refspecs and pushes to main; the
# double-space rules ("git push origin  *" and the RTK mirror) deny any
# second space after "origin" — the narrow allow still completes the match
# with the "?" absorbing one character, and the required handover form
# separates remote and refspec with exactly one space. No rule in
# this list matches on "?", so no flag-cluster pattern can misfire on branch
# names; the only "?" sits in the allow, and the double-space rules close the
# two-or-more-space family the "?" cannot exclude on its own — the one shape
# no rule here can express is the tab after the space, recorded as a limit in
# the Git Manager's model comment. The remote-only and other-remote
# push shapes carry no
# deny rule of their own — under the narrow "git push origin ?*" allow they
# match no allow rule and the project-level "git *" deny decides them, so an
# agent-level rule would be unreachable as a deciding rule;
# NON_ORIGIN_REMOTE_PUSH_DENY_SAMPLES pins those resolutions behaviourally,
# including the whitespace-tail spellings.
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
    "git push -*",
    "git push * -*",
    "git push *--force*",
    "git push *--mirror*",
    "git push *--all*",
    "git push *--delete*",
    "git push *+main*",
    "git push *+*",
    "git push * :*",
    "git push :*",
    "git push",
    "git push origin  *",
    "rtk git push -*",
    "rtk git push * -*",
    "rtk git push *--force*",
    "rtk git push *--mirror*",
    "rtk git push *--all*",
    "rtk git push *--delete*",
    "rtk git push *+main*",
    "rtk git push *+*",
    "rtk git push * :*",
    "rtk git push :*",
    "rtk git push",
    "rtk git push origin  *",
    "*/.ssh*",
    "*/.aws*",
    "*/.gnupg*",
    "*/.config/gh*",
    "*/.kube*",
    "*/.docker/config.json*",
    "*/.netrc*",
    "*/.git-credentials*",
    "*/.npmrc*",
    "*/.pypirc*",
    "*/.local/share/opencode/auth.json*",
    "*/.local/share/opencode/opencode.db*",
    "*/.local/share/opencode/log/*",
    "*Library/Keychains*",
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
    for command in REV_LIST_ALLOW_SAMPLES:
        add(("shell", command, "allow"))
    for command in GH_READ_COMMANDS:
        add(("shell", f"gh {command}", "allow"))
        add(("shell", f"rtk gh {command}", "allow"))
    for tool in RTK_REPORT_TOOLS:
        add(("shell", f"rtk {tool}", "allow"))
    for command in READONLY_SHELL_UTILITY_SAMPLES + DEFAULT_ALLOW_SHELL_SAMPLES:
        add(("shell", command, "allow"))
    add(("shell", "rtk read src/x.ts", "allow"))
    add(("shell", "rtk tree src", "allow"))
    for command in GO_QUALITY_SAMPLES + RTK_FILTERED_QUALITY_SAMPLES:
        add(("shell", command, "allow"))

    for command in (
        INFRA_ASK_SAMPLES
        + INFRA_ASK_RTK_SAMPLES
        + WRAPPER_ASK_SAMPLES
        + OUTSIDE_WORKTREE_ASK_SAMPLES
        + ASK_SHELL_UTILITY_SAMPLES
    ):
        add(("shell", command, "ask"))

    for command in (
        SENSITIVE_SHELL_SAMPLES
        + PUSH_TO_MAIN_DENY_SAMPLES
        + UNSAFE_PUSH_DENY_SAMPLES
        + NON_ORIGIN_REMOTE_PUSH_DENY_SAMPLES
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
    for command in REV_LIST_ALLOW_SAMPLES:
        expect("shell", command, "allow")
    for command in GH_READ_COMMANDS:
        expect("shell", f"gh {command}", "allow")
        expect("shell", f"rtk gh {command}", "allow")
    for tool in RTK_REPORT_TOOLS:
        expect("shell", f"rtk {tool}", "allow")
    for command in READONLY_SHELL_UTILITY_SAMPLES + DEFAULT_ALLOW_SHELL_SAMPLES:
        expect("shell", command, "allow")
    for command in GO_QUALITY_SAMPLES + RTK_FILTERED_QUALITY_SAMPLES:
        expect("shell", command, "allow")

    for command in (
        ["git add .", "git commit -m test", "git push origin HEAD"]
        + PUSH_TO_MAIN_DENY_SAMPLES
        + UNSAFE_PUSH_DENY_SAMPLES
        + NON_ORIGIN_REMOTE_PUSH_DENY_SAMPLES
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
        + ASK_SHELL_UTILITY_SAMPLES
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
    baseline: list[dict[str, Any]],
    open_pr: list[dict[str, Any]],
) -> tuple[set[str], list[dict[str, Any]], list[dict[str, str]]]:
    baseline_ids, proposals, conflicts = evaluate_adrs(baseline, open_pr)
    baseline_line = f"ADR baseline (merged, accepted): {sorted(baseline_ids) or '[]'}"
    print(baseline_line)
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


def resolve_baseline_ref() -> tuple[str | None, str | None]:
    """Prefer ``origin/main`` and fall back to the local ``main``.

    Returns ``(chosen_ref, warning)``. The warning is a line to print when
    both refs exist and resolve to different commits: a local ``main`` can be
    stale, so ``origin/main`` wins and the disagreement is reported instead
    of silently trusted.
    """
    local = git("rev-parse", "--verify", "main")
    origin = git("rev-parse", "--verify", "origin/main")
    local_sha = local.stdout.strip() if local.returncode == 0 else None
    origin_sha = origin.stdout.strip() if origin.returncode == 0 else None
    if origin_sha is not None:
        if local_sha is not None and local_sha != origin_sha:
            return "origin/main", (
                "WARN adr: local main "
                f"{local_sha[:7]} differs from origin/main {origin_sha[:7]}; "
                "using origin/main"
            )
        return "origin/main", None
    if local_sha is not None:
        return "main", None
    return None, None


def ref_has_adr_records(ref: str) -> bool:
    """Whether the ref carries any ``ADR-*.md`` record under ``docs/adr``.

    A ``docs/adr`` directory that exists but holds no ``ADR-*.md`` file — for
    example only a README or a pre-convention record name — yields no
    baseline records either, so both cases honestly answer ``False``.
    """
    listing = git("ls-tree", "-r", "--name-only", ref, "--", "docs/adr")
    if listing.returncode != 0:
        return False
    return any(
        path.endswith(".md") and Path(path).name.startswith("ADR-")
        for path in listing.stdout.splitlines()
    )


def check_adr_actual() -> None:
    ref, warning = resolve_baseline_ref()
    if ref is None:
        print(
            "SKIP adr: no local main or origin/main ref; "
            "the fixture still validates baseline handling"
        )
        return
    if warning:
        print(warning)
    if not ref_has_adr_records(ref):
        # Reviewer I-8: without ADR records in the baseline ref nothing about
        # the merged baseline can be asserted here, so print a non-asserting
        # line instead of PASS; the fixtures carry the real assertions.
        print(
            f"SKIP adr (live tree): the resolved baseline ref {ref!r} contains "
            "no ADR-*.md record under docs/adr; merged-baseline handling is "
            "asserted only by the fixtures"
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


# Evidence entries that are case-insensitively equal to one of these, or
# empty/whitespace, are treated as absent. The shared feedback contract uses
# `none` as the explicit "no content" sentinel for empty report fields, so a
# sentinel item in `evidence` cannot support a `covered` claim.
VACUOUS_EVIDENCE_TERMS = {
    "",
    "none",
    "n/a",
    "n.a.",
    "na",
    "-",
    "--",
    "tbd",
    "no evidence",
    "none.",
}


def absent_evidence_entry(item: Any) -> bool:
    """Whether one evidence entry carries no content."""
    return (
        not isinstance(item, str)
        or item.strip() == ""
        or item.strip().lower() in VACUOUS_EVIDENCE_TERMS
    )


def evidence_supports_covered(entry: dict[str, Any]) -> bool:
    """Feedback-contract rule 2: a covered claim needs string evidence.

    ``evidence`` must be a non-empty list of strings whose items carry
    content; items that are ``absent_evidence_entry()`` count as absent, so a
    list consisting only of vacuous sentinels (for example ``["none"]``)
    leaves the claim unsupported. Anything else leaves the claim unsupported.
    """
    evidence = entry.get("evidence")
    if not isinstance(evidence, list) or len(evidence) == 0:
        return False
    if not all(isinstance(item, str) for item in evidence):
        return False
    return any(not absent_evidence_entry(item) for item in evidence)


def validate_report(report: dict[str, Any], scenario: dict[str, Any]) -> None:
    """Validate one report against its scenario.

    Beyond field presence and the status enum, the report must match the
    scenario identity — the issue and the task declared for its agent — and
    its coverage entries must carry support: a ``covered`` claim needs
    evidence that survives the vacuous-sentinel filter of
    ``evidence_supports_covered`` and a ``not_applicable`` claim needs a note
    explaining why. ``supersedes`` entries must name tasks the scenario
    declares for the same agent; unknown, cross-agent and self-supersession
    targets are rejected.
    """
    agent = report.get("agent", "<unknown>")
    missing = [field for field in REPORT_FIELDS if field not in report]
    require(not missing, f"report {agent} misses fields: {missing}")
    require(report["status"] in REPORT_STATUSES, f"invalid report status: {report['status']}")

    scenario_issue = scenario.get("issue")
    require(
        report["issue"] == scenario_issue,
        f"report {agent}: issue {report['issue']!r} does not match scenario "
        f"issue {scenario_issue!r}",
    )

    task_id = report["task_id"]
    require(
        isinstance(task_id, str) and task_id.strip() != "",
        f"report {agent}: task_id must be a non-empty string",
    )
    tasks = scenario.get("tasks", {})
    declared = tasks.get(agent) if isinstance(tasks, dict) else None
    require(
        declared is not None,
        f"report {agent}: the scenario declares no task for agent {agent!r}",
    )
    allowed_tasks = list(declared) if isinstance(declared, list) else [declared]
    require(
        task_id in allowed_tasks,
        f"report {agent}: task_id {task_id!r} does not match the scenario "
        f"task declared for this agent: {allowed_tasks!r}",
    )

    for entry in report["acceptance_criteria_coverage"]:
        require(
            "criterion_id" in entry,
            f"report {agent}: coverage entry misses criterion_id: {entry}",
        )
        require(
            entry.get("coverage") in COVERAGE_VALUES,
            f"report {agent}: invalid coverage for "
            f"{entry.get('criterion_id')!r}: {entry.get('coverage')!r}",
        )
        if entry["coverage"] == "covered":
            require(
                evidence_supports_covered(entry),
                f"report {agent}: coverage {entry.get('criterion_id')!r} is "
                "marked covered without evidence: 'evidence' must be a "
                "non-empty list of non-empty strings, and vacuous sentinel "
                "entries such as 'none' count as absent",
            )
        if entry["coverage"] == "not_applicable":
            notes = entry.get("notes")
            require(
                isinstance(notes, str) and notes.strip() != "",
                f"report {agent}: coverage {entry.get('criterion_id')!r} is "
                "marked not_applicable without a note explaining why: "
                "'notes' must be a non-empty string",
            )

    supersedes = report.get("supersedes", [])
    require(
        isinstance(supersedes, list)
        and all(isinstance(task, str) and task.strip() != "" for task in supersedes),
        f"report {agent}: 'supersedes' must be a list of non-empty task_id strings",
    )
    # Supersession identity: each target must name a task the scenario
    # declares for this same agent. Self-supersession, targets of other
    # agents and phantom targets are rejected here instead of silently
    # dropping nothing or dropping another agent's report.
    scenario_tasks = scenario.get("tasks") if isinstance(scenario.get("tasks"), dict) else {}
    for target in supersedes:
        require(
            target != task_id,
            f"report {agent}: 'supersedes' entry {target!r} supersedes its own "
            "task; supersession must point at another task of the same agent",
        )
        if target in allowed_tasks:
            continue
        holder = None
        for other, value in scenario_tasks.items():
            declared_for_other = list(value) if isinstance(value, list) else [value]
            if other != agent and target in declared_for_other:
                holder = other
                break
        if holder is not None:
            require(
                False,
                f"report {agent}: 'supersedes' entry {target!r} supersedes a "
                f"task declared for another agent ({holder!r}); supersession "
                "is scoped to the reporting agent's own tasks",
            )
        all_ids = sorted(
            declared
            for value in scenario_tasks.values()
            for declared in (list(value) if isinstance(value, list) else [value])
        )
        require(
            False,
            f"report {agent}: 'supersedes' entry {target!r} supersedes an "
            f"unknown task; the scenario declares the tasks {all_ids} "
            f"for agents {sorted(scenario_tasks)}",
        )


def assert_acyclic_supersession(reports: list[dict[str, Any]]) -> None:
    """Reject circular supersession instead of silently dropping both reports.

    A cycle (report A supersedes report B while B supersedes A) would let the
    drop step below remove every participating report without a visible gap.
    The graph is built from the ``supersedes`` entries whose target is the
    ``task_id`` of another report in the batch; targets without a report drop
    nothing, so chains through them cannot cycle.
    """
    edges: dict[str, set[str]] = {}
    for report in reports:
        targets = set(report.get("supersedes", []) or [])
        edges.setdefault(report["task_id"], set()).update(targets)
    visiting: set[str] = set()
    done: set[str] = set()
    path: list[str] = []

    def visit(node: str) -> None:
        visiting.add(node)
        path.append(node)
        for target in sorted(edges.get(node, ())):
            if target not in edges or target in done:
                continue
            if target in visiting:
                raise CheckError(
                    "cyclic 'supersedes' chain "
                    + " -> ".join(path[path.index(target):] + [target])
                    + "; superseding reports must form an acyclic chain"
                )
            visit(target)
        path.pop()
        visiting.discard(node)
        done.add(node)

    for node in sorted(edges):
        if node not in done:
            visit(node)


def drop_superseded_reports(reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop reports whose task_id another report supersedes.

    Supersession models a re-done task: the newer report lists the older
    report's ``task_id`` in its ``supersedes`` list and the superseded report
    no longer participates in reconciliation. Reports without supersession
    pass through unchanged. Supersession identity and acyclicity are asserted
    by ``validate_report`` and ``assert_acyclic_supersession`` before the
    drop, so only legitimate single-direction drops reach this step.
    """
    superseded = {
        task for report in reports for task in report.get("supersedes", []) or []
    }
    if not superseded:
        return reports
    return [report for report in reports if report["task_id"] not in superseded]


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
        # Only supported claims count towards coverage: a 'covered' entry
        # without evidence is dropped from the status, evidence and
        # disagreement computation even if a caller skipped validation.
        counted = [
            entry
            for entry in entries
            if entry["coverage"] != "covered" or evidence_supports_covered(entry)
        ]
        coverage_values = {entry["coverage"] for entry in counted}
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
        if len(coverage_values) > 1:
            # Contradictory claims surface as a disagreement gap while the
            # status rule above stays in force: a valid covered entry still
            # wins, so the disagreement is visible without discarding it.
            criterion_gaps.append(
                "disagreement:" + "/".join(sorted(coverage_values))
            )

        evidence = sorted(
            {item for entry in counted for item in entry.get("evidence", [])}
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


def load_scenario_reports(
    scenario_path: Path, scenario: dict[str, Any]
) -> list[dict[str, Any]]:
    base = scenario_path.parent
    reports: list[dict[str, Any]] = []
    for relative in scenario["reports"]:
        report = json.loads((base / relative).read_text(encoding="utf-8"))
        validate_report(report, scenario)
        reports.append(report)
    return reports


def assert_scenario_expectations(
    scenario: dict[str, Any],
    ledger: dict[str, dict[str, Any]],
    gaps: list[str],
    escalations: list[str],
) -> None:
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


def run_report_scenario(
    scenario_path: Path, check_expectations: bool = True
) -> tuple[dict[str, dict[str, Any]], list[str], list[str]]:
    """Validate, supersede-filter and reconcile one report scenario.

    With ``check_expectations`` the scenario's ``expected`` block is asserted
    exactly; invalid-fixture runs disable it because a well-formed failure
    must surface from validation or reconciliation itself.
    """
    scenario = json.loads(scenario_path.read_text(encoding="utf-8"))
    base = scenario_path.parent
    criteria = json.loads((base / scenario["criteria_file"]).read_text(encoding="utf-8"))[
        "criteria"
    ]
    reports = load_scenario_reports(scenario_path, scenario)
    assert_acyclic_supersession(reports)
    reports = drop_superseded_reports(reports)
    ledger, gaps, escalations = reconcile(criteria, reports)
    if check_expectations:
        assert_scenario_expectations(scenario, ledger, gaps, escalations)
    return ledger, gaps, escalations


INVALID_REPORT_FIXTURES = FIXTURES / "workflow" / "invalid"


def check_invalid_report_fixtures() -> None:
    """Run every invalid report fixture; failures name the case and reason.

    Each case directory under ``docs/validation/fixtures/workflow/invalid/``
    holds one ``scenario.json``. A scenario with an ``invalid.error``
    substring must fail validation or reconciliation with a message
    containing that substring; any other scenario reconciles normally and its
    ``expected`` block asserts the stated ledger, gaps and escalations.
    """
    require(
        INVALID_REPORT_FIXTURES.is_dir(),
        f"missing invalid report fixture directory: {INVALID_REPORT_FIXTURES}",
    )
    cases = sorted(path for path in INVALID_REPORT_FIXTURES.iterdir() if path.is_dir())
    require(bool(cases), "at least one invalid report fixture case is required")
    for case_dir in cases:
        label = case_dir.name
        scenario_path = case_dir / "scenario.json"
        require(
            scenario_path.is_file(),
            f"invalid report fixture {label}: scenario.json is required",
        )
        scenario = json.loads(scenario_path.read_text(encoding="utf-8"))
        failure = scenario.get("invalid", {}).get("error")
        if failure is None:
            run_report_scenario(scenario_path)
            print(f"invalid report fixture {label}: reconciled with the stated gaps")
            continue
        try:
            run_report_scenario(scenario_path, check_expectations=False)
        except CheckError as error:
            require(
                failure in str(error),
                f"invalid report fixture {label}: expected an error containing "
                f"{failure!r}, got: {error}",
            )
            print(f"invalid report fixture {label}: rejected as expected: {failure}")
            continue
        raise CheckError(
            f"invalid report fixture {label}: expected a CheckError containing "
            f"{failure!r}, but the reports validated and reconciled cleanly"
        )
    print(
        f"PASS reports negative fixtures: {len(cases)} invalid report cases "
        "fail or reconcile exactly as stated"
    )


def check_reports(scenario_path: Path) -> None:
    scenario = json.loads(scenario_path.read_text(encoding="utf-8"))
    base = scenario_path.parent
    criteria = json.loads((base / scenario["criteria_file"]).read_text(encoding="utf-8"))[
        "criteria"
    ]
    reports = load_scenario_reports(scenario_path, scenario)
    assert_acyclic_supersession(reports)
    reports = drop_superseded_reports(reports)
    ledger, gaps, escalations = reconcile(criteria, reports)
    print_ledger(ledger, gaps, escalations)
    assert_scenario_expectations(scenario, ledger, gaps, escalations)
    print("PASS reports: synthetic reports reconcile with the exact expected gaps and escalations")
    check_invalid_report_fixtures()


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


def check_adr_combined_fixture() -> None:
    """Model the real combined layout: merged baseline plus open proposals.

    The default branch already carries the accepted ADR-0001 requirements
    baseline and the accepted ADR-0003 bootstrap, while the open pull request
    adds ADR-0002 and a changed ADR-0003 that reuses the merged identifier.
    The accepted baseline stays in force: both new records remain proposals
    with an effective status of ``Proposed`` while the pull request is open,
    and a proposal that conflicts with the accepted merged bootstrap still
    escalates.
    """
    base = FIXTURES / "adr" / "combined"
    baseline = adrs_from_dir(base / "baseline", "merged")
    open_pr = adrs_from_dir(base / "open-pr", "open_pr")
    baseline_ids, proposals, conflicts = check_adr(baseline, open_pr)
    require(
        baseline_ids == {"ADR-0001", "ADR-0003"},
        "combined fixture baseline must contain the merged ADR-0001 "
        f"requirements baseline and the accepted bootstrap ADR-0003, got "
        f"{sorted(baseline_ids)}",
    )
    proposal_ids = [proposal["id"] for proposal in proposals]
    require(
        proposal_ids == ["ADR-0002", "ADR-0003"],
        "combined fixture must contain the open proposals ADR-0002 and the "
        f"changed ADR-0003, got {proposal_ids}",
    )
    require(
        all(proposal["effective_status"] == "Proposed" for proposal in proposals),
        "combined fixture proposals must stay effective 'Proposed' while the "
        "pull request is open",
    )
    require(
        any(
            conflict["proposal"] == "ADR-0002" and conflict["baseline"] == "ADR-0003"
            for conflict in conflicts
        ),
        "a combined-layout proposal that conflicts with the merged bootstrap "
        "must escalate",
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


def check_reconcile_in_memory_fixture() -> None:
    """Prove the reconciliation guards in code, without fixture files.

    The negative fixtures cover the report-validated path; this fixture pins
    the defence-in-depth rules in code: an empty-evidence and a
    sentinel-only ``covered`` claim must not produce a covered ledger row,
    contradictory coverage values surface as a disagreement gap without
    discarding a valid covered entry, self-supersession is rejected and a
    cyclic ``supersedes`` chain is rejected instead of silently dropping
    both reports.
    """
    criteria = [
        {
            "id": "AC-01",
            "title": "In-memory reconciliation guard",
            "delegated_to": ["planner"],
        }
    ]

    def report(
        agent: str,
        task_id: str,
        report_status: str,
        entries: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            "agent": agent,
            "issue": 30,
            "task_id": task_id,
            "status": report_status,
            "acceptance_criteria_coverage": entries,
            "missing_requirements": [],
            "adr_alignment": {},
        }

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

    empty = report(
        "planner",
        "issue-30-support",
        "Completed",
        [{"criterion_id": "AC-01", "coverage": "covered", "evidence": []}],
    )
    ledger, gaps, _ = reconcile(criteria, [empty])
    require(
        ledger["AC-01"]["status"] == "missing",
        "an empty-evidence covered claim must not produce a covered ledger "
        f"row: got {ledger['AC-01']['status']}",
    )
    require(
        "follow_up:AC-01" in gaps,
        "an unsupported covered claim must leave the follow_up gap",
    )

    sentinel = report(
        "planner",
        "issue-30-support",
        "Completed",
        [{"criterion_id": "AC-01", "coverage": "covered", "evidence": ["none"]}],
    )
    ledger, _, _ = reconcile(criteria, [sentinel])
    require(
        ledger["AC-01"]["status"] == "missing",
        "a sentinel-evidence ('none') covered claim must not produce a "
        f"covered ledger row: got {ledger['AC-01']['status']}",
    )

    supported = report(
        "implementer",
        "issue-30-support",
        "Completed",
        [{"criterion_id": "AC-01", "coverage": "covered", "evidence": ["docs/x.md"]}],
    )
    contradicting = report(
        "reviewer",
        "issue-30-support-r2",
        "Partial",
        [{"criterion_id": "AC-01", "coverage": "unverified", "evidence": ["docs/x.md"]}],
    )
    ledger, gaps, _ = reconcile(criteria, [supported, contradicting])
    require(
        ledger["AC-01"]["status"] == "covered",
        "a valid covered entry must still win the status rule: "
        f"got {ledger['AC-01']['status']}",
    )
    require(
        "AC-01:disagreement:covered/unverified" in gaps,
        "contradictory coverage values must surface as a disagreement gap: "
        f"gaps are {gaps}",
    )

    def full_report(supersedes: list[str], task_id: str = "issue-30-a") -> dict[str, Any]:
        base = report("tester", task_id, "Completed", [])
        base.update(
            {
                "completed_work": [],
                "findings": [],
                "assumptions": [],
                "dependencies": [],
                "recommended_next_actions": [],
                "feedback": {},
                "supersedes": supersedes,
            }
        )
        return base

    scenario = {"issue": 30, "tasks": {"tester": ["issue-30-a", "issue-30-b"]}}
    expect_error(
        "self-supersession",
        lambda: validate_report(full_report(["issue-30-a"]), scenario),
        "supersedes its own task",
    )
    expect_error(
        "unknown supersession target",
        lambda: validate_report(full_report(["issue-30-phantom"]), scenario),
        "supersedes an unknown task",
    )
    cross_scenario = {
        "issue": 30,
        "tasks": {"tester": "issue-30-a", "implementer": "issue-30-impl"},
    }
    expect_error(
        "cross-agent supersession",
        lambda: validate_report(full_report(["issue-30-impl"]), cross_scenario),
        "supersedes a task declared for another agent",
    )
    expect_error(
        "cyclic supersession",
        lambda: assert_acyclic_supersession(
            [
                {"task_id": "issue-30-a", "supersedes": ["issue-30-b"]},
                {"task_id": "issue-30-b", "supersedes": ["issue-30-a"]},
            ]
        ),
        "cyclic 'supersedes' chain",
    )
    require(
        validate_report(full_report(["issue-30-b"]), scenario) is None,
        "a legitimate same-agent supersession must validate",
    )
    print(
        "PASS reports in-memory fixtures: empty and sentinel-evidence covered "
        "claims stay unsupported, contradictory coverage values surface as "
        "disagreement, and self-, cross-agent, unknown and cyclic supersession "
        "is rejected"
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
    check_adr_combined_fixture()
    check_adr_in_memory_fixture()
    check_permissions_fixture()
    check_reconcile_in_memory_fixture()
    check_reports(FIXTURES / "workflow" / "scenario.json")


def check_self_audit() -> None:
    """Audit this validator statically before its results are trusted.

    ``all`` runs the sibling auditor as its first step. The auditor imports
    only the standard library, parses this file as an AST and fails on
    anything outside its audited boundary; a failure raises the same
    ``CheckError`` every other check uses.
    """
    tools_dir = str(Path(__file__).resolve().parent)
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    import audit_validator

    findings = audit_validator.audit_module(Path(__file__))
    require(
        findings == 0,
        f"the validator failed its own audit with {findings} finding(s); "
        "see the FAIL audit lines above",
    )


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
        if args.command == "all":
            check_self_audit()
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
