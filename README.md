# Multi-Agent Model Advisor

A local-first advisor that recommends suitable LLMs for configurable agent roles based on task relevance, benchmark evidence, availability and cost. See [docs/vision-and-mvp.md](docs/vision-and-mvp.md) for the product goals.

## Status: Phase 1 bootstrap

This repository is at an early bootstrap stage (issue #27). What exists today:

- an executable with `--help` and `--version`,
- a minimal Bubble Tea shell screen with documented quit controls,
- offline build and offline tests once the module setup is done, with CI running its project-level checks with Go module/toolchain resolution disabled after one module-setup step.

Not implemented yet: model recommendations, YAML project files (#28), domain contracts (#29), provider adapters, quality scoring, inference, persistence or databases, and no external services of any kind. The delivery plan is described in [docs/roadmap.md](docs/roadmap.md).

## Prerequisites

- Go 1.27.4 (the exact version pinned in `go.mod`; rationale in the [ADR](docs/adr/0001-go-bubble-tea-bootstrap.md)).

## Supported platforms

- darwin/arm64 — manually verified locally.
- linux/amd64 (ubuntu-24.04) — target of the CI job; verified when the PR CI run is green.
- All other platforms are explicitly not yet supported or verified.

## Setup/build-time network versus runtime offline

- The Go toolchain and the module setup (the module download plus the `go mod tidy -diff` verification, or the first `go get`/`go test` after a fresh clone) need network once — that is build-time setup, not a runtime feature.
- At runtime the program is fully offline: it makes no network connections, needs no credentials, performs no inference, scans no projects and changes no configuration. CI verifies the project-level checks after the single online module-setup step (`go mod download` plus `go mod tidy -diff`), running them with `GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off GOFLAGS=-mod=readonly`, which disables Go module/toolchain resolution.
- These Go settings are not an OS-level network sandbox: CI does not prove network isolation by itself. See [Network isolation evidence](#network-isolation-evidence) below.

## Network isolation evidence

- CI is not an OS network sandbox. In the build-test job, `GOPROXY=off`, `GOSUMDB=off` and `GOTOOLCHAIN=local` disable the Go toolchain's module and toolchain resolution only; they do not block other sockets and do not prove that no connection was opened.
- The ci.yml workflow contains five separate jobs. Build-and-test is the only job whose project-level steps run with Go module/toolchain resolution disabled (after its module-setup step); the lint, govulncheck, Trivy and jactionlint jobs use the network deliberately to download tools, linters and scan/verify databases on the CI machine. That tooling traffic belongs to CI, not to the application, and does not change the application's runtime offline property.
- Runtime offline behavior rests on code inspection (the bootstrap contains no network code — no HTTP or dialing calls) and side-effect-free unit tests. CI does not prove OS-level network isolation: no reproducible OS-level network-sandbox experiment on a running program exists for this project (a reviewer attempt to impose one on macOS 27.2.1 did not succeed and is not claimed as evidence). No claim of OS network isolation is made here.
- A startup PTY smoke check of the program is recorded in the issue #27 PR discussion; it exercised CLI behavior only and is not evidence of network isolation. Application startup has no network code by inspection and test design.

## Build, test and verify

CI runs five separate jobs (each its own job, never a step inside another):

| CI job | Network use on CI |
| --- | --- |
| Build and test (offline after module setup) | one online module-setup step (`go mod download` + `go mod tidy -diff`); all following steps run with Go module/toolchain resolution disabled |
| Lint (golangci-lint) | downloads the pinned golangci-lint v2.15.0 binary |
| Vulnerability check (govulncheck) | downloads govulncheck v1.10.0 (module proxy) and the vulnerability DB |
| Security scan (Trivy) | downloads the Trivy v0.76.2 binary and its DB |
| Workflow lint (jactionlint) | downloads the pinned jactionlint v2.6.0 binary, then lints locally (`online: 'false'`) |

The local equivalents, all currently passing:

```sh
go build ./...
go vet ./...
go test ./...
go build ./cmd/multi-agent-model-advisor   # produces ./multi-agent-model-advisor (gitignored)
```

Module setup (build-time, needs network; `go mod tidy -diff` fetches the transitive test dependencies of dependencies that `go mod download` alone does not cover, so tidiness is verified while the proxy is still reachable):

```sh
go mod download
go mod tidy -diff
git diff --exit-code   # fails on go.mod/go.sum drift
```

Build-test-equivalent verification with Go module/toolchain resolution disabled (not OS network isolation), after that module setup. The exports are scoped to the subshell so they cannot leak into later commands:

```sh
(
  export GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off GOFLAGS=-mod=readonly
  go mod verify
  go test -race -count=1 ./...
  gofmt -l cmd internal   # must print nothing
)
```

Separate quality/security checks (run by their own CI jobs, not by build-test; they need network and tool installation themselves, so they are distinct from the offline verification above). `mise` is optional: the pinned tools can be installed by other means just as well.

```sh
mise x golangci-lint@2.15.0 -- golangci-lint run ./...
go install golang.org/x/vuln/cmd/govulncheck@v1.10.0
"$(go env GOPATH)/bin/govulncheck" ./...
mise x trivy@0.76.2 -- trivy fs --scanners vuln,secret,misconfig --severity HIGH,CRITICAL --exit-code 1 --ignore-unfixed --quiet .
mise x jactionlint@2.6.0 -- jactionlint
```

Trivy policy (deliberate, not exhaustive): the gate covers fixed HIGH/CRITICAL vulnerabilities plus secrets and misconfigurations at the selected severity; `--ignore-unfixed` excludes vulnerabilities with no available fix from the reported findings and the gate (the scan still runs), and severities below HIGH are not gated. A passing scan is evidence for this configured scope, not proof that no vulnerabilities exist.

## Run

```sh
./multi-agent-model-advisor --help     # usage + quit controls, exit 0
./multi-agent-model-advisor -h         # same as --help
./multi-agent-model-advisor --version  # "multi-agent-model-advisor dev" by default
./multi-agent-model-advisor            # starts the TUI
```

- Running without any option starts the interactive TUI. When no controlling terminal is available (CI, fully detached pipes), startup fails with status 1.
- In the TUI, press `q` or `Ctrl+C` to quit.
- Unknown flags or positional arguments exit with status 2 and print usage to stderr.
- If the stdout output of `--help` or `--version` cannot be written (e.g. a closed pipe), the program reports the failure to stderr as `<program>: write help|version: <err>` (best effort) and exits with status 1.

## Version injection

The default version string is `dev`. Production-style builds inject the version at link time:

```sh
go build -trimpath \
  -ldflags "-X github.com/PeterKopa/multi-agent-model-advisor/internal/app.version=v0.1.0-alpha.1" \
  -o multi-agent-model-advisor ./cmd/multi-agent-model-advisor
```

CI builds the same way with the injected value `ci-test` and asserts the exact `--version` and `--help` output, including empty stderr for `--help`.

## Architecture and packages

Bootstrap decisions (versions, platforms, boundaries): [docs/adr/0001-go-bubble-tea-bootstrap.md](docs/adr/0001-go-bubble-tea-bootstrap.md).
Overall implementation architecture: [docs/architecture.md](docs/architecture.md).

Packages, with dependency direction `cmd` → `internal/app` → `internal/tui`:

- `cmd/multi-agent-model-advisor` — thin executable entry point.
- `internal/app` — CLI flag contract (`-h`/`--help`, `--version`), exit-code mapping and startup; composes the TUI.
- `internal/tui` — the Bubble Tea presentation shell; a leaf package with no knowledge of the application layer.

## CI and privacy

CI (`.github/workflows/ci.yml`) runs five separate jobs: the **build-and-test** job — one online module-setup step (`go mod download` plus `go mod tidy -diff`) and then module integrity (`go mod verify`), formatting, vetting, race-tested unit tests, the offline build and the CLI's exact `--version`/`--help` contract, all with Go module/toolchain resolution disabled (`GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off GOFLAGS=-mod=readonly`) — plus four separate quality/security jobs that may use the network on the CI machine to download their pinned tools and databases: **Lint (golangci-lint)** v2.15.0, **Vulnerability check (govulncheck)** v1.10.0, **Security scan (Trivy)** v0.76.2 and **Workflow lint (jactionlint)** v2.6.0. Those downloads are CI tooling traffic and do not change the application's runtime offline guarantee. The module/toolchain-resolution settings are not an OS-level network sandbox, and CI does not prove offline/network isolation by itself; see [Network isolation evidence](#network-isolation-evidence). Consistent with the project's privacy goals ([docs/privacy-and-policies.md](docs/privacy-and-policies.md)), the current bootstrap performs no inference, touches no credentials, scans or writes no project files and changes no configuration.
