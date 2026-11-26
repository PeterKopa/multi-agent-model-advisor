// Package app implements the application layer of the Multi-Agent Model
// Advisor bootstrap: the CLI flag contract, startup and wiring of the
// terminal presentation shell. It depends on internal/tui; domain packages
// (owned by a later issue) must never depend on this or the tui package.
package app

import (
	"flag"
	"fmt"
	"io"
	"strings"

	tea "charm.land/bubbletea/v2"

	"github.com/PeterKopa/multi-agent-model-advisor/internal/tui"
)

// programName is the name of the executable and the report prefix used in
// output messages.
const programName = "multi-agent-model-advisor"

// version is reported by --version and defaults to "dev". Production builds
// override it at link time:
//
//	go build -ldflags "-X github.com/PeterKopa/multi-agent-model-advisor/internal/app.version=v1.0.0" ./cmd/multi-agent-model-advisor
var version = "dev"

// helpText is the stable -h/--help output. Its content is part of the CLI
// contract and is asserted exactly by the unit tests and CI.
const helpText = `Multi-Agent Model Advisor

Usage: ` + programName + ` [-h | --help] [--version]

Options:
  -h, --help     Show this help and exit.
      --version  Print the version and exit.

Running without any option starts the interactive TUI shell.
The bootstrap screen does not load any project data.
Press q or Ctrl+C to quit.
`

// usageText is the short usage line printed on argument errors to stderr.
const usageText = "Usage: " + programName + " [-h | --help] [--version]\n" +
	"Run '" + programName + " --help' for details.\n"

// Run is the process entry point. It parses args, honors the --help and
// --version flags and otherwise starts the minimal TUI shell. It returns the
// process exit code: 0 on success, 1 when the TUI fails to start, and 2 for
// usage errors.
func Run(args []string, stdout, stderr io.Writer) int {
	return run(args, stdout, stderr, runTUI)
}

// run contains the flag handling and exit-code mapping. startTUI is injected
// so tests can exercise Run's control flow without opening a terminal.
func run(args []string, stdout, stderr io.Writer, startTUI func(io.Writer) error) int {
	fs := flag.NewFlagSet(programName, flag.ContinueOnError)
	fs.SetOutput(stderr)
	fs.Usage = func() {
		fmt.Fprint(stderr, usageText)
	}

	var showHelp, showVersion bool
	fs.BoolVar(&showHelp, "help", false, "show help and exit")
	fs.BoolVar(&showHelp, "h", false, "show help and exit")
	fs.BoolVar(&showVersion, "version", false, "print version and exit")

	if err := fs.Parse(args); err != nil {
		// The error itself is already reported to stderr by the flag
		// package, together with our usage line.
		return 2
	}

	if fs.NArg() > 0 {
		fmt.Fprintf(stderr, "%s: unexpected positional argument(s): %s\n", programName, strings.Join(fs.Args(), " "))
		fs.Usage()
		return 2
	}

	switch {
	case showHelp:
		// Help wins over --version when both are requested.
		fmt.Fprint(stdout, helpText)
		return 0
	case showVersion:
		fmt.Fprintf(stdout, "%s %s\n", programName, version)
		return 0
	}

	if err := startTUI(stdout); err != nil {
		fmt.Fprintf(stderr, "%s: %v\n", programName, err)
		return 1
	}
	return 0
}

// runTUI builds the Bubble Tea program for the bootstrap shell and runs it
// against the given output writer. Program.Run returns
// (tea.Model, error) in Bubble Tea v2; the final model is not needed here.
func runTUI(stdout io.Writer) error {
	program := tea.NewProgram(tui.NewModel(), tea.WithOutput(stdout))
	if _, err := program.Run(); err != nil {
		return fmt.Errorf("run TUI: %w", err)
	}
	return nil
}
