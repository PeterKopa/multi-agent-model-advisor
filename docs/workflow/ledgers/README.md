# Acceptance-criteria ledgers

The Orchestrator keeps one ledger per active issue under this directory. The
ledger is the authoritative record of acceptance criteria, delegation,
coverage, evidence, gaps, architecture decisions and unresolved items.

## Naming and lifecycle

- File name: `issue-<number>.md`.
- Create or update the ledger during intake, before the first delegation.
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
