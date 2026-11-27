#!/usr/bin/env python3
"""Offline validation for the Multi-Agent Model Advisor development workflow.

The validator checks these things without network access or credentials:

1. the project agent configuration and its permission boundaries, including
   the RTK mirror policy, the Go quality-toolchain allows, the credential-path
   denials, the ask rules for infrastructure tools and paths outside the
   worktree, and the human-only merge enforcement. Compound shell samples are
   split into subcommands so the per-agent expectations follow OpenCode's
   scanner-based shell permission model;
2. ADR baseline handling when an open pull request declares an ADR accepted,
   including reference and identifier validation for the ADR links;
3. feedback reconciliation with synthetic reports — scenario identity (issue
   and task per agent), required model/provider/reviewed-artifact provenance,
   ``covered`` claims backed by current, applicable, content-bearing evidence,
   a note for ``not_applicable``, disagreement demotion instead of
   covered-wins, stale/blocked/wrong-assignment gaps, supersession scoped to
   the same agent's declared tasks and required to be acyclic, and invalid
   negative fixtures asserted against the exact expected ledger, gap,
   escalation and blocker sets;
4. permission fixtures that reject over-broad agent allow rules;
5. the ledger's durable structure — the eight required sections exactly once
   in order, the three required tables with their header and row predicates,
   self-consistent inner tables and forbidden tool-payload shapes;
6. the frozen plan identity — the reviewed commit, ledger path and section
   SHA-256, with anchored line-start boundaries and the trailing blank line;
7. the CI workflow contract — the ``workflow-validator`` job checks out the
   exact pull-request head, records and enforces an explicit base commit and
   runs the trusted ``audit_validator.py`` then ``ci`` commands, with each
   guard proven by a named mutation; the static contract proves the YAML
   shape only, never that a run passed;
8. the single ``release_ready`` boolean over the live release record: the
   committed plan review, independent AI and named-human code reviews, Tester
   verification, inspected workflow-validator CI, current evidence for every
   required criterion, no gaps or disagreements, no open decisions or pending
   proposals and exact PR-head agreement. Only an inspected ``passed`` required
   check is green.

The fixture harness also proves the coordination rules: the AC-PL1 nine-factor
right-sized work-item schema, the AC-CX1 canonical delegation packet and its
links, and the AC-WO1 single-writer ownership cases (disjoint, overlapping,
handover, stale and read-only) with in-memory mutations. Those checks prove the
recorded schema and records only; context sufficiency, write obedience and
filesystem isolation remain instruction and human-judgement rules.

``ci`` is the trusted offline mode (audit plus checks 1-7). ``all`` is ``ci``
plus check 8 and exits non-zero whenever ``release_ready`` is false or the live
record is unavailable. ``config``, ``adr``, ``reports`` and ``fixtures`` are
diagnostics that run one section only. Every ``ci``/``all`` run starts by
auditing this file: ``check_self_audit()`` loads the sibling
``tools/audit_validator.py`` and statically bounds the constructs this module
may use before any result is trusted.
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
CI_WORKFLOW_PATH = ROOT / ".github" / "workflows" / "ci.yml"

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
    "model",
    "provider",
    "reviewed_artifact",
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

# Required-check taxonomy for the live release record. Only an inspected
# ``passed`` check is green; every other state blocks. A verified explicit base
# SHA is an input to a later inspected re-run, never a relabel permission, and a
# named human resolution records identity, rationale, reference and final head.
CHECK_STATES = {"passed", "failed", "skipped", "unavailable", "contributor-reported"}

# Identities that are AI agents or automated roles. They are ineligible for the
# named-human review slot even when the record claims ``reviewer_type: human``.
AI_IDENTITIES = {
    "ai",
    "automation",
    "orchestrator",
    "planner",
    "reviewer",
    "implementer",
    "tester",
    "git-manager",
}

# Provenance accepted for the named-human review: a pull-request review or an
# owner-recorded review. Free text without either source stays open.
HUMAN_REVIEW_PROVENANCE = {"pr-review", "owner-record"}

# A release record binds to commits, not free text. ``pr_head`` and ``artifact``
# are validated as full 40-hex commit identities; only the required CI
# ``base_sha`` keeps the 7-40 abbreviated range, because a verified base may be
# recorded in the abbreviated form CI prints.
COMMIT_ID_RE = re.compile(r"[0-9a-f]{40}")

# Top-level keys the release record may carry. An unknown key is rejected by
# name instead of being silently discarded: a record that declares a binding
# the evaluator ignores would look like evidence it does not have. Schema
# evolution updates this set deliberately, the same way a new git verb needs a
# conscious decision in the self-audit.
RELEASE_KEYS = frozenset(
    {
        "issue",
        "pr_head",
        "artifact",
        "tasks",
        "criteria",
        "reports",
        "plan_review",
        "ai_code_review",
        "human_review",
        "tester_verification",
        "workflow_validator_ci",
        "decisions",
        "proposals",
        "gaps",
    }
)

# Reviewed and frozen issue-30 plan. Identity is
# (commit, ledger path, section SHA-256); the recorded hash is asserted against
# the committed blob and the section boundaries are matched at line starts.
# Byte offsets are deliberately not asserted: they move with unrelated ledger
# edits while the reviewed section bytes stay frozen.
PLAN_REVIEW_COMMIT = "e881bb1"
PLAN_LEDGER_PATH = "docs/workflow/ledgers/issue-30.md"
PLAN_SECTION_SHA256 = (
    "474f2c07a443ea74bf3fb144db52f2a0b67af466c401f9f28e3526163e4f2ce1"
)
PLAN_HEADING = "## Implementation plan (revision 2)"
PLAN_END_HEADING = "## Reports reconciled"

# Ledger structure. The Orchestrator's reconciliation ledger is the only
# change-set artefact that had no structural validation, and malformed table
# rows twice reached a commit: once a cell was appended instead of replaced
# (five cells in a four-column table) and once a raw tool payload was written
# into a row. The check asserts the durable shape — the eight required sections
# exactly once in order, the three required tables with their header and row
# predicates, and self-consistent table blocks everywhere else — plus a small
# set of contamination literals. It reads the working-tree ledger, which is the
# file a commit or a CI checkout carries, and it asserts no byte offset: the
# frozen plan section keeps its own identity check and its inner tables keep
# their own column counts.
LEDGER_PATH = ROOT / "docs" / "workflow" / "ledgers" / "issue-30.md"
LEDGER_SECTIONS = (
    "## Acceptance criteria",
    PLAN_HEADING,
    "## Reports reconciled",
    "## Findings and resolutions",
    "## Architecture baseline",
    "## Unresolved items",
    "## Deferred or out-of-scope work",
    "## Handover",
)
# Section -> (required header first cell, required column count).
LEDGER_TABLE_SPECS = {
    "## Acceptance criteria": ("ID", 6),
    "## Reports reconciled": ("Agent", 5),
    "## Findings and resolutions": ("Severity", 4),
}
LEDGER_ROLE_NAMES = (
    "Orchestrator",
    "Planner",
    "Reviewer",
    "Implementer",
    "Tester",
    "Git Manager",
)
LEDGER_SEVERITIES = ("High", "Medium", "Low", "Informational")
# Severity vocabulary that must use one of the four canonical labels. Rows
# with a non-severity first cell (for example the ledger's `Decision` and
# `P1`/`P2` external-review rows) are exempt, the same way the report table
# tolerates non-role sources such as `Synthetic fixture`.
LEDGER_SEVERITY_LIKE = {
    "high",
    "medium",
    "low",
    "informational",
    "critical",
    "severe",
    "major",
    "minor",
    "trivial",
    "info",
    "warning",
    "blocker",
}
# Payload contamination that has actually occurred or that a tool call leaves
# behind. The first two are the raw edit payload from the recorded incident;
# the third is a literal `\n|` escape that would corrupt a table row.
LEDGER_FORBIDDEN_LITERALS = ('","oldString"', '","newString"', "\\n|")
# A line that ends in `}` while quoting a JSON key/value pair is a tool-call
# tail pasted after prose, not ledger content.
LEDGER_PAYLOAD_TAIL_RE = re.compile(r'"[A-Za-z_][A-Za-z0-9_]*"\s*:')

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
    for token in ("thinking", "check_state", "reviewed_artifact"):
        require(
            token in contract,
            f"feedback contract is missing the {token!r} provenance/check field",
        )

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


def extract_plan_section(text: str) -> str:
    """Extract the frozen plan section from the committed ledger blob.

    The section starts at the line-start heading and ends immediately before
    the line-start ``## Reports reconciled`` heading that follows it. Both
    boundaries are anchored to the start of a line, so a mention inside prose
    or a code fence cannot shift the slice. The section must end with the
    trailing blank line (``\\n\\n``) the freeze protocol records. No byte
    offset is asserted: offsets move when unrelated ledger sections change,
    while the reviewed bytes do not.
    """
    heading = re.compile(r"^" + re.escape(PLAN_HEADING) + r"$", re.MULTILINE)
    headings = list(heading.finditer(text))
    require(
        len(headings) == 1,
        f"the committed ledger must contain exactly one line-start heading "
        f"{PLAN_HEADING!r}, found {len(headings)}",
    )
    start = headings[0].start()
    tail = text[start + len(PLAN_HEADING) :]
    end_heading = re.compile(
        r"^" + re.escape(PLAN_END_HEADING) + r"$", re.MULTILINE
    ).search(tail)
    require(
        end_heading is not None,
        f"the committed ledger has no line-start {PLAN_END_HEADING!r} after "
        "the plan heading",
    )
    section = text[start : start + len(PLAN_HEADING) + end_heading.start()]
    require(
        section.endswith("\n\n"),
        "the frozen plan section must end with the trailing blank line "
        "(\\n\\n) recorded by the freeze protocol",
    )
    return section


def check_plan_identity() -> None:
    """Bind the reviewed plan to its committed bytes and durable structure.

    The reviewed commit, ledger path and section SHA-256 are the plan
    identity. The check reads the committed blob at that commit, extracts the
    section with anchored line-start matches and recomputes the hash; it does
    not assert a byte offset, because offsets move with unrelated ledger edits
    while the reviewed section bytes stay frozen.
    """
    shown = git("show", f"{PLAN_REVIEW_COMMIT}:{PLAN_LEDGER_PATH}")
    require(
        shown.returncode == 0,
        f"cannot read {PLAN_LEDGER_PATH!r} at the reviewed commit "
        f"{PLAN_REVIEW_COMMIT!r}: {shown.stderr.strip()}",
    )
    section = extract_plan_section(shown.stdout)
    digest = hashlib.sha256(section.encode("utf-8")).hexdigest()
    require(
        digest == PLAN_SECTION_SHA256,
        "reviewed plan section hash mismatch: recorded "
        f"{PLAN_SECTION_SHA256}, recomputed {digest}",
    )
    print(
        "PASS plan identity: reviewed section of "
        f"{PLAN_LEDGER_PATH} at {PLAN_REVIEW_COMMIT} matches "
        f"sha256 {digest} ({len(section.encode('utf-8'))} bytes)"
    )


def _ledger_table_cells(line: str) -> list[str]:
    """Split one Markdown table row, ignoring escaped and code-span pipes."""
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    cells: list[str] = []
    current: list[str] = []
    in_code = False
    escaped = False
    for character in stripped:
        if escaped:
            current.append(character)
            escaped = False
        elif character == "\\":
            escaped = True
            current.append(character)
        elif character == "`":
            in_code = not in_code
            current.append(character)
        elif character == "|" and not in_code:
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(character)
    cells.append("".join(current).strip())
    return cells


def _ledger_headings(lines: list[str]) -> list[tuple[int, str]]:
    """Return ``(zero-based index, heading)`` for every ``## `` heading."""
    return [
        (index, line)
        for index, line in enumerate(lines)
        if line.startswith("## ")
    ]


def _ledger_section_ranges(
    lines: list[str],
) -> tuple[list[tuple[int, str]], dict[str, list[tuple[int, int]]]]:
    """Map each top-level heading to its half-open line ranges.

    The returned ranges are zero-based and end at the next ``## `` heading, so
    a ``###`` subsection stays inside its parent section. A duplicated heading
    yields more than one range; the section check rejects that explicitly.
    """
    headings = _ledger_headings(lines)
    ranges: dict[str, list[tuple[int, int]]] = {}
    for position, (index, heading) in enumerate(headings):
        end = headings[position + 1][0] if position + 1 < len(headings) else len(lines)
        ranges.setdefault(heading, []).append((index, end))
    return headings, ranges


def _ledger_table_blocks(
    lines: list[str], start: int, end: int
) -> list[tuple[int, int]]:
    """Return half-open runs of consecutive table lines inside a section."""
    blocks: list[tuple[int, int]] = []
    index = start
    while index < end:
        if lines[index].startswith("|"):
            block_start = index
            while index < end and lines[index].startswith("|"):
                index += 1
            blocks.append((block_start, index))
        else:
            index += 1
    return blocks


def _ledger_header_cell(cells: list[str]) -> str:
    """Normalise a header cell's Markdown emphasis for comparison."""
    return cells[0].strip().strip("*` ")


def _check_ledger_sections(
    headings: list[tuple[int, str]], label: str
) -> None:
    """Assert the eight required sections exactly once, in the documented order."""
    positions: list[int] = []
    for section in LEDGER_SECTIONS:
        found = [index for index, heading in headings if heading == section]
        if not found:
            raise CheckError(f"{label}: missing required ledger section {section!r}")
        if len(found) > 1:
            rendered = ", ".join(str(index + 1) for index in found)
            raise CheckError(
                f"{label}: required ledger section {section!r} appears "
                f"{len(found)} times (lines {rendered}); it must appear exactly once"
            )
        positions.append(found[0])
    for position in range(1, len(positions)):
        if positions[position] <= positions[position - 1]:
            previous = LEDGER_SECTIONS[position - 1]
            current = LEDGER_SECTIONS[position]
            raise CheckError(
                f"{label}: required ledger sections are out of order: "
                f"{current!r} (line {positions[position] + 1}) must follow "
                f"{previous!r} (line {positions[position - 1] + 1})"
            )


def _check_ledger_block_columns(
    lines: list[str],
    block_start: int,
    block_end: int,
    expected: int,
    section: str,
    label: str,
) -> None:
    """Every row of a required table must have exactly ``expected`` cells."""
    for index in range(block_start, block_end):
        actual = len(_ledger_table_cells(lines[index]))
        if actual != expected:
            raise CheckError(
                f"{label}:{index + 1}: table row in {section!r} has "
                f"{actual} cells, expected {expected}"
            )


def _check_ledger_block_consistency(
    lines: list[str],
    block_start: int,
    block_end: int,
    label: str,
) -> None:
    """Rows in a non-required table block must match that block's own header.

    This is what keeps a real table inside a prose section, and each inner
    table of the frozen plan section, valid with its own column count instead
    of the column count of the three required tables.
    """
    header_count = len(_ledger_table_cells(lines[block_start]))
    for index in range(block_start + 1, block_end):
        actual = len(_ledger_table_cells(lines[index]))
        if actual != header_count:
            raise CheckError(
                f"{label}:{index + 1}: table row has {actual} cells, expected "
                f"{header_count} from the block header at line {block_start + 1}"
            )


def _ledger_data_rows(
    lines: list[str], block_start: int, block_end: int
) -> list[tuple[int, list[str]]]:
    """Return the content rows of a table block, without header or separator."""
    rows: list[tuple[int, list[str]]] = []
    for index in range(block_start + 1, block_end):
        cells = _ledger_table_cells(lines[index])
        if cells and any(cell for cell in cells) and all(
            re.fullmatch(r":?-+:?", cell) for cell in cells if cell
        ):
            continue
        rows.append((index, cells))
    return rows


def _check_ledger_row_predicate(
    lines: list[str],
    block_start: int,
    block_end: int,
    section: str,
    label: str,
) -> None:
    """Assert the per-section first-cell predicate for a required table."""
    for index, cells in _ledger_data_rows(lines, block_start, block_end):
        first = cells[0]
        if section == "## Acceptance criteria":
            if not first.strip("`* ").startswith("AC-"):
                raise CheckError(
                    f"{label}:{index + 1}: acceptance-criteria row must start "
                    f"with 'AC-', got {first!r}"
                )
        elif section == "## Reports reconciled":
            lowered = first.lower()
            mentioned = [
                role for role in LEDGER_ROLE_NAMES if role.lower() in lowered
            ]
            if mentioned and not any(
                lowered.startswith(role.lower()) for role in LEDGER_ROLE_NAMES
            ):
                raise CheckError(
                    f"{label}:{index + 1}: agent-role row must begin with one of "
                    f"{list(LEDGER_ROLE_NAMES)}, got {first!r}"
                )
        elif section == "## Findings and resolutions":
            token = re.match(r"[A-Za-z]+", first)
            if token and token.group(0).lower() in LEDGER_SEVERITY_LIKE:
                if not any(
                    first.lower().startswith(severity.lower())
                    for severity in LEDGER_SEVERITIES
                ):
                    raise CheckError(
                        f"{label}:{index + 1}: findings row severity must be one "
                        f"of {list(LEDGER_SEVERITIES)}, got {first!r}"
                    )


def _check_ledger_forbidden(
    text: str, lines: list[str], label: str
) -> None:
    """Reject tool-payload contamination anywhere in the ledger."""
    for literal in LEDGER_FORBIDDEN_LITERALS:
        position = text.find(literal)
        if position >= 0:
            line_number = text.count("\n", 0, position) + 1
            raise CheckError(
                f"{label}:{line_number}: forbidden tool-payload literal "
                f"{literal!r} in ledger content"
            )
    for index, line in enumerate(lines, 1):
        stripped = line.rstrip()
        if stripped.endswith("}") and LEDGER_PAYLOAD_TAIL_RE.search(stripped):
            raise CheckError(
                f"{label}:{index}: line ends with a '}}' tool-payload tail "
                f"after prose: {stripped[:120]!r}"
            )


def _ledger_spec_table(
    lines: list[str],
    start: int,
    end: int,
    header: str,
    section: str,
    label: str,
) -> tuple[int, int]:
    """Locate the one table in a section whose header first cell matches."""
    matches = [
        (block_start, block_end)
        for block_start, block_end in _ledger_table_blocks(lines, start, end)
        if _ledger_header_cell(_ledger_table_cells(lines[block_start])) == header
    ]
    if len(matches) != 1:
        raise CheckError(
            f"{label}: {section!r} must contain exactly one table whose "
            f"header first cell is {header!r}, found {len(matches)}"
        )
    return matches[0]


def _validate_ledger_structure(text: str, label: str) -> tuple[int, int]:
    """Validate the ledger text and return ``(required rows, table blocks)``."""
    lines = text.splitlines()
    headings, ranges = _ledger_section_ranges(lines)
    _check_ledger_sections(headings, label)
    _check_ledger_forbidden(text, lines, label)

    designated: set[int] = set()
    required_rows = 0
    for section, (header, columns) in LEDGER_TABLE_SPECS.items():
        start, end = ranges[section][0]
        block_start, block_end = _ledger_spec_table(
            lines, start, end, header, section, label
        )
        designated.add(block_start)
        _check_ledger_block_columns(
            lines, block_start, block_end, columns, section, label
        )
        _check_ledger_row_predicate(
            lines, block_start, block_end, section, label
        )
        required_rows += len(_ledger_data_rows(lines, block_start, block_end))

    blocks = 0
    for section_ranges in ranges.values():
        if len(section_ranges) != 1:
            continue
        section_start, section_end = section_ranges[0]
        for block_start, block_end in _ledger_table_blocks(
            lines, section_start, section_end
        ):
            blocks += 1
            if block_start in designated:
                continue
            _check_ledger_block_consistency(
                lines, block_start, block_end, label
            )
    return required_rows, blocks


def check_ledger_structure(
    text: str | None = None, label: str = PLAN_LEDGER_PATH
) -> None:
    """Validate the durable structure of the reconciliation ledger.

    The check is deliberately about shape, not prose: it can prove that a row
    was not appended to or cut into a table, not that a sentence is true. It
    reads the working-tree ledger by default and accepts in-memory text so the
    fixture harness can prove each guard. It asserts no byte offset and it does
    not touch the frozen plan section: that section's identity is
    ``check_plan_identity()``'s job, and its inner tables are validated only
    for self-consistency against their own headers.
    """
    if text is None:
        require(
            LEDGER_PATH.is_file(),
            f"missing reconciliation ledger: {PLAN_LEDGER_PATH}",
        )
        text = LEDGER_PATH.read_text(encoding="utf-8")
    required_rows, blocks = _validate_ledger_structure(text, label)
    column_counts = "/".join(
        str(columns) for _, columns in LEDGER_TABLE_SPECS.values()
    )
    print(
        f"PASS ledger structure: {len(LEDGER_SECTIONS)} sections in order; "
        f"3 required tables ({column_counts} columns) with {required_rows} "
        f"data rows; {blocks} table blocks self-consistent; "
        f"{len(LEDGER_FORBIDDEN_LITERALS) + 1} forbidden payload shapes absent"
    )


def deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> None:
    """Merge ``patch`` into ``base`` in place, recursing into dictionaries."""
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            deep_merge(base[key], value)
        else:
            base[key] = value


def synthetic_release() -> dict[str, Any]:
    """Build the synthetic all-green release record for the fixture harness.

    This proves the evaluator only. It is not live release evidence and never
    establishes real readiness; the live record is the Orchestrator-owned
    JSON document passed to ``all``.
    """
    head = "1" * 40
    base_sha = "2" * 40

    def report(agent: str, task_id: str, criterion_id: str) -> dict[str, Any]:
        return {
            "agent": agent,
            "issue": 30,
            "task_id": task_id,
            "status": "Completed",
            "model": "synthetic-model",
            "provider": "synthetic-provider",
            "thinking": "unknown",
            "reviewed_artifact": head,
            "completed_work": ["Synthetic release fixture work."],
            "acceptance_criteria_coverage": [
                {
                    "criterion_id": criterion_id,
                    "coverage": "covered",
                    "evidence": [
                        "docs/validation/fixtures/workflow/scenario.json"
                    ],
                }
            ],
            "missing_requirements": [],
            "findings": [],
            "assumptions": [],
            "dependencies": [],
            "adr_alignment": {
                "baseline": [],
                "proposals": [],
                "conflicts": [],
                "decision_needed": [],
            },
            "recommended_next_actions": [],
            "feedback": {
                "delegation": "Synthetic release fixture.",
                "planning": "Synthetic release fixture.",
                "instructions": "Synthetic release fixture.",
                "collaboration": "Synthetic release fixture.",
            },
        }

    return {
        "issue": 30,
        "pr_head": head,
        "artifact": head,
        "tasks": {
            "implementer": "t-release-impl",
            "tester": "t-release-test",
        },
        "criteria": [
            {
                "id": "AC-01",
                "title": "Synthetic release criterion one",
                "delegated_to": ["implementer"],
                "required": True,
            },
            {
                "id": "AC-02",
                "title": "Synthetic release criterion two",
                "delegated_to": ["tester"],
                "required": True,
            },
        ],
        "reports": [
            report("implementer", "t-release-impl", "AC-01"),
            report("tester", "t-release-test", "AC-02"),
        ],
        "plan_review": {
            "state": "passed",
            "commit": PLAN_REVIEW_COMMIT,
            "section_sha256": PLAN_SECTION_SHA256,
        },
        "ai_code_review": {
            "state": "passed",
            "reviewer_type": "ai",
            "reviewer": "reviewer",
            "head": head,
        },
        "human_review": {
            "state": "passed",
            "reviewer_type": "human",
            "name": "Ada Lovelace",
            "login": "ada-lovelace",
            "attribution": "human",
            "independent": True,
            "provenance": "pr-review",
            "review_id": "REVIEW-1",
            "timestamp": "2026-11-27T10:00:00Z",
            "head": head,
        },
        "tester_verification": {"state": "passed", "head": head},
        "workflow_validator_ci": {
            "state": "passed",
            "inspected": True,
            "head": head,
            "base_sha": base_sha,
            "continue_on_error": False,
            "job": "workflow-validator",
            "run": "1",
        },
        "decisions": [],
        "proposals": [],
        "gaps": [],
    }


def release_check(
    release: dict[str, Any], name: str, *, inspected: bool = False
) -> tuple[dict[str, Any] | None, list[str]]:
    """Resolve one required release check under the check-state taxonomy."""
    value = release.get(name)
    if not isinstance(value, dict):
        return None, [f"{name}:missing"]
    state = value.get("state")
    if state not in CHECK_STATES:
        return None, [f"{name}:invalid-state:{state}"]
    if state != "passed":
        return None, [f"{name}:{state}"]
    if inspected and value.get("inspected") is not True:
        return None, [f"{name}:not-inspected"]
    return value, []


def recorded_ai_identities(release: dict[str, Any]) -> set[str]:
    """Collect every AI identity recorded in the same release record.

    The static agent-name set is always included. The AI review slot may carry
    a model-style reviewer name (for example ``deepseek-v4.1-flash``) that is
    not an agent ID; reusing it in the human slot must still fail, so the
    recorded value is added to the ineligible set for this record.
    """
    identities = set(AI_IDENTITIES)
    for slot_name in ("ai_code_review", "plan_review"):
        slot = release.get(slot_name)
        if not isinstance(slot, dict):
            continue
        for key in ("reviewer", "name", "login", "model"):
            value = slot.get(key)
            if isinstance(value, str) and value.strip():
                identities.add(value.strip().lower())
    return identities


def human_review_blockers(
    slot: dict[str, Any], pr_head: str, ai_identities: set[str]
) -> list[str]:
    """Validate the named-human review slot.

    Distinctness (a human-attributed name and login outside the AI identity
    set, and distinct from each other) and provenance (a pull-request review
    or an owner record) are separate load-bearing checks; removing any of them
    lets the fixture pass. Actual human independence remains attested
    judgement, labelled in the documentation.
    """
    blockers: list[str] = []
    if slot.get("reviewer_type") != "human":
        blockers.append("human_review:not-human")
    name = str(slot.get("name", "")).strip()
    login = str(slot.get("login", "")).strip()
    if not name or not login:
        blockers.append("human_review:missing-identity")
    if {name.lower(), login.lower()} & ai_identities:
        blockers.append("human_review:ai-identity")
    if name and login and name.lower() == login.lower():
        blockers.append("human_review:name-equals-login")
    if str(slot.get("attribution", "")).strip().lower() != "human":
        blockers.append("human_review:missing-attribution")
    if slot.get("independent") is not True:
        blockers.append("human_review:not-independent")
    provenance = slot.get("provenance")
    if provenance not in HUMAN_REVIEW_PROVENANCE:
        blockers.append("human_review:missing-provenance")
    elif provenance == "pr-review" and not str(slot.get("review_id", "")).strip():
        blockers.append("human_review:missing-provenance")
    elif provenance == "owner-record" and not str(slot.get("record", "")).strip():
        blockers.append("human_review:missing-provenance")
    if not str(slot.get("timestamp", "")).strip():
        blockers.append("human_review:missing-timestamp")
    if slot.get("head") != pr_head:
        blockers.append("human_review:head-mismatch")
    return blockers


def decision_resolution_blockers(
    decision_id: Any,
    decision: dict[str, Any],
    pr_head: str,
    ai_identities: set[str],
) -> list[str]:
    """Require a non-AI identity, rationale, reference and final head.

    A required decision is human-only, so ``resolved_by`` must be absent from
    the same ineligible-identity set the named-human slot uses: the static
    agent names plus every AI identity recorded in this release record. A
    record whose AI reviewer's model identity closes a decision is the same
    bypass as a human slot reusing it, so the dynamic half is load-bearing and
    the comparison is literal after lowercase normalisation, like the slot.
    """
    blockers: list[str] = []
    resolved_by = str(decision.get("resolved_by", "")).strip()
    if not resolved_by or resolved_by.lower() in ai_identities:
        blockers.append(f"decision-resolution:{decision_id}:identity")
    if not str(decision.get("rationale", "")).strip():
        blockers.append(f"decision-resolution:{decision_id}:rationale")
    if not str(decision.get("reference", "")).strip():
        blockers.append(f"decision-resolution:{decision_id}:reference")
    if decision.get("head") != pr_head:
        blockers.append(f"decision-resolution:{decision_id}:head")
    return blockers


def evaluate_release_gate(release: dict[str, Any]) -> dict[str, Any]:
    """Evaluate the single release boolean and return its exact blockers.

    ``release_ready`` is one boolean. Its conjuncts are the committed plan
    review, the independent AI code review, the named-human code review, the
    Tester verification, the inspected workflow-validator CI run, current
    applicable evidence for every required criterion, no gaps, no
    disagreements, no ``decision_needed``, no pending effective proposals, no
    open required decisions and exact PR-head agreement across evidence.
    ``pr_head`` and the record ``artifact`` are full 40-hex commit identities,
    never free text, and an unknown top-level key blocks by name instead of
    being discarded.
    """
    blockers: list[str] = []
    issue = release.get("issue")
    for key in sorted(release):
        if key not in RELEASE_KEYS:
            blockers.append(f"release-record:unknown-key:{key}")
    pr_head = release.get("pr_head")
    pr_head_valid = (
        isinstance(pr_head, str) and COMMIT_ID_RE.fullmatch(pr_head) is not None
    )
    if not isinstance(pr_head, str) or pr_head.strip() == "":
        blockers.append("pr_head:missing")
    elif not pr_head_valid:
        blockers.append("pr_head:invalid")

    artifact = release.get("artifact")
    artifact_value: str | None = None
    artifact_present = isinstance(artifact, str) and artifact.strip() != ""
    artifact_valid = (
        artifact_present and COMMIT_ID_RE.fullmatch(artifact) is not None
    )
    if not artifact_present:
        blockers.append("artifact:missing")
    else:
        if not artifact_valid:
            blockers.append("artifact:invalid")
        else:
            artifact_value = artifact
        if pr_head_valid and artifact != pr_head:
            blockers.append("artifact:head-mismatch")

    plan, plan_blockers = release_check(release, "plan_review")
    blockers.extend(plan_blockers)
    if plan is not None:
        if plan.get("commit") != PLAN_REVIEW_COMMIT:
            blockers.append("plan_review:commit-mismatch")
        if plan.get("section_sha256") != PLAN_SECTION_SHA256:
            blockers.append("plan_review:hash-mismatch")

    ai_review, ai_blockers = release_check(release, "ai_code_review")
    blockers.extend(ai_blockers)
    if ai_review is not None:
        if ai_review.get("reviewer_type") != "ai":
            blockers.append("ai_code_review:not-ai")
        if ai_review.get("head") != pr_head:
            blockers.append("ai_code_review:head-mismatch")

    human, human_slot_blockers = release_check(release, "human_review")
    blockers.extend(human_slot_blockers)
    # One ineligible-identity set per record: the static agent names plus every
    # AI identity recorded here. The human slot and the human-only decision
    # resolutions both compare against it, so an AI model identity cannot close
    # either one.
    ai_identities = recorded_ai_identities(release)
    if human is not None:
        blockers.extend(human_review_blockers(human, pr_head, ai_identities))

    tester, tester_blockers = release_check(release, "tester_verification")
    blockers.extend(tester_blockers)
    if tester is not None and tester.get("head") != pr_head:
        blockers.append("tester_verification:head-mismatch")

    ci, ci_blockers = release_check(
        release, "workflow_validator_ci", inspected=True
    )
    blockers.extend(ci_blockers)
    if ci is not None:
        if ci.get("head") != pr_head:
            blockers.append("workflow_validator_ci:head-mismatch")
        base_sha = ci.get("base_sha")
        if not isinstance(base_sha, str) or not base_sha.strip():
            blockers.append("workflow_validator_ci:missing-base")
        elif not re.fullmatch(r"[0-9a-f]{7,40}", base_sha):
            blockers.append("workflow_validator_ci:invalid-base")
        if not str(ci.get("job", "")).strip():
            blockers.append("workflow_validator_ci:missing-job")
        if not str(ci.get("run", "")).strip():
            blockers.append("workflow_validator_ci:missing-run")
        if ci.get("continue_on_error") is not False:
            blockers.append("workflow_validator_ci:continue-on-error")

    ledger: dict[str, dict[str, Any]] = {}
    gaps: list[str] = []
    escalations: list[str] = []
    criteria = release.get("criteria")
    reports = release.get("reports")
    if not isinstance(criteria, list) or not criteria:
        blockers.append("criteria:missing")
    elif not isinstance(reports, list):
        blockers.append("reports:missing")
    else:
        scenario = {"issue": issue, "tasks": release.get("tasks", {})}
        try:
            for report in reports:
                if not isinstance(report, dict):
                    raise CheckError("every report must be a JSON object")
                validate_report(report, scenario)
            ledger, gaps, escalations = reconcile(
                criteria,
                reports,
                artifact=artifact_value,
            )
        except (CheckError, AttributeError, TypeError, KeyError) as error:
            blockers.append(f"reports:invalid:{error}")

    for criterion in criteria if isinstance(criteria, list) else []:
        if not isinstance(criterion, dict):
            blockers.append("criteria:invalid")
            continue
        if not criterion.get("required", True):
            continue
        entry = ledger.get(criterion.get("id"))
        if entry is None or entry["status"] != "covered":
            status = entry["status"] if entry is not None else "missing"
            blockers.append(f"criterion-open:{criterion.get('id')}:{status}")
    for gap in gaps:
        blockers.append(f"gap:{gap}")
    if gaps:
        blockers.append("gaps:present")
    if any(":disagreement:" in gap for gap in gaps):
        blockers.append("disagreement:present")
    release_gaps = release.get("gaps") or []
    if not isinstance(release_gaps, list):
        blockers.append("gaps:invalid")
        release_gaps = []
    for gap in release_gaps:
        blockers.append(f"release-gap:{gap}")
    for escalation in escalations:
        blockers.append(f"escalation:{escalation}")
    if any(escalation.startswith("decision:") for escalation in escalations):
        blockers.append("decision_needed:present")
    if any(
        escalation.startswith("adr:") and ":pending:" in escalation
        for escalation in escalations
    ):
        blockers.append("pending-proposal:present")
    if any(":stale_artifact:" in gap for gap in gaps):
        blockers.append("stale-artifact:present")

    decisions = release.get("decisions") or []
    if not isinstance(decisions, list):
        blockers.append("decisions:invalid")
        decisions = []
    for decision in decisions:
        if not isinstance(decision, dict):
            blockers.append(f"decision:invalid:{decision}")
            continue
        decision_id = decision.get("id", "<unknown>")
        if not decision.get("required", True):
            continue
        if decision.get("state") != "resolved":
            blockers.append(f"decision-open:{decision_id}")
            continue
        blockers.extend(
            decision_resolution_blockers(
                decision_id, decision, pr_head, ai_identities
            )
        )

    proposals = release.get("proposals") or []
    if not isinstance(proposals, list):
        blockers.append("proposals:invalid")
        proposals = []
    for proposal in proposals:
        if not isinstance(proposal, dict):
            blockers.append(f"proposal:invalid:{proposal}")
            continue
        proposal_id = proposal.get("id")
        effective = proposal.get("effective_status")
        if effective != "Accepted":
            blockers.append(f"proposal-pending:{proposal_id}:{effective}")

    if any(blocker.endswith(":head-mismatch") for blocker in blockers):
        blockers.append("pr-head:mismatch")

    unique = sorted(set(blockers))
    return {
        "ready": not unique,
        "blockers": unique,
        "ledger": ledger,
        "gaps": gaps,
        "escalations": escalations,
    }


def check_live_release(release_path: Path) -> bool:
    """Run the live release record; unknown input is unavailable and false."""
    print(f"Live release record: {release_path}")
    if not release_path.is_file():
        print(f"UNAVAILABLE release record: {release_path} is missing")
        print("Release gate: release_ready=false")
        print("Blockers:")
        print("  - release-record:unavailable:missing")
        return False
    try:
        release = json.loads(release_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"UNAVAILABLE release record: {release_path} is unusable: {error}")
        print("Release gate: release_ready=false")
        print("Blockers:")
        print("  - release-record:unavailable:unreadable")
        return False
    if not isinstance(release, dict):
        print(f"UNAVAILABLE release record: {release_path} is not a JSON object")
        print("Release gate: release_ready=false")
        print("Blockers:")
        print("  - release-record:unavailable:not-an-object")
        return False
    result = evaluate_release_gate(release)
    print(
        "Release gate: release_ready="
        + ("true" if result["ready"] else "false")
    )
    print("Blockers:")
    for blocker in result["blockers"]:
        print(f"  - {blocker}")
    print(
        "Note: synthetic all-green fixtures prove the evaluator only; they "
        "never establish real release readiness."
    )
    return bool(result["ready"])


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
    """Whether one evidence entry carries no content.

    A string entry is absent when it is empty, whitespace or a vacuous
    sentinel. A structured entry is absent when it lacks a non-empty
    ``artifact`` reference; its ``check_state`` is evaluated separately by
    ``evidence_check_states()`` so blocked evidence stays visible and open
    instead of being silently dropped as absent.
    """
    if isinstance(item, dict):
        artifact = item.get("artifact")
        return not isinstance(artifact, str) or artifact.strip() == ""
    return (
        not isinstance(item, str)
        or item.strip() == ""
        or item.strip().lower() in VACUOUS_EVIDENCE_TERMS
    )


def evidence_check_states(entry: dict[str, Any]) -> list[str]:
    """Return the ``check_state`` of every structured evidence item.

    String evidence carries no state and contributes none. A structured item
    must record ``check_state`` explicitly; an absent, blank or non-string
    state is returned as ``missing`` so the claim stays open instead of
    defaulting to green. An unknown state is returned verbatim for the same
    fail-closed reason.
    """
    states: list[str] = []
    for item in entry.get("evidence", []) or []:
        if isinstance(item, dict):
            state = item.get("check_state")
            if isinstance(state, str) and state.strip():
                states.append(state.strip())
            else:
                states.append("missing")
    return states


def evidence_supports_covered(entry: dict[str, Any]) -> bool:
    """Feedback-contract rule 2: a covered claim needs content-bearing evidence.

    ``evidence`` must be a non-empty list whose items carry content; items
    that are ``absent_evidence_entry()`` count as absent, so a list consisting
    only of vacuous sentinels (for example ``["none"]``) leaves the claim
    unsupported. Structured items must name an ``artifact``. Presence is all
    this check proves; ``evidence_check_states()`` lets reconciliation keep a
    claim open when a state other than ``passed`` is recorded.
    """
    evidence = entry.get("evidence")
    if not isinstance(evidence, list) or len(evidence) == 0:
        return False
    if not all(isinstance(item, (str, dict)) for item in evidence):
        return False
    return any(not absent_evidence_entry(item) for item in evidence)


def render_evidence_item(item: Any) -> str | None:
    """Render one evidence item for the reconciliation view.

    String entries are kept verbatim. A structured entry is rendered as
    ``<artifact> [<check_state>]`` so its artifact and check state stay visible
    in the ledger instead of being dropped by a string-only filter; an absent
    state renders as ``missing``, matching the fail-closed rule. A structured
    item without an artifact is already treated as absent and contributes
    nothing here either.
    """
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        artifact = item.get("artifact")
        if not isinstance(artifact, str) or artifact.strip() == "":
            return None
        state = item.get("check_state")
        state_text = (
            state.strip()
            if isinstance(state, str) and state.strip()
            else "missing"
        )
        return f"{artifact} [{state_text}]"
    return None


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

    # Model/provider provenance is required. ``unknown`` is the explicit way to
    # record that the identity was not available; a blank value would look like
    # provenance without being reproducible, so it is rejected.
    for field in ("model", "provider", "reviewed_artifact"):
        value = report.get(field)
        require(
            isinstance(value, str) and value.strip() != "",
            f"report {agent}: {field} must be a non-empty string; record an "
            "unknown value explicitly as 'unknown' instead of leaving it blank",
        )
    if "thinking" in report:
        thinking = report["thinking"]
        if isinstance(thinking, dict):
            require(
                bool(thinking),
                f"report {agent}: thinking must be a non-empty string or "
                "object when present",
            )
        else:
            require(
                isinstance(thinking, str) and thinking.strip() != "",
                f"report {agent}: thinking must be a non-empty string or "
                "object when present",
            )

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
            evidence = entry.get("evidence")
            if isinstance(evidence, list):
                for item in evidence:
                    if isinstance(item, dict) and absent_evidence_entry(item):
                        raise CheckError(
                            f"report {agent}: structured evidence for "
                            f"{entry['criterion_id']!r} must name a non-empty "
                            "'artifact'; a structured item without an "
                            "artifact reference carries no content"
                        )
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
        evidence = entry.get("evidence")
        if isinstance(evidence, list):
            for item in evidence:
                if not isinstance(item, dict):
                    continue
                if (
                    "criterion_id" in item
                    and item["criterion_id"] != entry["criterion_id"]
                ):
                    raise CheckError(
                        f"report {agent}: evidence for "
                        f"{entry['criterion_id']!r} names criterion_id "
                        f"{item['criterion_id']!r}; structured evidence must "
                        "agree with its coverage entry"
                    )
                if "task_id" in item and item["task_id"] != task_id:
                    raise CheckError(
                        f"report {agent}: evidence for "
                        f"{entry['criterion_id']!r} names task_id "
                        f"{item['task_id']!r}; structured evidence must agree "
                        f"with the report task {task_id!r}"
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
    criteria: list[dict[str, Any]],
    reports: list[dict[str, Any]],
    artifact: str | None = None,
) -> tuple[dict[str, dict[str, Any]], list[str], list[str]]:
    """Reconcile reports into a fail-closed coverage ledger.

    A ``covered`` claim counts only when it carries content-bearing evidence,
    every structured evidence item records ``check_state: passed``, the
    reporting agent is delegated the criterion and — when ``artifact`` names
    the current reviewed artefact — the report was produced against that same
    artefact. Contradictory supported coverage values demote the criterion to
    ``unverified`` instead of letting ``covered`` win, and ``covered`` never
    suppresses a disagreement. Every non-covered row keeps a ``follow_up``
    gap, so a criterion can only leave the gap list by being covered.
    """
    ledger: dict[str, dict[str, Any]] = {}
    gaps: list[str] = []
    for criterion in criteria:
        criterion_id = criterion["id"]
        delegated = list(criterion.get("delegated_to", []))
        entries = []
        for report in reports:
            for entry in report["acceptance_criteria_coverage"]:
                if entry["criterion_id"] == criterion_id:
                    entries.append(
                        {
                            **entry,
                            "agent": report["agent"],
                            "task_id": report["task_id"],
                            "reviewed_artifact": report.get("reviewed_artifact"),
                        }
                    )
        counted: list[dict[str, Any]] = []
        stale_agents: set[str] = set()
        wrong_agents: set[str] = set()
        bad_state_agents: dict[str, set[str]] = {}
        for entry in entries:
            states = evidence_check_states(entry)
            non_passed = sorted({state for state in states if state != "passed"})
            for state in non_passed:
                bad_state_agents.setdefault(state, set()).add(entry["agent"])
            stale = artifact is not None and entry["reviewed_artifact"] != artifact
            if stale:
                stale_agents.add(entry["agent"])
            assigned = entry["agent"] in delegated
            # A covered claim has to satisfy every identity, freshness and
            # state rule; a dropped claim stays open through follow_up.
            if entry["coverage"] == "covered":
                if (
                    not evidence_supports_covered(entry)
                    or non_passed
                    or stale
                    or not assigned
                ):
                    if not assigned:
                        wrong_agents.add(entry["agent"])
                    continue
            counted.append(entry)

        coverage_values = {entry["coverage"] for entry in counted}
        disagreement = len(coverage_values) > 1
        if disagreement:
            # Contradictory supported values are never resolved by precedence:
            # covered does not win, the row is demoted and stays open.
            status = "unverified"
        elif "covered" in coverage_values:
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
        for agent in sorted(stale_agents):
            criterion_gaps.append(f"stale_artifact:{agent}")
        for agent in sorted(wrong_agents):
            criterion_gaps.append(f"wrong_criterion_assignment:{agent}")
        for state in sorted(bad_state_agents):
            for agent in sorted(bad_state_agents[state]):
                criterion_gaps.append(f"evidence:{state}:{agent}")
        if disagreement:
            criterion_gaps.append(
                "disagreement:" + "/".join(sorted(coverage_values))
            )

        evidence: set[str] = set()
        for entry in counted:
            for item in entry.get("evidence", []):
                rendered = render_evidence_item(item)
                if rendered is not None:
                    evidence.add(rendered)
        ledger[criterion_id] = {
            "title": criterion.get("title", ""),
            "delegated_to": delegated,
            "status": status,
            "evidence": sorted(evidence),
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
        alignment = report.get("adr_alignment", {}) or {}
        for conflict in alignment.get("conflicts", []) or []:
            escalations.append(
                f"adr:{conflict.get('proposal')}:conflicts:{conflict.get('baseline')}"
            )
        for proposal in alignment.get("proposals", []) or []:
            effective = proposal.get("effective_status")
            if effective != "Accepted":
                escalations.append(f"adr:{proposal.get('id')}:pending:{effective}")
            if proposal.get("declared_status") == "Accepted" and effective != "Accepted":
                escalations.append(
                    f"adr:{proposal.get('id')}:declared-accepted-in-open-pr"
                )
        for decision in alignment.get("decision_needed", []) or []:
            if isinstance(decision, dict):
                decision_id = (
                    decision.get("id")
                    or decision.get("decision")
                    or decision.get("description")
                )
            else:
                decision_id = decision
            if isinstance(decision_id, str) and decision_id.strip():
                escalations.append(
                    f"decision:{report['agent']}:{report['task_id']}:{decision_id}"
                )
    return ledger, gaps, sorted(set(escalations))


def scenario_blockers(
    ledger: dict[str, dict[str, Any]], gaps: list[str], escalations: list[str]
) -> list[str]:
    """Derive the deterministic blocker list used by synthetic scenarios.

    Synthetic scenarios never reach the live release exit; they assert this
    derived list so an expected-false case proves the exact reason instead of
    only the final boolean.

    Divergence risk: this derivation is deliberately narrower than
    ``evaluate_release_gate()``. It names reconciled gaps, escalations and
    open criteria only; the live evaluator additionally checks the release
    record's required slots, artifact/head equality, record-declared
    ``gaps``, decisions and proposals. Do not reuse one in place of the other:
    a scenario blocker list is fixture evidence, not a release verdict.
    """
    blockers = [f"gap:{gap}" for gap in gaps]
    blockers.extend(f"escalation:{escalation}" for escalation in escalations)
    for criterion_id, entry in ledger.items():
        if entry["status"] != "covered":
            blockers.append(f"criterion-open:{criterion_id}:{entry['status']}")
    return sorted(blockers)



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
    blockers = scenario_blockers(ledger, gaps, escalations)
    if "release_ready" in expected:
        require(
            (not blockers) == expected["release_ready"],
            "release readiness mismatch: expected "
            f"{expected['release_ready']}, derived blockers {blockers}",
        )
    if "blockers" in expected:
        require(
            set(blockers) == set(expected["blockers"]),
            f"blocker set mismatch: expected {sorted(expected['blockers'])}, "
            f"got {blockers}",
        )
    for expected_blocker in expected.get("blockers_include", []):
        require(
            expected_blocker in blockers,
            f"expected blocker not found: {expected_blocker}",
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
    ledger, gaps, escalations = reconcile(
        criteria, reports, artifact=scenario.get("artifact")
    )
    if check_expectations:
        assert_scenario_expectations(scenario, ledger, gaps, escalations)
    return ledger, gaps, escalations


INVALID_REPORT_FIXTURES = FIXTURES / "workflow" / "invalid"
RELEASE_FIXTURES = FIXTURES / "workflow" / "invalid-release"

# --- Coordination and ownership (AC-PL1, AC-CX1, AC-WO1) -------------------
# The nine factors AC-PL1 weighs before detailed planning. The fixture is a
# positive control for the schema; whether a split is cohesive, right-sized or
# a scope change is material remains Planner and human judgement.
RIGHT_SIZED_FACTORS = (
    "cohesion",
    "dependencies",
    "complexity",
    "architectural_impact",
    "side_effects",
    "testability",
    "agent_context",
    "coordination_overhead",
    "ai_human_review_effort",
)
# AC-PL1 forbids rigid size thresholds. A fixture that encodes a maximum file,
# line, byte or criterion count as a rule is rejected by key name instead of
# being silently treated as sizing guidance.
RIGID_THRESHOLD_KEYS = (
    "max_files",
    "max_lines",
    "max_bytes",
    "max_criteria",
    "file_limit",
    "line_limit",
    "size_threshold",
)
RIGHT_SIZED_FIXTURE = FIXTURES / "workflow" / "planning" / "right-sized.json"

# The canonical delegation packet is docs/workflow/delegation-packet.md. The
# validator checks field presence only: concision, context sufficiency and
# actually requesting missing context are instruction and human-judgement
# rules that the offline harness cannot prove.
DELEGATION_PACKET_DOC = ROOT / "docs" / "workflow" / "delegation-packet.md"
DELEGATION_PACKET_FIXTURE = (
    FIXTURES / "workflow" / "planning" / "delegation-packet.json"
)
DELEGATION_PACKET_DOC_MARKERS = (
    "**Task identity**",
    "**Criteria**",
    "**ADR baseline and proposals**",
    "**Repository context**",
    "**Dependencies**",
    "**Constraints**",
    "**Expected evidence**",
    "**Reviewed artifact**",
    "**Write ownership**",
)
# The pre-canonical list that used to live in the workflow document. A section
# that repeats these bullets duplicates the normative rules instead of linking
# to them.
DELEGATION_WORKFLOW_DUPLICATED_RULES = (
    "- issue number, title and acceptance criteria relevant to the task",
    "- the accepted ADR baseline and any proposal relevant to the task",
    "- affected files or areas and repository constraints",
    "- expected evidence, checks and report format",
    "- adjacent responsibilities and the agent that owns them",
    "- known dependencies, assumptions and deferred scope",
)

# Write ownership. The single writer is recorded per task; read-only roles
# claim no write scope and the ledger, ADR and Git/GitHub writers keep their
# own domains. Overlapping active scopes are serialised, never merged.
WORKFLOW_AGENTS = frozenset(REQUIRED_AGENTS)
OWNERSHIP_FIXTURES = FIXTURES / "workflow" / "ownership"
OWNERSHIP_STATUSES = frozenset({"active", "handed-over", "closed"})
READ_ONLY_WRITE_AGENTS = frozenset({"reviewer", "tester"})
ROLE_WRITE_PREFIXES = {
    "orchestrator": ("docs/workflow/ledgers/",),
    "planner": ("docs/adr/",),
}
# Paths that the Implementer must never claim: the ledger belongs to the
# Orchestrator and ADR proposals belong to the Planner.
IMPLEMENTER_EXCLUDED_PREFIXES = ("docs/workflow/ledgers/", "docs/adr/")


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
    ledger, gaps, escalations = reconcile(
        criteria, reports, artifact=scenario.get("artifact")
    )
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
    contradictory coverage values demote the row to ``unverified`` instead of
    letting ``covered`` win, structured evidence that names a different
    criterion or task is rejected, self-supersession is rejected and a cyclic
    ``supersedes`` chain is rejected instead of silently dropping both
    reports.
    """
    criteria = [
        {
            "id": "AC-01",
            "title": "In-memory reconciliation guard",
            "delegated_to": ["implementer", "reviewer"],
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

    structured = report(
        "implementer",
        "issue-30-support",
        "Completed",
        [
            {
                "criterion_id": "AC-01",
                "coverage": "covered",
                "evidence": [
                    {
                        "artifact": "docs/x.md",
                        "check_state": "passed",
                    }
                ],
            }
        ],
    )
    ledger, _, _ = reconcile(criteria, [structured])
    require(
        ledger["AC-01"]["status"] == "covered",
        "structured evidence that names an artifact and records "
        f"check_state 'passed' must stay green: got {ledger['AC-01']['status']}",
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
        ledger["AC-01"]["status"] == "unverified",
        "contradictory coverage values must demote the criterion to "
        f"unverified instead of letting covered win: got "
        f"{ledger['AC-01']['status']}",
    )
    require(
        "AC-01:disagreement:covered/unverified" in gaps,
        "contradictory coverage values must surface as a disagreement gap: "
        f"gaps are {gaps}",
    )
    require(
        "follow_up:AC-01" in gaps,
        "a demoted disagreement must stay open with the follow_up gap: "
        f"gaps are {gaps}",
    )

    def full_report(supersedes: list[str], task_id: str = "issue-30-a") -> dict[str, Any]:
        base = report("tester", task_id, "Completed", [])
        base.update(
            {
                "model": "synthetic-model",
                "provider": "synthetic-provider",
                "reviewed_artifact": "1" * 40,
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
    criterion_mismatch = full_report([])
    criterion_mismatch["acceptance_criteria_coverage"] = [
        {
            "criterion_id": "AC-01",
            "coverage": "covered",
            "evidence": [
                {
                    "artifact": "docs/x.md",
                    "check_state": "passed",
                    "criterion_id": "AC-02",
                }
            ],
        }
    ]
    expect_error(
        "evidence criterion mismatch",
        lambda: validate_report(criterion_mismatch, scenario),
        "must agree with its coverage entry",
    )
    task_mismatch = full_report([])
    task_mismatch["acceptance_criteria_coverage"] = [
        {
            "criterion_id": "AC-01",
            "coverage": "covered",
            "evidence": [
                {
                    "artifact": "docs/x.md",
                    "check_state": "passed",
                    "task_id": "issue-30-b",
                }
            ],
        }
    ]
    expect_error(
        "evidence task mismatch",
        lambda: validate_report(task_mismatch, scenario),
        "must agree with the report task",
    )
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
    # AC-PV1: an explicit ``unknown`` sentinel is valid provenance; a blank
    # value is not. The truth of the identity and the absence of reasoning
    # traces stay reviewer-inspected limits.
    unknown = full_report([], task_id="issue-30-a")
    unknown["model"] = "unknown"
    unknown["provider"] = "unknown"
    require(
        validate_report(unknown, scenario) is None,
        "an explicit 'unknown' model/provider sentinel must validate",
    )
    expect_error(
        "blank model provenance",
        lambda: validate_report({**unknown, "model": "   "}, scenario),
        "model must be a non-empty string",
    )
    print(
        "PASS reports in-memory fixtures: empty and sentinel-evidence covered "
        "claims stay unsupported, structured evidence identity is enforced, "
        "contradictory coverage values demote to unverified, unknown "
        "provenance is accepted while blank provenance is rejected, and "
        "self-, cross-agent, unknown and cyclic supersession is rejected"
    )


def check_release_gate_in_memory_fixture() -> None:
    """Prove the named release-gate guards with in-memory mutations.

    The synthetic all-green control proves the evaluator only; it is never
    live release evidence. Each case starts from that control, applies one
    mutation and asserts both the false verdict and the named blocker(s), so a
    removed guard flips the case to passing and fails this fixture. The guards
    proven here are named in the summary line and listed in
    ``docs/validation/README.md``; the same document lists the branches that
    were reviewed but are not mutation-proven, and that list is not claimed to
    be exhaustive.
    """
    control = evaluate_release_gate(synthetic_release())
    require(
        control["ready"] and not control["blockers"],
        "the synthetic all-green control must evaluate to true without "
        f"blockers, got {control['blockers']}",
    )
    proven = 0

    def case(label: str, mutate: Any, *blockers: str) -> None:
        nonlocal proven
        proven += 1
        release = json.loads(json.dumps(synthetic_release()))
        mutate(release)
        result = evaluate_release_gate(release)
        require(not result["ready"], f"{label}: expected release_ready false")
        for blocker in blockers:
            require(
                blocker in result["blockers"],
                f"{label}: expected blocker {blocker!r}, got {result['blockers']}",
            )

    def set_path(path: tuple[str, ...], value: Any) -> Any:
        def mutate(release: dict[str, Any]) -> None:
            target: Any = release
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value

        return mutate

    case(
        "plan review missing",
        lambda r: r.pop("plan_review"),
        "plan_review:missing",
    )
    case(
        "plan review skipped",
        set_path(("plan_review", "state"), "skipped"),
        "plan_review:skipped",
    )
    case(
        "plan review commit mismatch",
        set_path(("plan_review", "commit"), "0" * 40),
        "plan_review:commit-mismatch",
    )
    case(
        "plan review hash mismatch",
        set_path(("plan_review", "section_sha256"), "0" * 64),
        "plan_review:hash-mismatch",
    )
    case(
        "AI review missing",
        lambda r: r.pop("ai_code_review"),
        "ai_code_review:missing",
    )
    case(
        "AI review not AI",
        set_path(("ai_code_review", "reviewer_type"), "human"),
        "ai_code_review:not-ai",
    )
    case(
        "AI review head mismatch",
        set_path(("ai_code_review", "head"), "9" * 40),
        "ai_code_review:head-mismatch",
    )
    case(
        "human review missing",
        lambda r: r.pop("human_review"),
        "human_review:missing",
    )
    case(
        "human identity reuse",
        lambda r: r["human_review"].update(
            {"name": "reviewer", "login": "rev-reviewer"}
        ),
        "human_review:ai-identity",
    )
    case(
        "human provenance missing",
        lambda r: r["human_review"].pop("provenance"),
        "human_review:missing-provenance",
    )
    case(
        "human attribution missing",
        lambda r: r["human_review"].pop("attribution"),
        "human_review:missing-attribution",
    )
    case(
        "human independence missing",
        set_path(("human_review", "independent"), False),
        "human_review:not-independent",
    )
    case(
        "human timestamp missing",
        set_path(("human_review", "timestamp"), ""),
        "human_review:missing-timestamp",
    )
    case(
        "human head mismatch",
        set_path(("human_review", "head"), "9" * 40),
        "human_review:head-mismatch",
    )
    case(
        "tester verification missing",
        lambda r: r.pop("tester_verification"),
        "tester_verification:missing",
    )
    case(
        "tester verification skipped",
        set_path(("tester_verification", "state"), "skipped"),
        "tester_verification:skipped",
    )
    case(
        "tester verification unavailable",
        set_path(("tester_verification", "state"), "unavailable"),
        "tester_verification:unavailable",
    )
    case(
        "tester head mismatch",
        set_path(("tester_verification", "head"), "9" * 40),
        "tester_verification:head-mismatch",
    )
    case(
        "CI head mismatch",
        set_path(("workflow_validator_ci", "head"), "9" * 40),
        "workflow_validator_ci:head-mismatch",
    )
    case(
        "contributor-reported CI",
        set_path(("workflow_validator_ci", "state"), "contributor-reported"),
        "workflow_validator_ci:contributor-reported",
    )
    case(
        "uninspected CI",
        set_path(("workflow_validator_ci", "inspected"), False),
        "workflow_validator_ci:not-inspected",
    )
    case(
        "CI base missing",
        set_path(("workflow_validator_ci", "base_sha"), ""),
        "workflow_validator_ci:missing-base",
    )
    case(
        "CI job missing",
        set_path(("workflow_validator_ci", "job"), ""),
        "workflow_validator_ci:missing-job",
    )
    case(
        "CI run missing",
        set_path(("workflow_validator_ci", "run"), ""),
        "workflow_validator_ci:missing-run",
    )
    case(
        "CI continue-on-error",
        set_path(("workflow_validator_ci", "continue_on_error"), True),
        "workflow_validator_ci:continue-on-error",
    )
    case(
        "CI base short",
        set_path(("workflow_validator_ci", "base_sha"), "12345"),
        "workflow_validator_ci:invalid-base",
    )
    case(
        "CI base non-hex",
        set_path(("workflow_validator_ci", "base_sha"), "x"),
        "workflow_validator_ci:invalid-base",
    )
    case(
        "CI slot missing",
        lambda r: r.pop("workflow_validator_ci"),
        "workflow_validator_ci:missing",
    )
    case(
        "plan review invalid state",
        set_path(("plan_review", "state"), "unknown"),
        "plan_review:invalid-state:unknown",
    )
    case(
        "AI review invalid state",
        set_path(("ai_code_review", "state"), "unknown"),
        "ai_code_review:invalid-state:unknown",
    )
    case(
        "human review invalid state",
        set_path(("human_review", "state"), "unknown"),
        "human_review:invalid-state:unknown",
    )
    case(
        "tester verification invalid state",
        set_path(("tester_verification", "state"), "unknown"),
        "tester_verification:invalid-state:unknown",
    )
    case(
        "CI invalid state",
        set_path(("workflow_validator_ci", "state"), "unknown"),
        "workflow_validator_ci:invalid-state:unknown",
    )
    case(
        "record artifact missing",
        lambda r: r.pop("artifact"),
        "artifact:missing",
    )
    case(
        "record artifact mismatch",
        lambda r: (
            r.update({"artifact": "9" * 40}),
            [
                report.update({"reviewed_artifact": "9" * 40})
                for report in r["reports"]
            ],
        ),
        "artifact:head-mismatch",
    )
    case(
        "PR head is not a commit",
        set_path(("pr_head",), "not-a-commit"),
        "pr_head:invalid",
    )
    case(
        "record artifact is not a commit",
        set_path(("artifact",), "not-a-commit"),
        "artifact:invalid",
    )
    case(
        "relabelled frozen diff",
        lambda r: (
            r.update({"pr_head": "a" * 64, "artifact": "a" * 64}),
            [
                report.update({"reviewed_artifact": "a" * 64})
                for report in r["reports"]
            ],
            r["ai_code_review"].update({"head": "a" * 64}),
            r["human_review"].update({"head": "a" * 64}),
            r["tester_verification"].update({"head": "a" * 64}),
            r["workflow_validator_ci"].update({"head": "a" * 64}),
        ),
        "pr_head:invalid",
        "artifact:invalid",
    )
    case(
        "unknown record key",
        lambda r: r.update({"frozen_diff": "a" * 64}),
        "release-record:unknown-key:frozen_diff",
    )
    case(
        "human name equals login",
        lambda r: r["human_review"].update(
            {"name": "ada-lovelace", "login": "ada-lovelace"}
        ),
        "human_review:name-equals-login",
    )
    case(
        "human login reuses AI reviewer identity",
        lambda r: (
            r["ai_code_review"].update({"reviewer": "deepseek-v4.1-flash"}),
            r["human_review"].update({"login": "deepseek-v4.1-flash"}),
        ),
        "human_review:ai-identity",
    )
    case(
        "criterion uncovered",
        set_path(
            ("reports", 1, "acceptance_criteria_coverage", 0, "coverage"),
            "unverified",
        ),
        "criterion-open:AC-02:unverified",
        "gap:follow_up:AC-02",
        "gaps:present",
    )
    case(
        "record-declared gap",
        lambda r: r.update({"gaps": ["synthetic-gap"]}),
        "release-gap:synthetic-gap",
    )
    case(
        "stale evidence",
        set_path(("reports", 0, "reviewed_artifact"), "9" * 40),
        "stale-artifact:present",
    )
    case(
        "contradictory coverage",
        lambda r: r["reports"][1]["acceptance_criteria_coverage"].append(
            {
                "criterion_id": "AC-02",
                "coverage": "unverified",
                "evidence": ["docs/x.md"],
            }
        ),
        "disagreement:present",
        "gap:AC-02:disagreement:covered/unverified",
    )
    case(
        "report decision needed",
        lambda r: r["reports"][0]["adr_alignment"]["decision_needed"].append(
            "Approve the synthetic decision"
        ),
        "decision_needed:present",
        "escalation:decision:implementer:t-release-impl:Approve the synthetic decision",
    )
    case(
        "report pending proposal",
        lambda r: r["reports"][0]["adr_alignment"]["proposals"].append(
            {
                "id": "ADR-0002",
                "declared_status": "Proposed",
                "effective_status": "Proposed",
            }
        ),
        "pending-proposal:present",
    )
    case(
        "release pending proposal",
        lambda r: r.update(
            {"proposals": [{"id": "ADR-0002", "effective_status": "Proposed"}]}
        ),
        "proposal-pending:ADR-0002:Proposed",
    )
    case(
        "open required decision",
        lambda r: r.update(
            {"decisions": [{"id": "OD-ROLE", "required": True, "state": "open"}]}
        ),
        "decision-open:OD-ROLE",
    )
    case(
        "decision resolution by AI identity",
        lambda r: r.update(
            {
                "decisions": [
                    {
                        "id": "OD-ROLE",
                        "required": True,
                        "state": "resolved",
                        "resolved_by": "orchestrator",
                        "rationale": "Synthetic rationale.",
                        "reference": "synthetic-reference",
                        "head": r["pr_head"],
                    }
                ]
            }
        ),
        "decision-resolution:OD-ROLE:identity",
    )
    case(
        "decision resolution by recorded AI identity",
        lambda r: (
            r["ai_code_review"].update({"model": "deepseek-v4.1-flash"}),
            r.update(
                {
                    "decisions": [
                        {
                            "id": "OD-ROLE",
                            "required": True,
                            "state": "resolved",
                            "resolved_by": "deepseek-v4.1-flash",
                            "rationale": "Synthetic rationale.",
                            "reference": "synthetic-reference",
                            "head": r["pr_head"],
                        }
                    ]
                }
            ),
        ),
        "decision-resolution:OD-ROLE:identity",
    )
    case(
        "PR head mismatch",
        set_path(("pr_head",), "9" * 40),
        "pr-head:mismatch",
    )
    print(
        "PASS release gate in-memory fixtures: the synthetic all-green "
        f"control evaluates true and {proven} mutations each force false with "
        "their named blocker; this proves the evaluator only, never real "
        "release readiness"
    )


def check_release_fixtures() -> None:
    """Run the file fixtures for expected-false release records.

    Every case patches the in-memory all-green control and asserts the exact
    verdict plus named blockers. These expected-false cases stay inside the
    fixture harness and never invoke the live release exit.
    """
    require(
        RELEASE_FIXTURES.is_dir(),
        f"missing release fixture directory: {RELEASE_FIXTURES}",
    )
    cases = sorted(path for path in RELEASE_FIXTURES.iterdir() if path.is_dir())
    require(bool(cases), "at least one release fixture case is required")
    for case_dir in cases:
        label = case_dir.name
        scenario_path = case_dir / "scenario.json"
        require(
            scenario_path.is_file(),
            f"release fixture {label}: scenario.json is required",
        )
        scenario = json.loads(scenario_path.read_text(encoding="utf-8"))
        release = json.loads(json.dumps(synthetic_release()))
        deep_merge(release, scenario.get("release_patch", {}))
        for key in scenario.get("release_remove", []):
            parts = key.split(".")
            target: Any = release
            for part in parts[:-1]:
                target = target.get(part) if isinstance(target, dict) else None
            if isinstance(target, dict):
                target.pop(parts[-1], None)
        result = evaluate_release_gate(release)
        expected = scenario["expected"]
        require(
            result["ready"] == expected["release_ready"],
            f"release fixture {label}: expected release_ready "
            f"{expected['release_ready']}, got {result['ready']} with "
            f"blockers {result['blockers']}",
        )
        if "blockers" in expected:
            require(
                set(result["blockers"]) == set(expected["blockers"]),
                f"release fixture {label}: blocker set mismatch: expected "
                f"{sorted(expected['blockers'])}, got {result['blockers']}",
            )
        for blocker in expected.get("blockers_include", []):
            require(
                blocker in result["blockers"],
                f"release fixture {label}: expected blocker not found: "
                f"{blocker}; got {result['blockers']}",
            )
        print(
            f"release fixture {label}: release_ready=false with the stated "
            "blockers"
        )
    print(
        f"PASS release negative fixtures: {len(cases)} expected-false release "
        "cases assert the exact blockers inside the fixture harness"
    )


def _non_empty_string(value: Any) -> bool:
    """Whether a value is a string with at least one non-whitespace character."""
    return isinstance(value, str) and bool(value.strip())


def _markdown_section(text: str, heading: str) -> str:
    """Return the body of one level-two Markdown section, heading excluded.

    Returns an empty string when the heading is absent, so a caller can turn
    that into a named blocker instead of raising from a validation helper.
    """
    pattern = re.compile(r"^" + re.escape(heading) + r"$", re.MULTILINE)
    match = pattern.search(text)
    if match is None:
        return ""
    start = match.end()
    tail = text[start:]
    next_heading = re.compile(r"^## ", re.MULTILINE).search(tail)
    return text[start : start + (next_heading.start() if next_heading else len(tail))]


def validate_right_sized_work_item(work_item: dict[str, Any]) -> list[str]:
    """Return the sorted AC-PL1 blockers for one work-item sizing record.

    The record proves the schema only: all nine factors, an independently
    verifiable outcome and a named-human approval for a material scope change
    are required, and no numeric size threshold is accepted as a rule. Whether
    a split is cohesive, right-sized or genuinely material remains Planner and
    human judgement.
    """
    blockers: list[str] = []
    if not isinstance(work_item, dict):
        return ["right-sized:invalid:record"]
    for key in RIGID_THRESHOLD_KEYS:
        if key in work_item:
            blockers.append(f"right-sized:rigid-threshold:{key}")
    factors = work_item.get("factors")
    if not isinstance(factors, dict):
        blockers.append("right-sized:missing:factors")
    else:
        for factor in RIGHT_SIZED_FACTORS:
            if not _non_empty_string(factors.get(factor)):
                blockers.append(f"right-sized:missing-factor:{factor}")
    if not _non_empty_string(work_item.get("outcome")):
        blockers.append("right-sized:missing:outcome")
    if work_item.get("independently_verifiable") is not True:
        blockers.append("right-sized:not-independently-verifiable")
    scope_change = work_item.get("scope_change")
    if not isinstance(scope_change, dict):
        blockers.append("right-sized:missing:scope_change")
    elif scope_change.get("material") is True:
        approval = scope_change.get("approval")
        if not isinstance(approval, dict):
            blockers.append("right-sized:missing:approval")
        else:
            if approval.get("required") is not True:
                blockers.append("right-sized:approval-not-required")
            if approval.get("approved_by") != "human":
                blockers.append("right-sized:approval-not-human")
            if not _non_empty_string(approval.get("reference")):
                blockers.append("right-sized:missing:approval-reference")
    return sorted(set(blockers))


def check_right_sized_work_item_fixture() -> None:
    """Prove the AC-PL1 work-item schema with in-memory mutations.

    The positive control carries all nine factors, an independently verifiable
    outcome and a named-human approval for a material scope change. Each
    mutation removes or corrupts exactly one requirement, so removing the
    matching guard makes its case pass. No case encodes a file, line or
    criterion count as a rule.
    """
    fixture = json.loads(RIGHT_SIZED_FIXTURE.read_text(encoding="utf-8"))
    control = fixture.get("work_item", fixture)
    require(
        not validate_right_sized_work_item(control),
        "right-sized positive control must pass, got "
        f"{validate_right_sized_work_item(control)}",
    )
    mutations = 0

    def case(label: str, mutate: Any, *expected: str) -> None:
        nonlocal mutations
        mutations += 1
        work_item = json.loads(json.dumps(control))
        mutate(work_item)
        found = validate_right_sized_work_item(work_item)
        require(bool(found), f"{label}: expected at least one blocker")
        for blocker in expected:
            require(
                blocker in found,
                f"{label}: expected blocker {blocker!r}, got {found}",
            )

    for factor in RIGHT_SIZED_FACTORS:
        case(
            f"factor removed: {factor}",
            lambda work_item, factor=factor: work_item["factors"].pop(factor),
            f"right-sized:missing-factor:{factor}",
        )
    case(
        "factor blank",
        lambda work_item: work_item["factors"].update({"cohesion": ""}),
        "right-sized:missing-factor:cohesion",
    )
    case(
        "independent verification removed",
        lambda work_item: work_item.pop("independently_verifiable"),
        "right-sized:not-independently-verifiable",
    )
    case(
        "independent verification false",
        lambda work_item: work_item.update({"independently_verifiable": False}),
        "right-sized:not-independently-verifiable",
    )
    case(
        "outcome removed",
        lambda work_item: work_item.pop("outcome"),
        "right-sized:missing:outcome",
    )
    case(
        "scope change removed",
        lambda work_item: work_item.pop("scope_change"),
        "right-sized:missing:scope_change",
    )
    case(
        "approval removed",
        lambda work_item: work_item["scope_change"].pop("approval"),
        "right-sized:missing:approval",
    )
    case(
        "approval identity removed",
        lambda work_item: work_item["scope_change"]["approval"].pop("approved_by"),
        "right-sized:approval-not-human",
    )
    case(
        "approval not human",
        lambda work_item: work_item["scope_change"]["approval"].update(
            {"approved_by": "orchestrator"}
        ),
        "right-sized:approval-not-human",
    )
    case(
        "approval reference removed",
        lambda work_item: work_item["scope_change"]["approval"].pop("reference"),
        "right-sized:missing:approval-reference",
    )
    case(
        "rigid file threshold",
        lambda work_item: work_item.update({"max_files": 3}),
        "right-sized:rigid-threshold:max_files",
    )
    case(
        "rigid line threshold",
        lambda work_item: work_item.update({"max_lines": 200}),
        "right-sized:rigid-threshold:max_lines",
    )
    print(
        "PASS right-sized work item fixture: nine factors, an independently "
        f"verifiable outcome and named-human approval for material scope "
        f"changes are required; {mutations} mutations each fail their case and "
        "no rigid size threshold is encoded"
    )


def validate_delegation_packet_links(
    workflow_text: str, agents_text: str, doc_text: str
) -> list[str]:
    """Check that the canonical packet document is linked, not duplicated.

    The canonical document must carry every required-field marker. The
    workflow section named ``## Delegation packet`` must link to it without
    repeating the pre-canonical bullet list, and ``AGENTS.md`` must link to it
    as well. Context sufficiency and concision are not checked here: they are
    instruction and human-judgement rules.
    """
    blockers: list[str] = []
    for marker in DELEGATION_PACKET_DOC_MARKERS:
        if marker not in doc_text:
            blockers.append(f"delegation-packet:doc-marker:{marker}")
    section = _markdown_section(workflow_text, "## Delegation packet")
    if "delegation-packet.md" not in section:
        blockers.append("delegation-packet:workflow-link-missing")
    for duplicated in DELEGATION_WORKFLOW_DUPLICATED_RULES:
        if duplicated in section:
            blockers.append(f"delegation-packet:workflow-duplicates-rule:{duplicated}")
    if "delegation-packet.md" not in agents_text:
        blockers.append("delegation-packet:agents-link-missing")
    return sorted(set(blockers))


def validate_delegation_packet(packet: dict[str, Any]) -> list[str]:
    """Return the sorted AC-CX1 blockers for one delegation packet.

    Required fields are task identity, issue and target agent, the delegated
    criteria, the accepted ADR baseline and proposals, repository context,
    dependencies, constraints, expected evidence, the reviewed artifact and
    write ownership. The write-ownership record is run through the ownership
    guard, so a packet cannot delegate a write that the target role may not
    perform. Field presence is all the offline validator can check; concise
    and sufficient context and an actual request for missing context remain
    instruction and human-judgement rules.
    """
    blockers: list[str] = []
    if not isinstance(packet, dict):
        return ["packet:invalid:record"]
    if not _non_empty_string(packet.get("task_id")):
        blockers.append("packet:missing:task_id")
    issue = packet.get("issue")
    if not isinstance(issue, int) or isinstance(issue, bool):
        blockers.append("packet:missing:issue")
    agent = packet.get("agent")
    if not _non_empty_string(agent):
        blockers.append("packet:missing:agent")
    elif agent not in WORKFLOW_AGENTS:
        blockers.append(f"packet:unknown-agent:{agent}")
    criteria = packet.get("criteria")
    if not isinstance(criteria, list) or not criteria:
        blockers.append("packet:missing:criteria")
    else:
        for index, criterion in enumerate(criteria):
            if isinstance(criterion, str):
                if not _non_empty_string(criterion):
                    blockers.append(f"packet:invalid:criterion:{index}")
            elif not isinstance(criterion, dict) or not _non_empty_string(
                criterion.get("id")
            ):
                blockers.append(f"packet:invalid:criterion:{index}")
    baseline = packet.get("adr_baseline")
    if not isinstance(baseline, dict):
        blockers.append("packet:missing:adr_baseline")
    else:
        for key in ("accepted", "proposals"):
            if not isinstance(baseline.get(key), list):
                blockers.append(f"packet:missing:adr_baseline.{key}")
    for field in ("repository_context", "constraints", "expected_evidence"):
        value = packet.get(field)
        if not isinstance(value, list) or not value:
            blockers.append(f"packet:missing:{field}")
    if not isinstance(packet.get("dependencies"), list):
        blockers.append("packet:missing:dependencies")
    if not _non_empty_string(packet.get("reviewed_artifact")):
        blockers.append("packet:missing:reviewed_artifact")
    ownership = packet.get("write_ownership")
    if not isinstance(ownership, dict):
        blockers.append("packet:missing:write_ownership")
    else:
        if ownership.get("agent") != agent:
            blockers.append("packet:write-ownership:agent-mismatch")
        if ownership.get("task_id") != packet.get("task_id"):
            blockers.append("packet:write-ownership:task-mismatch")
        blockers.extend(
            validate_write_ownership(
                {
                    "active_tasks": [packet.get("task_id")],
                    "records": [ownership],
                }
            )
        )
    return sorted(set(blockers))


def check_delegation_packet_fixture() -> None:
    """Prove the canonical packet fields and links with named mutations.

    Each mutation omits or corrupts one required field, removes the workflow or
    ``AGENTS.md`` link, or re-adds a duplicated rule to the workflow section;
    the matching blocker must appear. Concision and context sufficiency are
    explicitly not proven here.
    """
    require(
        DELEGATION_PACKET_DOC.is_file(),
        f"missing canonical delegation packet: {DELEGATION_PACKET_DOC}",
    )
    doc_text = DELEGATION_PACKET_DOC.read_text(encoding="utf-8")
    workflow_path = ROOT / "docs" / "workflow" / "development-workflow.md"
    workflow_text = workflow_path.read_text(encoding="utf-8")
    agents_path = ROOT / "AGENTS.md"
    agents_text = agents_path.read_text(encoding="utf-8")
    links = validate_delegation_packet_links(workflow_text, agents_text, doc_text)
    require(not links, f"delegation packet documents must pass, got {links}")
    fixture = json.loads(DELEGATION_PACKET_FIXTURE.read_text(encoding="utf-8"))
    control = fixture.get("packet", fixture)
    require(
        not validate_delegation_packet(control),
        "delegation packet positive control must pass, got "
        f"{validate_delegation_packet(control)}",
    )
    mutations = 0

    def case(label: str, mutate: Any, *expected: str) -> None:
        nonlocal mutations
        mutations += 1
        packet = json.loads(json.dumps(control))
        mutate(packet)
        found = validate_delegation_packet(packet)
        require(bool(found), f"{label}: expected at least one blocker")
        for blocker in expected:
            require(
                blocker in found,
                f"{label}: expected blocker {blocker!r}, got {found}",
            )

    for field in (
        "task_id",
        "issue",
        "agent",
        "criteria",
        "adr_baseline",
        "repository_context",
        "dependencies",
        "constraints",
        "expected_evidence",
        "reviewed_artifact",
        "write_ownership",
    ):
        case(
            f"field removed: {field}",
            lambda packet, field=field: packet.pop(field),
            f"packet:missing:{field}",
        )
    case(
        "criteria empty",
        lambda packet: packet.update({"criteria": []}),
        "packet:missing:criteria",
    )
    case(
        "criterion without id",
        lambda packet: packet["criteria"].append({"title": "no id"}),
        "packet:invalid:criterion:3",
    )
    case(
        "ADR baseline accepted removed",
        lambda packet: packet["adr_baseline"].pop("accepted"),
        "packet:missing:adr_baseline.accepted",
    )
    case(
        "ADR baseline proposals removed",
        lambda packet: packet["adr_baseline"].pop("proposals"),
        "packet:missing:adr_baseline.proposals",
    )
    case(
        "reviewed artifact blank",
        lambda packet: packet.update({"reviewed_artifact": "  "}),
        "packet:missing:reviewed_artifact",
    )
    case(
        "write ownership agent mismatch",
        lambda packet: packet["write_ownership"].update({"agent": "reviewer"}),
        "packet:write-ownership:agent-mismatch",
    )
    case(
        "write ownership task mismatch",
        lambda packet: packet["write_ownership"].update({"task_id": "other-task"}),
        "packet:write-ownership:task-mismatch",
    )
    case(
        "read-only target claims a write",
        lambda packet: (
            packet.update({"agent": "reviewer"}),
            packet["write_ownership"].update(
                {
                    "agent": "reviewer",
                    "write_scope": ["docs/workflow/development-workflow.md"],
                }
            ),
        ),
        "write-ownership:read-only:reviewer:docs/workflow/development-workflow.md",
    )
    link_mutations = 0

    def link_case(label: str, workflow: str, agents: str, doc: str, expected: str) -> None:
        nonlocal link_mutations
        link_mutations += 1
        found = validate_delegation_packet_links(workflow, agents, doc)
        require(
            expected in found,
            f"{label}: expected blocker {expected!r}, got {found}",
        )

    link_case(
        "workflow link removed",
        workflow_text.replace("delegation-packet.md", "packet.md"),
        agents_text,
        doc_text,
        "delegation-packet:workflow-link-missing",
    )
    link_case(
        "AGENTS link removed",
        workflow_text,
        agents_text.replace("delegation-packet.md", "packet.md"),
        doc_text,
        "delegation-packet:agents-link-missing",
    )
    link_case(
        "canonical field marker removed",
        workflow_text,
        agents_text,
        doc_text.replace("**Write ownership**", "**Writes**"),
        "delegation-packet:doc-marker:**Write ownership**",
    )
    duplicated = (
        _markdown_section(workflow_text, "## Delegation packet")
        + "\n- the accepted ADR baseline and any proposal relevant to the task\n"
    )
    duplicated_workflow = workflow_text.replace(
        _markdown_section(workflow_text, "## Delegation packet"), duplicated
    )
    link_case(
        "workflow duplicates a rule",
        duplicated_workflow,
        agents_text,
        doc_text,
        "delegation-packet:workflow-duplicates-rule:"
        "- the accepted ADR baseline and any proposal relevant to the task",
    )
    print(
        "PASS delegation packet fixture: the canonical document carries every "
        f"required field, the workflow and AGENTS.md link to it, and "
        f"{mutations + link_mutations} mutations each fail their case; "
        "concision and context sufficiency remain human judgement"
    )


def _paths_overlap(left: str, right: str) -> bool:
    """Whether two write scopes name the same file or a directory prefix of it."""
    if left == right:
        return True
    if left.endswith("/") and right.startswith(left):
        return True
    if right.endswith("/") and left.startswith(right):
        return True
    return False


def _record_scope(record: dict[str, Any]) -> list[str]:
    """Effective write scope of one record: declared paths plus its scratch dir."""
    scope: list[str] = []
    declared = record.get("write_scope")
    if isinstance(declared, list):
        scope.extend(path for path in declared if _non_empty_string(path))
    scratch = record.get("scratch")
    if isinstance(scratch, str) and scratch:
        scope.append(scratch)
    return scope


def validate_write_ownership(ownership: dict[str, Any]) -> list[str]:
    """Return the sorted AC-WO1 blockers for one ownership record set.

    The check enforces the recorded single-writer protocol: every active task
    is in the active list (a stale active task is a blocker), a handed-over
    task names an active successor, overlaps between active write scopes are
    reported, scratch lives under ``.tmp/<task-id>/``, and role scopes hold:
    the Orchestrator writes only the ledger, the Planner only ADR proposals,
    the Implementer not those two, the Reviewer and Tester nothing and the Git
    Manager no repository file. Actual write obedience and filesystem
    isolation are instruction-only limits; this checks the records only.
    """
    blockers: list[str] = []
    if not isinstance(ownership, dict):
        return ["write-ownership:invalid:record"]
    active_tasks = ownership.get("active_tasks")
    if not isinstance(active_tasks, list) or not all(
        _non_empty_string(task) for task in active_tasks
    ):
        return ["write-ownership:invalid:active-tasks"]
    records = ownership.get("records")
    if not isinstance(records, list) or not records:
        return ["write-ownership:missing:records"]
    active_set = set(active_tasks)
    by_task: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            blockers.append(f"write-ownership:invalid:record:{index}")
        elif _non_empty_string(record.get("task_id")):
            by_task[record["task_id"]] = record
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        task_id = record.get("task_id")
        agent = record.get("agent")
        status = record.get("status")
        if not _non_empty_string(task_id):
            blockers.append(f"write-ownership:missing:task:{index}")
            continue
        if not _non_empty_string(agent):
            blockers.append(f"write-ownership:missing:agent:{task_id}")
        elif agent not in WORKFLOW_AGENTS:
            blockers.append(f"write-ownership:unknown-agent:{agent}")
        if status not in OWNERSHIP_STATUSES:
            blockers.append(f"write-ownership:invalid-status:{task_id}:{status}")
        scope = record.get("write_scope")
        if not isinstance(scope, list):
            blockers.append(f"write-ownership:invalid-scope:{task_id}")
            scope = []
        for path in scope:
            if not _non_empty_string(path):
                blockers.append(f"write-ownership:invalid-scope:{task_id}")
                continue
            if agent in READ_ONLY_WRITE_AGENTS:
                blockers.append(f"write-ownership:read-only:{agent}:{path}")
            elif agent in ROLE_WRITE_PREFIXES:
                if not any(
                    path.startswith(prefix) for prefix in ROLE_WRITE_PREFIXES[agent]
                ):
                    blockers.append(f"write-ownership:role-scope:{agent}:{path}")
            elif agent == "git-manager":
                blockers.append(f"write-ownership:role-scope:{agent}:{path}")
            elif agent == "implementer" and path.startswith(
                IMPLEMENTER_EXCLUDED_PREFIXES
            ):
                blockers.append(f"write-ownership:role-scope:{agent}:{path}")
        scratch = record.get("scratch")
        if scratch is not None:
            if not _non_empty_string(scratch):
                blockers.append(f"write-ownership:invalid-scratch:{task_id}")
            elif not scratch.startswith(f".tmp/{task_id}/"):
                blockers.append(f"write-ownership:scratch:{task_id}:{scratch}")
        for path in scope:
            if (
                _non_empty_string(path)
                and path.startswith(".tmp/")
                and not path.startswith(f".tmp/{task_id}/")
            ):
                blockers.append(f"write-ownership:scratch:{task_id}:{path}")
        if not isinstance(record.get("dependencies"), list):
            blockers.append(f"write-ownership:missing:dependencies:{task_id}")
        if status == "active" and task_id not in active_set:
            blockers.append(f"write-ownership:stale:{task_id}")
        if status == "handed-over":
            handover = record.get("handover")
            if not isinstance(handover, dict) or not _non_empty_string(
                handover.get("to")
            ):
                blockers.append(f"write-ownership:missing-handover:{task_id}")
            else:
                target = handover["to"]
                target_record = by_task.get(target)
                if (
                    target == task_id
                    or target_record is None
                    or target_record.get("status") != "active"
                ):
                    blockers.append(
                        f"write-ownership:unknown-handover:{task_id}:{target}"
                    )
    active_records = [
        record
        for record in records
        if isinstance(record, dict)
        and record.get("status") == "active"
        and isinstance(record.get("write_scope"), list)
    ]
    for index, left in enumerate(active_records):
        for right in active_records[index + 1 :]:
            if left.get("task_id") == right.get("task_id"):
                continue
            for left_path in _record_scope(left):
                for right_path in _record_scope(right):
                    if not _paths_overlap(left_path, right_path):
                        continue
                    representative = (
                        left_path if len(left_path) >= len(right_path) else right_path
                    )
                    first, second = sorted(
                        [str(left.get("agent")), str(right.get("agent"))]
                    )
                    blockers.append(
                        f"write-ownership:overlap:{representative}:{first}:{second}"
                    )
    return sorted(set(blockers))


def check_write_ownership_fixture() -> None:
    """Run the ownership cases and prove each guard with a mutation.

    The file cases cover disjoint writes, overlapping writes, an explicit
    handover, stale ownership and a read-only write. The in-memory mutations
    start from the disjoint positive control and corrupt one rule at a time,
    so removing a guard makes its own mutation pass. Actual write obedience and
    filesystem isolation stay instruction-only.
    """
    require(
        OWNERSHIP_FIXTURES.is_dir(),
        f"missing ownership fixture directory: {OWNERSHIP_FIXTURES}",
    )
    cases = sorted(OWNERSHIP_FIXTURES.glob("*.json"))
    require(bool(cases), "at least one ownership fixture case is required")
    control: dict[str, Any] | None = None
    for case_path in cases:
        label = case_path.stem
        document = json.loads(case_path.read_text(encoding="utf-8"))
        expected = document.get("expected_blockers", [])
        found = validate_write_ownership(document)
        require(
            set(found) == set(expected),
            f"ownership fixture {label}: expected blockers {sorted(expected)}, "
            f"got {found}",
        )
        if label == "disjoint-writes":
            control = document
        print(f"ownership fixture {label}: {found or 'no blockers'}")
    require(control is not None, "the disjoint-writes positive control is required")
    mutations = 0

    def base() -> dict[str, Any]:
        return json.loads(json.dumps(control))

    def case(label: str, mutate: Any, *expected: str) -> None:
        nonlocal mutations
        mutations += 1
        document = base()
        mutate(document)
        found = validate_write_ownership(document)
        require(bool(found), f"{label}: expected at least one blocker")
        for blocker in expected:
            require(
                blocker in found,
                f"{label}: expected blocker {blocker!r}, got {found}",
            )

    def add_record(
        document: dict[str, Any],
        task_id: str,
        agent: str,
        scope: list[str],
    ) -> dict[str, Any]:
        document["active_tasks"].append(task_id)
        record = {
            "task_id": task_id,
            "agent": agent,
            "status": "active",
            "write_scope": scope,
            "scratch": f".tmp/{task_id}/",
            "dependencies": [],
        }
        document["records"].append(record)
        return record

    case(
        "overlapping write added",
        lambda document: add_record(
            document, "task-b", "implementer", ["tools/workflow_check.py"]
        ),
        "write-ownership:overlap:tools/workflow_check.py:implementer:implementer",
    )
    case(
        "handover missing",
        lambda document: document["records"][0].update({"status": "handed-over"}),
        "write-ownership:missing-handover:issue-30-wi-co-implementation",
    )
    case(
        "handover target unknown",
        lambda document: (
            document["records"][0].update(
                {"status": "handed-over", "handover": {"to": "ghost-task"}}
            )
        ),
        "write-ownership:unknown-handover:issue-30-wi-co-implementation:ghost-task",
    )
    case(
        "stale active task",
        lambda document: document["active_tasks"].remove(
            "issue-30-wi-co-implementation"
        ),
        "write-ownership:stale:issue-30-wi-co-implementation",
    )
    case(
        "read-only agent writes",
        lambda document: document["records"][2].update(
            {"write_scope": ["docs/workflow/development-workflow.md"]}
        ),
        "write-ownership:read-only:reviewer:docs/workflow/development-workflow.md",
    )
    case(
        "shared scratch directory",
        lambda document: document["records"][0].update(
            {"scratch": ".tmp/shared/"}
        ),
        "write-ownership:scratch:issue-30-wi-co-implementation:.tmp/shared/",
    )
    case(
        "orchestrator writes outside the ledger",
        lambda document: document["records"][1].update(
            {"write_scope": ["src/main.go"]}
        ),
        "write-ownership:role-scope:orchestrator:src/main.go",
    )
    case(
        "planner writes outside the ADRs",
        lambda document: add_record(document, "task-plan", "planner", ["src/main.go"]),
        "write-ownership:role-scope:planner:src/main.go",
    )
    case(
        "implementer writes the ledger",
        lambda document: document["records"][0].update(
            {"write_scope": ["docs/workflow/ledgers/issue-30.md"]}
        ),
        "write-ownership:role-scope:implementer:docs/workflow/ledgers/issue-30.md",
    )
    case(
        "git manager writes files",
        lambda document: add_record(
            document, "task-git", "git-manager", ["tools/workflow_check.py"]
        ),
        "write-ownership:role-scope:git-manager:tools/workflow_check.py",
    )
    case(
        "unknown agent",
        lambda document: document["records"][0].update({"agent": "docs-auditor"}),
        "write-ownership:unknown-agent:docs-auditor",
    )
    case(
        "invalid status",
        lambda document: document["records"][0].update({"status": "paused"}),
        "write-ownership:invalid-status:issue-30-wi-co-implementation:paused",
    )
    case(
        "missing dependencies",
        lambda document: document["records"][0].pop("dependencies"),
        "write-ownership:missing:dependencies:issue-30-wi-co-implementation",
    )
    case(
        "invalid active task list",
        lambda document: document.update({"active_tasks": "issue-30-wi-co-implementation"}),
        "write-ownership:invalid:active-tasks",
    )
    case(
        "missing records",
        lambda document: document.update({"records": []}),
        "write-ownership:missing:records",
    )
    print(
        f"PASS write ownership fixtures: {len(cases)} cases cover disjoint, "
        "overlapping, handover, stale and read-only ownership, and "
        f"{mutations} in-memory mutations each fail their case with the named "
        "blocker; write obedience and filesystem isolation remain "
        "instruction-only"
    )


# --- CI workflow contract -------------------------------------------------
#
# The `workflow-validator` job in .github/workflows/ci.yml is the CI evidence
# for AC-CI1. The contract below proves the YAML shape: the job, the
# exact-head checkout, the full-history setting, the recorded explicit base,
# the trusted commands and the absence of a soft-fail flag. It never proves
# that a run passed — only inspected run/job/step/log evidence on the reviewed
# head does that, and `jactionlint` only checks the workflow syntax.
CI_VALIDATOR_JOB = "workflow-validator"
CI_AUDIT_COMMAND = "python3 tools/audit_validator.py"
CI_TRUSTED_COMMAND = "python3 tools/workflow_check.py ci"


def _yaml_indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _ci_job_lines(text: str, job: str) -> list[str] | None:
    """Return the lines of one two-space-indented job body, or None.

    The parser is deliberately narrow: it only understands this repository's
    workflow layout, and it returns None unless the job name appears exactly
    once as a job key.
    """
    lines = text.splitlines()
    header = f"  {job}:"
    starts = [index for index, line in enumerate(lines) if line.rstrip() == header]
    if len(starts) != 1:
        return None
    body: list[str] = []
    for line in lines[starts[0] + 1 :]:
        if line.strip() and _yaml_indent(line) <= 2:
            break
        body.append(line)
    return body


def _ci_steps(job_lines: list[str]) -> list[list[str]]:
    """Split a job body into step blocks, each starting at `      - `."""
    steps: list[list[str]] = []
    current: list[str] | None = None
    for line in job_lines:
        if line.startswith("      - "):
            if current is not None:
                steps.append(current)
            current = [line]
        elif current is not None:
            current.append(line)
    if current is not None:
        steps.append(current)
    return steps


def _ci_step_script(step_lines: list[str]) -> str:
    """Return the shell script of one step, in block or single-line form."""
    for index, line in enumerate(step_lines):
        if re.match(r"\s*run:\s*[|>][-+]?\s*$", line):
            indent = _yaml_indent(line)
            body: list[str] = []
            for follow in step_lines[index + 1 :]:
                if follow.strip() and _yaml_indent(follow) <= indent:
                    break
                body.append(follow)
            return "\n".join(body)
    for line in step_lines:
        match = re.match(r"\s*run:\s*(\S.*)$", line)
        if match:
            return match.group(1).strip()
    return ""


def validate_ci_workflow_contract(text: str) -> list[str]:
    """Return the named CI-contract blockers for one workflow text.

    Every blocker names the exact guard it proves, so a mutation that removes
    one property fails with its own identifier instead of a generic error.
    """
    blockers: list[str] = []
    job_lines = _ci_job_lines(text, CI_VALIDATOR_JOB)
    if job_lines is None:
        return [f"ci-contract:job:{CI_VALIDATOR_JOB}"]
    job_text = "\n".join(job_lines)
    code_lines = [
        line for line in job_lines if not line.strip().startswith("#")
    ]
    code_text = "\n".join(code_lines)
    steps = _ci_steps(job_lines)

    def want(condition: bool, blocker: str) -> None:
        if not condition:
            blockers.append(blocker)

    # The job only means something for a pull request: a push or a manual
    # dispatch carries no reviewed base to assert.
    want(
        bool(
            re.search(
                r"(?m)^\s+if:\s*github\.event_name\s*==\s*'pull_request'\s*$",
                job_text,
            )
        ),
        "ci-contract:event-gate",
    )
    want(
        bool(re.search(r"(?m)^\s+timeout-minutes:\s*\d+\s*$", job_text)),
        "ci-contract:timeout",
    )
    want(
        bool(
            re.search(
                r"(?m)^\s+BASE_REPOSITORY:\s*\$\{\{\s*"
                r"github\.event\.pull_request\.base\.repo\.full_name\s*\}\}\s*$",
                job_text,
            )
        ),
        "ci-contract:base-repository",
    )
    want(
        bool(
            re.search(
                r"(?m)^\s+EXPECTED_HEAD_SHA:\s*\$\{\{\s*"
                r"github\.event\.pull_request\.head\.sha\s*\}\}\s*$",
                job_text,
            )
        ),
        "ci-contract:head-sha",
    )
    # The base is an explicit commit identity, never a branch name: a stale
    # local `main` is environment state and must not decide the check. Every
    # recorded value must be a commit, so a second, softer declaration cannot
    # hide behind a valid one.
    base_values = re.findall(
        r"(?m)^\s+EXPECTED_BASE_SHA:\s*(\S+)\s*$", job_text
    )
    if not base_values:
        blockers.append("ci-contract:base-sha:missing")
    for value in base_values:
        if not re.fullmatch(r"[0-9a-f]{7,40}", value):
            blockers.append(f"ci-contract:base-sha:not-a-commit:{value}")

    checkouts = [
        step for step in steps if "uses: actions/checkout@" in "\n".join(step)
    ]
    want(bool(checkouts), "ci-contract:checkout")
    for checkout in checkouts:
        checkout_text = "\n".join(checkout)
        want(
            bool(re.search(r"uses:\s*actions/checkout@[0-9a-f]{40}\b", checkout_text)),
            "ci-contract:checkout-pin",
        )
        want(
            bool(re.search(r"(?m)^\s+fetch-depth:\s*0\s*$", checkout_text)),
            "ci-contract:fetch-depth",
        )
        want(
            bool(re.search(r"(?m)^\s+persist-credentials:\s*false\s*$", checkout_text)),
            "ci-contract:persist-credentials",
        )
        want(
            bool(
                re.search(
                    r"(?m)^\s+ref:\s*\$\{\{\s*"
                    r"github\.event\.pull_request\.head\.sha\s*\}\}\s*$",
                    checkout_text,
                )
            ),
            "ci-contract:head-ref",
        )
        want(
            bool(
                re.search(
                    r"(?m)^\s+repository:\s*\$\{\{\s*"
                    r"github\.event\.pull_request\.head\.repo\.full_name\s*\}\}\s*$",
                    checkout_text,
                )
            ),
            "ci-contract:head-repository",
        )

    scripts = [_ci_step_script(step) for step in steps]
    base_script = next(
        (
            script
            for script in scripts
            if "EXPECTED_BASE_SHA" in script and "rev-parse" in script
        ),
        "",
    )
    if not base_script:
        blockers.append("ci-contract:base-assert:missing")
    else:
        want(
            bool(
                re.search(
                    r"rev-parse\s+(?:--verify\s+)?(?:refs/remotes/)?origin/main",
                    base_script,
                )
            ),
            "ci-contract:base-assert:rev-parse",
        )
        want(
            bool(
                "git fetch" in base_script
                and "BASE_REPOSITORY" in base_script
                and "+refs/heads/main:refs/remotes/origin/main" in base_script
            ),
            "ci-contract:base-fetch",
        )
        want(
            bool("merge-base --is-ancestor" in base_script),
            "ci-contract:base-ancestor",
        )
        want(
            bool(
                re.search(
                    r"(?m)^\s*if\s+\[\[?[^\n]*EXPECTED_BASE_SHA[^\n]*\]\]?",
                    base_script,
                )
            ),
            "ci-contract:base-assert:compare",
        )
        want(
            bool(
                re.search(
                    r"(?m)^\s*if\s+\[\[?[^\n]*EXPECTED_HEAD_SHA[^\n]*\]\]?",
                    base_script,
                )
            ),
            "ci-contract:head-assert:compare",
        )
        want(
            bool(re.search(r"(?m)^\s*exit 1\s*$", base_script)),
            "ci-contract:assert-exit",
        )
        want(
            all(
                re.search(rf'(?mi)^\s*echo\s+"?expected {part}', base_script)
                for part in ("head", "base")
            ),
            "ci-contract:assert-print:expected",
        )
        want(
            all(
                re.search(rf'(?mi)^\s*echo\s+"?actual {part}', base_script)
                for part in ("head", "base")
            ),
            "ci-contract:assert-print:actual",
        )

    # The trusted commands must be executed command lines, not comments, and
    # in the trusted order: the self-audit first, then `ci`. `all` belongs to
    # the live release evaluation, never to this job.
    command_lines = [
        line.strip()
        for script in scripts
        for line in script.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    want(CI_AUDIT_COMMAND in command_lines, "ci-contract:audit-command")
    want(CI_TRUSTED_COMMAND in command_lines, "ci-contract:trusted-command")
    if CI_AUDIT_COMMAND in command_lines and CI_TRUSTED_COMMAND in command_lines:
        want(
            command_lines.index(CI_AUDIT_COMMAND)
            < command_lines.index(CI_TRUSTED_COMMAND),
            "ci-contract:command-order",
        )
    want(
        not any(
            re.search(r"workflow_check\.py\s+all\b", line) for line in command_lines
        ),
        "ci-contract:all-mode",
    )
    want("continue-on-error" not in code_text, "ci-contract:continue-on-error")
    return blockers


def check_ci_workflow_contract() -> None:
    """Prove the CI workflow contract with named mutations.

    The positive control is the real workflow. Each mutation removes or
    corrupts exactly one guard — the full-history setting, the exact-head
    checkout, the recorded base, the trusted command or the no-soft-fail
    rule — and its own blocker must appear. A mutation that no longer matches
    the workflow fails the run instead of passing vacuously.
    """
    require(CI_WORKFLOW_PATH.is_file(), f"missing CI workflow: {CI_WORKFLOW_PATH}")
    text = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
    control = validate_ci_workflow_contract(text)
    require(not control, f"CI workflow contract must pass, got {control}")
    mutations = 0

    def case(label: str, old: str, new: str, expected: str) -> None:
        nonlocal mutations
        mutations += 1
        require(
            old in text,
            f"{label}: mutation target is not in the workflow: {old!r}",
        )
        mutated = text.replace(old, new, 1)
        require(mutated != text, f"{label}: mutation did not change the workflow")
        found = validate_ci_workflow_contract(mutated)
        require(
            expected in found,
            f"{label}: expected blocker {expected!r}, got {found}",
        )

    case(
        "job removed",
        "  workflow-validator:\n",
        "",
        f"ci-contract:job:{CI_VALIDATOR_JOB}",
    )
    case(
        "event gate removed",
        "    if: github.event_name == 'pull_request'\n",
        "",
        "ci-contract:event-gate",
    )
    case(
        "timeout removed",
        "    runs-on: ubuntu-24.04\n    timeout-minutes: 10\n"
        "    # Only a pull request carries the base the change is reviewed against; a\n",
        "    runs-on: ubuntu-24.04\n"
        "    # Only a pull request carries the base the change is reviewed against; a\n",
        "ci-contract:timeout",
    )
    case(
        "checkout step replaced",
        "      - name: Checkout the exact pull-request head\n"
        "        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
        " # v7.0.1\n",
        "      - name: Checkout the exact pull-request head\n"
        "        uses: actions/cache@0000000000000000000000000000000000000000\n",
        "ci-contract:checkout",
    )
    case(
        "checkout unpinned",
        "      - name: Checkout the exact pull-request head\n"
        "        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
        " # v7.0.1\n",
        "      - name: Checkout the exact pull-request head\n"
        "        uses: actions/checkout@v7.0.1\n",
        "ci-contract:checkout-pin",
    )
    case(
        "full history removed",
        "          ref: ${{ github.event.pull_request.head.sha }}\n"
        "          fetch-depth: 0\n",
        "          ref: ${{ github.event.pull_request.head.sha }}\n",
        "ci-contract:fetch-depth",
    )
    case(
        "shallow history",
        "          fetch-depth: 0\n",
        "          fetch-depth: 1\n",
        "ci-contract:fetch-depth",
    )
    case(
        "persisted credentials",
        "          fetch-depth: 0\n          persist-credentials: false\n",
        "          fetch-depth: 0\n",
        "ci-contract:persist-credentials",
    )
    case(
        "exact head ref removed",
        "          repository: ${{ github.event.pull_request.head.repo.full_name }}\n"
        "          ref: ${{ github.event.pull_request.head.sha }}\n"
        "          fetch-depth: 0\n",
        "          repository: ${{ github.event.pull_request.head.repo.full_name }}\n"
        "          fetch-depth: 0\n",
        "ci-contract:head-ref",
    )
    case(
        "head ref pinned to a branch",
        "          ref: ${{ github.event.pull_request.head.sha }}\n",
        "          ref: main\n",
        "ci-contract:head-ref",
    )
    case(
        "head repository removed",
        "          repository: ${{ github.event.pull_request.head.repo.full_name }}\n"
        "          ref: ${{ github.event.pull_request.head.sha }}\n",
        "          ref: ${{ github.event.pull_request.head.sha }}\n",
        "ci-contract:head-repository",
    )
    case(
        "base repository removed",
        "      BASE_REPOSITORY: ${{ github.event.pull_request.base.repo.full_name }}\n",
        "",
        "ci-contract:base-repository",
    )
    case(
        "expected head removed",
        "      EXPECTED_HEAD_SHA: ${{ github.event.pull_request.head.sha }}\n",
        "",
        "ci-contract:head-sha",
    )
    case(
        "recorded base removed",
        "      EXPECTED_BASE_SHA: 17cf55aa0181bf16bf6b0c1c5942ce67bcc57119\n",
        "",
        "ci-contract:base-sha:missing",
    )
    case(
        "recorded base pinned to a branch",
        "      EXPECTED_BASE_SHA: 17cf55aa0181bf16bf6b0c1c5942ce67bcc57119",
        "      EXPECTED_BASE_SHA: main",
        "ci-contract:base-sha:not-a-commit:main",
    )
    case(
        "assertion step emptied",
        "      - name: Assert the recorded base and head\n        run: |\n",
        "      - name: Assert the recorded base and head\n        run: echo skipped\n",
        "ci-contract:base-assert:missing",
    )
    case(
        "base resolution removed",
        '          actual_base="$(git rev-parse refs/remotes/origin/main)"\n',
        "",
        "ci-contract:base-assert:rev-parse",
    )
    case(
        "base fetch removed",
        '          git fetch --no-tags "https://github.com/${BASE_REPOSITORY}" \\\n'
        '            "+refs/heads/main:refs/remotes/origin/main"\n',
        "",
        "ci-contract:base-fetch",
    )
    case(
        "base refspec removed",
        '            "+refs/heads/main:refs/remotes/origin/main"\n',
        "",
        "ci-contract:base-fetch",
    )
    case(
        "base ancestry removed",
        '          if ! git merge-base --is-ancestor "${EXPECTED_BASE_SHA}" HEAD; then\n',
        "          if false; then\n",
        "ci-contract:base-ancestor",
    )
    case(
        "base comparison softened",
        '          if [ "${actual_base}" != "${EXPECTED_BASE_SHA}" ]; then\n',
        '          if [ "1" != "1" ]; then\n',
        "ci-contract:base-assert:compare",
    )
    case(
        "head comparison softened",
        '          if [ "${actual_head}" != "${EXPECTED_HEAD_SHA}" ]; then\n',
        '          if [ "1" != "1" ]; then\n',
        "ci-contract:head-assert:compare",
    )
    case(
        "assertions cannot fail",
        '          if [ "${actual_head}" != "${EXPECTED_HEAD_SHA}" ]; then\n'
        '            echo "checked-out head is not the reviewed pull-request head" >&2\n'
        "            exit 1\n"
        "          fi\n"
        '          if [ "${actual_base}" != "${EXPECTED_BASE_SHA}" ]; then\n'
        '            echo "origin/main does not resolve to the recorded base SHA" \\\n'
        '              "record the base deliberately instead of relabelling the check" >&2\n'
        "            exit 1\n"
        "          fi\n"
        '          if ! git merge-base --is-ancestor "${EXPECTED_BASE_SHA}" HEAD; then\n'
        '            echo "the recorded base is not an ancestor of the reviewed head" >&2\n'
        "            exit 1\n"
        "          fi\n",
        '          if [ "${actual_head}" != "${EXPECTED_HEAD_SHA}" ]; then\n'
        '            echo "checked-out head is not the reviewed pull-request head" >&2\n'
        "            true\n"
        "          fi\n"
        '          if [ "${actual_base}" != "${EXPECTED_BASE_SHA}" ]; then\n'
        '            echo "origin/main does not resolve to the recorded base SHA" \\\n'
        '              "record the base deliberately instead of relabelling the check" >&2\n'
        "            true\n"
        "          fi\n"
        '          if ! git merge-base --is-ancestor "${EXPECTED_BASE_SHA}" HEAD; then\n'
        '            echo "the recorded base is not an ancestor of the reviewed head" >&2\n'
        "            true\n"
        "          fi\n",
        "ci-contract:assert-exit",
    )
    case(
        "expected print removed",
        '          echo "expected head: ${EXPECTED_HEAD_SHA}"\n',
        "",
        "ci-contract:assert-print:expected",
    )
    case(
        "actual print removed",
        '          echo "actual base:   ${actual_base}"\n',
        "",
        "ci-contract:assert-print:actual",
    )
    case(
        "audit command removed",
        "        run: python3 tools/audit_validator.py\n",
        "        run: echo audit skipped\n",
        "ci-contract:audit-command",
    )
    case(
        "trusted command removed",
        "        run: python3 tools/workflow_check.py ci\n",
        "        run: echo checks skipped\n",
        "ci-contract:trusted-command",
    )
    case(
        "trusted command replaced by all",
        "        run: python3 tools/workflow_check.py ci\n",
        "        run: python3 tools/workflow_check.py all"
        " --release-scenario docs/workflow/ledgers/issue-30.release.json\n",
        "ci-contract:all-mode",
    )
    case(
        "trusted command softened",
        "        run: python3 tools/workflow_check.py ci\n",
        "        run: python3 tools/workflow_check.py ci || true\n",
        "ci-contract:trusted-command",
    )
    case(
        "command order reversed",
        "      - name: Audit the validator\n"
        "        run: python3 tools/audit_validator.py\n\n"
        "      - name: Run the trusted offline workflow checks\n"
        "        run: python3 tools/workflow_check.py ci\n",
        "      - name: Run the trusted offline workflow checks\n"
        "        run: python3 tools/workflow_check.py ci\n\n"
        "      - name: Audit the validator\n"
        "        run: python3 tools/audit_validator.py\n",
        "ci-contract:command-order",
    )
    case(
        "continue-on-error added",
        "      - name: Run the trusted offline workflow checks\n",
        "      - name: Run the trusted offline workflow checks\n"
        "        continue-on-error: true\n",
        "ci-contract:continue-on-error",
    )
    print(
        f"PASS ci workflow contract: the workflow-validator job checks out the "
        f"exact pull-request head, enforces the recorded explicit base and runs "
        f"the trusted commands, and {mutations} mutations each fail their named "
        f"case; the static contract proves the YAML shape only, never a passing "
        f"run"
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


def check_ledger_structure_in_memory_fixture() -> None:
    """Prove each ledger-structure guard with an in-memory ledger.

    Every case starts from the same well-formed control and changes exactly one
    property, so the case fails only when its guard is present. The two real
    incidents are represented directly: a five-cell row appended to the
    four-column findings table and a raw edit payload pasted into a row. The
    mutation proof is recorded in the implementation report; removing one
    helper below makes exactly its own case stop failing.
    """
    sections = {
        "acceptance": (
            "## Acceptance criteria\n\n"
            "Intro prose.\n\n"
            "| ID | Criterion | Delegated to | Status | Evidence | Gaps |\n"
            "| --- | --- | --- | --- | --- | --- |\n"
            "| AC-01 | Criterion | Implementer | covered | `file` | none |"
        ),
        "plan": (
            "## Implementation plan (revision 2)\n\n"
            "Plan prose.\n\n"
            "| Item | Binding rule |\n"
            "| --- | --- |\n"
            "| Extraction | hashes the frozen section |"
        ),
        "reports": (
            "## Reports reconciled\n\n"
            "| Agent | Task | Status | Received | Key findings |\n"
            "| --- | --- | --- | --- | --- |\n"
            "| Implementer | t-1 | Completed | 2026-11-27 | none |\n"
            "| Local discovery | t-2 | completed | 2026-11-27 | none |"
        ),
        "findings": (
            "## Findings and resolutions\n\n"
            "| Severity | Finding | Resolution | Status |\n"
            "| --- | --- | --- | --- |\n"
            "| High | finding | resolution | Resolved |\n"
            "| Decision | choice | recorded | Implemented |"
        ),
        "architecture": "## Architecture baseline\n\nProse only.",
        "unresolved": "## Unresolved items\n\nProse only.",
        "deferred": "## Deferred or out-of-scope work\n\nProse only.",
        "handover": "## Handover\n\nProse only.",
    }
    order = [
        "acceptance",
        "plan",
        "reports",
        "findings",
        "architecture",
        "unresolved",
        "deferred",
        "handover",
    ]

    def compose(
        section_order: list[str] | None = None,
        replacements: dict[str, str] | None = None,
    ) -> str:
        replacement_map = replacements or {}
        parts = [
            replacement_map.get(name, sections[name])
            for name in (section_order or order)
        ]
        return "\n\n".join(parts) + "\n"

    def expect_pass(label: str, text: str) -> None:
        _validate_ledger_structure(text, label)

    def expect_error(label: str, text: str, *fragments: str) -> None:
        try:
            _validate_ledger_structure(text, label)
        except CheckError as error:
            for fragment in fragments:
                require(
                    fragment in str(error),
                    f"ledger fixture {label}: expected {fragment!r} in the "
                    f"failure, got: {error}",
                )
        else:
            raise CheckError(
                f"ledger fixture {label}: expected a CheckError and got a pass"
            )

    expect_pass("well-formed", compose())

    bad_findings = (
        sections["findings"] + "\n| Low | extra | cells | here | overflow |"
    )
    bad_findings_text = compose(replacements={"findings": bad_findings})
    overflowing = "| Low | extra | cells | here | overflow |"
    expected_line = (
        bad_findings_text.splitlines().index(overflowing) + 1
    )
    expect_error(
        "five-cell findings row",
        bad_findings_text,
        f":{expected_line}:",
        "5 cells",
        "expected 4",
    )

    tool_payload = (
        sections["unresolved"]
        + '\n\nThe row ended with ","oldString":"value","path":"file" and prose.'
    )
    expect_error(
        "raw edit payload",
        compose(replacements={"unresolved": tool_payload}),
        "forbidden tool-payload literal",
        "oldString",
    )

    new_string_payload = (
        sections["unresolved"]
        + '\n\nThe row ended with ","newString":"value" and prose.'
    )
    expect_error(
        "raw newString payload",
        compose(replacements={"unresolved": new_string_payload}),
        "forbidden tool-payload literal",
        "newString",
    )

    payload_tail = (
        sections["unresolved"]
        + '\n\nThe payload was ","path":"file","content":"text"}'
    )
    expect_error(
        "tool payload tail",
        compose(replacements={"unresolved": payload_tail}),
        "tool-payload tail",
    )

    expect_error(
        "missing section",
        compose(section_order=[name for name in order if name != "handover"]),
        "missing required ledger section",
        "## Handover",
    )

    expect_error(
        "duplicated section",
        compose(section_order=order + ["unresolved"]),
        "appears 2 times",
        "## Unresolved items",
    )

    out_of_order = list(order)
    out_of_order[4], out_of_order[5] = out_of_order[5], out_of_order[4]
    expect_error(
        "out-of-order sections",
        compose(section_order=out_of_order),
        "out of order",
    )

    escaped_pipe = sections["handover"] + "\n\nA literal \\n| escape."
    expect_error(
        "escaped newline pipe",
        compose(replacements={"handover": escaped_pipe}),
        "forbidden tool-payload literal",
        "\\n|",
    )

    prose_table = (
        sections["unresolved"]
        + "\n\n| Item | Note |\n| --- | --- |\n| one | two |\n\n"
        "Prose after the table."
    )
    expect_pass(
        "prose section around a real table",
        compose(replacements={"unresolved": prose_table}),
    )

    bad_id = sections["acceptance"].replace("| AC-01 |", "| PREP-01 |")
    expect_error(
        "acceptance row without AC-",
        compose(replacements={"acceptance": bad_id}),
        "must start with 'AC-'",
    )

    bad_role = (
        sections["reports"]
        + "\n| Lead Reviewer | t-3 | Completed | 2026-11-27 | none |"
    )
    expect_error(
        "misplaced role in reports",
        compose(replacements={"reports": bad_role}),
        "agent-role row must begin with",
    )

    bad_severity = sections["findings"].replace("| High |", "| Critical |")
    expect_error(
        "unknown severity",
        compose(replacements={"findings": bad_severity}),
        "findings row severity must be one of",
    )

    wrong_header = sections["findings"].replace("| Severity |", "| Level |")
    expect_error(
        "wrong findings header",
        compose(replacements={"findings": wrong_header}),
        "header first cell is 'Severity'",
    )

    print(
        "PASS ledger structure in-memory fixtures: the well-formed control "
        "passes, a five-cell row names its line and both counts, the recorded "
        "edit payloads, the tool-call tail and the literal \\n| escape fail, "
        "and missing, duplicated and out-of-order sections are rejected"
    )


def check_fixtures() -> None:
    check_adr_fixture()
    check_adr_combined_fixture()
    check_adr_in_memory_fixture()
    check_permissions_fixture()
    check_ledger_structure_in_memory_fixture()
    check_reconcile_in_memory_fixture()
    check_release_gate_in_memory_fixture()
    check_release_fixtures()
    check_right_sized_work_item_fixture()
    check_delegation_packet_fixture()
    check_write_ownership_fixture()
    check_ci_workflow_contract()
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
        choices=["config", "adr", "reports", "fixtures", "ci", "all"],
        nargs="?",
        default="all",
    )
    parser.add_argument(
        "--scenario",
        default=str(FIXTURES / "workflow" / "scenario.json"),
        help="feedback reconciliation scenario",
    )
    parser.add_argument(
        "--release-scenario",
        default=str(ROOT / "docs" / "workflow" / "ledgers" / "issue-30.release.json"),
        help="live release record evaluated by all",
    )
    args = parser.parse_args()
    try:
        if args.command in {"ci", "all"}:
            check_self_audit()
        if args.command in {"config", "ci", "all"}:
            check_config()
        if args.command == "reports":
            check_reports(Path(args.scenario))
        if args.command in {"fixtures", "ci", "all"}:
            check_fixtures()
        if args.command in {"ci", "all"}:
            check_plan_identity()
            check_ledger_structure()
        if args.command == "adr" or args.command in {"ci", "all"}:
            check_adr_actual()
        if args.command == "all":
            if not check_live_release(Path(args.release_scenario)):
                print("FAIL: release_ready is false", file=sys.stderr)
                return 1
        print("All workflow checks passed.")
        return 0
    except CheckError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
