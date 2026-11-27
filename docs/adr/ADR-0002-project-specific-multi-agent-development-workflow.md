---
id: ADR-0002
title: Adopt a project-specific multi-agent development workflow
status: Accepted
date: 2026-11-26
issues: [30]
supersedes: []
superseded-by: null
conflicts-with: []
---

# Context

The project needs a repeatable way to turn issues into planned, implemented,
tested and reviewed changes before application development starts. The workflow
must keep architecture decisions visible, keep credentials and personal model
assignments out of the repository, and give specialists clear capabilities
without losing overall accountability.

# Decision

Adopt one Orchestrator and five specialist subagents for project development:

- `orchestrator` (primary) owns intake, delegation, the acceptance-criteria
  ledger, reconciliation, escalation and the human handover;
- `planner` produces acceptance-criteria-driven plans, architecture impact and
  ADR proposals;
- `reviewer` performs independent plan review and independent code review;
- `implementer` implements the reviewed plan and records evidence;
- `tester` verifies behaviour independently and records reproducible evidence;
- `git-manager` performs branch, commit, push and pull-request preparation after
  the review gates and explicit human approval; merging a pull request is
  reserved for the human user.

The workflow uses:

- project agent definitions in `.opencode/agents/`;
- a project-wide, ordered permission policy in `opencode.jsonc` in which the
  last matching rule wins;
- repository-wide instructions in `AGENTS.md`;
- the structured feedback contract in `docs/workflow/feedback-contract.md`;
- the ADR lifecycle and baseline rules in `docs/adr/README.md`;
- the offline workflow validator in `tools/workflow_check.py`.

The permission policy implements four standing rules:

- **RTK-aware command boundaries.** Git and GitHub are denied first, and
  read-only inspection is re-enabled in plain and RTK form (`rtk git`,
  `rtk gh` mirror the plain rules). The RTK file and report tools are allowed
  for output condensing; `rtk test`, `rtk err` and `rtk summary` execute hidden
  commands and are denied except for the narrow Go quality-tool filters
  (`rtk test *govulncheck*`, `rtk test *golangci-lint*`,
  `rtk test *jactionlint*`), while `rtk bypass` and `rtk proxy` ask. Nested
  write commands (`*git add *`, `*git commit *`, `*git push *`, `*gh pr
  create*`, `*gh api *`, and similar) are denied in every scanner-produced
  command string, so wrappers and compound commands cannot smuggle writes past
  the role boundaries.
- **Credential-path denials.** Credential stores and secret files — including
  `~/.ssh/`, `~/.aws/`, `~/.gnupg/`, `~/.config/gh/`, `~/.kube/`,
  `~/.docker/config.json`, `~/.netrc`, `~/.git-credentials`, `~/.npmrc`,
  `~/.pypirc`, the OpenCode authentication database and logs, and
  `~/Library/Keychains/` — are denied for `read`, `edit` and
  `external_directory`, and the same locations are denied inside shell command
  strings. Every `*.env` file is denied except an `.env.example` or
  `*.env.example` template, if present; `~/.config/opencode/*` stays local and
  is used on approval only, also from shell command arguments.
- **External-path approval.** The `external_directory` gate asks for approval
  before anything outside the worktree is accessed, and RTK commands that
  reference home or parent-directory paths ask as well. Scratch work therefore
  belongs under `.tmp/` inside the worktree.
- **Human-only merge enforcement.** `gh api` and `gh pr merge` are denied
  project-wide, and pushes to `main` are denied even for the Git Manager, so
  the human-only merge decision from the alternatives below is enforced by the
  permission layer and not only by instruction.

Model assignments remain configurable in the global OpenCode configuration or
in optional project overrides. The repository keeps credentials and personal
provider configuration out of version control.

## Implemented verification, provenance and release-gate rules

The offline validator (`tools/workflow_check.py`), shared feedback contract
(`docs/workflow/feedback-contract.md`) and workflow documentation
(`docs/workflow/development-workflow.md`, `docs/validation/README.md`) enforce
the following gate and evidence rules:

- **Report provenance and privacy.** Every delegated report must include
  `model`, `provider` and `reviewed_artifact` as non-empty strings; when model
  or provider identity cannot be determined, the explicit `"unknown"` sentinel
  is required, while missing or blank values are rejected. `thinking` is
  optional: omitted when unused, and when present must be a non-empty string or
  non-empty JSON object (`"unknown"` when used but unobservable). Provenance is
  limited to provider and model identifiers (and optional thinking setting or
  sentinel); credentials, endpoints, account details, personal configuration and
  reasoning traces stay out of repository reports. Actual identity truth and the
  absence of reasoning traces are inspected by the Reviewer and are not proven
  by the offline validator.
- **Required-check taxonomy and structured evidence.** Required release-record
  slots (`plan_review`, `ai_code_review`, `human_review`,
  `tester_verification`, `workflow_validator_ci`) accept only the five-value
  `CHECK_STATES` taxonomy: `passed`, `failed`, `skipped`, `unavailable` and
  `contributor-reported`. Only `passed` is green, and `workflow_validator_ci`
  additionally requires `inspected: true`, `head == pr_head`, a 7–40 lowercase
  hexadecimal `base_sha`, non-empty `job` and `run`, and
  `continue_on_error: false` (a verified explicit `base_sha` enables a later
  inspected re-run rather than relabelling a skip). In report coverage entries,
  `validate_report()` runs before `reconcile()` and requires every structured
  evidence item on a `covered` claim to name an `artifact`, while a `covered`
  claim counts in `reconcile()` only when the reporting agent is delegated the
  criterion, `reviewed_artifact` matches the current `artifact` (when provided),
  `evidence` contains at least one content-bearing item (vacuous sentinels such
  as `"none"` count as absent), and every structured evidence item records
  `check_state: "passed"`; an absent or blank state renders as `missing`, and
  any non-`passed` state — including `failed`, `skipped`, `unavailable`,
  `contributor-reported` or `blocked` — keeps the criterion open with
  `evidence:<state>:<agent>` and `follow_up:<criterion_id>`.
- **Disagreement demotion.** When counted reports assert contradictory
  supported coverage values for the same criterion, `reconcile()` demotes the
  criterion status to `unverified` (`covered` never wins a contradiction) and
  records `<criterion_id>:disagreement:<values>` together with
  `follow_up:<criterion_id>`, blocking release (`disagreement:present`).
- **Decision and proposal escalation.** Non-empty
  `adr_alignment.decision_needed` entries escalate as
  `decision:<agent>:<task_id>:<id>` (`decision_needed:present`), and
  `adr_alignment.proposals` entries whose `effective_status` is not `Accepted`
  escalate as `adr:<id>:pending:<effective_status>` (`pending-proposal:present`,
  plus `adr:<id>:declared-accepted-in-open-pr` when declared `Accepted` in an
  open pull request). Both block release regardless of report status. At the
  release-record level, any `proposals` entry with
  `effective_status != "Accepted"` and any required `decisions` entry not in
  `state: "resolved"` with a non-AI `resolved_by`, non-empty `rationale` and
  `reference`, and `head == pr_head` likewise block release. This real
  `ADR-0002` record carries `conflicts-with: []` and has no conflict with
  `ADR-0001` or `ADR-0003`; any `adr:ADR-0002:conflicts:ADR-0001` escalation
  observed during validation originates from the synthetic open-pull-request
  fixture under `docs/validation/fixtures/adr/open-pr/`, not from this file.
- **Plan identity.** `check_plan_identity()` binds the reviewed implementation
  plan by `(commit, path, section sha256)`: it reads the committed ledger blob
  with `git show <commit>:<path>`, extracts the section using anchored
  line-start `MULTILINE` headings (a unique `^## Implementation plan (revision 2)$`
  through immediately before the following `^## Reports reconciled$`), asserts
  the trailing blank line (`\n\n`), and verifies the UTF-8 SHA-256 digest. Byte
  offsets are deliberately not asserted because unrelated ledger edits move
  offsets while the reviewed section bytes stay frozen.
- **Artefact binding.** The Orchestrator-owned release record
  (`docs/workflow/ledgers/issue-30.release.json` for issue #30) accepts only
  the closed top-level key set `RELEASE_KEYS` (unknown top-level keys fail as
  `release-record:unknown-key:<key>`). Both `pr_head` and the record's
  `artifact` must be full 40-character lowercase hexadecimal commit identities
  (`^[0-9a-f]{40}$`), and `artifact` must equal `pr_head`, with no fallback and
  no frozen-diff form in the release record. A working-tree or frozen-diff
  review is an intermediate state: before `release_ready` can be true, the
  change must be committed and `artifact`, `pr_head`, all evidence slot heads
  and every report's `reviewed_artifact` must be re-bound together to the
  handover commit.
- **Named-human review slot.** The `human_review` slot requires
  `state: "passed"`, `reviewer_type: "human"`, non-empty `name` and `login`
  distinct from each other (`name.lower() != login.lower()`) and outside the
  ineligible AI-identity set (the static `AI_IDENTITIES` roles plus any
  `reviewer`, `name`, `login` or `model` string recorded in `ai_code_review` or
  `plan_review` in the same record, compared literally after lowercase
  normalisation and stripping; separator differences are not normalised),
  `attribution: "human"` (case-insensitive), `independent: true`, `provenance`
  in `{"pr-review", "owner-record"}` with its corresponding non-empty
  reference (`review_id` or `record`), a non-empty `timestamp`, and
  `head == pr_head`. AI identities are ineligible, including an AI-authored
  owner review. The validator checks only the recorded identity fields and
  provenance; genuine human independence remains attested human judgement.
- **Single `release_ready` boolean and validator modes.**
  `evaluate_release_gate()` returns a single `release_ready` boolean and a
  sorted blocker list. `release_ready` is true only when all conjuncts hold:
  committed `plan_review` passed, independent `ai_code_review` passed,
  named-human `human_review` passed, `tester_verification` passed, inspected
  `workflow_validator_ci` passed, all required criteria `covered` against the
  current `artifact`, no reconciled or record-declared `gaps`, no disagreements,
  no `decision_needed`, no pending effective proposals, no open or improperly
  resolved required decisions, no unknown top-level keys, and exact `pr_head`
  agreement across all evidence. In `tools/workflow_check.py`, `ci` is the
  trusted offline mode: it runs `check_self_audit()` first (loading
  `tools/audit_validator.py` to check six static AST properties before any
  result is trusted), then `check_config()`, `check_fixtures()`,
  `check_plan_identity()` and `check_adr_actual()`. `all` runs `ci` plus
  `check_live_release()` against the live release record and exits non-zero
  (`1`) whenever `release_ready` is false or the live record is missing or
  unusable; synthetic all-green fixtures prove the evaluator only and never
  establish live readiness. Individual subcommands (`config`, `adr`, `reports`,
  `fixtures`) are uncertified diagnostics that omit the self-audit.

## Right-sized work items

Before detailed planning, the Planner sizes the work item without rigid numeric
thresholds (`docs/workflow/development-workflow.md` `## Right-sized work items`,
`docs/workflow/ledgers/README.md` `## Work-item sizing template`,
`tools/workflow_check.py` `RIGHT_SIZED_FACTORS`, `RIGID_THRESHOLD_KEYS`,
`validate_right_sized_work_item()`, `check_right_sized_work_item_fixture()`,
`docs/validation/fixtures/workflow/planning/right-sized.json`, and
`docs/validation/README.md` `### Right-sized work items`):

- **Nine sizing factors.** Every sizing record weighs all nine factors:
  `cohesion`, `dependencies`, `complexity`, `architectural_impact`,
  `side_effects`, `testability`, `agent_context`, `coordination_overhead` and
  `ai_human_review_effort`.
- **Independently verifiable outcomes and no rigid thresholds.** A split is
  recommended only when each resulting part has an independently verifiable
  outcome (`independently_verifiable: true` with a non-empty `outcome`). Counts
  of criteria, files, lines or bytes are never entry rules:
  `validate_right_sized_work_item()` explicitly rejects `RIGID_THRESHOLD_KEYS`
  (`max_files`, `max_lines`, `max_bytes`, `max_criteria`, `file_limit`,
  `line_limit`, `size_threshold`).
- **Named-human approval for material scope changes.** When
  `scope_change.material` is `true`, the record must include an `approval`
  object with `required: true`, `approved_by: "human"` and a non-empty
  `reference`. Twenty in-memory mutations in
  `check_right_sized_work_item_fixture()` prove each guard by name.
- **What the code does not prove.** The validator checks only the presence and
  shape of the sizing schema fields and rejects the named threshold keys; whether
  a split is genuinely cohesive, right-sized, or whether a scope change is
  material remains Planner and human judgement.

## Canonical delegation packet

One canonical document defines the delegation packet so rules do not drift
across prompts and workflow documentation (`docs/workflow/delegation-packet.md`,
`docs/workflow/development-workflow.md` `## Delegation packet`, `AGENTS.md`
`## Working agreements`, `tools/workflow_check.py`
`DELEGATION_PACKET_DOC_MARKERS`, `DELEGATION_WORKFLOW_DUPLICATED_RULES`,
`validate_delegation_packet_links()`, `validate_delegation_packet()`,
`check_delegation_packet_fixture()`,
`docs/validation/fixtures/workflow/planning/delegation-packet.json`, and
`docs/validation/README.md` `### Delegation packet`):

- **Single normative source and link-only references.**
  `docs/workflow/delegation-packet.md` is the sole normative definition.
  `validate_delegation_packet_links()` verifies that the canonical document
  carries all nine `DELEGATION_PACKET_DOC_MARKERS`, that `AGENTS.md` and the
  `## Delegation packet` section of `docs/workflow/development-workflow.md` link
  to `delegation-packet.md`, and that `development-workflow.md` does not repeat
  the pre-canonical rule bullets (`DELEGATION_WORKFLOW_DUPLICATED_RULES`).
- **Required fields and ownership binding.** `validate_delegation_packet()`
  requires `task_id`, integer `issue`, `agent` (in `WORKFLOW_AGENTS`), non-empty
  `criteria` (each a non-empty string or an object with a non-empty `id`),
  `adr_baseline` (`accepted` and `proposals` lists), non-empty lists for
  `repository_context`, `constraints` and `expected_evidence`, a
  `dependencies` list, non-empty `reviewed_artifact`, and a `write_ownership`
  record whose `agent` and `task_id` match the packet and pass
  `validate_write_ownership()`, preventing delegation of writes to a read-only
  role. Twenty-three mutations (19 packet mutations and 4 link mutations) in
  `check_delegation_packet_fixture()` prove each guard.
- **Context isolation and efficiency.** Packets favour concise, sufficient
  repository path pointers over full issue dumps, and a receiving agent requests
  missing context from the Orchestrator before making a consequential decision
  rather than assuming it.
- **What the code does not prove.** The validator checks only field presence,
  ownership record consistency and canonical links; concision, context
  sufficiency and whether an agent actually asked for missing context remain
  instruction and human-judgement rules.

## Single writer / write ownership

Mutating tasks obey an explicit single-writer protocol recorded before work
starts (`docs/workflow/development-workflow.md` `## Write ownership`,
`docs/workflow/delegation-packet.md` `## Write ownership`,
`docs/workflow/ledgers/README.md` `## Write-ownership record`,
`tools/workflow_check.py` `OWNERSHIP_STATUSES`, `READ_ONLY_WRITE_AGENTS`,
`ROLE_WRITE_PREFIXES`, `IMPLEMENTER_EXCLUDED_PREFIXES`, `_paths_overlap()`,
`_record_scope()`, `validate_write_ownership()`,
`check_write_ownership_fixture()`, `docs/validation/fixtures/workflow/ownership/`,
and `docs/validation/README.md` `### Write ownership`):

- **Record before mutation and serialise overlaps.** Each task records `task_id`,
  `agent`, `status` (`active`, `handed-over` or `closed`), `write_scope`,
  `dependencies` and optional `scratch`. `validate_write_ownership()` checks
  that every `active` record appears in `active_tasks` (rejecting stale
  ownership), that a `handed-over` task names a distinct `active` successor
  record in `handover.to`, and that no two active tasks have overlapping
  effective scopes (`_record_scope()` over `write_scope` plus `scratch` via
  `_paths_overlap()` exact-path and directory-prefix matching). Overlapping
  writes are serialised and handed over; parallel read-only analysis stays
  allowed.
- **Role write scopes.** `orchestrator` may claim only paths under
  `docs/workflow/ledgers/`; `planner` may claim only paths under `docs/adr/`;
  `implementer` may not claim `docs/workflow/ledgers/` or `docs/adr/`;
  `reviewer` and `tester` (`READ_ONLY_WRITE_AGENTS`) may claim no write scope;
  and `git-manager` may claim no repository file write scope (Git and GitHub
  writes only).
- **Task-scoped scratch.** Scratch files live under `.tmp/<task-id>/` inside the
  worktree (`scratch` and any `.tmp/` path in `write_scope` must begin with
  `.tmp/<task-id>/`), are never shared between tasks, and are removed before the
  task reports back. Five ownership fixture files (`disjoint-writes.json`,
  `overlapping-writes.json`, `ownership-handover.json`, `stale-ownership.json`,
  `read-only-write.json`) and 15 in-memory mutations prove these cases.
- **What the code does not prove.** The offline validator inspects only declared
  ownership records and synthetic fixture cases; actual write obedience, scratch
  cleanup and filesystem isolation remain instruction-only limits rather than
  runtime enforcement of which files an agent opened or modified.

## CI validation

Pull-request CI runs the deterministic offline validator through the
`workflow-validator` job (`.github/workflows/ci.yml` lines 256–320,
`docs/workflow/development-workflow.md` `## CI validation`,
`docs/workflow/ledgers/README.md` `## Release record template`,
`tools/workflow_check.py` `CI_VALIDATOR_JOB`, `CI_AUDIT_COMMAND`,
`CI_TRUSTED_COMMAND`, `_yaml_indent()`, `_ci_job_lines()`, `_ci_steps()`,
`_ci_step_script()`, `validate_ci_workflow_contract()`,
`check_ci_workflow_contract()`, and `evaluate_release_gate()` lines 2245–2262,
and `docs/validation/README.md` `### CI workflow contract` and
`## Scope and limitations`):

- **Pull-request-only job and exact-head checkout.** `workflow-validator` is
  gated to `if: github.event_name == 'pull_request'` with `timeout-minutes: 10`,
  inheriting the workflow's top-level `permissions: contents: read`. It pins
  `actions/checkout` to a 40-hex commit SHA with `fetch-depth: 0` (full history
  required for `check_plan_identity()` and base ancestry),
  `persist-credentials: false`, and checks out the exact pull-request head
  (`ref: ${{ github.event.pull_request.head.sha }}`,
  `repository: ${{ github.event.pull_request.head.repo.full_name }}`) rather than
  GitHub's synthetic merge commit.
- **Enforced explicit base and head commit assertions.** `EXPECTED_BASE_SHA`
  must be an explicit 7–40 lowercase hexadecimal commit SHA (never a branch name),
  paired with `EXPECTED_HEAD_SHA` and `BASE_REPOSITORY`. The assertion step
  fetches `+refs/heads/main:refs/remotes/origin/main` from
  `https://github.com/${BASE_REPOSITORY}`, prints expected versus actual head
  and base, and exits `1` if `HEAD != EXPECTED_HEAD_SHA`, if
  `refs/remotes/origin/main != EXPECTED_BASE_SHA`, or if
  `git merge-base --is-ancestor "${EXPECTED_BASE_SHA}" HEAD` fails.
- **Trusted commands and no soft-fail.** Executed non-comment step lines must
  run `python3 tools/audit_validator.py` before
  `python3 tools/workflow_check.py ci`, never `workflow_check.py all` (which
  belongs to the Orchestrator's later live release gate), and `continue-on-error`
  and shell soft-fails (such as `|| true`) are forbidden. Thirty-one in-memory
  mutations in `check_ci_workflow_contract()` prove each `ci-contract:*` guard.
- **Static contract versus inspected run evidence, and base SHA handling.**
  `validate_ci_workflow_contract()` checks static YAML shape only and
  `jactionlint` checks workflow syntax only; neither proves a passing CI run.
  Satisfying the release record's `workflow_validator_ci` slot requires inspected
  run, job, step and log evidence on the exact reviewed head (`state: "passed"`,
  `inspected: true`, `head == pr_head`, 7–40 hex `base_sha`, non-empty `job` and
  `run`, `continue_on_error: false`), and a skipped job is never green. A
  verified explicit `base_sha` is an input to re-running the job for an
  inspected pass, never permission to relabel a `SKIP` line as `passed`.
- **What the code does not prove and operational limits.** Beyond static shape vs
  runtime execution, `_ci_job_lines()`, `_ci_steps()` and `_ci_step_script()`
  form a narrow indentation/regex text parser tailored to this repository's
  workflow layout rather than a full YAML or shell AST parser (and top-level
  `permissions: contents: read` is verified by review rather than by
  `validate_ci_workflow_contract()`). The base fetch uses anonymous HTTPS against
  the public repository URL (a private repository would require a different
  credential-free path and fail closed rather than skip), and `EXPECTED_BASE_SHA`
  requires constant base maintenance in a reviewed commit whenever `main`
  advances.

# Consequences

- Every issue has one accountable coordinator and a stable report format.
- Plan review happens before implementation and code review before pull-request
  completion.
- Acceptance-criteria gaps, omitted delegations and unverified claims become
  visible in the ledger instead of being lost in prose.
- Git and GitHub write operations have one responsible agent and are backed by
  permission rules; the rules are RTK-aware so the proxy cannot bypass them.
- Credential stores, secret files and paths outside the worktree are protected
  at the permission layer and cannot be reached through file tools or plain
  shell command strings.
- `gh api` and pull-request merges are denied for every agent and pushes to
  `main` are denied even for the Git Manager, making the human-only merge
  decision technically enforced.
- Open pull-request ADRs remain proposals; humans approve architecture changes.
- The workflow adds documentation and validation work, but keeps application
  implementation in later issues.
- The release gate is fail-closed: `release_ready` stays `false` (and `all`
  exits non-zero) whenever required live evidence, named-human review,
  inspected CI, commit-bound artefact parity or decision/proposal clearance is
  missing, contradicted or stale.
- Genuine human independence in code review and truthful model/provider
  provenance without reasoning traces remain attested human and Reviewer
  judgement beyond what field-level validation proves.
- Work-item sizing without rigid numeric thresholds, the canonical delegation
  packet and recorded single-writer ownership keep coordination explicit, while
  split cohesion, materiality, context sufficiency, requesting missing context,
  write obedience and filesystem isolation remain Planner, instruction and human
  judgement beyond what schema and ownership-record checks prove.
- Pull-request CI enforces the static `workflow-validator` job shape, exact-head
  checkout and explicit `EXPECTED_BASE_SHA` ancestry; `EXPECTED_BASE_SHA`
  requires deliberate updates when `main` advances, and release readiness still
  depends on inspected run, job, step and log evidence rather than static YAML
  checks alone.

# Residual risks

The following residuals of the permission model were reviewed and are accepted:

- **Shell scanner and compound commands.** OpenCode evaluates shell
  permission checks on scanner-produced command strings across Bash, Zsh,
  POSIX sh and PowerShell, and rules apply to every extracted subcommand and
  `cd` target (see the "Scanner" section of the official permissions page,
  <https://opencode.ai/docs/permissions>). Protected operations — `gh api`,
  pull-request merges and pushes to `main` — are therefore denied in direct
  and compound invocations: the matching subcommand resolves to the standing
  deny even when a preceding subcommand is a legitimate Git Manager operation.
  The offline validator approximates the scanner best-effort by splitting
  samples on the common top-level separators (`&&`, `||`, `;`, `|` and
  newlines) and resolving each subcommand; quoted wrapper arguments stay one
  subcommand, and exotic constructs rely on the scanner's fail-closed
  behaviour for commands it cannot analyse.
- **Plain shell paths outside the worktree.** A general path rule for non-RTK
  shell commands is intentionally not part of the policy, because absolute
  paths inside the worktree also resolve under the home directory and a broad
  rule would ask on every routine command. Credential locations remain denied,
  and RTK commands plus the read/edit file tools require approval outside the
  worktree. The risk is accepted and documented.
- **Minor friction.** The `rtk * ~*` approval rule also fires when an RTK
  command carries a home-path argument, for example `rtk read ~/x`; this is an
  approval prompt, not a silent allow, and is accepted.

# Alternatives considered

- A single general-purpose agent. Rejected because independent review and
  verification would be weaker and role boundaries unclear.
- Separate repositories or external orchestration. Rejected because the
  workflow, ADRs and instructions belong with the project and need to be
  reviewed together.
- Automatically merging agent work. Rejected because architecture and
  implementation changes need human approval.

# Links

- Issue: [#30](https://github.com/PeterKopa/multi-agent-model-advisor/issues/30)
- Related ADRs: `ADR-0001`
- Implementation or workflow:
  `docs/workflow/development-workflow.md`,
  `docs/workflow/delegation-packet.md`,
  `docs/workflow/feedback-contract.md`,
  `docs/workflow/model-assignments.md`,
  `docs/workflow/ledgers/README.md`,
  `docs/validation/README.md`,
  `tools/workflow_check.py`,
  `tools/audit_validator.py`,
  `.github/workflows/ci.yml`,
  `.opencode/agents/`,
  `opencode.jsonc`,
  `AGENTS.md`
- Evidence: `python3 tools/audit_validator.py`,
  `python3 tools/workflow_check.py ci`,
  `python3 tools/workflow_check.py all` and
  `docs/validation/opencode-v2.4.1-discovery.md`

# Review notes

Introduced with the issue #30 workflow change. The ADR becomes part of the
authoritative baseline when a human approves and merges its pull request. The
permission model in the Decision (RTK mirroring, credential-path denials,
external-path approval, human-only merge enforcement) was extended while this
pull request is open; the whole record remains a proposal until that approval.
The residual risks recorded under "Residual risks" were reviewed and explicitly
accepted by the human owner while the pull request is open.

Amended on 2026-11-27 while the issue #30 pull request remains open to align
the Decision, Consequences and Links with the implemented verification,
reconciliation, provenance, plan-identity, artefact-binding, named-human review
and release-gate behaviour in `tools/workflow_check.py`. Frontmatter `status`
remains `Accepted` as declared and its effective status remains `Proposed` until
a human approves and merges the pull request; `conflicts-with` remains `[]` (the
synthetic `adr:ADR-0002:conflicts:ADR-0001` escalation belongs only to the
fixture under `docs/validation/fixtures/adr/open-pr/`).

Amended on 2026-11-28 while the issue #30 pull request remains open to align
the Decision, Consequences and Links with the implemented WI-CO (right-sized
work items, canonical delegation packet, single-writer write ownership) and
WI-CI (`workflow-validator` CI job and static contract) rules. Frontmatter
`status` remains `Accepted` as declared (effective status `Proposed` until a
human approves and merges the pull request) and `conflicts-with` remains `[]`.
