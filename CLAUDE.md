# CLAUDE.md — byte-brewery

## Project overview

A collection of Python CLI utilities for AI development workflows. Source lives under `src/`, tests under `tests/`. Installed in editable mode into `.venv`.

## Running tests

```bash
.venv/bin/pytest tests/ -v
```

There is no `python` or `pytest` on the system PATH — always use `.venv/bin/pytest` and `.venv/bin/python`.

## Development conventions (from instruct.txt)

- Act as a commercial-grade Python developer following clean code and Agile principles.
- **Work iteratively with atomic, coherent changes.**
- **Write unit tests before editing non-visual code.**
- After every atomic change: update the spec if needed, then commit all touched files.

## CLI entry points (pyproject.toml)

| Command    | Module                          |
|------------|---------------------------------|
| `aug`      | `augment_ai.aug_pipeline:main`  |
| `aug-recap`| `augment_ai.recap:main`         |
| `dce`      | `augment_ai.dce:main`           |
| `pext`     | `augment_ai.pext:main`          |
| `aireview` | `aireview.main:main`            |
| `chatmap`  | `prompt_extractor.cli:main`     |

## prompt_extractor module (`src/prompt_extractor/`)

Parses Google AI Studio / Gemini JSON conversation exports into Markdown.

### Key files

| File         | Purpose                                            |
|--------------|----------------------------------------------------|
| `models.py`  | `MessageNode` dataclass                            |
| `core.py`    | `parse_chunks`, `build_threads`, `format_timeline`, `format_tree` |
| `cli.py`     | `chatmap` CLI entry point                          |

### `MessageNode` fields

```python
timestamp: datetime
role: str               # "user" or "model"
text: str
image_id: Optional[str]
branch_parent: Optional[dict]  # {"promptId": ..., "displayName": ...}
children: List[MessageNode]
```

### Core logic

- `parse_chunks(data)` — filters `isThought=True` chunks, extracts `driveImage.id`, parses `createTime`, sorts chronologically.
- `build_threads(nodes)` — splits on `branchParent` markers; returns `[(display_name, nodes)]` list; first entry always has `None` as name (main thread).
- `format_timeline(nodes)` — default view; inserts `🔄 TIMELINE BRANCH (Rewind)` markers before branching nodes.
- `format_tree(threads)` — groups as `🌿 Main Thread` + `🌿 Branch N` sections.

### CLI usage

```bash
chatmap <input_path> [--view timeline|tree] [-o output_path]
```

`input_path` can be a single `.json` file or a directory. For directories, all `*.json` files are processed; `-o` must point to an output directory.

### Test data

Real Gemini conversation exports live in `prompt_extractor/` (`.txt` files containing JSON). The `Branch of Czym jest aforyzm_.txt` file demonstrates the `branchParent` structure.

### Spec

Full v2.0 spec: `src/prompt_extractor/goal.md`
