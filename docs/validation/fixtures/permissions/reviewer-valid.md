---
description: Regression fixture: compliant Reviewer rules that the agent policy check must accept
mode: subagent
permissions:
  - action: edit
    resource: "*"
    effect: deny
  - action: subagent
    resource: "*"
    effect: deny
  - action: webfetch
    resource: "*"
    effect: ask
  - action: websearch
    resource: "*"
    effect: ask
---

# Fixture

This fixture is not a real agent definition. It exists so the offline validator
can prove the positive case of the agent policy check: deny rules for the edit
and subagent actions plus ask rules for web access contain no `effect: allow`
rule outside the `edit` and `subagent` actions, so a non-Git-Manager agent like
the Reviewer passes. Scratch copies created while reviewing belong under
`.tmp/` inside the worktree.
