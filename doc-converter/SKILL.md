---
name: doc-converter
description: Converts documents between Markdown, HTML, and PDF formats.
---

# Universal Document Format Converter

This skill converts files between `.md`, `.html`, and `.pdf` formats using the
[`multi_convert`](https://github.com/tasteslikecobrachicken/multi_convert) package.

Supported conversions:
- **Markdown (`.md`)** ➔ HTML (`.html`), PDF (`.pdf`)
- **HTML (`.html`)** ➔ Markdown (`.md`), PDF (`.pdf`)
- **PDF (`.pdf`)** ➔ Markdown (`.md`), HTML (`.html`)

Every conversion routes through Markdown as an intermediate representation.

## Limitations of PDF input

PDF text extraction is **unstructured**. `multi_convert` reads PDFs with `pypdf`,
which returns the text of each page in roughly reading order, with no document
structure recovered:

- No headings — everything comes out as flat body text.
- Words hyphenated across a line break stay broken (`lif ting`, `rec eptors`).
- Paragraphs arrive as hard-wrapped lines, not reflowed prose.
- Tables are flattened into loose lines; column structure is lost.
- Figures/images are dropped entirely; only their stray text labels survive.
- Captions, sidenotes and footers are interleaved into the body text at the
  position they occupy on the page.

So `pdf → md` and `pdf → html` produce a **faithful text dump, not structured
markup**. Treat the output as raw material: read it and reformat it by hand
(headings, joined paragraphs, real markdown tables) before calling it done.
For table-heavy PDFs, prefer the `pdf-table-extractor` skill.

## Environment & Dependency Management

`multi_convert` installs once into a shared venv at
`~/.cache/claude-doc-converter/.venv` (kept out of the working directory so
converting a file never litters the user's folders). It pulls in `markdown`,
`markdown-pdf`, `html2text` and `pypdf` as dependencies.

## Execution Command

Set `INPUT_FILE` and `TARGET_FORMAT` below, then run the block. Add `--force` as
a third argument to allow overwriting an existing output file.

```bash
INPUT_FILE="path/to/input.pdf"   # <-- set this
TARGET_FORMAT="md"               # <-- set this: "pdf", "html", or "md"
FORCE=""                         # set to "--force" to allow overwriting output

VENV="$HOME/.cache/claude-doc-converter/.venv"

# 1. Create the shared virtual environment if missing
if [ ! -d "$VENV" ]; then
    python3 -m venv "$VENV"
fi
source "$VENV/bin/activate"

# 2. Install multi_convert (and its dependencies) only if not already present
if ! python3 -c "import multi_convert" 2>/dev/null; then
    pip install --quiet multi_convert
fi

# 3. Work out the output path and refuse the two destructive cases
OUTPUT_FILE="${INPUT_FILE%.*}.${TARGET_FORMAT}"

# Converting a file to its own format would read and rewrite the same path,
# replacing the original with a degraded copy of itself. Never do that.
if [ "$(echo "$OUTPUT_FILE" | tr 'A-Z' 'a-z')" = "$(echo "$INPUT_FILE" | tr 'A-Z' 'a-z')" ]; then
    echo "Error: input and output are the same file ($INPUT_FILE). Nothing to convert." >&2
elif [ -e "$OUTPUT_FILE" ] && [ "$FORCE" != "--force" ]; then
    echo "Error: '$OUTPUT_FILE' already exists. Move it, or set FORCE=\"--force\" to overwrite." >&2
else
    multi-convert "$INPUT_FILE" "$OUTPUT_FILE"
fi
```

If the source was a PDF, review the output and restructure it before reporting
the conversion as complete.
