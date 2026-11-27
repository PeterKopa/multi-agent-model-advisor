# Architecture Decision Records

Architecture Decision Records (ADRs) capture decisions that shape the
Multi-Agent Model Advisor and its development workflow. ADRs make the accepted
architecture baseline explicit, reviewable and traceable to issues and
implementation work.

## Directory layout

| Path | Purpose |
| --- | --- |
| `docs/adr/README.md` | Lifecycle, baseline rules and authoring guidance |
| `docs/adr/template.md` | Template for new ADRs |
| `docs/adr/ADR-NNNN-short-title.md` | Individual decisions, numbered sequentially |

Use a zero-padded four-digit identifier, for example `ADR-0003`. Keep the title
short and imperative. A decision that changes an earlier decision gets a new ADR
and links to the superseded record; the earlier file stays in place.

## Status lifecycle

| Status | Meaning |
| --- | --- |
| `Proposed` | A draft decision is being prepared or discussed |
| `In Review` | The decision is under review, normally in an open pull request |
| `Accepted` | The decision is approved and merged into the default branch; it is part of the authoritative baseline |
| `Rejected` | The decision was considered and not adopted; the record and rationale remain for traceability |
| `Superseded` | A later accepted ADR replaced the decision; the record stays for history |

Allowed transitions:

```text
Proposed -> In Review -> Accepted
                     \-> Rejected

Accepted -> Superseded   (only through a later accepted ADR)
```

The frontmatter `status` records the author's declared state. The effective
state depends on the merge status described below.

## Authoritative architecture baseline

The authoritative baseline consists of **Accepted ADRs merged into the default
branch**. Agents read that baseline before planning, implementation, review and
handover. Accepted requirements in the existing product documentation remain in
force and are referenced by the initial baseline ADR.

## Open pull requests are proposals

New or modified ADRs in an **open pull request** are proposals, regardless of
their declared status. This includes a file whose frontmatter says `Accepted`:
until a human explicitly approves the pull request and it is merged, the
effective status is `Proposed` (or `In Review` when the pull request is under
active review), and the previously accepted baseline remains in force.

The workflow therefore:

- keeps the last merged accepted baseline authoritative;
- reports proposals separately from the baseline;
- does not let an open pull request silently change the architecture;
- requires explicit human approval and a merge before a proposal becomes
  baseline.

## Conflicts and pending decisions

Conflicts, missing decisions and proposals that would change an accepted
decision are escalated to a human. Record:

- the conflicting ADRs and the affected decision;
- the available options and their consequences;
- the impact of waiting or proceeding without a decision;
- the responsible human and the state before handover.

An agent does not resolve an architecture conflict by editing an accepted ADR
inside an open pull request and declaring it accepted. The Orchestrator records
the unresolved item in the ledger until a human decides.

## Linking issues and implementation decisions

Every ADR includes:

- the issue or issues that motivated the decision;
- the implementation area or workflow it governs;
- related ADRs, including `supersedes`, `superseded-by` and `conflicts-with`;
- the evidence or review that supports the decision.

Implementation reports include an `adr_alignment` section that names the
accepted baseline, any proposals and any conflict or decision needed. Pull
requests state whether they introduce a proposal, change the baseline or rely
on the existing baseline.

## Authoring and review

1. Copy `template.md` to `docs/adr/ADR-NNNN-short-title.md`.
2. Fill in context, decision, consequences, alternatives and links. Keep the
   decision testable and the consequences honest.
3. Set `status: Proposed` while drafting; use `In Review` when the pull request
   is under review.
4. Link the ADR from the issue and from the implementation plan or pull request.
5. Ask for independent review. The Reviewer checks that the decision is needed,
   the alternatives are credible and the consequences are acceptable.
6. A human approves the pull request. After merge, an ADR with `status: Accepted`
   becomes part of the authoritative baseline.
7. When a later decision replaces an accepted ADR, create a new ADR, set
   `supersedes`, and update the earlier ADR to `Superseded` with
   `superseded-by` in the same approved change.

## Initial records

ADR-0001 and ADR-0002 are introduced by the workflow change for issue #30.
The Go and Bubble Tea bootstrap decision from issue #27 was approved and
merged with PR #31, so that decision is already in force on the default
branch; ADR-0003 is the normalised record of that already-merged decision.
The normalised ADR-0003 file follows this ADR directory convention
only through this pull request: while that pull request is open the records
below are proposals under the rule above, including ADR-0003 even though its
decision is already in force, and they become part of the baseline when a
human approves and merges the pull request.

| ADR | Decision |
| --- | --- |
| `ADR-0001` | Use the reviewed issue #1 requirements as the initial architecture baseline |
| `ADR-0002` | Adopt a project-specific multi-agent development workflow |
| `ADR-0003` | Bootstrap with Go and Bubble Tea |
