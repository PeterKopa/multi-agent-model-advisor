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

| ID | Criterion | Delegated to | Status | Evidence | Gaps / follow-up |
| --- | --- | --- | --- | --- | --- |
| AC-A1 | Define a primary Orchestrator and five subagents: Planner, Reviewer, Implementer, Tester, Git Manager | Implementer | covered | `.opencode/agents/*.md`, `docs/workflow/development-workflow.md`, `opencode debug agents` | none |
| AC-A2 | Establish role boundaries and capability-based permissions, with Git write operations assigned to the Git Manager | Implementer | covered | `opencode.jsonc` ordered deny→allow→ask→deny policy, `.opencode/agents/git-manager.md` allowlist (`git push origin ?*` plus the write commands it owns) with trailing denials, per-agent resolution tables and compound samples in `tools/workflow_check.py`, Implementer hardening reports, Reviewer frozen-diff and delta reports, Tester 34/34 resolution table, final frozen tree `5116b645…` with the tab limit stated | `gh api`, `gh pr merge` and pushes to `main` resolve to `deny` for all six agents, including the Git Manager. Every push that does not name `origin` with a non-empty refspec separated by a single space falls through to the project deny or is caught by an explicit trailing deny — a second space after the remote is denied too, and the one shape the pattern language cannot express (a tab after the space) is recorded as a limit rather than granted. The OpenCode shell scanner checks every extracted subcommand, so the protected operations deny in direct and compound invocations; the validator splits on common separators to model this |
| AC-A3 | Use positive, actionable and constructive language; express restrictions through permissions and explicit responsibilities | Implementer | covered | Agent prompts and `AGENTS.md` | none |
| AC-A4 | Support configurable model assignments and preserve existing global configuration | Implementer | covered | `docs/workflow/model-assignments.md`, `opencode debug config`, inherited effective models | none |
| AC-A5 | Verify project-specific agent discovery with OpenCode v2.4.1 and document layout and shared instruction loading | Implementer | covered | `docs/validation/opencode-v2.4.1-discovery.md`, `opencode debug agents` | none |
| AC-D1 | Establish ADR directory, template and lifecycle: Proposed, In Review, Accepted, Rejected, Superseded | Implementer | covered | `docs/adr/README.md`, `docs/adr/template.md` | none |
| AC-D2 | Use explicitly approved, accepted ADRs merged into the default branch as the authoritative baseline | Implementer | covered | `docs/adr/README.md`, `tools/workflow_check.py adr`, reconciliation-merge evidence (`17cf55a` as ancestor, `ADR-0003` normalisation) | The Go and Bubble Tea bootstrap decision from #27 is in force on `main` since PR #31; the named `ADR-0001/0002/0003` baseline becomes effective when this pull request is merged |
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

The commits and the reconciliation merge were verified in sequence. The
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
| Low | Final delta: the validator splits only on `&&`, `||`, `;`, `|` and newlines, so a single `&`, `$()` or backtick compound can resolve to `allow` in the model. The runtime shell scanner splits `&` and fails closed for commands it cannot analyse, so the enforcement boundary is intact. | Recorded as a validator-fidelity residual. No rule or code change before the pull request; extending the splitter is a follow-up if strict model fidelity is wanted. | Open |
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
- Conflicts: the validator escalates `adr:ADR-0002:conflicts:ADR-0001` because
  ADR-0002 declares a conflict with the not-yet-accepted ADR-0001. Both are
  proposals of this pull request, so the escalation resolves on the human merge
  and is recorded rather than silently dropped.
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
