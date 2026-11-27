# Delegation packet

This document is the normative definition of a delegation packet. The
Orchestrator sends one packet per delegated task. The workflow document, the
shared instructions and the agent prompts link to this page instead of
restating its rules.

## Required fields

Every packet carries the fields below. `validate_delegation_packet()` in
`tools/workflow_check.py` rejects a packet that omits a required field, and the
positive control lives in
`docs/validation/fixtures/workflow/planning/delegation-packet.json`.

| Field | Content |
| --- | --- |
| **Task identity** | `task_id`, issue number and target agent. Every report, evidence item and ownership record uses the same task identity. |
| **Criteria** | The acceptance criteria delegated to the task, with their IDs and coverage target. The Orchestrator keeps the full ledger even when a packet carries a subset. |
| **ADR baseline and proposals** | The accepted ADR baseline governing the task and the proposals relevant to it. A proposal in an open pull request never enters the baseline. |
| **Repository context** | The files, areas, patterns and existing behaviour the task needs. Prefer a concise pointer to repository paths over a pasted copy. |
| **Dependencies** | Inputs, decisions, agents or external conditions the task needs, with the owner, including the reviewed artefact it builds on. |
| **Constraints** | Boundaries such as offline-only checks, out-of-scope files, permission limits and the reviewed artefact. |
| **Expected evidence** | The checks, commands, fixtures or artefacts the report must contain. |
| **Reviewed artifact** | `reviewed_artifact`: the reviewed commit or frozen diff the task binds to. |
| **Write ownership** | The responsible agent, task, affected files, dependencies and write scope, recorded before work starts. Read-only tasks state an empty write scope. |

## Context efficiency

Prefer a concise, sufficient packet over a complete issue dump. Include the
repository context that the receiving agent cannot reconstruct cheaply and
point to paths instead of paraphrasing them. Keep the packet focused on the
delegated task and record context assumptions explicitly.

Concision, context sufficiency and requesting missing context before a
consequential decision are instruction and human-judgement rules. The validator
checks that the required fields are present; it does not prove that the content
is concise or sufficient, and it cannot prove that an agent actually asked for
missing context. A receiver that lacks context asks the Orchestrator instead of
assuming, and the Orchestrator records the answer in the packet or the ledger.

## Write ownership

Record the owner before work starts: responsible agent, task identity, affected
files, dependencies and write scope. Serialise overlapping writes and pause and
hand over when scopes collide. The Orchestrator is the sole ledger writer, the
Implementer owns implementation changes, the Planner owns ADR proposals, the
Reviewer and Tester stay read-only and Git and GitHub writes stay with the Git
Manager. Parallel read-only analysis is allowed. Scratch work lives in
`.tmp/<task-id>/` and is removed before the task reports back.

The ownership record and its release counterpart are templated in
[`ledgers/README.md`](ledgers/README.md); the policy and its limits are stated
in [`development-workflow.md`](development-workflow.md#write-ownership).
`validate_write_ownership()` and the fixtures under
`docs/validation/fixtures/workflow/ownership/` prove the disjoint, overlapping,
handover, stale and read-only cases. Actual write obedience and filesystem
isolation are instruction-only limits: the offline validator checks the
recorded ownership fields and synthetic cases, not which files an agent really
opened.

## Report format

The receiving agent reports per the shared
[`feedback-contract.md`](feedback-contract.md), including actual model and
provider provenance, the `reviewed_artifact`, acceptance-criteria coverage,
evidence, missing requirements, findings, assumptions, dependencies, ADR
alignment, recommended next actions and feedback on the packet.
