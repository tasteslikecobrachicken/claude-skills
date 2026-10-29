---
name: claude-suggest
description: Reviews CLAUDE.md files — repo-level or the user's global one — and proposes specific edits, backed by evidence mined from past session transcripts showing what the user repeatedly has to restate or correct. Use when asked to improve, audit, tidy or update a CLAUDE.md.
---

# Claude Suggest

A CLAUDE.md is always-on context: every rule in it is paid for in every session,
whether or not it changes anything. This skill audits that file against two
sources of evidence — the text itself, and what the user has actually had to
type over and over — and proposes edits for approval.

**Never edit a CLAUDE.md without showing the proposal first.** These files
encode somebody's deliberate intent. A rule that looks redundant is often load
bearing for a reason that isn't visible in the text.

## The two signals, and how much to trust them

| Signal | Source | Strength |
| --- | --- | --- |
| **Static** — rules that are vague, duplicated, stale, or formatter-enforced | The file | Reliable. Judge from the rubric. |
| **Usage** — constraints the user restates across sessions | Transcripts | Suggestive. A pattern, never a proof. |

Be honest about the second one. Transcript volume is usually small — dozens of
prompts, not thousands — and heuristics over that are noisy. Usage evidence is
good for *raising a candidate*; the rubric and the user decide whether it
becomes a rule. Never present a 2-session phrase match as a settled finding.

## 1. Settle scope

| Ask | Target |
| --- | --- |
| "review our CLAUDE.md", "audit this repo's rules" | `<repo>/CLAUDE.md` |
| "improve my global instructions" | `~/.claude/CLAUDE.md` |
| "improve how you work with me" | Both — they interact |

Check what exists before proposing anything:

```bash
ls -la ./CLAUDE.md ./.claude/CLAUDE.md ~/.claude/CLAUDE.md 2>/dev/null
```

Read every file in scope in full. If both a repo and a global file exist, read
both even when only one is the target — the most common real finding is a rule
sitting at the wrong level, and that is invisible if you only read one.

## 2. Static review

Against `references/rubric.md`. Work rule by rule and record, for each finding,
the rule text and what is wrong with it.

Two things to verify rather than assume:

- **Stale references.** Any rule naming a file, command, directory or flag —
  check it still exists. A rule pointing at a deleted script is worse than no
  rule, because it gets followed.
- **Conflicts.** Between repo and global, and within a file. Conflicts are the
  highest-value finding and the one the user is least likely to have spotted.

## 3. Usage evidence

**Ask before reading transcripts.** They contain everything the user has ever
typed. State the scope and get a yes:

> This reads ~N prompts from M projects under `~/.claude/projects/` to find
> constraints you repeat. Nothing leaves the machine, and no prompt text gets
> written into CLAUDE.md — only the rule it implies. Scan?

If declined, say the findings are file-only and continue at §4.

```bash
# Global CLAUDE.md — evidence across every project
python3 scripts/mine.py --scope global --text

# Repo CLAUDE.md — this project only
python3 scripts/mine.py --scope project --text

# Full structured output, including every prompt
python3 scripts/mine.py --scope global --since 90
```

The script filters transcript JSONL down to genuinely typed prompts — dropping
tool results, subagent sidechains, meta records and skill boilerplate, and
stripping the `<system-reminder>` / `<ide_opened_file>` blocks the harness
prepends to real prompts. It reports three things:

| Output | Means |
| --- | --- |
| `corrections` | Mid-session repairs — "no, actually", "you didn't", "revert" |
| `directives` | Pre-emptive standing orders — "don't", "never", "always", "make sure" |
| `themes` | Word phrases recurring across *distinct sessions* |

**Directives usually carry more signal than corrections.** A user who has
learned to pre-empt a behaviour stopped correcting it and started prefacing
every prompt with it — which looks like zero corrections and is actually the
strongest possible evidence that a rule is missing. Low correction counts are a
normal result, not a failed run.

Read the matched prompts themselves before concluding anything. The classifier
matches keywords; only the text says what the constraint was. A phrase that
recurs because the user pasted the same task twice is not a preference.

### Turning evidence into a candidate

Ask: *is this restated because CLAUDE.md doesn't say it, or because it does say
it and it isn't working?* The two have opposite fixes — add a rule, versus
sharpen or relocate one that is already there and being missed. Check the file
before assuming the first.

## 4. Propose

Group by evidence strength, strongest first, and **make no edits yet**. Every
proposal needs exact wording and a reason; anything weaker than that is noise.

```
CLAUDE.md review — ~/.claude/CLAUDE.md (9 rules)   no changes made

STRONG — file evidence
  §3 and §4 are the same rule
    "Simplicity First" / "Don't Build for Someday" both forbid speculative code.
    → merge into §3, drop §4

  §7 names scripts/check.sh — no such file
    → drop the clause, or point it at the current path

MEDIUM — usage evidence
  Temp file location, prefaced in 4 prompts across 3 projects
    "use $TMPDIR not /tmp" — never stated in CLAUDE.md
    → add: "Always write temp files to $TMPDIR, never /tmp."

WEAK — worth a look, low confidence
  "keep code concise" recurs in 3 sessions, all Terraform
    → repo-level, not global. Ask before adding anywhere.

Apply which? (all / numbers / none)
```

Rules to hold to:

- **Deletions are findings too.** A rule that fails the rubric costs context
  every session. Proposing removals is most of the value here.
- **Quote the current text** for anything you want to change. The user cannot
  evaluate a rewrite they can't see the original of.
- **One proposal per idea.** Don't bundle a merge and a rewrite.
- **Say when there is nothing to do.** A tight CLAUDE.md should get "this is in
  good shape", not three manufactured suggestions.

## 5. Apply

Only what was approved. Preserve the file's existing structure, numbering and
voice — match how the user writes rules, not how this skill writes them. If
renumbering is needed after a deletion, do it, and say so.

Show the diff after writing. Never touch a rule that wasn't approved, and never
"tidy" adjacent wording on the way past.

## 6. Report

```
~/.claude/CLAUDE.md — 2 of 4 proposals applied

  merged §3 + §4          9 rules → 8
  added §8 temp files     from 4 prompts across 3 projects

Skipped: §7 stale path (you're fixing the script instead),
         "keep code concise" (belongs in the Terraform repo).

Evidence: 71 prompts / 55 sessions / 20 dirs. 0 corrections —
you pre-empt rather than correct, so directives carried this.
```

State the evidence base plainly, including when it was thin. "Two sessions" and
"forty sessions" justify very different confidence, and only the report shows
the user which one they got.
