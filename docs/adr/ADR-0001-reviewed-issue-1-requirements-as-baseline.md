---
id: ADR-0001
title: Use the reviewed issue #1 requirements as the initial architecture baseline
status: Accepted
date: 2026-11-26
issues: [1, 30]
supersedes: []
superseded-by: null
conflicts-with: []
---

# Context

Issue #1 consolidated the vision, MVP requirements, privacy and eligibility
rules, scoring methodology, user workflow, integrations, cost model and roadmap
for the Multi-Agent Model Advisor. The reviewed documents are the shared
reference for later implementation issues, but the repository did not yet have
an explicit architecture baseline that agents and reviewers could name.

# Decision

The reviewed documents in `docs/` are the initial accepted architecture
baseline for the project:

- `docs/vision-and-mvp.md`
- `docs/acceptance-criteria.md`
- `docs/architecture.md`
- `docs/cost-model.md`
- `docs/integrations.md`
- `docs/privacy-and-policies.md`
- `docs/roadmap.md`
- `docs/scoring-methodology.md`
- `docs/user-workflow.md`

Confirmed decisions in those documents are normative. Open design checks and
unverified capabilities remain open until a later accepted ADR or a Phase 0
evidence record resolves them. Later ADRs extend or amend this baseline through
the lifecycle in `docs/adr/README.md`.

# Consequences

- Agents, reviewers and implementers can name the baseline and check alignment.
- Existing accepted requirements are preserved instead of being re-decided in
  every issue.
- New decisions require an ADR and explicit human approval before they change
  the baseline.
- Phase 0 validation still determines which capabilities are verified; this ADR
  does not turn unverified assumptions into facts.

# Alternatives considered

- Treat the product documents as informal context only. Rejected because review
  and handover would lack a stable baseline.
- Copy all requirements into ADRs. Rejected because it would duplicate the
  normative documents and create drift.

# Links

- Issue: [#1](https://github.com/PeterKopa/multi-agent-model-advisor/issues/1),
  [#30](https://github.com/PeterKopa/multi-agent-model-advisor/issues/30)
- Related ADRs: `ADR-0002`
- Implementation or workflow: `docs/workflow/development-workflow.md`
- Evidence: reviewed requirements committed on the default branch

# Review notes

Introduced with the issue #30 workflow change. The ADR becomes part of the
authoritative baseline when a human approves and merges its pull request.
