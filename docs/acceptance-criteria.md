# Requirements acceptance criteria

- [ ] A concise project vision and intended audience are documented.
- [ ] MVP user flow, inputs, outputs and non-goals are documented.
- [ ] The distinction between deterministic scoring, optional LLM assistance and external benchmark ingestion is documented.
- [ ] Privacy boundaries, missing-data policy, and cost limitations are explicit.
- [ ] External benchmark data terms and attribution requirements are identified as a prerequisite for ingestion/redistribution; the project's MIT source-code license does not automatically cover third-party data.
- [ ] Follow-up implementation issues are identified with small, independent scopes and dependencies.
- [ ] The requirements document records all ten confirmed questionnaire decisions, the phased MVP delivery plan and the Go/Bubble Tea modular-monolith architecture, distinguishing confirmed requirements from open technical design details.

- [ ] The requirements document describes per-agent annotations, optional AI benchmark suggestions, manual weight tuning, immediate local recalculation, and persistence of user-approved settings.
- [ ] The requirements document specifies that re-import and re-analysis preserve manual overrides unless explicitly replaced by the user.

- [ ] The requirements document defines accessible, contextual benchmark help including methodology, sources, score interpretation, limitations and agent-specific relevance.
- [ ] The requirements document defines German and English localization, persistent language selection, offline benchmark help and language-independent scoring.

- [ ] The requirements document defines global settings with independently selectable general-assistance and analysis/evaluation CLI/backend/model profiles (including disabled), local persistence, project inheritance/overrides, explicit operation overrides, no silent fallback or premium escalation, and a separate optional early-MVP test-judge profile linked to #2.
- [ ] The requirements document defines a versioned local YAML project file, save/open lifecycle, offline editing, and persistence of agent annotations and approved benchmark weights.
- [ ] The requirements document defines individual and bulk agent refresh, change previews, preservation of user overrides, and explicit re-analysis of changed agents.
- [ ] The requirements document defines safe local persistence, missing-source handling, and separation of secrets from portable project files.

- [ ] The requirements document defines provider/model/endpoint eligibility, organization-approved allowlists and denylists, independent privacy and cost filters, unknown metadata handling, policy precedence, exclusion explanations and no-match behavior.

- [ ] The requirements document defines independent geographic filters for developer origin, provider domicile, service availability, inference and applicable storage locations, including region definitions, routing/fallback behavior, unknown metadata and exclusion explanations.

- [ ] The requirements document defines assisted provider discovery, source-backed candidate metadata, deterministic pre-filtering, user review and adjustment, approved shortlist persistence, refresh diffs and a manual fallback without an LLM.

- [ ] The requirements document defines current Ollama Cloud catalog refresh and configured cloud access routes, model identity, user confirmation and refresh, with local-model support explicitly marked Coming soon and local inventory, downloadable models, hardware compatibility and local execution deferred.

- [ ] The requirements document defines pending review for missing filter metadata, explicit conditional inclusion in local benchmark comparisons, clear warnings, local persistence/revalidation of user decisions, and separation from verified policy compliance and missing benchmark measurements.

- [ ] The requirements document specifies developer-friendly filter terminology and simple defaults, with optional advanced restrictions, and avoids implying formal compliance certification.

- [ ] The requirements document defines OpenCode v2 and GitHub Copilot CLI as the MVP coding-CLI adapters, with independent capability and compatibility validation, optional model auto-discovery, project context, distinction between discovered availability and user-approved candidates, manual confirmation, refresh and fallback without inference or credential extraction.

- [ ] The requirements document defines arbitrary configured CLI backends, exact native model IDs, separate access-route/service/model identities, backend-grouped selection, alias handling and non-destructive refresh without credential extraction.

- [ ] The requirements document defines inherited upstream filters, scoped CLI inventories, provenance of user-declared restrictions, non-expanding metadata enrichment and separation of inventory membership from verified endpoint properties.

- [ ] The requirements document distinguishes catalog visibility from request-time eligibility, records restriction scope, supports read-only endpoint eligibility enrichment and avoids automatic inference probes or weakening routing restrictions.

- [ ] The requirements document defines a two-step backend then model selection workflow, grouped search and bulk actions, preservation of selections when navigating and refreshing, and explicit final shortlist confirmation.

- [ ] The requirements document specifies a single model-centric ranking of distinct evaluable model configurations with backend hints and route-specific details, a separate default-recommendation eligibility preference that never changes rank or score, selection of an economically suitable eligible default using the confirmed per-agent quality and reference-cost strategy (including outside the displayed top N), and a clear no-default state.

- [ ] The requirements document defines exact copy-ready native model references in grouped rankings, read-only import and comparison of current agent assignments, clipboard fallback and no automatic client configuration changes.

- [ ] The requirements document defines a common quality ranking with clearly flagged conditional comparison candidates, a separate current-model baseline even when it is not selected, reproducible evaluation inputs/versioning, and the cost-efficiency objective with detailed unresolved billing and scoring design explicitly deferred to bounded follow-up tasks.

## Review additions
- [ ] Cloud-only MVP and Coming soon local-model exclusion apply consistently across all adapters, settings and recommendations.
- [ ] Verify quality-rank invariance under cost, default eligibility and soft-preference changes; distinguish admission from scoring.
- [ ] Specify and test 70% default coverage, mathematical bounds, common-subset comparison, mandatory missing values, no-score states and comparable default-effort evidence.
- [ ] Define all-agent evaluation, project overview including unresolved agents, individual re-evaluation, collaboration context and warnings without fabricated team scores; manual and AI-disabled flows work.
- [ ] Specify reference-cost inputs, cache semantics, unknown costs, proxy provenance and RTK double-count protection; per-agent threshold and cost recommendation remain independent of rank.
- [ ] Define independent optional Test Judge profile and small prompt tests (#2), separate consent, safe bounded execution, manual entry of existing responses, manual and judge assessments kept separate from public scores, no silent fallback.
- [ ] Phase 0 checks document actual data/adapter capabilities and allowance reuse, limitations and manual alternatives before dependent implementation; tests and privacy gates are explicit.
- [ ] German/English glossary, keyboard usability, project overview, simple defaults and advanced settings separation are documented.
- [ ] The reviewed documents are merged and referenced by issue #1; follow-up implementation work is divided into bounded tasks with dependencies. No unchecked item is represented as completed.

- [ ] Optional OpenRouter benchmark-data credential setup explains purpose, supports skip/session-only/default or explicitly opted-in protected OS storage, masked input, read-only connection test, replacement and forgetting; verify no secret leakage, no plaintext fallback, no inference use, and offline/manual fallback. Validate supported platform stores and failure handling with synthetic keys only. Verify that session-only is preselected, shows no persistent location, and produces no persistent credential entry. For persistent storage, show the actual backend and exact non-secret logical entry identifier before opt-in and after saving, any reliably exposed applicable path, or an explicit unavailable/not-applicable message. Verify that the identifier resolves to the same entry for retrieval/removal; never reveal the secret.

- [ ] Storage transparency includes independent indicators for persistence, in-memory plaintext exposure, encryption at rest, HTTPS/TLS, and known platform memory protection limitations. Verify with synthetic credentials that secrets are not intentionally serialized or logged; do not claim that memory is fully encrypted, unswappable or completely erased without evidence. Validate best-effort cleanup and documented limitations in both storage modes.

- [ ] Evaluate session credential encryption between requests (Go AES-GCM preferred candidate, compare protected-memory libraries). Document key custody, nonce handling, plaintext lifetime, cleanup, platform limitations and failure handling using synthetic credentials. Do not claim protection from arbitrary process-memory access. Show actual implemented protections and residual risks, not merely the algorithm name; final design requires validation.
