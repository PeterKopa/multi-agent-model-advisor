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

## Follow-up: catalog and default-model fallback

Official documentation reviewed 2026-11-25: https://opencode.ai/docs/console/api/models/ documents GET https://opencode.ai/console/api/v1/models, returning caller-accessible providers and model IDs. This is a Console-specific authenticated catalog, not a substitute for installed CLI/project-context discovery, and does not establish all configured custom routes. Prefer the installed CLI and existing authentication; no new API key or automatic API fallback. https://opencode.ai/docs/models/ documents project-specific availability and a default-model fallback when the configured model is unavailable. Preserve configured versus effective model identity and mark unresolved effective assignments. For later bounded inference (#11), verify the exact effective route/model and fail closed if substitution cannot be prevented or detected before dispatch. Do not treat an upstream default fallback as user approval. No live requests performed in this follow-up.

## Installed CLI help evidence (2026-11-25)

The user supplied terminal output from OpenCode v2.4.1 on macOS. `models --help` confirms the model-list command, with no documented JSON output option. `debug --help` confirms agents, config and paths subcommands. `api --help` confirms operation-ID or HTTP method/path invocation, --param, --standalone and --server. Only version/help was observed; no model inventory or agent API response was supplied. Do not use heap-dump for discovery because it may contain secrets.

Current official API reference https://opencode.ai/docs/api documents read-only GET /api/model (model.list, explicitly experimental), GET /api/agent (agent.list), and GET /api/model/default (model.default). Candidate structured discovery path: validate these operations against installed v2.4.1 in a user-approved disposable context; prefer method/path for initial validation. The models snapshot may be incomplete before plugins settle. Check response shape, readiness, context, secrets and side effects locally before enabling. Do not automatically start a server, switch between standalone/shared server, or fall back to another method on error. No prompt or inference is required. No raw agent/config data should be shared. A local GET does not by itself prove no background network/plugin activity. Retain #7 runtime gates.

## Observed model inventory response (OpenCode v2.4.1)

On 2026-11-25 the user supplied a truncated prefix of the output of `opencode api GET /api/model | head -c 3000`. Structured model records were observed in a top-level data array, with location metadata. This confirms that the installed CLI can return structured model inventory in the tested context, not that the entire response parses, all providers are covered, or discovery is free of side effects. The reported location must be checked locally against the requested project context; do not assume the invoking working directory determines the returned context.

Observed field names include id, modelID, providerID, canonical (optional), type, name, family (optional), capabilities, variants, time.released, cost (array with input, output, cache.read and cache.write), status, enabled and limit (context, input, output where present). Preserve native provider/model identifiers including nested namespaces; canonical is not proof of exact benchmark identity. Variants include supported reasoning settings in some records; availability does not identify the effective default. An explicit zero rate was observed on a free offering, but tariff units, cost-array tier semantics, peak/off-peak, promotions, context thresholds and actual allowance billing are not established by the truncated sample. Validate under #6 and #13. Prefer applicable configured route reference rates where verified; do not infer missing rates as zero.

The response also exposes headers, settings and location information that can contain account/organization/connection identifiers, credentials or local paths. Use an explicit allowlist of needed fields, with nested-field validation; never persist raw headers, settings, endpoints containing private identifiers or full debug dumps, or export them to external services/logs. No user-specific values or raw records are copied here. Keep project context local. Next validation should parse the entire response locally and emit only structural counts and known field presence, rather than a raw prefix. Agent discovery and default model endpoints remain untested. No inference requested by this GET; network/background writes and complete runtime isolation are still unverified.

## Complete model inventory structural counts (2026-11-25)

The user subsequently reported successful local parsing of the full GET /api/model response using Python json.load and aggregate counts only. Observed in the user's installed OpenCode v2.4.1 configuration context: 476 model offerings across 7 distinct providerID values, 476 enabled, 422 with a nonempty cost field, 68 with more than one cost entry, and 312 with nonempty variants. These are route/model offering counts, not unique canonical models or verified account entitlements. 54 offerings have an empty or absent cost field. Presence of cost is not proof of complete applicable rates, price units, current tariff, actual charges, or allowance eligibility; multiple entries do not establish peak/context semantics by themselves. Variant presence does not establish effective default effort. The user-local parse confirms full JSON was readable in that observed run; no raw inventory or private identifiers are included. Next inspect only allowlisted structural metadata of cost entries and their conditional fields, then independently verify tariff units/semantics (#6) and agent discovery. No inference requested; context isolation and background side effects remain unverified.

## Observed price-tier field shapes (2026-11-25)

The user reported aggregate-only inspection of multi-price offerings: 68 entries with cache/input/output fields and 70 entries with those fields plus tier (138 entries total). A base rate and additional conditional rates appear plausible, but the nested tier conditions and applicability have not yet been inspected. The official API reference https://opencode.ai/docs/api defines Model.Cost input/output as Money.USDPerMillionTokens and optional tier; https://opencode.ai/docs/providers documents per-million-token pricing. https://opencode.ai/docs/console/providers documents context tiers. Validate nested tier shapes, supported conditions and installed-version compatibility before selecting rates; do not infer peak or context meaning from array position. No private records copied.

## Observed OpenCode context tier conditions

User-reported local OpenCode v2.4.1 inventory inspection on 2026-11-25 found 70 tier entries, all with type=context and numeric size: 32000 (2), 100000 (4), 128000 (3), 200000 (15), 256000 (8), 272000 (37), 512000 (1). Counts are entries, not distinct models. No peak/off-peak condition was observed in these tier objects. Official Console provider documentation https://opencode.ai/docs/console/providers describes context tiers as prices above the configured prompt size, and https://opencode.ai/docs/providers documents cost rates per million tokens. For the reference scenario, Small selects the documented base price, Large selects the applicable higher context tier; where more than one higher tier exists, expose its threshold and require unambiguous selection rather than guessing. Preserve all rates and thresholds. A flat documented tariff is unaffected. Peak/Off-Peak cannot be derived from the observed tier objects; validate separate applicable rate evidence and do not silently relabel an unqualified price as off-peak. This local observation is not an actual billing test. No private inventory records stored.

## Observed agent inventory response (2026-11-25)

User-local OpenCode v2.4.1 GET /api/agent parsed successfully as a JSON object with data and location. Aggregate field presence: 19 records, each containing id, name, request, mode, hidden and permissions; model present in 11, description in 5, system in 4. These counts describe field presence, not necessarily non-null or valid values. Do not equate all returned agents with the user's configured project agents, infer effective model assignments for missing model fields, or treat location as validated against requested context. Inspect model value types and known nested model fields using aggregate-only local output next. Preserve hidden status for explicit selection rather than silently excluding records. Exclude request, system and permissions payloads from inventory persistence by default; do not export agent prompts, raw records or private identifiers. The GET returned structured agent inventory in the observed context; exact assignment/variant interpretation, inheritance, project isolation and background side effects remain open. No inference requested.

## Observed agent model value shapes (2026-11-25)

User-local aggregate inspection of GET /api/agent returned 11 model objects and 8 missing/null model values. All 11 objects contain id and providerID; no other model-object keys were reported. Candidate exact inventory join is agent.model.providerID plus agent.model.id against inventory providerID plus modelID (retain inventory id separately and validate equality/mismatches, duplicate matches and context consistency). No individual identifier values or prompts were supplied in this probe. The absence of an explicit variant field in these objects does not establish default reasoning or lack of variant support; variant semantics, inheritance and effective assignments remain unverified. Validate matching locally with aggregate counts, requiring matching response locations, and never guess an alias or silently choose between duplicate matches. The result does not establish side-effect isolation. No inference requested.

## Observed exact agent-to-model inventory join (2026-11-25)

The user reported a successful local aggregate-only join of GET /api/model and GET /api/agent on installed v2.4.1: equal reported location objects, 11 exact unique matches using (agent.model.providerID, agent.model.id) against (inventory.providerID, inventory.modelID), 8 agents without explicit models, no unmatched or ambiguous explicit assignments reported. This establishes exact route association for the observed explicit assignments, not effective session model identity or actual inference routing. Equal reported locations are not proof of the requested project context or isolation. Missing assignments remain unresolved unless inheritance can be established; do not substitute the default model. Supported catalog variants do not establish selected/default effort. Prefer structured read-only CLI API for the MVP, subject to version/context checks and side-effect validation; do not automatically fall back. Use synthetic fixtures for ambiguous/missing joins and variant handling. No private identifiers or raw records stored, no inference requested.

## Correction: selector identity versus upstream model ID

Verified official documentation on 2026-11-25: https://opencode.ai/docs/providers/ distinguishes the OpenCode models-map key (selectable model ID) from modelID (upstream model/deployment ID). https://opencode.ai/docs/models/ documents case-sensitive native references and optional #variant; https://opencode.ai/docs/agents/ documents parent-session model inheritance for subagents and separately stored session selection. Correct the earlier provisional join: use (agent.model.providerID, agent.model.id) against (catalog.providerID, catalog.id), retaining catalog.modelID separately for possible canonical mapping. The 11 observed matches using modelID remain historical evidence, not proof of alias-safe joining. Verify alias/variant behavior in a synthetic fixture. https://opencode.ai/docs/api documents the location[directory] query for model discovery and optional location for agent discovery. Explicitly request and validate the intended location, rather than assuming cwd or equal default locations proves project scope. Test only GET on a temporary synthetic project; no reload, session, generation, real config edits or raw response export. Existing shared server may initialize global/system integrations; do not claim complete isolation. Runtime fixture results remain pending.
