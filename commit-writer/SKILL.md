---
name: commit-writer
description: Analyzes the pending git changes and generates quality commit messages
---

# Commit Writer

Read the pending changes, work out what they actually do, and propose a commit
message. Commit only after the user approves.

## 1. Gather context

Run these together:

```bash
git status --short
git diff --stat HEAD
git diff --cached
git diff
git log -20 --no-merges --format='%s%n%b%n---'
```

If the diff is too large to read in full, use `git diff --stat` to find the
files that carry the change and read those diffs individually. Do not write a
message from the file list alone — the subject has to describe behaviour, and
filenames rarely tell you that.

## 2. Decide what is being committed

- Staged changes exist → those are the commit. Ignore unstaged work.
- Nothing staged, but there are modified/untracked files → tell the user what
  you would stage and ask before staging anything.
- Nothing to commit → say so and stop.

If the pending changes are clearly two or more unrelated pieces of work, say so
and offer to split them into separate commits rather than writing one message
that papers over the seam.

## 3. Pick the convention

Judge the last 20 commits. Match the repo's existing style **if that history is
good quality**, meaning most commits:

- have specific subjects — "Reject expired tokens on refresh", not "fix",
  "update", "wip", "changes"
- use a consistent form (tense, capitalization, prefixes)
- carry a body when the change is non-trivial

If the history is poor, mixed, or the repo has fewer than ~5 real commits, fall
back to Conventional Commits:

```
type(scope): subject

body

footer
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`,
`ci`, `chore`. Scope is optional and names the affected area. Breaking changes
get a `!` after the type/scope and a `BREAKING CHANGE:` footer.

Tell the user which convention you chose and why, in one line.

## 4. Write the message

Whatever the convention:

- Subject ≤ 50 characters, imperative mood, no trailing period.
- Blank line, then body wrapped at 72 characters.
- The body explains **why** — the problem, the reason for this approach, and
  anything a reviewer would otherwise have to reconstruct from the diff. Skip
  the body only when the change is genuinely self-evident.
- Describe the change, not the process. No "as requested", "per review", or a
  narration of how you arrived at the code.
- Don't list files that the diff already shows. Group by intent instead.
- Keep issue/ticket references in a footer (`Refs #142`, `Fixes #142`) if the
  repo's history does that.

## 5. Propose, then commit

Show the full message in a fenced block and stop. Do not commit yet.

On approval, commit with a heredoc so the formatting survives:

```bash
git commit -F - <<'EOF'
<message>
EOF
```

If the session has attribution rules in effect (CLAUDE.md, or the harness's own
co-author lines), append them as footers. Otherwise add none.

If a pre-commit hook rewrites or rejects the commit, report the hook's output
and let the user decide — don't retry with `--no-verify`.
