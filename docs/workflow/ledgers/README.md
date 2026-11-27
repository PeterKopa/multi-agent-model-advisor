# Acceptance-criteria ledgers

The Orchestrator keeps one ledger per active issue under this directory. The
ledger is the authoritative record of acceptance criteria, delegation,
coverage, evidence, gaps, architecture decisions and unresolved items.

## Naming and lifecycle

- File name: `issue-<number>.md`.
- Create or update the ledger during intake, before the first delegation.
- Record the single writer and write scope for each delegated task before the
  first edit, and update the record at every handover.
- Update it after every report and before the human handover.
- Keep completed ledgers in the repository so that later issues can trace what
  was covered and which evidence was used.
- The Orchestrator is the only workflow agent that writes ledger files. Project
  permissions allow edits under `docs/workflow/ledgers/**` and deny edits
  elsewhere for that role.

## Status values

| Status | Meaning |
| --- | --- |
| `covered` | Satisfied with reproducible evidence |
| `partial` | Partly satisfied or only partly evidenced |
| `unverified` | Work may exist, but the evidence is missing or not reproducible |
| `missing` | Delegated without work or evidence, or never delegated |
| `not applicable` | Does not apply; the reason is recorded |

## Ledger template

```markdown
# Issue <number> — <title>

- Branch:
- Pull request:
- Last updated:
- Human approval:

## Acceptance criteria

| ID | Criterion | Delegated to | Status | Evidence | Gaps / follow-up |
| --- | --- | --- | --- | --- | --- |

## Reports reconciled

| Agent | Task | Status | Received | Key findings |
| --- | --- | --- | --- | --- |

## Architecture baseline

- Accepted baseline:
- Proposals in this pull request:
- Conflicts:
- Decisions needed:

## Unresolved items

## Deferred or out-of-scope work

## Handover

- Plan review:
- Code review:
- Test evidence:
- Human approval:
- Git Manager:
```

## Work-item sizing template

Record the AC-PL1 decision before detailed planning. Weigh the nine factors,
name the independently verifiable outcome and, for a material scope change,
the named-human approval and its reference. No numeric size threshold is a
rule: counts of criteria, files or lines are not entry criteria.

```markdown
### Work item <id>

| Factor | Decision |
| --- | --- |
| Cohesion | |
| Dependencies | |
| Complexity | |
| Architectural impact | |
| Side effects | |
| Testability | |
| Agent context | |
| Coordination overhead | |
| AI/human review effort | |

- Independently verifiable outcome:
- Split recommendation (only for independently verifiable outcomes):
- Material scope change:
- Named-human approval and reference:
```

## Write-ownership record

Record the single writer before the first edit and update the record at each
handover.

| Task | Agent | Write scope | Dependencies | Scratch | May read | Must not touch |
| --- | --- | --- | --- | --- | --- | --- |
| `<task-id>` | `<agent>` | `<paths>` | `<tasks or decisions>` | `.tmp/<task-id>/` | `<paths>` | `<paths>` |

One active writer per file: serialise overlapping writes and pause and hand over
when scopes collide. The Orchestrator writes only the ledger, the Planner only
ADR proposals, the Implementer the implementation, the Reviewer and Tester
nothing and the Git Manager performs Git and GitHub writes. Parallel read-only
analysis is allowed. Actual write obedience and filesystem isolation are
instruction-only limits; the offline validator checks the recorded fields and
synthetic cases only. The rules are in
[`../development-workflow.md`](../development-workflow.md#write-ownership) and
the fixtures in
`docs/validation/fixtures/workflow/ownership/`.

## Release record template

The Orchestrator owns `issue-<number>.release.json` next to the ledger. It is
the live release evidence, never a synthetic fixture. The evaluator and its
exact rules are described in
[`../../validation/README.md`](../../validation/README.md).

```json
{
  "issue": 30,
  "pr_head": "<40-hex final head>",
  "artifact": "<same 40-hex handover commit>",
  "tasks": {"<agent>": "<task-id>"},
  "criteria": [{"id": "AC-01", "title": "…", "delegated_to": ["…"], "required": true}],
  "reports": ["<feedback-contract report objects>"],
  "plan_review": {"state": "passed", "commit": "…", "section_sha256": "…"},
  "ai_code_review": {"state": "passed", "reviewer_type": "ai", "reviewer": "…", "head": "…"},
  "human_review": {"state": "passed", "reviewer_type": "human", "name": "…", "login": "…", "attribution": "human", "independent": true, "provenance": "pr-review", "review_id": "…", "timestamp": "…", "head": "…"},
  "tester_verification": {"state": "passed", "head": "…"},
  "workflow_validator_ci": {"state": "passed", "inspected": true, "head": "…", "base_sha": "…", "continue_on_error": false, "job": "workflow-validator", "run": "…"},
  "decisions": [{"id": "OD-ROLE", "required": true, "state": "resolved", "resolved_by": "…", "rationale": "…", "reference": "…", "head": "…"}],
  "proposals": [{"id": "ADR-0002", "declared_status": "Accepted", "effective_status": "Proposed"}],
  "gaps": []
}
```

`pr_head` and `artifact` are full 40-hex commits and must be equal; there is no
frozen-diff form. Only an inspected `passed` required check is green. A missing
or unusable record is `unavailable` and false.

The CI slot names the `workflow-validator` job of `.github/workflows/ci.yml` and
the `base_sha` that run printed. Only an inspected `passed` run on the reviewed
head fills it; `failed`, `skipped`, `unavailable` and `contributor-reported`
stay blockers, and a verified base SHA is an input to re-running the job for an
inspected pass, never permission to relabel a `SKIP` line. A named human
resolution records identity, rationale, reference and the final head. The
static CI contract check and `jactionlint` prove the workflow shape and syntax
only, so the slot needs the actual run, job, step and log evidence.

## Reconciliation rules

Use the rules in [`../feedback-contract.md`](../feedback-contract.md):

1. Coverage combines evidence from all reports, not only the latest report.
2. `Partial` and `unverified` stay open until follow-up evidence exists.
3. A delegated criterion missing from its agent's report is recorded as a gap
   even when another report covers the criterion.
4. A criterion with no delegation is recorded as a delegation gap.
5. Proposed ADRs and architecture conflicts are recorded as unresolved until a
   human approves them.
6. Follow-up delegation or explicit escalation closes each gap; gaps are not
   silently dropped.
