# OpenCode v2 discovery feasibility

Related to #7. Documentation reviewed 2026-11-25. Status: documented, installed-version behavior unverified.

## Official discovery interfaces

- `opencode models` lists available model references. Check `opencode models --help` on the installed release before selecting any output or refresh options. Inventory is not proof of quota, actual endpoint, privacy, price or successful invocation.
- `opencode debug agents` is documented for agent inspection, `opencode debug config` for configuration sources, and `opencode debug paths` for global paths. The precise output schema, secret exposure, plugin execution, background-server behavior, network access and side effects have not been tested. Do not automatically run these commands on real projects before validating their boundaries in a disposable context.
- The CLI documents requests to an already running server through `opencode api`. Evaluate supported structured read-only interfaces separately; do not assume an operation ID or start a server automatically.
- Start by collecting only version/help output on the user's installed CLI. No prompts, real project configurations, agent bodies, credentials, full debug dumps, logs or environment values are needed for this step.

## Configuration and identity

Native V2 uses JSON/JSONC configuration with an `agents` object, and Markdown agents with YAML frontmatter at global or project `agents/` directories. Nested agent file paths may form nested agent IDs. Configuration resolution includes global configuration, ancestor direct files, ancestor .opencode configuration and system-managed settings, with documented precedence. Validate V1 migration/compatibility and actual installed version before interpreting older forms. Do not implement a guessed precedence algorithm.

V2 model references support provider/model#variant as well as expanded model objects with providerID, model and variant for agent definitions. Preserve full original references, arbitrary provider IDs, nested model namespaces, version tags and suffixes. Parse variant semantics only with confirmed version-specific rules. Keep route identity, underlying service, canonical benchmark identity and reasoning configuration separate. Unknown aliases remain unresolved. Preserve explicit variants even though default-effort comparison remains the MVP ranking rule.

A configured subagent may inherit the parent session model if none is specified. Session-selected models are separate from configured defaults; do not fabricate effective assignments or assume selecting a primary agent changes the session model. Distinguish explicitly configured, inherited, session-specific and unresolved assignments. Do not inspect session history merely to discover configuration.

Synthetic examples (not user data):
- Agent ID team/reviewer with model custom-gateway/vendor/example-model:revision#high.
- Expanded model object providerID=custom-gateway, model=vendor/example-model:revision, variant=high.
- Agent with omitted model: inherited/unknown effective model until the applicable context is established.

## Validation plan

1. Obtain installed version and command help only. Compare documented CLI surface to actual release.
2. Build disposable synthetic fixtures with JSONC comments/trailing commas, Markdown frontmatter, nested agent IDs, custom backends, explicit/inherited models, V1/V2 forms and precedence conflicts. Use no actual credentials or project content.
3. Validate inventory and agent discovery separately, including structured output support and absent CLI, timeout, malformed output, unsupported flags, disabled providers and unresolved execution type. Verify no writes to original project/configuration, no inference, no credential export, no unauthorized network or plugin execution. A documented command is not proof of these properties.
4. Prefer supported structured output; if unavailable, validate a version-specific parser or offer explicit manual import. Keep raw configuration and prompts local. No automatic fallback, account changes, model substitution or inference.
5. Document observed version, exact command, context, sanitized fixture, side effects and unsupported capabilities. Do not enable production auto-discovery before validation.

## Sources

- https://opencode.ai/docs/cli/commands/
- https://opencode.ai/docs/config/
- https://opencode.ai/docs/agents/
- https://opencode.ai/docs/models/
- https://opencode.ai/docs/migrate-v1/

No installed CLI was run by this documentation review. Keep #7 open; prompt-only execution and allowance reuse remain separate #11 and #13 gates.
