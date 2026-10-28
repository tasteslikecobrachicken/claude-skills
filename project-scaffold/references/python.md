# Python

Tooling: **uv** for the project and environment, **ruff** for lint and format,
**pytest** for tests, **mypy** for types. Ruff replaces black, isort, flake8 and
most plugins — don't install those alongside it.

Always use a `src/` layout. A flat layout leaves the working directory on
`sys.path`, so tests import the source tree rather than the installed package
and packaging bugs stay invisible until release.

## Native init

`uv init` picks a template from the flag:

| Project type | Command | Produces |
| --- | --- | --- |
| Library | `uv init --lib <name>` | `src/` layout, build backend configured |
| CLI | `uv init --package <name>` | `src/` layout plus a `[project.scripts]` entry point |
| Application / service | `uv init --package <name>` | Same; prefer it over bare `uv init`, which gives a flat `main.py` |
| Adding to an existing tree | `uv init --bare` | `pyproject.toml` only — no README, no `.python-version`, no `git init` |

Add `--python 3.13` to pin the interpreter.

uv chooses a build backend for you, and the default has changed across releases
(recent versions use `uv_build`). Read the generated `[build-system]` rather
than assuming; pass `--build-backend hatchling` if the project needs the more
widely recognised one.

Then layer the dev tooling:

```bash
uv add --dev ruff pytest pytest-cov mypy
```

## What to add on top

`uv init` writes no lint, format, type or test configuration. Append to
`pyproject.toml`:

```toml
[tool.ruff]
line-length = 88
src = ["src", "tests"]

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B", "SIM", "RUF"]

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["S101"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra --strict-markers --strict-config"

[tool.mypy]
python_version = "3.13"
strict = true
files = ["src", "tests"]
```

The rule selection is deliberately short: pycodestyle/pyflakes for correctness,
`I` for import order, `N` for naming, `UP` for syntax that's outdated for the
target version, `B` for real bugs, `SIM` for needless complexity, `RUF` for
ruff's own checks. Widen it if the user asks; don't enable `ALL`, which pulls in
mutually contradictory rules.

## Layout

```
src/<import_name>/__init__.py
src/<import_name>/py.typed        # libraries only — ships the type info
tests/test_<something>.py
pyproject.toml
.python-version
.gitignore
```

The distribution name (`[project].name`, hyphens allowed) and the import name
(the directory under `src/`, underscores only) are different strings. Set both
deliberately.

For a CLI, `uv init --package` **has already written a `[project.scripts]`
section** pointing at a generated `main` in the package root. Edit that entry;
do not append a second section, or `pyproject.toml` gets a duplicate key and
every uv command fails with a TOML parse error before doing anything else.

```toml
[project.scripts]
ferry = "ferry.cli:main"
```

The left side is the command the user types; the right is
`<import_name>.<module>:<function>`. If you move `main` out of the package root
— into `cli.py`, say — update this path to match, or the installed command
will fail on a missing attribute.

## Fallback — no uv installed

```bash
python3 -m venv .venv && .venv/bin/python -m pip install -U pip
.venv/bin/pip install ruff pytest pytest-cov mypy
```

Write `pyproject.toml` by hand with an explicit backend:

```toml
[project]
name = "<dist-name>"
version = "0.1.0"
description = ""
readme = "README.md"
requires-python = ">=3.11"
dependencies = []

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/<import_name>"]
```

Then `pip install -e .`. Everything in the sections above still applies —
only the bootstrap differs. Never hand-write `uv.lock`.

## .gitignore

```gitignore
__pycache__/
*.py[cod]
.venv/
venv/
build/
dist/
*.egg-info/
.pytest_cache/
.ruff_cache/
.mypy_cache/
.coverage
htmlcov/
.env
```

## Verification loop

```bash
uv sync
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest
```

## CI (only if requested)

```yaml
name: ci
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: uv sync --all-extras --dev
      - run: uv run ruff check .
      - run: uv run ruff format --check .
      - run: uv run mypy
      - run: uv run pytest
```

Drop the matrix for an application — it targets one interpreter. Keep it for a
library, which has to work on every version its metadata claims.

## Pre-commit (only if requested)

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

Check the current `rev` rather than copying that tag forward.
