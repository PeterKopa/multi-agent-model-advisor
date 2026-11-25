# Roadmap

Reviewed requirements for [issue #1](https://github.com/PeterKopa/multi-agent-model-advisor/issues/1). Confirmed decisions are normative; open design checks are not verified capabilities.

## MVP delivery phases (confirmed question 9)

- Deliver the confirmed MVP incrementally through small, independently testable implementation issues with explicit dependencies and acceptance criteria. The phase boundaries are planning guidance, not a reason to postpone privacy, tests, or basic usability.
- Phase 1: local core engine, project persistence, model identity, benchmark ingestion/normalization, role weights, coverage and quality ranking.
- Phase 2: reference-cost engine, token usage profiles, manual token optimization settings, per-agent quality requirements, economic recommendations and Pareto comparison.
- Phase 3: public benchmark/model data adapters (OpenRouter and Hugging Face), OpenCode v2, GitHub Copilot CLI, Ollama Cloud catalog discovery and configured cloud access; implement and validate integrations incrementally. Local-model integration is post-MVP.
- Phase 4: optional AI assistance, separate LLM task profiles, role analysis and benchmark/weight suggestions.
- Phase 5: complete terminal UI, settings, project/model selection, results, contextual help and localization. Provide a minimal usable interface earlier and evolve it alongside the engine.
- A key product goal is to reuse the user's existing OpenCode and Ollama subscription allowances through the configured access routes and existing supported authentication, rather than require a new paid API key or additional account. This applies to eligible recommendations and optional, explicitly approved LLM assistance. Validate whether each route can actually use the existing allowance, respecting provider terms, quota limits and applicable policies; never silently fall back to separately billed usage. A direct Ollama inference adapter is not required if a supported configured OpenCode route already meets this goal. Do not conflate using existing allowances with estimating their consumption: the common token reference-cost approach from question 7 remains unchanged and automated allowance optimization is deferred.

## Out of scope

Implementing the scoring engine, provider adapters, live data ingestion, terminal interface and architecture/bootstrap belongs in separate follow-up issues. Go and Bubble Tea are confirmed; their detailed technical design and implementation remain separate tasks. Locally executed LLM support (Coming soon), large/automated test suites, measured team execution and automatic agent reconfiguration are not MVP implementation requirements. Small opt-in practical tests and the independent judge (#2) are now early MVP work.

## Revised delivery order

0. Capability and representative-data validation; record evidence, unsupported capabilities and privacy/cost constraints. No inference without approval.
1. Go/Bubble Tea bootstrap, minimal TUI, versioned YAML, fixtures, local scoring and model identity.
2. First safe OpenCode integration and independent Test Judge profile; small user-initiated prompt tests/manual and optional judge assessment (#2) as soon as bounded prompt-only execution is validated. Public scoring remains independent. If capability cannot be established, disable execution for that adapter and retain manual evaluation.
3. Reference-cost engine, token usage profiles, RTK settings, quality requirements and Pareto comparison.
4. Complete data-source and CLI adapters (OpenRouter, Hugging Face, Copilot CLI, Ollama Cloud); optional assistance and all-agent collaboration-context workflow.
5. Complete project overview, agent details, localization, privacy and integration tests, MVP release.

The earlier phase descriptions above identify workstreams; this revised dependency order takes precedence. Apply testing, privacy and basic UX from the first phase. Use small independent issues with explicit acceptance criteria; do not implement all features in one task.

## Post-MVP

Local models/inventory, hardware compatibility, quantization comparison and local compute pricing (see integrations.md); automatic RTK statistics; subscription quota optimization; Oh My Pi; automated or large benchmark suites, measured collaboration/team tests, calibrated outcome costs and any later explicit combination of practical and public benchmark scores. No automatic configuration changes.
