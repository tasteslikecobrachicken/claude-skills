---
name: todoer
description: Find every TODO-style marker (TODO, FIXME, HACK, XXX, BUG, OPTIMIZE, REFACTOR, DEPRECATED) in the codebase and report them grouped by area and urgency. Use when the user asks to find, list, count, audit, analyze, or review the TODOs in a project.
---

# Todoer

Find the TODO-style markers a codebase has accumulated, work out which ones
still describe real work, and report them grouped by theme and ranked by what
fixing them actually buys.

The grep takes thirty seconds. Everything of value happens after it: throwing
out the matches that were never tasks, noticing that nine of the remainder are
the same task, and being honest that most of the survivors are not worth doing.
A raw list of 400 hits is something the user could have produced themselves.

## 1. Scope the run and learn the local dialect

If the user named a path, sweep that path. Otherwise sweep the whole repo.

Prefer `git grep` over `grep -r`: it only searches tracked files, so everything
in `.gitignore` — build output, caches, downloaded dependencies — is excluded
for free. Outside a git repo, use `rg` and exclude those directories by hand.

Before sweeping, find out which markers this project actually uses. The default
set is a starting point, not the answer:

- **Linter config is authoritative where it exists.** ESLint's
  `no-warning-comments` has a `terms` list; Ruff's `TD`/`FIX` rules and
  `flake8-todos` define the accepted forms. If the project configures these,
  use its list.
- **House conventions** — `@todo`, `NB:`, `WIP`, `TODO(alice)`, `TODO[PROJ-42]`,
  `REVISIT`, `SMELL`. A quick sample of a few source files shows the shape.
- **Ticket references** attached to markers. If most markers carry a ticket ID,
  that ID is the most useful grouping key you will get.

## 2. Sweep

```bash
python3 scripts/scan.py --text                      # whole repo
python3 scripts/scan.py src/billing --markers WIP,REVISIT
python3 scripts/scan.py                             # JSON, for working through
```

The script does the part a regex cannot: it tracks where comments and strings
actually begin and end per language, so a marker only counts when it is in a
comment. It also applies the file-level exclusions, clusters duplicate notes,
and dates every marker with `git blame`. Output carries `note`, `context`
(`code` / `docstring` / `prose`), `owner`, `tickets`, `key`, `age_days` and
`author`, plus counts of what it dropped and why.

Read `--text` first for shape, then the JSON when you start judging individual
markers. Under ~50 markers, read them all. Over a few hundred, work subsystem by
subsystem and say in the report that the run was partial.

Without Python, fall back to grep — same marker boundaries, none of the
comment-versus-string filtering, so expect to discard more by hand:

```bash
git grep -nIE '(^|[^A-Za-z0-9_])(TODO|FIXME|HACK|XXX|BUG|OPTIMIZE|REFACTOR|DEPRECATED)([^A-Za-z0-9_]|$)' \
  -- . ':(exclude)vendor' ':(exclude)third_party' ':(exclude)*.min.*'
```

## 3. Throw out what was never a task

Most of the difference between a useful report and a dump is here. The script
handles the mechanical half; the rest is yours. Each of these is a match, not a
finding:

| Hit | Why it isn't a task | Who catches it |
| --- | --- | --- |
| **Identifier** | The marker is a name, not a note — `XXXHandler`, `BUG_REPORT_URL`, a `Todo` model, a `bugs` field | Script: case-sensitive match bounded by non-word characters |
| **String literal / data** | The marker is the program's subject matter — a lint rule's term list, a parser test fixture, a scaffolding template, a regex hunting TODOs (including this skill's) | Script: counted under `rejected`. Fixtures that live in comments are still yours to spot |
| **Generated / minified / vendored** | Nobody edits it; the TODO belongs to a generator's template, a bundler, or somebody else's repo | Script: path, name, `@generated` banner, long-line test — see `skipped` |
| **Prose** | Docs *discussing* the convention: "leave a TODO comment when you can't finish" | **You.** Script tags `context: prose` and keeps them all |
| **Commented-out code** | A TODO inside a dead block is as dead as the block | **You.** Surrounding lines are commented-out statements |
| **Someone else's convention** | `TODO` in a `syntax: guessed` file may not be a comment at all | **You.** Check the line before trusting it |

Glance at `skipped` before moving on. It is the one place a wrongly-excluded
directory shows up, and a repo that keeps real source in `build/` will quietly
lose it.

**Prose is the judgment call the script deliberately refuses.** A `## TODO`
checklist in a README or a roadmap is a real task list and belongs in the
report; a sentence explaining the team's comment convention does not. Keep
doc-sourced tasks in their own group — they are usually project-level intent,
not code debt, and mixing the two distorts the ranking.

Report what was dropped and why. `312 hits → 46 markers` with the reason for the
gap is a finding in itself; a silent 46 looks like an error.

## 4. Read each survivor in context

A marker is a claim about the code that was true when someone typed it. Open
the surrounding code and decide which of three states it's in:

- **Live** — the claim still holds. This is a finding.
- **Stale** — already fixed, or about code, a dependency, a flag or a deadline
  that no longer exists. The work is deleting the comment. These are the
  cheapest wins in the whole report and worth calling out separately.
- **Unverifiable** — the note is too vague to act on ("TODO: clean up",
  "FIXME??"). Report as a group with a count; the honest recommendation is
  usually to delete them.

The script gives you `tickets`, `owner`, `author` and `age_days` already. The
one thing only reading can find is the **unblocking condition** — "remove once
we're on Node 18", "after the v2 migration" — and whether it has already been
met.

An unblocking condition that has already been met is the highest-value pattern
this skill finds. Check them — the repo usually answers it: the manifest says
which version is pinned, the flag is gone from config, the migration directory
is empty.

## 5. Cluster into themes

Before ranking anything, collapse the list. The script's `clusters` gives you
the first axis for free — it normalizes away punctuation, owners, ticket ids and
numbers, so "remove after Node 18" and "remove after node 20" land together. The
rest you find by reading:

| Axis | What it tells you |
| --- | --- |
| **Same text, many files** (`clusters`) | Copy-paste, or one missing abstraction. Usually one fix, not N |
| **Same ticket ID** | Already-tracked work; report as one item with its sites |
| **Same unblocking condition** | One dependency bump or migration closes the whole cluster — the best leverage in the report |
| **Same subsystem** | A module people are afraid of. The theme is the module, not the markers |
| **Same author and date range** | An abandoned sprint or a departed maintainer. Strong evidence the cluster is stale, not urgent |

Verify before collapsing: the same sentence in twelve files is sometimes twelve
independent problems, and sometimes a comment that was copied to places where it
never applied. Check two or three sites before reporting the cluster as one fix.

## 6. Rank by impact

Impact is what changes if the work gets done. Judge it from the text and the
code, never from the keyword — a `TODO` can say "auth bypass here" and a
`FIXME` can say "rename this variable".

In descending weight:

1. **Severity of the claim** — data loss, a security hole, a correctness bug or
   a known crash beats performance, which beats structure, which beats taste.
2. **Reach** — how much traffic, how many callers, how many users touch the
   code. A HACK on the login path outranks a FIXME in a debug script.
3. **Leverage** — one change that closes a whole §5 cluster.
4. **Cost now versus later** — an already-unblocked cleanup is nearly free
   today and grows harder as code accretes around it.
5. **Cost of leaving it** — does it block other work, or is it stable and
   ignorable? Plenty of markers are load-bearing notes, not debt.

**Age is not impact.** A five-year-old TODO is evidence that the codebase
tolerates it fine, which argues for deleting the comment more often than for
doing the work. Report age because it is informative; do not sort by it.

Say so when the answer is that nothing here is urgent. A report claiming ten
critical TODOs in a healthy repo is worse than useless — it gets the next one
ignored.

## 7. Report

Themes first, since they are what a raw grep can't give. Then the ranked list,
then the cheap wins, then the counts.

```
TODO audit — 46 markers in 213 files   (31 hits in strings, 14 files skipped)

THEMES
  Node 18 upgrade          9 markers, 6 files    already unblocked — engines: >=20
  PROJ-412 retry logic     4 markers, 3 files    ticket open since 2024-03
  billing/                 11 markers, 4 files   half the repo's FIXMEs live here

RANKED
  1. src/auth/session.ts:88   HACK    skips signature check when clock skews
                                      >5m — auth path, no ticket, 2y old
  2. src/billing/charge.py:210 FIXME  double-charges on retry; PROJ-412
                                      + 3 more sites, one fix
  3. src/api/list.go:44       TODO    unbounded query, no pagination
                                      — fine today, breaks past ~10k rows

CHEAP WINS (stale — delete the comment, no code change)
  9 × "remove after Node 18"    engines already >=20
  3 × "temporary, pre-launch"   launched 2023-11

LOW VALUE
  14 markers too vague to act on (7 bare "TODO", 4 "clean up", 3 "?")

Nothing here is an emergency. The auth HACK is the only one I'd schedule.
```

Close with the single marker you would fix first and why, and stop there.
Do not start fixing.

## 8. If asked to act

Take one theme or one marker at a time, smallest first, and run the project's
tests after each.

Two rules that matter more than the rest:

- **Never resolve a TODO by deleting the comment.** Deleting a stale comment is
  legitimate and needs the user's say-so; deleting a live one because the work
  looks tedious is silent data loss.
- **When you fix the code, remove the marker in the same change.** A resolved
  TODO left in place is how the next audit gets 312 hits.
