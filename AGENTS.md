# Multi-Agent Model Advisor — shared development instructions

This repository uses a project-specific OpenCode workflow with one Orchestrator
and five specialist subagents. The complete workflow is documented in
[`docs/workflow/development-workflow.md`](docs/workflow/development-workflow.md).
The shared feedback contract in
[`docs/workflow/feedback-contract.md`](docs/workflow/feedback-contract.md) is
loaded into every agent through `opencode.jsonc`.

## Working agreements

- Start from the issue and its acceptance criteria. Record each criterion in the
  Orchestrator's coverage ledger before delegating work.
- Map every delegated task to one or more acceptance criteria and share the
  relevant context, constraints and expected evidence in the delegation packet.
- Return a structured report for every delegated task using the shared feedback
  contract. Include completed work, acceptance-criteria coverage, missing or
  unverified requirements, findings, assumptions, dependencies, ADR alignment
  and recommended next actions.
- Include constructive feedback on delegation, planning, instructions and
  collaboration. Prefer specific, actionable observations over general praise
  or blame.
- Ask for independent plan review before implementation starts and independent
  code review before a pull request is completed.
- Reconcile every report in the Orchestrator ledger. Identify criteria that were
  omitted from delegation or from a report, and resolve them with targeted
  follow-up work or explicit escalation.
- Keep deliverables focused on the current issue. Record deferred work and
  unresolved items instead of silently expanding scope.

## Architecture baseline

- The authoritative architecture baseline is the set of **Accepted** ADRs that
  are merged into the default branch. See
  [`docs/adr/README.md`](docs/adr/README.md).
- Treat new or modified ADRs in an open pull request as proposals regardless of
  their declared status. Keep the previously accepted baseline until a human
  explicitly approves the pull request and it is merged.
- Link ADRs to the relevant issue and to implementation decisions. Preserve
  existing accepted requirements.
- Escalate architecture conflicts and pending decisions to a human. Record the
  open question, affected options and the consequence of waiting.

## Quality gates

1. The Planner produces a plan with acceptance-criteria coverage and ADR impact.
2. The Reviewer performs an independent plan review.
3. The Implementer implements the reviewed plan and records evidence.
4. The Tester verifies behaviour and records reproducible evidence.
5. The Reviewer performs an independent code review of the final diff.
6. The Orchestrator reconciles the ledger and records remaining gaps.
7. The Git Manager prepares the branch, commits and pull request after the
   Orchestrator confirms the gates and a human approves the handover. Merging a
   pull request is reserved for the human user.

## Repository and data rules

- Keep credentials, personal provider configuration and private account details
  in their authorised local locations. Repository files contain placeholders,
  model-agnostic defaults and non-secret configuration only.
- Read and write only the locations the permission policy approves. Credential
  and secret stores stay untouched because the permission policy denies file
  access to `~/.ssh/`, `~/.aws/`, `~/.gnupg/`, `~/.config/gh/`,
  `~/.local/share/opencode/auth.json` and every `*.env` / `*.env.*` file, and
  mirrors the same locations in shell command strings; an `.env.example` or
  `*.env.example` template, if present, is the approved exception — readable
  for every role, and editable by the role that may edit files (the
  Implementer; every other role denies `edit` in its own agent rules).
- Keep all file writes inside the active worktree. Work outside the worktree is
  available on approval: paths outside the active worktree resolve to `ask` for
  the `external_directory` gate and for RTK commands, and `~/.config/opencode/*`
  stays local and is readable, editable and reachable from shell command
  arguments on approval only.
- Treat `.tmp/` inside the worktree as the approved scratch location and remove
  its contents before the task reports back. Keep test material inside the
  worktree so every path the task touches stays inside the approved boundary.
- Use RTK for output condensing as a permission-mirroring convenience:
  `rtk git ...` and `rtk gh ...` mirror the plain `git`/`gh` rules one-to-one
  and the RTK file and report tools are allowed. The plain `go` commands and
  the narrowly filtered quality runs (`rtk test` wrapping `govulncheck`,
  `golangci-lint` or `jactionlint`, with the nested-write denials still
  winning) are the approved filtered paths; `rtk test`, `rtk err` and
  `rtk summary` execute hidden commands and stay denied, while `rtk bypass`
  and `rtk proxy` remain escape hatches that require approval.
- Use the Go quality toolchain directly: `go`, `govulncheck`, `golangci-lint`
  and `jactionlint`. Infrastructure, cluster, cloud, database and network tools
  (`docker`, `kubectl`, `oc`, `aws`, `psql`, `wget`, and their RTK mirrors) run
  on approval, and `pnpm`, `dotnet` and their RTK mirrors stay outside the
  approved set.
- Treat pull-request merging as the human user's responsibility. The approved
  handover is: the Git Manager prepares branch, commits and pull request after
  the Orchestrator confirms the gates and the human approves; the human merges.
  `gh api` and `gh pr merge` stay denied for every agent, and direct pushes to
  `main` are denied even for the Git Manager. Pushes are controlled by an
  allowlist, not a deny category: the Git Manager may push only
  `git push origin <refspec>` (or `git push origin HEAD`), in plain and RTK
  form — there is no push to another remote name, and any push without an
  explicit refspec does not match the allow and falls back to the project-level
  `git *` deny instead of a bare or remote-only allow. Because the Git
  Manager's own allows can override every project deny, its rules re-create
  the second deny layer: every option-bearing push — any argument starting
  with `-`, so no force spelling, `--mirror`, `--all`, `--delete`, `-u`,
  `--follow-tags`, `--quiet` or `--dry-run` in any position — is re-denied
  after the allow; a `+`-prefixed refname is denied as a side effect of the
  `+` blanket rule.
- Use project configuration for shared workflow settings and keep personal model
  assignments in the global OpenCode configuration. See
  [`docs/workflow/model-assignments.md`](docs/workflow/model-assignments.md).
- Prefer offline, deterministic checks for workflow validation, and run them in
  the trusted order without network access or credentials:
  `python3 tools/audit_validator.py` and then
  `python3 tools/workflow_check.py all`.
- Keep German and English user-facing product terminology consistent with the
  existing documentation. Workflow and engineering documentation stays in
  English.

The permission model in `opencode.jsonc` is a guardrail with default-allow,
not a sandbox: named denies and approval gates bound the listed commands and
paths, while role discipline, the review gates and the human-approved handover
complete the control set. Report an observed guardrail gap to the human owner
and escalate it in the ledger instead of working around it.
