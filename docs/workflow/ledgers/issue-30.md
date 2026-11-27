# Issue 30 — Establish project-specific OpenCode multi-agent development workflow

- Branch: `issue-30-multi-agent-development-workflow`
- Frozen commit: `498444ceaf78f53bae419870202c91e90b43315c` (29 files)
- Hardening commit: `4d3f6dc981cec39607e26879b38a4484a4c5328f` (16 files, +1257/-197)
- Final commit: `613c13ae9b2143cc0e097e6fde487400033707f1` (9 files, +409/-60)
- Reconciliation merge: `f19d1c59e3fc131d5e5d6113a70db119aa4e2f31` (parents `613c13a` and `17cf55a`; 16-path merge delta)
- Ledger refresh: `97fd890` (docs only)
- Review delta: `c9fc085b34ebbbd146506a78b4d259f2cea68b1a` (39 files, +2677/-131; ledger and `.idea/` excluded)
- Handover target: tracked diff against `c9fc085` with the ledger excluded, SHA-256
  `5116b64519199a2ba6f4b08f141f9558e8af26d5ad8af620b62f43246ea3181a` (five files,
  +160/−72)
- Handover commits: `32977e1` (reviewed delta, five files) and `5f55d0e` (ledger);
  pushed as `97fd890..5f55d0e`, a fast-forward that also carried `c9fc085`
- Pull request: [#32](https://github.com/PeterKopa/multi-agent-model-advisor/pull/32);
  description replaced with the handover state, review answer posted as
  [#issuecomment-7226782493](https://github.com/PeterKopa/multi-agent-model-advisor/pull/32#issuecomment-7226782493)
- Last updated: 2026-11-27
- Human approval: granted for the commits, the push, pull-request creation and the `main`
  reconciliation on 2026-11-26, and for this handover round (review-delta commit, ledger
  commit, push, pull-request description and review answer) on 2026-11-27; review and merge pending

## Acceptance criteria

The authoritative baseline is the issue #30 body as updated on 2026-11-26: the 21
original criteria plus nine added by the three scope comments on PR #32
(`#issuecomment-7204153066`, `#issuecomment-7204224068`,
`#issuecomment-7204320585`). The nine additions are recorded below with stable
IDs. The Orchestrator's earlier intake missed those comments; the follow-up
review on `b013f04` found the gap, and the coverage below is the reconciled
state, not a retroactive claim that the work was complete.

**Coverage semantics.** The 21 original criteria carry `covered` from the
pre-baseline round; the plan's carry-forward section requires every one of them
to be re-verified at the final head, nine of them in full because the 21-to-30
gap impeached them. Until that re-verification runs, those rows are carried
claims and not current evidence. The nine criteria added by the scope comments
are tracked separately, and of those AC-PV1, AC-PL1, AC-CX1 and AC-WO1 are now
covered by evidence from the current rounds. The counts in the status column
therefore read 24 `covered`, 6 `partial`, 0 `missing`, but 21 of the 24 are carried originals awaiting final-head re-verification; only four are covered by evidence produced after the baseline was corrected. Of the 21 originals, 20 are now re-verified at `171d3d9` and AC-D2 stays `partial`.

| ID | Criterion | Delegated to | Status | Evidence | Gaps / follow-up |
| --- | --- | --- | --- | --- | --- |
| AC-A1 | Define a primary Orchestrator and five subagents: Planner, Reviewer, Implementer, Tester, Git Manager | Implementer | covered | `.opencode/agents/*.md`, `docs/workflow/development-workflow.md`, `opencode debug agents` | none |
| AC-A2 | Establish role boundaries and capability-based permissions, with Git write operations assigned to the Git Manager | Implementer | covered | `opencode.jsonc` ordered deny→allow→ask→deny policy, `.opencode/agents/git-manager.md` allowlist (`git push origin ?*` plus the write commands it owns) with trailing denials, per-agent resolution tables and compound samples in `tools/workflow_check.py`, Implementer hardening reports, Reviewer frozen-diff and delta reports, Tester 34/34 resolution table, final frozen tree `5116b645…` with the tab limit stated | `gh api`, `gh pr merge` and pushes to `main` resolve to `deny` for all six agents, including the Git Manager. Every push that does not name `origin` with a non-empty refspec separated by a single space falls through to the project deny or is caught by an explicit trailing deny — a second space after the remote is denied too, and the one shape the pattern language cannot express (a tab after the space) is recorded as a limit rather than granted. The OpenCode shell scanner checks every extracted subcommand, so the protected operations deny in direct and compound invocations; the validator splits on common separators to model this |
| AC-A3 | Use positive, actionable and constructive language; express restrictions through permissions and explicit responsibilities | Implementer | covered | Agent prompts and `AGENTS.md` | none |
| AC-A4 | Support configurable model assignments and preserve existing global configuration | Implementer | covered | `docs/workflow/model-assignments.md`, `opencode debug config`, inherited effective models | none |
| AC-A5 | Verify project-specific agent discovery with OpenCode v2.4.1 and document layout and shared instruction loading | Implementer | covered | `docs/validation/opencode-v2.4.1-discovery.md`, `opencode debug agents` | none |
| AC-D1 | Establish ADR directory, template and lifecycle: Proposed, In Review, Accepted, Rejected, Superseded | Implementer | covered | `docs/adr/README.md`, `docs/adr/template.md` | none |
| AC-D2 | Use explicitly approved, accepted ADRs merged into the default branch as the authoritative baseline | Implementer | partial | `docs/adr/README.md`, `tools/workflow_check.py adr`, reconciliation-merge evidence (`17cf55a` as ancestor, `ADR-0003` normalisation); live check at `171d3d9` is honest SKIP because `origin/main` carries no `ADR-*.md`, only the legacy `0001-go-bubble-tea-bootstrap.md` | The Go and Bubble Tea bootstrap decision from #27 remains in force; the named ADR baseline becomes effective only when this PR is merged. Live baseline stays open under OD-ADR-LIVE |
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
| AC-V2 | Validate configuration discovery, ADR baseline handling and feedback reconciliation with offline fixtures and synthetic reports; include an omitted criterion and a proposed ADR in an open-PR scenario | Tester | covered | Tester frozen-commit, delta, final-delta, reconciliation-merge, round-3, final, whitespace, documentation-truth and granted/limit reports (`python3 tools/workflow_check.py all` exit 0 twice byte-identical, recorded output byte-identical, 53-sample permission matrix, 48/48 compound cells, 2340-cell push cluster sweep, ten invalid-report fixtures each rejected for its own reason, mutated ADR self-tests, 34/34 resolution cells, `?*` mutant failure, 432 deny checks and 1,800 module expectations with the two new denies proven load-bearing), Reviewer reports on `498444c`, `4d3f6dc`, `613c13a`, `f19d1c5`, the review delta and the final tree | Independent verification covers every commit, the review delta and the final handover tree; the audit gate is falsified against patched copies and proven fail-closed as the first `all` step |
| AC-V3 | Store agent definitions and shared instructions in the repository; keep credentials and personal provider settings in authorised locations | Implementer | covered | `.opencode/agents/`, `AGENTS.md`, `docs/workflow/`, `opencode.jsonc` | Credential paths denied for read, edit, external access and shell strings; `~/.config/opencode/*` requires approval; `.env.example` stays readable |
| AC-V4 | Preserve global OpenCode configuration and hand over reviewed pull requests for human approval | Orchestrator / Git Manager | covered | `opencode debug config` sources; global file unchanged; Git Manager handover instructions; `gh pr merge`, `gh api` and pushes to `main` denied for every agent and re-denied last in the Git Manager | Human review and merge pending |
| AC-V5 | Keep deliverables focused on the development workflow and supporting documentation | Orchestrator | covered | Changed-file review | Application implementation remains in #27–#29 |
| AC-AI1 | Adopt AI-first development: AI agents own planning, implementation, automated verification, independent technical review and pull-request preparation; the human defines and approves goals, significant scope and architecture decisions, independently reviews the code and retains final approval and merge authority | Implementer | partial | `AGENTS.md` and the workflow document assign the roles and keep the merge human-only | The AI-first principle and the independent human code-review step are not stated as a gate |
| AC-PL1 | Apply Right-Sized Work Items before detailed planning, weighing cohesion, dependencies, complexity, architectural impact, side effects, testability, agent context, coordination overhead and AI/human review effort; recommend splitting only for independently verifiable outcomes; present material scope changes for approval; use no rigid size thresholds | Planner | covered | `docs/workflow/development-workflow.md` §Right-sized, `AGENTS.md`, Planner/Orchestrator prompts, `ledgers/README.md` sizing template, `planning/right-sized.json` (nine factors, verifiable outcome, named-human approval, no file/line count), `validate_right_sized_work_item()` with 20 mutations; Tester and Reviewer independently proved all nine factor removals, approval and rigid-threshold guards load-bearing; `ci` exit 0 | Verifiable part covered. Whether a split is cohesive or a change material remains Planner/human judgement and is labelled as such, not validator-proven |
| AC-RV1 | Require independent AI code review and independent human code review before merge; the Reviewer checks the original issue and all acceptance criteria independently of the implementation plan | Reviewer | partial | Reviewer gates cover the AI review; the handover records no independent human code review | Add the human review step and its handover state |
| AC-VB1 | Bind plan review to a versioned plan and code review, test evidence and handover to the exact reviewed commit or an identifiable frozen diff; revalidate affected gates after material changes; reconcile the final PR head with the reviewed evidence | Orchestrator | partial | Plan revision 2 is committed as `e881bb1`; the Reviewer approved the extracted section `474f2c07…` from that commit and reproduced hash, length and range; the freeze protocol is written into the plan | Plan identity is implemented and verified (`check_plan_identity()`, anchored, no byte offsets, reproduced from the committed blob); artefact binding is commit-only with full 40-hex `pr_head` and `artifact` and the re-bind obligation is documented in the contract, the workflow document and the validation README; the handover half is open by design because the live release record does not exist and no evidence is re-bound to a commit |
| AC-PV1 | Extend the feedback contract with actual model/provider identity and optional thinking configuration; record unknowns explicitly, preserve local privacy and keep personal provider settings in authorised locations | Implementer | covered | `docs/workflow/feedback-contract.md` provenance section; `REPORT_FIELDS` and `validate_report()` require `model`, `provider` and `reviewed_artifact`, accept the explicit `unknown` sentinel and reject blank or whitespace-only values; `missing-model-provenance` and `blank-model-provenance` fixtures; three independent Tester rounds reproduced the behaviour; the privacy wording keeps personal assignments in authorised local configuration | Identity truth and the absence of reasoning traces are reviewer-inspected and labelled as such, not validator-proven |
| AC-CI1 | Integrate the deterministic offline workflow validator into GitHub Actions; tie final verification to the reviewed commit and inspect job, step and log evidence; distinguish passed, failed, skipped, unavailable and contributor-reported checks | Implementer | partial | `workflow-validator` job in `.github/workflows/ci.yml` (fetch-depth 0, persist-credentials false, exact head, enforced `EXPECTED_BASE_SHA` commit, audit+ci only, no continue-on-error), `validate_ci_workflow_contract()` with 27 guards / 31 mutations all load-bearing, `jactionlint` clean, `ci` twice byte-identical, Tester and Reviewer verified independently | Static/offline half covered; run 46081689891 / job 140781893967 `success` on head `171d3d9` with expected==actual head/base in the log, inspected by the Git Manager. The AI reviewer could not re-open the run offline and classifies it as contributor-reported; independent Tester inspection of the live log is the next gate. |
| AC-CX1 | Apply Context Isolation & Context Efficiency: task-specific delegation packets with the relevant acceptance criteria, ADR baseline and proposals, necessary repository context, dependencies, constraints, expected evidence and task identity; prefer concise structured handoffs; document context assumptions and request missing context before consequential decisions | Orchestrator | covered | `docs/workflow/delegation-packet.md` (normative, nine field markers), workflow §Delegation packet reduced to a link, `AGENTS.md` + six prompts link, `validate_delegation_packet()` (23 mutations) and link validation; Tester and Reviewer proved field-removal and link-removal guards load-bearing | Field presence is validator-proven; concision, sufficiency and requesting-missing-context are explicitly labelled instruction/human-judgement rules. Link-only claim is slightly wider than enforcement (paraphrased duplicates not caught) — carried as follow-up |
| AC-FC1 | Apply Fail-Closed Quality Gates: distinguish passed, failed, unverified and blocked; mark covered only with sufficient applicable evidence tied to the correct issue, task and reviewed artefact; keep missing, skipped, stale, contradictory or blocked evidence open; add offline negative fixtures for missing evidence, conflicting reports and stale verification | Tester | partial | `validate_report()` and `reconcile()` enforce the five-state check taxonomy, disagreement demotion to `unverified`, artifact staleness and issue/task/criterion identity; `evaluate_release_gate()` blocks on every open criterion, gap, disagreement, decision open item and pending proposal; 17 invalid-report fixtures, 12 expected-false release fixtures and 52 in-memory mutations, with guard-removal proofs that each named guard fails its own case; `python3 tools/workflow_check.py ci` exit 0 twice byte-identical | Verified independently across three Tester rounds, which closed two real fail-opens (absent `check_state`, unvalidated `pr_head`). Demoted by the code review because the decision gate accepted an AI resolver; the fix is verified and the reported bypass is closed, but the residual remains: an AI identity that is not recorded in an attestation slot still passes a `resolved_by`. The Tester called that a defensible boundary, the Reviewer called it a bounded fail-open — the stricter reading is adopted, so the row stays `partial` until the normative sentence is scoped to what the gate can enforce. |
| AC-WO1 | Apply Single Writer and explicit write ownership: record responsible agent, task, affected files, dependencies and write scope before mutating work; serialise overlapping writes; keep the Orchestrator as sole ledger writer, the Implementer for product code, the Planner for ADR proposals, Reviewer and Tester read-only, Git operations with the Git Manager; allow parallel read-only analysis; isolate test outputs; pause and hand over on overlap; validate with offline synthetic cases | Orchestrator | covered | `validate_write_ownership()`, five fixtures (disjoint/overlap/handover/stale/read-only), 15 mutations, `.tmp/<task-id>/` enforcement, role scopes matching agent frontmatter; Tester proved 21 guard removals across WI-CO, Reviewer confirmed scopes and instruction-only labelling | Record-level checks only. Actual write obedience and filesystem isolation are instruction-only limits stated in the docs. One `.tmp`-in-`write_scope` branch has no mutation (follow-up) |

## Implementation plan (revision 2)

- Author: Planner, issue #30, task `issue-30-baseline-30-r2`, 2026-11-27; status `Completed`.
- Review disposition: revision 1 required changes; F1-F11 are closed by the blocks indexed below.
- Baseline: all 30 criteria, including the carry-forward re-verification below; #33/#34 remain separate.

### Plan identity and freeze protocol (F1, F8)

| Item | Binding rule |
| --- | --- |
| Extraction | In the committed UTF-8/LF ledger blob, hash from the first byte of `## Implementation plan (revision N)` up to, but excluding, the first byte of the following `## Reports reconciled`. Include every raw section byte, including internal code fences and the trailing blank line, so the section ends `\n\n`; an outer presentation fence and display line numbers are not ledger content. `section_sha256 = SHA256(extracted_bytes)`; also record the half-open byte range and length. |
| Writers | The Orchestrator alone pastes/revises this ledger section. The Git Manager makes a plan-only commit after the approved Git handover. The Implementer, Tester and Reviewer make no ledger edits. |
| Review and identity | The Reviewer independently reviews the extracted section **from that commit** against the original issue and all 30 criteria. Plan identity is `(reviewed_commit_sha, ledger_path, section_sha256)`; an uncommitted section or candidate hash is not plan identity. |
| Freeze point | The freeze occurs when the Reviewer approves that committed section and names its commit and section hash. WI-EV delegation starts only after this point. Any plan-content change requires a new revision, plan-only commit and independent plan review. |
| Later ledger commits | Every post-review ledger-only commit is a material AC-VB1 change: re-run affected reconciliation, Tester and Reviewer gates and reconcile the final PR head. A plan-section change always restarts plan review; there is no ledger exclusion or free pass. |

### Right-Sized Work Items decision (AC-PL1; F3, F10)

Keep the reviewed split: three sequential work items inside issue #30, not nine and no new issues.

| Work item | Criteria | Independently verifiable outcome |
| --- | --- | --- |
| WI-EV: evidence and review gates | AC-AI1, AC-RV1, AC-VB1, AC-PV1, AC-FC1 | Provenance/artifact-bound reports, fail-closed reconciliation, trusted `ci` validation mode and the single-boolean final release gate |
| WI-CO: coordination and ownership | AC-PL1, AC-CX1, AC-WO1 | Right-sized planning, one canonical delegation packet and deterministic ownership/handover cases |
| WI-CI: CI evidence | AC-CI1 | An exact-head `workflow-validator` job with enforced base ref and inspected run/job/step/log evidence |

| AC-PL1 factor | Decision |
| --- | --- |
| Cohesion | Evidence schema/reconciliation are one contract; coordination/ownership are a second; CI is an operational integration. |
| Dependencies | WI-CO stale/conflict cases and WI-CI evidence use WI-EV's schema. At integration the dependency is bidirectional: WI-EV supplies the CI contract and release evaluator, while the later WI-CI job supplies required CI evidence to the release gate. |
| Complexity | Keep schema and precedence together to avoid repeated fixture migrations; isolate CI's external-evidence complexity. |
| Architectural impact | WI-EV/WI-CO amend the unmerged ADR-0002 workflow proposal; WI-CI changes the CI contract already approved by the owner on 2026-11-27. |
| Side effects | String-only covered evidence becomes insufficient; old fingerprints/readiness claims become historical; CI and human gates can block release. |
| Testability | WI-EV/WI-CO are deterministic offline; WI-CI additionally needs actual Actions evidence, and real human review cannot be synthesized. |
| Agent context | Three focused packets limit context without separating tightly coupled validator changes. |
| Coordination overhead | One serial mutation path and three review points avoid nine migrations/handovers; shared files are never concurrently edited. |
| AI/human review effort | Each item gets focused AI review/testing, then one integrated final-head AI review and one named-human review of the complete PR. |

This uses independently verifiable outcomes, not rigid counts of criteria, files or lines. The ADR-0002 amendment remains Planner-owned within WI-EV.

### Sequence (unchanged order; F1, F3)

1. Orchestrator writes revision 2; Git Manager makes the plan-only commit; Reviewer approves that committed section; freeze.
2. WI-EV, then Tester verification and Reviewer code review of its frozen target.
3. WI-CO, then Tester verification and Reviewer code review of its frozen target.
4. WI-CI, then Tester verification, a published candidate for actual Actions evidence, and Reviewer code review. The job runs trusted `ci` mode; its result later feeds `all`.
5. Integrated final gate: record actual CI and named-human review in the ledger release record, reconcile the actual PR base/head, refresh affected gates, then run `all`. The human alone merges after `release_ready=true`.

### Criterion map (F2-F9)

| Criterion | Concrete file/section changes | Verification |
| --- | --- | --- |
| AC-AI1 | `AGENTS.md` quality gates; `docs/workflow/development-workflow.md` goals/roles/handover; `.opencode/agents/orchestrator.md`; `docs/workflow/ledgers/README.md`; ADR-0002 decision/consequences | `validate_release_gate()` rejects AI-only evidence; documents label the principle and human authority as instruction/human-judgement rules, not offline-proven behaviour |
| AC-PL1 | Sizing steps in the workflow and Planner/Orchestrator prompts; ledger sizing template; `docs/validation/fixtures/workflow/planning/right-sized.json`; `check_right_sized_work_item_fixture()` | Nine-factor positive control; mutations remove each factor, independent verifiability and required approval field. Actual approval/material trade-offs remain named-human evidence |
| AC-RV1 | Reviewer/Orchestrator/Git Manager prompts; `docs/workflow/feedback-contract.md` review evidence; `AGENTS.md`; `validate_release_gate()` | Missing AI review, missing human review, AI-identity reuse, missing human provenance and head mismatch each force false; Reviewer reads the original issue/all criteria directly |
| AC-VB1 | This committed ledger plan; `docs/workflow/ledgers/README.md`; feedback contract; workflow stages and agent prompts; `check_plan_identity()` and artifact checks | One-byte/trailing-newline, stale-artifact and final-head mutations fail; post-review ledger-only changes trigger affected revalidation |
| AC-PV1 | Feedback contract fields `model`, `provider`, `thinking`; `docs/workflow/model-assignments.md`; `REPORT_FIELDS`/report validation; `fixtures/workflow/invalid/missing-model-provenance/` | Synthetic actual/unknown values pass; missing/blank fails. Truth/privacy of real identities and absence of reasoning traces are reviewer-inspected and labelled as such |
| AC-CI1 | `.github/workflows/ci.yml` `workflow-validator`; `tools/workflow_check.py` trusted `ci`/`all` modes; validation/workflow/ledger docs | `check_ci_workflow_contract()` plus `jactionlint`; actual run/job/step/log inspection binds the reviewed SHA and base; no skipped required check is green |
| AC-CX1 | **Normative:** `docs/workflow/delegation-packet.md`. `development-workflow.md ## Delegation packet` becomes only a link to it; `AGENTS.md` and agent prompts also link rather than duplicate rules | `validate_delegation_packet()` mutations omit identity/criteria/artifact/ownership. Concision, sufficient context and requesting missing context are explicitly instruction/human-judgement rules |
| AC-FC1 | Feedback contract evidence/check states; `validate_report()`, `reconcile()`, `evaluate_release_gate()`; ledger release record; validation docs and fixtures | Exact status/gap/escalation/blocker assertions and a mutation per guard; fixture false outcomes are expected test results, while the live `all` gate fails non-zero on false |
| AC-WO1 | `AGENTS.md`; workflow ownership section; ledger ownership/release templates; canonical packet; role prompts; `validate_write_ownership()` and ownership fixtures | Overlap/disjoint/handover/stale/read-only mutations; `.tmp/<task-id>/` paths. Actual write obedience and filesystem isolation are instruction-only limits stated in the documents |

The Orchestrator owns both `docs/workflow/ledgers/issue-30.md` and the machine-readable `docs/workflow/ledgers/issue-30.release.json`. The latter carries live release evidence and decisions; synthetic fixtures never serve as that live record.

### Reconciliation and the single release boolean (F2-F4, F6, F9)

| Rule | Exact required behaviour and load-bearing mutation |
| --- | --- |
| Disagreement | In `reconcile`, any contradictory supported coverage values produce `disagreement:<values>`, demote the criterion to `unverified`, add `follow_up`, and force `release_ready=false`; `covered` never wins. `test_conflicting_reports_cannot_pass` starts from an otherwise green control: restoring covered-wins or omitting the release blocker makes the conflicting case pass and must fail the test suite. |
| Decisions/proposals | Every non-empty `adr_alignment.decision_needed` emits `decision:<agent>:<task>:<id>` and every effective non-accepted proposal emits `adr:<id>:pending:<effective-status>`; either forces false regardless of report status. Removing either loop makes `unresolved-decision` pass and must be caught. |
| Evidence | `covered` requires sufficient applicable structured evidence matching issue, task, delegated criterion and current artifact. Missing, stale, blocked, failed or unrelated evidence stays open. Removing identity/freshness checks is caught by wrong-task, wrong-criterion and stale-verification mutations. |
| Required checks | `check_state` is exactly `passed`, `failed`, `skipped`, `unavailable`, `contributor-reported`; only inspected `passed` evidence is green. Skipped/unavailable/contributor-reported required checks block unless a verified explicit base SHA enables a subsequent inspected pass or a named human resolves the item under the approval rules. |
| Human slot | `human_review` requires a distinct human-attributed name/login, `reviewer_type: human`, independent-review attestation, PR-review/owner-record provenance, timestamp and final head. AI identities, including the AI-authored owner review, are ineligible. Removing distinctness/provenance checks must fail a fixture. |

`release_ready` is one boolean, not a prose verdict:

```text
release_ready = committed_plan_review_passed
  AND ai_code_review_passed
  AND named_human_code_review_passed
  AND tester_verification_passed
  AND workflow_validator_ci_passed
  AND all_required_criteria_covered_with_current_evidence
  AND no_gaps
  AND no_disagreements
  AND no_decision_needed
  AND no_pending_effective_proposals
  AND no_open_required_decisions
  AND pr_head_matches_all_evidence
```

The complete required-item set is therefore: committed plan review; independent AI code review against the original issue/all criteria; independent named-human code review; Tester verification; passing workflow-validator CI; current applicable evidence for every required criterion; no gaps or disagreements; no `decision_needed`, pending proposal or other required decision; and exact PR-head agreement across plan/code/test/CI/human/handover evidence. Ownership overlaps and stale/blocked/skipped/unavailable/contributor-only required evidence are gaps, not exceptions.

Add trusted `ci` mode (audit plus offline config/ADR/report/fixture checks) and final `all` mode (`ci` plus the live release record). `all --release-scenario docs/workflow/ledgers/issue-30.release.json` exits non-zero whenever `release_ready=false`; missing/unusable live input is `unavailable` and false. Expected-false synthetic cases run inside the fixture harness and do not invoke the live exit path. The synthetic all-green control proves only the evaluator, never real release readiness. After the named human's independent review is recorded in both ledger views, the Orchestrator re-runs `all` against that record.

This resolves the CI ordering without weakening either gate: WI-EV builds `ci` and `all`; WI-CI later runs `ci` in Actions; the inspected CI result is then a required input to `all`. The release gate depends on that later CI artifact, and the CI workflow contract depends on WI-EV's validator.

### Open required decisions (F5; all force `release_ready=false` until closed)

| ID | Required human resolution and closure evidence |
| --- | --- |
| OD-ROLE | Per-role tool/MCP lockdown: the owner chooses/approves the boundary and harmless final-head capability inspection verifies it. Shell matrices alone do not close exposed merge capabilities. |
| OD-BRANCH | Repository-side branch protection: the owner decides/applies required human review, no force push and no direct push; the ledger names the human and settings evidence. Agents do not change settings. |
| OD-ADR-LIVE | Live ADR baseline: the owner resolves the verified explicit base SHA/legacy mapping; the actual live check must pass, or the owner records an explicit decision under the approval rules. A fixture or SKIP cannot close it. |
| OD-PR-INVENTORY | PR-description ADR inventory: the owner approves the correct accepted-baseline/proposal inventory; the Git Manager updates and reads back the description on the final head. |

These are recorded in `decision_needed` even where implementation is outside agent scope. They cannot disappear behind deferred scope.

### CI binding (F3, F6)

The `workflow-validator` job must use `actions/checkout` with `fetch-depth: 0`, `persist-credentials: false`, the exact PR head SHA/repository, and an enforced `origin/main` resolved to the recorded explicit base SHA. It prints/asserts expected versus actual base/head, runs `python3 tools/audit_validator.py` then `python3 tools/workflow_check.py ci`, and has no `continue-on-error`. `check_ci_workflow_contract()` mutations remove the full-history setting, exact-head checkout, base enforcement or trusted command. `jactionlint` checks workflow syntax; only actual run/job/step/log inspection establishes `passed`.

For a skipped live ADR check, a verified base SHA is an input to re-running and obtaining an inspected pass, not permission to relabel SKIP. Failed, skipped, unavailable and contributor-reported required checks remain blockers; a named human resolution records identity, rationale, reference and final head.

### Fixture strategy (F2-F6, F9)

| Suite | Cases and expected proof |
| --- | --- |
| AC-FC1 file fixtures | Migrate `conflicting-reports` to unverified/false; add `stale-verification`, `blocked-evidence`, `missing-required-gate`, `unresolved-decision`, `contributor-reported-required-check`, `wrong-criterion-assignment`, missing AI/human review and pending-proposal cases. Assert exact ledger, gaps, escalations and blockers. |
| AC-FC1 in-memory | All-green positive control; mutations for covered-wins disagreement, each required release input, each decision/proposal loop, stale head, AI-identity reuse and every non-pass check state. Expected-false fixtures pass the harness only when false is detected. |
| AC-WO1 | `overlapping-writes`, `disjoint-writes`, `ownership-handover`, `conflicting-evidence`, `stale-evidence`, `parallel-read-only`; mutations add shared `.tmp/`, missing handover, role violation, changed scope and separate-worktree integration without renewed gates. |
| Regression | `python3 tools/audit_validator.py`; trusted `ci` twice with byte comparison under frozen refs; `jactionlint`; recorded output refresh. Final `all` runs separately against live release evidence and must be zero only when true. |

### Documentation-versus-rules contract (F7)

Every normative statement is classified here and receives the same limitation label in its normative document.

| Rule | Validator assertion + load-bearing mutation, or explicit judgement-only limit |
| --- | --- |
| Committed plan identity/freeze | `check_plan_identity()` recomputes committed bytes; one-byte/trailing-newline/post-review-commit mutations. Human approval of the plan is judgement evidence. |
| AI-first allocation and human authority | Instruction/human judgement only; the release gate checks required evidence slots, not whether agents truly behaved AI-first. State this in `AGENTS.md`, workflow and ADR-0002. |
| Right-sized factors/split schema | `check_right_sized_work_item_fixture()`; remove each factor and independent-verification field. Actual cohesion and material-scope approval are Planner/human judgement, labelled in the workflow. |
| AI Reviewer independence/original-issue reading | Artifact/hash and report fields are validated; actual independence is Reviewer/human judgement, stated in the Reviewer prompt and workflow. |
| Named-human review | `validate_release_gate()` rejects missing human provenance, AI identity and wrong head; genuine human independence remains attested human judgement, stated in the ledger template. |
| Model/provider/thinking | Required/unknown-field mutations; actual identity truth and privacy/reasoning-trace exclusion are reviewer-inspected limits stated in the contract. |
| Evidence identity/freshness/disagreement | Wrong issue/task/criterion/artifact, stale, conflicting and blocked mutations. Semantic evidence sufficiency remains human judgement, stated in the feedback contract. |
| Decisions/pending proposals/final boolean | Remove each escalation loop and each required-input check; named-human resolution authenticity remains judgement evidence. |
| CI YAML contract | `check_ci_workflow_contract()` mutations plus `jactionlint`. Actual job/step/log meaning, cancellation and SHA binding are inspected, not claimed by static text checks; state this in validation docs. |
| Delegation packet | Canonical-template/link and required-field mutations. Context sufficiency, concision and actual missing-context requests are instruction/human judgement, explicitly labelled in both linking documents. |
| Ownership/scratch/handover | Overlap/disjoint/role/stale-handover/shared-scratch mutations. Real write obedience and filesystem isolation are instruction-only and stated as unenforced in `AGENTS.md` and workflow. |
| ADR baseline/proposal rules | Existing ADR signature/status mutations plus pending-proposal release mutations. Human acceptance remains external approval evidence. |

### ADR impact (F8)

Amend `docs/adr/ADR-0002-project-specific-multi-agent-development-workflow.md` as a proposal with the nine new principles and their honest limits; do not rewrite ADR-0003's bootstrap decision. The old `5116b645...` fingerprint and readiness verdicts are historical. The reviewed plan-only ledger commit is the immutable plan head; subsequent ledger-only commits trigger AC-VB1 revalidation.

The string `adr:ADR-0002:conflicts:ADR-0001` comes from the synthetic ADR fixture, not the real ADR-0002 (`conflicts-with: []`). Keep it as fixture behaviour; never "resolve" it by editing an accepted ADR. Real proposals stay effective proposals until human-approved merge, and all pending proposals block the live release gate.

### Carry-forward re-verification at the final gate (F11)

The review named eight IDs but called for nine impeached originals and twelve others. AC-D4 is therefore included as the ninth: the earlier external review explicitly impeached it, and the follow-up's live-baseline/PR-inventory findings keep its concerns open. This yields nine plus twelve across the 21 originals.

| Impeached original | Final-head re-verification |
| --- | --- |
| AC-A2 | Re-run resolved permission matrices and harmless capability inspection; OD-ROLE and OD-BRANCH remain required human decisions, not covered by prose. |
| AC-D2 | Verify explicit base SHA, legacy ADR-0003 mapping and actual live baseline result; no unearned PASS from fixtures or SKIP. |
| AC-D3 | Re-run unchanged/changed ADR signature and open-PR status fixtures; real ADR-0001/0002/0003 remain proposals until merged and pending proposals block release. |
| AC-D4 | Re-check issue/implementation links, preservation of accepted requirements and the corrected PR ADR inventory; OD-PR-INVENTORY requires owner approval and final-head read-back. |
| AC-D5 | Assert every `decision_needed`, pending proposal and OD-* item escalates and blocks; close only with named-human evidence. |
| AC-F4 | Reconcile all 30 criteria, every delegated report, current issue/task/criterion/artifact identity and the committed ledger; omitted criteria remain gaps. |
| AC-F5 | Assert every gap receives verification or named-human resolution and every unresolved item forces false; successful unrelated checks cannot close it. |
| AC-V2 | Re-run audit, all old/new offline fixtures and load-bearing mutations under trusted `ci`; actual CI evidence remains separately required. |
| AC-V4 | Prove global config unchanged and Git/GitHub writes stayed with the Git Manager; reconcile final PR head, human-only merge and the open capability decisions. |

| Other original | Re-affirmation at the final gate |
| --- | --- |
| AC-A1 | Discover exactly one Orchestrator and five specialists; no new agent. |
| AC-A3 | Run the positive-language scan over every new/changed instruction (`Never`, `Do not`, imperative-negative remnants) and human-review constructive wording; permissions carry restrictions. |
| AC-A4 | Re-check effective configurable model assignments and unchanged global configuration; report provenance does not pin repository models. |
| AC-A5 | Re-run OpenCode v2.4.1 agent/config discovery after agent changes and record shared instruction loading. |
| AC-D1 | Re-run ADR lifecycle/template fixtures; no lifecycle change. |
| AC-F1 | Check the extended contract is loaded through `opencode.jsonc` for every agent. |
| AC-F2 | Validate every required report field plus new provenance/artifact/evidence fields on final reports. |
| AC-F3 | Require concrete delegation/planning/instructions/collaboration feedback in every final specialist report. |
| AC-F6 | Re-check independent plan and AI code-review gates on their exact artifacts; AC-RV1 separately adds named-human review and original-issue/all-criteria independence. |
| AC-V1 | Check the complete workflow, canonical links and documentation-versus-rules table against final text. |
| AC-V3 | Scan final files/reports for credentials, private provider settings, local secrets and reasoning traces; confirm authorised locations unchanged. |
| AC-V5 | Review the final changed-file set for workflow-only scope and record all deferred work. |

### Deferred scope and closure index

#33/#34, product implementation, additional agents, automatic model selection, live benchmarks/telemetry and advanced locking/scheduling remain deferred. OD-ROLE and OD-BRANCH implementation may stay with the human, but their decisions are open release blockers above, not silently deferred criteria.

| Finding | Closing block(s) |
| --- | --- |
| F1 | Plan identity and freeze protocol; sequence step 1 |
| F2 | Reconciliation disagreement rule and conflicting-case mutation |
| F3 | Single boolean, complete required-item set, trusted `ci`/`all` split, sequence and CI binding |
| F4 | Decisions/proposals rule and fixtures |
| F5 | Open required decisions table |
| F6 | Required-check taxonomy, CI binding and skipped-check rule |
| F7 | Documentation-versus-rules contract; canonical delegation-packet rule |
| F8 | Freeze protocol and ADR impact, including fixture-conflict provenance |
| F9 | Human-slot rule, boolean and final live re-run |
| F10 | Nine-factor sizing table and bidirectional dependency |
| F11 | Nine impeached-original and twelve other-original final-gate tables, including AC-A3 |

## Reports reconciled

| Agent | Task | Status | Received | Key findings |
| --- | --- | --- | --- | --- |
| Synthetic fixture | Planner, Implementer, Reviewer reconciliation | mixed | 2026-11-26 | Exercises omitted criterion, unverified criterion, undelegated criterion, missing report and proposed ADR conflict |
| Local discovery | OpenCode v2.4.1 agent and config discovery | completed | 2026-11-26 | Six agents discovered with expected modes; project and global config merged; shared instruction loaded |
| Tester | Independent verification | Completed | 2026-11-26 | Validator, discovery, permissions and JSON/link checks passed; two broken links and a validator-strength gap found and fixed |
| Reviewer | Independent code review, first pass | Partial | 2026-11-26 | Found R1 and F2–F8; R1 and F2–F6/F8 fixed, F7 final frozen-diff re-review pending |
| Tester | Frozen-commit verification of `498444c` | Completed | 2026-11-26 | All nine checks passed; recorded output byte-identical; `gh api` merge bypass and ADR diagnostics reported as follow-up |
| Reviewer | Frozen-diff re-review of `498444c` | Completed | 2026-11-26 | F7 closed; all 21 criteria met in the commit; F-1 `gh api` and F-2 `action: "*"` named as merge blockers, F-3 ledger state and F-4–F-8 improvements |
| Implementer | Permission hardening and RTK policy | Completed | 2026-11-26 | RTK mirroring, ask/deny matrix, credential-path denials, `gh api` allow removed, push-to-main denials, validator F-1/F-2/F-4/F-5/F-7, Go quality-tool allows |
| Implementer | Document accepted residual risks | Completed | 2026-11-26 | Added `# Residual risks` to ADR-0002; no rule, validator or fixture change; recorded output unchanged |
| Git Manager | Commit and push the hardening change | Completed | 2026-11-26 | `4d3f6dc` (parent `498444c`, 16 files, +1257/-197), staged exactly the delegated paths, validator exit 0, branch pushed, no pull request, no merge |
| Implementer | Correct the compound model and validator fidelity | Completed | 2026-11-26 | Rule set unchanged; validator splits subcommands; compound samples and a positive control; `.config/opencode` shell ask; in-memory ADR self-test; scanner documentation; recorded output regenerated |
| Tester | Delta verification of `4d3f6dc` | Completed | 2026-11-26 | Validator and 53-sample matrix green; all standalone boundaries correct; High compound-prefix bypass for the Git Manager, plus `~/.config/opencode` shell mirror and two wording gaps |
| Reviewer | Delta review of `498444c..4d3f6dc` | Completed | 2026-11-26 | F-1/F-2 closed, no new defect, no merge blocker; confirms the compound-prefix bypass at Medium and asks for precise wording plus a regression fixture; flags two wording gaps and untested validator branches |
| Tester | Final delta verification of `613c13a` | Completed | 2026-11-26 | 11/11 checks; splitter 12/12; compound matrix 48/48; four mutated ADR assertions all fail as required; scans clean; ready for the pull request |
| Reviewer | Final delta review of `4d3f6dc..613c13a` | Completed | 2026-11-26 | PR-ready with no fix required; rule set unchanged except the `~/.config/opencode` ask; splitter, two-sided samples and ADR self-test verified; one Low validator-fidelity residual (single `&`, substitutions) |
| Git Manager | Open the pull request | Completed | 2026-11-26 | PR #32 opened against `main` from `613c13a` with the prepared body file; `.tmp/pr-body.md` removed; no merge. Reported that `main` had advanced and the PR was conflicting |
| Git Manager | Fetch and merge state for the reconciliation | Blocked, then Completed | 2026-11-26 | `git fetch` and `git pull` rejected by the runtime despite the allowlist; after the human fetch, `git merge --no-commit --no-ff origin/main` produced exactly one add/add conflict in `.gitignore` and 11 staged paths from `main` |
| Implementer | Resolve `.gitignore` and normalise ADR-0003 | Completed | 2026-11-26 | Union resolution; ADR-0003 with frontmatter and verbatim decision text; both `README.md` links and the ADR index updated; `git ls-tree` allowlist in four places; recorded output regenerated |
| Git Manager | Conclude the reconciliation merge | Completed | 2026-11-26 | `f19d1c5` (parents `613c13a`, `17cf55a`), 16-path merge delta, ledger excluded, validator exit 0, no push |
| Tester | Verify the reconciliation merge | Completed | 2026-11-26 | 12 checks; Go imports byte-identical to `main`; `.gitignore` union complete; all 34 decision lines of ADR-0003 verbatim; validator byte-identical; `go vet`, `go build` and `go test` pass (22 tests, 3 packages); `git ls-tree` allowed in both forms; ready to push |
| Reviewer | Independent review of the reconciliation merge | Completed | 2026-11-26 | `f19d1c5` acceptable to push; no correctness, security, privacy or baseline regression; only permission change is the two read-only `ls-tree` allows; CI stays `contents: read`; PR #32 body stale and must be updated; validator `ADR baseline: []` is a stale-`main` artifact |
| External review (owner, GPT-6.2) | Independent review of `613c13a` | Commented, request changes | 2026-11-26 | Four P1 and three P2 findings. P1.1 (`main` integration) and P1.2 (ADR reconciliation) are substantially closed by `f19d1c5`; P1.3 (push policy, guardrail wording), P1.4 (reconciliation acceptance), P2.5 (baseline ref) and P2.7 (positive wording) are scheduled for this round; CI job, per-role tool lockdown and repo-side branch protection are escalated decisions |
| Git Manager | Handover: ledger commit, push, PR description | Partial | 2026-11-26 | Ledger committed as `97fd890` and pushed as a fast-forward; PR now `MERGEABLE`/`CLEAN`; the PR body write was denied because the text contains the literal `gh pr merge`, so the description is still the `613c13a` text |
| Orchestrator | Ledger reconciliation and handover preparation | Completed | 2026-11-26 | Every report reconciled; final coverage recorded; residuals, follow-ups and human-approval state listed below |
| Implementer | Review delta: reconciliation, push policy, baseline ref, wording, audit gate | Completed | 2026-11-26 | Verified the interrupted round instead of redoing it; added the missing `not_applicable` fixture; created the combined ADR fixture that had never existed and strengthened its assertions; rewrote `AGENTS.md` positively; ADR-0003 review note, ADR index and validation README wording; new six-property audit gate wired as the first `all` step. Found and fixed two auditor bugs of its own making and one resolver defect. |
| Implementer | Close force-push spelling gaps | Completed | 2026-11-26 | Anchored short-flag series instead of the prescribed `-*f*` (which matched branch names), plus short `-d` and remote-less `:*`; matrix 28→36 samples; docs name the forms; `audit` and `all` exit 0, recorded output unchanged. Two verified bypasses closed beyond the packet. |
| Tester | Independent verification of the review delta and the audit gate | Completed | 2026-11-26 | Fingerprint stable before and after; audit falsified against 14 patched copies and fails closed as the first `all` step; seven negative fixtures each rejected for the intended reason; combined fixture proven non-vacuous by two mutations; 53-line recorded output byte-identical; push matrix matches the delegation except the doc claim. Two audit escape shapes and one delta-introduced doc overclaim found. |
| Reviewer | Independent review of the review delta and the audit gate | Completed | 2026-11-26 | No blocker. Verified the fail-closed audit by fault injection, the bidirectional verb pin, the combined fixture as genuinely new and binding, and the trailing-deny pin as non-tautological. Eight improvements: `-ud`/`-vd` delete cluster (High), vacuous `["none"]` evidence and unvalidated supersession identity (Medium), a factually wrong `?` anchoring comment, resolvable audit evasions, audit gating only `all`, an uncorroborated owner note, and a vacuous live-tree ADR `PASS`. |
| Implementer | Close the verification findings | Completed | 2026-11-26 | Push model replaced by two shapes (option-bearing and remote-only) with the `?` enumeration removed; vacuous evidence sentinels and supersession identity/cycles enforced with three new fixtures; audit resolves `subprocess` aliases, pins verbs at every site and checks `Path(...).open(mode)`; live-tree ADR line prints `SKIP` instead of an unearned `PASS`; wording fixes in five documents and three agent files. `audit` and `all` exit 0, capture regenerated. |
| Tester | Independent verification of the round-3 fixes | Completed | 2026-11-26 | Push model deny 46/46 and a 2340-cell cluster sweep with zero non-denies; preserved writes and the compound handover form allow only for the Git Manager; vacuous evidence, supersession identity and 2-/3-cycles rejected, legitimate chain and drop semantics intact; five audit evasions now rejected with two controls still passing; `SKIP` does not hide a broken fixture; capture byte-identical, Go suite green, fingerprints reproduced. Blocked on one now-false README sentence; measured the starred carve-out as a real but bounded hole. |
| Reviewer | Independent review of the round-3 fixes | Completed | 2026-11-26 | No blocker; reproduced all three frozen hashes, re-ran a 40-command push probe, the audit evasion probes and the reconciliation cases. Confirmed I-1…I-8, with I-6 and I-7 explicitly non-behavioural by design. Four improvements: the remote-only deny is `origin`-only while the prose claims the category (fourth instance of the doc-vs-rules class), the audit still passes wildcard imports and aliased `subprocess` attributes, the false README fixture sentence, and two remaining "write/patch" sentences. |
| Implementer | Close the final review findings | Completed | 2026-11-26 | Push control inverted to an allowlist: only `git push origin <refspec>` remains allowed, so any other remote or a refspec-less push falls through to the project deny; the unreachable exact-origin deny was dropped with a stated reason and replaced by behavioural samples for non-`origin` remotes. The audit now refuses wildcard imports and rebound `subprocess` spawn attributes and resolves dotted receivers; docs state the allowlist shape and the shape-based carve-out limit. `audit` and `all` green, capture delta one line. |
| Implementer | Close the trailing-space allow edge | Completed | 2026-11-26 | The allow now requires a non-empty refspec (`?*`), so a scanner-normalised remote-only push can no longer match it; samples pin the trailing-space and double-space shapes. |
| Tester | Final verification before handover | Completed | 2026-11-26 | 34/34 resolution cells correct, fall-through proven with the Git Manager's rules removed in memory, and a mutant `?*`→`*` makes `all` fail exactly on the trailing-space sample. Gates green, capture byte-identical, Go suite green, fingerprints reproduced before and after. `PR-ready`; two documentation-level findings and one recorded design note. |
| Reviewer | Final review before handover | Completed | 2026-11-27 | `READY FOR HANDOVER`, no blocker, on the committed tree (`c9fc085`). Reproduced the tracked fingerprint, resolved all 98 push samples with zero mismatches, audited the 47 trailing-deny pins, re-ran the A–N audit probes (all rejected, legitimate direct calls pass) and confirmed the capture byte-identical. M-1…M-4 all closed. Found one Medium on the allow side of the same doc-vs-rules class — a whitespace-only tail of two or more characters still resolved to `allow` — plus a Low wording remnant of the earlier F1 fix. |
| Orchestrator | Decision on the final review findings | Completed | 2026-11-27 | Chose the rule fix over documenting the edge: a two-space tail is never part of a handover command, the deny is expressible in the existing pattern language, and closing it removes the standalone/compound inconsistency. Documentation-only acceptance would have left six claims that the rules do not produce. |
| Implementer | Close the whitespace-only allow edge | Completed | 2026-11-27 | Added the two-space trailing denies with structural pins, moved the double-space samples to the deny tables, rewrote the six falsified locations to the measurable single-space statement, and aligned the earlier comment. Five files touched, 138 insertions/69 deletions; `audit` and `all` exit 0, capture unchanged, mutant proves exactly the four new samples fail. Reported a residual tab family instead of copying an over-broad rationale sentence from the delegation. |
| Tester | Verify the whitespace fix | Completed | 2026-11-27 | 432 deny checks and 1,800 module expectations with zero mismatches; exactly four samples fail when the two new denies are removed, so the rules are load-bearing; standalone and compound now agree for the double-space family; nothing legitimate regressed; capture byte-identical, Go suite green, fingerprint reproduced before and after. `PR-ready`. Measured the tab family precisely (allow for the Git Manager, including refspec shapes, standalone and compound) and flagged that the model comment's "the one gap this pattern language leaves open" is too narrow once the tab limit is accepted. |
| Reviewer | Confirm the whitespace fix | Completed | 2026-11-27 | Confirmed the two-space family closed with the allow-then-deny ordering as the deciding pair, both tables defensible, no legitimate form regressed. Verdict `blocker`, but only on documentation truth: "the one gap this pattern language leaves open" is an exhaustiveness claim the tab shape falsifies, and the ledger claimed the limit was named in the comment when it was not. Corrected the Orchestrator's rationale: a tab-literal deny would decide, so the reason to omit it is cost and observability, not unreachability. |
| Implementer | Name the tab limit and close the documentation truth | Completed | 2026-11-27 | Replaced the exhaustiveness claim with the space-scoped statement plus a tab-limit paragraph that states the reason as cost and observability; added the limit where the closed family is enumerated; added the bare-push attribution once per document; also reworded the same closure claim in the `GIT_MANAGER_REQUIRED_TRAILING_DENIES` comment, which the delegation had not enumerated. Prose only; `audit` and `all` green, capture byte-identical. |
| Tester | Re-verify after the documentation truth fix | Completed | 2026-11-27 | No behavioural delta: the only rule delta against the previously verified tree is the two double-space denies, the samples moved as intended, `opencode.jsonc` untouched and the pin list grew by exactly those two entries. 1,800 expectations and 432 push denials reproduce, the mutant still fails on exactly four samples, `all` twice byte-identical, capture unchanged, Go suite green, fingerprint reproduced before and after. `PR-ready`; one Low precision item — "the only push that passes at the allow level" is literally false for the tab shape. |
| Implementer | Apply the granted/limit precision | Completed | 2026-11-27 | One sentence in the workflow document now states that the allow grants exactly the handover shape and that everything else either matches no allow, is re-denied, or is recorded as a limit. It rejected the suggested two-outcome clause because it omitted the tab outcome and would have reintroduced the same error class. Prose only; `all` green, capture byte-identical, fingerprint `5116b645…`. |
| Reviewer | Confirm the documentation-truth closure | Completed | 2026-11-27 | `ready for handover` on the frozen tree `5116b645…`, reproduced three times. The documentation-truth blocker is closed: the three-outcome clause is exhaustive against measured resolution, the tab paragraph states cost/observability as the reason and hedges the runtime normalisation instead of asserting it, no unscoped closure claim remains, and the validator-comment hunk is required rather than scope creep. One process note: the reconstruction command was denied by the guardrail because its text contained the denied shape — it reported the denial instead of working around it. |
| Orchestrator | Decision on the delta findings | Completed | 2026-11-26 | Rejected the "enumerate every spelling" direction: an option-first push ban (`git push -*` and `git push * -*`, plain and RTK) closes the whole family — short, clustered, four-flag, `--follow-tags`, `-q`/`--quiet`, `--dry-run` — instead of chasing spellings. The Git Manager keeps `git push origin <branch>`; the `-u` fixture and docs move to that form. Auditor hardened against aliased `subprocess` imports and unpinned direct call sites. |
| Orchestrator | Independent check of the delta before verification | Completed | 2026-11-26 | Ran the audit directly (`PASS`, exit 0) and `all` without a `FAIL` line (exit code re-confirmed by the Tester), read the new auditor, and found the `-f`/`+HEAD`/`:branch` allow gap that the round had documented but not enforced. Escalated as a targeted follow-up instead of accepting the report. |
| Implementer | Fold in the two tester wording findings | Completed | 2026-11-26 | F1: the frontmatter comment no longer calls the bare push unreachable — the project deny decides the non-`origin` and remote-only shapes, and the bare push is additionally re-denied by the agent's own required rules. F2: the body states `git push origin <refspec>` instead of the too-narrow `<branch>`/`HEAD` pair. Comment/prose only; `all` byte-identical to the capture. |
| Git Manager | Handover step 1: commit the review delta | Completed | 2026-11-26 | `c9fc085` (parent `97fd890`, 39 files, +2677/−131) staged through pathspec exclusions; ledger and `.idea/` excluded and left untouched; audit, `all`, `go build` and `go test` re-run green before the commit; no push, no pull-request command, no branch change. |
| Implementer | Write the handover texts | Completed | 2026-11-27 | Wrote the replacement pull-request description (8,688 bytes) and the point-by-point review answer (5,790 bytes) under `.tmp/handover/`, applied the Orchestrator's date correction (CI decision 2026-11-26, not 27), and touched no tracked file. |
| Git Manager | Handover step 2: commit the delta and the ledger | Completed | 2026-11-27 | `32977e1` (five files, +160/−72, staged to exactly the reviewed pathspec) and `5f55d0e` (ledger only). The staged diff re-hashed to `5116b645…` before committing, and the fingerprint was unchanged after the ledger commit. `Refs #30` appended to both messages, matching the repository style. No push in this step. |
| Git Manager | Handover step 3: push, description and review answer | Completed | 2026-11-27 | `git push origin issue-30-multi-agent-development-workflow` fast-forwarded `97fd890..5f55d0e` (three commits; `c9fc085` was also local-only, contrary to the packet). The description and the review answer were applied through the GitHub MCP server after the literal `gh pr edit`/`gh pr comment` forms resolved to deny, and both read back byte-identically. `.tmp/handover/` removed; `.idea/` untouched; no merge, no force, no branch-protection change. |
| Planner | Plan revision 1 for the 30-criterion baseline (`issue-30-baseline-30`) | Completed | 2026-11-27 | Nine newly added criteria mapped to three sequential work items with a criterion-to-file map, fixture strategy and ADR-impact note; recorded the nine as missing or partial and carried the 21 originals on a single baseline line |
| Reviewer | Independent plan review of revision 1 (`issue-30-plan-review-30`) | Completed | 2026-11-27 | `plan changes required` with F1–F11. Confirmed the three-work-item split and the sequence as dependency-correct and defensible, and that amending the ADR-0002 proposal (not a new ADR, not docs-only) is correct. Found the plan was an uncommitted working-tree section with no immutable identity, that 8 of the 21 originals are impeached and carried without re-planning, that disagreement precedence, `decision_needed`, pending proposals and a complete required-item set were unspecified, and that P1-2/P2-5 disappeared behind "Out of scope". Plan identity `e740c9b3…` over the uncommitted section |
| Planner | Plan revision 2 (`issue-30-baseline-30-r2`) | Completed | 2026-11-27 | Closes F1–F11 as a drop-in section: freeze protocol and plan identity, single `release_ready` boolean with the complete required-item set, disagreement/precedence and decision rules, required-check taxonomy, CI binding with `fetch-depth: 0`, four open required decisions (OD-ROLE, OD-BRANCH, OD-ADR-LIVE, OD-PR-INVENTORY), nine-factor sizing, a documentation-versus-rules table and the carry-forward re-verification of 21 originals. Candidate section `474f2c07…`, 23,784 bytes |
| Git Manager | Plan-only freeze commit (`issue-30-plan-freeze-commit`) | Completed | 2026-11-27 | `e881bb1` (parent `b013f04`), one path `docs/workflow/ledgers/issue-30.md`, +278/−4. Section hash measured three times — working tree, staged blob and committed blob — all `474f2c07…`, range `[13564, 37348)`, 23,784 bytes. `audit` and `all` exit 0, capture byte-identical, no push, no PR change, `.idea/` untouched |
| Reviewer | Independent plan review of revision 2 (`issue-30-plan-review-30-r2`) | Completed | 2026-11-27 | `plan approved` against `e881bb1` with identity `(e881bb1, docs/workflow/ledgers/issue-30.md, 474f2c07…)`. Reproduced hash, length, range and the naive-substring counter-case from the committed blob; F1–F11 all closed with code-level evidence; all 30 criteria covered by the plan and none carried without re-verification; ruled the extraction wording reproducible enough, so no revision 3. Raised three implementation-time clarifications (RC-1…RC-3) and confirmed the corrected ADR-baseline claim against the real ADR, the fixture and both capture scenarios |
| Implementer | WI-EV implementation (`issue-30-wi-ev-implementation`) | Completed | 2026-11-27 | Validator evidence model and release gate: required `model`/`provider`/`reviewed_artifact`, structured evidence with the five-state taxonomy, disagreement demotion to `unverified`, `decision:`/`adr:*:pending:` escalations, `check_plan_identity()` (anchored, no offsets), `evaluate_release_gate()` as the single RC-2 name, trusted `ci` and `all` modes, 15 invalid-report and 12 expected-false release fixtures, 31 in-memory release mutations and a guard-removal table; contract, workflow, `AGENTS.md`, validation docs and five agent prompts updated; capture regenerated as `ci` output (75 lines, 6,074 bytes). Claims: AC-RV1, AC-PV1 and AC-FC1 covered; AC-AI1 and AC-VB1 partial because `docs/workflow/ledgers/README.md` and ADR-0002 are owned elsewhere. Frozen-diff hash `6f87257c…` (method unrecorded), 37 modified and 22 new files, +1,783/−206 excluding this ledger |
| Tester | Independent verification of WI-EV (`issue-30-wi-ev-verification`) | Completed | 2026-11-27 | `verified with findings` against its own frozen-diff hash `4ba3b8ed…`; the Implementer's `6f87257c…` did not reproduce under ten methods. Reproduced `audit` exit 0, `ci` twice byte-identical, the capture identical, `all` exit 1 with exactly `release-record:unavailable:missing`, unchanged config and 36 sample strings with 1,800 policy tuples, and the plan section `474f2c07…` in both HEAD and the working tree. Re-derived 13 guard removals — 11 reproduced, 2 mappings inverted — and found 8 guards with no mutation at all. Seven blocking findings B-1…B-7 plus ten improvements, nearly all of the "sentence promises more than the code delivers" shape. |
| Implementer | WI-EV fix round (`issue-30-wi-ev-fixes`) | Completed | 2026-11-27 | Fixed B-1 (absent `check_state` is now `missing`, not green) and B-2 (record `artifact` must equal `pr_head`, no fallback in the release path) in code; corrected the stale `ci` capture statement (B-3); narrowed the exhaustiveness claim to the named guards plus an explicit reviewed-only list and added the two uncovered cases (B-4, B-13); adopted and documented the artifact-identity recipe in `docs/validation/README.md` (B-7); added cross-slot distinctness (B-8), hex `base_sha` (B-9), the contract's criterion-prefixed gap name (B-15) and `no_record_declared_gaps` (B-16). New identity `f12fcc21…` over 64 files, 17 invalid-report fixtures, 37 mutations, capture 77 lines / 6,255 bytes. Reported the two `scenario_blockers()`/`evaluate_release_gate()` derivations as intentionally divergent and open rather than unified |
| Tester | Re-verification of WI-EV after the fix round (`issue-30-wi-ev-reverification`) | Completed | 2026-11-27 | `verified with findings` against `f12fcc21…`, recomputed from the repository recipe over 64 files — the first reproducible identity in this work item. B-1, B-2, B-3, B-5, B-6, B-7 and the improvement set verified closed, each with its own mutation; B-4 partially closed (the list is honest but ten branch classes remain unlisted). Proved the three evidence states stay distinguishable, the old `artifact` fallback is gone, the capture is a `ci` run everywhere, and every invariant holds — `audit`, `ci` twice byte-identical, 17/12/37 counts recounted from code, `all` exit 1 with exactly one blocker, 1,800 policy tuples unchanged. Answered the AC-VB1 question by test: no frozen-diff record shape is accepted, and the only passing shape relabels the frozen diff as `pr_head`, which works only because `pr_head` is unvalidated. Seven new findings N-1…N-7, including my own corrupted ledger row. |
| Implementer | Final WI-EV round (`issue-30-wi-ev-final`) | Completed | 2026-11-27 | Implemented the human decision: `pr_head` and `artifact` validated as full 40-hex commits (`COMMIT_ID_RE`, `fullmatch`), so the equality is over two commits and the relabelled frozen-diff shape fails with exactly `artifact:invalid` plus `pr_head:invalid`; unknown record keys rejected as `release-record:unknown-key:<key>` against a closed key set; six new mutations covering CI presence and all five invalid-state slots, 47 mutations in total; contract self-contradiction fixed; commit-only binding and the re-bind obligation documented in the contract, the workflow document and the validation README; N-4 normalisation, N-5 behaviour and N-7 rendering addressed as documented judgement. New identity `11f0f2ef…` over 64 files; capture regenerated to `d7ec26a3…` (77 lines / 6,255 bytes — same size, different content, verified). |
| Tester | Final WI-EV verification (`issue-30-wi-ev-final-verification`) | Completed | 2026-11-27 | `verified with findings` against `11f0f2ef…` recomputed from the repository recipe (64 files, reproduced again after scratch cleanup) — **no blocking defect in the new guards or in the sentences changed this round**. N-2 covered: `fullmatch` rejects prefix and suffix attacks, and the relabelled 64-char shape fails with exactly `artifact:invalid` plus `pr_head:invalid`. Unknown top-level keys rejected; nested keys accepted, consistent with the contract's own wording. N-4, N-5 and N-7 covered, with `render_evidence_item` proven display-only by patching it after coverage is computed. Invariants all green, including a live `ci` run byte-identical to the capture and exactly one `all` blocker. Four non-blocking findings: F-1 `development-workflow.md` omits the 40-hex and no-frozen-diff clauses; F-2 the reviewed-only list is not the authoritative remainder and the docstring still says it is; F-3 contract line 180 still names `disagreement:<values>` without the criterion prefix; F-4 nested unknown keys are accepted. This closes WI-EV under the applied stop rule: three rounds, odd, the third with materially changed scope, no blocking defect. |
| Implementer | Doc-precision micro-round (`issue-30-wi-ev-f1-f4`) | Completed | 2026-11-27 | Closed F-1…F-4: the 40-hex and no-frozen-diff clauses now appear in `development-workflow.md` as well; the CI head-mismatch case was added and — beyond the literal ask — the Tester head-mismatch and Tester presence cases too, so the sentence is true rather than narrowed; the four reporting branches are now proven instead of relisted; the in-memory docstring no longer calls the reviewed-only list an authoritative remainder; the disagreement gap is criterion-prefixed in the contract; nested slot keys are documented as open and ignored. Mutations 47 → 51, and the printed count is now derived from the case counter so it cannot drift from the cases. Identity `1f76a98c…` over 64 files. Declared the two extensions and the derived count rather than folding them in silently. |
| Planner | ADR-0002 amendment (`issue-30-wi-ev-adr-amendment`) | Completed | 2026-11-27 | Amended `docs/adr/ADR-0002-project-specific-multi-agent-development-workflow.md` to describe what was implemented rather than what was proposed: a new decision subsection covering report provenance, the five-value check taxonomy, structured evidence and the absent-state rule, disagreement demotion, decision and proposal escalation, plan identity, commit-only artefact binding with re-bind, the named-human slot, and the `ci`/`all` split — each mapped to the code location it was read from. Added two consequence bullets for the fail-closed and attested-judgement limits, validation links, and a dated review note stating the effective `Proposed` status and separating this file's `conflicts-with: []` from the synthetic open-PR fixture. Frontmatter untouched, ADR-0001 and ADR-0003 untouched. Identity `e12f16d5…` over 65 files. Declared five things it could not describe without inventing detail instead of smoothing them over, one of which is now the finding below. |
| Reviewer | Independent code review of the WI-EV diff (`issue-30-wi-ev-code-review`) | Blocked | 2026-11-27 | No verdict produced. The delegated model returned a session usage limit on the account serving the provider before any review work was reported, so nothing was reviewed and nothing is claimed. The gate stays open: `ai_code_review` is unset and `release_ready` remains false. The Orchestrator did not substitute its own reading for the review, because a review by the party that wrote the delegations and reconciled the ledger is not independent. WI-CO and WI-CI stay blocked behind the unresolved WI-EV gate. |
| Reviewer | Independent code review of the WI-EV diff (`issue-30-wi-ev-code-review`) | Completed | 2026-11-27 | `changes required` — one confirmed fail-open blocks the pull request. Ran in a fresh session on `opencode-go/hy4`, recomputed the identity before reading anything (`e12f16d5…`, 65 files) and reproduced the plan identity from the committed blob (`474f2c07…`, 23,784 bytes). Verified all four new mutations load-bearing, the printed count derived rather than typed, and every high-risk sentence against behaviour; judged the two extra mutations appropriate rather than scope creep. **F-1 blocking:** `decision_resolution_blockers()` checks `resolved_by` only against the static identity list, so a decision recorded as resolved by the reviewer's own model identity yields `release_ready=true` with no blockers — and ADR-0002 and the validation README both promise a non-AI resolver, so the documents currently overclaim. F-2…F-5 non-blocking: an ADR bullet credits `reconcile()` with a rule enforced by `validate_report()`; the plan's 12-conjunct formula is implemented as 13, a fail-closed strengthening, and names a test that does not exist; the ledger AC table was stale; the WI-EV report's AC-RV1 `covered` claim is unsubstantiated. |
| Planner | ADR-0002 attribution fix (`issue-30-wi-ev-adr-attribution`) | Completed | 2026-11-27 | Confirmed F-2 against the code before editing: `validate_report()` enforces the every-item-`artifact` rule, `evidence_supports_covered()` requires only one content-bearing item, and `reconcile()` therefore accepts a mixed list that `validate_report()` would have rejected. Corrected the single sentence so it names `validate_report()` before `reconcile()` and describes `reconcile()`'s actual requirement. Frontmatter, `conflicts-with: []` and every other line untouched; `python3 tools/workflow_check.py adr` exit 0. Published a file-level identity only, because the Implementer was editing `tools/workflow_check.py` concurrently — the combined identity is computed by the Orchestrator. |
| Implementer | F-1 fail-open fix (`issue-30-wi-ev-f1-fix`) | Completed | 2026-11-27 | Fixed the confirmed bypass: `decision_resolution_blockers()` now takes the recorded identity set and rejects a `resolved_by` that matches a static agent name **or** an AI identity recorded in the same release record; the set is computed once in `evaluate_release_gate()` and shared with the human slot, so the two paths can no longer drift. One new mutation closes a decision with `ai_code_review.model`, count 51 → 52 and still counter-derived; removing the dynamic half makes exactly that case fail. Probed the boundary both ways: `hy4` and `HY4` are rejected, a genuine human resolver with the same record still passes, so the guard does not over-block. README count and proven-guard list propagated, capture regenerated. |
| Tester | Verification of the F-1 fix (`issue-30-wi-ev-f1-verification`) | Completed | 2026-11-27 | `verified with findings` against `ec7df78b…` over 65 files, recomputed from the recipe and reproduced again independently; frozen plan recomputed from the committed blob. Re-derived the bypass and confirmed it is closed with exactly `decision-resolution:OD-ROLE:identity`, across five variants — uppercase, `plan_review`, `login` and `reviewer` all blocked — while a genuine human resolver in a record that also names AI identities still passes, so the guard does not over-block. Proved the new mutation load-bearing by removing only the dynamic half: exactly one case flips, the other 51 still bite. Confirmed the count is counter-derived, that the capture matches a live run, and that the scope, permission tuples and single `all` blocker are unchanged. Probed the disclosed residual and found the boundary exactly as described at slot level, with one nuance in F-V1. Judged the boundary defensible rather than blocking, because the record is the trust boundary and importing external identities would break the offline determinism. Its own report misstates the prior rounds' model — see the finding below. |
| Reviewer | Re-review after the F-1 fix (`issue-30-wi-ev-rereview`) | Completed | 2026-11-27 | `code review passed with findings` against `ec7df78b…`, recomputed before reading and again after cleanup; plan identity re-derived from the committed blob. F-1 closed as reported: the identity set is computed once and shared by both paths, comparison is case-insensitive, the new mutation is load-bearing, `hy4`/`HY4`/`Hy4`/padded all blocked, a genuine human resolver still passes, and the human slot is unchanged. F-2 closed without overshoot. F-3/F-4/F-5 reconciliation verified as honest, including the coverage-semantics note checked programmatically against the 30 rows. **It overturned the Tester's classification:** the residual is a bounded fail-open, not a defensible boundary, because the control is fail-closed for human-only decisions, the protection is a denylist over optional fields, `resolved_by` carries no positive attestation of humanness, and the ADR and README still claim an unconditional non-AI resolver. Non-blocking because the reported defect is closed, the record is absent so nothing improper is being approved, and the follow-up is recorded. Raised N-1 (count propagation incomplete in two illustrative blocks), N-2 (the unqualified normative sentences) and N-3 (the AC-FC1 decision). |

The commits and the reconciliation merge were verified in sequence. The
| Implementer | WI-CO implementation (`issue-30-wi-co-implementation`) | Completed | 2026-11-27 | Added the canonical `docs/workflow/delegation-packet.md` and reduced the workflow packet section to a link; `validate_delegation_packet()` and link validation with 23 mutations; right-sized fixture `planning/right-sized.json` (nine factors, no rigid file/line count) with `validate_right_sized_work_item()` and 20 mutations; `validate_write_ownership()` with five fixtures (disjoint, overlapping, handover, stale, read-only) and 15 mutations; 19/19 guard-removal proofs. Regenerated capture: 87 lines, 7,767 bytes, `5f417bbf…`. Claims AC-PL1, AC-CX1, AC-WO1 covered; WI-EV invariants (52 mutations, 17+12 fixtures, ledger structure) stay green. Identity `cdb3246b…` over 75 files, recomputed and matching. Disclosed: two extra prompt links (reviewer, git-manager) and a stale WI-EV capture statement corrected. |
| Tester | Verification of WI-CO (`issue-30-wi-co-verification`) | Completed | 2026-11-27 | `verified with findings` against `cdb3246b…`, recomputed twice and matching (75 files, reproduced again after scratch removal). Plan identity independently extracted from the committed blob. No blocking defect. Re-proved 21 guard removals across the three new validators (more than the claimed 19), including empty-factor rejection, rigid-threshold rejection, and eight packet/link guards. Invariants hold: `audit` exit 0, `ci` twice byte-identical, `all` exit 1 with exactly one blocker, 1,800 policy tuples recomputed, no WI-CI or Go changes. Four non-blocking findings: a stale capture (ledger gained a table block after capture, 16→17), link-check overclaim for paraphrased duplicates, one untracked `.tmp`-in-`write_scope` branch, and a non-reproducible "36 sample strings" count. |
| Reviewer | Code review of WI-CO (`issue-30-wi-co-code-review`) | Completed | 2026-11-27 | `code review passed with findings` against `cdb3246b…` (75 files, recomputed twice). Fresh session that did not approve the WI-EV plan. No correctness fail-open, no conformance break, no regression. Verified all three validators, hand-mutations, instruction-only labelling, the two extra prompt links as appropriate, and invariants (`audit` 0, `ci` twice identical, `all` exit 1 with one blocker, no CI/Go changes). Capture staleness (16 vs 17 blocks) confirmed non-blocking and already tracked by the Tester. Findings F-1…F-5 below; smallest blocking set: none. |
| Implementer | WI-CI implementation (`issue-30-wi-ci-implementation`) | Completed | 2026-11-27 | Added the `workflow-validator` job to `.github/workflows/ci.yml` (+81 lines): pinned checkout, `repository`/`ref` from the PR head, `fetch-depth: 0`, `persist-credentials: false`, `EXPECTED_BASE_SHA` as an explicit commit (not a branch name), an assertion step printing expected vs actual base/head and failing on mismatch or non-ancestry, then `audit` + `ci` — never `all`, no `continue-on-error`, `pull_request`-only. Implemented `validate_ci_workflow_contract()` with 27 guards, 31 mutations, all proven load-bearing. Regenerated capture: 88 lines, 8,041 bytes, `a757c97e…` (refreshed at pre-handover; the live run is byte-identical to the capture now). Claims AC-CI1 **partial**: the static/offline half is covered; the run/job/step/log half is unverified because no Actions run was triggered. Identity `f445b095…` over 76 files, recomputed and matching. |
| Tester | Verification of WI-CI static half (`issue-30-wi-ci-verification`) | Completed | 2026-11-28 | `verified with findings` against `f445b095…` (76 files, recomputed twice, matching). Static half of AC-CI1 covered; run half `unverified` as expected. 18 independent CI mutations flip with their named blockers, four plan-mandated classes proven, 31/27 counts recounted, plan identity extracted from the committed blob, base SHA == `origin/main` == ancestor of HEAD, `ci.yml` +81/-0, `jactionlint` clean. New finding F-1: capture one line stale (239 vs 243 data rows) for the same ledger-mutability reason as WI-CO. |
| Reviewer | Code review of WI-CI (`issue-30-wi-ci-code-review`) | Completed | 2026-11-28 | `code review passed with findings` against `f445b095…` (76 files, recomputed before reading). Word-for-word plan conformance verified, all 27 CI guards independently re-proven by weakening, fork/base/skip design judged sound, no doc claims a static check proves a run, AC-CI1 honestly `partial`. Findings are the recurring capture staleness (239→243), two "contract proves" sentences wider than the guards, the stale AC row (now reconciled), and present-tense looseness. Smallest blocking set: none. |
| Planner | WI-CO/WI-CI ADR amendment (`issue-30-wi-co-ci-adr-amendment`) | Completed | 2026-11-28 | Amended ADR-0002 with four Decision subsections (right-sized, canonical packet, write ownership, CI validation), each mapped to code locations read from the implementation and with the unproven limits stated in the ADR itself (judgement-only factors, field-presence-only packet check, record-only ownership check, text-parser limit + anonymous fetch + constant base). Frontmatter untouched (`status: Accepted` declared, effective `Proposed`, `conflicts-with: []`). Also disclosed a packet-vs-validator gap (criteria coverage_target not enforced). Identity `54893f97…` over 76 files (was `f445b095…`), recomputed and matching. |
| Implementer | Release-record draft + 21 originals re-verification (`issue-30-release-record-draft`) | Completed | 2026-11-28 | Draft at `.tmp/issue-30-release-record-draft/release.json` (30 criteria, 2 reports, CI slot `passed/inspected` from run 46081689891/job 140781893967/base 17cf55aa…, `human_review: skipped` not fabricated, four OD decisions open, three proposals pending). `all` with the draft → exit 1, `release_ready=false` with 60 blockers, all for the right reasons (missing orchestrator/planner/reviewer/git-manager reports, missing human review, open decisions/proposals, partial criteria). Re-verified the 21 originals at `171d3d9`: 19 covered, AC-D2 partial (live SKIP, OD-ADR-LIVE), AC-F6 partial (no integrated AI review artefact at that head yet). Fail-closed probes confirmed no AI-resolver bypass. No ledger or live-record write. |
| Git Manager | Handover commit/push + Actions run (`issue-30-handover-commit`) | Completed | 2026-11-28 | Commits `aaa627d` (76 files, +6,123/−258, implementation) and `171d3d9` (1 file, ledger), pushed `b013f04..171d3d9` (no force, no merge, `main` untouched, `.idea/` untracked). PR #32 description replaced (10,695 chars, 30 ACs, ADR inventory) and read back on the head. `ci` byte-identical to capture (`a757c97e…`), `jactionlint` clean, identity `c548dfb6…` reproduced three times including on the committed head. **Actions run 46081689891 / job 140781893967 `success` on head 171d3d9**: expected==actual head `171d3d9…` and base `17cf55aa…` in the log; the other five jobs also pass. This is inspected CI evidence for AC-CI1 — `release_ready` explicitly not claimed. |
| Reviewer | Integrated final-head review (`issue-30-final-head-review`) | Completed | 2026-11-28 | `passed with findings` — this report is the single integrated AI code review of the complete change set `17cf55aa..171d3d9` on the committed head, bound to `171d3d9` (not a frozen diff). Accepted as the AI half of AC-F6/AC-RV1. No blocking defect. Confirmed: no semantic change since WI-CI (ADR amendment + capture + ledger only), no Go files in the diff, capture byte-identical, CI shape honest, 31/27 counts re-proven. Human half does not exist; release_ready remains false. Findings: working-tree drift, ai_code_review pre-declared (now substantiated), CI run-half contributor-reported, AC-D2 wording, AC-FC1 partial. |
frozen-diff reviews cover `498444c`, the delta reviews cover `4d3f6dc`, the
final delta reviews cover `613c13a`, the merge review covers `f19d1c5`, and the
review-delta round covers the working tree on top of it, now committed as
`c9fc085`. Both final reports declared `613c13a` ready for pull-request
creation, the merge reports declared `f19d1c5` ready to push, and the final
Tester report declared the review delta `PR-ready` before the commit. The
Reviewer's fifth pass over that delta closed it with `ready for handover` on
the frozen tree `5116b645…`, and the Git handover then pushed and published it.

The synthetic reports are fixtures, not reports from real subagent sessions for
this issue. They validate the reconciliation rules. The pull request is subject
to the independent review and human-approval gate before merge.

### Agent model provenance (AC-PV1)

Repository files pin no model and hold no credential, so a model change produces
no diff and no fingerprint change. The effective assignment is read from the
global configuration with `opencode debug agents` and was checked on
2026-11-27:

| Role | Effective model | Note |
| --- | --- | --- |
| orchestrator | `opencode-go/muse-ember-1.0` | switched 2026-11-27 to `muse-ember-1.0`; was `deepseek-v4.1-flash`. Note: running on `opencode-go` (subscription rail), not `opencode` (pay-per-token) |
| planner | `opencode/gemini-4-hydrogen` | switched 2026-11-27 for cost reasons; revisions 1 and 2 were `console-ollama/kimi-k3.1-pro` |
| reviewer | `opencode-go/hy4` | provider moved 2026-11-27; model unchanged |
| implementer | `opencode-go/deepseek-v4.1-flash` | switched 2026-11-27; a `depseek` typo was caught by the provenance check and corrected the same day |
| tester | `opencode/mistral-large-4` | moved to the pay-per-token rail and changed model 2026-11-27; the three WI-EV verification rounds were `deepseek-v4.1-flash`, so the handover re-bind is produced by a different instrument |
| git-manager | `opencode-go/deepseek-v4.1-flash` | provider moved 2026-11-27; model unchanged |

The human moved the workflow from the `console-ollama` provider to `opencode-go`
on 2026-11-27 after a session usage limit, and the effective assignment was
re-read with `opencode debug agents` afterwards; the models are unchanged apart
from the earlier Planner switch. Reports produced before the move name
`console-ollama` and stay valid evidence for the round that produced them.
AC-PV1 binds provenance to the report, not to this table, so a provider change
does not retroactively invalidate a verdict. Every delegation after the move
must state the provider it actually ran on, and the Reviewer's code review is
the first gate on the new provider — if that report names a different provider
than this table, the report wins and the table is corrected.

The two provider identifiers are the same provider under two billing models,
clarified by the human on 2026-11-27: `opencode-go` is the subscription with a
session usage limit, `opencode` is pay-per-token. Capacity is therefore a
property of the billing rail, not of the provider, and a role that hits the
subscription limit must either move to the pay-per-token rail or wait. That is
a cost decision, not an architectural one, so it stays with the human.

The subscription rail is capped rather than metered: its limit is a rolling
window that resets every five hours, not an absolute exhaustion, so a blocked
gate is a delay rather than a failure. That distinction matters for the ledger: a
throttled gate must never be recorded as a verification result, not even as
`failed`, because no evidence was produced either way. It also means a retry is
worth attempting before any paid rail is considered — the fresh review session
below is exactly that probe.

Three capacity models are in use across providers and they fail differently,
which is the only part the workflow needs: usage-capped subscriptions throttle
per window and reset within hours; token-bundle subscriptions are a monthly
budget that can be spent in full and is refilled at the next cycle; metered
pay-as-you-go bills and does not block. The workflow records the rail and its
failure behaviour. It does not record the plan tier, the price or the account:
that is personal configuration and stays in the authorised local location,
which is also what keeps a paid rail from looking equivalent to a capped one
when the two are compared later.

Model and rail are coupled, because each provider serves its own set of models.
Moving a role to a different rail therefore usually means changing its model as
well — the Tester's move above is the example, and the earlier attempt to keep
`hy4` unchanged worked only because the same model happened to be served on a
second rail. A provider move is never a neutral operation in this workflow: it
changes the instrument, and with it the independence structure between
implementation, verification and review. Any future move must be recorded as a
model change and judged as one.

Because the quota sits on a legacy tier, the subscription rail is best treated
as opportunistic capacity for short gates rather than as the base for long
ones. A full code review, a CI round trip or the handover re-bind should be
planned so that a five-hour throttle delays one step instead of stalling the
chain — either by batching them inside one window or by running them on the
pay-per-token rail.

The limit itself still fails every role on the subscription rail at once, and it
fails them closed. That is an availability property, not a correctness one, and
it is the reason the blocked review recorded above was not worked around — the
alternative would have been an orchestrator reviewing its own delegation, which
would satisfy the slot's shape and none of its purpose.

The Tester moved to `opencode/mistral-large-4` on 2026-11-27, which is a model
change and not only a billing change: the Implementer stays on
`deepseek-v4.1-flash`, so verification and implementation are now different
model families. That is the independence the three WI-EV rounds lacked — those
rounds had the same model implementing and verifying. It also means the
handover re-bind is a different instrument from the rounds it re-binds, which is
what the closing rule asks for and what the report must say rather than
presenting the re-bind as a repetition of the third round.

The Orchestrator moved to `opencode-go/muse-ember-1.0` on 2026-11-27 (verified
via `opencode debug agents`), changing from `deepseek-v4.1-flash` after the
WI-EV code review. This breaks the prior coupling where Orchestrator and
Implementer were both DeepSeek — the pair where correlated misunderstanding is
most expensive — and gives WI-CO a different framing instrument. Current
distinct families: Planner `gemini-4-hydrogen`, Orchestrator `muse-ember-1.0`,
Implementer/Git-Manager `deepseek-v4.1-flash`, Tester `mistral-large-4`,
Reviewer `hy4`. Implementer/Git-Manager remain shared, which is acceptable
because the Git Manager performs mechanics, not judgement. Reports after the
switch must name the new Orchestrator provenance.

A seventh agent, `docs-auditor` (primary, now `opencode/claude-haiku-5-5`),
exists in the global configuration and its model changed on the same day. It is
not one of the six workflow roles: it produces no plan, implementation,
verification or review, appears in no gate and can therefore contribute no
evidence. If it is later used as a workflow instrument it needs a role, a report
format and a position in the gate order first; until then its output is advisory
and must not be cited as support for any criterion.

The human switched the Implementer and the Tester from `glm-5.3-flash` to
`deepseek-v4.1-flash` on 2026-11-27. Reports from earlier rounds therefore carry
GLM provenance and reports from WI-EV onwards carry DeepSeek provenance. Both
stay valid evidence for the round that produced them; AC-PV1 requires each report
to state its own model and provider rather than assuming the current assignment.

The Planner moved from `console-ollama/kimi-k3.1-pro` to
`opencode/gemini-4-hydrogen` on 2026-11-27 for cost reasons, chosen over the
same model served as `console-openrouter/google/gemini-4-hydrogen` so the
billing stays with the OpenCode provider. Plan revisions 1 and 2 are kimi-authored; a revision
3, if the plan review requires one, is authored by the new assignment and must
name it in its report. The section hash, not the author, is the identity that
binds implementation to the plan.

### Write ownership for WI-EV (AC-WO1)

| Task | Agent | Write scope | May read | Must not touch |
| --- | --- | --- | --- | --- |
| `issue-30-wi-ev-implementation` | Implementer | `tools/workflow_check.py`, `docs/workflow/feedback-contract.md`, `docs/workflow/development-workflow.md`, `AGENTS.md`, `docs/validation/**`, and the `.opencode/agents/*.md` files only where a WI-EV criterion requires it | the frozen plan at `e881bb1`, the validator, the fixtures | `docs/adr/**` (Planner-owned), `docs/workflow/ledgers/**` (Orchestrator only), `.github/workflows/**` (WI-CI) |
| `issue-30-wi-ev-adr-amendment` | Planner | `docs/adr/ADR-0002-project-specific-multi-agent-development-workflow.md` only | the implementation outcome | a status change, ADR-0003, the ledger, the validator |

Sequence: the Implementer runs first and the Planner's ADR amendment follows, so
the proposal describes what was implemented rather than what was intended.
Tester and Reviewer stay read-only. Every task uses `.tmp/<task-id>/` as its
scratch and removes it before reporting. The plan section in this ledger is
frozen; only the Orchestrator writes the ledger.

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
| Low | F7: the review targeted a moving, uncommitted tree. | Froze the tree as `498444c`, recorded the SHA and re-ran Tester and Reviewer against that commit. Both reported on the immutable diff. | Resolved |
| Medium | F-1 (Tester and Reviewer): the Git Manager's `gh api*` allow permitted a REST pull-request merge, so the human-only merge boundary was enforceable only by convention. | Removed the `gh api*` allow, kept `gh api*`/`gh pr merge*` denied project-wide and re-denied them last in the Git Manager, and added validator assertions for REST, `-X PUT`, GraphQL and RTK forms. | Resolved |
| Medium | F-2 (Reviewer): an `action: "*"` allow rule in a non-Git-Manager agent passed the validator because only `action: shell` was filtered. Reproduced with `planner` and `git notes*`. | Wildcard actions are treated as shell-capable; any `action: "*"` allow is rejected project-wide, and `docs/validation/fixtures/permissions/planner-broad-allow.md` is a regression fixture. | Resolved |
| Low | F-4 (Reviewer and Tester): ADR reference validation missed `superseded-by`, treated known-but-non-accepted merged ADRs as unknown, and could silently drop a conflict on an id collision. | Validate `supersedes`, `superseded-by` and `conflicts-with` against all known ADR ids, keep the accepted baseline separate for escalation, reject proposal-id collisions and make the non-accepted-conflict error reachable. | Resolved |
| Low | F-5 (Reviewer): extra agent files and agent files without `mode` passed validation. | Require exactly the six agent files and a `mode` key in each. | Resolved |
| Low | F8: `.gitignore` did not guard local overrides or environment files. | Added `.env*`, `opencode.local.json(c)` and `*.local.json(c)` patterns. | Resolved |
| Low | F-7 (Reviewer): body-only edits to accepted ADRs were not detected and `check_reports` used "includes" checks, so unexpected gaps passed. | Added a SHA-256 of the ADR body to the signature and assert exact expected gap and escalation sets for the fixture. | Resolved |
| Informational | Tester findings 3 and 5: `adr` standalone runs only the actual-repository check, and the recorded output depends on the `main`/`origin/main` ref state. | Corrected the validation README wording and documented the capture conditions next to the recorded output. | Resolved |
| Low | Tester finding 4: `adr_from_text` builds its default id eagerly and raises `IndexError` for a stem without a dash. Latent only; real call sites use `ADR-*.md`. | Not changed in the hardening round; recorded as a small validator follow-up. | Open |
| Decision | RTK mirroring: `rtk git`/`rtk gh` are pass-throughs, `rtk test`/`err`/`summary` execute hidden commands, `rtk bypass`/`proxy` are escape hatches. | Mirror every plain rule in RTK form, deny `rtk test`/`err`/`summary`, ask for `bypass`/`proxy`, and ask for RTK commands touching paths outside the worktree. | Implemented |
| Decision | Tooling scope: the project is Go with a Python validator and does not use Node or .NET. | `go`, `govulncheck`, `golangci-lint` and `jactionlint` are allowed, including narrow `rtk test` filters; `pnpm` and `dotnet` are denied; `docker`, `kubectl`, `oc`, `aws`, `psql` and `wget` require approval. | Implemented |
| Decision | Credential and path handling. | Deny credential stores for read, edit, external access and shell strings; `~/.config/opencode/*` is approval-only; access outside the worktree requires approval; scratch work belongs under `.tmp/`. | Implemented |
| High (downgraded) | Delta F-1: under the validator's whole-string model, a Git Manager compound command whose first verb matches a start-anchored allow resolves to `allow`, so `git fetch origin && gh pr merge 1`, `git commit -m x && gh api …/pulls/1/merge` and `git stash && git push origin main` appeared reachable. The Tester rated it High; the Reviewer rated it Medium. | Orchestrator checked the official V2 permissions documentation: shell checks use a scanner and apply the rules to every extracted subcommand, and any deny denies the operation. The runtime therefore already denies those compounds; the gap was a validator-model artifact. The validator now splits compounds on common separators, the compound samples and a positive control are asserted, and ADR-0002, the workflow document and the discovery record describe the scanner. No wildcard deny rules were added. | Resolved |
| Medium/Low | Delta F-2: `~/.config/opencode/*` has read, edit and external_directory asks but no shell-string rule, so `cat ~/.config/opencode/opencode.json` resolved to `allow`, contradicting the approval-only wording. | Added a shell `ask` mirror (not deny, per the owner's instruction), asserted for all six agents, and aligned the wording in `AGENTS.md` and the ADR. | Resolved |
| Low | Delta F-3: the ADR "Minor friction" example was wrong; `rtk * ~*` does not match `HEAD~1` because the pattern needs a space before the tilde. | Reworded the example to home-path arguments such as `rtk read ~/x`. | Resolved |
| Low | Delta F-4: `AGENTS.md`, ADR-0002 and the workflow document referred to "the committed `.env.example`", but the tree has no such file; only `.gitignore` keeps the exception. Both reviewers flagged it. | Reworded to "an `.env.example` or `*.env.example` template, if present" in all four places. | Resolved |
| Low | Reviewer F-3: validator coverage gaps — `ENV_ALLOW_SHELL_SAMPLES` was dead code, the ADR body hash only ran on `main`, and the F-4 branches (id collision, unknown `superseded-by`, non-accepted conflict) were not exercised by a fixture. | The environment sample is asserted, and an in-memory ADR self-test now covers the body hash, unknown `superseded-by`, id collision, non-accepted conflict and the status mapping. | Resolved |
| Low | Final delta: the validator splits only on `&&`, on the double-pipe operator, on `;`, on a single pipe and on newlines, so a single `&`, `$()` or backtick compound can resolve to `allow` in the model. The runtime shell scanner splits `&` and fails closed for commands it cannot analyse, so the enforcement boundary is intact. | Recorded as a validator-fidelity residual. No rule or code change before the pull request; extending the splitter is a follow-up if strict model fidelity is wanted. | Open |
| Low | Final delta: `docs/validation/README.md` phrases the environment exemption as "except `.env.example`" while the rules and `AGENTS.md` allow any `*.env.example` template. | Closed in this round: the wording is aligned to an `.env.example` or `*.env.example` template. | Resolved |
| Medium | `main` advanced to `17cf55a` when PR #31 (Go and Bubble Tea bootstrap, #27) was merged after the branch was frozen, so GitHub reported PR #32 as `CONFLICTING`. The only Git conflict was an add/add on `.gitignore`. | Merged `main` into the branch with a merge commit, resolved `.gitignore` as the union of both rule sets, and left the Go imports byte-identical to `main`. | Resolved |
| Medium | The merge brought in `docs/adr/0001-go-bubble-tea-bootstrap.md`, which used a second ADR convention, a header-style status and the number `0001` twice. The validator discovers only `ADR-*.md`, so that merged ADR would have stayed invisible to the baseline. | Human decision: normalise. Renamed to `ADR-0003`, added frontmatter with `status: Accepted`, preserved the decision text verbatim, updated both root `README.md` links and the ADR index. The normalised file stays a proposal until PR #32 merges. | Resolved by human decision |
| Medium | `git fetch` and `git pull` are on the Git Manager's allowlist yet the runtime rejected both plain forms during the reconciliation, so the work stalled until the human ran `git fetch origin main`. The validator models the rule list and cannot detect this mismatch. | Recorded as a policy/runtime mismatch. No policy change mid-pull-request beyond the owner's `git ls-tree` request; the human fetched once. Follow-up: reproduce and correct the resolution for `git fetch`/`git pull`. | Open |
| Informational | Owner request during the reconciliation: add read-only `git ls-tree` to the permission model. | Added `git ls-tree*` and `rtk git ls-tree*` at project level, `"ls-tree"` to `GIT_READ_COMMANDS`, and the command to the read-only enumeration in `docs/workflow/development-workflow.md`. | Implemented |
| Informational | Tester F1 and Reviewer: the actual ADR-0003 normalisation differed from the delegation's expected-difference list in two template-mandated ways — a `# Decision` heading before the five subsections and the heading normalised to the literal `# Consequences`. Neither changes decision text; the containment check confirmed all 34 decision lines remain verbatim. | Recorded as a delegation-precision note, no code change. Future ADR normalisations should derive the expected surface from `docs/adr/template.md`, not from the implementer's report. | Resolved |
| Informational | Git Manager and Reviewer: the merge had staged the old `docs/adr/0001-…` as `A`, so `git rm` required `-f`; content preservation was verified first against `ADR-0003`. The step-2 `git diff --check` also ran while `.gitignore` was still `AA`, so its clean exit was weaker evidence than it looked. | Recorded as a process note for future merge packets: expect `git rm -f` for merge-staged renames, and run `--check` after the conflict is staged. | Resolved |
| Medium | Reviewer RP-10: the PR #32 description describes the branch as of `613c13a`. It claims the last commit is the ledger update touching "no workflow, rule, validator or fixture file", lists three commits, names only ADR-0001/0002 as proposals, and states "main has no accepted ADR yet" and "accepts both". After `f19d1c5` every one of those statements is wrong. | PR description is refreshed at handover: fourth commit row, the `.gitignore` union, the ADR-0003 normalisation with its proposal status, the `git ls-tree` allow, and the Go/Bubble Tea decision already in force on `main` through PR #31. | Open until the description is updated |
| Low | Reviewer RP-9: the validator's live-tree line `ADR baseline (merged, accepted): []` is an artifact — `resolve_baseline_ref()` prefers the stale local `main` (`73dbbec`, pre-PR #31, no `docs/adr`) over `origin/main`, and `adrs_from_ref` filters `ADR-*.md`, so the in-force legacy bootstrap record is invisible. It must not be read as "main has no accepted ADR". | Closed in this round: the resolver prefers `origin/main`, warns when the two refs disagree, and states explicitly when the chosen ref holds no `ADR-*.md` record. | Resolved |
| Low | Reviewer RP-5: `docs/adr/README.md` says "ADR-0003 records the issue #27 bootstrap and was merged with PR #31". Strictly, PR #31 merged `0001-go-bubble-tea-bootstrap.md`; the `ADR-0003` file exists only through PR #32. The following sentences disambiguate, so there is no overclaim. | Closed in this round: the sentence now attributes the decision, not the normalised file, to PR #31; the disambiguation sentences and the table row are unchanged. | Resolved |
| P1 (external R-1) | The branch did not contain `main` after PR #31 merged at `17cf55a`; `.gitignore` was an add/add conflict and GitHub reported the pull request non-mergeable. | Closed by `f19d1c5`: `main` merged, `.gitignore` union, Go imports byte-identical, GitHub now `MERGEABLE`/`CLEAN`, and the merge independently re-reviewed. | Resolved |
| P1 (external R-2) | The validator discovers only `ADR-*.md`, so the merged legacy `0001-go-bubble-tea-bootstrap.md` was invisible, and the number `0001` was used twice. The external reviewer asked for an explicit human decision on its status instead of silent acceptance. | Closed by ADR-0003: unique ids `ADR-0001/0002/0003`, frontmatter, README index and links. The owner explicitly confirmed `status: Accepted` on 2026-11-26 because the decision is already in force on `main` through PR #31; the decision is recorded in the ADR review notes and here. Combined-layout fixture is added in this round. | Resolved by human decision |
| P1 (external R-3) | The permission policy is a command-string guardrail, not a sandbox: unmatched operations resolve to `allow`, the Go toolchain and inherited global tools/MCP are outside the role boundaries, `git push*` allows force/mirror pushes, and `git push origin +main` bypasses the `main` destination denials. | This round: deny force, mirror, delete and `+main` push forms, state the guardrail boundary in ADR-0002, the workflow document and `AGENTS.md`, and add an explicit feature-branch handover rule. The long spellings alone left `git push -f`, a `+HEAD` force refspec and a `:branch` delete refspec allowed for the Git Manager; the Orchestrator found this while checking the rules and the follow-up round closes it (see the force-spelling finding below). Per-role tool/MCP lockdown is an architecture decision escalated to the human. | Resolved for push forms; role lockdown decision open |
| P1 (external R-4) | `validate_report` checks only field presence and the coverage enum; `reconcile` marks a criterion `covered` from any claim, including empty evidence, and ignores `issue`/`task_id` identity and contradictory entries. That contradicts the feedback contract's reconciliation rules. | This round: require non-empty evidence for `covered`, validate `issue` and `task_id` against the scenario, surface contradictory claims as a disagreement gap, and add negative fixtures for empty evidence, wrong issue/task, conflicting reports and an explicit missing requirement. Implemented with seven negative fixtures (empty evidence, wrong issue, wrong task, conflicting reports, explicit missing, supersession that drops a report, `not_applicable` without a note), each asserted in every `all` run. | Resolved, pending independent verification |
| P2 (external R-5) | `resolve_baseline_ref()` prefers a possibly stale local `main` over `origin/main`, so the live-tree baseline line can be wrong; an unchanged merged non-accepted ADR can collide with a proposal. | This round: prefer `origin/main`, fall back to `main`, and print a warning when the two refs disagree or the baseline is stale. Implemented; the resolver now also requires an `ADR-*.md` record to consider a ref authoritative and states explicitly when the chosen ref yields none, so the honest note can fire on the real `origin/main`. | Resolved, pending independent verification |
| P2 (external R-6) | The ledger handover section still described a running review and no pull request while the PR claimed completion; no workflow validation runs in GitHub Actions for this head. | The ledger was reconciled in `97fd890` and this entry. The owner decided on 2026-11-26 that the CI validator job is not part of this pull request; it stays a post-merge follow-up because it changes the CI contract inherited from #31. | Partially resolved, CI job deferred by owner |
| P2 (external R-7) | `AGENTS.md` uses imperative negatives ("Never", "Do not") although AC-A3 asks for positive, actionable language. | This round: rewrite the working agreements and data rules as permitted responsibilities, approved locations and escalation paths, keeping the machine-readable denies as the enforcement layer. Implemented; a grep for `Never`/`never`/`Do not` in `AGENTS.md` is empty, every technical fact is preserved, and the document now states that the permission model is a guardrail with default-allow, not a sandbox. | Resolved, pending independent verification |
| Medium | Git Manager finding: the runtime denies every shell command whose text contains `gh pr merge`, including a heredoc that only writes Markdown. The prepared PR description could therefore not be created from the shell. | The description is written with the file tool instead of the shell in this round and applied with `gh pr edit`. Recorded as a policy over-match on documentation text next to the `git fetch`/`git pull` mismatch. | Workaround identified, policy follow-up open |
| Informational | Owner request: a way to test that the validator is correct and carries no risk before executing it. Today the script is stdlib-only, reads files only, calls `git` without a shell and has no network imports, but nothing enforces those properties. | New `tools/audit_validator.py` statically audits `tools/workflow_check.py` (import allowlist, no eval/exec/shell, `git`-only subprocess with read-only verbs, no write access, no network modules). `workflow_check.py all` runs it first; documented as a guardrail, not a sandbox. The CI job stays deferred. Implemented as six property groups (`ast`/`sys`/`pathlib` only), `PASS audit:` on success, `FAIL audit:` on stderr, `check_self_audit()` as the first `all` step; during development the auditor's own negative probes caught two auditor bugs (an unwired `open()` write-mode check and a `Path` dataflow blind spot), both fixed before finalising. | Implemented, pending independent verification |
| High | Orchestrator check before verification: the documented push rule claimed "any force spelling", but the deny block covered only the long spellings. With the Git Manager's `git push*` allow winning, `git push -f origin HEAD`, `git push origin +HEAD` (force refspec) and `git push origin :feature` (delete refspec) resolved to `allow`, and the validator matrix had no sample for them. | Short-flag, force-refspec and delete-refspec denies added in plain and RTK form without weakening the existing denies; matrix samples added for all four forms; `AGENTS.md`, the workflow document and the validation README name the short `-d` and both refspec forms. The prescribed naive `git push -*f*` was rejected during implementation because `fnmatch` lets it match branch names (`git push -u origin issue-30-…workflow`); an anchored series (`-?f*`, `-??f*` and their mid-command forms) denies one- and two-flag clusters without touching a refname after the space. The implementer also closed two bypasses beyond the packet: the short `-d` of the already-denied `--delete`, and the remote-less `:feature` delete refspec whose comment had wrongly claimed the bare-push deny covered it. | Resolved, pending independent verification |
| Low | Residual after the short-flag hardening, stated in the rule comment: reordered clusters such as `-ud`/`-vd`, four-flag clusters, and legal refnames containing `+` are not covered; `--follow-tags` is denied as a side effect. | Accepted: deleting `main` stays denied through the destination rules regardless of flags, so the uncovered spellings can only affect feature refs; the Git Manager's legitimate writes (`origin HEAD`, `-u origin <branch>`, the compound allow fixture) were re-verified as allowed. Recorded for the Reviewer to confirm the trade-off rather than silently widened. | Superseded by the option-first push ban below |
| High | Tester finding: the delta-introduced wording "any force spelling (long or short) … stay denied" in `AGENTS.md`, `docs/validation/README.md` and `docs/workflow/development-workflow.md` is falsified — measured `git push -uvqf origin feature` → `allow` for the Git Manager. The same probe family exposed an undocumented residual: option-only pushes with an implicit upstream (`git push -q`, `--quiet`, `--dry-run`) stay allowed, and `git push origin` with an implicit refspec is equally unguarded. Third instance of the "documentation claims more than the rules" class in this pull request. The Reviewer independently rated the `-ud`/`-vd` delete cluster High: a `-d` hidden in a flag cluster bypasses every delete deny. | Root cause is the enumeration approach itself: each new spelling needs a new pattern. Decision: deny option-first pushes outright (`git push -*` and `git push * -*`, plain and RTK), which subsumes every short, clustered, four-flag and long spelling including `--follow-tags`, `-q`/`--quiet` and `--dry-run`; the Git Manager keeps explicit `git push origin <branch>` / `git push origin HEAD` writes, and the `-u` compound fixture moves to that form. Docs then state the rule instead of listing spellings. | Implemented, verified |
| Medium | Tester finding: two shapes that violate the read-only invariant pass the audit — an aliased import (`import subprocess as sp; sp.run("git push --force origin main", shell=True)`) and a direct `subprocess.run(["git","push",…])` with an unpinned verb, because the verb pin keys only on the local `git()` helper. No shipped defect: `subprocess` occurs in the validator only inside `git()` with a literal `["git", *args]` list. | Hardening delegated: resolve import aliases for `subprocess` (including `from subprocess import run as r`), apply the forbidden-call, `shell` and shape checks to alias receivers, and pin the git verb at every `subprocess` call site rather than only the helper. Remaining escape shapes (`getattr`, `globals()`) stay inside the documented "guardrail, not sandbox" limit. The Reviewer confirmed the same evasions independently and added `Path(...).open("w")`, which the Path dataflow should classify as a write. | Implemented, verified |
| Medium | Reviewer I-2: `evidence: ["none"]` is accepted as support for a `covered` claim, although the feedback contract uses `none` as the explicit no-content sentinel; likewise `n/a`, `-`, `None` and `no evidence`. The negative fixture only covered an empty list. | Vacuous sentinels are filtered before the `covered` check, and a `covered-with-sentinel-evidence` fixture pins the case. | Implemented, verified |
| Medium | Reviewer I-3: supersession identity was unvalidated. A `reviewer` report could supersede an implementer task and drop that report; a phantom task id was accepted and dropped nothing; self- and cyclic supersession would drop both reports. | `supersedes` must name a task declared for the same agent in the scenario; unknown, cross-agent, self and cyclic cases are rejected, with negative fixtures. The legitimate `supersedes-drops-report` fixture keeps its semantics. | Implemented, verified |
| Low | Reviewer I-4: the comment claimed `?` matches "exactly one flag letter and never a space"; measured, `fnmatch.fnmatchcase("a b", "a?b")` is `True`. The rules behaved correctly, the explanation did not. | The `?`-based enumeration is removed by the option-first rule, so the false explanation disappears with it; the implementer confirms no `?` pattern remains or corrects the wording. | Implemented, verified |
| Low | Reviewer I-6: only `all` runs the audit, so `config`, `adr`, `reports` and `fixtures` return unaudited results. | Documented explicitly: `all` is the trusted entry point, the subcommands are diagnostics. No code change, stated instead of implied. | Implemented, verified |
| Low | Reviewer I-7: the ADR-0003 owner-confirmation note asserts an external human action that nothing in the repository corroborates. | The note references where the confirmation is recorded (the PR #32 review and ledger entry R-2), keeping date and substance. | Implemented, verified |
| Low | Reviewer I-8: with a baseline ref that has no `ADR-*.md`, the live-tree ADR step printed `PASS adr: …` although nothing was asserted, and the recorded output bakes in the current `main`/`origin/main` SHAs. | The live-tree step prints an explicit `SKIP` line when the ref has no ADR records, and the recorded output is labelled as an illustrative snapshot of the current ref state. The fixtures keep the real assertions. | Implemented, verified |
| Medium | Reviewer M-1: the remote-only deny covers only `origin`, while five prose locations describe the category "a push that names a remote but no refspec". Measured: `git push upstream` and `git push github` → `allow` for the Git Manager. Fourth instance of the documentation-claims-more-than-the-rules class. | Fixed structurally, not by wording: the Git Manager's broad `git push*` allow is narrowed to `git push origin ?*` — a non-empty refspec after the remote — so any push that does not name `origin` and a refspec falls through to the project-level `git *` deny. The prose then states the allowlist shape ("only `git push origin <refspec>`"), which is both stronger and simpler than a deny category. | Implemented, verified |
| Low | Implementer finding, raised after its own fix: `git push origin ` with a trailing space still matched the allow, because `*` also matches the empty string — a normalised remote-only push would have been allowed again. | The allow now requires one character after the remote (`?*`), closing the empty-refspec shape without touching any legitimate form; the trailing-space and double-space shapes are pinned as samples and a mutant run proves the sample bites. | Implemented, verified |
| Medium | Reviewer final-1 (fifth instance of the doc-vs-rules class, this time on the allow side): the `?*` allow admits a whitespace-only tail of two or more characters, because `?` can be satisfied by the second space — `git push origin␣␣` resolved to `allow` for the Git Manager, and the same string inside a compound resolved to `deny` because the splitter trims. Six locations claim a non-empty refspec and no sample pinned the shape. | Closed by a trailing deny for the two-space form (`git push origin  *` and the RTK mirror) instead of trying to make `?` whitespace-aware: the allowed form separates remote and refspec with a single space, and every whitespace-only tail expressible in this pattern language begins with two spaces. Samples moved from allow to deny so the mutant and the structural pin both bite, and the six locations now state the single-space requirement. | Implemented, verified |
| Low | Reviewer final-2: the first Git Manager frontmatter comment still grouped the bare push with the shapes that fall back to the project deny, while the corrected push-model comment says the agent's own rule decides it as the last match. Same effect, inconsistent wording. | Aligned with the push-model comment. No rule change. | Implemented, verified |
| Low | Tester finding (doc precision, changed file): the Git Manager model comment says the double-space denies close "the one gap this pattern language leaves open", which is too narrow once the tab family is accepted as a model limit, and the tab limit itself is not named in the comment although the ledger promises it there. | Reworded to the space-shaped gap the pattern language can express, and one sentence naming the tab limit. Comment-only; `all` output unchanged. The same closure claim was also found and reworded in the comment above `GIT_MANAGER_REQUIRED_TRAILING_DENIES`, which the delegation had not enumerated. | Implemented, verified |
| Low | Tester finding (pre-existing attribution): `AGENTS.md`, the validation README and the development workflow group the bare push under "falls back to the project deny", while for the Git Manager the deciding rule is its own trailing `git push` deny. Outcome is deny either way; only the attribution is imprecise. | Corrected where the sentence is already touched so the deciding rule is named. No rule change. | Implemented, verified |
| Low | Tester finding after the doc-truth round: `docs/workflow/development-workflow.md` says the handover shape "is the only push that passes at the allow level", while the tab shape also passes the allow and is only recorded as a limit. Literally false, though the intended meaning — the only shape the allow grants — is correct and the tab limit is disclosed two sentences later. | Reworded to the granted/limit distinction the Git Manager comment already uses, so the sentence matches the measured behaviour without a new claim. Prose only. | Implemented, verified |
| Low | Implementer finding after its own fix: `origin␣<tab>` (single space, then a tab) still completes the `?` and resolves to `allow` for the Git Manager, including refspec shapes, standalone and compound. The two-space-prefix deny cannot express it; a tab-literal pattern would decide in the offline model but is rejected on cost and observability grounds, as the resolution records. | Accepted as a documented model limit, not as a rule. The reason is cost and observability, not unreachability: the Reviewer measured that a tab-literal deny *would* decide (`origin␣<tab>` and `origin␣<tab>HEAD` flip to deny, legitimate forms stay allowed), so an earlier "unreachable-as-deciding" rationale was wrong and is corrected here. What argues against it is that its only matching input is an invisible tab in review, that it would deny a legitimate refspec push if the runtime normalises whitespace — which cannot be observed offline — and that it would close one character of a family the pattern language cannot express. The limit is therefore named in the Git Manager's model comment and in the workflow document rather than granted as a permission. | Accepted residual |
| Low | Tester F1: the Git Manager's frontmatter comment groups the bare push with the unreachable fall-through shapes, but the bare push is decided by the agent's own required trailing deny (redundant with the project deny, but reachable as last match). | One-sentence correction so the comment describes the deciding rule, not an unreachability claim. No rule change. The same comment's opening bullet still repeated the fall-through framing; closed as `final-2` above. | Resolved, superseded in part by final-2 |
| Low | Tester F2: the Git Manager body says the allowlist admits "exactly `git push origin <branch>` or `git push origin HEAD`", while the rules admit any non-empty, option-free `origin` refspec. | Aligned to the generic `<refspec>` wording already used in `AGENTS.md`. No rule change. | Resolved |
| Informational | Tester F3: a dotted `subprocess.subprocess.run(["git", …])` receiver with a pinned read-only argv resolves clean in the auditor — it is audited shape-based per the docstring, not rejected outright. | Recorded so the behaviour is a stated design choice rather than an assumed rejection; the same receiver with a non-`git` argv or `shell=True` is rejected. | Recorded |
| Medium | Reviewer M-2: the audit still passes `from subprocess import *; run(..., shell=True)`, `runner = subprocess.run; runner(..., shell=True)` and an `import subprocess.subprocess` receiver — shapes the AST can resolve, so the honest-limit text understated them. | Closed by refusing the shapes: wildcard imports are rejected, binding a `subprocess` attribute to a name is rejected, and receivers are resolved by root binding and final attribute. The docs name both the newly rejected shapes and the remaining dynamic ones, including the shape-based (not call-site-based) Starred carve-out. | Implemented, verified |
| Low | Tester finding / Reviewer M-3: the round moved `check_invalid_report_fixtures()` into `check_reports` — an unrequested behaviour change — so `docs/validation/README.md`'s "the fixture scenarios only run under `fixtures` and `all`" became false. | Kept, because running the invalid-report cases with report validation is the stronger behaviour, but recorded as an undelegated change and the sentence now names which fixtures run under which subcommand and why. | Implemented, verified |
| Low | Tester finding: the audit's `subprocess.run(["git", *args])` carve-out is shape-based, not call-site-based, so any new call site of that shape is exempt from the verb pin and runs unchecked argv. Measured: a new site outside the helper passes with zero findings. | Bounded (the `shell` check still applies) and inside the accepted "guardrail, not sandbox" limit, but the stated justification only covers the existing wrapper. The docstring and README state the exemption's true width and the manual-review obligation for such a site. | Implemented, verified |
| Low | Tester observation: `covered-without-evidence` and `covered-with-sentinel-evidence` produce the same failure message, so the `all` log distinguishes them only by case label. | Both fail for their own declared reason and the fixtures are labelled; no change, recorded so the next reader does not mistake it for duplication. | Recorded |
| Low | Tester finding, pre-existing: `docs/validation/README.md` says the Reviewer, Tester and Git Manager have "the edit, write and patch tools denied", but `write`/`patch` appear in no agent frontmatter and are not checked by the validator; the enforcement lives in the operator's global configuration. Reviewer M-4 found two remaining occurrences in `docs/workflow/development-workflow.md`. | Wording aligned to what the repository actually enforces, including the two remaining sentences; the discovery record's past-tense historical sentence is confirmed as history, not a current guarantee. | Implemented, verified |
| Low | Tester finding: "a legal refname holding a plus sign is not covered" reads as "allowed", but the blanket `*+*` deny rejects it (fail-closed); and `AGENTS.md` says `*.env.example` "stays readable and editable", while five of six roles deny `edit`. | Both reworded to match the measured behaviour: denied as a side effect, and readable with editing limited to the role that may write files. | Implemented, verified |
| Informational | Tester finding: the delegation packet said 25 untracked files; the tree has 26 including five `.idea/**` entries from `goland .`. | Packet bookkeeping only. `.idea/**` is the human's IDE state, stays untracked, and is excluded from the frozen fingerprint. | Recorded |
| Informational | Implementer report precision: its ADR-alignment section quotes `ADR baseline (merged, accepted): ['ADR-0001']` as the state for `origin/main`, but that line belongs to the open-pr fixture; the live line is `SKIP … contains no ADR-*.md record`. | Orchestrator verified the live output directly and recorded the distinction so the report is not read as a change in the baseline. | Recorded |
| Informational | User decision: merging a pull request is reserved for the human user. | Removed `gh pr merge*` from the Git Manager allow rules, added an explicit project deny and a validator assertion, and updated agent and workflow instructions. | Resolved |
| High | Git Manager finding during the handover push: the GitHub MCP server exposed `merge_pull_request` and `update_pull_request_branch` to the session, although the workflow and the shell rules reserve merging for the human. No agent merged, but the capability sits outside the control that the documentation describes. | Escalated, not silently accepted: this is the concrete case behind the open R-3 decision on per-role tool and MCP lockdown. The pull-request description lists that lockdown as an open architecture decision rather than a solved control. | Escalated to human |
| Medium | Git Manager finding: `gh pr edit*`, `gh pr comment*` and `git fetch*` are allowed in `.opencode/agents/git-manager.md`, but the literal forms resolved to `deny` in the session. The two GitHub writes were therefore applied through the MCP server, and the pre-push remote state could not be refreshed. | Recorded, not fixed in the reviewed diff: the effective policy is stricter than the intent, and the workaround used a channel the role rules do not describe. A permission-model pass should either make the allows effective or remove them and describe the MCP path explicitly. | Open follow-up |
| Low | Git Manager finding: the delegation said the branch was two commits ahead of the remote; it was three, because `c9fc085` was also local-only. | Corrected in the record: the push `97fd890..5f55d0e` carried three commits, all of them covered by the recorded approval (review-delta commit, ledger commit, push). The description and the review answer referred to the final state, not to a commit count. | Resolved by record |
| Low | Model-provenance check during the human's Implementer/Tester switch: `opencode debug agents` reported `console-ollama/depseek-v4.1-flash` for the Implementer. This was a typo rather than a model variant — `opencode models` contains no `depseek` entry — so the configured assignment could not resolve and the WI-EV delegation would have opened on a broken model. | The human corrected the entry on 2026-11-27. A re-read of `opencode debug agents` reports `console-ollama/deepseek-v4.1-flash` for orchestrator, implementer, tester and git-manager, with planner and reviewer unchanged, and `opencode models` confirms no `depseek` entry exists. The effective assignment is recorded in the provenance table above so AC-PV1 makes the same check repeatable. | Resolved |
| Medium | Ledger self-check before the freeze commit: the Architecture baseline section claimed the validator escalates `adr:ADR-0002:conflicts:ADR-0001` because "ADR-0002 declares a conflict with the not-yet-accepted ADR-0001". The real `docs/adr/ADR-0002-project-specific-multi-agent-development-workflow.md` carries `conflicts-with: []`; the escalation comes from `docs/validation/fixtures/adr/open-pr/ADR-0002-declared-accepted.md`, and the recorded capture holds two fixture scenarios, escalating against `ADR-0001` and against `ADR-0003`. | Corrected in place with the fixture path named, so the line is not read as a real conflict and cannot invite an agent to "resolve" it by editing an accepted ADR. The plan's own ADR-impact block already stated this correctly, which is how the mismatch surfaced. | Resolved |
| Informational | Plan revision 2 was inserted as a drop-in and verified byte-exact: section SHA-256 `474f2c07a443ea74bf3fb144db52f2a0b67af466c401f9f28e3526163e4f2ce1` equals the Planner's candidate, length 23,784 bytes, half-open range `[13564, 37348)`, section ends `\n\n`. | Recorded so the freeze commit can be re-hashed independently. The hash becomes plan identity only when the Reviewer approves the committed section and names the commit. | Recorded |
| Low | The plan's extraction convention hashes up to "the first byte of the following `## Reports reconciled`", but that heading also occurs inside the section as inline code in the Extraction row. Measured on the current ledger: two occurrences, at byte `14160` (inline, inside the table cell) and `37348` (line-start heading); a naive `find` from the plan start returns `14160` and yields a 596-byte "section". | The recorded hash was computed with an anchored line-start match (`^## Reports reconciled$`) after the plan start and reproduces `474f2c07…`, so the artifact is unambiguous; only the wording is. Rewording it is a plan-content change and needs revision 3 plus a new plan review, so the Reviewer rules whether the anchored reading is reproducible enough or a revision is required. | Ruled: anchored reading is sufficient, no revision 3; closed in implementation as RC-1 |
| Informational | The freeze commit `e881bb1` is not a plan-only diff: besides the plan section it corrects the `## Architecture baseline` conflict claim, adds the model-provenance subsection, three report rows, four findings rows and the four `OD-*` items. The Git Manager flagged this itself as a scope question. | Accepted deliberately: every change is inside the single authorised path, no ADR or rule file is touched, and the plan section — the reviewed artifact — is byte-identical before and after. The Reviewer was instructed to read the whole diff and did so without raising a finding. | Recorded |
| Informational | Independent plan review of revision 2 returned `plan approved` against the committed target and stated the identity as `(e881bb1, docs/workflow/ledgers/issue-30.md, 474f2c07…)`. It also ruled that the extraction wording needs no revision 3, because the byte range, the length, the `\n\n` ending and the documented anchored match each force the same result and the identity is pinned to an immutable commit. | Recorded as the freeze point. Implementation delegations bind to that triple. The approval is the plan gate only; the code and test gates are still open. | Approved |
| Low | RC-1 from the plan review: the extraction sentence remains substring-ambiguous even though the identity is unambiguous. | `check_plan_identity()` implements the anchored `^## Reports reconciled$` match and asserts the recorded range, length and `\n\n` invariants; the clarification is recorded outside the frozen section so the hash stays valid. | Open, WI-EV |
| Low | RC-2 from the plan review: one gate carries two names, `validate_release_gate()` in the criterion map and `evaluate_release_gate()` in the AC-FC1 row and the release boolean. | One name across the criterion map, the documentation-versus-rules table and the boolean, so the rule-to-assertion mapping the plan promises is traceable. | Open, WI-EV |
| Low | RC-3 from the plan review: `check_ci_workflow_contract()` appears in the AC-CI1 criterion row but in no work item's independently verifiable outcome. | WI-CI owns it explicitly and builds on the `ci` mode that WI-EV delivers, which is the bidirectional dependency the plan states. | Open, WI-CI |
| Informational | The plan review noted that `## Handover` and `## Deferred or out-of-scope work` still describe the validator CI job as deferred, pre-dating the owner's 2026-11-27 decision to implement it. | The AC-CI1 row and WI-CI are authoritative; the stale framing is corrected when WI-CI lands, so the handover section describes the implemented job rather than the old deferral. | Open, WI-CI |
| Medium | Ledger check before starting WI-EV: the plan records the section as byte range `[13564, 37348)`, which held on `e881bb1` but no longer holds on the working tree, because the AC-VB1 row and the reports table were edited after the freeze. The current range is `[13758, 37542)` while the section hash is unchanged at `474f2c07…`. | The hash is the invariant; the byte range is a property of one frozen commit. RC-1 is amended accordingly: `check_plan_identity()` asserts the hash plus the durable structural invariants (the section starts at the line-start heading and ends with `\n\n`) and does not hard-code an offset that the next ledger edit invalidates. Recorded before the delegation so a commit-specific number cannot become a durable assertion. | Open, WI-EV |
| Low | The WI-EV implementation pins the plan identity to the short SHA `PLAN_REVIEW_COMMIT = "e881bb1"`. It resolves to exactly one commit today, but a short prefix is not a durable identity and a future object could make it ambiguous. | Recorded for the code review to judge. The plan identity the Reviewer approved is the full SHA `e881bb10e005d08d0001a8a44f13e6506f7eb19f`; widening the constant is a one-line change if the Reviewer requires it. | Open, WI-EV review |
| Informational | Report precision: the Implementer's ADR-alignment section states that ADR-0001 is the accepted, merged baseline and that ADR-0002 conflicts with ADR-0001. Neither holds for the real records — only the #27 bootstrap decision is in force on `main`, ADR-0001/0002/0003 are proposals in PR #32, and ADR-0002's frontmatter carries `conflicts-with: []`. The only ADR-0002/ADR-0001 conflict is the synthetic open-PR fixture and its fixture report. | Corrected by record, not by editing the report: no repository file repeats the misstatement (`docs/adr/**` is untouched and the fixture is the sole carrier). The Reviewer should apply the same standard to the report's claims that it applies to the diff. | Recorded |
| High | B-1 (Tester): `evidence_check_states()` defaults an absent `check_state` to `passed`, so a structured entry that names only an `artifact` turns a claim green, although the contract and the validation README say every structured entry must record `check_state: passed`. Fail-open, and no fixture pins it. | Fix the default to non-green and add the missing fixture, so the sentence and the code agree by tightening the code rather than the sentence. | Verified closed by the re-verification |
| High | B-2 (Tester): `evaluate_release_gate()` takes `release.get("artifact") or pr_head` and never compares the two, so a record whose artifact is an older SHA, with every report bound to that SHA and every slot head equal to `pr_head`, passes with no blockers. The contract promises exact PR-head agreement across plan, code, test, CI, human and handover evidence. | Compare the record artifact with `pr_head` and fail on a mismatch; add the mutation. If a frozen-diff artifact is ever legitimate, it needs an explicit kind and an attested head rather than a silent fallback. | Verified closed by the re-verification |
| Medium | B-3 (Tester): `docs/validation/opencode-v2.4.1-discovery.md` still states that the committed capture is the full `all` run and shows an `all` command block, while the capture is now a `ci` run without the live-release section. The replacement capture itself is honest and documented in the validation README. | Update the discovery record to `ci`, regenerate its abridged block, and keep the two documents consistent about what the capture contains. | Verified closed by the re-verification |
| Medium | B-4 (Tester): the claim that every guard is proven load-bearing by a mutation is not true. Eight defensive branches have no mutation in either suite (record `gaps`, `pr_head:missing`, `criteria:missing`, decision-resolution sub-fields, `tester_verification:head-mismatch`, `human_review:{not-human,missing-identity}`, and "structured evidence must name an `artifact`"), and two of them have no coverage at all. | Narrow the claim to the named guards plus the list of defensive branches that were reviewed but not mutation-proven, and add fixtures for the two rules with no coverage (absent `check_state`, structured evidence without `artifact`). | Verified for the six added classes, each load-bearing; the reviewed-only list is still not the authoritative remainder and the in-memory docstring still calls it that (F-2). Non-blocking follow-up. |
| Low | B-5 (Tester): the frozen plan's reconciliation table says removing the `decision_needed` loop makes `unresolved-decision` pass. The real guard for that fixture is the release-record `decisions` loop; the reconcile loop is guarded by the in-memory "report decision needed" case. The same inversion applies to `pending-proposal`. Detection still holds, but the stated mapping is wrong. | The plan section is frozen and must not be edited, so the deviation is recorded here. The code keeps both loops and the fixtures keep the real mapping; the review sees both statements side by side. | Recorded deviation |
| Low | B-6 (Tester): RC-2 cannot be closed as written, because `validate_release_gate()` appears three times inside the frozen plan while the code and the non-plan documents use `evaluate_release_gate()`. | Closed by record: the single name holds in code and in every document that can change; the frozen plan keeps both spellings. The Implementer row's claim is narrowed to that scope. | Resolved by record |
| Medium | AC-VB1 tension exposed by B-2, tested: the criterion permits binding review evidence to the exact reviewed commit **or** an identifiable frozen diff, and this work item is reviewed as the frozen-diff identity `f12fcc21…`. The gate accepts no such shape: a record bound to `f12fcc21…` is either rejected with `artifact:head-mismatch` or collapses to `stale-artifact`, and the only passing shape relabels the frozen diff as `pr_head` — which passes only because `pr_head` is not shape-validated at all (N-2), so it is B-2 fail-open one field to the left. | Decision needed before handover, three options: validate `pr_head` as a commit identity and require evidence re-bound to the final head at handover; or add `artifact_kind` with a per-slot attested head for frozen-diff rounds; or declare record-level commit binding only and re-bind before handover. N-2 (hex `pr_head`) was required under every option. Decided by the human on 2026-11-27: commit binding only — the record's `artifact` is the reviewed artefact and must be the handover commit, there is no frozen-diff shape, and a frozen-diff round is re-bound to the handover head before `release_ready` can be true. `pr_head` and `artifact` must be full 40-hex identities. Consequence recorded deliberately: this work item's own evidence is bound to `f12fcc21…`, so the handover needs one deterministic re-run of the affected checks on the committed head, which is exactly the re-binding AC-VB1 describes. | Resolved by decision |
| Medium | B-7 (Tester): the frozen-diff identifier `6f87257c…` did not reproduce under ten methods and the Implementer published no method, so the round had no reproducible artifact identity — the exact failure AC-VB1 exists to prevent. The Tester published its method and hash `4ba3b8ed…` instead. | Adopt the Tester's documented method as this work item's identity, require the Implementer to publish method and hash with every future report, and correct `tester.md`, which says only an inspected `passed` check is green although that holds for the CI slot alone. | Verified closed by the re-verification |
| Medium | Improvement set from the same verification: a human slot may reuse the AI reviewer's identity and may carry `name == login`; `base_sha` passes as `x` or `12345`; `reconcile` alone does not enforce evidence criterion identity although the README claims it does; a structured evidence item without `artifact` is rejected with a message about non-empty strings; the contract quotes `evidence:<state>:<agent>` while the observable gap is criterion-prefixed; the contract formula omits record-declared `gaps`; two blocker derivations (`scenario_blockers` and `evaluate_release_gate`) can drift. | Fix the cheap ones in the same round: cross-slot distinctness (the human login differs from the AI reviewer identity and the name differs from the login), hex validation for `base_sha`, the two wording corrections, the accurate rejection message and the contract note for record gaps. Unify the two blocker derivations if the change is contained; otherwise record the divergence risk at the definition. | Verified closed by the re-verification |
| Informational | B-17 (Tester): the plan asks to record the half-open byte range and length, but only the length is recorded. | Deliberate: the range is commit-specific and recording it as durable is what RC-1 forbids. The length and the hash are durable; the range is documented once as a property of `e881bb1`. | Recorded |
| Medium | N-1, self-inflicted: a ledger edit of mine wrote its own tool payload into the row, leaving the B-6 row followed by a literal payload tail and the AC-VB1 row missing. The Tester found it while auditing the tracked tree, not while verifying code, and flagged it as contamination a commit would carry. | Repaired by replacing the single corrupted line with the B-6 row plus a real AC-VB1 row, then re-measuring: plan section still `474f2c07…` / 23,784 bytes, no payload string left. Recorded rather than quietly fixed because it is the same defect class the PR exists to prevent, committed by the orchestrator. | Resolved |
| High | N-2 (Tester): `pr_head` is not shape-validated, so `artifact == pr_head` is equality over free text. A record with `pr_head = "not-a-commit"`, every slot re-bound to it and `artifact` equal to it reaches `ready=true`. I rate this above the Tester's Medium: the relabelling loophole is B-2's fail-open one field to the left, and it lets a record claim commit binding while all evidence is bound to a working-tree hash. | Validate `pr_head` as a commit identity (`^[0-9a-f]{40}$`, or the 7–40 hex rule used for `base_sha`) and add the mutation. Required under every option of the AC-VB1 decision. | Verified closed |
| Low | N-3 (Tester): ten branch classes are neither mutation-proven nor listed as reviewed-only (`{slot}:invalid-state`, `workflow_validator_ci:missing`, `reports:missing`, `reports:invalid:`, `criteria:invalid`, `gaps:invalid`, `decisions:invalid`, `proposals:invalid`, `proposal:invalid:`, `decision:invalid:`), so the narrowed claim still reads as an exhaustive remainder. | Add the `workflow_validator_ci:missing` and invalid-state cases first, then list the rest as reviewed-only. The claim must be exactly as wide as the evidence. | Verified closed |
| Low | N-4 (Tester): cross-slot normalisation is inconsistent in both directions. Capitalisation cannot bypass the check, but separators can (`DeepSeek V4.1 Flash` against `deepseek-v4.1-flash` passes), and a human legitimately named `Tester` is rejected. | Not an arms race worth winning: one sentence in the contract that identity comparison is literal-normalised and that independence beyond that is attested human judgement. The Reviewer judges whether the sentence is enough. | Addressed as documented judgement, verified against behaviour |
| Low | N-5 (Tester): an evidence state gap also attaches to rows that are already non-covered, so a legitimate `unverified` report with `check_state: skipped` gains `AC-01:evidence:skipped:implementer` and reads as an evidence error rather than as the justification it is. | Decide whether the state is named only when it is the reason a claim failed. Diagnostic quality, not fail-open. | Addressed as documented judgement, verified against behaviour |
| Low | N-6 (Tester): the contract's absent-state sentence still says the gap is `evidence:missing:<agent>`, while the observable gap is criterion-prefixed `AC-04:evidence:missing:<agent>` — the correct form appears two sentences later, so the file contradicts itself. | One-line correction; the same sentence pair is the place where B-15 was closed. | Verified closed |
| Informational | N-7 (Tester): `reconcile` filters rendered evidence to strings, so structured evidence items no longer appear in the ledger view the Orchestrator reads. | Cosmetic for the report path, but it removes the artifact and check-state from exactly the view used to reconcile. Consider rendering `artifact` and `check_state` alongside the string entries. | Fixed in the reconciliation view, verified display-only |
| Medium | Unknown top-level keys in a release record were silently discarded. The Tester's shape C2 declared `artifact_kind` and `frozen_diff`, was accepted, and was evaluated as if those keys did not exist — a record can therefore look like it declares a binding the evaluator ignores. | Rejected as `release-record:unknown-key:<key>` with a closed key set, so the record schema is an explicit interface and adding a field is a conscious validator change. Accept the cost: schema evolution now requires code. | Verified closed |
| Low | F-1 (Tester, final round): `docs/workflow/development-workflow.md` states commit binding and the re-bind obligation but never says the identity is a full 40-hex commit, nor that the record has no frozen-diff form. It does not imply the opposite, but the three documents then differ in what they pin down. | One clause in the same sentence, so the workflow document is not the weakest of the three descriptions of one rule. | Closed in the micro-round; the code review verifies |
| Low | F-2 (Tester, final round): the reviewed-only list is still not the authoritative remainder. `workflow_validator_ci:head-mismatch` has no proving case while its analogue `tester_verification:head-mismatch` is listed, and `gaps:present` plus the `gap:`, `release-gap:` and `escalation:` loops are unproven and unlisted — yet the in-memory fixture docstring still calls the list authoritative. | Add the CI-head mutation and `gaps:present` to the claim, and soften the docstring so it describes what is known rather than what is hoped. The sentence must be as wide as the evidence, which is the same defect B-4 named. | Closed in the micro-round; the code review verifies |
| Low | F-3 (Tester, final round): the contract still says a `disagreement:<values>` gap is recorded, while the runtime gap is `AC-01:disagreement:covered/unverified`. | One-word fix to the criterion-prefixed form. Same kind-versus-name imprecision N-6 closed two sentences earlier. | Closed in the micro-round; the code review verifies |
| Informational | F-4 (Tester, final round): nested unknown keys are accepted — `plan_review.frozen_diff`, `human_review.ai_identity` and `workflow_validator_ci.frozen_diff` all leave `ready=true`. Literal-consistent with the contract's "unknown top-level keys", and an ignored nested field binds nothing the evaluator reads, but a record can still carry a field that looks like a binding. | Document nested slot keys as open and ignored, or close them in a later pass. Not a fail-open today because no nested field is read as authority. | Documented as accepted behaviour; the code review verifies |
| Informational | Stop-rule deviation, recorded rather than silently applied: the doc-precision micro-round changed the artefact from `11f0f2ef…` to `1f76a98c…` after the third verification round. Read literally, the rule resets the count and demands three fresh rounds on the new identity — ritual, because the delta is four test cases and four sentences. | Routed to the Reviewer's code review instead: a different role with a different instrument, which is what the rule exists to protect. The Tester's three rounds stand for everything the delta did not touch; the Reviewer verifies the delta itself, including that the four new cases are load-bearing and that the printed count matches the cases. Recorded so the human can overrule rather than discover it afterwards. This is the second time in one session that the rule needed a judgement call, which is evidence about the rule, not about the work item. | Recorded |
| Medium | Asymmetry surfaced by the Planner, untested: `human_review_blockers()` rejects a human identity against both the static `AI_IDENTITIES` list and the dynamic identities recorded in the same record (`ai_code_review` reviewer/model/name/login, `plan_review`), while `decision_resolution_blockers()` checks a decision's `resolved_by` only against the static list. If that holds, a decision recorded as resolved by `hy4` or by the recorded AI reviewer's model name would pass, although the same identity is rejected in the human slot — the guard B-8 closed, one field to the left. | Test it before the code review signs: a release record whose `decisions[].resolved_by` names a dynamic AI identity. If it passes, it is a real fail-open and not merely an asymmetry, because a decision is exactly the kind of item an AI must not be able to close. | Confirmed by the code review as a blocking fail-open: `resolved_by` is checked only against the static list, so the reviewer's own model identity closes a required decision and the gate returns `release_ready=true` with no blockers. Both ADR-0002 and the validation README promise a non-AI resolver, so the code fix also makes those sentences true rather than requiring a doc rewrite. Fixed and verified by the fourth round; closed by the re-review |
| Informational | The ledger structure check landed on the identity the re-review read (`ec7df78b…` → `43f650f9…`, 65 files, +3,048/−217, 32 untracked). Additive and green in `ci`, but not yet independently verified — the whole point of the exercise was that a guard nobody measured is not yet a guard, and the check's own coverage argument is exactly the kind of claim that was disproved elsewhere today. | Verify it in the next independent round against the new identity. Not blocking for WI-EV, whose plan hash, invariants and other tools are unchanged; blocking for the handover, because the plan is the artefact every later gate inherits. | Open, next verification |
| Low | F-2 (Reviewer): ADR-0002 attributes the "every structured evidence item names an `artifact`" rule to `reconcile()`, but `reconcile()` only requires one content-bearing item; the every-item rule is enforced one layer earlier by `validate_report()`. End-to-end behaviour is correct, so this is attribution, not a gap. | Correct the sentence in the ADR, which is read as the architecture baseline once merged. Planner-owned. | Fixed, awaits the next review pass |
| Low | F-1 (Tester WI-CO): the committed capture is stale. It matches two consecutive `ci` runs at capture time, but a fresh run on the current tree says 17 table blocks where it says 16, because the ledger gained a table block after capture. The ledger is excluded from the identity, so `cdb3246b…` is unaffected. | Regenerate the capture at the final tree, or scope the "verbatim capture" sentence to capture time. Carried to the pre-handover pass. | Deferred to pre-handover |
| Low | F-2 (Tester WI-CO): `validate_delegation_packet_links()` rejects only the six exact pre-canonical bullets; a paraphrased duplicate passes, while the README claims it rejects duplicated rule bullets. Current docs are clean. | Narrow the sentence to the six verbatim bullets, or extend the check. Not blocking. | Open, follow-up |
| Low | F-3 (Tester WI-CO): the `write_scope` containing another task's `.tmp/` branch has no mutation. All 19 named guards are proven; this extra branch is effectively reviewed-only. | Add one mutation case or list it as reviewed-only next to the named 19. Not blocking. | Open, follow-up |
| Informational | F-4 (Tester WI-CO): the "36 sample strings" figure is not reproducible as a current count; the 1,800 policy tuples reproduce exactly. | Treat the tuple count as the invariant. | Recorded |
| Medium | F-1 (Reviewer WI-CO, same as Tester): the checked-in capture is not byte-identical to a live `ci` run — capture says 16 table blocks, live says 17, because `check_ledger_structure()` reads the working-tree ledger which is excluded from the identity and was edited after capture. | This is structural, not a one-off: the capture comparison is ledger-dependent, so every ledger edit makes it transiently stale. Regenerate at the handover re-bind and consider making the comparison ledger-independent (exclude the structure line from the byte-identity contract, or freeze the ledger snapshot with the capture). Non-blocking for WI-CO. | Deferred to pre-handover, mechanism noted |
| Low | F-2 (Reviewer WI-CO, corroborates Tester): "link only" overclaims — the section paraphrases the caveat and the validator rejects only the six exact pre-canonical bullets. | Scope the sentence or widen the check. Same action as Tester F-2. | Open, follow-up |
| Low | F-3 (Reviewer WI-CO, corroborates Tester): the `.tmp`-in-`write_scope` guard has no mutation, so the "19/19" removal count is contributor-reported, not repo-reproducible. | Add one case; treat the count as contributor-reported until re-derived. Same action as Tester F-3. | Open, follow-up |
| Low | F-4 (Reviewer WI-CO): the discovery record's abridged block says 47 mutations, while README, capture and live run say 52. The old 77/6,255/51 triple is gone from non-ledger docs, but a new stale number was introduced. | Bring the block to 52 at the handover re-bind. | Deferred to pre-handover |
| Informational | F-5 (Reviewer WI-CO): the Orchestrator's post-capture ledger edit inserted report rows into the middle of a prose sentence, and the structure check passed anyway — a headerless fragment counts as self-consistent. This is the mechanism behind F-1. | Orchestrator to tidy ledger placement; the check's blind spot is recorded rather than treated as proof the ledger is clean. | Recorded |
| Medium | CI-1 (Implementer WI-CI): the recorded base is a constant (`EXPECTED_BASE_SHA`) that must be re-recorded when `main` advances. That is the fail-closed reading of "enforced base", but it is a recurring maintenance point — the job goes red until a reviewed commit updates it, and it never auto-accepts a new base. | Documented in the workflow comment and both docs. The handover re-bind must re-record the base at that time. | Open, maintained by reviewed commits |
| Low | CI-2 (Implementer WI-CI): the base fetch is an anonymous HTTPS read (`persist-credentials: false`), deliberate for fork PRs but only viable while the repo is publicly readable. A private repo would fail closed. | Stated in the docs. | Recorded |
| Low | CI-3 (Implementer WI-CI): the job is `pull_request`-only. Push-to-main and manual dispatch skip it, and a skipped job is not green. | Stated in the workflow and docs. | Recorded |
| Low | CI-4 (Implementer WI-CI): the contract is a text-level check on a narrow YAML subset. A workflow that satisfies the markers could still misbehave at runtime; job/step/log inspection and the Tester/Reviewer gates remain the control set. | Stated in the docs, not claimed otherwise. | Recorded |
| Low | F-2 (Reviewer WI-CI): two "The contract proves" sentences overclaim guard scope — the base/head compare guards only prove an `if` referencing `EXPECTED_*` and an `exit 1` exist; removing only the base-compare `exit 1` or inverting `!=` to `==` still passes. The workflow is correct; the proof-scope is wider than the guards. | Scope the sentences to the shape-level property, or add a per-`exit 1` and an operator mutation. | Open, follow-up |
| Low | F-4 (Reviewer WI-CI): present-tense looseness — the job "is the CI evidence" is qualified two sections later. | Optional tightening. | Open, follow-up |
| Low | F-1 (Tester WI-CI): capture is one line stale again (239 vs 243 data rows) on the current tree — the ledger grew after capture, third occurrence of the same class. | Regenerate only at the final handover head, after the last ledger edit. The comparison contract itself needs the fix the Reviewer already proposed. | Deferred to pre-handover, third occurrence |
| Low | F-3 (Reviewer): two plan-conformance deviations that are not dropped commitments. The frozen plan fixes a 12-conjunct `release_ready` formula; the implementation has 13, the addition being `no_record_declared_gaps` — a fail-closed strengthening. And the plan's disagreement row names a test `test_conflicting_reports_cannot_pass` that does not exist; the behaviour is proven by the `contradictory coverage` mutation and the `conflicting-reports` fixture instead. | Both are recorded here rather than edited into the frozen plan. The conjunct addition should be named as a deliberate strengthening wherever the formula is described, so a reader is not surprised by the count. | Recorded |
| Low | F-4 (Reviewer): the ledger acceptance table was stale against its own implementation — AC-PV1 still read `missing` and AC-VB1 still claimed `check_plan_identity()` was unimplemented, while the run notes above already reported both as delivered. Caught by the code review, not by me, although I had reported the higher coverage numbers in conversation. | Fixed in this reconciliation: both rows now carry the evidence they have, with the remaining handover half of AC-VB1 named as open by design. Recorded because the ledger is the artefact criteria are reconciled against, and a stale row there is a false claim regardless of what the chat said. | Fixed |
| Informational | F-5 (Reviewer): the WI-EV implementation report claimed AC-RV1 as `covered`. No independent human review exists, so the claim is unsubstantiated; the acceptance table kept it `partial` throughout. | The claim stays in the report row as what the agent reported, and is not carried into coverage. A report's self-assessment never outranks the placement of its claim. | Recorded |
| Medium | Residual boundary of the F-1 fix, reported by the Implementer rather than smoothed over: the identity harvest reads only the two review slots. If a release record omits `ai_code_review.model`, a decision closed by that model's name passes, because the name is then recorded only in a report's provenance, which the gate does not consult. The same limit applies to the human slot, so this is not a regression introduced by the fix — but it means the guard protects against a recorded identity, not against an unrecorded one. | Decide at the next gate: either require `ai_code_review.model` in the release record, or widen the harvest to the reports' provenance. Until then the rule is stated as it is, not as it would be convenient to read. | Open, follow-up |
| Informational | The Implementer reported that the ledger overstates AC-CI1 because `check_ci_workflow_contract()` and a `workflow-validator` job do not exist. Line 133 is inside the frozen plan, in the criterion map, and describes what WI-CI is planned to deliver — not what exists today. The plan is frozen and was reviewed as a plan. | No correction to the plan, which must not change. The observation is itself the defect class this PR keeps meeting: a plan row read as a status row. The AC table, not the plan, is where implemented state lives. | Recorded |
| Low | F-V1 (Tester): the ineligible identity set is scoped to the two attestation slots. An identity recorded only in `reports[].model` does not block a `resolved_by`, so read literally, "an AI identity recorded in the same release record" is wider than what the code checks. | Accepted as a documented boundary, not a blocker: the record is the trust boundary, `resolved_by` is free text, and importing identities from the operator's global configuration would break the validator's offline determinism. An identity absent from the record is indistinguishable from a human name, and that limit is stated rather than implied. Optional hardening: harvest `reports[].model` too, or say in the validation README that the attestation slots define the boundary. | Accepted, optional hardening |
| Low | F-V2 (Tester): the validation README's embedded abridged `ci` snapshot still shows 51 mutations and 1,164 call sites, while its own normative prose, the capture and the live run all say 52 and 1,167. The block is explicitly labelled as a non-current illustration, so it is stale rather than false. | Deliberately not fixed now: a documentation edit would change the identity while the re-review is reading `ec7df78b…`. Fixed at the handover re-bind, where the identity changes anyway and the whole capture is regenerated. | Deferred to handover |
| Low | Provenance error in the fourth-round Tester report: it states that the previous three WI-EV rounds ran on `opencode-go/hy4`. They ran on `deepseek-v4.1-flash`; `hy4` is the reviewer. The report's statement about its own model (`mistral-large-4` / `opencode`) is consistent with the assignment, so the verification itself is not affected. | Recorded, not corrected in place, because a report is a historical statement of what an agent claimed. It is nonetheless the second time in this session that an agent asserted a provenance fact without reading it, and provenance is exactly what AC-PV1 exists to keep true. The ledger's provenance table, not the report's narrative, is the record. | Recorded |
| High | Classification disagreement between instruments, resolved on the stricter reading: the Tester judged the residual identity boundary "defensible, not blocking"; the Reviewer judged it "a bounded fail-open, non-blocking". The facts are not in dispute — both probed a record whose decision is resolved by an identity that appears only in a report's provenance, and both saw it pass. They differ on the label. | The stricter label is adopted because a fail-closed control for a human-only decision that accepts an unrecorded AI identity is a fail-open relative to the sentence the documents state. Bounded, disclosed and pre-existing does not make it a boundary. The disagreement itself is recorded rather than averaged away: two instruments disagreed, so the record shows both readings and the reason for the choice. | Recorded |
| Low | N-1 (Reviewer): count propagation is still incomplete in two illustrative blocks — the validation README's abridged "expected result" block says 51 mutations and the discovery record says 47, while the capture and the normative prose say 52. The README disclaimer covers refs and SHAs, not structural counts. | Carried into the handover preparation as an explicitly scoped task, not silently deferred: the counts are corrected in the same pass that prepares the commit, and the handover re-bind re-runs the capture anyway. Fixing them now would change the identity while the verdict is being recorded. | Carried to handover |
| Low | N-2 (Reviewer): ADR-0002 and the validation README say a resolved required decision needs a "non-AI `resolved_by`", while the code enforces "not a static role and not an identity recorded in the two review slots". The normative sentence is wider than the enforcement. | Scope both sentences to the recorded identity set, or close the class by requiring and cross-checking the reviewer identity. Until then AC-FC1 stays `partial`, because the criterion is about fail-closed claims and the claim is currently wider than the code. | Carried to handover |

## Architecture baseline

- Accepted baseline on the default branch: the Go and Bubble Tea bootstrap
  decision from issue #27, in force since PR #31 merged as `17cf55a`. It was
  recorded as `docs/adr/0001-go-bubble-tea-bootstrap.md` without frontmatter and
  is invisible to the validator until this pull request normalises it to
  `ADR-0003`. The decision itself, not the file name, is the baseline.
- Proposals in this pull request: ADR-0001 (reviewed issue #1 requirements as
  baseline), ADR-0002 (multi-agent development workflow) and ADR-0003
  (normalised bootstrap record). All three declare `status: Accepted` and are
  effectively `Proposed` while PR #32 is open; the validator reports exactly
  that mapping.
- Conflicts: none in the real records. ADR-0002's frontmatter carries
  `conflicts-with: []`. The escalation `adr:ADR-0002:conflicts:ADR-0001` in the
  recorded output belongs to the synthetic open-pull-request fixture
  (`docs/validation/fixtures/adr/open-pr/ADR-0002-declared-accepted.md`), whose
  ADR-0002 declares that conflict; the second scenario in the same capture
  escalates against `ADR-0003` for the same reason. The distinction matters
  because the escalation line reads as if the real proposal conflicted with a
  sibling proposal, and it must not be "resolved" by editing an accepted ADR.
  Both are proposals of this pull request, so the declared status resolves on
  the human merge.
- Decisions needed: human approval of ADR-0001, ADR-0002 and ADR-0003 through
  the pull request. Until that merge the accepted baseline stays limited to the
  bootstrap decision already in force on `main`.

## Unresolved items

- The initial ADR baseline is effective only after the human-approved merge of
  this pull request. Until then, the workflow checks treat ADR-0001, ADR-0002
  and the normalised ADR-0003 record as proposals, while the bootstrap decision
  itself is already in force through PR #31.
- Independent human review and approval of this pull request are required
  before merge.
- Open required decisions introduced by plan revision 2. Each one forces
  `release_ready=false` until the human closes it, and none may be deferred
  silently behind "out of scope":
  - `OD-ROLE` — per-role tool and MCP lockdown. The GitHub MCP server exposed
    `merge_pull_request` and `update_pull_request_branch` during the handover
    push, so shell permission matrices cannot close this on their own. The owner
    chooses the boundary; a harmless capability inspection on the final head
    verifies it.
  - `OD-BRANCH` — repository-side branch protection: required human review, no
    force push and no direct push. Agents do not change repository settings; the
    record names the human and the settings evidence.
  - `OD-ADR-LIVE` — live ADR baseline. A verified explicit base SHA, or the
    owner's explicit recorded decision, must produce an inspected pass. A
    synthetic fixture or a `SKIP` line cannot close it.
  - `OD-PR-INVENTORY` — the pull-request description's accepted-baseline and
    proposal inventory. The owner approves the inventory and the Git Manager
    updates and reads it back on the final head.
- Configuration discovery was verified against the local OpenCode v2.4.1 and
  the existing global model assignments. A different OpenCode version or model
  configuration may require a repeated discovery check.
- Verification history: Tester and Reviewer both cleared `613c13a` and the
  recorded validator output matched a fresh run byte-for-byte; PR #32 was opened
  from that state. Five further review rounds followed on the branch — the
  external-review delta, the remote-only push category, the whitespace-only
  allow edge, the documentation-truth blocker and the granted/limit precision.
  Each round was independently reviewed and tested against a frozen
  tracked-diff fingerprint, and the final tree `5116b645…` carries a
  `ready for handover` verdict.
- Reconciliation verification: the merge commit `f19d1c5` was verified
  independently by the Tester — state and shape, byte-identical Go imports from
  `main`, the `.gitignore` union, verbatim ADR decision text, link resolution,
  a byte-identical validator run (37 lines), the extended permission matrix
  including `git ls-tree`, and a green `gofmt`/`go vet`/`go build`/`go test`
  (22 tests, 3 packages).
- The residuals below are documented and accepted in ADR-0002 under
  `# Residual risks`. The tab limit was found after ADR-0002 was written, so it
  is documented in the Git Manager's model comment, in the workflow document and
  here instead of being appended to the proposal; folding it into ADR-0002's
  residual list is a post-merge edit, not a change to this reviewed diff:
  - Compound commands are checked per extracted subcommand by the OpenCode
    shell scanner, so `gh api`, pull-request merges and pushes to `main` are
    denied even when they follow an allowed Git verb. The offline validator
    approximates the scanner by splitting on common separators; exotic
    constructs rely on the scanner's fail-closed behaviour.
  - Non-RTK shell commands that touch paths outside the worktree are not
    restricted by a general path rule. Only the credential locations are
    denied; RTK commands and file tools require approval outside the worktree.
  - The `rtk * ~*` approval rule asks for RTK commands with home-path
    arguments such as `rtk read ~/x`. Approval prompt only, not a silent allow.
- Follow-up (Git Manager finding): permission patterns are literal command
  prefixes, so `git -C <path> …` does not match the read allowlist; routine
  inspection has to use the plain `git` forms. `git ls-tree` was added on the
  owner's request during the reconciliation and `git rev-list*` in this round; a
  `git -C *`-tolerant rule remains deferred until after this pull request.
- Permission-runtime mismatch: `git fetch*` and `git pull*` are on the Git
  Manager's allowlist, but the runtime rejected both plain forms during the
  reconciliation until the human ran `git fetch origin main`. This has to be
  reproduced and corrected before the next handover that depends on a moving
  base branch; the validator cannot detect it because it models rules, not the
  runtime.
- ADR-0003 is already in force on `main` through PR #31, while the normalised
  `ADR-0003` file is a proposal until PR #32 merges. After the merge the record
  is accepted under the `ADR-NNNN` convention; no further rename is planned.
- Transition discrepancy until PR #32 merges: the Go and Bubble Tea decision is
  in force on `origin/main` under the legacy name
  `docs/adr/0001-go-bubble-tea-bootstrap.md` (no frontmatter, text status
  "In Review"), while the normative `ADR-0003` exists only as a proposal in this
  pull request. Merging PR #32 closes the discrepancy. It is recorded rather
  than resolved by an agent.
- The validator's live-tree baseline line was a stale-`main` and legacy-filename
  artifact: `resolve_baseline_ref()` preferred the local `main` (`73dbbec`,
  pre-PR #31) over `origin/main`, and `adrs_from_ref` filters `ADR-*.md`. The
  resolver now prefers `origin/main`, warns when the two refs disagree, and
  states explicitly when the chosen ref contains no `ADR-*.md` record. On the
  current tree the honest output is therefore "resolved ref `origin/main`
  contains no `ADR-*.md` record under `docs/adr`" plus the divergence warning —
  not an empty baseline list. After PR #32 merges, `origin/main` carries
  ADR-0001/0002/0003 and the line becomes a real baseline.
- PR #32's description still describes `613c13a`. The prepared replacement is
  blocked from the shell because its text contains the literal `gh pr merge`,
  which the runtime rejects inside any shell command. It is written with the
  file tool in this round and applied with `gh pr edit 32 --body-file`.
- Policy over-match: the runtime denies any shell command string that contains
  `gh pr merge`, including a heredoc that only writes Markdown. Documentation
  that names the command cannot be produced through the shell. The Tester hit
  the same class with the `git push `, `.env` and `/.ssh` mirror substrings
  while writing scratch harnesses whose comments merely contained those words,
  and then with `git commit ` / `git add ` from the defence-in-depth mirrors.
  This is a false-positive class next to the `git fetch`/`git pull` mismatch; the
  deny should anchor to command position rather than a raw substring. Recorded,
  not fixed mid-pull-request.
- Decision (CI), owner decision on 2026-11-26: no validator job is added to
  `.github/workflows/ci.yml` in this pull request. The job would need
  `fetch-depth: 0` and an enforced `origin/main` so the baseline check cannot
  silently skip; it stays a post-merge follow-up. The CI contract inherited from
  the issue #27 ADR is unchanged.
- Decision needed (roles): whether the six agents should get per-role tool and
  MCP restrictions. That is an architecture change beyond a permission-rule
  correction and is explicitly out of scope of the current round.
- Human action (repository settings): branch protection on `main` — required
  review, no force push, no direct push. Agents cannot set or verify it because
  `gh api` is denied project-wide; only the repository owner can.
- Validator follow-up: the eager `setdefault` id in `adr_from_text` still raises
  `IndexError` for an ADR path without a dash. No current call site triggers it.
- Validator-fidelity follow-up: the subcommand splitter handles `&&`, `||`, `;`,
  `|` and newlines. Single `&`, command substitution and process substitution
  are left to the runtime scanner; the model could resolve such a compound to
  `allow`. No enforcement impact.
- Documentation follow-up: closed — the `docs/validation/README.md` environment
  exemption now reads "an `.env.example` or `*.env.example` template, if
  present", matching the rules and `AGENTS.md`.
- Follow-up, not decided: the auditor's negative probes (patched copies that
  must be rejected) exist only as transient checks, not as a committed fixture
  runner. In-repo regression coverage for the audit itself is an option for the
  post-merge round, together with the deferred CI job. Accepted limit, stated in
  `docs/validation/README.md`: an AST audit bounds constructs and is a
  guardrail, not a sandbox; it cannot prove the absence of every unsafe path.
- Proposed follow-up, not decided: add permanent Markdown hygiene checks
  (relative links, trailing whitespace, heading jumps) to the offline validator
  instead of introducing a Node-based linter, which the permission policy
  denies.
- Workflow improvement from the Reviewer: parallel agents share `.tmp/`, and one
  agent's cleanup deleted another's scratch mid-run. Per-agent scratch
  subdirectories (`.tmp/<agent>/`) would remove the race; recorded as a
  coordination improvement for the next workflow revision, not changed in this
  pull request.
- Runtime behaviour not verifiable offline: whether the OpenCode scanner trims a
  command string before matching. Three shapes are now denied in the checked
  model regardless of trimming — the remote-only form, the one-space tail and
  any tail of two or more spaces, the last through an explicit deny rule — so
  the uncertainty is fail-closed in every interpretation. Recorded because the
  validator models the raw string and the runtime is not observable here.
- `?` in the allow matches any single character, including a leading `-`, `+` or
  `:` of a pathological refname. Every such shape is then decided by the trailing
  deny rules, so the residual sits on the deny side. Accepted, not changed.
- Model limit, accepted: a single space followed by a tab after the remote
  (`origin␣<tab>`, and the refspec form) still completes the `?`, matches no deny
  rule and therefore resolves to `allow` for the Git Manager in the offline
  model. A tab-literal deny would decide (measured), so this is not an
  unreachable rule; it is not added because its only matching input is invisible
  in review, because it would deny a legitimate refspec push if the runtime
  normalises that whitespace — unobservable offline — and because it would close
  one character of a family this pattern language cannot express. The limit is
  named in the Git Manager's model comment and in the workflow document, so no
  shipped sentence claims that every whitespace-only tail is denied.
- Validator mechanism to remember: compound splitting strips each subcommand, so
  a whitespace-only tail inside a compound reduces to the remote-only shape and
  is denied by the project fall-through, while the same string standalone is
  decided by the double-space rule. Outcomes now agree for every space-shaped
  tail; only the tab family still diverges, in the allow direction, standalone.
- Auditor design choice (Tester F3): a dotted `subprocess.subprocess.run([...])`
  receiver is audited shape-based like plain `subprocess`, not rejected outright.
  A pinned read-only `git` argv therefore passes; a non-`git` argv or a non-literal
  `shell` keyword through the same receiver is rejected. Stated in the docstring
  so the next maintainer does not read the pass as an oversight.
- The external owner review on PR #32 was read from the review body by the
  Orchestrator and answered point by point in a posted comment. The review text
  is owner-authored evidence, not something this workflow produced; the answer
  was applied through the GitHub MCP server and read back byte-identically.
- Effective session policy is stricter than the agent file for three allows:
  `gh pr edit*`, `gh pr comment*` and `git fetch*` are allowed in
  `.opencode/agents/git-manager.md` but resolved to `deny` in the session, so
  the two GitHub writes went through the MCP server. Open follow-up: either make
  the allows effective or remove them and document the MCP path as the intended
  channel.
- The GitHub MCP server exposed `merge_pull_request` and
  `update_pull_request_branch` to the Git Manager session. The workflow rule and
  the shell rules reserve merging for the human, and no agent merged, but the
  capability is reachable outside them. This is the concrete case behind the
  open R-3 decision on per-role tool and MCP lockdown, and it must be closed
  before the human-only control is described as complete rather than intended.

## Deferred or out-of-scope work

- Application implementation (#27–#29).
- Additional specialist agents.
- Automatic model selection and live benchmark execution.
- Advanced workflow automation.
- Live inference remains subject to the existing approval and capability gates.

## Handover

**The ledger structure check is now in `ci`.** `check_ledger_structure()` runs
in `ci` and `all`: eight required sections, exactly once each and in order;
three required tables with 6/5/4 columns and row predicates located by header;
every table block validated for self-consistency against its own header, which
is what lets prose sections and the plan's inner tables pass; and four forbidden
payload shapes absent — the oldString and newString tool-payload literals, a
backslash-n pipe escape, and a tool-call tail. The current ledger passes: 229 data rows,
16 blocks self-consistent, no forbidden shape. The check was built against the
two real incidents, and both reproduce as failures against the real file: the
five-cell row names line 482 with both counts, and the payload literal is named
at the same line.

- Plan review: workflow gates defined; synthetic reconciliation covers planner,
  implementer and reviewer reports.
- Code review: independent review of every state. The Reviewer cleared
  `498444c` with two merge blockers, cleared `4d3f6dc` after both were fixed,
  cleared `613c13a` with no item to fix before the pull request, and cleared the
  reconciliation merge `f19d1c5` as acceptable to push with no correctness,
  security, privacy or baseline regression. It then reviewed the
  external-review delta in five passes, each against a frozen fingerprint: the
  first found no blocker and eight improvements; the second confirmed all eight
  and found four more, chiefly that the remote-only push deny was an `origin`
  literal while five prose locations claimed the category; the third found the
  remaining whitespace tail on the allow side (`origin` plus two spaces still
  completed `?*`); the fourth found that the corrected prose still claimed to
  close "the one gap this pattern language leaves open" while the tab shape
  stayed open; the fifth confirmed that the tab limit is stated with the
  cost/observability reason and that the three-outcome clause is exhaustive. The push control was inverted rather than re-worded — the Git
  Manager now holds an allowlist (`git push origin ?*` plus a trailing deny for
  the two-space form), so every other push falls through to the project deny
  and the prose only has to state what the allow grants and where the recorded
  limit sits. The compound finding was resolved as a validator-fidelity issue
  against the official OpenCode V2 scanner semantics, not by adding rules. The
  fourth pass closed the documentation-truth blocker on the frozen tree
  `5116b645…` with `ready for handover`.
- Test evidence: the Tester's final delta report on `613c13a` passed 11/11
  checks, including a 12-case splitter probe, the 48-cell compound matrix,
  four mutated ADR assertions that all fail as required, and the hygiene scans.
  The reconciliation-merge report on `f19d1c5` passed 12 checks, including the
  byte-identical Go imports, the `.gitignore` union, the verbatim ADR decision
  text, a green `gofmt`/`go vet`/`go build`/`go test` (22 tests, 3 packages) and
  the extended permission matrix. The review-delta round then passed four
  verifications: the audit gate falsified against patched copies and proven
  fail-closed, the push matrix and a 2340-cell cluster sweep with zero
  non-denies, the reconciliation and supersession cases with their own fixtures,
  and the final pass measured 34/34 resolution cells, proved the fall-through
  with the Git Manager's rules removed in memory, and showed that a `?*`→`*`
  mutant makes `all` fail on the trailing-space sample. The whitespace round
  added 432 deny checks and 1,800 module expectations with zero mismatches, and
  proved the two new denies load-bearing: removing them fails exactly the four
  samples they decide. The documentation-truth round was re-verified with no
  behavioural delta: the only rule change against the previously verified tree
  is the two double-space denies, `opencode.jsonc` is untouched, the pin list
  grew by exactly those two entries, and every earlier anchor reproduced. The
  granted/limit round was prose-only. On the final tree `python3
  tools/workflow_check.py all` exits 0 twice byte-identically and the recorded
  output is byte-identical to a fresh run.
- Review target: the frozen fingerprint is the SHA-256 of the tracked diff
  against `HEAD` with the ledger excluded — `git diff HEAD -- .
  ':(exclude)docs/workflow/ledgers/issue-30.md' | shasum -a 256`. The final value
  is `5116b64519199a2ba6f4b08f141f9558e8af26d5ad8af620b62f43246ea3181a`; every
  earlier target in this round used the same command. The ledger and the
  untracked `.idea/` directory are outside the reviewed diff by construction.
- Residual risks and follow-ups: the accepted residuals are recorded in
  ADR-0002 under `# Residual risks`; the open follow-ups are listed in the
  unresolved items above, including the accepted tab limit, the push-shape
  residual on the deny side, the runtime behaviour that cannot be observed
  offline and the deferred CI job and role-lockdown decisions.
- Human approval: granted on 2026-11-26 for the commits, the push, opening the
  pull request, and normalising the branch against the new `main` (rename to
  ADR-0003) plus read-only `git ls-tree`. Granted again on 2026-11-27 for this
  handover round: commit the review delta, commit the ledger, push without
  force, update the pull-request description and answer the external review.
  Merging stays with the human user.
- Git Manager: committed and pushed the three commits
  (`498444c`, `4d3f6dc`, `613c13a`) on
  `issue-30-multi-agent-development-workflow` and opened PR #32; after `main`
  advanced to `17cf55a` it created the reconciliation merge `f19d1c5` (parents
  `613c13a`, `17cf55a`), committed the ledger refresh `97fd890` and pushed the
  branch as a fast-forward. This round it committed the review delta as
  `c9fc085` (39 files, +2677/−131) on top of `97fd890`, excluding the ledger and
  `.idea/`. The handover then added `32977e1` (the five reviewed files) and
  `5f55d0e` (the ledger), pushed them as `97fd890..5f55d0e`, replaced the
  pull-request description with the final state and posted the point-by-point
  answer to the external review. No force push, no merge, no branch-protection
  change.
- Handover complete: the branch `issue-30-multi-agent-development-workflow` is
  published, PR #32 is `OPEN` and mergeable, the description reflects the final
  tree and the review answer is posted. The reviewed fingerprint
  `5116b645…` is unchanged by the ledger-only commit.
- Open for the human: review and merge PR #32, which also accepts ADR-0002 and
  the normalised ADR-0003 record; decide the per-role tool and MCP lockdown
  (the handover showed a reachable `merge_pull_request`, so this is no longer
  hypothetical); schedule the post-merge CI job and the deferred follow-ups.
  Merging the pull request remains the human's step, and no agent merged.
