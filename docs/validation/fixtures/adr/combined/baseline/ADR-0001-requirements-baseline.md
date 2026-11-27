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

The fixture mirrors the real post-merge layout: a requirements baseline ADR
that a previous change already merged and approved. While a later pull request
is open, this record is part of the authoritative baseline.

# Decision

Keep the reviewed issue #1 requirements as the initial architecture baseline.

# Consequences

Agents read the requirements baseline before planning and implementation. An
open pull request can propose changes, but this record stays in force until a
human approves and merges that pull request.
