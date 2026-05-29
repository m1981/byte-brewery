# byte-brewery

Small Python CLI utilities for AI-assisted development workflows.

## Projects

- `utils` — general developer helpers:
  - `repo-map`: print a compact structural map of a Python project.
  - `gen-diagram`: emit a Graphviz DOT class diagram for a Python project.
  - `dce`, `pext`: smaller command-line helpers.
- `augment-ai` — tools for extracting and summarizing Augment IDE chat/state exports.
  Commands: `aug`, `aug-recap`.
- `prompt_extractor` — map Google AI Studio / LLM conversation exports into timeline, tree, HTML, or prompt-list views.
  Command: `chatmap`.
- `aireview` — AI-assisted code review and pre-push validation.
  Command: `aireview`.

## Install

Install the project utilities globally on macOS with `pipx`.

```bash
brew install pipx python@3.13
pipx ensurepath
Plea --python /opt/homebrew/bin/python3.13 'git+https://github.com/m1981/byte-brewery.git#subdirectory=packages/utils'
```

After installing, open a new terminal and run:

```bash
repo-map --help
gen-diagram --help
```

If Homebrew's newest Python fails during install, for example with
`platform.mac_ver() returned an empty value`, keep using the explicit
`--python /opt/homebrew/bin/python3.13` command above.

For local development from a cloned repo:

```bash
git clone https://github.com/m1981/byte-brewery.git
cd byte-brewery
uv sync
uv run repo-map --help
uv run gen-diagram --help
```

## Examples

```bash
repo-map --root .
repo-map --root . --show-imports
gen-diagram . > architecture.dot
```
