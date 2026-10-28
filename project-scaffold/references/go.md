# Go

Tooling: the standard toolchain does most of it. **`go mod`** for
dependencies, **`gofmt`** for format (non-negotiable, no config), **`go vet`**
plus **golangci-lint** for lint, **`go test`** for tests. Resist adding
third-party frameworks — no assertion library, no mocking framework, no DI
container, unless the user asks.

## Native init

```bash
go mod init github.com/<owner>/<repo>
```

The module path is a URL, not a name. It must match where the code will
actually live or `go get` breaks for everyone else. Ask for it if the user only
gave a bare project name — guessing the owner is the most common mistake here.

`go mod init` creates exactly one file. Everything else is yours to write,
which is normal for Go.

## Layout

Go's layout is driven by visibility rules, not convention:

```
cmd/<binary>/main.go     # one directory per binary; thin, wires things together
internal/<pkg>/          # importable only within this module — the default home
<pkg>/                   # only for packages you intend others to import
go.mod
.gitignore
```

Rules that matter:

- **Default to `internal/`.** Anything outside it is public API you're
  committing to. Move packages out of `internal/` when there's a real consumer.
- **Skip `pkg/`.** It's a widely copied but contested convention that adds a
  directory level and communicates nothing `internal/` doesn't already.
- **A single-binary project doesn't need `cmd/`.** `main.go` at the root is
  fine and simpler. Add `cmd/` at the second binary.
- Package name is the directory name. Avoid `util`, `common`, `helpers` and
  `base` — they attract unrelated code.

## Tests

Table-driven, in the same package, in `<file>_test.go`:

```go
func TestParse(t *testing.T) {
	tests := []struct {
		name    string
		in      string
		want    Config
		wantErr bool
	}{
		{name: "empty", in: "", wantErr: true},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := Parse(tt.in)
			if (err != nil) != tt.wantErr {
				t.Fatalf("Parse(%q) error = %v, wantErr %v", tt.in, err, tt.wantErr)
			}
			if !tt.wantErr && !reflect.DeepEqual(got, tt.want) {
				t.Errorf("Parse(%q) = %v, want %v", tt.in, got, tt.want)
			}
		})
	}
}
```

Use `_test` as a package suffix (`package foo_test`) when you want to test only
the exported surface.

## golangci-lint

Config schema v2 — the `version` key is required, and **formatters live in
their own section**. Putting `gofmt` or `goimports` under `linters.enable` is a
hard validation error in v2, not a warning. Write `.golangci.yml`:

```yaml
version: "2"

linters:
  default: standard
  enable:
    - bodyclose
    - errorlint
    - misspell
    - revive
    - unconvert
  exclusions:
    rules:
      # revive's package-comments rule wants a doc comment on every package,
      # including main, where it reads as noise. Keep the rule for real
      # packages; drop it for entry points.
      - path: main\.go
        linters: [revive]
        text: package-comments

formatters:
  enable:
    - gofmt
    - goimports
```

`default: standard` is errcheck, govet, ineffassign, staticcheck and unused —
the right baseline. The other options are `all`, `fast` and `none`; `all`
enables mutually contradictory linters and is not a good default.

**Give every non-`main` package a doc comment**, or revive fails the scaffold on
its first run. The comment goes immediately above the `package` clause in one
file per package, and must start with the word `Package`:

```go
// Package parse converts raw config text into a Config.
package parse
```

Two traps in that config worth knowing before you edit it:

- **Don't reach for `linters.settings.revive` to turn off one rule.** Supplying
  *any* revive settings discards all of revive's default rules and keeps only
  the ones you list — so disabling `package-comments` that way silently
  disables the other 22 as well. Keeping the defaults while dropping one rule
  needs `enable-default-rules: true` plus an explicit `disabled: true` entry.
  The exclusion rule above sidesteps this entirely, which is why it's written
  that way.
- `issues.exclude-rules` is the v1 spelling. In v2 it's
  `linters.exclusions.rules`, nested under `linters`.

If golangci-lint isn't installed, `go vet ./...` plus `gofmt -l .` covers a
useful fraction of it with zero dependencies. Say that's what you did.

## Fallback — no Go installed

`go.mod` is simple enough to write by hand:

```
module github.com/<owner>/<repo>

go 1.23
```

Set the version to a real released Go version. Never hand-write `go.sum` —
it holds cryptographic hashes and a wrong one breaks every build.

## .gitignore

```gitignore
# Binaries — adjust to the actual binary name
/<binary>
*.exe
*.test
*.out
coverage.txt
vendor/
.env
```

Go builds to the module root by default, so the binary name lands next to
`go.mod`. Either ignore it by name or build with `-o bin/`.

## Verification loop

```bash
go build ./...
gofmt -l .            # prints files needing formatting; empty output is a pass
go vet ./...
go test ./... -race
golangci-lint run     # if installed
```

Always pass `-race` in CI and when verifying. It catches the class of bug Go
projects actually ship.

## CI (only if requested)

```yaml
name: ci
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: stable
          cache: true
      - run: go build ./...
      - run: go vet ./...
      - run: go test ./... -race -coverprofile=coverage.txt
      - uses: golangci/golangci-lint-action@v6
        with:
          version: latest
```
