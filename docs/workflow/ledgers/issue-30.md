# Issue 30 — Establish project-specific OpenCode multi-agent development workflow

- Branch: `issue-30-multi-agent-development-workflow`
- Reviewed commit: `498444ceaf78f53bae419870202c91e90b43315c` (frozen diff, 29 files)
- Hardening commit: `4d3f6dc981cec39607e26879b38a4484a4c5328f` (16 files, +1257/-197, pushed)
- Pull request: created after the delta review and human-approval gate
- Last updated: 2026-11-26
- Human approval: granted for commit and push; pull-request review and merge pending

## Acceptance criteria

| ID | Criterion | Delegated to | Status | Evidence | Gaps / follow-up |
| --- | --- | --- | --- | --- | --- |
| AC-A1 | Define a primary Orchestrator and five subagents: Planner, Reviewer, Implementer, Tester, Git Manager | Implementer | covered | `.opencode/agents/*.md`, `docs/workflow/development-workflow.md`, `opencode debug agents` | none |
| AC-A2 | Establish role boundaries and capability-based permissions, with Git write operations assigned to the Git Manager | Implementer | covered | `opencode.jsonc` ordered deny→allow→ask→deny policy, `.opencode/agents/git-manager.md` write allows with trailing denials, per-agent resolution tables and compound samples in `tools/workflow_check.py`, Implementer hardening reports, Reviewer frozen-diff and delta reports | `gh api`, `gh pr merge` and pushes to `main` resolve to `deny` for all six agents, including the Git Manager. The OpenCode shell scanner checks every extracted subcommand, so the protected operations deny in direct and compound invocations; the validator splits on common separators to model this |
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
| AC-V2 | Validate configuration discovery, ADR baseline handling and feedback reconciliation with offline fixtures and synthetic reports; include an omitted criterion and a proposed ADR in an open-PR scenario | Tester | covered | Tester frozen-commit report (9/9 checks, `python3 tools/workflow_check.py all` exit 0, recorded output byte-identical), Reviewer frozen-diff report, mutation tests F2–F4, new permission fixture | Evidence covers commit `498444c`. Delta verification of the hardening commit is a handover item, not a criterion gap |
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
| Orchestrator | Ledger reconciliation and handover preparation | in progress | 2026-11-26 | Combined coverage recorded; delta verification and pull-request handover remain |

The hardening round changed files after the frozen commit, so the frozen-diff
reviews above do not cover its diff. Tester and Reviewer delta verification of
the hardening commit is required before the pull request is marked ready.

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
| Informational | User decision: merging a pull request is reserved for the human user. | Removed `gh pr merge*` from the Git Manager allow rules, added an explicit project deny and a validator assertion, and updated agent and workflow instructions. | Resolved |

## Architecture baseline

- Accepted baseline: ADR-0001 and ADR-0002 become accepted when this pull
  request is merged; `main` had no ADR baseline before this change.
- Proposals in this pull request: ADR-0001 and ADR-0002. ADR-0002 now also
  documents the RTK-aware permission model, the credential-path denials, the
  approval rule for paths outside the worktree and the enforcement of
  human-only merge.
- Conflicts: none between the proposals; the fixture exercises a synthetic
  conflict with an already merged baseline.
- Decisions needed: human approval of ADR-0001 and ADR-0002 through the pull
  request. The accepted baseline stays empty until that merge.

## Unresolved items

- The initial ADR baseline is effective only after the human-approved merge of
  this pull request. Until then, the workflow checks treat both ADRs as
  proposals.
- Independent human review and approval of this pull request are required
  before merge.
- Configuration discovery was verified against the local OpenCode v2.4.1 and
  the existing global model assignments. A different OpenCode version or model
  configuration may require a repeated discovery check.
- The hardening round after `498444c` changes `opencode.jsonc`, the Git Manager
  rules, the validator, fixtures and documentation. Tester and Reviewer delta
  verification must run against the hardening commit before the pull request is
  marked ready for human approval.
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
  `git` forms. Adding `git rev-list*` and a `git -C *`-tolerant rule is deferred
  until after this pull request.
- Validator follow-up: the eager `setdefault` id in `adr_from_text` still raises
  `IndexError` for an ADR path without a dash. No current call site triggers it.

## Deferred or out-of-scope work

- Application implementation (#27–#29).
- Additional specialist agents.
- Automatic model selection and live benchmark execution.
- Advanced workflow automation.
- Live inference remains subject to the existing approval and capability gates.

## Handover

- Plan review: workflow gates defined; synthetic reconciliation covers planner,
  implementer and reviewer reports.
- Code review: Reviewer completed the frozen-diff re-review of `498444c` and
  found no Critical or High defect. Its two merge blockers (F-1 `gh api`,
  F-2 `action: "*"`) and the Low/Informational findings are addressed in
  `4d3f6dc`. Delta review of `498444c..4d3f6dc` is running.
- Test evidence: commit `4d3f6dc` passes `python3 tools/workflow_check.py all`
  (exit 0) and the recorded output is byte-identical to a fresh run. The
  Tester's frozen-commit report passed all nine checks on `498444c`. Its delta
  report on `4d3f6dc` is completed: every standalone boundary is correct, but
  the compound-prefix bypass (High) blocks the pull request until fixed.
- Follow-up round implemented: the rule set is unchanged, the validator models
  compound commands the way the OpenCode scanner does, the compound samples and
  the ADR self-test are in place, and the `~/.config/opencode` shell ask and the
  wording corrections are applied. The next step is a second commit followed by
  a final delta verification; the pull request stays on hold until then.
- Human approval: granted on 2026-11-26 for the commit and push, with the pull
  request to follow after green delta verification. The two residual risks
  above are accepted and recorded in ADR-0002. Merging stays with the human
  user.
- Git Manager: committed and pushed `4d3f6dc` on
  `issue-30-multi-agent-development-workflow`; no pull request yet, no merge.
  Pull-request creation follows once both delta reports are green.
