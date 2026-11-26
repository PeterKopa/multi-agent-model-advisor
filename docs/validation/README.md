# Workflow validation

The workflow has an offline validator that checks configuration, ADR baseline
handling and feedback reconciliation without network access or credentials.

## Run

From the repository root:

```bash
python3 tools/workflow_check.py all
```

Individual checks:

```bash
python3 tools/workflow_check.py config
python3 tools/workflow_check.py adr
python3 tools/workflow_check.py reports
python3 tools/workflow_check.py fixtures
```

`adr` runs only the actual-repository check: it compares the ADRs merged into
the resolved baseline ref with the ADRs in the current working tree. The
fixture scenarios only run under `fixtures` and `all`.

Which ADRs are recorded as merged depends on the state of `main` and
`origin/main`: the validator resolves `main` first, falls back to
`origin/main`, skips the section with a deterministic message when neither ref
exists, and prints the resolved baseline, the open proposals and any
escalations. While a workflow change is in an open pull request, its ADRs
therefore appear as proposals even when their frontmatter declares `Accepted`.

## What is checked

### Configuration

- `opencode.jsonc` selects the Orchestrator, loads the shared feedback contract
  and resolves the ordered permission policy with last-match-wins semantics:
  Git and GitHub are denied by default in plain and RTK form, read-only
  inspection is re-enabled in both forms, `gh api*` and `gh pr merge*` stay
  denied, pushes to `main` are denied, `docker`/`kubectl`/`oc`/`aws`/`psql`/
  `wget` and their RTK mirrors ask, `pnpm`/`dotnet` and their RTK mirrors are
  denied, credential and secret locations are denied for `read`, `edit`,
  `external_directory` and inside shell command strings, every `*.env` /
  `.env.*` file except `.env.example` is denied, `~/.config/opencode/*` is
  read and edited on approval only, the `external_directory` gate asks for
  anything outside the worktree, and the Go quality tools (`go`, `govulncheck`,
  `golangci-lint`, `jactionlint`) are allowed directly and through the narrow
  `rtk test` filters while the wrapper rules `rtk test`/`rtk err`/
  `rtk summary` stay denied and `rtk bypass`/`rtk proxy` ask.
- `.opencode/agents/` contains exactly the six workflow agents (no extra files),
  each with a required `mode`, description and prompt.
- Agent rules are validated against the role policy: no `action: "*"` allow
  rule anywhere, and outside the Git Manager no allow rule for any action other
  than `edit` and `subagent`. Agents may only deny or ask; allow rules outside
  those two actions are reserved for the Git Manager's write role.
- The Orchestrator can launch exactly the five specialist agents and can write
  only under `docs/workflow/ledgers/`.
- The Planner can draft ADRs, while the Reviewer, Tester and Git Manager have
  the edit, write and patch tools denied; shell commands remain
  permission-controlled.
- The Git Manager has the explicit Git and GitHub write allow rules — including
  the RTK write mirrors `rtk git add/branch/checkout/commit/push/switch` and
  `rtk gh pr create` — and the other agents do not. `gh pr merge` and `gh api`
  are denied for every agent, including the Git Manager. The Git Manager
  frontmatter must repeat every protected denial (gh api, pull-request merges,
  pushes to `main`, the sensitive-path shell block) after its allow rules, and
  no write allow may follow those denials.
- Permission rules are resolved with last-match-wins semantics. The check
  computes the combined rule set for every agent over a sample table that
  covers the read-only commands and their RTK mirrors, the Go quality tools and
  their filtered runs, the ask rules, the credential-path denials in file and
  shell form, the compound/hidden-write denials, the push-to-main denials and
  the Git Manager's write commands including `git push` to a feature branch. It
  rejects broad allow rules and allow rules added after a deny, rather than
  only looking for permission strings.
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

## Expected result

The output below is abridged; the full run also prints the fixture ledger and
the actual-repository ADR section. A verbatim run is committed in
[`workflow-check-output.txt`](workflow-check-output.txt).

```text
PASS config: six agents, resolved permission boundaries, shared instructions, Git ownership and human-only merge are consistent
PASS adr: open pull-request ADRs remain proposals and do not change the baseline
PASS permissions fixtures: over-broad allow rules are rejected and compliant agent rules pass
PASS reports: synthetic reports reconcile with the exact expected gaps and escalations
PASS adr: open pull-request ADRs remain proposals and do not change the baseline
All workflow checks passed.
```

## Scope and limitations

- The validator is offline and deterministic. It does not call OpenCode models,
  providers or GitHub. The actual-ADR check needs a local git ref for `main` or
  `origin/main`; without one it skips that section and still runs the fixture.
- It checks the configuration and reconciliation rules; it does not replace the
  live discovery check recorded in
  [`opencode-v2.4.1-discovery.md`](opencode-v2.4.1-discovery.md).
- The fixtures are synthetic and contain no credentials, private account
  settings or agent content from a real project.
