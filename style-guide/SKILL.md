---
name: style-guide
description: Defines, applies and enforces coding style for Python, JavaScript/TypeScript, Java, Go or Rust — writes the project's style contract, generates new code against it, and runs a supervised pass over an existing codebase. Extensible to other languages.
---

# Style Guide

Make style explicit rather than inferred. Left to guess, code generation
averages the conventions of every codebase it has ever seen; the result is
plausible everywhere and correct nowhere.

## The split that governs everything here

Two kinds of style, two different enforcement mechanisms. Confusing them is the
main way a style guide rots.

| | Examples | Enforced by |
| --- | --- | --- |
| **Mechanical** | Line length, quotes, indentation, import order, braces | A formatter — deterministic, free, not worth an opinion |
| **Judgment** | Naming, error shape, when to abstract, docs, type strictness | A written guide — nothing else checks these |

**Never restate mechanical rules in prose.** Don't write "88 characters" in a
guide — write the formatter config that enforces 88, and let the tool win. Prose
that duplicates tool config is prose that goes stale silently.

Everything in `references/` is therefore judgment rules plus the formatter
config to install. Read the one file for the language in play; don't read the
others.

| Language | Reference |
| --- | --- |
| Python | `references/python.md` |
| JavaScript / TypeScript | `references/typescript.md` |
| Java | `references/java.md` |
| Go | `references/go.md` |
| Rust | `references/rust.md` |
| Anything else | `references/_template.md` — §6 |

## Where the rules come from

Two layers. Later wins, rule by rule — an override replaces only what it
speaks to, it does not discard the rest of the defaults.

```
references/<lang>.md       shipped defaults
<repo>/.claude/style.md    this project's overrides   <- wins
```

There is also a generated block in the project's `CLAUDE.md`. It is **a build
artifact, not a source**:

```markdown
<!-- style-guide:begin lang=python -->
...generated...
<!-- style-guide:end -->
```

It exists because a skill only loads when invoked, while `CLAUDE.md` is in
context every session — so the block is what actually shapes code you write
without asking for this skill. It is regenerated wholesale from the two layers
above.

**Never hand-edit between those markers.** A rule typed there is lost on the
next regeneration and, worse, disagrees with `.claude/style.md` until then.
Changes go in `.claude/style.md`; then regenerate. If you find the block already
edited by hand, say so and ask before overwriting — those edits are somebody's
intent and they belong in `.claude/style.md`.

## 1. Settle the brief

Which mode, and for which language:

| Ask | Mode |
| --- | --- |
| "set up a style guide", "define our conventions" | §3 Establish |
| "write X", "add Y" with the guide in force | §4 Generate |
| "format the codebase", "bring this repo in line" | §5 Sweep |

Detect the language from the repo rather than asking — `git ls-files` and the
presence of `pyproject.toml`, `package.json`, `go.mod`, `Cargo.toml`,
`pom.xml`/`build.gradle`. Ask only if it is genuinely mixed or absent.

Then check what already exists, before proposing anything:

```bash
ls .claude/style.md 2>/dev/null
grep -n 'style-guide:begin' CLAUDE.md 2>/dev/null
```

If both exist, this is not a fresh setup — go to §4 or §5 and leave the contract
alone unless asked.

## 2. Read, don't assume

Even with a style file present, the codebase is evidence. Before generating or
sweeping, read enough real code to see what the project actually does — three
or four representative files, not one. Where the code and the style file
disagree, the style file wins, but **say that you found the disagreement**. It
usually means either the file is aspirational or the codebase drifted, and the
user is the only one who knows which.

Never infer a rule from a single occurrence. Two files doing the same thing is a
convention; one file doing it is a coincidence.

## 3. Establish the style contract

The goal is a short file the team will actually read, not a transcription of the
defaults. **Record only deviations.** If the project is happy with the shipped
default for error handling, that section should not appear in `.claude/style.md`
at all — the default already covers it, and restating it creates a second copy
to maintain.

Ask once, as a single batched question, not one prompt per topic. The topics
worth asking about, because defaults genuinely differ by team:

| Topic | Why it varies |
| --- | --- |
| Type strictness | Gradual adoption vs. strict from day one |
| Docstrings / comments | Public API only, everything, or minimal |
| Error handling | Exceptions vs. result types; how much wrapping |
| Function/file size limits | Hard cap vs. smell test |
| Test conventions | Naming, layout, how much mocking is acceptable |

Anything the user doesn't have an opinion on, take the default and say so.
Don't manufacture a preference to fill a section.

Then write three things:

1. **`.claude/style.md`** — the deviations, with a one-line reason each. A rule
   without a reason gets argued about every six months.
2. **Formatter and linter config** — from the reference file, into the project's
   native config. This is where every mechanical rule lives.
3. **The `CLAUDE.md` block** — generated. Distil both layers into roughly 20–30
   lines of imperative rules. It must stand alone: assume the reader has not
   read `references/` and cannot. Lead with the deviations, then the defaults
   that matter most. Do not exceed ~40 lines; past that it stops being read.

Create `CLAUDE.md` if absent. If present, insert the block at the end and touch
nothing else in the file.

A generated block, for shape — deviations first, then the defaults that get
broken most often, all imperative, no rationale (the reasons live in
`.claude/style.md`):

```markdown
<!-- style-guide:begin lang=python -->
## Python style

Generated by the style-guide skill. Do not edit by hand — edit
`.claude/style.md` and regenerate.

Formatting is ruff's job; run `ruff format` rather than hand-aligning.

- Google-style docstrings on public API only (project deviation).
- `Result[T, E]` from `src/result.py` for expected failures; exceptions
  only for bugs (project deviation).
- No function over 60 lines (project deviation).
- Annotate every public signature. Never `Any` — `object` then narrow.
- Parameters take the widest type that works; returns the narrowest.
- No bare `except` / `except Exception`. Never `except: pass`.
- Re-raise with `raise ... from err`.
- `dataclass` or `TypedDict` for structured data, never a bare dict.
- Guard clauses over nesting; no mutable default arguments.
- Module level is definitions only — no I/O at import.
<!-- style-guide:end -->
```

Keep it to rules that change what gets written. A block nobody finishes reading
is a block that does nothing.

## 4. Generate new code

Read `.claude/style.md` and the language reference, then write. Two habits that
matter more than the rules themselves:

- **Run the formatter on what you wrote, before showing it.** Not as a final
  flourish — mechanical style should never be something you hand-tune or
  apologise for.
- **When the guide doesn't cover the case, match the surrounding file** rather
  than the wider ecosystem. Local consistency beats global correctness inside
  one file. If you had to make that call on something non-trivial, mention it —
  it may be a missing rule worth adding to `.claude/style.md`.

## 5. Sweep an existing codebase

The whole risk here is an unreviewable diff. A pass that changes formatting and
semantics in one commit gets rubber-stamped, and a regression inside it is
almost impossible to bisect. So: mechanical changes are automatic and bulk,
judgment changes are supervised and one category at a time.

### 5.1 Refuse to start on a dirty tree

```bash
git status --porcelain
```

Anything uncommitted → stop and say so. Not a formality: a formatter touching
every file makes existing uncommitted work unrecoverable by review.

Record the baseline before changing anything, so "the tests already failed" is a
fact rather than a claim:

```bash
<the project's test command>
```

If the suite is already red, say which tests fail and ask whether to continue.
Don't treat a pre-existing failure as your own.

### 5.2 Mechanical pass — automatic, one commit each

Per the reference file's commands. Format and autofix are **separate commits**,
because the first is provably behaviour-preserving and the second is not.

```
style: apply <formatter>          # whole tree, no review needed
style: apply <linter> --fix       # autofixable lint only
```

Re-run the tests after the autofix commit. Autofixers do occasionally change
behaviour — an unused-import removal that killed a registration side effect is
the classic. If the suite goes red, that commit is the cause; say so plainly
rather than hunting elsewhere.

On a codebase that has never been formatted, offer to add the format commit to
`.git-blame-ignore-revs`. A one-off reformat that destroys `git blame` for
everyone is a real cost and it is trivially avoidable.

### 5.3 Judgment pass — report first, then one category at a time

**Report before editing.** Group findings by rule, with counts and file
references — never a wall of individual diffs:

```
Judgment findings (no changes made yet):

  bare except swallows errors      12 sites   src/api.py:40, src/db.py:88, +10
  function over 150 lines           4 sites   src/report.py:112, +3
  missing return annotations       31 sites   across src/models/
```

Then take them **one category per commit**, stopping for approval between
categories. Each commit is one mechanical transformation applied consistently,
which is a diff a human can actually review. Re-run the tests after each.

Two rules that keep this honest:

- **Never bundle categories** to save round trips. The reviewability of the
  commit is the entire point of the exercise.
- **A category that can't be done safely gets reported, not attempted.**
  "Function over 150 lines" is not a mechanical fix — extracting helpers is a
  design decision. Offer the list and let the user direct it, or do them
  individually with real thought. Don't mass-extract.

Anything ambiguous, large, or touching public API: leave it, and list it.

## 6. Adding a language

Copy `references/_template.md` to `references/<lang>.md` and fill it in. The
template's section order is the contract the rest of this skill relies on —
§3 reads the formatter config from it, §5 reads the command list — so keep the
headings even where a section is thin.

Two failure modes to avoid:

- **Don't write rules from memory for an ecosystem you're unsure of.** Check the
  current formatter, the current lint defaults, the community style guide. A
  confidently wrong convention is worse than an absent one.
- **Don't pad the judgment section.** Ten rules that a reviewer would actually
  raise in a code review beat forty that nobody enforces.

For a one-off language that doesn't warrant a reference file, rules can go
straight into the project's `.claude/style.md` under a language heading.

## 7. Report

Short, and specific about what was *not* done.

```
Style contract: Python 3.13 (ruff, mypy strict)

  .claude/style.md    4 deviations from default
  pyproject.toml      ruff + mypy config
  CLAUDE.md           generated block, 26 lines

Swept: 2 mechanical commits (format, autofix), 1 judgment commit
  (narrowed 12 bare excepts). Tests green after each.

Left alone: 4 functions over 150 lines — extraction is a design call,
listed above. Say the word and I'll take them one at a time.
```

Never imply a verification you didn't run. If the test suite doesn't exist or
wouldn't run, say that rather than reporting a clean sweep.
