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
| `reviewer` | subagent | Independent plan review and independent code review | Edit/write/patch tools denied; shell remains permission-controlled |
| `implementer` | subagent | Implementation, tests and implementation evidence | Repository edits and local commands |
| `tester` | subagent | Independent verification, test execution and reproducible evidence | Edit/write/patch tools denied; local command execution |
| `git-manager` | subagent | Branch, commit, push and pull-request preparation after approval; merge stays with the human user | Git and GitHub write operations, except pull-request merge |

The Orchestrator is the only agent that launches subagents. The Reviewer and
Tester work independently of the Implementer. Project-level permission rules in
`opencode.jsonc` deny Git and GitHub commands by default, re-enable read-only
inspection, and reserve write operations for the Git Manager, which appends its
own allow rules in `.opencode/agents/git-manager.md`. Technical restrictions are
enforced with permissions; the agent instructions describe the positive
responsibility of each role.

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

The workflow is validated offline with fixtures and synthetic reports:

```bash
python3 tools/workflow_check.py all
```

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
