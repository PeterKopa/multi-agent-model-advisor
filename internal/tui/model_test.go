package tui

import (
	"fmt"
	"strings"
	"testing"

	tea "charm.land/bubbletea/v2"
)

// wantScreenText is the exact, stable screen content. It is intentionally
// duplicated here: this is the contract asserted against the actual view.
const wantScreenText = "Multi-Agent Model Advisor\n\n" +
	"Phase 1 bootstrap. No project data is loaded.\n\n" +
	"Press q or Ctrl+C to quit."

func TestInitReturnsNoCommand(t *testing.T) {
	if cmd := NewModel().Init(); cmd != nil {
		t.Errorf("Init() = %v, want nil so the bootstrap starts no commands or I/O", cmd)
	}
}

func TestViewHasExactScreenContent(t *testing.T) {
	got := NewModel().View().Content
	if got != wantScreenText {
		t.Errorf("View().Content = %q, want %q", got, wantScreenText)
	}
	if !strings.Contains(got, "q") {
		t.Errorf("screen %q must document the q quit control", got)
	}
	if !strings.Contains(got, "Ctrl+C") {
		t.Errorf("screen %q must document the Ctrl+C quit control", got)
	}
}

func TestQuitKeysReturnQuitCommand(t *testing.T) {
	tests := []struct {
		name string
		key  tea.KeyPressMsg
	}{
		{name: "q quits", key: tea.KeyPressMsg{Code: 'q'}},
		{name: "ctrl+c quits", key: tea.KeyPressMsg{Code: 'c', Mod: tea.ModCtrl}},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			m := NewModel()
			next, cmd := m.Update(tc.key)

			if _, ok := next.(Model); !ok {
				t.Errorf("Update(%s) returned model of type %T, want tui.Model", tc.name, next)
			}
			if cmd == nil {
				t.Fatalf("Update(%s) returned a nil command, want tea.Quit", tc.name)
			}
			// The command must produce a quit message; the command function
			// itself is not compared. The command is invoked exactly once and
			// the message stored, so it is not called twice.
			quitMsg := cmd()
			if _, ok := quitMsg.(tea.QuitMsg); !ok {
				t.Errorf("command produced %T, want tea.QuitMsg", quitMsg)
			}
		})
	}
}

func TestOtherMessagesAreNoOps(t *testing.T) {
	m := NewModel()
	beforeView := m.View().Content

	msgs := []tea.Msg{
		tea.KeyPressMsg{Code: 'a'},
		tea.KeyPressMsg{Code: 'c'},
		tea.KeyPressMsg{Code: 'x', Mod: tea.ModAlt},
		tea.WindowSizeMsg{Width: 80, Height: 24},
	}

	for i, msg := range msgs {
		t.Run(fmt.Sprintf("case-%d-%T", i, msg), func(t *testing.T) {
			next, cmd := m.Update(msg)

			if cmd != nil {
				t.Errorf("Update(%v) returned command %v, want nil", msg, cmd)
			}
			nextModel, ok := next.(Model)
			if !ok {
				t.Fatalf("Update(%v) returned model of type %T, want tui.Model", msg, next)
			}
			if nextModel != m {
				t.Errorf("Update(%v) changed the model, want it unchanged", msg)
			}
			if afterView := nextModel.View().Content; afterView != beforeView {
				t.Errorf("view after Update(%v) = %q, want unchanged %q", msg, afterView, beforeView)
			}
		})
	}
}
