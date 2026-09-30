package main

import (
	"encoding/json"
	"fmt"
	"os"
	"runtime/debug"

	"github.com/alecthomas/chroma/v2/lexers"
)

type request struct {
	Language string `json:"language"`
	Code     string `json:"code"`
}

type payload struct {
	Requests []request `json:"requests"`
}

type token struct {
	Text string `json:"text"`
	Raw  string `json:"raw"`
}

type response struct {
	Version string    `json:"version"`
	Results [][]token `json:"results"`
	Error   string    `json:"error,omitempty"`
}

// chromaVersion reports the chroma release this runner was built against, so
// a report says which grammars were actually measured.
func chromaVersion() string {
	info, ok := debug.ReadBuildInfo()
	if !ok {
		return ""
	}
	for _, dep := range info.Deps {
		if dep.Path == "github.com/alecthomas/chroma/v2" {
			return dep.Version
		}
	}
	return ""
}

func main() {
	var in payload
	if err := json.NewDecoder(os.Stdin).Decode(&in); err != nil {
		json.NewEncoder(os.Stdout).Encode(response{Error: err.Error()})
		os.Exit(1)
	}
	out := response{Version: chromaVersion()}
	for _, req := range in.Requests {
		lexer := lexers.Get(req.Language)
		if lexer == nil {
			out.Results = append(out.Results, nil)
			continue
		}
		iterator, err := lexer.Tokenise(nil, req.Code)
		if err != nil {
			out.Results = append(out.Results, nil)
			continue
		}
		var tokens []token
		for _, t := range iterator.Tokens() {
			tokens = append(tokens, token{Text: t.Value, Raw: t.Type.String()})
		}
		out.Results = append(out.Results, tokens)
	}
	if err := json.NewEncoder(os.Stdout).Encode(out); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
