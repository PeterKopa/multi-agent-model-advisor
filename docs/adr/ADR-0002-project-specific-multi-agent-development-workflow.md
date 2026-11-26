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
- a project-wide, ordered permission policy in `opencode.jsonc` in which the
  last matching rule wins;
- repository-wide instructions in `AGENTS.md`;
- the structured feedback contract in `docs/workflow/feedback-contract.md`;
- the ADR lifecycle and baseline rules in `docs/adr/README.md`;
- the offline workflow validator in `tools/workflow_check.py`.

The permission policy implements four standing rules:

- **RTK-aware command boundaries.** Git and GitHub are denied first, and
  read-only inspection is re-enabled in plain and RTK form (`rtk git`,
  `rtk gh` mirror the plain rules). The RTK file and report tools are allowed
  for output condensing; `rtk test`, `rtk err` and `rtk summary` execute hidden
  commands and are denied except for the narrow Go quality-tool filters
  (`rtk test *govulncheck*`, `rtk test *golangci-lint*`,
  `rtk test *jactionlint*`), while `rtk bypass` and `rtk proxy` ask. Nested
  write commands (`*git add *`, `*git commit *`, `*git push *`, `*gh pr
  create*`, `*gh api *`, and similar) are denied wherever they appear in a
  command string, so wrappers and compound commands cannot smuggle writes past
  the role boundaries.
- **Credential-path denials.** Credential stores and secret files — including
  `~/.ssh/`, `~/.aws/`, `~/.gnupg/`, `~/.config/gh/`, `~/.kube/`,
  `~/.docker/config.json`, `~/.netrc`, `~/.git-credentials`, `~/.npmrc`,
  `~/.pypirc`, the OpenCode authentication database and logs, and
  `~/Library/Keychains/` — are denied for `read`, `edit` and
  `external_directory`, and the same locations are denied inside shell command
  strings. Every `*.env` file is denied except the committed `.env.example`;
  `~/.config/opencode/*` stays local and is used on approval only.
- **External-path approval.** The `external_directory` gate asks for approval
  before anything outside the worktree is accessed, and RTK commands that
  reference home or parent-directory paths ask as well. Scratch work therefore
  belongs under `.tmp/` inside the worktree.
- **Human-only merge enforcement.** `gh api` and `gh pr merge` are denied
  project-wide, and pushes to `main` are denied even for the Git Manager, so
  the human-only merge decision from the alternatives below is enforced by the
  permission layer and not only by instruction.

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
  permission rules; the rules are RTK-aware so the proxy cannot bypass them.
- Credential stores, secret files and paths outside the worktree are protected
  at the permission layer and cannot be reached through file tools or plain
  shell command strings.
- `gh api` and pull-request merges are denied for every agent and pushes to
  `main` are denied even for the Git Manager, making the human-only merge
  decision technically enforced.
- Open pull-request ADRs remain proposals; humans approve architecture changes.
- The workflow adds documentation and validation work, but keeps application
  implementation in later issues.

# Residual risks

The following residuals of the permission model were reviewed and are accepted:

- **Git Manager compound commands.** Because agent rules are appended after the
  project rules and the last matching rule wins, a compound shell command that
  starts with a Git verb the Git Manager may run stays allowed for that agent.
  Protected operations still resolve to `deny` at the end of the rule chain:
  `gh api`, pull-request merges, and pushes to `main` or `refs/heads/main`.
  The risk is accepted; the alternative would be to deny all compound
  commands, which would remove legitimate chained Git operations.
- **Plain shell paths outside the worktree.** A general path rule for non-RTK
  shell commands is intentionally not part of the policy, because absolute
  paths inside the worktree also resolve under the home directory and a broad
  rule would ask on every routine command. Credential locations remain denied,
  and RTK commands plus the read/edit file tools require approval outside the
  worktree. The risk is accepted and documented.
- **Minor friction.** The `rtk * ~*` approval rule also fires on tilde
  revisions such as `rtk git show HEAD~1`; this is an approval prompt, not a
  silent allow, and is accepted.

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
authoritative baseline when a human approves and merges its pull request. The
permission model in the Decision (RTK mirroring, credential-path denials,
external-path approval, human-only merge enforcement) was extended while this
pull request is open; the whole record remains a proposal until that approval.
The residual risks recorded under "Residual risks" were reviewed and explicitly
accepted by the human owner while the pull request is open.
