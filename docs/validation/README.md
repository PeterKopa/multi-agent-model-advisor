# Workflow validation

The workflow has an offline validator that checks configuration, ADR baseline
handling and feedback reconciliation without network access or credentials.

## Run

Run the static audit of the validator first, then the validator itself. From
the repository root:

```bash
python3 tools/audit_validator.py
python3 tools/workflow_check.py all
```

`all` includes the audit as its first step: the validator imports the sibling
auditor, statically bounds its own source before any result is printed, and
fails fast when the audit finds anything outside the audited boundary. Run
`python3 tools/audit_validator.py` directly when only the audit gate is
needed. The audit is honest about its limit: it is an AST audit that bounds
constructs — a guardrail, not a sandbox.

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
scenario (`fixtures/workflow/scenario.json`) plus the ten invalid-report cases
in `fixtures/workflow/invalid/` — the negative suite is deliberately invoked
from inside `check_reports`, so even a diagnostic `reports` run certifies the
positive and the negative reconciliation behaviour together and cannot pass
only one half of it; `fixtures` runs every fixture file (the ADR,
combined-ADR, in-memory ADR, permissions and in-memory reconciliation cases,
plus the `reports` section above); `config` and the fixture-driven parts of
`all` run what `reports` and `fixtures` run.

`all` is the trusted entry point: it is the only command that runs the
self-audit first. `config`, `adr`, `reports` and `fixtures` are diagnostics
that execute individual sections only and do not run the audit, so their
results are not certified; use them to inspect one section, and use `all` to
produce a trusted run.

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
- The feedback contract contains every required report field.

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
- contradictory coverage values across agents keep the status rule but surface
  an explicit `disagreement:<values>` gap, and an unvalidated caller cannot
  smuggle a covered status in: `reconcile` itself recomputes support;
- a newer report may supersede an older report's task via a `supersedes`
  list of task ids, and the supersession is validated: every entry must name
  a task the scenario declares for the same agent — unknown targets,
  targets of other agents, a report superseding its own task and a cyclic
  chain (A supersedes B while B supersedes A) are rejected instead of being
  silently tolerated — and the superseded report then stops participating in
  reconciliation.

The invalid fixture suite under `docs/validation/fixtures/workflow/invalid/`
runs one scenario per case and requires each rule to fail or reconcile
exactly as stated: `wrong-issue`, `wrong-task`, `covered-without-evidence`,
`covered-with-sentinel-evidence`, `not-applicable-without-note`,
`conflicting-reports`, `explicit-missing`, `supersedes-drops-report`,
`supersedes-cross-agent` and `supersedes-unknown-task`. An in-memory
reconciliation fixture pins the defence-in-depth rules in code: an
empty-evidence `covered` claim cannot produce a covered ledger row,
contradictory coverage values surface as a disagreement gap without
discarding a valid covered entry, and self- or cyclic supersession is
rejected at the report level.

## Expected result

The `all` output below is abridged; the full run also prints the fixture
ledger, the negative fixture cases and the actual-repository ADR section.
The verbatim capture in
[`workflow-check-output.txt`](workflow-check-output.txt) is an illustrative
snapshot of the current ref state at capture time — local `main` stale with
respect to `origin/main`, and `origin/main` carrying no `ADR-*.md` record, so
the live-tree ADR step prints a `SKIP` line. Its ref names, SHAs and live-tree
lines change as the branch and refs move; regenerate that file after your own
run and do not treat its line values as current.

```text
PASS audit: workflow_check.py passed 6 static properties (imports and wildcard rejection, network modules, forbidden calls and spawn references, subprocess shape and verb pin, git verb pin, write access) across 11 imports, 657 call sites, 1 subprocess sites and 3 git verbs
PASS config: six agents, resolved permission boundaries, shared instructions, Git ownership and human-only merge are consistent
PASS adr: open pull-request ADRs remain proposals and do not change the baseline
PASS adr in-memory fixtures: body-signature stability, unknown references, identifier collisions, non-accepted conflicts and open pull-request status mapping are enforced
PASS permissions fixtures: over-broad allow rules are rejected and compliant agent rules pass
PASS reports in-memory fixtures: empty and sentinel-evidence covered claims stay unsupported, contradictory coverage values surface as disagreement, and self-, cross-agent, unknown and cyclic supersession is rejected
PASS reports: synthetic reports reconcile with the exact expected gaps and escalations
PASS reports negative fixtures: 10 invalid report cases fail or reconcile exactly as stated
SKIP adr (live tree): the resolved baseline ref 'origin/main' contains no ADR-*.md record under docs/adr; merged-baseline handling is asserted only by the fixtures
All workflow checks passed.
```

The penultimate line is the live-tree step of the illustrative snapshot
described above: with a baseline ref that carries no `ADR-*.md` record the
run prints this non-asserting `SKIP` line instead of a `PASS adr` line; with
an `ADR-*.md`-carrying ref it prints the resolved baseline, the proposal
lines and `PASS adr: open pull-request ADRs remain proposals and do not
change the baseline` instead.

## Scope and limitations

- The validator is offline and deterministic. It does not call OpenCode models,
  providers or GitHub. The actual-ADR check needs a local git ref for `main` or
  `origin/main`; without one it skips that section and still runs the fixture.
- It checks the configuration and reconciliation rules; it does not replace the
  live discovery check recorded in
  [`opencode-v2.4.1-discovery.md`](opencode-v2.4.1-discovery.md).
- The fixtures are synthetic and contain no credentials, private account
  settings or agent content from a real project.
- The validator self-audit reads the validator source as an AST and bounds
  constructs. It is a guardrail, not a sandbox: it cannot prove runtime
  behaviour, and a reviewer still owns the judgement about what the validator
  may be trusted with.
