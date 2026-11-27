# Model assignments

The workflow keeps model selection configurable and personal. Repository files
define roles, permissions and shared instructions; they do not pin models or
credentials.

## Default: global OpenCode configuration

Assign models in the existing global configuration at
`~/.config/opencode/opencode.json(c)`. The agent IDs match the project agent
files:

```jsonc
{
  "agents": {
    "orchestrator": { "model": "provider/model#variant" },
    "planner": { "model": "provider/model#variant" },
    "reviewer": { "model": "provider/model#variant" },
    "implementer": { "model": "provider/model#variant" },
    "tester": { "model": "provider/model#variant" },
    "git-manager": { "model": "provider/model#variant" }
  }
}
```

Edit only the entries you need. OpenCode merges the global configuration with
the project configuration; unrelated global settings, providers, MCP servers
and agent assignments remain in place. Keep credentials and account-specific
provider settings in their existing authorised local locations.

## Optional project-local overrides

When a repository needs a pinned model, add the relevant entry under `agents` in
`opencode.jsonc` and uncomment or replace the example in that file:

```jsonc
{
  "agents": {
    "reviewer": { "model": "provider/model#variant" }
  }
}
```

Project values override only the fields they define. An agent without a model
inherits its model from the global configuration or, for a subagent, from the
parent session when no assignment exists. Prefer the global configuration for
personal preferences so that a shared repository stays model-agnostic.

## Verification

Check the effective assignments and the discovered agents from the repository
root:

```bash
opencode debug agents
opencode debug config
```

The agent list shows the project agent IDs, modes and effective models; the
configuration listing shows which configuration documents were loaded. Record
the OpenCode version when verifying a new setup. The workflow was checked with
OpenCode v2.4.1; see
[`docs/validation/opencode-v2.4.1-discovery.md`](../validation/opencode-v2.4.1-discovery.md).
