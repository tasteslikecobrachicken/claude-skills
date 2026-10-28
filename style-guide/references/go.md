# Go

Tooling: **gofmt** for format (no configuration, not negotiable), **go vet**
plus **golangci-lint** for lint, `go test` for tests. Full project setup lives
in `project-scaffold/references/go.md`; this file is only about style.

## Mechanical — owned by the tools

gofmt has no options and never will. Every mechanical argument other languages
have is already settled here — don't reopen any of it in prose.

`.golangci.yml` (v2 schema):

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

formatters:
  enable:
    - gofmt
    - goimports
```

Formatters go under their own `formatters:` key in v2. Putting `gofmt` under
`linters.enable` is a hard validation error, not a warning.

`default: standard` is errcheck, govet, ineffassign, staticcheck and unused.
`all` enables mutually contradictory linters; don't.

## Judgment rules

### Naming

Short names, scoped to their lifetime. `i`, `r`, `buf` in a five-line function
are correct Go, not laziness; a package-level identifier needs a real name.

Receivers are one or two letters and identical across every method on the type.
Never `this` or `self`.

Don't stutter. The package qualifies the name, so it is `http.Server` not
`http.HTTPServer`, `user.New` not `user.NewUser`.

Acronyms keep their case: `userID`, `ServeHTTP`, `parseURL` — never `userId`.

No `Get` prefix on accessors. The method is `Name()`, the setter is `SetName()`.

Interfaces named for behaviour: `Reader`, `Formatter`, `-er` where it reads
naturally.

### Types

Accept interfaces, return structs. A concrete return gives callers everything;
an interface parameter lets them substitute.

Interfaces are defined by the consumer, in the consuming package, and are
small. An interface with eight methods exists to describe one implementation,
which is what a struct is for.

`any` only at genuine boundaries — decoding, reflection, printf-alikes.
Generics or a concrete type almost everywhere else.

The zero value should be useful where you can manage it. `bytes.Buffer` and
`sync.Mutex` work unconstructed, and types that follow suit need no `New`.

### Errors

Errors are values and get handled where they occur. Never `_ =` an error to
silence the linter — if it is genuinely ignorable, say why in a comment.

Wrap with `%w` and add what the caller can't know:

```go
if err != nil {
    return fmt.Errorf("load config %s: %w", path, err)
}
```

Message conventions matter because they compose: lowercase, no trailing
punctuation, no "failed to" — the chain already reads as a failure, and
"failed to failed to open" is what you get otherwise.

Compare with `errors.Is`, convert with `errors.As`. Never `==` on a wrapped
error and never string matching on `err.Error()`.

No `panic` in library code. Panic is for programmer error that makes continuing
meaningless — a nil dependency at construction, an impossible switch default.
Recover only at a process boundary, like an HTTP handler, and only to turn the
panic into a `500` and a log line.

### Structure

`context.Context` is the first parameter, named `ctx`, and never stored in a
struct. Storing it ties a request lifetime to an object lifetime, and the
cancellation stops meaning anything.

No `init()`. It runs at import in an order you don't control and can't test.
Do the work in `New` or in `main`.

Package-level mutable state is global state. Constants and truly immutable
values only.

Keep the happy path at the left margin. Handle the error and return; don't
`else` after a `return`.

Don't create a `utils` or `common` package. It becomes the place things go when
nobody decided where they belong, and it ends up imported by everything.

### Documentation

Doc comments on exported identifiers, beginning with the identifier's name:
`// Server handles incoming ferry bookings.` That prefix is what makes `go doc`
and pkg.go.dev read properly.

Package comment on one file per package. On `main`, it is usually noise — the
golangci config above excludes it there.

### Idioms

`defer` for cleanup, immediately after acquiring the thing. Remember it
evaluates arguments at defer time but runs at return — and that a `defer` in a
loop doesn't fire until the function ends.

Table-driven tests, with `t.Run` per case so failures name themselves.

Slices and maps are references. A function that appends to a caller's slice, or
writes to its map, is mutating shared state — say so in the doc comment or
copy.

Check the `ok` from a map lookup or type assertion whenever absence is
meaningful. A bare `v := m[k]` silently yields the zero value.

## Commands

```bash
gofmt -w .                    # autofixing
golangci-lint run --fix       # autofixing
gofmt -l .                    # report only; empty output is a pass
go vet ./...                  # report only
golangci-lint run             # report only
go test ./...                 # report only
```

`gofmt -l .` prints files needing formatting and exits 0 either way — check for
empty output, not the exit code.

## Sweep notes

gofmt is close to risk-free and most Go repos are already formatted, so the
mechanical commit is often empty. That is a good sign, not a problem.

`goimports` adds and removes imports. Removal is safe unless the import was
blank (`_ "github.com/lib/pq"`) — those exist purely for `init()` side effects
like driver registration, and dropping one breaks the program at runtime with a
message that names neither the import nor the file. Grep for blank imports
before accepting the commit.

`golangci-lint run --fix` only autofixes a subset; most findings are reports.
Expect the fix pass to leave the majority of the backlog for the judgment stage.

Enabling `errcheck` on a codebase that has ignored errors freely produces a very
large finding count. Report the number before fixing — each site is a real
decision about what should happen on failure, and it is not a mechanical sweep.
