# User workflow and settings

Reviewed requirements for [issue #1](https://github.com/PeterKopa/multi-agent-model-advisor/issues/1). Confirmed decisions are normative; open design checks are not verified capabilities.

## Agent profile enrichment and benchmark tuning

1. Import agent definitions while preserving their original content.
2. Allow the user to add and edit separate, per-agent annotations (responsibilities, task boundaries, domain expertise, practical experience and preferences), without changing the imported definition.
3. Offer optional LLM-assisted analysis of the agent definition and selected annotations against the benchmark catalog. Return suggested benchmark selections, relative weights and short explanations of their relevance and limitations. External LLM analysis requires explicit user approval of the data to be transmitted.
4. Present the suggestions for review. The user can add or remove benchmarks, adjust individual weights, disable benchmarks with zero weight, and accept or reject suggestions. A manual workflow must also work without an LLM.
5. Recalculate rankings locally and deterministically as weights change; display the impact and missing-data coverage. Normalize relative weights for scoring and display effective percentages.
6. Persist user annotations and approved weights locally per agent. Keep AI suggestions distinguishable from user-approved settings, and never silently overwrite manual changes when re-importing or re-running analysis.

## Benchmark explanations and localization (DE/EN)

- Provide contextual help for each benchmark directly in the benchmark selection, weight editor and model comparison views (e.g. an info box, details panel or keyboard-accessible help action in the TUI).
- Explain what the benchmark measures, typical tasks, score meaning and units, whether higher or lower values are better, methodology/version, source link and known limitations. Distinguish official benchmark facts from AI-generated role-specific relevance explanations.
- Where a benchmark is recommended for an agent, show why it is relevant to that agent's responsibilities and what it does not measure. Make this information accessible without leaving the current workflow.
- Support German and English throughout the user-facing CLI/TUI, including menus, prompts, validation messages, benchmark descriptions and AI-generated explanations. Provide an explicit language setting, persist it locally, and allow switching languages without changing agent profiles, benchmark IDs, weights or scores.
- Preserve original benchmark/model names, imported agent definitions and user notes; do not automatically translate or modify them. Use a shared localization mechanism rather than hard-coded UI strings. Core benchmark help must be available offline from locally stored metadata; missing translations must be clearly identified, with English as fallback.

## Application settings and local project workspaces

### Global application settings
- Provide a Settings view with independently configurable LLM task profiles: General Assistance (simple tasks such as supported metadata interpretation and formatting) and Analysis/Evaluation (demanding agent-role analysis, benchmark relevance assessment and weight suggestions). Each profile allows explicit selection of an installed supported CLI adapter (or disabled), configuration context, configured provider/backend and exact native model reference, with executable path settings where needed. For the MVP, users may choose OpenCode v2, GitHub Copilot CLI or disabled independently per profile, with the exact supported backend/model reference and configuration context. Support different available routes per profile or reuse the same route. The architecture must allow additional CLI adapters later. Never require a premium model, assume quality from price, or automatically escalate to a more expensive route.
- Define which optional LLM operations use each profile; the core ranking, filter checks, numeric scoring, and ordinary local data processing remain deterministic and do not require LLM calls. Do not route a task to another profile silently on failure. Allow explicit per-operation override subject to the same restrictions and consent.
- Include an independently configurable Model Test Judge profile for the early optional MVP test workflow (#2). It can be disabled, explicitly reuse another profile or select its own supported hosted CLI/backend/model. Never invoke automatically or silently escalate; preview transferred data and reference costs separately.
- Show adapter availability and allow an explicit connection/capability test. Use the CLI's existing authentication where supported; never store credentials in portable project files.
- Persist global settings locally, including UI language, LLM task profiles and local data/cache preferences. Projects may inherit or explicitly override individual profiles using non-secret identifiers; preserve mandatory privacy, geographic and provider restrictions. Keep profile model selection independent of the candidate models being ranked.
- CLI execution and any external transfer of agent content require the established explicit user approval; opening a project or importing agents does not trigger LLM calls.

### OpenRouter benchmark-data authentication

- Add an optional global Settings → Benchmark Data → OpenRouter configuration with an explanation that the credential is for retrieving model metadata, benchmark evidence and reference pricing for local evaluation, not for LLM inference. Allow skipping setup and using cached/permitted alternative data or manual import.
- Ask explicitly whether to use the key for the current application session only (default), or persist it in the platform's protected credential store. Mask input and display only connection/status information; never prompt for secrets in project files, chat or command-line arguments.
- Session-only mode (default) retains the credential in application process memory, encrypted between requests using Go standard-library AES-256-GCM; do not serialize it. Decrypt only when needed for approved HTTPS authentication. Persistent mode also minimizes plaintext exposure when retrieving and using the stored credential. Clear references on disconnect/exit and avoid promising guaranteed memory zeroization. Persistent mode requires explicit opt-in and a supported OS-backed secure store (e.g. macOS Keychain, Windows Credential Manager, Linux Secret Service with a protected backend). Keep only non-secret settings/references in application configuration. If the selected secure storage is unavailable or locked, fail the save operation and show the reason; never automatically switch storage mode or fall back to plaintext or self-managed hardcoded encryption keys. The user may separately initiate a new session-only setup explicitly.
- Show a non-secret storage-location detail in Settings before confirming persistent storage and afterward. Session-only (default): display "Process memory — no persistent file or credential-store entry". Persistent: identify the actual OS credential-store backend, its logical store/collection where available, and the exact application-specific entry identifier (service/account or target name, as appropriate). Display the actual filesystem path only if a dedicated, non-secret path is reliably exposed by the backend; do not invent paths or imply that an OS-managed credential has its own file. Distinguish any non-secret application settings file from the secret's storage location. Show how the entry can be found and removed using the OS store without displaying the key. If a location is not exposed, say so explicitly. Never expose secret contents.
- Provide explicit read-only connection test, replace, disconnect and forget actions. Distinguish forgetting a locally stored credential from revoking the key at OpenRouter. Preserve previously cached non-secret benchmark data when disconnecting. Do not perform automatic external requests merely because Settings is opened.
- A credential supplied here is independent of all configured CLI/LLM task profiles and the Test Judge. It must not be reused for inference, passed to subprocesses or transmitted to another service.

- Show memory protection separately from storage mode. Session-only is not a guarantee of encrypted RAM, absence of OS swap or crash dumps, or complete erasure. Display the actual status of session credential AES-256-GCM encryption between requests, distinguishing the confirmed requirement from implemented and validated protection. Both modes may require plaintext temporarily for authentication. Display transport protection (HTTPS/TLS) separately from storage protection. Explain remaining risks in plain language.

- Show connection security in Settings: intended HTTPS origin, actual verified peer hostname, negotiated TLS version, certificate validation result, issuer, certificate validity period, effective trust source (system trust store), and effective proxy mode when available from the actual connection. Optional SHA-256 certificate fingerprint is diagnostic only, not a pin or proof of origin by itself. Label unavailable values explicitly and show the last successful verification timestamp; before a connection test, display "Not yet verified" rather than a success state. Explain that a system-trusted interception certificate can pass standard checks. On validation or other request failure show a blocked/failed status with a redacted reason; no proceed-anyway action, automatic retry or fallback. Preserve the last successful verification and cached data as historical information only. Offer explicit new attempts under the same policy or separately selected offline/manual workflows; never report stale data as a successful refresh. A successful read-only connection test is not evidence of data residency or ZDR.

### Local project lifecycle
- Support creating, naming, saving, Save As, opening and reopening multiple independent projects from local files (YAML is the canonical MVP project format, chosen for human readability and manual editing; JSON project-file support is out of scope for the MVP. This does not restrict importing external JSON agent configurations).
- A project file is self-contained for agent profile editing: include a schema version, project name/ID, agent source references and imported definition snapshots, stable agent identities, user annotations, AI suggestions with provenance, approved benchmark selections and weights, current model assignments and project-specific provider filters/preferences.
- Store references to the benchmark dataset/version and scoring configuration so the user can identify the data used for a ranking. Record the scoring algorithm version, effective weights, model/route mappings and relevant eligibility and price data versions or snapshots for each reproducible evaluation. When recalculating with updated inputs, identify changed inputs and distinguish the previous result from the new result; never silently overwrite or substitute historical evidence. Keep public benchmark caches separate from private project files; if a referenced dataset is unavailable, clearly indicate the limitation and do not silently substitute results.
- Allow re-import/update of all agents or individually selected agents from their original source. Match agents by stable identity, preview additions/changes/removals, and require explicit confirmation before destructive changes. Preserve annotations, approved weights and manual overrides. Mark outdated AI analysis when the definition changes; offer explicit re-analysis without automatically replacing approved weights.
- Allow projects to be reopened and edited offline, including when their original source is temporarily unavailable. Flag unavailable source references. Detect unsaved changes and protect existing data from failed imports or writes.
- Validate project files, provide actionable errors for unsupported schema versions or malformed files, and document migration expectations. Save safely (atomic replacement where supported). Do not include credentials or automatically upload project files. Warn users that project files can contain private agent instructions and notes before sharing or committing them.

## Two-step project model selection

- Step 1 (Select backends): list discovered CLI sources and configured backends with model counts. Let the user select which backends to consider; preserve their exact identifiers and distinguish multiple configuration contexts.
- Step 2 (Select models): show the offerings from the selected backends, grouped by backend, with searchable exact model IDs, optional filters, individual and per-backend bulk selection, and visible selected/total counts. Allow manual additions and conditional inclusion for unresolved metadata under the existing rules. A selected backend does not automatically constitute approval of every model.
- Allow navigation back to step 1 without losing individual model selections for retained backends. Confirm the final shortlist explicitly and persist it locally per project. On reopening or refreshing a project, preserve existing selections, show changes and require explicit approval of newly discovered models.
- Use the final confirmed model offerings as the candidate set for agent-specific evaluation. Perform costly or optional metadata enrichment only as needed; do not require complete provider metadata before the user can select models for comparison.

## Copy-ready recommendations and current agent assignments

- In each model-centric ranking and standard recommendation, display the exact native model reference for every selected access route (e.g. OpenCode's configured backend ID followed by the complete model ID). Place the copy action immediately after each displayed full native model reference (inline, not in a separate trailing column or details screen), including each backend route in grouped rankings. Provide an equivalent keyboard-accessible copy action in the TUI and a plain-text fallback when clipboard integration is unavailable. Never reconstruct references from display names or canonical benchmark IDs.
- Import current agent model assignments from the supported client configuration when available, including OpenCode JSON/JSONC; match exact native references to the corresponding configured access routes and agent identities. Display the currently assigned model alongside the recommendation, including when the current model is not selected, unavailable, or lacks benchmark evidence. When sufficient comparable benchmark evidence exists, calculate its score using the same role weights and scoring version as a separate reference baseline, even if it is outside the selected candidate set. Do not assign it a candidate rank or reintroduce it into recommendations unless explicitly selected. Do not silently substitute another route or model.
- Keep the workflow advisory and read-only: the developer can copy a recommended reference and manually edit their own client configuration. Optionally provide a copyable client-specific configuration snippet for an individual agent when the relevant schema is known; clearly distinguish examples from actual changes. Do not automatically rewrite source configuration, comments, agent definitions or assignments.
- Preserve route-specific default recommendation eligibility: highlight which exact references are recommended for standard use and which are comparison-only. If several eligible routes exist, let the user choose which reference to copy; do not silently select a route with unknown or incomparable costs.

## Project-wide evaluation and collaboration

- Evaluate all agents in the active project by default using a consistent dataset snapshot, each agent's own weights, requirements, filters and usage profile. Every agent appears even without evidence or an eligible recommendation. Allow individual re-evaluation; preserve unaffected results and mark dependent context/stale results explicitly.
- Project overview: current/recommended model, quality, coverage, comparable reference cost, change status and reason if no recommendation. Filter changed, unresolved or unmet requirements; drill into agent rankings and exact copy-ready routes. Open saved results without network calls.
- Support optional local notes on collaboration: responsibilities, dependencies/handoffs, expected shared artifacts and input/output formats, critical roles. Import only supported relationships; users can correct them. Do not infer facts solely from role names. Optional LLM analysis may propose collaboration-aware benchmark weights and requirements per agent, subject to preview, explicit approval and manual review. Do not silently change approved settings or transmit all agent definitions.
- Flag potential weak links based on actual declared requirements and evidence, not invented compatibility scores. Do not average heterogeneous role scores into a team-quality score or claim the individually best models necessarily work best together. Measured joint task performance is future work.
- A total reference cost is optional and only meaningful for a defined common workflow scenario with explicit per-agent token volumes/invocation counts and comparable rates. Mark incomplete totals partial; do not claim actual spend.

## Default journey

1. Create/open YAML project, import or manually define agents.
2. Select backends then cloud models, confirm shortlist; resolve only applicable filters.
3. Review benchmark selections/weights and requirements manually or with optional AI assistance. Apply inherited defaults and overrides.
4. Evaluate all agents; inspect overview, individual details and copy exact model IDs. Save results. Optional practical tests are a separate action, not triggered by scoring. Allow manual entry of previously obtained responses; judging these still requires explicit consent and a validated hosted judge route. See #2.

Keep advanced settings collapsed. Provide keyboard navigation, search, bulk actions, clear progress/cancellation/errors, contextual help and offline/manual fallback. Use English/German terms consistently:

| English | German |
| --- | --- |
| Data coverage | Datenabdeckung |
| Quality score | Qualitätswert |
| Quality ranking | Qualitätsrangliste |
| Recommended model | Empfohlenes Modell |
| Eligible as default | Als Standardmodell erlauben |
| Comparison only | Nur zum Vergleich |
| Access route | Modellzugang |
| Price-performance alternatives | Preis-Leistungs-Alternativen |
| Reference workload | Referenzverbrauch |
| Estimated reference cost | Geschätzte Referenzkosten |
| Source and date | Datenquelle und Stand |
| Coming soon | Demnächst verfügbar |
