// Package tui implements the minimal terminal presentation layer of the
// Multi-Agent Model Advisor bootstrap phase: a single static screen with
// documented quit controls. It must stay free of application and domain
// knowledge: this package imports nothing from the application layer.
package tui

import (
	tea "charm.land/bubbletea/v2"
)

// screen is the exact content of the bootstrap screen. It is asserted
// character-for-character by the unit tests.
const screen = "Multi-Agent Model Advisor\n\n" +
	"Phase 1 bootstrap. No project data is loaded.\n\n" +
	"Press q or Ctrl+C to quit."

// Model is the minimal Bubble Tea model of the bootstrap shell.
type Model struct{}

// NewModel returns the initial model of the bootstrap shell.
func NewModel() Model { return Model{} }

// Init implements tea.Model. The bootstrap shell starts no commands, timers
// or I/O of any kind.
func (Model) Init() tea.Cmd { return nil }

// Update implements tea.Model. Pressing q or ctrl+c quits the program; every
// other message is ignored for now.
func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	if key, ok := msg.(tea.KeyPressMsg); ok {
		switch key.String() {
		case "q", "ctrl+c":
			return m, tea.Quit
		}
	}
	return m, nil
}

// View implements tea.Model. It renders the static bootstrap screen without
// styling, alternate screen or cursor management.
func (Model) View() tea.View { return tea.NewView(screen) }
