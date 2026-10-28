# <Language>

Copy this file to `references/<lang>.md` and fill it in. Keep every heading,
even where a section is thin — `SKILL.md` §3 reads the config out of
**Mechanical**, and §5 reads the command list out of **Commands**.

Tooling: name the formatter, the linter, and the type checker if there is one.
One sentence. If the ecosystem has a single blessed tool, say that it is not a
decision and move on.

## Mechanical — owned by the tools

The formatter and lint config to install, as a config snippet the project can
take verbatim.

Nothing in this section should ever be restated as prose elsewhere. If the
formatter enforces it, the formatter is the documentation.

State explicitly which knobs are deliberately left at their defaults. "We use
the default line length" is a decision worth recording, because it stops the
question being reopened.

## Judgment rules

The actual content of the guide: rules no formatter can check. Aim for ten to
twenty. The test for inclusion is **would a reviewer raise this in a pull
request** — if not, it is padding, and padding is what makes guides go unread.

Group under whichever of these apply. Drop headings that have nothing real to
say rather than inventing entries.

### Naming
### Types
### Errors
### Structure
### Documentation
### Idioms

Write each rule as an imperative, with the reason attached when it isn't
obvious. "Don't X" with no rationale gets re-litigated forever; "Don't X,
because Y" gets accepted or argued once.

Prefer showing a short bad/good pair over describing the rule in the abstract.
Two lines of code beats a paragraph.

## Commands

The exact commands for format, lint, type-check and test. `SKILL.md` §5 runs
these, so they must be copy-pasteable and correct for a default project.

```bash
<format>
<lint>
<typecheck>
<test>
```

Note which of these are autofixing and which only report — the sweep splits
those into separate commits and needs to know which is which.

## Sweep notes

Language-specific hazards when reformatting an existing codebase: autofixes
that can change behaviour, tooling that rewrites more than expected, anything
that makes a mass reformat riskier than it looks.

If there are none worth naming, say so explicitly rather than leaving the
section empty — an empty section reads like an oversight.
