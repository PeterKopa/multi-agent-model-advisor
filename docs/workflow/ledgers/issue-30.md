# Issue 30 — Establish project-specific OpenCode multi-agent development workflow

- Branch: `issue-30-multi-agent-development-workflow`
- Frozen commit: `498444ceaf78f53bae419870202c91e90b43315c` (29 files)
- Hardening commit: `4d3f6dc981cec39607e26879b38a4484a4c5328f` (16 files, +1257/-197)
- Final commit: `613c13ae9b2143cc0e097e6fde487400033707f1` (9 files, +409/-60)
- Reconciliation merge: `f19d1c59e3fc131d5e5d6113a70db119aa4e2f31` (parents `613c13a` and `17cf55a`; 16-path merge delta)
- Pull request: [#32](https://github.com/PeterKopa/multi-agent-model-advisor/pull/32)
- Last updated: 2026-11-26
- Human approval: granted for the commits, the push, pull-request creation and the `main`
  reconciliation; review and merge pending

## Acceptance criteria

| ID | Criterion | Delegated to | Status | Evidence | Gaps / follow-up |
| --- | --- | --- | --- | --- | --- |
| AC-A1 | Define a primary Orchestrator and five subagents: Planner, Reviewer, Implementer, Tester, Git Manager | Implementer | covered | `.opencode/agents/*.md`, `docs/workflow/development-workflow.md`, `opencode debug agents` | none |
| AC-A2 | Establish role boundaries and capability-based permissions, with Git write operations assigned to the Git Manager | Implementer | covered | `opencode.jsonc` ordered deny→allow→ask→deny policy, `.opencode/agents/git-manager.md` write allows with trailing denials, per-agent resolution tables and compound samples in `tools/workflow_check.py`, Implementer hardening reports, Reviewer frozen-diff and delta reports | `gh api`, `gh pr merge` and pushes to `main` resolve to `deny` for all six agents, including the Git Manager. The OpenCode shell scanner checks every extracted subcommand, so the protected operations deny in direct and compound invocations; the validator splits on common separators to model this |
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
| AC-V2 | Validate configuration discovery, ADR baseline handling and feedback reconciliation with offline fixtures and synthetic reports; include an omitted criterion and a proposed ADR in an open-PR scenario | Tester | covered | Tester frozen-commit, delta, final-delta and reconciliation-merge reports (`python3 tools/workflow_check.py all` exit 0, recorded output byte-identical, 53-sample matrix, 48/48 compound cells, mutated ADR self-test, `f19d1c5` verification), Reviewer reports on `498444c`, `4d3f6dc`, `613c13a` and the merge diff | None. Independent verification covers the final commit and the reconciliation merge |
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
| Orchestrator | Ledger reconciliation and handover preparation | Completed | 2026-11-26 | Every report reconciled; final coverage recorded; residuals, follow-ups and human-approval state listed below |

The three commits and the reconciliation merge were verified in sequence. The
frozen-diff reviews cover `498444c`, the delta reviews cover `4d3f6dc`, the
final delta reviews cover `613c13a`, and the merge review covers `f19d1c5`.
Both final reports declared `613c13a` ready for pull-request creation, and the
merge reports declare `f19d1c5` ready to push.

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
| Low | Final delta: `docs/validation/README.md` phrases the environment exemption as "except `.env.example`" while the rules and `AGENTS.md` allow any `*.env.example` template. | Cosmetic documentation polish, deferred to the post-merge documentation follow-up. | Open |
| Medium | `main` advanced to `17cf55a` when PR #31 (Go and Bubble Tea bootstrap, #27) was merged after the branch was frozen, so GitHub reported PR #32 as `CONFLICTING`. The only Git conflict was an add/add on `.gitignore`. | Merged `main` into the branch with a merge commit, resolved `.gitignore` as the union of both rule sets, and left the Go imports byte-identical to `main`. | Resolved |
| Medium | The merge brought in `docs/adr/0001-go-bubble-tea-bootstrap.md`, which used a second ADR convention, a header-style status and the number `0001` twice. The validator discovers only `ADR-*.md`, so that merged ADR would have stayed invisible to the baseline. | Human decision: normalise. Renamed to `ADR-0003`, added frontmatter with `status: Accepted`, preserved the decision text verbatim, updated both root `README.md` links and the ADR index. The normalised file stays a proposal until PR #32 merges. | Resolved by human decision |
| Medium | `git fetch` and `git pull` are on the Git Manager's allowlist yet the runtime rejected both plain forms during the reconciliation, so the work stalled until the human ran `git fetch origin main`. The validator models the rule list and cannot detect this mismatch. | Recorded as a policy/runtime mismatch. No policy change mid-pull-request beyond the owner's `git ls-tree` request; the human fetched once. Follow-up: reproduce and correct the resolution for `git fetch`/`git pull`. | Open |
| Informational | Owner request during the reconciliation: add read-only `git ls-tree` to the permission model. | Added `git ls-tree*` and `rtk git ls-tree*` at project level, `"ls-tree"` to `GIT_READ_COMMANDS`, and the command to the read-only enumeration in `docs/workflow/development-workflow.md`. | Implemented |
| Informational | Tester F1 and Reviewer: the actual ADR-0003 normalisation differed from the delegation's expected-difference list in two template-mandated ways — a `# Decision` heading before the five subsections and the heading normalised to the literal `# Consequences`. Neither changes decision text; the containment check confirmed all 34 decision lines remain verbatim. | Recorded as a delegation-precision note, no code change. Future ADR normalisations should derive the expected surface from `docs/adr/template.md`, not from the implementer's report. | Resolved |
| Informational | Git Manager and Reviewer: the merge had staged the old `docs/adr/0001-…` as `A`, so `git rm` required `-f`; content preservation was verified first against `ADR-0003`. The step-2 `git diff --check` also ran while `.gitignore` was still `AA`, so its clean exit was weaker evidence than it looked. | Recorded as a process note for future merge packets: expect `git rm -f` for merge-staged renames, and run `--check` after the conflict is staged. | Resolved |
| Medium | Reviewer RP-10: the PR #32 description describes the branch as of `613c13a`. It claims the last commit is the ledger update touching "no workflow, rule, validator or fixture file", lists three commits, names only ADR-0001/0002 as proposals, and states "main has no accepted ADR yet" and "accepts both". After `f19d1c5` every one of those statements is wrong. | PR description is refreshed at handover: fourth commit row, the `.gitignore` union, the ADR-0003 normalisation with its proposal status, the `git ls-tree` allow, and the Go/Bubble Tea decision already in force on `main` through PR #31. | Open until the description is updated |
| Low | Reviewer RP-9: the validator's live-tree line `ADR baseline (merged, accepted): []` is an artifact — `resolve_baseline_ref()` prefers the stale local `main` (`73dbbec`, pre-PR #31, no `docs/adr`) over `origin/main`, and `adrs_from_ref` filters `ADR-*.md`, so the in-force legacy bootstrap record is invisible. It must not be read as "main has no accepted ADR". | Recorded as a known validator limitation and a follow-up. Documentation states the real position correctly. | Open (validator follow-up) |
| Low | Reviewer RP-5: `docs/adr/README.md` says "ADR-0003 records the issue #27 bootstrap and was merged with PR #31". Strictly, PR #31 merged `0001-go-bubble-tea-bootstrap.md`; the `ADR-0003` file exists only through PR #32. The following sentences disambiguate, so there is no overclaim. | Optional wording polish, deferred so the reviewed merge commit is not re-opened for a non-blocking sentence. | Deferred |
| Informational | User decision: merging a pull request is reserved for the human user. | Removed `gh pr merge*` from the Git Manager allow rules, added an explicit project deny and a validator assertion, and updated agent and workflow instructions. | Resolved |

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
  this pull request. Until then, the workflow checks treat both ADRs as
  proposals.
- Independent human review and approval of this pull request are required
  before merge.
- Configuration discovery was verified against the local OpenCode v2.4.1 and
  the existing global model assignments. A different OpenCode version or model
  configuration may require a repeated discovery check.
- Final verification before the pull request: Tester and Reviewer both cleared
  `613c13a`, and the recorded validator output matched a fresh run
  byte-for-byte. PR #32 was opened from that state.
- Reconciliation verification: the merge commit `f19d1c5` was verified
  independently by the Tester — state and shape, byte-identical Go imports from
  `main`, the `.gitignore` union, verbatim ADR decision text, link resolution,
  a byte-identical validator run (37 lines), the extended permission matrix
  including `git ls-tree`, and a green `gofmt`/`go vet`/`go build`/`go test`
  (22 tests, 3 packages).
- The residuals below are documented and accepted in ADR-0002 under
  `# Residual risks`:
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
  prefixes, so `git -C <path> …` and read-only commands such as `git rev-list`
  do not match the read allowlist; routine inspection has to use the plain
  `git` forms. `git ls-tree` was added on the owner's request during the
  reconciliation; `git rev-list*` and a `git -C *`-tolerant rule remain deferred
  until after this pull request.
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
- The validator's live-tree line `ADR baseline (merged, accepted): []` is a
  stale-`main` and legacy-filename artifact: `resolve_baseline_ref()` prefers
  the local `main` (`73dbbec`, pre-PR #31) over `origin/main`, and
  `adrs_from_ref` filters `ADR-*.md`. The line must not be cited as evidence
  that `main` has no accepted ADR. Validator follow-up, out of scope here.
- PR #32's description still describes `613c13a`. It must be refreshed at
  handover (fourth commit, `.gitignore` union, ADR-0003 normalisation and
  proposal status, `git ls-tree` allow, bootstrap decision in force on `main`)
  so the human reviewer is not misled.
- Validator follow-up: the eager `setdefault` id in `adr_from_text` still raises
  `IndexError` for an ADR path without a dash. No current call site triggers it.
- Validator-fidelity follow-up: the subcommand splitter handles `&&`, `||`, `;`,
  `|` and newlines. Single `&`, command substitution and process substitution
  are left to the runtime scanner; the model could resolve such a compound to
  `allow`. No enforcement impact.
- Documentation follow-up: align the `docs/validation/README.md` environment
  exemption wording to `*.env.example`.
- Proposed follow-up, not decided: add permanent Markdown hygiene checks
  (relative links, trailing whitespace, heading jumps) to the offline validator
  instead of introducing a Node-based linter, which the permission policy
  denies.

## Deferred or out-of-scope work

- Application implementation (#27–#29).
- Additional specialist agents.
- Automatic model selection and live benchmark execution.
- Advanced workflow automation.
- Live inference remains subject to the existing approval and capability gates.

## Handover

- Plan review: workflow gates defined; synthetic reconciliation covers planner,
  implementer and reviewer reports.
- Code review: four independent rounds. The Reviewer cleared `498444c` with
  two merge blockers, cleared `4d3f6dc` after both were fixed, cleared
  `613c13a` with no item to fix before the pull request, and cleared the
  reconciliation merge `f19d1c5` as acceptable to push with no correctness,
  security, privacy or baseline regression. The compound finding was resolved
  as a validator-fidelity issue against the official OpenCode V2 scanner
  semantics, not by adding rules.
- Test evidence: the Tester's final delta report on `613c13a` passed 11/11
  checks, including a 12-case splitter probe, the 48-cell compound matrix,
  four mutated ADR assertions that all fail as required, and the hygiene scans.
  The reconciliation-merge report on `f19d1c5` passed 12 checks, including the
  byte-identical Go imports, the `.gitignore` union, the verbatim ADR decision
  text, a green `gofmt`/`go vet`/`go build`/`go test` (22 tests, 3 packages) and
  the extended permission matrix. `python3 tools/workflow_check.py all` exits 0
  and the recorded output is byte-identical to a fresh run.
- Residual risks and follow-ups: the accepted residuals are recorded in
  ADR-0002 under `# Residual risks`; the open follow-ups are listed in the
  unresolved items above.
- Human approval: granted on 2026-11-26 for the commits and the push, for
  opening the pull request, and for normalising the branch against the new
  `main` (rename to ADR-0003) and adding read-only `git ls-tree`. Merging stays
  with the human user.
- Git Manager: committed and pushed the three commits
  (`498444c`, `4d3f6dc`, `613c13a`) on
  `issue-30-multi-agent-development-workflow` and opened PR #32. After `main`
  advanced to `17cf55a` the Git Manager created the reconciliation merge
  `f19d1c5` locally (parents `613c13a`, `17cf55a`) — not yet pushed, not merged.
- Open before handover closes: commit this ledger refresh on top of `f19d1c5`
  (docs only, so the reviewed merge stays in history unchanged), push the
  branch, confirm GitHub re-evaluates PR #32 from `CONFLICTING` to `MERGEABLE`,
  and refresh the PR description or add a comment covering the reconciliation.
  Merging the pull request remains the human's step.
