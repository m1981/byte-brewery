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
- After every atomic change: commit all touched files.

## CLI entry points (pyproject.toml)

| Command     | Module                          |
|-------------|---------------------------------|
| `aug`       | `augment_ai.aug_pipeline:main`  |
| `aug-recap` | `augment_ai.recap:main`         |
| `dce`       | `augment_ai.dce:main`           |
| `pext`      | `augment_ai.pext:main`          |
| `aireview`  | `aireview.main:main`            |
| `chatmap`   | `prompt_extractor.cli:main`     |

## prompt_extractor module (`src/prompt_extractor/`)

Parses Google AI Studio / Gemini JSON conversation exports.

### Files

| File                 | Purpose                                                  |
|----------------------|----------------------------------------------------------|
| `models.py`          | `MessageNode` dataclass                                  |
| `core.py`            | `parse_chunks`, `build_threads`, `format_timeline`, `format_tree` |
| `html_formatter.py`  | `format_html` — self-contained HTML swimlane document    |
| `cli.py`             | `chatmap` entry point                                    |

### CLI usage

```bash
chatmap <input_path> [--view timeline|tree|html] [-o output_path]
```

- `input_path` — single file or directory; any extension accepted, non-JSON skipped silently
- `--view html` with a directory → all conversations rendered as lanes in one `.html` file
- `--view timeline|tree` with a directory → one `.md` per file written to output directory

### `MessageNode` fields

```python
timestamp: datetime
role: str               # "user" or "model"
text: str
image_id: Optional[str]
branch_parent: Optional[dict]  # {"promptId": ..., "displayName": ...}
children: List[MessageNode]
```

### Key behaviours

- `isThought=True` chunks are filtered out
- Chunks without text AND without driveImage are discarded
- Nodes sorted chronologically by `createTime`
- `branchParent` on a user node marks the start of a new conversation thread

### Test data

Real Gemini exports in `prompt_extractor/` (`.txt` files). `Branch of Czym jest aforyzm_.txt` demonstrates the `branchParent` structure.
