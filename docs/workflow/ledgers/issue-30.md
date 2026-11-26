# Issue 30 — Establish project-specific OpenCode multi-agent development workflow

- Branch: `issue-30-multi-agent-development-workflow`
- Pull request: created after the review and human-approval gate
- Last updated: 2026-11-26
- Human approval: pending pull-request review

## Acceptance criteria

| ID | Criterion | Delegated to | Status | Evidence | Gaps / follow-up |
| --- | --- | --- | --- | --- | --- |
| AC-A1 | Define a primary Orchestrator and five subagents: Planner, Reviewer, Implementer, Tester, Git Manager | Implementer | covered | `.opencode/agents/*.md`, `docs/workflow/development-workflow.md`, `opencode debug agents` | none |
| AC-A2 | Establish role boundaries and capability-based permissions, with Git write operations assigned to the Git Manager | Implementer | covered | `opencode.jsonc` project permissions, Git Manager allow rules, human-only merge deny, resolved-rule checks in `tools/workflow_check.py config`, tester report | Validator resolves rules with last-match-wins semantics and denies pull-request merge for every agent |
| AC-A3 | Use positive, actionable and constructive language; express restrictions through permissions and explicit responsibilities | Implementer | covered | Agent prompts and `AGENTS.md` | none |
| AC-A4 | Support configurable model assignments and preserve existing global configuration | Implementer | covered | `docs/workflow/model-assignments.md`, `opencode debug config`, inherited effective models | none |
| AC-A5 | Verify project-specific agent discovery with OpenCode v2.4.1 and document layout and shared instruction loading | Implementer | covered | `docs/validation/opencode-v2.4.1-discovery.md`, `opencode debug agents` | none |
| AC-D1 | Establish ADR directory, template and lifecycle: Proposed, In Review, Accepted, Rejected, Superseded | Implementer | covered | `docs/adr/README.md`, `docs/adr/template.md` | none |
| AC-D2 | Use explicitly approved, accepted ADRs merged into the default branch as the authoritative baseline | Implementer | covered | `docs/adr/README.md`, `tools/workflow_check.py adr` | Baseline becomes effective when this pull request is merged |
| AC-D3 | Treat ADRs in open pull requests as proposals, regardless of declared status; retain the accepted baseline | Implementer | covered | `docs/adr/README.md`, ADR fixture, `tools/workflow_check.py fixtures` | none |
| AC-D4 | Link ADRs to issues and implementation decisions; preserve existing accepted requirements | Implementer | covered | `docs/adr/ADR-0001-*`, `docs/adr/ADR-0002-*`, ADR links sections | none |
| AC-D5 | Escalate conflicts and pending architecture decisions for explicit human approval | Implementer | covered | `docs/workflow/feedback-contract.md`, ADR fixture escalation output | none |
| AC-F1 | Establish a shared structured feedback contract for every subagent and delegated task | Implementer | covered | `docs/workflow/feedback-contract.md`, `opencode.jsonc` instructions | none |
| AC-F2 | Return reports with status, completed work, coverage and evidence, missing items, findings, assumptions, dependencies, ADR alignment and next actions | Implementer | covered | Feedback contract, synthetic reports | none |
| AC-F3 | Include constructive feedback on delegation, planning, instructions and collaboration | Implementer | covered | Feedback contract, synthetic reports | none |
| AC-F4 | Maintain a consolidated coverage ledger; reconcile every report and identify gaps, including omitted delegation | Orchestrator | covered | `docs/workflow/ledgers/README.md`, `tools/workflow_check.py reports` | none |
| AC-F5 | Resolve gaps through follow-up or escalation; record unresolved items before handover | Orchestrator | covered | Feedback contract reconciliation rules, fixture gaps and escalations | none |
| AC-F6 | Require independent plan review before implementation and independent code review before pull-request completion | Reviewer | covered | `docs/workflow/development-workflow.md`, Reviewer agent, `AGENTS.md` quality gates | This pull request is reviewed by a human before merge |
| AC-V1 | Document the complete development workflow and shared instructions | Implementer | covered | `AGENTS.md`, `docs/workflow/development-workflow.md`, `docs/workflow/model-assignments.md` | none |
| AC-V2 | Validate configuration discovery, ADR baseline handling and feedback reconciliation with offline fixtures and synthetic reports; include an omitted criterion and a proposed ADR in an open-PR scenario | Tester | partial | Tester report, `tools/workflow_check.py`, `docs/validation/`, `docs/validation/workflow-check-output.txt`, mutation tests T1–T7 and F2–F4 | Fixes applied; final frozen-diff verification pending |
| AC-V3 | Store agent definitions and shared instructions in the repository; keep credentials and personal provider settings in authorised locations | Implementer | covered | `.opencode/agents/`, `AGENTS.md`, `docs/workflow/`, `opencode.jsonc` | none |
| AC-V4 | Preserve global OpenCode configuration and hand over reviewed pull requests for human approval | Orchestrator / Git Manager | covered | `opencode debug config` sources; global file unchanged; Git Manager handover instructions; merge denied for every agent | Human review and merge pending |
| AC-V5 | Keep deliverables focused on the development workflow and supporting documentation | Orchestrator | covered | Changed-file review | Application implementation remains in #27–#29 |

## Reports reconciled

| Agent | Task | Status | Received | Key findings |
| --- | --- | --- | --- | --- |
| Synthetic fixture | Planner, Implementer, Reviewer reconciliation | mixed | 2026-11-26 | Exercises omitted criterion, unverified criterion, undelegated criterion, missing report and proposed ADR conflict |
| Local discovery | OpenCode v2.4.1 agent and config discovery | completed | 2026-11-26 | Six agents discovered with expected modes; project and global config merged; shared instruction loaded |
| Tester | Independent verification | Completed | 2026-11-26 | Validator, discovery, permissions and JSON/link checks passed; two broken links and a validator-strength gap found and fixed |
| Reviewer | Independent code review | Partial | 2026-11-26 | Found R1 and F2–F8; R1 and F2–F6/F8 fixed, F7 final frozen-diff re-review pending |
| Orchestrator | Issue 30 implementation evidence | completed | 2026-11-26 | Workflow, ADRs, contract, ledger and offline validator delivered |

The synthetic reports are fixtures, not reports from real subagent sessions for
this issue. They validate the reconciliation rules. The pull request is subject
to the independent review and human-approval gate before merge.

## Findings and resolutions

| Severity | Finding | Resolution | Status |
| --- | --- | --- | --- |
| Medium | The config validator checked permission strings instead of resolved last-match-wins rules, so an edit allow after a deny could pass. | Replaced the string checks with parsed frontmatter rules and sample-command resolution. Mutation tests now fail as expected. | Resolved |
| Low | Two relative links in `.opencode/agents/orchestrator.md` resolved under `.opencode/docs/` instead of the repository `docs/` directory. | Corrected to `../../docs/workflow/...`. All relative links resolve. | Resolved |
| Low | A fixed deny list left exotic Git/GitHub write commands unmatched. | Inverted the project rules to deny `git *` and `gh *`, then re-enable read-only inspection. The Git Manager keeps explicit write allows. | Resolved |
| Informational | A transient untracked path appeared during testing. | The Git Manager re-checks `git status --porcelain` immediately before staging. | Handled in handover |
| Informational | The initial ADRs declare `Accepted` while their pull request is open. | Intentional: the open-PR rule demotes them to effective `Proposed`; the validator and fixture guard this behaviour. | Documented |
| Informational | The discovery record contained a local model snapshot. | Replaced model IDs with "Global OpenCode assignment"; the record is model-agnostic and contains no personal provider configuration. | Resolved |
| High | R1: blanket `*/* allow` rules in every agent overrode the project Git/GitHub denies and gave all six agents write access. | Removed the blanket rules; inverted project rules to deny `git *`/`gh *` with a read-only allowlist; validated resolved rules. | Resolved |
| Medium | F2: the validator only exercised a fixed sample of write commands, so an additional agent shell allow could pass. | Added a structural check that rejects any shell allow in non-Git-Manager agents and derives write samples from the Git Manager's allow rules. | Resolved |
| Medium | F3: `all` required a local `main` ref and failed in fresh checkouts without one. | Resolve `main` or `origin/main`; skip the actual-ADR section with a deterministic message when neither exists. The fixture still validates the policy. | Resolved |
| Medium | F4: the actual-repository ADR check was non-asserting, contained a dead `require`, and left open-PR `Rejected`/`Superseded` statuses unchanged. | Added real assertions, removed the dead check, map every open-PR ADR to `Proposed` (or `In Review`) and corrected the validation README. | Resolved |
| Medium/Low | F5: documentation said "read-only file access" although shell commands remain permission-controlled. | Reworded to "edit, write and patch tools denied; shell remains permission-controlled" across agents and docs. | Resolved |
| Low | F6: validation console blocks were abridged and the discovery record contained personal model IDs. | Added `docs/validation/workflow-check-output.txt` as a verbatim run and replaced model IDs with "Global OpenCode assignment". Blocks are labelled abridged. | Resolved |
| Low | F7: the review targeted a moving, uncommitted tree. | Freeze the final tree in a commit, record its SHA, and re-run Tester and Reviewer on the frozen diff before the pull request is completed. | Pending |
| Low | F8: `.gitignore` did not guard local overrides or environment files. | Added `.env*`, `opencode.local.json(c)` and `*.local.json(c)` patterns. | Resolved |
| Informational | User decision: merging a pull request is reserved for the human user. | Removed `gh pr merge*` from the Git Manager allow rules, added an explicit project deny and a validator assertion, and updated agent and workflow instructions. | Resolved |

## Architecture baseline

- Accepted baseline: ADR-0001 and ADR-0002 become accepted when this pull
  request is merged; `main` had no ADR baseline before this change.
- Proposals in this pull request: ADR-0001 and ADR-0002.
- Conflicts: none between the proposals; the fixture exercises a synthetic
  conflict with an already merged baseline.
- Decisions needed: human approval of ADR-0001 and ADR-0002 through the pull
  request.

## Unresolved items

- The initial ADR baseline is effective only after the human-approved merge of
  this pull request. Until then, the workflow checks treat both ADRs as
  proposals.
- Independent human review and approval of this pull request are required
  before merge.
- Configuration discovery was verified against the local OpenCode v2.4.1 and
  the existing global model assignments. A different OpenCode version or model
  configuration may require a repeated discovery check.
- Final Tester and Reviewer verification must run against the frozen commit and
  its recorded SHA before the pull request is marked ready for human approval.

## Deferred or out-of-scope work

- Application implementation (#27–#29).
- Additional specialist agents.
- Automatic model selection and live benchmark execution.
- Advanced workflow automation.
- Live inference remains subject to the existing approval and capability gates.

## Handover

- Plan review: workflow gates defined; synthetic reconciliation covers planner,
  implementer and reviewer reports.
- Code review: Reviewer completed a first pass (R1 and F2–F8). Fixes are applied;
  a frozen-diff re-review is required before pull-request completion. Human
  review of the pull request is pending.
- Test evidence: `python3 tools/workflow_check.py all` passes; independent tester report and mutation checks recorded.
- Human approval: pending.
- Git Manager: branch, commit and pull request after approval.
