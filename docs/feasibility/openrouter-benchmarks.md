# OpenRouter benchmark data: feasibility evidence

Related to #4. Status: **partially verified**, not an ingestion implementation.

## Observed sample

On 2026-11-25, the user supplied the JSON output of a local, one-request Go probe targeting GET https://openrouter.ai/api/v1/benchmarks. The probe uses a credential supplied through standard input, standard TLS chain/hostname verification, TLS >= 1.2, no proxy, no automatic redirects and no intentional retry/fallback. The observed output parses successfully. This is evidence of data availability for that local session, not an independent audit of the request or the production security implementation. No terminal TLS log was supplied; certificate details, permission scope and actual charges were not independently measured. No real credential or raw response is included in this repository.

Response metadata: version v1; as_of 2026-11-25T12:00:35.358Z; model_count 350; source and task_type null. Local analysis counted 1,842 records and 350 distinct model_permaslug values.

| Source | Records | Distinct slugs |
| --- | ---: | ---: |
| artificial-analysis | 255 | 255 |
| design-arena | 1,279 | 175 |
| openrouter | 308 | 156 |

The distinct counts overlap across sources. They are not counts of confirmed distinct provider-native routes.

## Structure and limitations

- Common fields: source, model_permaslug, display_name. Source-specific structures must remain separate. Preserve unknown source types and nullable fields rather than assigning zero.
- Artificial Analysis: intelligence_index and engineering_index each non-null in 65/255 records; coding_index and agentic_index each non-null in 0/255. Pricing is non-null in 172/255. Other domain indices have variable coverage. Do not treat domain indices as direct measures of coding or agent performance.
- Design Arena: arena, category, elo, win_rate, avg_generation_time_ms and tournament_stats. Categories include codecategories (170 records), uicomponent (165), website (176) and other categories. Do not treat Elo as an accuracy percentage or combine different arenas without a defined methodology.
- OpenRouter: benchmark_type, accuracy or primary_score, total_tasks, avg_cost_per_task, last_run_timestamp; 149 gpqa_diamond records, 145 tau_bench_verified_airline, 14 search records across four benchmark types. Do not equate airline tasks with coding-agent success. Accuracy and primary_score have different semantics.
- Pricing in this sample is partial and not a complete route-specific billing or subscription model. Verify units and cache pricing separately under #6.
- No SWE-bench or Terminal-Bench result fields were observed in the sample. Specific coding/agentic data availability remains open; the endpoint supports query filters that require separate validation. Do not infer universal absence from one unfiltered response.
- Anonymous preview/contributor models and unresolved version/effort mappings are expected. Preserve exact native routes and unknown fields. Coverage must be calculated for the user-selected candidates with confirmed identity/configuration mappings, not speculative aliases. Practical tests under #2 are independent.
- No raw response is published pending data terms and redistribution review.

## Official interface and remaining checks

Official endpoint reference: https://openrouter.ai/docs/api/api-reference/benchmarks/get-benchmarks (consulted 2026-11-25). Documentation lists 30 requests/minute per key and 500 requests/day per account. These are documented limits, not measured limits. See also https://openrouter.ai/docs/api/api-reference/models/get-models and https://openrouter.ai/blog/tutorials/choose-best-ai-model/ for catalog and filtered task-type discovery. Validate supported filter behavior, permissions, fees, terms/attribution, score units, direction, benchmark versions and default reasoning effort before closing #4. No live model inference is required.

Reproduction: run the local read-only probe with a user-approved short-lived credential supplied via masked local input; inspect the JSON locally and count records by source, distinct slugs, non-null score fields and benchmark types. Do not share keys or raw responses in GitHub. The probe is not the production AES-GCM session or persistent storage implementation. Fail closed on errors.
