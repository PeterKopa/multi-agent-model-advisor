#!/usr/bin/env python3
"""Offline validation for the Multi-Agent Model Advisor development workflow.

The validator checks three things without network access or credentials:

1. the project agent configuration and its permission boundaries;
2. ADR baseline handling when an open pull request declares an ADR accepted;
3. feedback reconciliation with synthetic reports, including an omitted
   criterion, an unverified criterion and a proposed ADR conflict.
"""

from __future__ import annotations

import argparse
import fnmatch
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
    frontmatter, _ = split_markdown(text)
    adr = dict(frontmatter)
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
    baseline_ids = {adr["id"] for adr in baseline if adr["status"] == "Accepted"}
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
    conflicts: list[dict[str, str]] = []
    for adr in open_pr:
        for conflicting in adr.get("conflicts-with", []):
            if conflicting in baseline_ids:
                conflicts.append(
                    {
                        "proposal": str(adr["id"]),
                        "baseline": str(conflicting),
                        "decision": "Open pull-request ADR conflicts with the accepted baseline",
                    }
                )
    proposal_ids = {proposal["id"] for proposal in proposals}
    all_ids = baseline_ids | proposal_ids
    for adr in open_pr:
        for reference in list(adr.get("supersedes", [])) + list(
            adr.get("conflicts-with", [])
        ):
            require(
                reference in all_ids,
                f"{adr['id']} references unknown ADR {reference}",
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
            conflict["baseline"] in baseline_ids,
            f"conflict references a baseline ADR that is not accepted: {conflict['baseline']}",
        )
    return baseline_ids, proposals, conflicts


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


def effective_effect(
    rules: list[dict[str, Any]], action: str, value: str
) -> str:
    effect = "allow"
    for rule in rules:
        if rule_matches(rule, action, value):
            effect = str(rule.get("effect", "allow"))
    return effect


def check_config() -> None:
    config = load_jsonc(ROOT / "opencode.jsonc")
    require(config.get("default_agent") == "orchestrator", "default_agent must be orchestrator")
    instructions = config.get("instructions", [])
    require(
        "docs/workflow/feedback-contract.md" in instructions,
        "opencode.jsonc must load the shared feedback contract",
    )

    global_rules = config.get("permissions", [])
    require(
        effective_effect(global_rules, "shell", "git status --short") == "allow",
        "project permissions must allow read-only git inspection",
    )
    for command in [
        "git add .",
        "git commit -m test",
        "git push origin HEAD",
        "git filter-branch --force",
        "gh pr create --title test",
        "gh pr merge 1 --merge",
        "gh workflow run test.yml",
        "gh api repos/x/y",
    ]:
        require(
            effective_effect(global_rules, "shell", command) == "deny",
            f"project permissions must deny {command!r}",
        )

    files = sorted(AGENTS_DIR.glob("*.md"))
    found = {path.stem for path in files}
    require(
        set(REQUIRED_AGENTS) <= found,
        f"required agent files are missing: {sorted(set(REQUIRED_AGENTS) - found)}",
    )

    write_commands = [
        "git add .",
        "git commit -m test",
        "git push origin HEAD",
        "git merge main",
        "git rebase main",
        "git checkout -b feature",
        "gh pr create --title test",
        "gh api repos/x/y",
    ]
    human_only_commands = [
        "gh pr merge 1 --merge",
        "gh pr merge 1",
    ]
    read_commands = [
        "git status --short",
        "git diff --stat",
        "git log --oneline -1",
        "git show HEAD",
        "gh pr view 1",
        "gh issue view 30",
    ]

    agent_rules: dict[str, list[dict[str, Any]]] = {}
    for path in files:
        agent = path.stem
        frontmatter, body = read_markdown(path)
        require(
            frontmatter.get("mode") == REQUIRED_AGENTS.get(agent),
            f"{agent}: expected mode {REQUIRED_AGENTS.get(agent)!r}",
        )
        require(bool(frontmatter.get("description")), f"{agent}: description is required")
        require(len(body.strip()) > 200, f"{agent}: system prompt is unexpectedly short")

        rules = parse_permissions(path)
        agent_rules[agent] = rules
        require(
            not any(
                rule.get("action") == "*"
                and rule.get("resource") == "*"
                and rule.get("effect") == "allow"
                for rule in rules
            ),
            f"{agent}: a broad allow rule would override the project write restrictions",
        )
        combined = list(global_rules) + rules
        for command in write_commands:
            expected = "allow" if agent == "git-manager" else "deny"
            actual = effective_effect(combined, "shell", command)
            require(
                actual == expected,
                f"{agent}: {command!r} resolves to {actual}, expected {expected}",
            )
        for command in human_only_commands:
            require(
                effective_effect(combined, "shell", command) == "deny",
                f"{agent}: pull-request merge is reserved for the human user",
            )
        for command in read_commands:
            require(
                effective_effect(combined, "shell", command) == "allow",
                f"{agent}: read-only command {command!r} must stay allowed",
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

    git_manager_allows = [
        rule
        for rule in agent_rules["git-manager"]
        if rule.get("action") == "shell" and rule.get("effect") == "allow"
    ]
    require(bool(git_manager_allows), "git-manager must have Git/GitHub write allow rules")
    require(
        not any(
            str(rule.get("resource", "")).startswith("gh pr merge")
            for rule in git_manager_allows
        ),
        "git-manager must not have a pull-request merge allow rule",
    )
    for agent, rules in agent_rules.items():
        if agent == "git-manager":
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
        combined = list(global_rules) + rules
        for rule in git_manager_allows:
            resource = str(rule.get("resource", ""))
            sample = resource.replace("*", "sample").strip()
            require(
                effective_effect(combined, "shell", sample) == "deny",
                f"{agent}: derived write command {sample!r} is not denied",
            )
    git_manager_combined = list(global_rules) + agent_rules["git-manager"]
    for rule in git_manager_allows:
        resource = str(rule.get("resource", ""))
        sample = resource.replace("*", "sample").strip()
        require(
            effective_effect(git_manager_combined, "shell", sample) == "allow",
            f"git-manager: derived write command {sample!r} is not allowed",
        )

    agents_md = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    require("feedback-contract.md" in agents_md, "AGENTS.md must point to the feedback contract")
    require("ADR" in agents_md, "AGENTS.md must describe the ADR baseline")

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
    for expected_gap in expected.get("gaps_include", []):
        require(expected_gap in gaps, f"expected gap not found: {expected_gap}")
    for expected_escalation in expected.get("escalations_include", []):
        require(
            expected_escalation in escalations,
            f"expected escalation not found: {expected_escalation}",
        )
    print("PASS reports: synthetic reports reconcile with gaps and escalations as expected")


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


def check_fixtures() -> None:
    check_adr_fixture()
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
