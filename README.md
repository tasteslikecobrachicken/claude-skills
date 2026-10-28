# Claude Skills

A collection of [Claude Code](https://claude.com/claude-code) skills. Each top-level directory is one skill.

## Skills

### Codebase analysis

| Skill | What it does |
| --- | --- |
| [is-it-dead](is-it-dead/) | Finds dead code — unreachable statements, unreferenced declarations, checks that can't fail — proves each candidate is actually dead, and reports it with a confidence level. Deletes only what you approve. Honours `is-it-dead:` ignore markers in comments. |
| [doc-gen](doc-gen/) | Writes documentation from what the code actually does rather than what its comments claim. Surveys and ranks the repo first, traces real execution paths, then writes the documents that repo shape warrants — and reports what it couldn't verify. |
| [todoer](todoer/) | Sweeps the codebase for TODO/FIXME/HACK/XXX markers, learns the project's own marker dialect from its linter config, then reports them grouped by theme and ranked by what fixing them buys. Comment-aware, so markers inside strings don't count. |

### Writing and publishing

| Skill | What it does |
| --- | --- |
| [doc-converter](doc-converter/) | Converts files between Markdown, HTML and PDF via [`multi_convert`](https://github.com/tasteslikecobrachicken/multi_convert). Documents where PDF input degrades — extraction is a text dump, not structure. |

### Project setup and standards

| Skill | What it does |
| --- | --- |
| [project-scaffold](project-scaffold/) | Stands up a new Python, TypeScript, Java, Go or Rust project with layout, build config, lint, format, tests and CI. Prefers each ecosystem's own scaffolder over hand-written templates. |
| [style-guide](style-guide/) | Defines and enforces a project's coding style, splitting mechanical rules (formatter config) from judgment rules (a written guide). Generates a block into `CLAUDE.md` so the rules apply without invoking the skill. |

## Installing

Skills are stored in `$HOME/.claude/skills/` on macOS/Linux and `C:\Users\<your-username>\.claude\skills\` on Windows by default.  
To install, just copy the skill directories from this repo into your Claude skills location.