# OpenCode prompt-only capability feasibility

Related to #11; depends on #7 and #10. Documentation inspected 2026-11-26. Installed v2.4.1 previously observed for read-only discovery, but generation controls have not been tested.

## Candidate interfaces

Official CLI documentation https://opencode.ai/docs/cli/commands/ describes noninteractive run, explicit --model, --agent, --format json (newline-delimited events), and --standalone where supported. Do not use --auto, attachments, session continuation, or existing project content. A normal run is an agent session, not a proven prompt-only call.

Prefer investigation of the documented experimental POST /api/experimental/generate/text (experimental.generate.text), described at https://opencode.ai/docs/api as one stateless text generation using server base configuration. Omitting the model selects the base default; always require an explicit exact model, never omit it. The published request and response schemas are generic objects, so the exact installed-version body, output limit, usage fields, tool absence, request count, cancellation, effective route and retry behavior remain unverified. Do not guess payload fields or send malformed POST requests to discover the schema. The older alias is deprecated; no automatic fallback. Session.generate uses existing session context and is not the preferred isolated path. An experimental endpoint needs explicit version compatibility checks.

## Important boundaries

https://opencode.ai/docs/agents/ documents ordered agent permission rules with wildcard deny, but project instructions, references and other instruction sources can still be added to system prompts. Agent steps are not a proven total provider-request cap. The same documentation warns per-agent request body/header overlays are not yet sent by the V2 session runner. Do not rely on those overlays or V1 tools/maxSteps fields for cost or privacy enforcement. https://opencode.ai/docs/permissions/ describes permissions, not proof of total plugin/tool isolation. https://opencode.ai/docs/config/ documents optional warming and automatic compaction; investigate auxiliary requests, inherited configuration and effective provider settings before execution. No configuration edits to the real client or disabling mandatory policies.

## Next local check

Collect only opencode --version and opencode run --help, and inspect documented or locally available supported OpenAPI/source schemas for the installed version, without printing configuration/credentials or issuing POST requests. Validate the candidate stateless API using a synthetic/fake provider or fixture first if a supported setup can be isolated without changing real settings. Verify exact model selection (including rejection of nonexistent selector before inference), no tools, exact outbound data, positive bounded token limit, no unapproved retry/fallback/auxiliary inference, errors, request accounting and actual cancellation. A client timeout alone does not establish server cancellation. Unknown controls block live execution; manual response import remains available. Do not treat successful read-only inventory as proof of these controls.

For the first eventual live test use a user-approved inexpensive Ollama-backed OpenCode route (DeepSeek V4.1 Flash preferred), a tiny synthetic text prompt, one authorized request, explicit cost/allowance warning and confirmation, no project data. Kimi only when separately needed and explicitly selected, never automatic. The billing path and effective privacy restrictions still require evidence. No live generation performed or authorized by this document.

Status: official candidate interfaces documented; runtime enforcement, installed schema, output accounting and cancellation unverified. Keep #11 open; no production implementation.
