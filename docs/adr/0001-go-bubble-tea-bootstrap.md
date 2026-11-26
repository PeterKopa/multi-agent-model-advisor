# ADR 0001: Bootstrap with Go and Bubble Tea

## Status

Accepted — implemented as part of issue #27, dated 2026-11-26.

## Context

Go and Bubble Tea as the implementation stack for a modular monolith are confirmed in [architecture.md](../architecture.md); the exact versions, module path, package boundaries and supported platforms were deliberately deferred to this bootstrap task. Issue #27 establishes the offline application foundation: an executable with `--help` and `--version`, and a minimal TUI shell with documented quit controls. Startup and tests must require no network, no credentials, no inference, no project scanning and no configuration changes. This record pins the bootstrap decisions made there. It does not design the versioned YAML project file (#28), the domain contracts (#29), providers, scoring, persistence or any integration; those follow in separate issues.

## Supported platforms

- darwin/arm64 — manually verified locally (build, unit tests, CLI behavior).
- linux/amd64 — verified in CI.
- All other GOOS/GOARCH combinations — including windows/\*, darwin on non-arm64, and linux on non-amd64 — are not claimed to be supported at this stage. No build matrix or runtime verification exists for them; platform support statements must be widened only after they are actually verified.

## Versions and dependency pinning

- Go 1.27.4 — the `go` directive in `go.mod` and the CI setup pin exactly this version (locally verified as go1.27.4 darwin/arm64).
- charm.land/bubbletea/v2 v2.2.0 — stable release (verified stable on 2026-11-26 at <https://pkg.go.dev/charm.land/bubbletea/v2@v2.2.0>). The v2 API is used (`tea.KeyPressMsg`, `tea.Model` with a `View() tea.View` method, `tea.NewView`, and `Program.Run()` returning `(Model, error)`). Its module declares `go 1.26.0`, which 1.27.4 satisfies. It is imported with the conventional alias `tea`.
- `go.mod` and `go.sum` are the dependency pins: one direct UI dependency plus its transitive closure, committed to the repository and verified with `go mod verify`. CI enforces `GOFLAGS=-mod=readonly` and `go mod tidy -diff` so the pins cannot drift.
- No other direct dependencies: no lipgloss or bubbles (styling/components), no YAML library, no database driver, no HTTP clients, no external services. Each of these belongs to later issues with their own verification.

## Module path and executable

- Module path: `github.com/PeterKopa/multi-agent-model-advisor` — the repository name.
- Single executable: `cmd/multi-agent-model-advisor`. `main()` only calls `os.Exit(app.Run(os.Args[1:], os.Stdout, os.Stderr))`.
- CLI contract: `-h`/`--help` prints stable help to stdout and exits 0 (help wins over `--version`); `--version` prints `multi-agent-model-advisor <version>` to stdout and exits 0; unknown flags or positional arguments print an error plus usage to stderr and exit 2; running without any option starts the TUI, whose exit code mirrors the TUI result (0 on success, 1 on error).
- The default version is `dev`, overridable at link time with `-ldflags "-X github.com/PeterKopa/multi-agent-model-advisor/internal/app.version=<value>"`.

## Package boundaries

- `cmd/multi-agent-model-advisor` — process entry point only; no logic.
- `internal/app` — CLI flag parsing, exit-code mapping and startup; owns the version string; composes the presentation layer and starts the TUI.
- `internal/tui` — Bubble Tea presentation shell; an isolated leaf that must not import `internal/app` or any other internal package.
- `internal/domain` intentionally does not exist in #27. The acceptance criterion "Separate presentation from domain and application packages" is satisfied without speculative empty packages: presentation and application are separate packages with a directed dependency (`cmd` → `internal/app` → `internal/tui`), and no domain logic exists yet to factor out. Issue #29 owns the domain contracts and will introduce the domain packages together with those contracts.
- For this bootstrap, `internal/app` imports `internal/tui` and the Bubble Tea package to compose the program — the application layer composing the presentation layer. Composition stays one-directional, and the rule going forward is that future domain packages must never import Bubble Tea (`tea`): the dependency stays an application/presentation concern only.

## Offline and side-effect guarantees

- At runtime and in tests, the application performs no network access, no inference, no credential access, no project scanning and no configuration or file-system writes; `Init()` returns `nil`, so the model starts no commands, timers or I/O. The only keyboard events it acts on are the documented quit controls (`q`, `Ctrl+C`).
- The only network touchpoint while developing or building is module download (`go mod download`) as build-time setup. CI performs that single download step and then enforces `GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off` for module verification, format checks, vetting, race tests, tidiness checks and the build. CI is therefore not whole-job offline (toolchain and module downloads are setup), but every project-level step after setup runs offline.
- The quit controls are documented both in the screen itself and in `--help` output (`Press q or Ctrl+C to quit.`).

## Consequences and rationale

- A concrete, continuously enforced foundation exists: exact versions, module path, CLI contract and package boundaries are pinned and checked (format, vet, race tests, module verify/tidy, offline build, `--version`/`--help` assertions), so later issues extend the base instead of renegotiating it.
- The bootstrap stays minimal (two internal packages, one direct dependency). Later capabilities — YAML files, domain contracts, provider adapters, scoring, persistence — can each be added behind explicit interfaces with their own decision records.
- Tests exercise the CLI contract and the TUI model directly through an injected `startTUI` seam; no PTY is opened and no Bubble Tea program is run in tests, keeping the suite fast and environment-free.
- Risk: Bubble Tea v2 is a recent major version. Issues that add styling or components (lipgloss, bubbles) must verify v2 compatibility before adding dependencies.
- Risk: users on platforms other than darwin/arm64 and linux/amd64 run untested builds; platform claims must be re-verified before being documented as supported.
