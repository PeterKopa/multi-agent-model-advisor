---
id: ADR-0003
title: Bootstrap with Go and Bubble Tea
status: Accepted
date: 2026-11-26
issues: [27]
supersedes: []
superseded-by: null
conflicts-with: []
---

# Context

The fixture models a changed ADR-0003 in an open pull request: the pull
request modifies the merged bootstrap record — in the real change this is the
file-name and frontmatter normalisation. The record reuses the identifier of
the accepted merged record.

# Decision

Keep the bootstrap decision and change the record itself while the pull
request is open.

# Consequences

A modified ADR in an open pull request is a proposal regardless of its
declared status; the accepted merged baseline stays in force until a human
approves and merges the pull request.
