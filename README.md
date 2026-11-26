# Multi-Agent Model Advisor

A local-first advisor that recommends suitable LLMs for configurable agent roles based on task relevance, benchmark evidence, availability and cost. See [docs/vision-and-mvp.md](docs/vision-and-mvp.md) for the product goals.

## Status: Phase 1 bootstrap

This repository is at an early bootstrap stage (issue #27). What exists today:

- an executable with `--help` and `--version`,
- a minimal Bubble Tea shell screen with documented quit controls,
- offline build, offline test and offline CI verification.

Not implemented yet: model recommendations, YAML project files (#28), domain contracts (#29), provider adapters, quality scoring, inference, persistence or databases, and no external services of any kind. The delivery plan is described in [docs/roadmap.md](docs/roadmap.md).

## Prerequisites

- Go 1.27.4 (the exact version pinned in `go.mod`; rationale in the [ADR](docs/adr/0001-go-bubble-tea-bootstrap.md)).

## Supported platforms

- darwin/arm64 — manually verified locally.
- linux/amd64 — verified in CI.
- All other platforms are explicitly not yet supported or verified.

## Setup/build-time network versus runtime offline

- The Go toolchain and the module download (`go mod download` or the first `go get`/`go test` after a fresh clone) need network once — that is build-time setup, not a runtime feature.
- At runtime the program is fully offline: it makes no network connections, needs no credentials, performs no inference, scans no projects and changes no configuration. CI verifies the offline property after the single download step (`GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off`).

## Build, test and verify

```sh
go build ./...
go vet ./...
go test ./...
go build ./cmd/multi-agent-model-advisor   # produces ./multi-agent-model-advisor (gitignored)
```

Offline verification (after one `go mod download`):

```sh
export GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off GOFLAGS=-mod=readonly
go mod verify
go mod tidy -diff
go test -race ./...
gofmt -l cmd internal   # must print nothing
```

## Run

```sh
./multi-agent-model-advisor --help     # usage + quit controls, exit 0
./multi-agent-model-advisor -h         # same as --help
./multi-agent-model-advisor --version  # "multi-agent-model-advisor dev" by default
./multi-agent-model-advisor            # starts the TUI
```

- Running without any option starts the interactive TUI; it needs an interactive terminal. Without a TTY (pipes, CI), startup is refused and the program exits with status 1.
- In the TUI, press `q` or `Ctrl+C` to quit.
- Unknown flags or positional arguments exit with status 2 and print usage to stderr.

## Version injection

The default version string is `dev`. Production-style builds inject the version at link time:

```sh
go build -trimpath \
  -ldflags "-X github.com/PeterKopa/multi-agent-model-advisor/internal/app.version=v0.1.0-alpha.1" \
  -o multi-agent-model-advisor ./cmd/multi-agent-model-advisor
```

CI builds the same way with the injected value `ci-test` and asserts the exact `--version` output.

## Architecture and packages

Bootstrap decisions (versions, platforms, boundaries): [docs/adr/0001-go-bubble-tea-bootstrap.md](docs/adr/0001-go-bubble-tea-bootstrap.md).
Overall implementation architecture: [docs/architecture.md](docs/architecture.md).

Packages, with dependency direction `cmd` → `internal/app` → `internal/tui`:

- `cmd/multi-agent-model-advisor` — thin executable entry point.
- `internal/app` — CLI flag contract (`-h`/`--help`, `--version`), exit-code mapping and startup; composes the TUI.
- `internal/tui` — the Bubble Tea presentation shell; a leaf package with no knowledge of the application layer.

## CI and privacy

CI (`.github/workflows/ci.yml`) enforces formatting, vetting, race-tested unit tests, module integrity/tidiness, an offline build and the CLI's `--version`/`--help` contract. Consistent with the project's privacy goals ([docs/privacy-and-policies.md](docs/privacy-and-policies.md)), the current bootstrap performs no inference, touches no credentials, scans or writes no project files and changes no configuration.
