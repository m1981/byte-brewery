# byte-brewery — LLM Agent Guide

> **Purpose of this document**: teach an LLM agent how to use every CLI tool
> in this repo effectively — what each tool produces, when to reach for it,
> how to chain tools together, and how to read the output.

---

## Mental Model

These tools are **code-surfacing instruments**.  Their job is to compress a
Python codebase into representations that are small enough to fit in a context
window yet rich enough to reason about architecture, hotspots, and structure.

```
Source files
    │
    ├─ repo-map      → one-liner signatures per file  (fastest overview)
    ├─ pysum         → imports + full signatures       (wider context)
    ├─ py-diagram    → class inheritance + fields      (type topology)
    ├─ gen-diagram   → Graphviz DOT class diagram      (visual / tooling)
    ├─ callgraph     → runtime call graph + timings    (behaviour, not structure)
    ├─ lsproj        → filtered file list              (whitelist-driven scoping)
    └─ py-diagram --format token  →  ultra-compact     (token budget critical)
```

**Rule of thumb**: start with `repo-map`, zoom in with `pysum`, then reach for
`callgraph` only when you need runtime behaviour, not static structure.

---

## Tools Reference

### `repo-map` — Fastest structural overview

**What it outputs**: one section per file, each function/class as a single
line with its signature and line number.  No bodies, no imports by default.

```
📄 src/chat_service.py
  class ChatService  [line 144]
      def handle_turn(self, session_id: str, user_message: str, ...)  [line 151]
  def _make_title(ui_messages: list[dict])  [line 73]
```

**When to use**:
- First pass on an unknown codebase — fit the whole project in one read.
- Locating which file a function lives in before reading it.
- Checking whether a refactor changed the public surface.

**Key flags**:
```bash
repo-map                          # scan current directory
repo-map --root src/              # specific subtree
repo-map --only src/domain        # narrow to one package
repo-map --skip tests migrations  # ignore noise dirs
repo-map --show-imports           # add import lines (bigger, but shows deps)
```

**Token cost**: very low.  A 20-file project fits in ~300 tokens.

---

### `pysum` — Signatures + imports (richer than repo-map)

**What it outputs**: per-file Markdown code blocks with all imports and full
typed signatures.  No function bodies.

```markdown
## chat_service.py
\`\`\`python
import json, uuid, structlog
from agent import process_chat_turn

class ChatService
    def handle_turn(self, session_id: str, ...) -> tuple[str, list[dict]]
def _make_title(ui_messages: list[dict]) -> str
\`\`\`
```

**When to use**:
- You need to know *which packages* a module imports (dependency audit).
- You want full type signatures, not just names.
- Feeding to an LLM that will write code calling into this module.

**Key flags**:
```bash
pysum                             # scan current dir
pysum src/                        # scan subdirectory
pysum > structure.md              # save for later
lsproj | pysum --pipe             # scope to .projlist whitelist first
find . -name '*.py' -not -path '*/tests/*' | pysum --pipe
```

**Token cost**: low–medium.  Larger than `repo-map` due to imports.

---

### `py-diagram` — Class topology (inheritance, fields, methods)

**What it outputs**: class hierarchy with inheritance, typed fields, and
method signatures in your chosen format.

**Formats**:

| Format | Use case |
|---|---|
| `mermaid` | Paste into GitHub / Obsidian for rendering |
| `token` | Smallest text form — best for LLM context window |
| `dot` | Feed to Graphviz `dot -Tpng` |
| `plantuml` | Feed to PlantUML server |

**Token format** (most useful for LLMs):
```
[MODULE] repositories
[CLASS] SQLiteSessionRepository [module=repositories]
    FIELDS: db_path:Path
    METHODS: save_session(session_id:str, ...)->None, load_session(...)->tuple
[CLASS] SessionRepository(Protocol) [module=repositories]
    METHODS: save_session(...), load_session(...)
```

**When to use**:
- You need to understand inheritance chains before editing a class.
- Checking whether an interface (Protocol) is fully implemented.
- Producing a diagram for documentation.

**Key flags**:
```bash
py-diagram                            # mermaid, scan cwd
py-diagram --format token             # smallest output for LLM prompts
py-diagram --format token > arch.txt  # save for reuse
py-diagram --source src/models.py     # single file
py-diagram --skip tests migrations    # exclude noise
py-diagram --max-classes 20           # cap large projects
```

**Token cost**: low (`token` format), medium (`mermaid`).

---

### `gen-diagram` — Graphviz DOT class diagram

**What it outputs**: a `.dot` file (Graphviz language) describing classes,
methods, and their relationships.  Pipe to `dot -Tpng` or paste into an
online viewer.

**When to use**:
- Generating a visual diagram for a PR description or wiki.
- When you need Graphviz-specific features (clusters, styling).
- Tooling pipelines that consume DOT format.

```bash
gen-diagram .                         # print DOT to stdout
gen-diagram . > architecture.dot
gen-diagram . | dot -Tpng -o arch.png
gen-diagram --skip tests .
```

**Token cost**: medium–high.  DOT syntax is verbose; prefer `py-diagram
--format token` for LLM consumption.

---

### `callgraph` — Runtime call graph (behaviour, not structure)

**What it outputs**: three optional artefacts from an **actual execution** of
a Python script:
1. **PNG/SVG image** — visual call graph (needs Graphviz `dot` binary)
2. **JSON report** — every function called, with call count, total time, and
   caller list, sorted by call frequency
3. **Mermaid flowchart** — text call graph, no Graphviz needed

**JSON schema**:
```json
{
  "call_graph": [
    {
      "name": "SQLiteConnection.get_connection",
      "call_count": 36,
      "time_total": 0.042,
      "callers": ["SQLiteSessionRepository.save_session", "load_session"]
    }
  ]
}
```
Records are sorted by `call_count` descending.

**When to use**:
- Finding hotspots: which functions are called most often?
- Understanding data flow: what calls what at runtime?
- Performance investigation: what is slow (`time_total`)?
- Validating that a refactor didn't change call patterns.

**Key flags**:
```bash
callgraph --target src/main.py
callgraph --target src/main.py --json report.json --mermaid graph.md
callgraph --target src/main.py --include 'mypackage.*'   # focus on your code only
callgraph --target src/main.py --exclude 'test*'
callgraph --target src/main.py --max-depth 5             # avoid deep stdlib noise
callgraph --target src/main.py --format svg              # if png is too big
```

**Important**: `callgraph` **actually runs the script**.  If `main.py` starts
a server or blocks, it will hang.  Prefer targeting a probe/init script or
use `--max-depth` to limit scope.

**Python version**: `callgraph` auto-detects the target project's `.venv` and
re-runs itself under the project's own Python interpreter.  No manual
`PYTHONPATH` setup needed.

**Token cost for JSON**: high (hundreds of records).  Filter before feeding to LLM:
```bash
# Top 10 hotspots only
python3 -c "
import json, sys
d = json.load(open('report.json'))
top = d['call_graph'][:10]
print(json.dumps(top, indent=2))
"

# Only app-level code (exclude stdlib noise)
python3 -c "
import json
d = json.load(open('report.json'))
NOISE = {'importlib', 'threading', 'abc', '_', 'ModuleSpec', 'contextlib'}
app = [r for r in d['call_graph'] if not any(r['name'].startswith(n) for n in NOISE)]
print(json.dumps(app[:20], indent=2))
"
```

---

### `lsproj` — Whitelist-driven file scoping

**What it outputs**: a newline-separated list of file paths matching the
`.projlist` whitelist and `.gitignore` exclusions in the current directory.

**`.projlist` syntax**:
```
*.py                   # match by filename anywhere
src/**/*.py            # recursive glob
!tests/__init__.py     # negation — exclude even if whitelisted
# comment              # ignored
```

**When to use**:
- Scoping other tools to exactly the files that matter.
- Avoiding test files, migrations, generated code when summarising.

```bash
lsproj                            # list files per .projlist
lsproj | pysum --pipe             # summarise only whitelisted files
lsproj | xargs wc -l              # line count of project files
lsproj -e '*.md'                  # ad-hoc extra exclusion
```

---

### `pext` — Extract prompts from ChatGPT/LLM chat exports

**What it outputs**: human prompts extracted from a JSON chat export, in
text, JSON, or CSV format.

```bash
pext chats.json                        # print all human prompts as text
pext chats.json --format json          # structured JSON
pext chats.json --format csv --timestamps
pext chats.json --output prompts.txt
```

---

### `chatmap` — Map Google AI Studio conversation exports

**What it outputs**: structured views of AI Studio JSON exports — timelines,
trees, HTML swimlanes, or plain prompt lists.

```bash
chatmap export.json                          # timeline view (default)
chatmap export.json --view tree              # branching conversation tree
chatmap export.json --view html -o out.html  # full HTML report
chatmap export.json --view prompts           # just the prompts
chatmap export.json --view recent            # most recent activity
chatmap exports/   --view html -o all.html   # whole directory → one file
```

---

### `aireview` — AI-powered pre-push code review

**What it does**: runs an AI code review on git changes before a push.
Reads `.aireview.yml` for configuration.

```bash
aireview           # review staged/recent changes
```

---

## Effective Chaining Patterns

### Pattern 1: "What does this project do?" (cold start)
```bash
repo-map --root src/
```
Feed the output directly.  Single call, low tokens, answers structure questions.

---

### Pattern 2: "I need to modify class X" (surgical zoom)
```bash
# Step 1: locate the file
repo-map --root src/ | grep -A5 "ClassName"

# Step 2: get full signatures + imports for that file
pysum src/that_file.py

# Step 3: read the actual source
cat src/that_file.py
```

---

### Pattern 3: "Is this interface fully implemented?" (Protocol check)
```bash
py-diagram --format token --source src/repositories.py
```
The token format shows Protocol methods and concrete class methods side by
side — gaps are immediately visible.

---

### Pattern 4: "Where are the performance hotspots?" (runtime analysis)
```bash
# 1. Run callgraph against a lightweight entry point
callgraph --target src/probe.py \
          --include 'src.*' \
          --json report.json \
          --mermaid hotspots.md

# 2. Extract the top 15 app-level calls for LLM analysis
python3 -c "
import json
d = json.load(open('report.json'))
noise = {'importlib','threading','_','ModuleSpec','contextlib','inspect','abc'}
app = [r for r in d['call_graph']
       if not any(r['name'].startswith(n) for n in noise)]
print(json.dumps({'hotspots': app[:15]}, indent=2))
"
```

---

### Pattern 5: "Summarise only meaningful files" (token budget tight)
```bash
# 1. Scope with lsproj (reads .projlist whitelist)
lsproj | pysum --pipe

# 2. Or scope manually
find src/ -name '*.py' -not -path '*/migrations/*' | pysum --pipe
```

---

### Pattern 6: "Generate architecture docs" (diagram pipeline)
```bash
# Mermaid (paste into GitHub PR / Obsidian)
py-diagram --format mermaid > docs/architecture.md

# PNG via Graphviz
gen-diagram . | dot -Tpng -o docs/architecture.png

# Token-compact for LLM context
py-diagram --format token > docs/architecture.txt
```

---

## Anti-patterns to Avoid

| Anti-pattern | Why it fails | Better approach |
|---|---|---|
| `cat src/**/*.py \| llm ...` | Blows token budget, buries signal in bodies | `pysum` or `repo-map` first |
| `callgraph --target src/main.py` when main starts a server | Hangs indefinitely | Write a lightweight `probe.py` entry point |
| Feeding full `report.json` (659 records) to LLM | Mostly stdlib noise | Filter to top 15 app-level records |
| `py-diagram --format dot` for LLM context | DOT is verbose | Use `--format token` |
| Skipping `lsproj` and scanning everything | Includes tests, migrations, generated code | Configure `.projlist` once, pipe always |
| Running `gen-diagram` and expecting image output | Outputs DOT text | Pipe to `dot -Tpng -o out.png` |

---

## Output Size Reference

| Tool + flags | Typical output | Token estimate |
|---|---|---|
| `repo-map` (20 files) | ~60 lines | ~400 |
| `pysum` (20 files) | ~150 lines | ~1 200 |
| `py-diagram --format token` | ~80 lines | ~600 |
| `py-diagram --format mermaid` | ~120 lines | ~900 |
| `callgraph --json` (full, 600 records) | ~2 000 lines | ~16 000 |
| `callgraph --json` (top 15 filtered) | ~50 lines | ~400 |
| `gen-diagram` (20 classes) | ~200 lines | ~1 600 |

---

## Quick Reference Card

```
TOOL          INPUT           OUTPUT              BEST FOR
──────────────────────────────────────────────────────────────────────
repo-map      .py files       signatures/file     cold start, locate files
pysum         .py files       imports+sigs/file   understand a module
py-diagram    .py files       class topology      inheritance, Protocol impl
gen-diagram   .py files       Graphviz DOT        visual diagrams, tooling
callgraph     .py script      call graph artefacts runtime hotspots, flow
lsproj        .projlist       file list           scoping other tools
pext          chat JSON       prompts list        extract LLM conversation
chatmap       AI Studio JSON  timeline/tree/HTML  navigate conversation history
aireview      git diff        AI review           pre-push code quality
```
