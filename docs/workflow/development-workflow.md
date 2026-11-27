# Development workflow

This document defines the project-specific OpenCode workflow for the
Multi-Agent Model Advisor. It implements [issue #30](https://github.com/PeterKopa/multi-agent-model-advisor/issues/30)
and is scoped to the development workflow and its supporting documentation.

## Goals

- Deliver issues through small, reviewable changes with explicit acceptance
  criteria and evidence.
- Keep architecture decisions visible, versioned and approved by a human.
- Use specialist agents with clear capabilities while keeping one Orchestrator
  accountable for the whole issue.
- Make every delegated task return a structured report that can be reconciled
  against the acceptance criteria.
- Keep credentials, personal model assignments and private account settings in
  their authorised local locations.

AI agents own planning, implementation, automated verification, independent
technical review and pull-request preparation. The human defines and approves
goals, significant scope and architecture decisions, independently reviews the
code and retains final approval and merge authority. This allocation is an
instruction and human-judgement rule: the offline validator checks the required
evidence slots, not whether the agents actually behaved AI-first.

## Review, evidence binding and the release gate

Plan review, code review, test evidence and handover bind to an identifiable
artefact — the reviewed commit or a frozen diff. The reviewed plan is the
committed ledger section identified by `(commit, ledger path, section
SHA-256)`; the plan bytes are frozen, and a byte offset is deliberately not
asserted because unrelated ledger sections move while the plan section does
not. Reports carry `reviewed_artifact` and their evidence is stale when it was
produced against a different artefact. A material change after review
revalidates the affected gates and reconciles the final pull-request head with
the reviewed evidence. A frozen-diff review is an intermediate state: handover
re-runs the deterministic checks on the committed head and re-binds the release
record to that commit.

Two independent reviews are required before merge: an independent AI code
review by the Reviewer, which reads the original issue and all acceptance
criteria independently of the implementation plan, and an independent named
human review. The Reviewer's validation binds the review to the artefact;
genuine independence remains Reviewer and human judgement, labelled as such.
The human review slot requires a distinct human-attributed name and login,
`reviewer_type: human`, an independent-review attestation, PR-review or
owner-record provenance, a timestamp and the final head. AI identities are
ineligible, including an AI-authored owner review.

The Orchestrator records the live release evidence in the machine-readable
release record (`docs/workflow/ledgers/issue-30.release.json` for issue #30).
`release_ready` is one boolean, not a prose verdict; every required criterion,
gate, decision, proposal and head binding must hold, and the record `artifact`
must equal `pr_head` — the full 40-hex handover commit; the record has no
frozen-diff form. Missing or unusable live input is `unavailable` and false. A
synthetic all-green fixture proves the evaluator only and never proves real
readiness.

## Right-sized work items

Size the work before detailed planning. Weigh nine factors: cohesion,
dependencies, complexity, architectural impact, side effects, testability,
agent context, coordination overhead and AI/human review effort. Recommend a
split only when each part has an independently verifiable outcome, and present
a material scope change for named-human approval before planning it.

There are no rigid size thresholds. A count of criteria, files or lines is not
a rule: a work item is right-sized when its outcome can be verified
independently and the factors above are weighed, not when it stays under a
number. The fixture
`docs/validation/fixtures/workflow/planning/right-sized.json` and
`check_right_sized_work_item_fixture()` require the nine factors, an
independently verifiable outcome and named-human approval for a material scope
change. Whether a split is cohesive or a change is material remains Planner and
human judgement, labelled as such.

## Roles and boundaries

| Agent | Mode | Primary responsibility | Key capabilities |
| --- | --- | --- | --- |
| `orchestrator` | primary | Intake, delegation, ledger, reconciliation, escalation and handover | Read access, ledger edits under `docs/workflow/ledgers/`, launching the five specialist subagents |
| `planner` | subagent | Acceptance-criteria-driven planning, architecture impact, ADR proposals | Read access and edits under `docs/adr/` |
| `reviewer` | subagent | Independent plan review and independent code review | `edit` denied by its agent rules (`write`/`patch` are named by no rule in this repository); shell remains permission-controlled |
| `implementer` | subagent | Implementation, tests and implementation evidence | Repository edits and local commands |
| `tester` | subagent | Independent verification, test execution and reproducible evidence | `edit` denied by its agent rules (`write`/`patch` are named by no rule in this repository); local command execution |
| `git-manager` | subagent | Branch, commit, push and pull-request preparation after approval; merge stays with the human user | Git and GitHub write operations, except pull-request merge |

The Orchestrator is the only agent that launches subagents. The Reviewer and
Tester work independently of the Implementer. Project-level permission rules in
`opencode.jsonc` implement the permission model below; the agent instructions
describe the positive responsibility of each role.

## Permission model

OpenCode resolves permissions as ordered `{action, resource, effect}` rules and
the **last matching rule wins**. Agent rules from `.opencode/agents/*.md` are
appended after the project rules from `opencode.jsonc`, so an agent can refine
the project policy for its own role and a later project denial can only be
overturned by a later agent allow. Effects are `deny` (blocked without
approval), `ask` (the operator must approve) and `allow`. The project policy
reads in that order: deny → allow → ask → deny.

Shell permission checks use OpenCode's built-in shell scanner across Bash,
Zsh, POSIX sh and PowerShell (see the "Scanner" section of
<https://opencode.ai/docs/permissions>). The `shell` resource is the
scanner-produced command string, and a compound command may produce several:
permission rules, saved approval patterns and best-effort directory inference
apply to every extracted subcommand and `cd` target. A command the scanner
cannot analyse fails when any shell deny rule applies to it and otherwise
requires approval for the whole command, which keeps unanalysable input
fail-closed. The offline validator mirrors this model by splitting its samples
on the top-level separators `&&`, `||`, `;`, `|` and newlines and resolving
each subcommand; separators inside quoted wrapper arguments do not split.

- **Git and GitHub by default.** `git *`, `gh *`, `rtk git *` and `rtk gh *` are
  denied first. Read-only inspection (status, diff, log, show, rev-parse,
  rev-list, ls-files, ls-tree, blame, grep, describe, shortlog, merge-base,
  and the read-only `gh` subcommands) is re-enabled in both plain and RTK
  form. Plain `ls` is an explicitly allowed read-only convenience and `cat` is
  approval-gated (`ask`); the credential shell mirrors further down still win
  by last-match, so neither can reach a denied path. The Git Manager
  appends allow rules for the write commands it owns — including the RTK
  mirrors `rtk git add/branch/checkout/commit/push/switch` and
  `rtk gh pr create` — and repeats the protected denials **after** its allows so
  they win for that agent. Destructive git allows (reset, clean, rebase,
  merge, tag, submodule) are deliberately not mirrored to RTK.
- **Human-only merge enforcement.** `gh api*` and `gh pr merge*` are denied
  project-wide and again as the Git Manager's last rules; merging a pull
  request is reserved for the human user. Direct pushes to `main` —
  `git push <remote> main`, `git push <remote> HEAD:main` and
  `git push <remote> HEAD:refs/heads/main`, plus their RTK forms — are denied
  for every agent. Pushes are controlled by an allowlist instead of a deny
  category: the Git Manager's single push allow is `git push origin ?*`
  (with the RTK mirror `rtk git push origin ?*`), where the `?` makes remote
  and refspec separate by exactly one space and demands at least one further
  character, so the handover shape —
  `git push origin <branch>` or `git push origin HEAD`, an explicit origin
  refspec every time, refspec non-empty — is the only push shape the allow
  grants; anything else either matches no allow, is re-denied below, or is
  recorded as a limit. Any second space after `origin` still completes the
  allow, so the Git Manager's final rules re-deny it in plain and RTK form
  (`git push origin  *` and `rtk git push origin  *`): every whitespace-only
  tail with a two-space prefix (two spaces, three or more spaces) and every
  two-space refspec spelling (`git push origin  HEAD`) is denied as the last
  match. A tab in place of the second space is the one shape this pattern
  language cannot express; it resolves to allow in the offline model and is
  recorded as a limit in the Git Manager's rules, not closed with a
  tab-literal rule. Any push that does not reach the allow — another remote
  name (`git push upstream`, `git push github`), a bare `git push`, or a
  remote-only `git push origin` (with or without a single trailing space)
  whose implicit refspec can resolve to a
  configured upstream (which can be `main`) — matches no Git Manager allow
  and falls back to the project-level `git *` deny (for the Git Manager the
  bare form is additionally re-denied by its own trailing rule as the last
  match). Because the Git Manager's own allows can override every project
  deny, its final rules re-create the
  second deny layer: every option-bearing push (`git push -*` and
  `git push * -*`, plain and RTK — any argument that starts with `-`,
  wherever it sits after the verb) is denied, which subsumes all force
  spellings (`--force`, `--force-with-lease` and any short or clustered form
  such as `-uf` or `-uvqf`), `--mirror`, `--all`, `--delete` and its short
  `-d`, and the quiet or dry-run options (`-q`, `--quiet`, `--dry-run`,
  `--follow-tags`); and the blanket `+` and ` :` rules deny a `+`-prefixed
  refname in any position and a delete refspec with or without a remote — a
  legal refname holding a plus sign is denied by the same side effect.
  Because the shell
  scanner evaluates every
  extracted subcommand, these protected operations deny in direct and
  compound invocations: `git fetch origin && gh pr merge 1` denies on the
  second subcommand even though the first is a legitimate Git Manager
  operation.
- **Defence in depth for hidden writes.** `*git add *`, `*git commit *`,
  `*git push *`, `*git merge *`, `*git rebase *`, `*git reset *`,
  `*gh pr create*`, `*gh pr merge*` and `*gh api *` are denied in every
  scanner-produced command string, so writes cannot hide behind a wrapper or
  inside a quoted argument such as `rtk test "jactionlint && git push origin
  main"`, whose quoted payload stays one command string and matches the deny.
  The narrow quality-tool allows sit before those denials, so a compound that
  also contains a write still resolves to deny.
- **RTK mirroring.** RTK condenses output but can also hide the executed
  command. `rtk git`/`rtk gh` mirror the plain rules one-to-one; the RTK file
  and report tools (`rtk read`, `rtk smart`, `rtk grep`, `rtk rg`,
  `rtk ast-grep`, `rtk find`, `rtk ls`, `rtk tree`, `rtk wc`, `rtk diff`,
  `rtk log`, `rtk json`, `rtk deps`, `rtk gain`, `rtk methods`) are allowed.
  `rtk test`, `rtk err` and `rtk summary` execute hidden commands and are
  denied, except the three narrow Go quality-tool filters
  (`rtk test *govulncheck*`, `rtk test *golangci-lint*`,
  `rtk test *jactionlint*`); `rtk bypass` and `rtk proxy` ask.
- **Go quality toolchain.** `go`, `govulncheck`, `golangci-lint` and
  `jactionlint` are allowed directly so quality checks run without approval.
  Filtered runs are allowed only through the narrow `rtk test` patterns above;
  every other `rtk test` invocation stays denied, and a compound command that
  also contains a write still resolves to deny.
- **Ask rules.** Infrastructure, cluster, cloud, database and network tools
  (`docker`, `kubectl`, `oc`, `aws`, `psql`, `wget`, and their RTK mirrors) ask
  for approval. Toolchains the project does not use (`pnpm`, `dotnet`, and
  their RTK mirrors) are denied.
- **Path policy.** Credential and secret locations — `~/.ssh/`, `~/.aws/`,
  `~/.gnupg/`, `~/.config/gh/`, `~/.kube/`, `~/.docker/config.json`, `~/.netrc`,
  `~/.git-credentials`, `~/.npmrc`, `~/.pypirc`,
  `~/.local/share/opencode/auth.json`, the OpenCode database and logs, and
  `~/Library/Keychains/` — are denied for `read`, `edit` and
  `external_directory`, and the same locations are denied inside shell command
  strings through leading-wildcard mirrors. The `external_directory` gate asks
  for approval before anything outside the worktree is touched and then denies
  the credential locations, so paths outside the worktree always require
  approval. Every `*.env` and `*.env.*` file is denied for read and edit except
  an `.env.example` or `*.env.example` template, if present.
  `~/.config/opencode/*` stays local and is readable, editable and reachable
  from shell command arguments on approval only.
- **Scratch convention.** Paths outside the worktree require approval, so
  scratch copies and mutation tests belong under `.tmp/<task-id>/` inside the
  worktree and must be removed afterwards; `.tmp/` is listed in `.gitignore`.
- **Guardrail, not sandbox.** The permission model is a command-level
  guardrail, not a sandbox. It denies and asks on the listed paths and
  command forms, while a shell command that matches no rule resolves to
  `allow` by design in OpenCode. The explicit `ls` and `cat` rules document
  intent within that model, they do not close it; `echo` is deliberately
  unnamed as a convenience because it is a write primitive through `>` and
  `>>`. The Go quality toolchain is allowed directly for every agent, and
  tools or MCP servers inherited from the operator's global configuration sit
  outside this per-role boundary. Role discipline, the review gates and the
  human-approved handover remain part of the control set, and repository-side
  branch protection plus a per-role tool and MCP lockdown are open decisions
  escalated to the human owner.

The offline validator in `tools/workflow_check.py` resolves the full combined
rule set for every agent with last-match-wins semantics and asserts these
effects, including the deny rules that must stay last in the Git Manager
frontmatter. For compound samples it splits the command on the top-level
separators `&&`, `||`, `;`, `|` and newlines, resolves each subcommand and
combines the results as any deny → deny, else any ask → ask, best-effort
mirroring the scanner model above. `.opencode/agents/*.md` must contain exactly
the six workflow agents, each with a `mode`, no `action: "*"` allow rule and —
outside the Git Manager — no allow rule for any action other than `edit` and
`subagent`.

## Write ownership

Before mutating work, record the responsible agent, task, affected files,
dependencies and write scope in the ledger. One writer owns a file at a time:
serialise overlapping writes and pause and hand over when scopes collide. The
Orchestrator is the sole ledger writer, the Implementer owns implementation
changes, the Planner owns ADR proposals, the Reviewer and Tester stay read-only
and Git and GitHub writes stay with the Git Manager. Parallel read-only
analysis is allowed.

Scratch work lives in `.tmp/<task-id>/` and is removed before the task reports
back; two tasks never share a scratch directory. `validate_write_ownership()`
and the fixtures under `docs/validation/fixtures/workflow/ownership/` prove the
disjoint, overlapping, handover, stale-ownership and read-only cases. The
ownership and release-record templates are in
[`ledgers/README.md`](ledgers/README.md). Actual write obedience and
filesystem isolation are instruction-only limits: the validator checks the
recorded ownership records and synthetic cases, not which files an agent really
opened.

## Configuration layout and discovery

The workflow was verified with OpenCode **v2.4.1** from the repository root.
See [`docs/validation/opencode-v2.4.1-discovery.md`](../validation/opencode-v2.4.1-discovery.md)
for the recorded commands and output.

| Path | Purpose | Loading behaviour |
| --- | --- | --- |
| `opencode.jsonc` | Project configuration: default agent, shared instructions and project-wide Git write restrictions | Discovered from the workspace and its ancestors; project values override only the fields they define |
| `.opencode/agents/*.md` | The six agent definitions | Discovered automatically; the file name becomes the agent ID, and frontmatter merges with any global entry that has the same ID |
| `AGENTS.md` | Repository-wide shared instructions | Loaded automatically for every session, after the global instructions |
| `docs/workflow/feedback-contract.md` | Shared feedback contract | Added to every session through the `instructions` array in `opencode.jsonc` |
| `docs/adr/` | Architecture Decision Records | Discovered by convention and referenced by the workflow; not loaded as instructions |

OpenCode searches for project configuration from the current directory upwards.
For a workspace inside this repository, the project configuration and
`.opencode/agents/` definitions apply in addition to the global configuration.
The project configuration does not replace global settings that it does not
mention. Personal model assignments therefore remain in the global
configuration, and the repository configuration keeps only shared workflow
settings. See [`model-assignments.md`](model-assignments.md).

The discovered agent IDs are `orchestrator`, `planner`, `reviewer`,
`implementer`, `tester` and `git-manager`. Agent definitions are reloaded when
the files change; a restart is not required for normal edits.

## Workflow stages

### 1. Intake and baseline check

The Orchestrator reads the issue, its dependencies, the acceptance criteria and
the relevant accepted ADRs. It creates or updates the ledger under
`docs/workflow/ledgers/` and records every criterion before delegating work.
New or modified ADRs in an open pull request are proposals and do not change
the baseline.

### 2. Planning

The Orchestrator sends the Planner a delegation packet. The Planner returns a
plan that maps each criterion to concrete work, affected areas, evidence, risks,
dependencies and ADR impact. When an architecture decision is needed, the
Planner drafts an ADR proposal in `docs/adr/` and links it to the issue.

### 3. Independent plan review

The Reviewer reviews the plan independently before implementation starts. The
review checks coverage, feasibility, risks, test strategy and ADR alignment,
and it binds the review to the reviewed commit and the frozen plan-section
hash. The Reviewer reads the original issue and all acceptance criteria
directly rather than accepting the plan's summary. The Orchestrator records
required changes and asks the Planner to revise the plan when needed; any
plan-content change needs a new revision, plan-only commit and fresh review.

### 4. Implementation and verification

The Implementer implements the reviewed plan and records changed files and local
evidence. The Tester derives checks from the acceptance criteria, runs the
relevant validation and reports reproducible evidence. The Tester does not edit
the repository; failures return to the Implementer through the Orchestrator.

### 5. Independent code review

The Reviewer reviews the final diff, the test evidence and the ADR status. Code
review happens before a pull request is completed and binds to the exact
reviewed commit or frozen diff; a material change revalidates the affected
gates. Findings are ordered by severity and include file or line references,
impact and a concrete action. Review status is `Completed`, `Partial`,
`Blocked` or `Needs Decision`. A separate independent named-human review of the
code is required before merge; the AI review never substitutes for it.

### 6. Reconciliation and escalation

The Orchestrator reconciles every report against the ledger. It combines
coverage from all reports, records missing evidence and looks for criteria that
were omitted from a delegation or from a report. Contradictory supported
coverage values demote the criterion to `unverified` instead of letting
`covered` win. Gaps receive targeted follow-up delegation. Architecture
conflicts, `decision_needed` entries and pending effective proposals are
escalated for explicit human approval and recorded as unresolved items; each
blocks release. Fail-closed means passed, failed, unverified and blocked stay
distinct: a criterion is covered only with sufficient applicable evidence tied
to the correct issue, task, criterion and reviewed artefact, and missing,
skipped, stale, contradictory or blocked evidence stays open.

### 7. Human-approved handover

After the plan review, AI code review, named-human code review and test
evidence are confirmed, the Orchestrator asks a human to approve the handover.
The Git Manager then prepares a focused branch, commit and pull request. The
pull request describes the issue, covered criteria, ADR status, validation
evidence, review status, unresolved items and the approval step. Before
handover the Orchestrator runs the live release gate against the recorded
evidence on the exact final head; `release_ready` must be true. A human reviews
and merges the pull request; merging is reserved for the human user, and agents
do not merge architecture or implementation changes on their own.

## Delegation packet

The normative packet template is
[`delegation-packet.md`](delegation-packet.md). This section is a link only and
does not restate its rules. Packet concision, context sufficiency and
requesting missing context remain instruction and human-judgement rules; the
validator checks the required packet fields, not their quality.

## Shared feedback contract

Every subagent returns the structured report defined in
[`feedback-contract.md`](feedback-contract.md). The report covers status, model
and provider provenance, the reviewed artefact, completed work,
acceptance-criteria coverage and evidence, missing or unverified requirements,
findings, assumptions, dependencies, ADR alignment, recommended next actions
and constructive feedback on the delegation and collaboration. `model` and
`provider` are required and record `unknown` explicitly when the identity is
unavailable; personal provider settings stay in authorised local locations and
reasoning traces stay out of repository reports.

The Orchestrator records every report in the ledger and reconciles coverage from
all reports. A report that omits a delegated criterion is not treated as
complete; it creates a coverage gap that is resolved by follow-up delegation or
explicit escalation.

## Architecture Decision Records

The ADR lifecycle is defined in [`docs/adr/README.md`](../adr/README.md). In
short:

- the authoritative baseline is the set of **Accepted** ADRs merged into the
  default branch;
- ADRs in an open pull request are proposals regardless of their declared
  status, and the previous accepted baseline remains in force;
- Accepted ADRs are explicitly approved by a human and merged into the default
  branch;
- conflicts and pending decisions are escalated instead of being resolved
  silently;
- ADRs link to their issue and to implementation decisions, and each agent
  reports its alignment with the baseline.

## Validation

The workflow is validated offline with fixtures and synthetic reports. Run the
static audit of the validator first, then the trusted offline validation:

```bash
python3 tools/audit_validator.py
python3 tools/workflow_check.py ci
```

`ci` is the trusted offline mode: the audit plus the configuration, ADR,
report, fixture, CI-workflow-contract and frozen-plan-identity checks. It is
deterministic and needs no network access or credentials. The audit and the
validator are guardrails, not sandboxes.

The final `all` mode is `ci` plus the live release record and exits non-zero
whenever `release_ready` is false:

```bash
python3 tools/workflow_check.py all --release-scenario docs/workflow/ledgers/issue-30.release.json
```

`all` is expected to fail until the implementation, tests, CI evidence and the
named-human review are recorded on the final head. Missing or unusable live
input is `unavailable` and false; it never silently passes. Expected-false
synthetic cases run inside the fixture harness and never reach the live exit,
and the synthetic all-green control proves the evaluator only.

The plan-identity check reads the reviewed commit, extracts the plan section
with anchored line-start headings (`## Implementation plan (revision N)` to the
following `## Reports reconciled`) and asserts the recorded SHA-256 plus the
trailing blank line. Byte offsets are not durable: they move with unrelated
ledger edits while the reviewed section bytes stay frozen, so no offset is
asserted.

The validator checks agent configuration and discovery prerequisites, ADR
baseline handling in an open pull-request scenario, feedback reconciliation
with an intentionally omitted acceptance criterion, an unverified criterion and
a proposed ADR that conflicts with the accepted baseline. The fixture harness
also proves the right-sized work-item schema, the delegation-packet fields and
canonical links, the write-ownership cases and the CI workflow contract; those
checks prove the schema and records only, never the quality or obedience of the
work. See [`docs/validation/README.md`](../validation/README.md).

## CI validation

`.github/workflows/ci.yml` carries the `workflow-validator` job, which runs the
deterministic offline validator on every pull request and is the CI evidence for
this workflow. The job:

- checks out the exact pull-request head commit and its repository, not the
  synthetic merge commit GitHub builds for the pull request, with
  `fetch-depth: 0` and `persist-credentials: false`. Full history is required:
  the plan-identity check reads the reviewed plan section out of its commit,
  and the base assertion resolves the recorded base commit;
- records the base the change was reviewed against in `EXPECTED_BASE_SHA` as a
  commit identity and enforces it: the job resolves the base branch from the
  base repository, prints expected versus actual base and head, and fails when
  the checked-out head is not the reviewed head, when `origin/main` does not
  resolve to the recorded base, or when the recorded base is not an ancestor of
  the head. A branch name is never the recorded base; a stale local `main` is
  environment state, not a product failure, and an advanced `main` is handled
  by re-recording the explicit base in a reviewed change, never by relabelling
  a result;
- runs `python3 tools/audit_validator.py` and then
  `python3 tools/workflow_check.py ci` — the trusted `ci` mode, never `all` —
  with no `continue-on-error`. The live release record does not exist yet and
  is evaluated later by the Orchestrator, so `all` belongs to that final gate.

The result is classified with the same five states as every other required
check: `passed`, `failed`, `skipped`, `unavailable` and
`contributor-reported`. Only an inspected `passed` run on the reviewed head is
green; the release record's `workflow_validator_ci` slot additionally needs
`inspected: true`, the recorded `base_sha` and `continue_on_error: false`, and a
failed, skipped, unavailable or contributor-reported required check stays a
blocker. A verified base SHA is an input to re-running the job and obtaining an
inspected pass; it is never permission to relabel a `SKIP` line as a pass. A
named human resolution of such a blocker records identity, rationale,
reference and the final head.

Static checks do not establish `passed`: `check_ci_workflow_contract()` proves
the YAML shape and each guard with a named mutation, and `jactionlint` checks
the workflow syntax only. Binding the release to CI therefore needs the actual
run, job, step and log evidence on the reviewed commit, read back by the
Orchestrator and verified by the Tester. The job runs only for pull requests; a
skipped job is not green and does not fill the CI slot.

## Deferred scope

Application implementation (#27–#29), additional specialist agents, automatic
model selection, live benchmark execution and advanced workflow automation are
outside this workflow issue. Live inference remains subject to the existing
approval and capability gates.
