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
  # The single push allow: only "git push origin ?*" — the "?" matches exactly
  # one character, so the refspec after origin must be non-empty; a
  # whitespace-only tail ("git push origin ", trailing space, no refspec) does
  # not complete the match. Any push that does not name origin with a refspec
  # (another remote name, a bare push, a remote-only "git push origin") matches
  # no allow rule here and falls back to the project-level "git *" deny.
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
  # RTK mirror of the single push allow: "rtk git push origin ?*" — the "?"
  # demands a non-empty refspec, so "rtk git push origin " does not match.
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
  # above: only "git push origin ?*" (and "rtk git push origin ?*") passes
  # for this agent, and the "?" demands a non-empty refspec, so even a
  # whitespace-only tail after "origin" does not pass. Every other push shape
  # is handled in one of two ways:
  # 1. Fall-through to the project deny. Pushes that do not name origin with
  #    a refspec — another remote name ("git push upstream", "git push
  #    github") and the remote-only "git push origin" (with or without a
  #    trailing space, whose implicit refspec can resolve to a configured
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
  #    " main", ":main" and "heads/main" rules above deny pushes to main; and
  #    the blanket rules deny a "+" anywhere in the arguments and a ":" refspec
  #    with or without a remote, so a legal refname holding a plus sign is
  #    denied as a side effect — fail-closed for this agent, not left
  #    uncovered.
  # Consequence: this agent pushes "git push origin <branch>" or
  # "git push origin HEAD" — an explicit origin refspec every time, never
  # with a "-u" upstream option, never option-bearing, never to another
  # remote, never remote-only.
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
   refspec every time; the permission allowlist admits only
   `git push origin <refspec>` (or `git push origin HEAD`) — there is no push
   to another remote name, and any push without an explicit refspec does not
   match the allow and falls back to the project-level Git deny. The
   policy additionally re-denies option-bearing pushes (any argument starting
   with `-`, so no `-u` upstream option) and pushes to `main`.
   Describe the issue, the acceptance
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
