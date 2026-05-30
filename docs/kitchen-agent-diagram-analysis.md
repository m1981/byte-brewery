# `py-diagram` Tool Analysis — `kitchen-agent` Repo

> Run date: 2026-05-30  
> Target: `/Users/michal/PycharmProjects/kuchnie/kitchen-agent/src`  
> Tool: `py-diagram` (utils package, byte-brewery)

---

## 1. What Was Found

| Metric | Value |
|---|---|
| Python source files scanned | 12 (`src/*.py` + `src/tools/*.py`) |
| Classes detected | **41 / 41** — 100% recall ✅ |
| Relationships detected | **5** (composition only) |
| Missing relationships | **~36** inheritance edges — see §4 |
| Module-level functions | **30+** — not surfaced (by design) |

---

## 2. Token Budget Comparison

| Format | Chars | Lines | ~Tokens (÷4) | Notes |
|---|---|---|---|---|
| **Raw Python source** | 151,334 | ~3,200 | **~37,833** | full source dump |
| TOKEN | 6,907 | 101 | **~1,727** | LLM-optimised |
| Mermaid | 6,551 | 221 | **~1,638** | best visual format |
| PlantUML | 6,108 | 304 | **~1,527** | most verbose per class |
| DOT (Graphviz) | 7,783 | 52 | **~1,946** | longest records |

### **Compression ratio vs raw source: ~96% token reduction**

Giving an LLM the TOKEN or Mermaid output instead of the raw source
uses **~22× fewer tokens** while conveying the full type/contract surface.

---

## 3. What Was Correctly Detected ✅

### Service layer classes
```
ChatService          — handle_turn() with full typed signature
MessageEditService   — 5 edit/truncate/system-prompt operations
PromptManager        — reload, list modes, get system instruction
```

### Repository layer (Protocol + SQLite implementations)
```
SessionRepository    Protocol  — 10 method contracts fully captured
NoteRepository       Protocol  — 3 method contracts
SQLiteConnection              — get_connection()
SQLiteSessionRepository       — all 10 methods, full signatures
SQLiteNoteRepository          — all 3 methods
```

### Pydantic schema layer (30 classes)
All request/response models fully extracted with fields + types:
```
ChatRequest, ChatResponse, ChatImagePart, ToolLog
ForkRequest, ForkResponse
SessionSummary, SessionNode (recursive: children: list['SessionNode'])
FileReadResponse, FileWriteRequest, FileAppendRequest, FileListItem
RevertResponse
NoteCreateRequest, NoteResponse
LlmExportMetadata, LlmExportConfig, LlmExportTurn, LlmExportResponse
PromptModeResponse, PromptModeDetail
MessageEditRequest, MessageEditResponse, MessageDeleteResponse
TruncateRequest, TruncateResponse
SystemPromptUpdateRequest, SystemPromptResponse, SystemPromptUpdateResponse
```

### Config
```
Settings(BaseSettings) — data_dir, prompts_dir, gemini_model,
                          gemini_temperature, allowed_origins,
                          db_path(), prompt_log_path(), parse_origins()
```

### Infrastructure
```
EditError(Exception)   — custom exception class
ToolEntry @dataclass   — declaration: FunctionDeclaration, fn: Callable
```

### Composition relationships (5 detected)
```
ChatRequest      *-- ChatImagePart   (images field)
ChatResponse     *-- ToolLog         (tools_used field)
LlmExportResponse *-- LlmExportMetadata (metadata)
LlmExportResponse *-- LlmExportConfig   (config)
LlmExportResponse *-- LlmExportTurn     (turns)
```

---

## 4. Gaps & Limitations Found 🔴

### 4a. Missing inheritance edges — BaseModel / Protocol NOT in class set

**Root cause:** `BaseModel`, `BaseSettings`, `Protocol`, `Exception` are
imported from external packages. The `RelationshipEngine` only draws edges
between classes **found in the scanned source** — cross-package bases are
extracted into `ClassInfo.bases` but produce no edge in the diagram because
the target class (e.g. `BaseModel`) is not in the known-class set.

**Impact:** 34 inheritance arrows are absent:
- `Settings` → `BaseSettings`
- 30× `XxxModel` → `BaseModel`
- `SessionRepository` → `Protocol`
- `NoteRepository` → `Protocol`
- `EditError` → `Exception`

**What it looks like now (correct but incomplete):**
```
[CLASS] Settings(BaseSettings) [module=config]   ← bases listed ✅
                                                  ← no arrow to BaseSettings ❌
```

**Fix needed:** Add a `STUB` node for external well-known bases so the
diagram shows the framework lineage. Configurable via `--show-external-bases`.

### 4b. Module-level functions not surfaced

`agent.py`, `exporter.py`, `serializers.py`, `main.py`, `logger.py`
contain **important domain logic purely in module-level functions** — not classes.

Specifically missed:
```
agent.py      process_chat_turn()         ← THE core agentic loop
exporter.py   export_session_to_markdown()
              export_session_to_llm_json()
              build_config_block()
serializers.py dehydrate_history()
              hydrate_history()
main.py       30+ FastAPI route handlers
```

**Impact:** An LLM given only the diagram would miss that `agent.py` is
the agentic heart of the system — it appears completely absent.

**Fix needed:** Add a `[MODULE_FUNCTIONS]` section in TOKEN format and
a `<<module>>` stereotype node in Mermaid/PlantUML.

### 4c. Protocol vs Implementation relationship not shown

`SQLiteSessionRepository` *implements* `SessionRepository(Protocol)` — this
is architecturally significant (DIP pattern) but invisible in the diagram.
The impl class has no `bases` pointing to the Protocol because Python
structural typing doesn't require explicit declaration.

**Fix needed:** Name-pattern matching heuristic: if class name starts with
the name of a known Protocol class, emit a `IMPLEMENTS` edge.

### 4d. `ToolEntry` missing `@dataclass` detection (minor)
`ToolEntry` IS marked `@dataclass` ✅ — this worked correctly.

### 4e. Recursive type `SessionNode.children: list['SessionNode']` — forward ref
The field type is `list['SessionNode']` (string forward reference).  
The tool captures it as the literal string `list['SessionNode']` which is
correct and readable, but the RelationshipEngine's regex won't find
`SessionNode` inside `'SessionNode'` (quoted).  
**Impact:** Missing self-referential composition edge.

---

## 5. Architectural Observations from the Diagram

Reading the output as an LLM would — what can be inferred:

### Clearly visible: Clean layered architecture
```
HTTP (main.py)          — not in diagram (functions only)
    ↓
Services                — ChatService, MessageEditService, PromptManager
    ↓
Repositories (Protocol) — SessionRepository, NoteRepository
    ↓
SQLite Impls            — SQLiteSessionRepository, SQLiteNoteRepository
    ↓
Schemas (Pydantic)      — 30 request/response models
```

### Clearly visible: Rich API contract surface
The 30 Pydantic schemas make every HTTP boundary self-documenting.
An LLM can reconstruct the entire REST API from the TOKEN output alone.

### Not visible but important:
- The **agentic loop** (`process_chat_turn` in `agent.py`)
- The **Gemini SDK integration** (tool calling via `DECLARATIONS`/`FUNCTION_MAP`)
- The **serialization** concern (`dehydrate_history` / `hydrate_history`)
- The **FastAPI dependency injection** chain

---

## 6. Format Recommendations by Use Case

| Use Case | Best Format | Why |
|---|---|---|
| Paste into LLM system prompt | **TOKEN** | Most compact, structured |
| GitHub/Obsidian documentation | **Mermaid** | Renders natively |
| `dot -Tpng` → PNG image | **DOT** | Best for visual tools |
| PlantUML server / IDE plugin | **PlantUML** | Best field/method separator |
| Architecture review | **Mermaid** + TOKEN | Combined context |

### Recommended LLM prompt prefix:
```
Below is the compressed type/class surface of the kitchen-agent codebase.
Use it to understand the architecture before answering questions.
Module-level functions (agent loop, routes, serializers) are NOT shown.

[paste TOKEN output here — ~1,727 tokens]
```

---

## 7. Proposed Improvements to `py-diagram`

| Priority | Improvement | Complexity |
|---|---|---|
| HIGH | Surface module-level functions in TOKEN output | Low |
| HIGH | External base class stubs (`--show-external-bases`) | Medium |
| MEDIUM | Protocol implementation detection (name heuristic) | Low |
| MEDIUM | Forward-reference type name extraction (`'ClassName'`) | Low |
| LOW | FastAPI route extraction (decorator-based) | High |
| LOW | `USES` edges from import statements (module-level coupling) | Medium |

---

## 8. Verdict

### ✅ Strengths
- **100% class recall** — every class in the codebase was found
- **Full typed signatures** — parameters + return types on all methods
- **Field types correct** — even complex generics (`dict[str, Any]`, `list['SessionNode']`)
- **Pydantic detection** — `BaseModel` bases correctly labelled
- **Dataclass detection** — `ToolEntry @dataclass` stereotyped correctly
- **96% token compression** — from 37,833 to ~1,727 tokens
- **Zero binary deps** — pure stdlib `ast`, no Graphviz install needed to produce text

### ⚠️ Weaknesses  
- **Missing inheritance arrows** for external bases (BaseModel, Protocol, Exception)
- **Module-level functions invisible** — misses the agentic core entirely
- **No FastAPI route surfacing** — HTTP contract invisible
- **Protocol ↔ Impl** relationship not inferred

### Overall Rating: **7.5 / 10**
The tool gives an LLM a very solid contract-level understanding of the
**data layer and service layer** in ~1,700 tokens. The main blind spot is
the procedural/functional layer (agent loop, routes, serializers) which
this codebase uses heavily alongside classes.
