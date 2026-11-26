---
description: Regression fixture: a Planner with an over-broad allow rule that the agent policy check must reject
mode: subagent
permissions:
  - action: "*"
    resource: "git notes*"
    effect: allow
---

# Fixture

This fixture is not a real agent definition. It exists so the offline validator
can prove the regression for over-broad allow rules: a Planner rule with
`action: "*"`, `resource: "git notes*"` and `effect: allow` must fail the
agent policy check. An `action: "*"` allow matches every action, including
`shell`, so it would override the project write restrictions for any command
string containing `git notes`, and pattern permits like this one broaden with
every new action OpenCode adds.
