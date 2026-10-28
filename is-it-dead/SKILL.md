---
name: is-it-dead
description: Analyze the code base for dead code and clean it up
---

# Is It Dead?

Find code that no longer does anything — unreachable statements, unreferenced
declarations, checks that can't fail, data nobody reads — and report it with a
confidence level. Delete only what the user approves.

The hard part is not spotting candidates. It is proving they are actually dead
before telling the user to delete them. Weight the work accordingly.

## 1. Scope the run

If the user named a path, analyze that path. Otherwise analyze the whole repo
minus vendored, generated and build output (`node_modules`, `vendor`, `dist`,
`build`, `target`, `.venv`, anything in `.gitignore`).

Work out three things first, because every later judgement depends on them:

- **Languages present**, by file count, so you know which analyzers apply.
- **Entry points** — `main`, CLI scripts, `bin`/`scripts` in the manifest, HTTP
  route handlers, test files, exported package surface, framework convention
  directories (`pages/`, `app/`, `migrations/`, `tasks/`). Anything reachable
  from an entry point is live.
- **Is this a library or an application?** For a library, the exported surface
  is consumed by code you cannot see — unreferenced exports are *not* dead.
  This single question changes most of the findings, so settle it early, from
  the manifest (`main`/`exports`/`publishConfig`, `[project]` + PyPI name,
  `crate-type`) and the README. If it's genuinely ambiguous, ask.

## 2. Honour the ignore markers

Before reporting anything, collect suppressions:

```bash
grep -rn "is-it-dead:" . --exclude-dir=node_modules --exclude-dir=.git
```

The marker is the literal token `is-it-dead:` followed by a directive, inside a
comment in whatever syntax the file uses (`//`, `#`, `--`, `/* */`, `<!-- -->`,
`"""`). Four directives:

| Directive | Effect |
| --- | --- |
| `is-it-dead: ignore` | On its own line: skips the next declaration or statement. As a trailing comment: skips that line. |
| `is-it-dead: ignore-start` / `ignore-end` | Skips everything between the two markers. |
| `is-it-dead: ignore-file` | Anywhere in the first 10 lines: skips the whole file. |
| `is-it-dead: ignore unused-export, useless-check` | Skips only the named categories from §4, in the same scopes as above. |

Anything after the directive is a free-text reason for humans; ignore it.

```python
# is-it-dead: ignore — called by the plugin loader via getattr
def on_shutdown(self): ...
```

Rules:

- Suppressed code is not reported, not ranked, not deleted. Say nothing about
  it beyond one summary line: `12 findings suppressed by ignore markers.`
- Never remove or edit a marker, and never move one to silence a finding.
- An unterminated `ignore-start` suppresses to end of file — report that as a
  problem with the marker, not as a finding about the code.
- If the user asks you to suppress something, add a marker with a reason rather
  than remembering it for the session.

## 3. Run the project's own analyzers, if it has them

Compilers and linters already know most of this, and they parse properly where
you are pattern-matching. Use one **only if it is already on `PATH` or declared
in the project's manifest/lockfile** — never install an analyzer, and never
fetch one implicitly (`npx --no-install`, not `npx`).

| Stack | Worth running |
| --- | --- |
| TypeScript | `tsc --noEmit --noUnusedLocals --noUnusedParameters`, `knip`, `ts-prune`, `depcheck` |
| JavaScript | `eslint` (`no-unreachable`, `no-unused-vars`, `no-constant-condition`) |
| Python | `ruff check --select F,ARG,ERA`, `vulture` |
| Go | `go vet`, `staticcheck` (U1000), `deadcode` |
| Rust | `cargo check` (the `dead_code` lint is on by default) |
| C# | `dotnet build` warnings (IDE0051, CS0162) |

Treat every hit as a **candidate**, not a finding. These tools are blind to the
same dynamic-reference cases you are — `vulture` flags framework hooks, and
`ts-prune` flags a library's entire public API. Each candidate still goes
through §5.

Where no analyzer applies, read the code and trace references yourself. On a
large codebase, don't try to hold it all at once: go package by package, and
prefer the categories in §4 that are provable locally.

## 4. What to look for

**Unreachable code** — statements after `return`/`throw`/`break`/`continue` or
a non-returning call; loop bodies that can't run (`while (false)`, iterating a
provably empty collection); `case` arms after a catch-all; code below an
unconditional early exit.

**Unreferenced declarations** — functions, classes, methods, constants, types,
imports, and whole modules with no reference anywhere. Also parameters never
read in the body, and private fields nobody touches.

**Write-only state** — a variable assigned (sometimes repeatedly) and never
read; a return value computed at real cost and always discarded; an
accumulator that never reaches an output.

**Useless checks** — conditions whose outcome is fixed at that point: a null
check on a value already dereferenced above, a re-test of a condition a guard
clause has settled, `if (x) { ... }` nested directly inside `if (x)`, a range
check subsumed by an earlier one, a type check on a parameter the type system
already constrains. Also both branches of an `if`/ternary being identical, and
a `catch` that only rethrows unchanged.

**Dead data** — enum members, config keys, database columns, struct fields,
error codes and translation strings that are written or defined but never read.

**Stale feature flags** — a flag hardcoded to a constant, or true/false in
every environment, and the branch that consequently never runs.

**Commented-out code** — blocks of real code left as comments. Version control
already has them.

Rank by what deleting actually buys: a dead module beats a dead local, and a
useless check that misleads a reader beats a harmless unused import.

## 5. Prove it before you report it

Search for the bare symbol name across **every** file type, not just the
language's source extensions — configs, CI YAML, Dockerfiles, shell scripts,
templates, SQL, Markdown and JSON all reference code by name.

```bash
git grep -n "symbolName"
```

Then rule out the ways a symbol gets used without a literal reference. Any one
of these means it isn't dead:

- **Dynamic dispatch by name** — `getattr`, `eval`, `Reflect`, method tables,
  `Object.keys` over a handler map, string-keyed registries. If the codebase
  does this anywhere, treat the whole symbol space it covers as reachable.
- **Registration side effects** — DI containers, decorators, annotations,
  plugin autoloading, `__init_subclass__`, import-for-effect.
- **Framework convention** — file-based routing, lifecycle methods, magic
  names (`setUp`, `componentDidMount`, `Handle*`), ORM/serializer fields, RPC
  or protobuf schema members.
- **Interface obligation** — a method that looks unused but implements an
  interface, satisfies a base class, or matches a callback signature.
- **Conditional compilation** — platform guards, build tags, `#ifdef`, code
  live only on another OS or in another build profile.
- **Cross-language reference** — a Python function called from a shell script,
  a Go symbol used via cgo, a JS function referenced in an HTML `onclick`.
- **Test-only usage.** Code exercised solely by its own tests is a real finding
  but a different one: report it as "used only by tests" and let the user
  decide. Do not count the test as proof of life, and do not delete it silently.

Then assign a confidence level and say what would have to be true for you to be
wrong:

- **Confirmed** — provable within the file or from the compiler. Unreachable
  statements, unused locals, identical branches.
- **Probable** — no reference found anywhere, and none of the §5 escape hatches
  apply.
- **Suspicious** — looks dead, but one of the escape hatches is in play, or the
  codebase uses dynamic dispatch and you can't rule it out.

If you can't get a candidate past **Suspicious**, say so plainly rather than
promoting it. A wrong deletion costs far more than a missed finding.

## 6. Report

Group by confidence, then by file. For each finding: location, category, one
line on why it's dead, and what removing it touches.

```
CONFIRMED (4)
  src/auth/session.ts:88  unreachable   3 statements after `return` on line 87
  src/util/parse.ts:14    write-only    `rawLen` assigned twice, never read

PROBABLE (2)
  src/legacy/migrate.ts   unused-module no importers; not an entry point or export

SUSPICIOUS (1)
  src/handlers/sync.py:40 unused-export no references, but handlers/ is loaded
                                        by name in registry.py:12 — verify first

7 findings suppressed by ignore markers.
```

Close with the single change you'd make first, and stop. Do not delete yet.

## 7. Delete on approval

On approval, delete only what the user approved, working one category or one
module at a time rather than in a single sweep.

- Remove the dependants your own deletion orphaned — imports, now-empty files,
  helpers whose only caller you just removed, config keys for a flag you just
  resolved. Then re-run §5 on those, since removals cascade.
- Resolving a stale flag means keeping the branch that ran and deleting the
  other — not deleting the check and leaving both.
- Leave behaviour identical. If removing a "useless" check changes what the
  code does in any input, it wasn't useless; put it back and re-classify.
- Run the project's build, type check, linter and tests after each group. If
  anything fails, revert that group and report it — a failure is evidence the
  code was live.
- `Suspicious` findings are never deleted without the user saying so explicitly
  for that specific finding.

Report what you removed and what you left, and suggest an `is-it-dead: ignore`
marker for anything the user declined, so the next run doesn't re-litigate it.
