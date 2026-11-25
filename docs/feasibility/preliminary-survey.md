# Phase 0 — Preliminary feasibility survey

Date: 2026-11-25. Related: #1, #2, #4–#13.

## Scope and conclusion

The cloud-only MVP is plausible. Public documentation establishes candidate interfaces and two retrieved JSON examples establish useful data shapes. This is a preliminary cross-issue survey, not completion of the individual feasibility spikes. No local installed CLI, authenticated benchmark API, account quota, safe execution boundary or live inference was tested. No paid requests were made. Source documents may change; examples retrieved via web search may be cached.

Status vocabulary: **documented** = official interface described; **sample inspected** = public response example retrieved; **unverified** = runtime/account/data rights or required semantics not established. None of these implies production readiness.

## Evidence by work package

| Issue | Preliminary finding | Remaining gate |
| --- | --- | --- |
| #4 OpenRouter benchmark data | Documented GET /api/v1/benchmarks, authenticated, multiple sources and heterogeneous response shapes. | Authenticated read-only sample, rights and benchmark/default-effort metadata. |
| #5 Hugging Face | Public SWE-bench Verified leaderboard JSON inspected. Dataset-level leaderboard API documented. | Dataset-specific terms, revisions, test configuration, broader sample and duplicate resolution. |
| #6 Pricing | OpenRouter model JSON sample inspected. Ollama and OpenCode Go publish rate information. | Normalize exact route/variant, currency, rates, cache semantics and billing tiers; no subscription cost guarantee. |
| #7 OpenCode discovery | models command and agent/config interfaces documented. | Installed-version test with sanitized config and read-only fixtures. |
| #8 Copilot discovery | Interactive model list and SDK listModels documented. | Test supported Go SDK/CLI version and existing authentication; manual import fallback. |
| #9 Ollama Cloud | Public cloud catalog and OpenCode integration documented. | Stable supported catalog retrieval, exact route/alias mapping, refresh and entitlement evidence. |
| #10 Privacy | OpenRouter public ZDR endpoint metadata and routing controls documented. | Private configured route enforcement, geography and evidence freshness; unresolved restrictions remain unknown. |
| #11 OpenCode prompt-only | Noninteractive run, JSON output, model choice and permissions documented. | Isolation, disabling tools/plugins, cancellation and permission enforcement must be demonstrated before any inference. |
| #12 Copilot prompt-only | Programmatic CLI and SDK model/tool controls documented. | Verify version, context isolation, denied tools, no silent substitution, timeout/cancellation. |
| #13 Allowances | OpenCode Go and Ollama Cloud support documented access routes. | Verify the actual configured account/plan, paid overage behavior, route eligibility and user-approved bounded live test if needed. |

## 1. Benchmark evidence (#4, #5)

- OpenRouter documents a unified benchmark endpoint aggregating multiple sources. The documented response contains source-specific fields: canonical model slug, benchmark type/score or aggregate indices, timestamp and source metadata where supplied. A valid OpenRouter key is required; the unauthenticated retrieval attempt did not yield a usable result in this environment. Authentication for read-only data retrieval is distinct from paid inference. Do not require a new paid inference account.
- Hugging Face documents official benchmark discovery and per-dataset leaderboard API. An accessible SWE-bench Verified response showed modelId, value, verified, lower_is_better, source and eval-results filename. Some displayed entries were explicitly unverified. This sample was cached, so it is evidence of structure, not current rank. The attempted Terminal-Bench 2.1 leaderboard retrieval did not return usable data through this environment; its dataset page is public. Do not infer all fields or coverage from the one sample.
- Start with a small set of role-relevant benchmark definitions, e.g. SWE-bench Verified and Terminal-Bench, with explicit version/harness and default-effort evidence. A missing reasoning configuration is not evidence of default effort. Compare runs only where sufficiently compatible; retain source and verification status. Do not count an aggregate index and its constituent benchmarks as independent evidence without a justified design.
- Licenses and terms for benchmark scores and redistribution remain unverified. The implementation repository should contain synthetic fixtures until permission and provenance are established.

Sources:
- https://openrouter.ai/docs/api/api-reference/benchmarks/list-benchmarks
- https://huggingface.co/docs/hub/leaderboard-data-guide
- https://huggingface.co/api/datasets/SWE-bench/SWE-bench_Verified/leaderboard
- https://huggingface.co/datasets/SWE-bench/SWE-bench_Verified
- https://huggingface.co/datasets/harborframework/terminal-bench-2.1

## 2. Reference costs (#6)

The retrieved OpenRouter model catalog JSON provides model IDs, canonical slugs, supported parameters and pricing fields. Individual entries can omit cache or other rates, so omitted data must not default to zero. Endpoint-specific pricing may differ from catalog-level price. The Ollama pricing page documents input, cached input, output and certain off-peak rates; Go documents allowance-related rates and limits. Public rates must not be applied to legacy plans without evidence.

Synthetic calculation (USD, rates per million): 400k uncached input at 1, 500k cached reads at 0.1, 100k output at 4 => 0.85. Cache-write and reasoning categories require explicit billing semantics: if included in another billed count, do not add them again; if separately billed and the rate is missing, the estimate is unknown. No-cache and cache-intensive scenarios remain editable. RTK assumptions are not measured savings. Always preserve source, date, tariff, model identity, and price type (actual route tariff, proxy, user estimate). Ranking remains quality-only.

Sources:
- https://openrouter.ai/api/v1/models
- https://openrouter.ai/docs/api/api-reference/models/get-models
- https://openrouter.ai/blog/tutorials/prompt-caching-sticky-routing/
- https://ollama.com/pricing
- https://opencode.ai/docs/console/go/

## 3. Discovery and route identity (#7–#9)

OpenCode documents model listing and agent/configuration definitions, including JSON/JSONC and native model references. Keep parsing of the effective context version-aware, preserve exact IDs and provide manual import. Copilot CLI documents an interactive model picker; its official SDK documents JSON-RPC model enumeration, including billing/capability/policy metadata. This is a promising alternative to parsing an interactive screen, but SDK version and installed CLI compatibility must be checked. Do not infer access from a public supported-model list.

Ollama documents a cloud catalog, cloud inference and OpenCode integration. Cloud model tags and canonical benchmark identities need explicit mapping; a local service URL can proxy a cloud model. Use already configured routes, not automatic configuration changes. Ollama Local remains outside MVP. No stable machine-readable cloud catalog interface or account-specific entitlement has yet been verified here.

Sources:
- https://opencode.ai/docs/cli/commands
- https://opencode.ai/docs/config
- https://opencode.ai/docs/agents
- https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-programmatic-reference
- https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-config-dir-reference
- https://docs.github.com/en/copilot/how-tos/copilot-sdk/troubleshooting/compatibility
- https://docs.ollama.com/cloud
- https://docs.ollama.com/integrations/opencode
- https://ollama.com/search?c=cloud

## 4. Privacy and optional execution (#10–#12)

OpenRouter documents ZDR endpoint information and routing constraints. A public endpoint being eligible does not prove the user's backend/account actually enforces ZDR. Geography, retention, policy constraints and endpoint evidence must remain separate; do not infer EU-only processing from a regional label or no training from ZDR. Provider evidence can change, so record dates and revalidate.

Both CLI families document noninteractive execution and model/tool controls. These are candidate interfaces, not proof that no files, external tools, plugins, inherited instructions or ambient context will be accessed. Before enabling an adapter for LLM assistance or judging, verify bounded prompt-only behavior on a disposable synthetic environment with explicit permissions, no tools or project access, exact route/model, cancellation, timeout, and controlled subprocess behavior. Do not use automatic permission approval. Unsupported/unverified controls disable execution. Manual supplied responses and manual rubric assessment can proceed independently. Judge outputs are untrusted assessments, separate from public scores and actual team effectiveness.

Sources:
- https://openrouter.ai/blog/insights/zero-data-retention/
- https://openrouter.ai/docs/guides/features/guardrails/overview
- https://openrouter.ai/blog/insights/ai-data-residency/
- https://opencode.ai/docs/permissions
- https://opencode.ai/docs/cli/commands
- https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-programmatic-reference
- https://docs.github.com/en/copilot/how-tos/copilot-sdk/troubleshooting/compatibility

## 5. Existing allowances (#13)

OpenCode documents Go as a configured provider and a dedicated API. It also documents optional Extra Usage after allowance exhaustion, and expectations for supported coding-agent traffic. Ollama documents cloud access and included plan credits, plus purchased credit usage after included credits for current plans. Older plans can have different limits. The user's exact legacy plan, credentials, settings and route have not been accessed. Do not infer authorization or free execution from a provider identifier, or infer actual cost from public rates.

Reuse existing supported routes only if terms, user approval, bounded prompt-only execution, and no unintended paid fallback can be established. If cost or account behavior cannot be established, keep live execution disabled for that route. No changes to account settings, no secret export, no live inference in this survey.

Sources:
- https://opencode.ai/docs/console/go/
- https://ollama.com/pricing
- https://docs.ollama.com/cloud

## Recommendation and next steps

Conditional go for the offline core and manual practical evaluation. Prioritize #4/#5/#6 source validation, #7 read-only discovery and #10 evidence model. Proceed with #11/#12 only after the relevant discovery and privacy gates. #13 remains contingent on #9/#11 and account-specific evidence. Go + Bubble Tea architecture remains suitable as a design decision; this survey did not build or benchmark it. Keep all ten issues open until their acceptance criteria are actually met. No implementation changes, no live requests, no completed capability or allowance claims.
