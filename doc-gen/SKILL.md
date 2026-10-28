---
name: doc-gen
description: Generate documentation from what a codebase actually does, by reading the code rather than trusting its comments, docstrings or README, and write it into the repo. Use when the user asks to document a codebase, write or rewrite a README, architecture doc or onboarding guide, explain how a project works, or check whether existing documentation still matches the code.
---

# Doc Gen

Documentation drifts because it is written once, beside code that then changes
without it. So write it from the code: read what the program does now, and let
every claim in the output trace back to something you read.

Comments, docstrings and the existing README are evidence of what somebody
*intended*, at some point. They are the input this skill exists because nobody
should trust. Read them — last, and as claims to check.

## 1. Survey before reading anything

You cannot read forty thousand files, and most of them are not the project.

```bash
python3 scripts/survey.py --text                    # whole repo
python3 scripts/survey.py --text --top 80           # more of the ranking
python3 scripts/survey.py src/billing --depth 3     # one subsystem, finer components
python3 scripts/survey.py                           # JSON, for working through
```

The script drops vendored, generated, minified and binary files, then ranks
what survives by entry point, fan-in, churn and role, and reports the import
edges between directories. Read `--text` first for shape; take the JSON when
you start choosing files.

Three things to check before trusting it:

- **`skipped`.** It is the one place a wrongly-excluded directory shows up. A
  project that keeps real source in `build/` or `bin/` will quietly lose it.
- **Fan-in 0 is not "unused."** The graph is regex over imports. Routes,
  dependency injection, reflection, plugin registries, autoloaders and
  build-time path aliases are all invisible to it. Files reached only that way
  look dead and are not.
- **Component depth.** Default 2. If components come out as `gson/src` or
  `packages/core`, raise `--depth` until they name real areas.

Then read. The top 20–40 files, the manifests, the CI config, and whatever
tracing (§4) pulls you into.

## 2. Decide what this repo warrants

Write what this codebase needs, not a fixed set of documents. The survey's
entry points, manifests and edges tell you which it is:

| Shape | Signals | What to write |
| --- | --- | --- |
| **Library** | manifest declares exports; importers are tests and examples | what it's for, the public surface, the concepts behind it, the shape of a typical use |
| **Service** | entry point is a server; infra and deploy files; CI publishes an image | architecture, the request lifecycle, configuration and environment, operations |
| **CLI** | entry under `bin/` or `cmd/`; arg-parsing early | the commands, their flags, config resolution, exit codes |
| **Monorepo** | many manifests; cross-package edges | an index, what each package is, and how they fit; then per-package |
| **Framework / plugin host** | registries, hooks, dynamic loading | the extension points and their contracts — the part users write against |

**Do not hand-write what a generator produces better.** If the project has (or
could have) typedoc, Sphinx autodoc, godoc, rustdoc or javadoc, a
signature-by-signature API reference belongs to the generator — it is derived
from the code, so it cannot drift. Say so rather than producing a worse copy of
`pkg.go.dev`.

What a generator cannot produce, and you should: why the API is shaped this
way, which five of the forty exported symbols people actually need, the
invariants callers must maintain, lifecycle and ordering constraints, and what
happens when things fail.

Three documents that are never worth writing: a file-by-file tour, a directory
listing with a line per folder, and a restatement of function signatures in
prose. They are stale within a sprint and teach nothing in the meantime.

## 3. Read for behaviour, not for claims

Rank your sources. Higher on this list beats lower whenever they disagree:

1. **The code on the path you are documenting.** The only thing that is
   definitionally true.
2. **CI config.** Executable documentation that passes on every commit — the
   surest available statement of how the project is really built, tested,
   linted and released. Trust it over any README's setup section.
3. **Manifests and lockfiles.** Real dependencies, real versions, real entry
   points, real scripts.
4. **Schemas and types.** Migrations, protobuf, OpenAPI, JSON Schema, type
   signatures — checked by something, so they rot slower than prose.
5. **Tests.** A behaviour spec. They name the cases the authors cared about,
   including edge cases the implementation doesn't advertise.
6. **Commit history and PRs.** Weak on *what*, often the only source for *why*.
7. **Comments and docstrings.** Intent at time of writing. Nothing more.
8. **Existing prose docs.** Least trustworthy. This is the premise of the skill.

The failures you are looking for are ordinary: a docstring describing a
parameter that was renamed, a README building with a tool replaced two years
ago, "returns None on failure" where the code raises, a documented default the
config loader doesn't have, an architecture page describing a service that was
merged away.

Where reading cannot settle a question and the check is cheap and safe, run it
— `--help`, a single test, a type check. Ask before anything that writes,
deploys, migrates, or reaches the network.

## 4. Trace paths, don't summarise directories

A directory summary is a description of the file browser. What a reader needs
is what happens when the system does its job. Pick two to four real end-to-end
paths and follow them through the code:

- an HTTP request, from route table to response body
- a CLI invocation, from argv to exit code
- a job, from enqueue to completion and retry
- the main read and the main write through the data model
- a build, from source to artifact

Tracing is what finds the things a reader cannot get from the tree: where the
real entry is, whether the layering is what the directories imply, where state
lives, where the transaction or lock boundary sits, what is synchronous and
what is deferred, and what happens on the error path. The survey's edges give
you candidates; the trace tells you which are load-bearing.

Build any diagram from the traces and the edges, never from the directory
tree. Keep it to 5–9 nodes — a diagram with thirty boxes communicates nothing.
If the system genuinely has thirty components, that is itself a finding: draw
the top level and link out to per-area diagrams. Every arrow must be a call you
traced or an edge the survey reported, and should be labelled with what flows
along it.

## 5. Read the existing docs last, and diff them

Last, deliberately — read them early and they will anchor you into repeating
their errors in fresh words.

Each existing claim lands in one of three buckets:

- **Agrees** with what you found. Leave it; say so.
- **Silent.** A gap. This is most of what you will add.
- **Contradicts** the code. A finding, and the most valuable thing this skill
  produces. Someone is being actively misled right now.

Report contradictions to the user separately and prominently, with the location
of the claim and the code that disproves it. Never silently overwrite one —
replacing a wrong claim quietly loses the single most useful fact you found.

Fit the repo's existing setup rather than inventing a parallel one. If there is
an `mkdocs.yml`, a Docusaurus site, or a Sphinx `docs/`, write in its format
(`.rst` vs `.md`) and register new pages in its nav or toctree — an unregistered
page does not render, and nobody will ever see it.

## 6. Write

Default to `docs/`, unless the survey found an existing docs location, in which
case use that one. The README stays the front door — what this is, why it
exists, a quickstart that works, and links out — not the whole manual.

- Open with what the thing is and what it is for, in two sentences, before any
  structure.
- Be concrete. Real paths, real commands, real names: `src/flask/app.py`, not
  "the application module".
- Link to code by path; don't quote it. Pasted code is the fastest-staling
  content in any document. Quote only a short signature or schema that is
  itself the subject.
- Every command you write must be one you saw in CI or a manifest, or ran
  yourself. Never copy a command out of the old README.
- Explain why. The *what* is in the code, and the code states it more
  accurately than you can.
- Prefer claims that will stay true. Documenting a volatile internal in detail
  guarantees drift; documenting a contract does not.
- Write the shortest document that answers the question. A twelve-page
  onboarding guide does not get read, so it does not get maintained.
- No skeleton sections with "TBD". Omit what you do not know.

## 7. Report what you could not verify

Back to the user, alongside the list of files you wrote:

- coverage — what you read against what the survey found, and what you skipped
- contradictions between the existing docs and the code (§5)
- claims you could not verify, and why: dynamic dispatch, config-driven
  behaviour, an external service, no running system to observe
- what the documentation deliberately does not cover

Inside the documents, mark uncertainty inline and specifically, or not at all.
"Unverified: the retry limit appears to come from `RETRY_MAX`, but nothing in
the repo sets it" is useful. "This may not be accurate" hedges everything and
tells the reader nothing.

The one failure mode that matters: fluent, confident text about code you did
not read. That is precisely the artifact this skill exists to replace.
