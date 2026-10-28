# Python

Tooling: **ruff** for both lint and format, **mypy** for types, **pytest** for
tests. Ruff replaces black, isort and flake8 — never run those alongside it.
Full project setup lives in `project-scaffold/references/python.md`; this file
is only about style.

## Mechanical — owned by the tools

```toml
[tool.ruff]
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B", "SIM", "RUF"]

[tool.ruff.format]
# All defaults: double quotes, magic trailing comma respected.

[tool.mypy]
strict = true
```

`I` makes import order a tool concern, `N` makes naming conventions a tool
concern, `UP` keeps syntax current for the target version. Nothing about
quotes, line length, import grouping or whitespace belongs in prose below.

Don't enable `ALL`. It pulls in mutually contradictory rules and the project
then spends its time writing `noqa`.

## Judgment rules

### Naming

Names describe the thing, not its type or its role in a pattern. `users` not
`user_list`, `config` not `config_dict`. Suffixes like `Manager`, `Helper`,
`Util` and `Data` mean the author hadn't decided what the class was for — if
you can't name it, it probably does more than one thing.

Booleans read as assertions: `is_active`, `has_permission`, `should_retry`.

A leading underscore is the only visibility marker Python has. Use it, and
treat someone else's `_name` as off limits.

### Types

Annotate every public signature. Internal helpers can go unannotated when the
types are obvious from two lines away, but a function that survives a refactor
deserves them.

Never `Any` as a shrug. `object` when you truly accept anything and will narrow;
`Any` only when interoperating with something genuinely untyped, with a comment
saying which.

Parameters take the widest type that works, returns give the narrowest:

```python
def totals(rows: Iterable[Row]) -> dict[str, int]:   # yes
def totals(rows: list[Row]) -> Mapping[str, int]:    # backwards
```

Returning a concrete `dict` lets callers use it; accepting `Iterable` lets them
pass a generator.

`X | None` means genuinely optional. A parameter that is "required but I haven't
got it yet" is a design problem, not a nullable.

### Errors

No bare `except:` and no bare `except Exception:` — both swallow
`KeyboardInterrupt`-adjacent bugs and turn a crash into silent wrong data. Catch
what you can actually handle.

Every package gets one base exception; every exception it raises inherits from
it. Callers can then catch the package without catching the world.

```python
class FerryError(Exception): ...
class RouteNotFound(FerryError): ...
```

Re-raise with `raise ... from err` so the original traceback survives. A
`logger.exception(...)` followed by `raise` is duplication — log at the boundary
that handles it, not at every frame it passes through.

Never `except ...: pass`. If it's genuinely ignorable, `contextlib.suppress`
says so deliberately and is greppable.

### Structure

Guard clauses over nested conditionals. Three levels of indentation inside a
function is the point to extract.

A class with one public method and no state is a function. A class whose
`__init__` only stores arguments that one method reads is a function with
ceremony around it.

Structured data gets a `dataclass` or `TypedDict`, not a bare dict passed
between functions. Dicts as records lose every typo to a `KeyError` at runtime,
usually in production.

Module level runs at import. Constants and definitions only — no I/O, no
network, no config loading, no logging setup.

### Documentation

Docstrings on public API; not on `__init__` that stores three arguments, not on
a five-line private helper whose name already says it.

One imperative line, then a blank line, then detail if there is any. Don't
restate the signature — annotations carry types, so a docstring that lists
parameter types is two copies of one fact.

Comments explain *why*. The code already says what. A comment that will be
wrong after the next edit is worse than no comment.

### Idioms

`pathlib` over `os.path`. f-strings over `%` and `.format()`, except in logging
calls, where `logger.info("got %s", n)` defers formatting until the record is
actually emitted.

Comprehensions when they fit on a line or two; a loop when they don't. A nested
comprehension with a condition is write-only.

Context managers for anything with a lifetime — files, locks, connections,
transactions.

Never a mutable default argument. `def f(x=[])` shares one list across every
call, and it is always a bug.

## Commands

```bash
ruff format .                 # autofixing
ruff check --fix .            # autofixing
ruff check .                  # report only
mypy                          # report only
pytest                        # report only
```

## Sweep notes

`ruff check --fix` removes unused imports. In codebases that rely on import side
effects — model registration, plugin discovery, signal handlers wired at import
— that deletion silently breaks startup and no test may cover it. Check for a
registry pattern before accepting the autofix commit, and re-run the app, not
just the suite.

`--unsafe-fixes` is off by default. Leave it off in a sweep; the fixes it adds
change behaviour by definition and belong in a supervised judgment commit.

Adding `strict = true` to mypy on an existing codebase produces hundreds of
errors at once. Turn it on per-module with `[[tool.mypy.overrides]]` and work
through them, rather than leaving a red type-check that everyone learns to
ignore.
