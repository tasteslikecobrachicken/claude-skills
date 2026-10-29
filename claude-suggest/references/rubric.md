# What makes a CLAUDE.md rule worth keeping

A rule earns its place by changing what gets written. Everything else is
consuming context in every single session to accomplish nothing.

## The test

A rule is good if you can answer all three:

1. **What would Claude have done otherwise?** If there is no plausible wrong
   default, the rule is decoration. "Write correct code" forbids nothing.
2. **Would two readers apply it the same way?** "Keep functions small" fails.
   "No function over 60 lines" passes.
3. **Is it in force every session?** CLAUDE.md is always-on context. Anything
   task-specific belongs in the prompt or a skill, not here.

## Failure modes, in rough order of how often they show up

| Smell | Why it hurts | Fix |
| --- | --- | --- |
| Unfalsifiable | "Write clean, maintainable code" — no behaviour excluded | Delete, or name the concrete thing you keep correcting |
| Mechanically enforced elsewhere | Line length, quote style, import order | Delete; the formatter already wins and prose goes stale silently |
| Two rules, one idea | §3 "Simplicity" and §4 "No speculative features" | Merge, keep the sharper wording |
| Scoped wrong | A Python rule in the global file | Move to the repo that needs it |
| Stale | Names a file, flag or command that no longer exists | Verify against the repo, then fix or drop |
| Restates the default | "Ask before force-pushing" | Delete; you are paying context for behaviour you already get |
| Buried | The real constraint is in the third sentence of a paragraph | Lead with the imperative |

## Shape

Imperative, second person, one rule per line. Lead with the verb.

```markdown
## 5. No Unrequested Tests
Don't write test files or test code unless I ask for it.
```

Not:

```markdown
## 5. Testing Philosophy
I have found over time that tests can sometimes be helpful, but in many
situations they add noise to a change, so generally speaking it would be
preferable if you exercised judgment about whether to include them.
```

Same intent. The first forbids something; the second starts an argument.

## Why, but only when it is non-obvious

A rule the reader thinks is wrong gets ignored or re-litigated every few months.
One clause of rationale prevents that — but only where the reason isn't already
obvious from the rule. Don't annotate "use tabs" with a paragraph.

## Length

Past roughly 40–60 lines a file stops being read in full, and the rules at the
bottom effectively don't exist. If a file is over that, the useful move is
almost never to trim wording — it's to find the rules that fail the test above
and delete them outright.

## Global vs. repo

| | Global (`~/.claude/CLAUDE.md`) | Repo (`<repo>/CLAUDE.md`) |
| --- | --- | --- |
| Holds | How you want Claude to work, everywhere | What this codebase requires |
| Examples | Ask before assuming; no unrequested tests; surgical diffs | Build/test commands, architecture, local conventions |
| Evidence | Themes recurring across *many* project directories | Corrections inside this one repo |

A rule that only bites in one repo, sitting in the global file, is a tax on
every other project. A rule that bites everywhere, copied into four repos, will
drift out of sync. Placement is part of the suggestion.
