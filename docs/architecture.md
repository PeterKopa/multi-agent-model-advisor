# Architecture

Reviewed requirements for [issue #1](https://github.com/PeterKopa/multi-agent-model-advisor/issues/1). Confirmed decisions are normative; open design checks are not verified capabilities.

## Implementation architecture (confirmed question 10)

- Use Go as the implementation language and Bubble Tea as the terminal UI framework. Build a modular monolith distributed as a single executable where supported, with no mandatory external server or separately installed database.
- Separate terminal presentation from application workflows and deterministic domain logic. Keep quality scoring, reference-cost calculations, eligibility/policy evaluation and local persistence independently testable. Keep external model/benchmark discovery, CLI integrations and optional LLM assistance behind explicit adapter interfaces; domain scoring must not depend on a particular CLI or LLM.
- Retain local YAML project files, local settings and separate public-data caches. Keep privacy and consent checks at the relevant application/adapter boundaries; no automatic inference, credential export or external transfer of private project content.
- Confirm exact Go and Bubble Tea versions, module/package boundaries, interface contracts, process execution behavior and supported platforms in a dedicated architecture/bootstrap task. Use incremental, independently testable implementation issues aligned with the agreed MVP phases rather than implementing the entire application in one issue.

## Architecture guardrails

Go + Bubble Tea modular monolith, local YAML and public cache, deterministic domain logic with no LLM dependency. Separate project/application workflows, quality, costs, policies, storage, inventory, optional assistance and optional test/judge execution. Use explicit interfaces, validated structured outputs, bounded CLI subprocesses and independent adapter capability flags. Test with fixtures and fake adapters before real external calls. No mandatory server or database installation. Versioned evaluation snapshots preserve inputs and results. Exact package layout, dependency versions and platforms remain bootstrap decisions.
