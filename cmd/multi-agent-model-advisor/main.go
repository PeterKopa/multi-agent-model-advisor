package main

import (
	"os"

	"github.com/PeterKopa/multi-agent-model-advisor/internal/app"
)

func main() {
	os.Exit(app.Run(os.Args[1:], os.Stdout, os.Stderr))
}
