---
id: ADR-0002
title: Adopt a project-specific multi-agent development workflow
status: Accepted
date: 2026-11-26
issues: [30]
supersedes: []
superseded-by: null
conflicts-with: []
---

# Context

The project needs a repeatable way to turn issues into planned, implemented,
tested and reviewed changes before application development starts. The workflow
must keep architecture decisions visible, keep credentials and personal model
assignments out of the repository, and give specialists clear capabilities
without losing overall accountability.

# Decision

Adopt one Orchestrator and five specialist subagents for project development:

- `orchestrator` (primary) owns intake, delegation, the acceptance-criteria
  ledger, reconciliation, escalation and the human handover;
- `planner` produces acceptance-criteria-driven plans, architecture impact and
  ADR proposals;
- `reviewer` performs independent plan review and independent code review;
- `implementer` implements the reviewed plan and records evidence;
- `tester` verifies behaviour independently and records reproducible evidence;
- `git-manager` performs branch, commit, push and pull-request preparation after
  the review gates and explicit human approval; merging a pull request is
  reserved for the human user.

The workflow uses:

- project agent definitions in `.opencode/agents/`;
- project configuration in `opencode.jsonc`, including project-wide Git and
  GitHub write restrictions and the shared feedback contract in the
  `instructions` array;
- repository-wide instructions in `AGENTS.md`;
- the structured feedback contract in `docs/workflow/feedback-contract.md`;
- the ADR lifecycle and baseline rules in `docs/adr/README.md`;
- the offline workflow validator in `tools/workflow_check.py`.

Model assignments remain configurable in the global OpenCode configuration or
in optional project overrides. The repository keeps credentials and personal
provider configuration out of version control.

# Consequences

- Every issue has one accountable coordinator and a stable report format.
- Plan review happens before implementation and code review before pull-request
  completion.
- Acceptance-criteria gaps, omitted delegations and unverified claims become
  visible in the ledger instead of being lost in prose.
- Git and GitHub write operations have one responsible agent and are backed by
  permission rules.
- Open pull-request ADRs remain proposals; humans approve architecture changes.
- The workflow adds documentation and validation work, but keeps application
  implementation in later issues.

# Alternatives considered

- A single general-purpose agent. Rejected because independent review and
  verification would be weaker and role boundaries unclear.
- Separate repositories or external orchestration. Rejected because the
  workflow, ADRs and instructions belong with the project and need to be
  reviewed together.
- Automatically merging agent work. Rejected because architecture and
  implementation changes need human approval.

# Links

- Issue: [#30](https://github.com/PeterKopa/multi-agent-model-advisor/issues/30)
- Related ADRs: `ADR-0001`
- Implementation or workflow:
  `docs/workflow/development-workflow.md`,
  `docs/workflow/feedback-contract.md`,
  `docs/workflow/model-assignments.md`,
  `.opencode/agents/`,
  `opencode.jsonc`,
  `AGENTS.md`
- Evidence: `python3 tools/workflow_check.py all` and
  `docs/validation/opencode-v2.4.1-discovery.md`

# Review notes

Introduced with the issue #30 workflow change. The ADR becomes part of the
authoritative baseline when a human approves and merges its pull request.
