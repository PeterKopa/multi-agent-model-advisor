# Hosted reference pricing and token billing feasibility

Related to #6. Reviewed 2026-11-25. Status: documented feasibility, partial verification; no live billing or inference test.

## Source evidence

- OpenRouter documents a public model catalog (GET /api/v1/models) and provider-specific prompt caching. Catalog prices are reference data, not a guarantee of the tariff for a particular eligible endpoint. The model page for qwen/qwen4-max documents USD per million input/output and separate cache-read and creation rates for different durations. Preserve durations, route, context thresholds, rate units and source timestamp. Source: https://openrouter.ai/docs/api/api-reference/models/get-models ; https://openrouter.ai/qwen/qwen4-max/ ; https://openrouter.ai/blog/tutorials/prompt-caching-sticky-routing/
- OpenCode Go publishes shared allowance rules and model-specific equivalent monthly limits. The API documentation distinguishes balance charge, billing source, list cost (including peak/long-context tariffs), allowance consumption, and normalized billed tokens. Its normalized input excludes cache reads/writes; output includes reasoning. Cache-write durations may be separate. Go extra usage may draw on purchased balance when enabled. Sources: https://opencode.ai/docs/console/go/ ; https://opencode.ai/docs/console/api/inference/ ; https://opencode.ai/console/go
- Ollama's current public pricing lists USD per million input, cached input and output, with off-peak rates for certain models, applicable outside 12:00–18:00 UTC weekdays and on weekends. Current plans use included credits before purchased credits. Legacy plan terms may differ; do not infer their quota consumption or actual cost. Source: https://ollama.com/pricing
- Artificial Analysis local probe reported availability of input, output and cache rate fields on some records; exact tariff/tier and rights remain open (#19). Treat mapped rates as proxies, not charges on a different access route. No raw third-party response or restricted data is copied.
- Copilot subscription/request billing must not be converted into invented token rates. Use a documented compatible model price proxy or explicit user reference rate; keep actual subscription charges independent. Exact account terms and route eligibility remain unverified.

## Representative documented rate examples

Rates below are USD per million tokens, public snapshots reviewed 2026-11-25; not measured user charges. Model variant/route mapping and rights for automated extraction remain open.

| Source and offering | Input | Cache read | Output | Notes |
| --- | ---: | ---: | ---: | --- |
| Ollama deepseek-v4.1-flash peak | 0.30 | 0.006 | 1.20 | Public cloud list tariff |
| Ollama deepseek-v4.1-flash off-peak | 0.15 | 0.003 | 0.60 | Public cloud list tariff, time-dependent |
| OpenRouter qwen/qwen4-max | 1.50 | 0.075 | 4.50 | Catalog model reference; cache creation 1.875 (5 min), 3.00 (1 h); endpoint applicability unverified |

## Normalization proposal

Represent decimal rates with explicit currency and units; prefer fixed-point or exact decimal/rational arithmetic in Go, rounding at display boundaries. Preserve raw source fields and version of each billing transformation. Separate canonical model identity from exact offered route and tariff schedule. A price record includes source URL, retrieval timestamp, effective interval if known, model/version, route/endpoint, price type (documented route tariff / mapped proxy / user estimate), billing categories, duration/context/peak conditions and unknown fields. Do not mix categories from different providers to fabricate one complete tariff.

Use disjoint billed token categories: uncached input, cache read, each separately billed cache-write tier, output including reasoning where documented, and separate reasoning only where independently charged. Normalize provider-specific inclusive totals before calculation; reject negative or inconsistent counts. Additional request fees require explicit request count, and tier pricing requires context information at request level. Unknown applicable rates or conditions mean unknown total, not zero. A known zero or documented inapplicable category is distinct from missing data. Reference profiles describe a common hypothetical workload, not predicted model consumption. Compare only compatible currencies/volumes/semantics. Record explicit exchange rate/date if conversion is later supported.

Synthetic examples (not market rates):
- 400,000 uncached input at $1/M + 500,000 cache read at $0.10/M + 100,000 output at $4/M = $0.85. If the 100,000 output includes 30,000 reasoning tokens, do not add them again.
- If 900,000 total prompt tokens include 500,000 reads, normalize to 400,000 uncached input before billing, where provider semantics establish this partition.
- If cache write usage is positive and its applicable rate is missing, the full reference cost is unknown. If usage is explicitly zero, that category contributes zero.
- RTK: for a baseline of 400,000 uncached input, 50% optimizable share and 20% reduction of that share, the estimate is 360,000 uncached input. Do not reduce measured post-optimization tokens or other categories automatically.

## Subscription and user interface boundaries

Show reference workload costs separately from observed charges and quota usage. A $0 balance charge within Go allowance is not evidence of free or unlimited usage. Documented allowance metadata can inform future optimization, but quota conversion/optimization is outside the MVP; no claim of actual legacy plan cost. Never enable paid overage or switch routes automatically. User-selected price sources, explicit manual reference rates, and offline evaluation remain possible; do not silently substitute sources after failures. Keep quality rankings independent of prices and use only comparable known cost evidence for qualifying recommendations.

## Remaining gates

Validate actual public catalog payloads and exact route/variant, cache/effort and context tier applicability, source rights, versioned billing transformations and numeric precision tests before production adapters. Verify account-specific behavior separately under #13; no new live inference, subscription, or spending for this spike. No implementation or full tariff coverage established. Keep #6 open until acceptance criteria are satisfied.
