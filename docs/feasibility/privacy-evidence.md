# Hosted route privacy evidence feasibility

Related to #10. Documentation reviewed 2026-11-26. No inference, private account inspection, or live authenticated metadata probes were performed.

## Public evidence and request controls

OpenRouter documents GET /api/v1/models?zdr=true as a model catalog restricted to models having ZDR endpoints, and GET /api/v1/endpoints/zdr as an endpoint registry. The API-reference search result for the latter was available but opening its reference URL returned 404 during this review; the current official ZDR article independently identifies the registry URL. Authentication requirements, live access, schema and pagination are unverified. A model-level match is not proof of the configured route's eligibility. Use endpoint evidence independently of inventory and benchmark identity. Never interpret registry absence as confirmed retention without establishing source completeness and scope.

OpenRouter documents request-level provider.zdr, provider.only, provider.ignore, provider.order, provider.allow_fallbacks and data_collection. Restricting providers and disabling fallback are distinct from verifying effective routing; these controls need not be exposed or forwarded by a configured CLI/gateway. Workspace and key guardrails may add restrictions. Record account or administrator declarations separately, without privileged APIs or credentials. Public endpoint policies and configured enforcement do not independently prove a provider's actual conduct. Provider retention, training, gateway logging and operational metadata are separate fields. OpenRouter describes exceptions to content deletion and retention of usage metadata.

OpenRouter's recent incident announcement (22 November 2026 according to the retrieved publication age) reports removal of 125 endpoints from ZDR eligibility. This illustrates why privacy evidence needs retrieval timestamps, independent refresh and re-evaluation of dependent eligibility. Do not retain stale evidence as verified or silently expand routes on refresh.

## Geography

OpenRouter advertises regional routing on eligible Business/Enterprise arrangements. Its European regional endpoint covers EU/EEA, UK and Switzerland for shared capacity; it is not an EU-member-states-only guarantee. US regional routing is also documented. BYOK deployment location is controlled by the customer's configuration, not inferred from the gateway domain. Operational/account/billing metadata is distinct from inference content location. Provider legal domicile and developer origin are independent of processing and storage. Do not infer the location of subprocessors or all possible fallback routes from a provider name or regional label.

## Other providers

OpenCode Console models and Go documentation publish different retention policies and exceptions by model/plan. The Go privacy table includes both zero-day and nonzero retention entries; do not propagate a Go or Console policy to a custom backend. OpenCode terms distinguish third-party model policies. Ollama's public privacy policy describes transient processing of hosted prompt/response content, but this alone does not establish an intermediary's policy, the specific deployment's geographic location or the effective behavior of a custom OpenCode route. These are service-level claims, not independently verified endpoint-specific enforcement.

## Synthetic eligibility fixtures

Use synthetic routes with no private identifiers. For a mandatory ZDR filter:
- Route A: sufficient fresh evidence for endpoint policy and effective routing constraints, all possible selected endpoints eligible: pass for this filter only.
- Route B: known applicable non-ZDR endpoint under the requested configuration: fail; no recommendation or execution.
- Route C: public ZDR-capable endpoint exists but actual configured routing is unknown: unknown; explicit comparison-only inclusion allowed, no eligible recommendation or external execution under this mandatory filter.
- Route D: previously eligible evidence is stale or revoked: re-evaluate to unknown or fail according to current evidence, preserve history; no silent substitution.

For mandatory EU-member-state-only inference, a Europe-wide route without narrower endpoint proof is insufficient. A known permitted-only deployment passes this filter if sufficiently evidenced; known disallowed processing fails; unresolved deployment/region remains unknown. No-filter conditions are not applicable. A confirmed comparison-only decision is scoped to the offering and unresolved criteria, not permission to transmit data. If all selected routes fail or remain unknown, show no eligible recommendation. Quality scoring stays separate.

## Bounded read-only verification plan

Use only explicit user-initiated HTTPS requests to the documented metadata origin/endpoints, with certificate validation, no redirect, bounded timeout, no automatic retry/fallback, and no credentials by default. Check HTTP status, parsed JSON shape, counts, scope and freshness locally; emit aggregate evidence only. If access requires authentication, record the blocker and do not request secret export or use privileged credentials. Any future optional authenticated access follows #4's secure credential requirements and separate consent; do not broaden the allowed endpoint scope automatically. No inference or policy mutation. Do not store raw private configuration, headers, account identifiers, or unlicensed catalogs. Record source, retrieval time, evidence type (public claim, user declaration, supported configuration observation, unknown), scope and limitations. Manual evidence entry and explicit refresh remain available; no automatic paid route selection.

Before #11/#12 prompt-only tests, independently establish the selected exact route, permitted transmitted data, bounded execution, disabled tools and no unapproved fallback. A successful response is not proof of privacy compliance. Unknown mandatory conditions block the test. No production policy engine or legal certification is delivered here.

## Sources reviewed 2026-11-26

- https://openrouter.ai/docs/api/api-reference/models/get-models
- https://openrouter.ai/docs/api/api-reference/endpoints/list-endpoints-zdr (indexed description; direct fetch returned 404)
- https://openrouter.ai/blog/insights/zero-data-retention/
- https://learn.openrouter.ai/courses/control-routing/provider-selection
- https://openrouter.ai/blog/announcements/data-processing-incidents-on-inference-providers/
- https://openrouter.ai/docs/guides/features/guardrails/overview
- https://openrouter.ai/business/eu/
- https://openrouter.ai/blog/announcements/us-in-region-routing/
- https://opencode.ai/docs/console/models/
- https://opencode.ai/docs/console/go/
- https://opencode.ai/de/legal/terms-of-service
- https://www.ollama.com/privacy

Status: documented controls and limitations; live registry accessibility, response schema, effective CLI enforcement and concrete route geography remain unverified. Keep #10 open.
