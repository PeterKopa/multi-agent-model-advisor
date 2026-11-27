# Workflow validation

The workflow has an offline validator that checks configuration, ADR baseline
handling, coordination and ownership rules, and feedback reconciliation without
network access or credentials.

## Run

Run the static audit of the validator first, then the trusted offline mode.
From the repository root:

```bash
python3 tools/audit_validator.py
python3 tools/workflow_check.py ci
```

`ci` is the trusted offline mode: it includes the audit as its first step, the
configuration, ADR, report and fixture checks, the ledger-structure check, the
frozen-plan-identity check and the CI workflow contract. The validator imports
the sibling auditor and
statically bounds its own source before any result is printed, so a result is
only trusted when the audit passes. Run `python3 tools/audit_validator.py`
directly when only the audit gate is needed. The audit is honest about its
limit: it is an AST audit that bounds constructs — a guardrail, not a sandbox.

The final release mode is `all` — `ci` plus the live release record:

```bash
python3 tools/workflow_check.py all --release-scenario docs/workflow/ledgers/issue-30.release.json
```

`all` exits non-zero whenever `release_ready` is false, and a missing or
unusable live record is `unavailable` and false. While the implementation, CI
evidence and named-human review are not yet recorded, a false result is the
expected correct result. Expected-false synthetic cases run inside the fixture
harness and never reach the live exit; a synthetic all-green control proves the
evaluator only, never real release readiness.

Individual checks:

```bash
python3 tools/workflow_check.py config
python3 tools/workflow_check.py adr
python3 tools/workflow_check.py reports
python3 tools/workflow_check.py fixtures
```

`adr` runs only the actual-repository check: it compares the ADRs merged into
the resolved baseline ref with the ADRs in the current working tree. Fixtures
run under different subcommands: `reports` runs the feedback-reconciliation
scenario (`fixtures/workflow/scenario.json`) plus the seventeen invalid-report
cases in `fixtures/workflow/invalid/` — the negative suite is deliberately
invoked from inside `check_reports`, so even a diagnostic `reports` run
certifies the positive and the negative reconciliation behaviour together and
cannot pass only one half of it; `fixtures` runs every fixture file (the ADR,
combined-ADR, in-memory ADR, permissions, ledger-structure in-memory,
in-memory reconciliation, release-gate in-memory, release-record, right-sized
work-item, delegation-packet, write-ownership and CI-workflow-contract cases,
plus the `reports` section above);
`config` and the fixture-driven parts of `ci` run what `reports` and `fixtures`
run.

`ci` and `all` are the trusted entry points: they run the self-audit first.
`config`, `adr`, `reports` and `fixtures` are diagnostics that execute
individual sections only and do not run the audit, so their results are not
certified; use them to inspect one section, and use `ci` or `all` to produce a
trusted run.

Which ADRs are recorded as merged depends on the state of `main` and
`origin/main`: the validator prefers `origin/main` and falls back to the
local `main`, prints a warning when both exist and resolve to different
commits (a stale local `main` is reported, not silently trusted), skips the
section with a deterministic message when neither ref exists, prints an
explicit non-asserting `SKIP adr (live tree)` line when the chosen ref yields
no `ADR-*.md` record under `docs/adr` — the merged-baseline and
open-proposal assertions then run only in the fixtures, and no `PASS adr`
line is printed for a baseline the live tree could not provide — and prints
the resolved baseline, the open proposals and any escalations.
While a workflow change is in an open pull request, its ADRs therefore appear
as proposals even when their frontmatter declares `Accepted`.

## Artifact identity for review and handover

Review, test evidence and handover bind to the exact change set, not to a
description of it. Compute the identity from the files that differ from `HEAD`,
excluding `.idea/**` and `docs/workflow/ledgers/issue-30.md` (the
Orchestrator-owned ledger). For every remaining path, hash the current file
bytes; emit `<sha256>\t<path>`; sort the lines bytewise; the identity is the
SHA-256 of that newline-terminated text.

```bash
python3 - <<'PY'
import hashlib, subprocess

excluded = {".idea", "docs/workflow/ledgers/issue-30.md"}
status = subprocess.run(
    ["git", "status", "--porcelain", "-uall"],
    check=True, capture_output=True, text=True,
).stdout
rows = []
for line in status.splitlines():
    path = line[3:]
    if " -> " in path:
        path = path.split(" -> ", 1)[1]
    if path in excluded or path.startswith(".idea/"):
        continue
    try:
        data = open(path, "rb").read()
    except FileNotFoundError:
        data = b""  # a deleted path contributes the empty-file digest
    rows.append(f"{hashlib.sha256(data).hexdigest()}\t{path}")
rows.sort(key=lambda row: row.encode())
text = "\n".join(rows) + "\n"
print(f"{len(rows)} files")
print(hashlib.sha256(text.encode()).hexdigest())
PY
```

The report publishes the value and the file count; the Tester recomputes both
with the same command and compares them with the reported `reviewed_artifact`.
The identity changes whenever any included byte changes, so it is recomputed
after the last edit; the ledger and `.idea/` stay outside the reviewed change.

## What is checked

### Validator self-audit

`tools/audit_validator.py` statically audits `tools/workflow_check.py` before
the validator is trusted. It parses the file as an AST and executes none of
it, checks six properties and prints one `PASS audit:` line with the checked
property count on success or one `FAIL audit:` line per finding on stderr
with exit code 1:

1. **Imports** — every root module must stay inside a pinned read-only
   standard-library allowlist (`argparse`, `ast`, `fnmatch`, `hashlib`,
   `json`, `re`, `subprocess`, `sys`, `pathlib`, `typing`, `__future__`),
   plus the sibling `audit_validator` module that `all` loads at run time; a
   wildcard import (`from <module> import *`) is rejected outright, because
   a star binding cannot be resolved and would let the auditor lose track of
   what a name refers to;
2. **Forbidden calls and attributes** — `eval`, `exec`, `compile`,
   `__import__`, `os.system`, `os.popen`, and any `subprocess` call — under
   its own name, an `import subprocess as <alias>` alias, a receiver reached
   through extra attribute segments such as `import subprocess.subprocess`
   followed by `subprocess.subprocess.run`, or a
   `from subprocess import <name>` binding (with or without `as`) — with a
   `shell` keyword that is not literal `False`. A `subprocess` spawn
   function (`run`, `call`, `check_call`, `check_output`, `Popen`,
   `getoutput`, `getstatusoutput`) may only appear as the callable of a
   direct `subprocess.<name>(...)` call: any other reference is rejected
   fail-closed — including rebinding it to a name (`runner =
   subprocess.run`, plain, annotated or as a walrus), storing it in a
   container, passing it as an argument, returning it or looping over it —
   because the auditor cannot promise to track every later use of such a
   name;
3. **Subprocess shape and verb pin** — every `subprocess.*` call site,
   including aliased, from-imported and multi-segment receivers, must pass a
   list or tuple literal as its first positional argument whose first
   element is the constant string `"git"` and whose second element is a
   pinned read-only git verb (`subprocess.run(["git", *args], …)` — the
   local `git()` wrapper's dynamic passthrough — is the one accepted dynamic
   shape, because every `git(<verb>, …)` call site is pinned individually by
   property 4). The carve-out is shape-based, not call-site based: any single
   call site whose argv is `["git", <Starred>, …]` is accepted by this
   property, so such a site's argv needs manual review;
4. **Git verb pin over all call sites** — every literal git verb in the
   audited file — the first argument of each local `git(...)` helper call and
   the constant second element of each `subprocess.*` command list — must
   stay in one pinned read-only verb set; the actual set is derived from the
   file and must equal the pinned set exactly, in both directions, so a new
   git verb needs a conscious decision to update `EXPECTED_GIT_VERBS`;
5. **No write access** — no `open()` with a mode containing `w`, `a`, `x` or
   `+` (and no non-literal mode), the same rule applied to
   `Path(...).open(...)` on receivers the Path dataflow recognises, no
   path-mutating method call (`write_text`, `write_bytes`, `unlink`,
   `rename`, `replace`, `mkdir`, `rmdir`, `touch`, `chmod`; plain
   `str.replace` stays allowed because it is read-only) and no `shutil`
   import;
6. **No network modules** — `socket`, `ssl`, `http`, `urllib`, `ftplib`,
   `smtplib`, `telnetlib`, `xmlrpc`, `requests` and `httpx`.

The audit bounds constructs; it is a guardrail, not a sandbox. It cannot
prove runtime behaviour. What it does not cover is stated so the claim stays
honest: dynamic-argument `subprocess` lists other than the audited
`git(*args)` wrapper shape, verbs or modes hidden behind calls the AST cannot
resolve (`getattr`, `globals()`, builtins monkeypatching, dynamic strings), a
`subprocess` alias built without an import or assignment statement (for
example through `getattr(subprocess, "run")`), `subprocess` functions reached
through a receiver the dataflow cannot resolve to the module root (for
example one produced by a call), and `.open(...)` on a receiver that is not
recognised as Path-ish stay outside the checks — reviewer judgement, the
review gates and the human-approved handover remain part of the control set.
The negative behaviour is exercised in a scratch run, not in the repository:
a patched copy of the validator with, for example, an extra `import socket`,
an `eval(` call, a `shell=True` spawn, a non-git command list, an aliased,
from-imported, rebound (`runner = subprocess.run`) or wildcard-imported
`subprocess` spawn with a forbidden verb, a receiver reached through an
extra attribute segment, a new git verb, or a `Path(...).write_text(...)`
or `Path(...).open("w")` call must fail the audit.

### Plan identity

`check_plan_identity()` binds the reviewed plan to durable evidence. It reads
`docs/workflow/ledgers/issue-30.md` from the reviewed commit `e881bb1` with
`git show`, extracts the `## Implementation plan (revision 2)` section with
line-start anchored heading matches (the inline `## Reports reconciled` mention
inside the extraction table cannot shift the slice), asserts the section ends
with the recorded trailing blank line and recomputes the SHA-256, which must
equal `474f2c07…` (23,784 bytes at the reviewed commit). A byte offset is
deliberately not asserted: offsets move when unrelated ledger sections change
while the reviewed bytes stay frozen. A one-byte change, a missing trailing
newline or a different reviewed commit fails the check.

### Ledger structure

`check_ledger_structure()` validates the durable shape of
`docs/workflow/ledgers/issue-30.md` without touching its prose or its frozen
plan section. The Orchestrator's reconciliation ledger is the only
change-set artefact without structural validation, and malformed table rows
have twice reached a commit, so the check asserts:

- the eight required top-level sections — `## Acceptance criteria`,
  `## Implementation plan (revision 2)`, `## Reports reconciled`,
  `## Findings and resolutions`, `## Architecture baseline`,
  `## Unresolved items`, `## Deferred or out-of-scope work` and
  `## Handover` — each exactly once and in that order;
- the three required tables with their header first cell and column count:
  `Acceptance criteria` (`ID`, six columns, every data row starts `AC-`),
  `Reports reconciled` (`Agent`, five columns, an agent-role row begins with
  one of the six roles) and `Findings and resolutions` (`Severity`, four
  columns, a severity row uses `High`, `Medium`, `Low` or `Informational`);
- every row of a required table has exactly that column count, and a failure
  names the line and both counts;
- every other table block is self-consistent against its own header, so a real
  table inside a prose section and the frozen plan's inner tables keep their
  own column counts instead of the required tables' counts;
- the file contains none of the recorded contamination shapes: the raw
  `","oldString"` or `","newString"` edit payload, a literal `\n|` escape, or a
  line that ends in `}` while quoting a JSON key/value pair.

`check_ledger_structure()` reads the working-tree ledger, asserts no byte
offset and does not re-derive the plan identity. Its in-memory fixture proves
a well-formed ledger passes, a five-cell row in the four-column findings table
fails with its line and both counts, the recorded edit payloads, the tool-call
tail and the `\n|` escape fail, missing, duplicated and out-of-order sections
fail, and a prose section wrapped around a real table passes. Removing one
helper flips exactly the cases it owns; the proof is recorded in the
implementation report.

### Configuration

- `opencode.jsonc` selects the Orchestrator, loads the shared feedback contract
  and resolves the ordered permission policy with last-match-wins semantics:
  Git and GitHub are denied by default in plain and RTK form, read-only
  inspection is re-enabled in both forms, `gh api*` and `gh pr merge*` stay
  denied, pushes to `main` are denied, `docker`/`kubectl`/`oc`/`aws`/`psql`/
  `wget` and their RTK mirrors ask, `pnpm`/`dotnet` and their RTK mirrors are
  denied, credential and secret locations are denied for `read`, `edit`,
  `external_directory` and inside shell command strings (the shell mirrors use
  a prefix form, so even a bare listing such as `ls ~/.ssh` denies), every
  `*.env` / `.env.*` file except an `.env.example` or `*.env.example`
  template, if present, is denied, plain `ls` is an allowed read-only
  convenience while `cat` asks for approval, `~/.config/opencode/*` is
  read and edited on approval only, the `external_directory` gate asks for
  anything outside the worktree, and the Go quality tools (`go`, `govulncheck`,
  `golangci-lint`, `jactionlint`) are allowed directly and through the narrow
  `rtk test` filters while the wrapper rules `rtk test`/`rtk err`/
  `rtk summary` stay denied and `rtk bypass`/`rtk proxy` ask. A command that
  matches no rule resolves to `allow` by design in OpenCode, so the model is a
  guardrail with default-allow, not a sandbox.
- `.opencode/agents/` contains exactly the six workflow agents (no extra files),
  each with a required `mode`, description and prompt.
- Agent rules are validated against the role policy: no `action: "*"` allow
  rule anywhere, and outside the Git Manager no allow rule for any action other
  than `edit` and `subagent`. Agents may only deny or ask; allow rules outside
  those two actions are reserved for the Git Manager's write role.
- The Orchestrator can launch exactly the five specialist agents and can write
  only under `docs/workflow/ledgers/`.
- The Planner can draft ADRs, while the Reviewer, Tester and Git Manager deny
  `edit` and `subagent` in their own agent rules (delegation belongs to the
  Orchestrator); the `write` and `patch` tools are named by no rule in this
  repository, so their availability is decided by the operator's global
  configuration. Shell commands remain permission-controlled.
- The Git Manager has the explicit Git and GitHub write allow rules — including
  the RTK write mirrors `rtk git add/branch/checkout/commit/push/switch` and
  `rtk gh pr create` — and the other agents do not. `gh pr merge` and `gh api`
  are denied for every agent, including the Git Manager. The Git Manager's
  push allow is the single allowlist shape `git push origin ?*` (plus its RTK
  mirror `rtk git push origin ?*`); the `?` makes remote and refspec separate
  by exactly one space and demands at least one further character, so only a
  push naming `origin` with a single-space-separated, non-empty refspec
  passes the allow, while another remote name, a
  bare `git push`, or a remote-only `git push origin` (with or without a
  single trailing space) whose implicit refspec can be `main` —
  matches no Git Manager allow and falls back to the project-level `git *`
  deny (for the Git Manager the bare form is additionally re-denied by its
  own trailing rule as the last match). A second space after `origin` still
  completes the allow, so the Git
  Manager frontmatter must repeat every other protected denial
  (gh api, pull-request merges, pushes to `main`, the double-space rules
  `git push origin  *` and `rtk git push origin  *`, option-bearing and
  `+`/` :`-refspec pushes, and the sensitive-path shell block) after its
  allow rules, and no write allow may follow those denials. Consequently the
  Git Manager pushes `git push origin <branch>` or `git push origin HEAD` —
  remote and refspec separated by a single space, refspec non-empty, never
  with a `-u` upstream option, never option-bearing, never with a second
  space after the remote, never to another
  remote, never remote-only.
- Permission rules are resolved with last-match-wins semantics. The check
  computes the combined rule set for every agent over a sample table that
  covers the read-only commands and their RTK mirrors, the Go quality tools and
  their filtered runs, the ask rules, the credential-path denials in file and
  shell form, the compound/hidden-write denials, the push-to-main and
  double-space-push denials and
  the Git Manager's write commands, including explicit `git push origin
  <feature-branch>` pushes without any option.
  Compound samples are split on the top-level separators `&&`, `||`, `;`, `|`
  and newlines and each subcommand is resolved on its own — any deny denies
  the sample, otherwise any ask asks — mirroring OpenCode's scanner-based
  shell permission model (see
  [`opencode-v2.4.1-discovery.md`](opencode-v2.4.1-discovery.md)). It rejects
  broad allow rules and allow rules added after a deny, rather than only
  looking for permission strings.
- `AGENTS.md` points to the feedback contract, documents the ADR baseline, the
  credential rules, the `.tmp/` scratch convention and the RTK usage rules.
- The feedback contract contains every required report field, including the
  `model`, `provider`, `reviewed_artifact` provenance/artifact fields, the
  optional `thinking` field and the structured `check_state` evidence rules.

### Permission fixtures

The fixture in `docs/validation/fixtures/permissions/` contains a Planner
definition with an `action: "*"` allow rule (`resource: "git notes*"`,
`effect: allow`) that must be rejected, and a compliant Reviewer definition
that must pass the agent policy check.

### ADR baseline

The fixture in `docs/validation/fixtures/adr/` contains:

- a merged baseline ADR with `status: Accepted`;
- an open pull-request ADR that declares `status: Accepted` and conflicts with
  the baseline.

The validator confirms that the open pull-request ADR has the effective status
`Proposed`, does not enter the baseline, and produces an escalation for the
conflict. It also validates the ADR links of an open proposal — `supersedes`,
`superseded-by` and `conflicts-with` — against every known ADR (merged records
of any status plus open proposals), rejects a proposal identifier that collides
with a merged ADR that is not accepted, and rejects conflicts that reference a
merged ADR that is not accepted. The signature that detects an unchanged ADR on
the default branch includes a SHA-256 of the record body.

An additional combined fixture in
`docs/validation/fixtures/adr/combined/` models the real post-merge layout:
the merged baseline carries the accepted ADR-0001 requirements baseline and
the accepted ADR-0003 bootstrap, while the open pull request adds ADR-0002
and a changed ADR-0003 that reuses the merged identifier. The check asserts
that the baseline contains both merged records, that the added and changed
records stay effective proposals while the pull request is open, and that a
proposal that conflicts with the accepted merged bootstrap still escalates a
conflict against it.

An additional in-memory ADR fixture builds records in code (no repository
files) and asserts the same guarantees: the signature stays stable for an
unchanged body and changes when the body changes, an unknown `superseded-by`
reference is rejected, an open-pull-request identifier collision with a merged
non-accepted ADR is rejected, a conflict against a merged non-accepted ADR
raises the non-accepted-conflict error, and declared `Accepted`, `Rejected`
and `Superseded` statuses in an open pull request map to an effective
`Proposed` while `In Review` stays `In Review`.

### Feedback reconciliation

The fixture in `docs/validation/fixtures/workflow/` contains seven synthetic
acceptance criteria and three synthetic reports. It deliberately includes:

- **AC-03**, delegated to the Planner but omitted from the Planner report;
- **AC-07**, never delegated to an agent;
- **AC-05**, reported as `unverified`;
- **AC-06**, delegated to the Orchestrator without a report;
- **ADR-0002**, declared `Accepted` in an open pull request, conflicting with the
  accepted baseline;
- a Reviewer report with status `Needs Decision`.

The validator builds the coverage ledger and asserts the **exact** expected gap
and escalation sets — not only that the expected entries are included — so a
new, unexpected gap or escalation fails the fixture.

Beyond the ledger shape, reconciliation now enforces report quality rules:

- the report's `issue` and `task_id` must match the issue and the task the
  scenario declares for its agent (the scenario `tasks` mapping; an agent may
  be declared several `task_id` values as a list for re-done tasks);
- a `covered` claim needs evidence that survives filtering: an evidence
  entry is treated as absent when it is empty or whitespace, or
  case-insensitively equal to a vacuous sentinel (`none`, `n/a`, `n.a.`,
  `na`, `-`, `--`, `tbd`, `no evidence`, `none.`), and a `covered` claim
  whose evidence list is empty after filtering is unsupported, dropped from
  the status computation and left with the `follow_up` gap — so
  `evidence: ["none"]` cannot masquerade as the contract's explicit
  "no content" sentinel;
- a `not_applicable` claim needs a non-empty note explaining why;
- contradictory supported coverage values demote the criterion to `unverified`
  and surface an explicit `disagreement:<values>` gap instead of letting
  `covered` win, and an unvalidated caller cannot smuggle a covered status in:
  `reconcile` itself recomputes support;
- a `covered` claim counts only when the reporting agent is delegated the
  criterion, the report was produced against the scenario `artifact`, and every
  structured evidence item names an `artifact` and records
  `check_state: passed`. An absent state is not green: the criterion-prefixed
  gap `AC-04:evidence:missing:<agent>` is recorded and the row stays open. A
  structured item's `criterion_id` or `task_id`, when present, must agree with
  its coverage entry and the report task; `validate_report` rejects a
  disagreement and `reconcile` relies on that validation instead of repeating
  it. Stale evidence adds `stale_artifact:<agent>`, an undelegated claim adds
  `wrong_criterion_assignment:<agent>`, and a non-`passed` state adds
  `evidence:<state>:<agent>`; the row stays open with `follow_up`;
- an `evidence:<state>:<agent>` gap also attaches to a row that was already
  non-covered: a legitimate `unverified` row whose structured evidence records
  `check_state: skipped` gains `AC-01:evidence:skipped:implementer` next to its
  own status gap. That is deliberate, not a contradiction — the gap records
  what the evidence said, separately from why the claim failed, and it is read
  as the justification that keeps the row open; the evaluator does not split
  the two into different fields;
- the ledger's `evidence` list renders structured items as
  `<artifact> [<check_state>]` (an absent state renders as `missing`) instead
  of dropping them in a string-only filter, so the reconciliation view keeps
  the artifact and check state next to each string entry;
- a newer report may supersede an older report's task via a `supersedes`
  list of task ids, and the supersession is validated: every entry must name
  a task the scenario declares for the same agent — unknown targets,
  targets of other agents, a report superseding its own task and a cyclic
  chain (A supersedes B while B supersedes A) are rejected instead of being
  silently tolerated — and the superseded report then stops participating in
  reconciliation.

The report-level checks also require `model`, `provider` and
`reviewed_artifact` as non-empty strings and allow an explicit `unknown`
sentinel; a missing or blank value is rejected. `thinking` is optional and,
when present, must be a non-empty string or object.

The invalid fixture suite under `docs/validation/fixtures/workflow/invalid/`
runs one scenario per case and requires each rule to fail or reconcile
exactly as stated: `wrong-issue`, `wrong-task`, `missing-model-provenance`,
`blank-model-provenance`, `covered-without-evidence`,
`covered-with-sentinel-evidence`, `evidence-without-artifact`,
`missing-check-state`, `not-applicable-without-note`,
`conflicting-reports`, `explicit-missing`, `stale-verification`,
`blocked-evidence`, `wrong-criterion-assignment`, `supersedes-drops-report`,
`supersedes-cross-agent` and `supersedes-unknown-task`. Each reconciling case
asserts the exact ledger, gap, escalation and blocker sets, not only that the
named entry is present. An in-memory reconciliation fixture pins the
defence-in-depth rules in code: an empty-evidence `covered` claim cannot
produce a covered ledger row, contradictory coverage values demote to
`unverified`, blank provenance is rejected while an explicit `unknown`
sentinel validates, and self- or cyclic supersession is rejected at the report
level.

### Release gate and release fixtures

`evaluate_release_gate()` returns one `release_ready` boolean and the exact
sorted blocker list. It requires the committed plan review, the independent AI
code review, the named-human code review, the Tester verification, the
inspected workflow-validator CI run, current applicable evidence for every
required criterion, no reconciled gaps or disagreements, no record-declared
`gaps`, no `decision_needed`, no pending effective proposal, no open required
decision and exact PR-head agreement across the evidence, with the record's
`artifact` equal to `pr_head`. `pr_head` and `artifact` must each be a full
40-hex commit identity (`^[0-9a-f]{40}$`); a malformed value is
`pr_head:invalid` or `artifact:invalid`, so the equality is never equality over
free text. Unknown top-level keys are rejected as
`release-record:unknown-key:<key>`, so a record cannot declare a binding the
evaluator ignores. Only the top level is a closed key set: the nesting inside a
known slot is open, so an unrecognised nested key such as
`plan_review.frozen_diff`, `human_review.ai_identity` or
`workflow_validator_ci.frozen_diff` is accepted and ignored, and it binds
nothing the evaluator reads. Only the exact check-state taxonomy `passed`,
`failed`, `skipped`, `unavailable`, `contributor-reported` is accepted; only
`passed` is green, CI additionally requires `inspected: true`, and a failed,
skipped, unavailable or contributor-reported required check stays a blocker.

The Orchestrator owns the live release record
(`docs/workflow/ledgers/issue-30.release.json` for issue #30). It is a JSON
object with these keys:

```json
{
  "issue": 30,
  "pr_head": "<40-hex final head>",
  "artifact": "<handover commit: 40-hex, identical to pr_head>",
  "tasks": {"<agent>": "<task-id>"},
  "criteria": [{"id": "AC-01", "title": "…", "delegated_to": ["…"], "required": true}],
  "reports": ["<feedback-contract report objects>"],
  "plan_review": {"state": "passed", "commit": "e881bb1", "section_sha256": "474f2c07…"},
  "ai_code_review": {"state": "passed", "reviewer_type": "ai", "reviewer": "reviewer", "head": "…"},
  "human_review": {
    "state": "passed", "reviewer_type": "human", "name": "…", "login": "…",
    "attribution": "human", "independent": true, "provenance": "pr-review",
    "review_id": "…", "timestamp": "…", "head": "…"
  },
  "tester_verification": {"state": "passed", "head": "…"},
  "workflow_validator_ci": {
    "state": "passed", "inspected": true, "head": "…", "base_sha": "…",
    "continue_on_error": false, "job": "workflow-validator", "run": "…"
  },
  "decisions": [{"id": "OD-ROLE", "required": true, "state": "resolved",
                 "resolved_by": "…", "rationale": "…", "reference": "…", "head": "…"}],
  "proposals": [{"id": "ADR-0002", "declared_status": "Accepted", "effective_status": "Proposed"}],
  "gaps": []
}
```

A resolved required decision needs a non-AI `resolved_by`, a rationale, a
reference and the final head. A proposal blocks while its
`effective_status` is not `Accepted`. The record's `artifact` is the reviewed
artefact and must be the handover commit: a full 40-hex commit identity
identical to `pr_head` and validated by the same shape rule. There is no
frozen-diff form in the record, a missing or malformed value blocks, and there
is no fallback from `artifact` to `pr_head`. A round reviewed as a working-tree
diff is intermediate: once the Git Manager commits it, the identity over the
working tree is replaced by the identity over the diff against the base commit
(`git diff <base_sha> <head>`) and `artifact`, `pr_head`, the slot heads and
every report's `reviewed_artifact` are re-bound together before `release_ready`
can be true. Unknown top-level keys are rejected by name rather than ignored:
the key set is closed so schema evolution is a conscious validator change, and
a record such as the Tester's `artifact_kind`/`frozen_diff` shape fails instead
of appearing to declare a binding the evaluator never read. The required CI
`base_sha` must match `^[0-9a-f]{7,40}$`. The human slot's `name` and `login`
must differ from each other and from every AI identity recorded in the same
record, including the AI review slot's reviewer/model value; comparison is
literal after lowercase normalisation, so capitalisation cannot bypass it while
separator differences are not normalised, and independence beyond the recorded
identity remains attested human judgement.

The release fixtures under
`docs/validation/fixtures/workflow/invalid-release/` start from an in-memory
all-green control and patch one field. Each case asserts `release_ready: false`
and the exact blocker set: `missing-required-gate`, `unresolved-decision`,
`contributor-reported-required-check`, `missing-ai-review`,
`missing-human-review`, `pending-proposal`, `ai-identity-human-slot`,
`missing-human-provenance`, `skipped-required-check`,
`uninspected-required-check`, `stale-plan-review` and `head-mismatch`. A
dedicated in-memory fixture adds 52 mutations that remove or corrupt one guard
at a time, so a removed guard makes its case pass and fails the suite. The
harness names every guard it proves: plan-review presence, state, commit and
section hash; AI-review presence, type and head; human-slot presence, identity,
attribution, independence, timestamp, head, name/login distinctness and
cross-slot AI-identity reuse; decision-resolution identity against both the
static agent names and the AI identities recorded in the same record; Tester
presence, state and head mismatch; CI
presence, state, inspection, head mismatch, base-SHA shape, job, run and
continue-on-error; every slot's `invalid-state` rejection; criterion coverage;
the `gap:`, `gaps:present`, `release-gap:` and `escalation:` reporting lines;
stale artifact; disagreement; report `decision_needed` and pending proposal;
release proposal; open decision; decision-resolution identity (static and
recorded AI); PR head and
artifact commit-shape validation; the relabelled-frozen-diff shape; record
artifact presence and head equality; and the unknown-top-level-key rejection.
The absent-`check_state` gap and the structured-artifact rejection are proven
by their report fixtures.

Reviewed only, not mutation-proven: `pr_head:missing`, `criteria:missing`,
`decision-resolution:*:{rationale,reference,head}`, `human_review:{not-human,
missing-identity}`, `reports:missing`, `reports:invalid:<error>`,
`criteria:invalid`, `gaps:invalid`, `decisions:invalid`, `proposals:invalid`,
`proposal:invalid:<value>` and `decision:invalid:<value>`. None of these
branches has its own mutation: the suite would still pass with the branch
removed, so this paragraph records review coverage only, not proof. It is the
list of branches reviewed without a mutation case, not a claim that every
unproven branch is named. The synthetic all-green control proves the evaluator
only; it is never live release evidence and never changes the `all` result for
a real record.

### CI workflow contract

`check_ci_workflow_contract()` asserts the shape of the `workflow-validator`
job in `.github/workflows/ci.yml` and checks each named guard with a mutation.
The positive control is the real workflow file; a mutation that no longer
matches the file fails the run instead of passing vacuously. The contract
checks the YAML shape:

- the job exists, is gated to `github.event_name == 'pull_request'` and carries
  a timeout;
- the checkout pins `actions/checkout` to a 40-hex commit, uses
  `fetch-depth: 0` and `persist-credentials: false`, and names the exact
  pull-request head `ref` and `repository`;
- the base is recorded as an explicit commit identity (`EXPECTED_BASE_SHA`,
  `^[0-9a-f]{7,40}$`, never a branch name), the expected head is the
  pull-request head commit, the base branch is fetched from the base
  repository (`BASE_REPOSITORY`) into `refs/remotes/origin/main`, and the
  assertion step resolves `origin/main`, prints expected versus actual base and
  head, compares the head and the base, checks that the base is an ancestor of
  the head and exits non-zero on mismatch; the guard proves that an `if`
  referencing `EXPECTED_*` exists and that an `exit 1` line exists, not that
  every comparison exits non-zero;
- the trusted commands run in order as executed command lines, not comments:
  `python3 tools/audit_validator.py` before
  `python3 tools/workflow_check.py ci`; `all` never runs in the job, and the
  job carries no `continue-on-error` and no shell soft-fail.

The job keeps the workflow's top-level `contents: read` permission; the
contract check does not assert that, it is part of the workflow review.

Thirty-one in-memory mutations remove or corrupt one guard each and fail with
their named `ci-contract:*` blocker: the job, the event gate, the timeout, the
checkout step and its pin, the full-history setting, persisted credentials, the
exact head ref and repository, the base repository, the recorded base (removed,
or pinned to a branch name), the base fetch and its refspec, resolution,
ancestry, comparisons, prints and non-zero exits, the audit and trusted
commands and their order, the `all` substitution, a `|| true` soft-fail and
`continue-on-error`. A scratch guard-removal run proves all 27 named guards
load-bearing at that shape level: removing one guard in a copy of the validator
makes its own case fail. The compare guards prove only the `if`/`exit 1` shape:
removing just one compare's `exit 1`, or inverting `!=` to `==`, still passes.

The contract is static. It proves the YAML shape only; it never proves that a
run passed, and `jactionlint` only checks the workflow syntax. Binding a release
to CI still needs the actual run, job, step and log evidence on the reviewed
head, and the record's `workflow_validator_ci` slot additionally needs
`inspected: true` and `continue_on_error: false`.

### Right-sized work items

`check_right_sized_work_item_fixture()` loads
`docs/validation/fixtures/workflow/planning/right-sized.json` and requires all
nine AC-PL1 factors (cohesion, dependencies, complexity, architectural impact,
side effects, testability, agent context, coordination overhead and AI/human
review effort), an independently verifiable outcome and a named-human approval
for a material scope change. Twenty in-memory mutations remove each factor,
remove or falsify independent verification, remove the outcome, remove the
approval and its human identity and reference, and add a rigid `max_files` or
`max_lines` threshold; each mutation fails with its named `right-sized:*`
blocker. No count of criteria, files or lines is a rule. Whether a split is
cohesive or a change is material remains Planner and human judgement.

### Delegation packet

`docs/workflow/delegation-packet.md` is the normative packet definition. The
workflow document and `AGENTS.md` link to it; the workflow
`## Delegation packet` section is a link only, and the check rejects any of the
six verbatim pre-canonical rule bullets reappearing in that section; a
paraphrased rule is review-covered, not detected.
`validate_delegation_packet()` requires task identity, issue and agent,
criteria, the accepted ADR baseline and proposals, repository context,
dependencies, constraints, expected evidence, `reviewed_artifact` and
a write-ownership record whose agent and task match the packet. It runs the
ownership guard on that record, so a packet cannot delegate a write to a
read-only role. Twenty-three mutations remove each field, empty the criteria,
corrupt a criterion and the ADR baseline, blank the artefact, mismatch the
owner and re-add a duplicated rule or drop a canonical marker or link; each
fails with its named `packet:*` or `delegation-packet:*` blocker. Concision,
context sufficiency and actually requesting missing context are instruction and
human-judgement rules, not validator-proven.

### Write ownership

`validate_write_ownership()` checks the recorded single-writer protocol against
the active task list. The fixtures under
`docs/validation/fixtures/workflow/ownership/` cover disjoint writes (pass),
overlapping writes (fail), an explicit handover (pass), stale ownership (fail)
and a read-only role claiming a write (fail). Fifteen in-memory mutations start
from the disjoint control and add an overlap, remove a handover, point a
handover at an unknown target, keep a closed task active, give a read-only or
wrong-role agent a write, use a shared scratch directory, and corrupt the
agent, status, dependencies, active list and record list; each fails with its
named `write-ownership:*` blocker. The check enforces `.tmp/<task-id>/` scratch
and the role scopes: the Orchestrator writes only the ledger, the Planner only
ADR proposals, the Implementer not those two, the Reviewer and Tester nothing
and the Git Manager no repository file. Actual write obedience and filesystem
isolation are instruction-only limits; the validator checks records and
synthetic cases only.

Across the three sections above, a scratch guard-removal run proves each of
the 19 named guards load-bearing: removing one guard in a copy of the validator
makes its own case fail, and restoring it makes the suite pass again. The
mutation table is recorded in the implementation report. The separate
`.tmp`-in-`write_scope` branch — a write scope naming another task's `.tmp/`
path — has no mutation and is reviewed-only; it is not counted among the 19.

## Expected result

The `ci` output below is abridged; the full run also prints the fixture
ledger, the negative fixture cases and the actual-repository ADR section.
The verbatim capture in
[`workflow-check-output.txt`](workflow-check-output.txt) is the exact stdout of
`python3 tools/workflow_check.py ci` at capture time: 88 lines, 8,041 bytes,
SHA-256
`a757c97e63d782aebf16a0b299f1d27e13fc1d071884b08ebef4332d5ac7e5c2`,
exit code 0, no network access and no credentials. It is an illustrative
snapshot of the current ref state — local `main` stale with respect to
`origin/main` (`73dbbec` vs `17cf55a`), and `origin/main` carrying no
`ADR-*.md` record, so the live-tree ADR step prints a `SKIP` line. Its ref
names, SHAs and live-tree lines change as the branch and refs move; regenerate
that file after your own run and do not treat its line values as current. Two
consecutive `ci` runs produce byte-identical stdout and stderr.

```text
PASS audit: workflow_check.py passed 6 static properties (imports and wildcard rejection, network modules, forbidden calls and spawn references, subprocess shape and verb pin, git verb pin, write access) across 11 imports, 1812 call sites, 1 subprocess sites and 3 git verbs
PASS config: six agents, resolved permission boundaries, shared instructions, Git ownership and human-only merge are consistent
PASS adr: open pull-request ADRs remain proposals and do not change the baseline
PASS adr in-memory fixtures: body-signature stability, unknown references, identifier collisions, non-accepted conflicts and open pull-request status mapping are enforced
PASS permissions fixtures: over-broad allow rules are rejected and compliant agent rules pass
PASS ledger structure in-memory fixtures: the well-formed control passes, a five-cell row names its line and both counts, the recorded edit payloads, the tool-call tail and the literal \n| escape fail, and missing, duplicated and out-of-order sections are rejected
PASS reports in-memory fixtures: empty and sentinel-evidence covered claims stay unsupported, structured evidence identity is enforced, contradictory coverage values demote to unverified, unknown provenance is accepted while blank provenance is rejected, and self-, cross-agent, unknown and cyclic supersession is rejected
PASS release gate in-memory fixtures: the synthetic all-green control evaluates true and 52 mutations each force false with their named blocker; this proves the evaluator only, never real release readiness
PASS release negative fixtures: 12 expected-false release cases assert the exact blockers inside the fixture harness
PASS right-sized work item fixture: nine factors, an independently verifiable outcome and named-human approval for material scope changes are required; 20 mutations each fail their case and no rigid size threshold is encoded
PASS delegation packet fixture: the canonical document carries every required field, the workflow and AGENTS.md link to it, and 23 mutations each fail their case; concision and context sufficiency remain human judgement
PASS write ownership fixtures: 5 cases cover disjoint, overlapping, handover, stale and read-only ownership, and 15 in-memory mutations each fail their case with the named blocker; write obedience and filesystem isolation remain instruction-only
PASS ci workflow contract: the workflow-validator job checks out the exact pull-request head, enforces the recorded explicit base and runs the trusted commands, and 31 mutations each fail their named case; the static contract proves the YAML shape only, never a passing run
PASS reports: synthetic reports reconcile with the exact expected gaps and escalations
PASS reports negative fixtures: 17 invalid report cases fail or reconcile exactly as stated
PASS plan identity: reviewed section of docs/workflow/ledgers/issue-30.md at e881bb1 matches sha256 474f2c07a443ea74bf3fb144db52f2a0b67af466c401f9f28e3526163e4f2ce1 (23784 bytes)
PASS ledger structure: 8 sections in order; 3 required tables (6/5/4 columns) with 246 data rows; 17 table blocks self-consistent; 4 forbidden payload shapes absent
SKIP adr (live tree): the resolved baseline ref 'origin/main' contains no ADR-*.md record under docs/adr; merged-baseline handling is asserted only by the fixtures
All workflow checks passed.
```

The final `all` mode adds the live release record and is expected to exit
non-zero while that record is missing or incomplete. With the record absent it
prints:

```text
Live release record: docs/workflow/ledgers/issue-30.release.json
UNAVAILABLE release record: docs/workflow/ledgers/issue-30.release.json is missing
Release gate: release_ready=false
Blockers:
  - release-record:unavailable:missing
FAIL: release_ready is false
```

A `release_ready=true` result requires the complete live evidence on the exact
final head; a false result is the correct fail-closed result until then.

The `SKIP adr (live tree)` line is the live-tree step of the illustrative
snapshot described above: with a baseline ref that carries no `ADR-*.md` record
the run prints this non-asserting `SKIP` line instead of a `PASS adr` line;
with an `ADR-*.md`-carrying ref it prints the resolved baseline, the proposal
lines and `PASS adr: open pull-request ADRs remain proposals and do not change
the baseline` instead.

## Scope and limitations

- The validator is offline and deterministic. It does not call OpenCode models,
  providers or GitHub. The actual-ADR check needs a local git ref for `main` or
  `origin/main`; without one it skips that section and still runs the fixture.
- It checks the configuration and reconciliation rules; it does not replace the
  live discovery check recorded in
  [`opencode-v2.4.1-discovery.md`](opencode-v2.4.1-discovery.md).
- The fixtures are synthetic and contain no credentials, private account
  settings or agent content from a real project.
- The CI workflow contract is static: it asserts the YAML shape of
  `.github/workflows/ci.yml` and its named guards, not that a GitHub Actions
  run passed. `jactionlint` checks the workflow syntax only. CI `passed`
  evidence must be read from an actual run, job, step and log on the reviewed
  head, so the contract check never fills the release record's CI slot.
- The `workflow-validator` job checks the head out with
  `persist-credentials: false` and fetches the base branch anonymously from
  the base repository URL. That is a credential-free read of this public
  repository; a private repository would need a different credential-free
  path, and the job would fail closed rather than skip the assertion.
- The synthetic all-green release control proves the evaluator only. It is
  never live release evidence and never changes the `all` result for the real
  record. Genuine human independence, the truth of a recorded model/provider
  identity and the absence of reasoning traces remain attested human or
  reviewer judgement; the validator checks the recorded evidence fields, not
  the person behind them.
- The validator self-audit reads the validator source as an AST and bounds
  constructs. It is a guardrail, not a sandbox: it cannot prove runtime
  behaviour, and a reviewer still owns the judgement about what the validator
  may be trusted with.
