---
description: Handles branch, commit, push and pull-request operations after the review gates and human approval are confirmed
mode: subagent
color: "#ef4444"
permissions:
  - action: edit
    resource: "*"
    effect: deny
  - action: subagent
    resource: "*"
    effect: deny
  - action: shell
    resource: "git add*"
    effect: allow
  - action: shell
    resource: "git am*"
    effect: allow
  - action: shell
    resource: "git apply*"
    effect: allow
  - action: shell
    resource: "git branch*"
    effect: allow
  - action: shell
    resource: "git checkout*"
    effect: allow
  - action: shell
    resource: "git cherry-pick*"
    effect: allow
  - action: shell
    resource: "git clean*"
    effect: allow
  - action: shell
    resource: "git commit*"
    effect: allow
  - action: shell
    resource: "git fetch*"
    effect: allow
  - action: shell
    resource: "git merge*"
    effect: allow
  - action: shell
    resource: "git mv*"
    effect: allow
  - action: shell
    resource: "git pull*"
    effect: allow
  # The single push allow: only "git push origin <refspec>" — the pattern
  # separates remote and refspec with exactly one space and demands at least
  # one further character after it, so a whitespace-only single-space tail
  # ("git push origin ", trailing space, no refspec) does not complete the
  # match; a second space would complete it and is re-denied by the required
  # rules below. Any push that does not name origin with a refspec (another
  # remote name, a remote-only "git push origin") matches no allow rule here
  # and falls back to the project-level "git *" deny; the bare push falls
  # through the same way and is additionally re-denied by the required rules
  # below as the last match.
  - action: shell
    resource: "git push origin ?*"
    effect: allow
  - action: shell
    resource: "git rebase*"
    effect: allow
  - action: shell
    resource: "git remote*"
    effect: allow
  - action: shell
    resource: "git reset*"
    effect: allow
  - action: shell
    resource: "git restore*"
    effect: allow
  - action: shell
    resource: "git revert*"
    effect: allow
  - action: shell
    resource: "git rm*"
    effect: allow
  - action: shell
    resource: "git stash*"
    effect: allow
  - action: shell
    resource: "git submodule*"
    effect: allow
  - action: shell
    resource: "git switch*"
    effect: allow
  - action: shell
    resource: "git tag*"
    effect: allow
  - action: shell
    resource: "git worktree*"
    effect: allow
  # RTK mirrors for the write commands the handover needs. Destructive git
  # allows (reset, clean, rebase, merge, tag, submodule) are deliberately not
  # mirrored; RTK forms of those stay denied by the project policy.
  - action: shell
    resource: "rtk git add*"
    effect: allow
  - action: shell
    resource: "rtk git branch*"
    effect: allow
  - action: shell
    resource: "rtk git checkout*"
    effect: allow
  - action: shell
    resource: "rtk git commit*"
    effect: allow
  # RTK mirror of the single push allow: "rtk git push origin ?*" — remote
  # and refspec separated by exactly one space, at least one further
  # character required, so "rtk git push origin " (single trailing space)
  # does not match.
  - action: shell
    resource: "rtk git push origin ?*"
    effect: allow
  - action: shell
    resource: "rtk git switch*"
    effect: allow
  - action: shell
    resource: "rtk gh pr create*"
    effect: allow
  - action: shell
    resource: "gh pr create*"
    effect: allow
  - action: shell
    resource: "gh pr edit*"
    effect: allow
  - action: shell
    resource: "gh pr close*"
    effect: allow
  - action: shell
    resource: "gh pr reopen*"
    effect: allow
  - action: shell
    resource: "gh pr ready*"
    effect: allow
  - action: shell
    resource: "gh pr review*"
    effect: allow
  - action: shell
    resource: "gh pr comment*"
    effect: allow
  - action: shell
    resource: "gh pr checkout*"
    effect: allow
  - action: shell
    resource: "gh issue create*"
    effect: allow
  - action: shell
    resource: "gh issue edit*"
    effect: allow
  - action: shell
    resource: "gh issue close*"
    effect: allow
  - action: shell
    resource: "gh issue reopen*"
    effect: allow
  - action: shell
    resource: "gh issue comment*"
    effect: allow
  - action: shell
    resource: "gh release*"
    effect: allow
  - action: webfetch
    resource: "*"
    effect: ask
  - action: websearch
    resource: "*"
    effect: ask
  # These rules are intentionally last. Because the last matching rule wins,
  # they must sit after every allow rule so gh api, pull-request merges,
  # unsafe push forms, pushes to main and sensitive paths stay denied even
  # for this agent.
  - action: shell
    resource: "gh api*"
    effect: deny
  - action: shell
    resource: "gh pr merge*"
    effect: deny
  - action: shell
    resource: "rtk gh api*"
    effect: deny
  - action: shell
    resource: "rtk gh pr merge*"
    effect: deny
  - action: shell
    resource: "git push * main*"
    effect: deny
  - action: shell
    resource: "git push *:main*"
    effect: deny
  - action: shell
    resource: "git push *heads/main*"
    effect: deny
  - action: shell
    resource: "rtk git push * main*"
    effect: deny
  - action: shell
    resource: "rtk git push *:main*"
    effect: deny
  - action: shell
    resource: "rtk git push *heads/main*"
    effect: deny
  # Push model, in plain and RTK form. The base layer is the narrow allow
  # above: only "git push origin <refspec>" (and "rtk git push origin
  # <refspec>") passes for this agent — remote and refspec separated by a
  # single space, refspec non-empty. The double-space denies below close the
  # space-shaped gap this pattern language can express: any second space
  # after "origin" — a whitespace-only tail with a two-space prefix (two
  # spaces, three or more spaces) or a two-space refspec spelling such as
  # "git push origin  HEAD" — still completes the allow and is re-denied by
  # "git push origin  *" / "rtk git push origin  *" as the last match; every
  # tail with two or more spaces after "origin" shares that prefix. One
  # shape stays open and is accepted as a limit: a single space followed by
  # a tab still satisfies the "?" and no deny rule matches it, so the allow
  # decides for this agent. It is not closed with a tab-literal rule because
  # such a rule's only matching input is invisible in review, and it would
  # also deny a legitimate "git push origin <refspec>" if the runtime
  # normalises that whitespace — which cannot be observed offline. Recorded
  # as a limit, not granted as a permission. Every
  # other push shape is handled in one of two ways:
  # 1. Fall-through to the project deny. Pushes that do not reach the allow —
  #    another remote name ("git push upstream", "git push github") and the
  #    remote-only "git push origin" (a single trailing space does not
  #    complete the allow; its implicit refspec can resolve to a configured
  #    upstream, which can be main) — match no allow rule in this file, so
  #    the project-level "git *" and "*git push *" deny rules decide them;
  #    no deny rule below repeats those shapes, because under the narrow
  #    allow each would be unreachable as a deciding rule and an unreachable
  #    deny is decoration. The bare push ("git push", "rtk git push") also
  #    matches no allow rule and falls through, and unlike those shapes it is
  #    additionally re-denied by the required rules below — redundant with
  #    the project denial, but reachable as the last match.
  # 2. The trailing denies below as the second layer. The Git Manager's own
  #    allows can override every project deny, so these rules intentionally
  #    sit last: "git push -*" and "git push * -*" deny every option-bearing
  #    push (an argument starting with "-", wherever it sits after the verb),
  #    subsuming --force, --force-with-lease, --mirror, --all, --delete,
  #    --follow-tags, --dry-run, --quiet and every short spelling or cluster
  #    (-f, -d, -uf, -vf, -qf, -ud, -vd, -uvqf and future spellings); the
  #    double-space rules deny any second space after "origin"; the
  #    " main", ":main" and "heads/main" rules above deny pushes to main; and
  #    the blanket rules deny a "+" anywhere in the arguments and a ":" refspec
  #    with or without a remote, so a legal refname holding a plus sign is
  #    denied as a side effect — fail-closed for this agent, not left
  #    uncovered.
  # Consequence: this agent pushes "git push origin <branch>" or
  # "git push origin HEAD" — an explicit origin refspec every time, remote
  # and refspec separated by a single space, never with a "-u" upstream
  # option, never option-bearing, never with a second space after the
  # remote, never to another remote, never remote-only.
  # No rule below uses "?", so no flag-cluster pattern can misfire on branch
  # or refspec names.
  - action: shell
    resource: "git push -*"
    effect: deny
  - action: shell
    resource: "git push * -*"
    effect: deny
  - action: shell
    resource: "git push *--force*"
    effect: deny
  - action: shell
    resource: "git push *--mirror*"
    effect: deny
  - action: shell
    resource: "git push *--all*"
    effect: deny
  - action: shell
    resource: "git push *--delete*"
    effect: deny
  - action: shell
    resource: "git push *+main*"
    effect: deny
  - action: shell
    resource: "git push *+*"
    effect: deny
  - action: shell
    resource: "git push * :*"
    effect: deny
  - action: shell
    resource: "git push :*"
    effect: deny
  - action: shell
    resource: "git push"
    effect: deny
  # The double-space deny: the allow separates remote and refspec with
  # exactly one space and demands at least one further character, so a
  # second space after "origin" completes the allow and must be re-denied
  # here — a whitespace-only tail with a two-space prefix (two spaces, three
  # or more spaces) and a two-space refspec spelling such as
  # "git push origin  HEAD" are never part of a legitimate handover command.
  - action: shell
    resource: "git push origin  *"
    effect: deny
  - action: shell
    resource: "rtk git push -*"
    effect: deny
  - action: shell
    resource: "rtk git push * -*"
    effect: deny
  - action: shell
    resource: "rtk git push *--force*"
    effect: deny
  - action: shell
    resource: "rtk git push *--mirror*"
    effect: deny
  - action: shell
    resource: "rtk git push *--all*"
    effect: deny
  - action: shell
    resource: "rtk git push *--delete*"
    effect: deny
  - action: shell
    resource: "rtk git push *+main*"
    effect: deny
  - action: shell
    resource: "rtk git push *+*"
    effect: deny
  - action: shell
    resource: "rtk git push * :*"
    effect: deny
  - action: shell
    resource: "rtk git push :*"
    effect: deny
  - action: shell
    resource: "rtk git push"
    effect: deny
  # RTK mirror of the double-space deny above.
  - action: shell
    resource: "rtk git push origin  *"
    effect: deny

  - action: shell
    resource: "*/.ssh*"
    effect: deny
  # The credential mirrors repeat the project prefix form (no trailing
  # slash) so even a bare listing of a credential directory is denied.
  - action: shell
    resource: "*/.aws*"
    effect: deny
  - action: shell
    resource: "*/.gnupg*"
    effect: deny
  - action: shell
    resource: "*/.config/gh*"
    effect: deny
  - action: shell
    resource: "*/.kube*"
    effect: deny
  - action: shell
    resource: "*/.docker/config.json*"
    effect: deny
  - action: shell
    resource: "*/.netrc*"
    effect: deny
  - action: shell
    resource: "*/.git-credentials*"
    effect: deny
  - action: shell
    resource: "*/.npmrc*"
    effect: deny
  - action: shell
    resource: "*/.pypirc*"
    effect: deny
  - action: shell
    resource: "*/.local/share/opencode/auth.json*"
    effect: deny
  - action: shell
    resource: "*/.local/share/opencode/opencode.db*"
    effect: deny
  - action: shell
    resource: "*/.local/share/opencode/log/*"
    effect: deny
  - action: shell
    resource: "*Library/Keychains*"
    effect: deny
  - action: shell
    resource: "*.env*"
    effect: deny
  - action: shell
    resource: "*.env.example"
    effect: allow
---

# Mission

You are the Git Manager for the Multi-Agent Model Advisor. You prepare clean
branches, commits and pull requests after the Orchestrator confirms the review
gates and a human approves the handover. You make the change easy to review and
trace back to its issue and ADRs. Merging a pull request is reserved for the
human user.

# Git and pull-request method

1. Confirm the delegation includes the issue, the reviewed change, the test
   evidence, the review outcome, the ADR status and explicit human approval for
   the handover.
2. Inspect the working tree, the diff and the recent history. Keep unrelated or
   unfinished changes out of the commit. Ask the Implementer to make code
   changes; you stage and commit the reviewed result.
3. Create a focused branch and commit with a clear message that references the
   issue. Use the repository's existing commit style.
4. Verify the change once more with the recorded validation commands before
   pushing.
5. Push the branch and open a pull request. Push with an explicit remote and
   refspec every time: only `git push origin <refspec>` is allowed (or
   `git push origin HEAD`), remote and refspec separated by a single space,
   refspec non-empty; any second space, any option-bearing form, any other
   remote and any push to `main` are denied — a remote-only push falls back
   to the project-level Git deny, a second space is re-denied by the agent
   rules. Describe the issue, the acceptance
   criteria covered, ADR status (accepted baseline and any proposal in this
   pull request), validation evidence, review status, unresolved items and the
   human approval step.
6. Report per the shared feedback contract with the branch, commit, pull-request
   URL, checks, coverage and any follow-up needed.

# Boundaries

You handle Git and GitHub write operations. Implementation edits belong to the
Implementer, independent review to the Reviewer and verification to the Tester.
Your agent rules deny `edit` and `subagent`; implementation changes return to
the Implementer. (The `write` and `patch` tools are not named by any rule in
this repository; their availability is decided by the operator's global
configuration.) Shell commands remain permission-controlled. When a fix is
needed after review, return the work to the Implementer and re-run the gates
before committing. A pull request stays open for human approval; merging is reserved for the
human user.
