# OpenCode v2.4.1 discovery record

This record documents the project-specific agent discovery and shared
instruction loading for the workflow. The check was run on 2026-11-26 from the
repository root of the workflow branch.

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

The effective rules showed the intended order:

- OpenCode placed its default `*: allow` rule first;
- project-wide rules denied every `git *` and `gh *` command, then re-enabled
  read-only inspection such as `git status`, `git diff`, `git log`, `gh pr view`
  and `gh issue view`;
- the Orchestrator had `edit: deny` with an allow only for
  `docs/workflow/ledgers/**`;
- the Orchestrator had `subagent: deny` with allow rules for exactly the five
  specialist agents;
- the Reviewer, Tester and Git Manager had edit, write and patch denied while
  shell commands remained permission-controlled;
- the Git Manager appended allow rules for branch, commit, push and pull-request
  preparation after the project-wide deny rules; `gh pr merge` stayed denied for
  every agent.

The last matching rule wins, so the Git Manager's explicit allow rules refine
the project-wide deny rules for that agent only. For example, `git commit` is
denied for every agent by the project rule and allowed for the Git Manager by
its later rule. A broad agent-level allow rule would override the project
restrictions, so the validator rejects one.

## Shared instruction loading

- `AGENTS.md` was loaded automatically as the repository instruction file.
- `docs/workflow/feedback-contract.md` was added through the `instructions`
  array in `opencode.jsonc`, after `AGENTS.md`.
- Agent-specific prompts came from the Markdown bodies in
  `.opencode/agents/`.

## Offline validation

The output below is abridged. The full run, including the fixture ledger and the
actual-repository ADR section, is committed in
[`workflow-check-output.txt`](workflow-check-output.txt).

```console
$ python3 tools/workflow_check.py all
PASS config: six agents, resolved permission boundaries, shared instructions, Git ownership and human-only merge are consistent
PASS adr: open pull-request ADRs remain proposals and do not change the baseline
PASS reports: synthetic reports reconcile with gaps and escalations as expected
PASS adr: open pull-request ADRs remain proposals and do not change the baseline
All workflow checks passed.
```

The recorded discovery used the local OpenCode installation and its existing
authentication context. No credentials were read or exported, no inference was
requested and no provider settings were changed.
