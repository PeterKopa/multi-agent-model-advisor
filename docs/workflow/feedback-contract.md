# Shared feedback contract

This contract applies to every subagent and every delegated task. It is loaded
into every session through `opencode.jsonc`. Reports are structured so the
Orchestrator can reconcile them against the acceptance-criteria ledger without
reconstructing the work from prose.

## Required report fields

| Field | Required | Content |
| --- | --- | --- |
| `agent` | yes | Agent ID that produced the report |
| `issue` | yes | Issue number this report belongs to |
| `task_id` | yes | Stable identifier for the delegated task |
| `status` | yes | `Completed`, `Partial`, `Blocked` or `Needs Decision` |
| `completed_work` | yes | Concise list of work actually completed, with file or command references |
| `acceptance_criteria_coverage` | yes | One entry per delegated criterion, with coverage and evidence; explicitly list delegated criteria that were not covered |
| `missing_requirements` | yes | Missing, skipped, deferred or unverified requirements, including the reason |
| `findings` | yes | Correctness, risk, architecture, privacy, security or usability findings, ordered by severity |
| `assumptions` | yes | Assumptions that affected the work or its evidence |
| `dependencies` | yes | Inputs, decisions, agents or external conditions needed for follow-up work |
| `adr_alignment` | yes | Accepted baseline references, proposals, conflicts and decisions needed |
| `recommended_next_actions` | yes | Targeted, actionable follow-ups with the responsible agent |
| `feedback` | yes | Constructive feedback on delegation, planning, instructions and collaboration |

When a field has no content, return an explicit empty list or `none` with a
short reason. An omitted field is a contract violation and is treated as an
unverified report.

## Status values

| Status | Meaning |
| --- | --- |
| `Completed` | The delegated work and its evidence are complete; any open items are outside the delegation |
| `Partial` | Useful work is complete, but at least one delegated requirement or evidence item is still open |
| `Blocked` | Work cannot continue without an input, dependency, access or decision |
| `Needs Decision` | Work is paused because an architecture, product, privacy or scope decision needs explicit human approval |

`Completed` does not mean that every acceptance criterion of the issue is
covered; it means the delegated task is covered. The Orchestrator reconciles
across reports.

## Acceptance-criteria coverage

Each coverage entry uses this shape:

```json
{
  "criterion_id": "AC-03",
  "coverage": "covered",
  "evidence": ["docs/adr/README.md", "python3 tools/workflow_check.py adr"],
  "notes": "Lifecycle and baseline rules documented and validated."
}
```

| Coverage | Meaning |
| --- | --- |
| `covered` | The criterion is satisfied and the evidence is reproducible |
| `partial` | Part of the criterion is satisfied, or the evidence covers only part of it |
| `unverified` | Work may exist, but the evidence is missing, stale or not reproducible |
| `missing` | The criterion was delegated but no work or evidence exists |
| `not_applicable` | The criterion does not apply to this task; explain why |

Use `missing` and `not_applicable` explicitly instead of omitting the entry.

## Evidence

Evidence is concrete and reproducible: file paths, commands, exit codes,
relevant output excerpts, test names, commit or pull-request references and
links to issues or ADRs. Summaries without evidence are supporting context, not
proof of coverage. For offline checks, state that no network access or
credentials were required.

## ADR alignment

Report:

- `baseline`: accepted ADR IDs and titles that governed the work;
- `proposals`: ADR IDs in the current open pull request or working tree,
  including their declared and effective status;
- `conflicts`: conflicts with the accepted baseline, with the affected decision;
- `decision_needed`: decisions that require explicit human approval.

A new or modified ADR in an open pull request is a proposal even when its
frontmatter declares `Accepted`. The previously accepted baseline stays in
force until the pull request is approved and merged.

## Constructive feedback

Feedback covers the collaboration, not only the artifact. Address:

- delegation: clarity, scope, context and acceptance criteria;
- planning: sequencing, risk identification and test strategy;
- instructions: missing or ambiguous guidance;
- collaboration: handoffs, dependencies and communication.

Prefer specific, actionable observations. Name what worked and what would make
the next iteration easier. Keep feedback respectful and focused on improving the
workflow.

## Orchestrator reconciliation

The Orchestrator maintains a ledger with:

- every acceptance criterion and its delegated agent;
- the combined coverage from all reports, with evidence links;
- gaps caused by missing work, missing evidence, an omitted criterion or a
  criterion that was never delegated;
- architecture proposals, conflicts and pending decisions;
- follow-up delegations and their status;
- unresolved items, assumptions and the human-approval state before handover.

Reconciliation rules:

1. A criterion is covered only when at least one report provides reproducible
   evidence that satisfies it.
2. `Partial` and `unverified` remain open until follow-up evidence is available.
3. A criterion delegated to an agent but absent from that agent's report is
   recorded as a delegation/report gap, even when another report covers it.
4. A criterion with no delegation is recorded as a delegation gap.
5. A proposed ADR or an architecture conflict is escalated and recorded as an
   unresolved decision until a human approves it.
6. Unresolved items are recorded before handover; they are not silently dropped.

## Report template

```markdown
## Agent report

- agent:
- issue:
- task_id:
- status:

### Completed work

### Acceptance-criteria coverage

| Criterion | Coverage | Evidence | Notes |
| --- | --- | --- | --- |

### Missing, skipped, deferred or unverified requirements

### Findings

### Assumptions

### Dependencies

### ADR alignment

- baseline:
- proposals:
- conflicts:
- decision needed:

### Recommended next actions

### Feedback on delegation and collaboration
```
