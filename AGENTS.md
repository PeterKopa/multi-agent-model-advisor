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
- Use project configuration for shared workflow settings and keep personal model
  assignments in the global OpenCode configuration. See
  [`docs/workflow/model-assignments.md`](docs/workflow/model-assignments.md).
- Prefer offline, deterministic checks for workflow validation. The workflow
  validator runs without network access or credentials:
  `python3 tools/workflow_check.py all`.
- Keep German and English user-facing product terminology consistent with the
  existing documentation. Workflow and engineering documentation stays in
  English.
