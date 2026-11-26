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

`adr` compares the accepted ADRs merged into `main` with the ADRs in the current
working tree. While a workflow change is in an open pull request, its ADRs
therefore appear as proposals even when their frontmatter declares `Accepted`.

## What is checked

### Configuration

- `opencode.jsonc` selects the Orchestrator, loads the shared feedback contract,
  denies Git and GitHub commands by default, re-enables read-only inspection and
  reserves write operations for the Git Manager.
- `.opencode/agents/` contains the Orchestrator and the five specialist
  subagents with the expected modes, descriptions and prompts.
- The Orchestrator can launch exactly the five specialist agents and can write
  only under `docs/workflow/ledgers/`.
- The Planner can draft ADRs, while the Reviewer, Tester and Git Manager have
  the edit, write and patch tools denied; shell commands remain
  permission-controlled.
- The Git Manager has the explicit Git and GitHub write allow rules, and the
  other agents do not. `gh pr merge` is denied for every agent: merging a pull
  request is reserved for the human user.
- Permission rules are resolved with last-match-wins semantics. The check
  rejects shell allow rules in non-Git-Manager agents, derives write-command
  samples from the Git Manager's own allow rules and exercises representative
  commands. It catches broad allow rules and allow rules added after a deny,
  rather than only looking for permission strings.
- `AGENTS.md` points to the feedback contract and the ADR baseline.
- The feedback contract contains every required report field.

### ADR baseline

The fixture in `docs/validation/fixtures/adr/` contains:

- a merged baseline ADR with `status: Accepted`;
- an open pull-request ADR that declares `status: Accepted` and conflicts with
  the baseline.

The validator confirms that the open pull-request ADR has the effective status
`Proposed`, does not enter the baseline, and produces an escalation for the
conflict. The actual repository is checked against `main`, falling back to
`origin/main`; when neither ref exists, that section is skipped with a
deterministic message and the fixture continues to validate the policy.

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

The validator builds the coverage ledger, records the delegation and report
gaps, creates follow-up entries for every non-covered criterion and lists the
architecture escalations.

## Expected result

The output below is abridged; the full run also prints the fixture ledger and
the actual-repository ADR section. A verbatim run is committed in
[`workflow-check-output.txt`](workflow-check-output.txt).

```text
PASS config: six agents, resolved permission boundaries, shared instructions, Git ownership and human-only merge are consistent
PASS adr: open pull-request ADRs remain proposals and do not change the baseline
PASS reports: synthetic reports reconcile with gaps and escalations as expected
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
