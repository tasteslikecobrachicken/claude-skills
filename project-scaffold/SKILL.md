---
name: project-scaffold
description: Generates a best-practice project scaffold — layout, build config, linting, formatting, tests and CI — for Python, JavaScript/TypeScript, Java, Go or Rust
---

# Project Scaffold

Stand up a new project that is already correct on its first commit: a real
source layout, a build that runs, a linter and formatter that agree, and at
least one test that passes.

The hard part is not knowing which files a project needs. It is not inventing
them. Every one of these ecosystems ships its own scaffolder, and that tool is
more current than any template written here — it knows today's edition, today's
default build backend, today's config schema. Use it wherever it exists, and
hand-write only what it leaves out.

Language specifics live in `references/`. Read the one file for the language in
play; don't read the others.

| Language | Reference |
| --- | --- |
| Python | `references/python.md` |
| JavaScript / TypeScript | `references/typescript.md` |
| Java | `references/java.md` |
| Go | `references/go.md` |
| Rust | `references/rust.md` |

If the user asks for a language not in that table, say so and stop rather than
improvising a scaffold you can't check.

## 1. Settle the brief

Five things, before touching disk:

- **Language and target version.** Default to the current stable release, not
  the newest. Say which you picked.
- **Project type.** This changes the layout more than anything else:

  | Type | What it implies |
  | --- | --- |
  | Library | Published surface, semver, no entry point, docs matter |
  | Application / service | Entry point, config loading, no published API |
  | CLI | Entry point plus argument parsing and an installable binary |

- **Names.** Most ecosystems need two, and conflating them is the single most
  common scaffolding error: distribution name vs import package (Python),
  module path vs binary name (Go), group + artifact + root package (Java),
  crate name vs binary name (Rust), npm package name vs exported entry.
- **Target directory**, and whether a repo already exists there.
- **Extras** — §2.

Ask only for what you can't infer. "A Python CLI called `ferry`" settles
language, type and name; don't re-ask them.

**Never scaffold into a directory that isn't empty without confirming first.**
Check before you write:

```bash
ls -A <target> 2>/dev/null; git -C <target> rev-parse --show-toplevel 2>/dev/null
```

If there are existing files, list what you'd add, name anything you'd
overwrite, and wait. Adding a scaffold to an existing project is a legitimate
request — silently clobbering its config is not.

## 2. Ask which extras are wanted

Nothing beyond source layout, build config, linter, formatter and tests is
assumed. Ask once, as a single multi-select question — don't drip-feed one
question per file:

| Extra | Offer when |
| --- | --- |
| CI workflow | Always, but detect the host first — `git remote -v`. Don't write a GitHub Actions file for a GitLab remote. |
| Pre-commit hooks | Always. Note that they run on every commit; some teams refuse them. |
| Dockerfile + `.dockerignore` | Applications and services. Skip for libraries unless asked. |
| README, LICENSE, `.editorconfig` | Always. Ask which licence; don't pick one for them. |
| Devcontainer | Only if the user raises it, or the repo already has one. |

Carry the answers into §4 — no extra beyond the chosen set, no matter how
standard it seems.

## 3. Check what's actually installed

Probe before planning, because the answer decides §4 or §5:

```bash
for t in <the language's tools>; do
  printf '%-16s ' "$t"; command -v "$t" >/dev/null 2>&1 \
    && "$t" --version 2>&1 | head -1 || echo MISSING
done
```

**Never install a toolchain.** Not with Homebrew, not with the ecosystem's curl
installer, not "just for the scaffold". Print the command the user would run
and let them decide — installing a language runtime changes their machine well
outside the scope of making a directory.

## 4. Scaffold with the native tool, then layer

Run the ecosystem's own scaffolder first. Then add what it omits — these tools
generate a working build, but none of them set up linting, formatting, CI or a
meaningful test.

Working order, so each step can be checked before the next:

1. Run the native init. Show the exact command; don't wrap it in a script.
2. Read what it produced (`git status --short`, or list the tree). Do not
   assume — versions change defaults, and the next steps depend on what's
   actually there.
3. Layer on config: lint, format, type-check, test runner.
4. Replace the placeholder source and test with something real for this
   project — a function that does one thing and a test that would fail if it
   broke. A generated `Hello, World!` test proves nothing.
5. Add the §2 extras.
6. `git init` if there's no repo, and write the `.gitignore` before the first
   commit so build output never enters history.

Don't fight the generated layout to match a template in the reference file. If
the tool's output differs from what's documented there, the tool is right —
note the difference and move on.

## 5. When the toolchain isn't installed

Write the files by hand. The reference files carry a full fallback layout for
exactly this case. It is a normal outcome, not a failure — say plainly that you
did it by hand and what the user should run once they have the toolchain.

Two hard limits to state rather than work around:

- **Binary artefacts can't be hand-written.** The Gradle and Maven wrappers
  include a `.jar`. You can write every other file, but the wrapper has to come
  from a real Gradle/Maven install. Say so instead of producing a build that
  fails on `./gradlew`.
- **Lockfiles can't be hand-written.** Never fabricate a `uv.lock`,
  `package-lock.json`, `go.sum` or `Cargo.lock`. Leave it to be generated on
  first install.

If you're unsure of a current config schema or a dependency's latest major
version, look it up rather than writing it from memory. A scaffold that fails
on first run is worse than no scaffold.

## 6. Verify it runs

A scaffold nobody ran is a guess. Run the full loop once — install, build,
lint, format check, test:

- Everything passes → say so, and give the exact commands you ran.
- Something fails → fix it and re-run. A failing scaffold ships only if the
  user asks for it as-is.
- Toolchain missing → state clearly that it is **unverified**, and list the
  commands the user should run first. Never imply you ran something you didn't.

## 7. Report

Short. The tree is visible on disk; don't re-print it in full.

```
Scaffolded: ferry (Python 3.13 CLI, src layout, uv)

  uv init --package + layered ruff, pytest, mypy
  Extras: CI (GitHub Actions), pre-commit, MIT licence
  Skipped: Dockerfile (declined)

Verified: uv sync, ruff check, ruff format --check, mypy src, pytest — all pass.

Next: uv run ferry --help
```

Close with the one thing to do next — the command that runs it, or the decision
you deferred. Then stop.
