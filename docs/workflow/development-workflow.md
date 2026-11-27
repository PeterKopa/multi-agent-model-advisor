# Development workflow

This document defines the project-specific OpenCode workflow for the
Multi-Agent Model Advisor. It implements [issue #30](https://github.com/PeterKopa/multi-agent-model-advisor/issues/30)
and is scoped to the development workflow and its supporting documentation.

## Goals

- Deliver issues through small, reviewable changes with explicit acceptance
  criteria and evidence.
- Keep architecture decisions visible, versioned and approved by a human.
- Use specialist agents with clear capabilities while keeping one Orchestrator
  accountable for the whole issue.
- Make every delegated task return a structured report that can be reconciled
  against the acceptance criteria.
- Keep credentials, personal model assignments and private account settings in
  their authorised local locations.

## Roles and boundaries

| Agent | Mode | Primary responsibility | Key capabilities |
| --- | --- | --- | --- |
| `orchestrator` | primary | Intake, delegation, ledger, reconciliation, escalation and handover | Read access, ledger edits under `docs/workflow/ledgers/`, launching the five specialist subagents |
| `planner` | subagent | Acceptance-criteria-driven planning, architecture impact, ADR proposals | Read access and edits under `docs/adr/` |
| `reviewer` | subagent | Independent plan review and independent code review | `edit` denied by its agent rules (`write`/`patch` are named by no rule in this repository); shell remains permission-controlled |
| `implementer` | subagent | Implementation, tests and implementation evidence | Repository edits and local commands |
| `tester` | subagent | Independent verification, test execution and reproducible evidence | `edit` denied by its agent rules (`write`/`patch` are named by no rule in this repository); local command execution |
| `git-manager` | subagent | Branch, commit, push and pull-request preparation after approval; merge stays with the human user | Git and GitHub write operations, except pull-request merge |

The Orchestrator is the only agent that launches subagents. The Reviewer and
Tester work independently of the Implementer. Project-level permission rules in
`opencode.jsonc` implement the permission model below; the agent instructions
describe the positive responsibility of each role.

## Permission model

OpenCode resolves permissions as ordered `{action, resource, effect}` rules and
the **last matching rule wins**. Agent rules from `.opencode/agents/*.md` are
appended after the project rules from `opencode.jsonc`, so an agent can refine
the project policy for its own role and a later project denial can only be
overturned by a later agent allow. Effects are `deny` (blocked without
approval), `ask` (the operator must approve) and `allow`. The project policy
reads in that order: deny → allow → ask → deny.

Shell permission checks use OpenCode's built-in shell scanner across Bash,
Zsh, POSIX sh and PowerShell (see the "Scanner" section of
<https://opencode.ai/docs/permissions>). The `shell` resource is the
scanner-produced command string, and a compound command may produce several:
permission rules, saved approval patterns and best-effort directory inference
apply to every extracted subcommand and `cd` target. A command the scanner
cannot analyse fails when any shell deny rule applies to it and otherwise
requires approval for the whole command, which keeps unanalysable input
fail-closed. The offline validator mirrors this model by splitting its samples
on the top-level separators `&&`, `||`, `;`, `|` and newlines and resolving
each subcommand; separators inside quoted wrapper arguments do not split.

- **Git and GitHub by default.** `git *`, `gh *`, `rtk git *` and `rtk gh *` are
  denied first. Read-only inspection (status, diff, log, show, rev-parse,
  rev-list, ls-files, ls-tree, blame, grep, describe, shortlog, merge-base,
  and the read-only `gh` subcommands) is re-enabled in both plain and RTK
  form. Plain `ls` is an explicitly allowed read-only convenience and `cat` is
  approval-gated (`ask`); the credential shell mirrors further down still win
  by last-match, so neither can reach a denied path. The Git Manager
  appends allow rules for the write commands it owns — including the RTK
  mirrors `rtk git add/branch/checkout/commit/push/switch` and
  `rtk gh pr create` — and repeats the protected denials **after** its allows so
  they win for that agent. Destructive git allows (reset, clean, rebase,
  merge, tag, submodule) are deliberately not mirrored to RTK.
- **Human-only merge enforcement.** `gh api*` and `gh pr merge*` are denied
  project-wide and again as the Git Manager's last rules; merging a pull
  request is reserved for the human user. Direct pushes to `main` —
  `git push <remote> main`, `git push <remote> HEAD:main` and
  `git push <remote> HEAD:refs/heads/main`, plus their RTK forms — are denied
  for every agent. Pushes are controlled by an allowlist instead of a deny
  category: the Git Manager's single push allow is `git push origin ?*`
  (with the RTK mirror `rtk git push origin ?*`), where the `?` matches
  exactly one character, so the allow requires a non-empty refspec after the
  remote and the handover shape —
  `git push origin <branch>` or `git push origin HEAD`, an explicit origin
  refspec every time — is the only push that passes for that agent. Any push
  that does not name `origin` with a non-empty refspec — another remote name
  (`git push upstream`, `git push github`), a bare `git push`, or a
  remote-only `git push origin` (with or without a trailing space) whose
  implicit refspec can resolve to a
  configured upstream (which can be `main`) — matches no Git Manager allow
  and falls back to the project-level `git *` deny. Because the Git Manager's
  own allows can override every project deny, its final rules re-create the
  second deny layer: every option-bearing push (`git push -*` and
  `git push * -*`, plain and RTK — any argument that starts with `-`,
  wherever it sits after the verb) is denied, which subsumes all force
  spellings (`--force`, `--force-with-lease` and any short or clustered form
  such as `-uf` or `-uvqf`), `--mirror`, `--all`, `--delete` and its short
  `-d`, and the quiet or dry-run options (`-q`, `--quiet`, `--dry-run`,
  `--follow-tags`); and the blanket `+` and ` :` rules deny a `+`-prefixed
  refname in any position and a delete refspec with or without a remote — a
  legal refname holding a plus sign is denied by the same side effect.
  Because the shell
  scanner evaluates every
  extracted subcommand, these protected operations deny in direct and
  compound invocations: `git fetch origin && gh pr merge 1` denies on the
  second subcommand even though the first is a legitimate Git Manager
  operation.
- **Defence in depth for hidden writes.** `*git add *`, `*git commit *`,
  `*git push *`, `*git merge *`, `*git rebase *`, `*git reset *`,
  `*gh pr create*`, `*gh pr merge*` and `*gh api *` are denied in every
  scanner-produced command string, so writes cannot hide behind a wrapper or
  inside a quoted argument such as `rtk test "jactionlint && git push origin
  main"`, whose quoted payload stays one command string and matches the deny.
  The narrow quality-tool allows sit before those denials, so a compound that
  also contains a write still resolves to deny.
- **RTK mirroring.** RTK condenses output but can also hide the executed
  command. `rtk git`/`rtk gh` mirror the plain rules one-to-one; the RTK file
  and report tools (`rtk read`, `rtk smart`, `rtk grep`, `rtk rg`,
  `rtk ast-grep`, `rtk find`, `rtk ls`, `rtk tree`, `rtk wc`, `rtk diff`,
  `rtk log`, `rtk json`, `rtk deps`, `rtk gain`, `rtk methods`) are allowed.
  `rtk test`, `rtk err` and `rtk summary` execute hidden commands and are
  denied, except the three narrow Go quality-tool filters
  (`rtk test *govulncheck*`, `rtk test *golangci-lint*`,
  `rtk test *jactionlint*`); `rtk bypass` and `rtk proxy` ask.
- **Go quality toolchain.** `go`, `govulncheck`, `golangci-lint` and
  `jactionlint` are allowed directly so quality checks run without approval.
  Filtered runs are allowed only through the narrow `rtk test` patterns above;
  every other `rtk test` invocation stays denied, and a compound command that
  also contains a write still resolves to deny.
- **Ask rules.** Infrastructure, cluster, cloud, database and network tools
  (`docker`, `kubectl`, `oc`, `aws`, `psql`, `wget`, and their RTK mirrors) ask
  for approval. Toolchains the project does not use (`pnpm`, `dotnet`, and
  their RTK mirrors) are denied.
- **Path policy.** Credential and secret locations — `~/.ssh/`, `~/.aws/`,
  `~/.gnupg/`, `~/.config/gh/`, `~/.kube/`, `~/.docker/config.json`, `~/.netrc`,
  `~/.git-credentials`, `~/.npmrc`, `~/.pypirc`,
  `~/.local/share/opencode/auth.json`, the OpenCode database and logs, and
  `~/Library/Keychains/` — are denied for `read`, `edit` and
  `external_directory`, and the same locations are denied inside shell command
  strings through leading-wildcard mirrors. The `external_directory` gate asks
  for approval before anything outside the worktree is touched and then denies
  the credential locations, so paths outside the worktree always require
  approval. Every `*.env` and `*.env.*` file is denied for read and edit except
  an `.env.example` or `*.env.example` template, if present.
  `~/.config/opencode/*` stays local and is readable, editable and reachable
  from shell command arguments on approval only.
- **Scratch convention.** Paths outside the worktree require approval, so
  scratch copies and mutation tests belong under `.tmp/` inside the worktree
  and must be removed afterwards; `.tmp/` is listed in `.gitignore`.
- **Guardrail, not sandbox.** The permission model is a command-level
  guardrail, not a sandbox. It denies and asks on the listed paths and
  command forms, while a shell command that matches no rule resolves to
  `allow` by design in OpenCode. The explicit `ls` and `cat` rules document
  intent within that model, they do not close it; `echo` is deliberately
  unnamed as a convenience because it is a write primitive through `>` and
  `>>`. The Go quality toolchain is allowed directly for every agent, and
  tools or MCP servers inherited from the operator's global configuration sit
  outside this per-role boundary. Role discipline, the review gates and the
  human-approved handover remain part of the control set, and repository-side
  branch protection plus a per-role tool and MCP lockdown are open decisions
  escalated to the human owner.

The offline validator in `tools/workflow_check.py` resolves the full combined
rule set for every agent with last-match-wins semantics and asserts these
effects, including the deny rules that must stay last in the Git Manager
frontmatter. For compound samples it splits the command on the top-level
separators `&&`, `||`, `;`, `|` and newlines, resolves each subcommand and
combines the results as any deny → deny, else any ask → ask, best-effort
mirroring the scanner model above. `.opencode/agents/*.md` must contain exactly
the six workflow agents, each with a `mode`, no `action: "*"` allow rule and —
outside the Git Manager — no allow rule for any action other than `edit` and
`subagent`.

## Configuration layout and discovery

The workflow was verified with OpenCode **v2.4.1** from the repository root.
See [`docs/validation/opencode-v2.4.1-discovery.md`](../validation/opencode-v2.4.1-discovery.md)
for the recorded commands and output.

| Path | Purpose | Loading behaviour |
| --- | --- | --- |
| `opencode.jsonc` | Project configuration: default agent, shared instructions and project-wide Git write restrictions | Discovered from the workspace and its ancestors; project values override only the fields they define |
| `.opencode/agents/*.md` | The six agent definitions | Discovered automatically; the file name becomes the agent ID, and frontmatter merges with any global entry that has the same ID |
| `AGENTS.md` | Repository-wide shared instructions | Loaded automatically for every session, after the global instructions |
| `docs/workflow/feedback-contract.md` | Shared feedback contract | Added to every session through the `instructions` array in `opencode.jsonc` |
| `docs/adr/` | Architecture Decision Records | Discovered by convention and referenced by the workflow; not loaded as instructions |

OpenCode searches for project configuration from the current directory upwards.
For a workspace inside this repository, the project configuration and
`.opencode/agents/` definitions apply in addition to the global configuration.
The project configuration does not replace global settings that it does not
mention. Personal model assignments therefore remain in the global
configuration, and the repository configuration keeps only shared workflow
settings. See [`model-assignments.md`](model-assignments.md).

The discovered agent IDs are `orchestrator`, `planner`, `reviewer`,
`implementer`, `tester` and `git-manager`. Agent definitions are reloaded when
the files change; a restart is not required for normal edits.

## Workflow stages

### 1. Intake and baseline check

The Orchestrator reads the issue, its dependencies, the acceptance criteria and
the relevant accepted ADRs. It creates or updates the ledger under
`docs/workflow/ledgers/` and records every criterion before delegating work.
New or modified ADRs in an open pull request are proposals and do not change
the baseline.

### 2. Planning

The Orchestrator sends the Planner a delegation packet. The Planner returns a
plan that maps each criterion to concrete work, affected areas, evidence, risks,
dependencies and ADR impact. When an architecture decision is needed, the
Planner drafts an ADR proposal in `docs/adr/` and links it to the issue.

### 3. Independent plan review

The Reviewer reviews the plan independently before implementation starts. The
review checks coverage, feasibility, risks, test strategy and ADR alignment.
The Orchestrator records required changes and asks the Planner to revise the
plan when needed.

### 4. Implementation and verification

The Implementer implements the reviewed plan and records changed files and local
evidence. The Tester derives checks from the acceptance criteria, runs the
relevant validation and reports reproducible evidence. The Tester does not edit
the repository; failures return to the Implementer through the Orchestrator.

### 5. Independent code review

The Reviewer reviews the final diff, the test evidence and the ADR status. Code
review happens before a pull request is completed. Findings are ordered by
severity and include file or line references, impact and a concrete action.
Review status is `Completed`, `Partial`, `Blocked` or `Needs Decision`.

### 6. Reconciliation and escalation

The Orchestrator reconciles every report against the ledger. It combines
coverage from all reports, records missing evidence and looks for criteria that
were omitted from a delegation or from a report. Gaps receive targeted
follow-up delegation. Architecture conflicts and pending decisions are
escalated for explicit human approval and recorded as unresolved items.

### 7. Human-approved handover

After the plan review, code review and test evidence are confirmed, the
Orchestrator asks a human to approve the handover. The Git Manager then prepares
a focused branch, commit and pull request. The pull request describes the issue,
covered criteria, ADR status, validation evidence, review status, unresolved
items and the approval step. A human reviews and merges the pull request;
merging is reserved for the human user, and agents do not merge architecture or
implementation changes on their own.

## Delegation packet

A delegation packet contains:

- issue number, title and acceptance criteria relevant to the task;
- the accepted ADR baseline and any proposal relevant to the task;
- affected files or areas and repository constraints;
- expected evidence, checks and report format;
- adjacent responsibilities and the agent that owns them;
- known dependencies, assumptions and deferred scope.

Delegation packets are explicit enough that the receiving agent can act without
reconstructing the whole issue. The Orchestrator retains the full ledger even
when a packet contains only a subset of criteria.

## Shared feedback contract

Every subagent returns the structured report defined in
[`feedback-contract.md`](feedback-contract.md). The report covers status,
completed work, acceptance-criteria coverage and evidence, missing or unverified
requirements, findings, assumptions, dependencies, ADR alignment, recommended
next actions and constructive feedback on the delegation and collaboration.

The Orchestrator records every report in the ledger and reconciles coverage from
all reports. A report that omits a delegated criterion is not treated as
complete; it creates a coverage gap that is resolved by follow-up delegation or
explicit escalation.

## Architecture Decision Records

The ADR lifecycle is defined in [`docs/adr/README.md`](../adr/README.md). In
short:

- the authoritative baseline is the set of **Accepted** ADRs merged into the
  default branch;
- ADRs in an open pull request are proposals regardless of their declared
  status, and the previous accepted baseline remains in force;
- Accepted ADRs are explicitly approved by a human and merged into the default
  branch;
- conflicts and pending decisions are escalated instead of being resolved
  silently;
- ADRs link to their issue and to implementation decisions, and each agent
  reports its alignment with the baseline.

## Validation

The workflow is validated offline with fixtures and synthetic reports. Run the
validator audit first, then the validator itself:

```bash
python3 tools/audit_validator.py
python3 tools/workflow_check.py all
```

`all` audits the validator statically with `tools/audit_validator.py` before it
runs any check, so its results are only trusted when the audit passes. The
audit and the validator are guardrails, not sandboxes.

The validator checks agent configuration and discovery prerequisites, ADR
baseline handling in an open pull-request scenario, and feedback reconciliation
with an intentionally omitted acceptance criterion, an unverified criterion and
a proposed ADR that conflicts with the accepted baseline. No network access or
credentials are required. See [`docs/validation/README.md`](../validation/README.md).

## Deferred scope

Application implementation (#27–#29), additional specialist agents, automatic
model selection, live benchmark execution and advanced workflow automation are
outside this workflow issue. Live inference remains subject to the existing
approval and capability gates.
