# GitHub Copilot CLI discovery feasibility

Related to #8. Documentation reviewed 2026-11-25. Status: documented interfaces; installed-version and runtime behavior unverified.

## Model inventory

GitHub's official Copilot SDK communicates with the CLI using JSON-RPC. The documented listModels interface exposes models with capabilities, billing and policy metadata; the server RPC is models.list. Prefer the official Go SDK over parsing the interactive /model menu, subject to compatibility and dependency review. The Go SDK does not ship a CLI automatically. Use an explicitly selected, already installed compatible binary over stdio; no automatic installation, account switching or new API-key requirement. Existing signed-in CLI credentials may be used by the CLI without exporting them to the advisor. Runtime startup, authentication selection, network access, retry behavior, logs and filesystem side effects still require validation. Do not assume inventory implies successful execution, remaining allowance or policy eligibility.

The SDK documents per-model token pricing via models.list and additional usage events during actual inference. Preserve price units, route identity, model variants, missing fields and context-tier limitations. Reference-cost scenarios remain governed by #6; do not convert account quotas into invented prices. Usage events are a possible future input for optional tests (#2), not required for discovery.

## Agent discovery and configured assignments

Documented custom agent files are Markdown with YAML metadata. The CLI's command reference describes user-level ~/.copilot/agents, project .github/agents and .claude/agents, added roots, plugin and remote organization agents, with specific precedence. Read only explicitly selected local configuration; do not fetch remote organization settings, load plugins or add trusted roots automatically. Preserve path-derived native IDs (nested paths are documented as joined by double hyphens), name, configured model(s), policy and reasoning effort. Keep declared assignments, user subagent overrides, inherited session defaults and actual effective models distinct. The documented precedence includes per-call override, user settings, agent declaration and parent session; required model policy has special constraints. Preferred model/effort can fall back to the session's value. Never treat this as consent for substitution; for #12 validate exact route selection and fail-closed behavior before enabling execution. Do not inspect session history or create an inference session just to infer an assignment.

Local or custom provider offerings may appear. Preserve native references and unresolved provider/model metadata; local execution remains outside the MVP. Do not infer canonical identity, actual location or privacy properties from a name.

## Local verification plan

- First collect installed CLI version and supported help output only.
- In a disposable context with synthetic agent files, test local discovery and precedence without modifying original settings. Validate unsupported version, absent CLI, conflicts, missing model, inherited model, custom IDs and malformed metadata.
- After explicit approval, test only the documented model inventory interface using existing authentication. Record exact SDK/CLI versions, structured field availability, subprocess lifetime, network destinations and any local writes. No prompt, session creation, tool execution, secret export, automatic retry/fallback, installation or settings changes. If these boundaries cannot be established, disable the adapter operation and retain explicit manual import.
- Use synthetic fixtures in the repository; never commit private inventory, credentials, agent bodies or raw settings. Keep #8 open until runtime evidence is obtained. Prompt-only execution and quota reuse remain separate work packages.

## Sources

- https://docs.github.com/en/copilot/how-tos/copilot-sdk/troubleshooting/compatibility
- https://docs.github.com/en/copilot/how-tos/copilot-sdk/setup/local-cli
- https://docs.github.com/en/copilot/how-tos/copilot-sdk/features/usage-and-billing
- https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference
- https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents-for-cli

No installed CLI or live account was tested, no inference or spending performed. No production dependency or adapter implemented.
