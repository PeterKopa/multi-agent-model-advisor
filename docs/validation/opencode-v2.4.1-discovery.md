# OpenCode v2.4.1 discovery record

This record documents the project-specific agent discovery and shared
instruction loading for the workflow. The check was first run on 2026-11-26
from the repository root of the workflow branch and was re-validated after the
permission policy was extended (credential-path denials, RTK mirroring,
external-path approval, Go quality-toolchain allows); see the "Permission
resolution" section below for the extended picture and
[`workflow-check-output.txt`](workflow-check-output.txt) for the recorded
validator output.

## Version

```console
$ opencode --version
opencode v2.4.1
```

## Configuration sources

```console
$ opencode debug config
```

The relevant configuration sources were:

| Source | Type | Contents relevant to this workflow |
| --- | --- | --- |
| `~/.config/opencode/opencode.json` | global document | Existing global model assignments, providers, MCP servers and other settings |
| `<repository>/opencode.jsonc` | project document | `default_agent`, `instructions`, project-wide Git/GitHub write restrictions |
| `<repository>/.opencode` | project directory | Agent definitions and future project-scoped resources |

OpenCode merged the project configuration over the global configuration. The
global document remained authoritative for settings the project did not
override, including model assignments.

## Discovered agents

```console
$ opencode debug agents
```

The six workflow agents were discovered with the expected modes and effective
models:

| Agent ID | Mode | Effective model source |
| --- | --- | --- |
| `orchestrator` | `primary` | Global OpenCode assignment |
| `planner` | `subagent` | Global OpenCode assignment |
| `reviewer` | `subagent` | Global OpenCode assignment |
| `implementer` | `subagent` | Global OpenCode assignment |
| `tester` | `subagent` | Global OpenCode assignment |
| `git-manager` | `subagent` | Global OpenCode assignment |

The verification confirmed that each agent resolved to its model in the local
global OpenCode configuration and that the project configuration did not pin
models. The repository intentionally does not record personal model IDs;
assignments remain configurable as described in
[`../workflow/model-assignments.md`](../workflow/model-assignments.md).

The discovery output also contained the built-in agents and other globally
configured agents. The six workflow IDs above were the project-specific entries.

## Permission resolution

The effective rules showed the intended order; with the extended policy the
resolved picture is:

- OpenCode placed its default `*: allow` rule first;
- project-wide rules denied every `git *`, `gh *`, `rtk git *` and `rtk gh *`
  command, then re-enabled read-only inspection such as `git status`,
  `git diff`, `rtk git log`, `gh pr view` and `rtk gh issue view` in both plain
  and RTK form; `gh api*` and `gh pr merge*` stayed denied at the end of the
  project list;
- the RTK file and report tools (`rtk read`, `rtk smart`, `rtk grep`, ... ) were
  allowed for output condensing, while `rtk test`, `rtk err` and `rtk summary`
  were denied except the narrow Go quality-tool filters
  (`rtk test *govulncheck*`, `rtk test *golangci-lint*`,
  `rtk test *jactionlint*`), and `rtk bypass`/`rtk proxy` asked;
- infrastructure, cluster, cloud, database and network tools
  (`docker`, `kubectl`, `oc`, `aws`, `psql`, `wget`) and their RTK mirrors asked
  for approval; `pnpm`, `dotnet` and their RTK mirrors were denied;
- credential and secret locations were denied for `read` and `edit` and inside
  shell command strings, the `external_directory` gate asked for approval first
  and then denied the credential locations plus `~/Library/*`, and every
  `*.env` file except `*.env.example` was denied;
- OpenCode expanded `~` in `read`, `edit` and `external_directory` resources to
  the absolute home directory at load time (for example `~/.ssh/*` becomes
  `/Users/<name>/.ssh/*` in `opencode debug agents`), so tilde patterns match
  the real tool paths at runtime while the committed configuration stays
  home-independent;
- the Go quality tools (`go`, `govulncheck`, `golangci-lint`, `jactionlint`)
  were allowed directly and through the narrow `rtk test` filters;
- the Orchestrator had `edit: deny` with an allow only for
  `docs/workflow/ledgers/**`;
- the Orchestrator had `subagent: deny` with allow rules for exactly the five
  specialist agents;
- the Reviewer, Tester and Git Manager had edit, write and patch denied while
  shell commands remained permission-controlled;
- the Git Manager appended allow rules for branch, commit, push and
  pull-request preparation after the project-wide deny rules — including the
  RTK write mirrors — and repeated the protected denials (`gh api*`,
  `gh pr merge*`, pushes to `main`, the sensitive-path shell block) after its
  allows; `gh pr merge` and `gh api` stayed denied for every agent.

The last matching rule wins, so the Git Manager's explicit allow rules refine
the project-wide deny rules for that agent only, and its trailing deny rules
restore the protected boundaries — for example, `git commit` is denied for
every agent by the project rule and allowed for the Git Manager by its later
rule, while a push to `main` stays denied even for the Git Manager. A broad
agent-level allow rule would override the project restrictions, so the
validator rejects one.

## Shell scanner semantics

The official OpenCode permissions page describes shell permission checks with
a built-in shell scanner across Bash, Zsh, POSIX sh and PowerShell
(<https://opencode.ai/docs/permissions>, section "Scanner"). Key statements
affecting this workflow:

- the `shell` permission resource is the scanner-produced command string, and
  a compound command may produce several;
- permission rules, saved approval patterns and best-effort directory
  inference apply to every extracted subcommand and `cd` target;
- for commands the scanner cannot analyse, a shell deny that applies makes the
  command fail; otherwise the whole command asks.

Consequence for this policy: a protected operation — `gh api`, a pull-request
merge or a push to `main` — is denied in direct and compound invocations even
for the Git Manager, because the matching subcommand resolves to the standing
deny while the preceding subcommand is evaluated separately. A chained
operation such as `git add . && git push origin HEAD` stays allowed because
every extracted subcommand resolves to allow.

`opencode debug agents` exposes the resolved rules, not the runtime matching:
the scanner runs inside OpenCode when a command executes. The offline
validator therefore approximates the scanner best-effort by splitting its
compound samples on the top-level separators `&&`, `||`, `;`, `|` and
newlines and resolving each subcommand with last-match-wins semantics
(quoted wrapper arguments stay one command string). Recorded expectations
such as `git fetch origin && gh pr merge 1` → `deny` follow this model, and
exotic constructs rely on the scanner's fail-closed behaviour.

## Shared instruction loading

- `AGENTS.md` was loaded automatically as the repository instruction file.
- `docs/workflow/feedback-contract.md` was added through the `instructions`
  array in `opencode.jsonc`, after `AGENTS.md`.
- Agent-specific prompts came from the Markdown bodies in
  `.opencode/agents/`.

## Offline validation

The output below is abridged. The committed capture in
[`workflow-check-output.txt`](workflow-check-output.txt) is the exact stdout of
`python3 tools/workflow_check.py ci`, including the release fixtures, the
fixture ledger and the negative fixture cases; the validation README records
its line count and byte size. `ci` runs without network access or credentials.
The final `all` mode adds the live release record and exits non-zero while that
record is missing or incomplete.

```console
$ python3 tools/workflow_check.py ci
PASS audit: workflow_check.py passed 6 static properties ...
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

The recorded discovery used the local OpenCode installation and its existing
authentication context. No credentials were read or exported, no inference was
requested and no provider settings were changed.
