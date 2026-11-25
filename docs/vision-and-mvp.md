# Vision and MVP

Reviewed requirements for [issue #1](https://github.com/PeterKopa/multi-agent-model-advisor/issues/1). Confirmed decisions are normative; open design checks are not verified capabilities.

## Goal

Define the scope of Multi-Agent Model Advisor, a local-first tool that recommends suitable LLMs for configurable agent roles based on task relevance, benchmark evidence, availability and cost.

## Target audience

Software developers who use or want to adopt AI-assisted development, particularly those configuring coding agents or multi-agent workflows. The tool should support individual developers and development teams in selecting suitable models for their tasks without requiring AI research expertise.

## MVP requirements

- Import a local agent-role definition and a local model/benchmark dataset with source, model version, test configuration and timestamp.
- Allow role-specific benchmark weights (e.g. reviewer, planner, orchestrator, implementer, execution-only tester).
- Compute reproducible, explainable model rankings locally; report missing measurements and coverage rather than treating missing values as zero.
- Filter candidates by available providers and show quality and cost separately; use a common pay-per-token reference-cost model for hosted offerings; distinguish reference estimates from actual billing and unknown costs. Evaluate hosted models only; local model execution support is Coming soon.
- Display per-role recommendations, raw benchmark comparisons and the reasons for rankings in a terminal interface.
- Keep agent definitions and project context local by default. Network access for public data refresh and optional LLM-assisted role analysis must be explicit; no automatic transmission of private project context.
- Keep the ranking engine independent of an LLM. Target OpenCode v2 and GitHub Copilot CLI as the coding-CLI integrations for the MVP, with OpenCode first and Copilot next, for supported read-only agent/configuration import, model discovery and optional user-approved LLM assistance. Validate capabilities independently; do not require unsupported operations to behave identically. Keep manual workflows available. Oh My Pi is a preferred post-MVP integration candidate, subject to separate capability and compatibility evaluation.

## Scope and success

Evaluate every agent in a project together, preserving role-specific settings and showing individual recommendations in a project overview. Consider user-declared collaboration and handoff context when suggesting role requirements. Include optional small practical prompt tests and independent rubric-based LLM judging early in the MVP, following #2 with manually supplied responses as fallback and direct execution only after safe prompt-only execution is validated. Keep practical judgments separate from benchmark scores. Actual end-to-end team effectiveness is not established by individual model scores.

Local-first refers to application storage, scoring and offline operation. Existing OpenCode and Ollama allowances should be reusable via supported configured routes. Do not require new paid API keys, silently charge another route, distinguish personal/work accounts, or automate agent reconfiguration. See [roadmap](roadmap.md) for explicit future scope.
