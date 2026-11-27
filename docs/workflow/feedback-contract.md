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
| `model` | yes | Actual model identity that produced the report; write `unknown` explicitly when it cannot be determined |
| `provider` | yes | Actual provider identity that served the model; write `unknown` explicitly when it cannot be determined |
| `thinking` | no | Optional thinking configuration (for example a budget or effort setting); omit it when unused and write `unknown` when it is used but cannot be determined |
| `reviewed_artifact` | yes | The commit or frozen-diff identifier the report's evidence was produced against |
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

## Model and provider provenance

`model` and `provider` are required and record the identity that actually
produced the report. Use the explicit sentinel `unknown` when the identity
cannot be determined; a blank value is rejected because it looks like
provenance without being reproducible. `thinking` is optional: omit it when no
thinking configuration was used, and record `unknown` when it was used but the
configuration cannot be observed.

Privacy limits the field: record the provider and model identifiers, not
credentials, endpoints, account details or personal configuration. Personal
model assignments stay in the operator's global configuration, and reasoning
traces stay out of repository reports. Actual identity truth and the absence
of reasoning traces are inspected by the Reviewer; they are not proven by the
validator.

## Evidence

Evidence is concrete and reproducible: file paths, commands, exit codes,
relevant output excerpts, test names, commit or pull-request references and
links to issues or ADRs. Summaries without evidence are supporting context, not
proof of coverage. For offline checks, state that no network access or
credentials were required.

Evidence entries may be strings or structured objects:

```json
{
  "criterion_id": "AC-03",
  "coverage": "covered",
  "evidence": [
    "python3 tools/workflow_check.py ci",
    {
      "artifact": "docs/adr/README.md",
      "check_state": "passed",
      "criterion_id": "AC-03",
      "task_id": "issue-30-adr"
    }
  ],
  "notes": "Lifecycle and baseline rules documented and validated."
}
```

A `covered` claim requires at least one content-bearing entry and every
structured entry must record `check_state: passed`; an absent state is not
green and is named as the criterion-prefixed gap `AC-04:evidence:missing:<agent>`
together with the `follow_up` gap. The required-check state taxonomy is exactly
`passed`, `failed`, `skipped`, `unavailable` and `contributor-reported`; only
`passed` is green, and the required CI check additionally needs `inspected: true`.
Any other value — including `blocked` — is never green: it keeps the claim open
and is named as the criterion-prefixed gap `AC-04:evidence:<state>:<agent>`.
Missing, vacuous-sentinel, stale,
blocked, failed, skipped, unavailable, contributor-reported or unrelated
evidence stays open and keeps the `follow_up` gap. Evidence is bound to
`reviewed_artifact`: a claim produced against a different commit or frozen diff
than the current one is stale and does not count as covered. When an entry
carries `criterion_id` or `task_id`, both must agree with the criterion and the
report task; `validate_report()` enforces that agreement and `reconcile()`
relies on the validated report instead of repeating the check.

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
   evidence that satisfies it, is produced by a delegated agent against the
   current `reviewed_artifact`, and every structured evidence entry is
   `passed`.
2. `Partial` and `unverified` remain open until follow-up evidence is available.
3. A criterion delegated to an agent but absent from that agent's report is
   recorded as a delegation/report gap, even when another report covers it.
4. A criterion with no delegation is recorded as a delegation gap.
5. Contradictory supported coverage values are never resolved by precedence:
   the criterion is demoted to `unverified`, a criterion-prefixed
   `<criterion>:disagreement:<values>` gap is recorded (for example
   `AC-01:disagreement:covered/unverified`), the row keeps its `follow_up` gap
   and `release_ready` is false. `covered` never wins a disagreement.
6. Every non-empty `decision_needed` entry is escalated as
   `decision:<agent>:<task>:<id>`, and every effective non-accepted proposal is
   escalated as `adr:<id>:pending:<effective-status>`. Either blocks release
   regardless of report status.
7. A proposed ADR or an architecture conflict is escalated and recorded as an
   unresolved decision until a human approves it.
8. Unresolved items are recorded before handover; they are not silently dropped.

## Release evidence and the single boolean

The Orchestrator owns the machine-readable release record
(`docs/workflow/ledgers/issue-30.release.json` for issue #30). It carries the
live evidence slots and never uses a synthetic fixture. Each required slot
records `state` from the exact taxonomy `passed`, `failed`, `skipped`,
`unavailable`, `contributor-reported`; only `passed` is green, CI additionally
requires `inspected: true`, and a verified explicit base SHA enables a later
inspected re-run instead of relabelling a skip.

`release_ready` is one boolean. It is true only when all of the following hold:

```text
release_ready = committed_plan_review_passed
  AND ai_code_review_passed
  AND named_human_code_review_passed
  AND tester_verification_passed
  AND workflow_validator_ci_passed
  AND all_required_criteria_covered_with_current_evidence
  AND no_gaps
  AND no_record_declared_gaps
  AND no_disagreements
  AND no_decision_needed
  AND no_pending_effective_proposals
  AND no_open_required_decisions
  AND pr_head_matches_all_evidence
```

The record's `artifact` is the reviewed artefact and must be the handover
commit: a full 40-hex commit identity identical to `pr_head`. `pr_head` is not
free text — both `pr_head` and `artifact` are validated as full lowercase
hexadecimal commit identities (`^[0-9a-f]{40}$`), so the equality between them
is equality over two commits rather than over arbitrary strings. There is no
frozen-diff form in the record and no fallback from `artifact` to `pr_head`; a
missing, malformed or different value blocks. A round reviewed as a
working-tree or frozen diff is an intermediate state: before `release_ready`
can be true it must be committed and every slot and report re-bound to the
handover commit. Unknown top-level keys are rejected as
`release-record:unknown-key:<key>` instead of being silently discarded, so a
record cannot appear to declare a binding the evaluator ignores. The required
CI `base_sha` must be a lowercase hexadecimal commit identity of 7–40
characters, not merely a non-empty string.

The named-human slot requires a distinct human-attributed name and login,
`reviewer_type: human`, an independent-review attestation, `pr-review` or
`owner-record` provenance with its reference, a timestamp and the final PR
head. The name and login must differ from each other and from every AI
identity recorded in the same release record — the agent IDs and the AI
review slot's reviewer/model identity. Comparison is literal after lowercase
normalisation: capitalisation cannot bypass the AI-identity check, while
separator differences are not normalised (for example `DeepSeek V4.1 Flash`
differs from `deepseek-v4.1-flash`), and independence beyond that recorded
identity remains attested human judgement. AI identities are ineligible,
including an AI-authored owner review. Genuine human independence remains
attested judgement; the validator checks the recorded identity and provenance,
not the person behind them.

The Tester and Reviewer never treat a synthetic all-green control as release
evidence: it proves the evaluator, not real readiness. A missing or unusable
live record is `unavailable` and false.

## Report template

```markdown
## Agent report

- agent:
- issue:
- task_id:
- status:
- model:
- provider:
- thinking:
- reviewed_artifact:

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
