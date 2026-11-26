# Ollama Cloud catalog and route mapping feasibility

Related to #9. Public documentation inspected 2026-11-26; live local catalog retrieval and account entitlement remain unverified.

## Public sources

- https://ollama.com/search?c=cloud is the official public cloud catalog. The retrieved page lists current cloud model families, including DeepSeek V4.1 Flash, GLM 5.3 Flash and Beam. A family listing does not establish a specific tag or account availability.
- https://docs.ollama.com/cloud distinguishes hosted inference and local operation, links the cloud library and model lifecycle, and documents direct cloud API access. Lifecycle detail page could not be retrieved during this review.
- https://docs.ollama.com/api/tags documents GET /api/tags and model names, modification timestamps, digests and details; its example is local. A public JSON response was also observed at https://ollama.com/api/tags, but the retrieved copy was approximately three months old. Freshness, cloud-only coverage, unauthenticated access from the user's environment, and production support of this exact hosted listing are not yet established. Do not query localhost or local inventory as an automatic substitute.
- https://ollama.com/library/deepseek-v4.1-flash and https://ollama.com/library/deepseek-v4.1-flash/tags distinguish the direct hosted API model name from CLI cloud tags. The retrieved tag page shows the same short digest for the default cloud tag and the explicit 1017 cloud tag. This supports a candidate equivalence at the observed date, not guaranteed runtime equivalence or a stable alias. Do not treat a short digest as full immutable identity.

## Route mapping

Keep exact OpenCode configured backend and selectable model ID, upstream ID, public Ollama tag/digest, canonical benchmark identity, effective execution location, intermediary, billing arrangement and account entitlement separate. A user-configured gateway can use a different backend ID; no provider-name hardcoding. The user supplied a configured Ollama-backed model list through OpenCode; intermediary and billing path are user-described but not independently verified. Do not copy private account-specific inventory into repository fixtures.

Public example: deepseek-v4.1-flash and deepseek-v4.1-flash:1017 are candidate upstream names corresponding to public CLI tags deepseek-v4.1-flash:cloud and deepseek-v4.1-flash:1017-cloud. Require supporting route metadata or explicit user-confirmed mapping, preserve both selectors, record provenance, and do not strip tags or namespace segments generically. An unknown alias stays unresolved; no inferred hosted eligibility or benchmark identity. Public catalog discovery alone does not establish actual routing, privacy, account quota, included subscription use, or a successful invocation. Do not assume current published plan credits apply to legacy plans.

## Next local read-only verification

Fetch only https://ollama.com/api/tags over HTTPS with certificate validation, no redirect, bounded timeout, no credentials and no automatic retry/fallback. Parse locally, report HTTP/parse success, record count, unique names and digest-field coverage only. If unavailable, report the blocker; do not silently substitute another endpoint or request authentication. Compare the public names with selected OpenCode route IDs locally, preserving tags and unresolved mappings; report only aggregate counts. No model invocation, downloads, local Ollama inventory or account changes. Public library metadata may be consulted separately when explicitly requested. Do not commit raw catalogs or benchmark data without confirmed rights.

Refresh is explicit, timestamped and previewed; preserve manual overrides and prior snapshots when incomplete. Source metadata and canonical mappings are independently versioned. Production automated catalog ingestion remains gated on current endpoint behavior, schema, rights and supported semantics.

## Remaining work

- Live local public catalog probe and freshness/coverage checks.
- Exact route mapping and hosted eligibility validation; manual unresolved correction.
- #10 privacy evidence, #11 bounded OpenCode prompt-only execution and #13 existing allowance validation remain separate gates. The user permits small tests on their configured Ollama-backed OpenCode routes, preferring inexpensive Flash models and avoiding Kimi unless specifically necessary. This does not authorize automatic paid fallback, retries, or arbitrary spending; confirm exact request scope, cost/allowance and privacy conditions before execution. No inference performed in this review.
