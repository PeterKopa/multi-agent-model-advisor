package app

import (
	"bytes"
	"errors"
	"io"
	"strings"
	"testing"
)

// wantHelpText is the exact, stable help output. It is intentionally
// duplicated here: this is the contract asserted against the actual stdout.
const wantHelpText = `Multi-Agent Model Advisor

Usage: multi-agent-model-advisor [-h | --help] [--version]

Options:
  -h, --help     Show this help and exit.
      --version  Print the version and exit.

Running without any option starts the interactive TUI shell.
The bootstrap screen does not load any project data.
Press q or Ctrl+C to quit.
`

func TestRunFlagCases(t *testing.T) {
	tests := []struct {
		name           string
		args           []string
		wantExit       int
		wantStdout     string
		stderrContains []string
	}{
		{
			name:       "--help exits 0 with exact help on stdout",
			args:       []string{"--help"},
			wantExit:   0,
			wantStdout: wantHelpText,
		},
		{
			name:       "-h behaves exactly like --help",
			args:       []string{"-h"},
			wantExit:   0,
			wantStdout: wantHelpText,
		},
		{
			name:       "--version prints the exact version",
			args:       []string{"--version"},
			wantExit:   0,
			wantStdout: "multi-agent-model-advisor dev\n",
		},
		{
			name:       "--help wins over --version",
			args:       []string{"--help", "--version"},
			wantExit:   0,
			wantStdout: wantHelpText,
		},
		{
			name:           "unknown flag exits 2 and mentions flag and usage on stderr",
			args:           []string{"--verbose"},
			wantExit:       2,
			stderrContains: []string{"flag", "Usage:"},
		},
		{
			name:           "positional argument exits 2 with usage on stderr",
			args:           []string{"project.yaml"},
			wantExit:       2,
			stderrContains: []string{"unexpected", "Usage:"},
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			var stdout, stderr bytes.Buffer
			exit := run(tc.args, &stdout, &stderr, func(io.Writer) error {
				t.Errorf("startTUI must not be called for args %v", tc.args)
				t.FailNow()
				return nil
			})

			if exit != tc.wantExit {
				t.Errorf("exit code = %d, want %d", exit, tc.wantExit)
			}
			if stdout.String() != tc.wantStdout {
				t.Errorf("stdout = %q, want %q", stdout.String(), tc.wantStdout)
			}
			if len(tc.stderrContains) == 0 {
				if stderr.Len() != 0 {
					t.Errorf("stderr = %q, want empty", stderr.String())
				}
			} else {
				for _, want := range tc.stderrContains {
					if !strings.Contains(stderr.String(), want) {
						t.Errorf("stderr = %q, want it to contain %q", stderr.String(), want)
					}
				}
			}
		})
	}
}

func TestRunStartsTUIWithoutArguments(t *testing.T) {
	var stdout, stderr bytes.Buffer
	calls := 0
	var passedWriter io.Writer

	exit := run(nil, &stdout, &stderr, func(w io.Writer) error {
		calls++
		passedWriter = w
		return nil
	})

	if exit != 0 {
		t.Errorf("exit code = %d, want 0", exit)
	}
	if calls != 1 {
		t.Errorf("startTUI call count = %d, want 1", calls)
	}
	if passedWriter != io.Writer(&stdout) {
		t.Errorf("startTUI received a different writer, want the Run stdout")
	}
	if stdout.Len() != 0 {
		t.Errorf("stdout = %q, want empty for a successful stubbed start", stdout.String())
	}
	if stderr.Len() != 0 {
		t.Errorf("stderr = %q, want empty for a successful stubbed start", stderr.String())
	}
}

func TestRunReportsTUIFailure(t *testing.T) {
	var stdout, stderr bytes.Buffer
	sentinel := errors.New("tui stub failure")

	exit := run(nil, &stdout, &stderr, func(io.Writer) error { return sentinel })

	if exit != 1 {
		t.Errorf("exit code = %d, want 1", exit)
	}
	if stdout.Len() != 0 {
		t.Errorf("stdout = %q, want empty on TUI failure", stdout.String())
	}
	if !strings.Contains(stderr.String(), sentinel.Error()) {
		t.Errorf("stderr = %q, want it to contain %q", stderr.String(), sentinel.Error())
	}
}
