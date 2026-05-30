# Code Surfacing Techniques for Agentic LLM Models

## What is Code Surfacing?

Code surfacing is the art of **extracting, indexing, and presenting code structure** to LLMs in a way that maximizes comprehension while minimizing token usage. The goal is to give an agent the *right* context about a codebase without dumping raw source.

---

## Techniques

### 1. **AST-Based Skeleton Extraction**
Parse Python source into Abstract Syntax Trees and emit only signatures — class names, method signatures, docstrings, type annotations — stripping bodies.

**Tools/Libs:**
- `ast` (stdlib) — parse to AST, walk nodes
- `libcst` — concrete syntax tree, preserves formatting, safer transforms
- `typed_ast` — legacy but type-annotation aware
- `astroid` — used by pylint, richer semantic model

```python
# Output: class Foo: def bar(self, x: int) -> str: ...
```

---

### 2. **Type & Dependency Graph Construction**
Build a directed graph of **which types reference which**, inheritance chains, import dependencies, call graphs.

**Tools/Libs:**
| Library | Purpose |
|---|---|
| `pydeps` | Module-level import dependency graph → PNG/SVG |
| `pyreverse` (pylint) | Class diagrams → PlantUML / dot |
| `networkx` | In-memory graph analysis (cycles, centrality) |
| `graphviz` | Render `.dot` files |
| `importlab` | Static import resolution |
| `modulegraph` | Dependency graph from entry points |
| `snakefood` | File-level dependency graph |
| `pipdeptree` | Package dependency tree |
| `mypy` + daemon | Full type inference graph |
| `pyright` | LSP-level type graph, faster than mypy |

---

### 3. **Symbol Index / Code Map**
Flat or hierarchical index: `module → class → method → signature + docstring`.

**Tools/Libs:**
- `jedi` — completion + inference engine, powers most IDEs
- `rope` — refactoring + symbol resolution
- `pygments` — tokenizer for lightweight indexing
- `ctags` / `universal-ctags` — fast symbol extraction
- `tree-sitter` — incremental parser, language-agnostic, extremely fast

---

### 4. **Semantic Chunking + Embedding**
Split code at *meaningful boundaries* (function/class level), embed each chunk, build vector index for retrieval.

**Tools/Libs:**
- `langchain` splitters — `PythonCodeTextSplitter`
- `llama-index` — `CodeSplitter` node parser
- `chroma` / `qdrant` / `weaviate` — vector stores
- `voyage-code-2` / `text-embedding-3-large` — code-optimized embeddings
- `instructor` — structured extraction from code

---

### 5. **Call Graph Analysis**
Trace which functions call which — dynamic or static.

**Tools/Libs:**
- `pycallgraph2` — runtime call graph → PNG
- `py-call-graph` — similar
- `callgraph` — static analysis
- `vulture` — finds dead code
- `prospector` — aggregates pylint, pyflakes, dodgy

---

### 6. **Incremental / LSP-Based Surfacing**
Use Language Server Protocol to query definitions, references, hover info — exactly what IDEs do.

**Tools/Libs:**
- `pylsp` (python-lsp-server)
- `pyright` LSP mode
- `jedi-language-server`
- `multilspy` (Microsoft, designed for agents)

---

### 7. **Diagram Generation**
Produce visual or textual diagrams from code.

**Tools/Libs:**
| Tool | Output |
|---|---|
| `pyreverse` | PlantUML / Graphviz class diagrams |
| `erdantic` | Pydantic/dataclass ER diagrams |
| `diagrams` | Cloud architecture as code |
| `plantuml` python lib | Generate UML from `.puml` |
| `mermaid` (via codegen) | Markdown-embeddable diagrams |
| `sphinx-apidoc` + autodoc | Full API docs with inheritance |
| `pdoc3` | Lightweight HTML API docs |

---

### 8. **Compressed Context Representation (for LLMs)**
The most advanced technique — produce a **minimal, structured, token-efficient** representation:

```
[MODULE] myapp.core
  [CLASS] UserService(BaseService)
    deps: UserRepo, EmailClient
    [METHOD] create_user(name: str, email: str) -> User
    [METHOD] delete_user(user_id: UUID) -> None
  [DATACLASS] User
    id: UUID, name: str, email: str
```

---

## My Recommended Stack for an Agent-Facing Code Surfacer

```
tree-sitter          # fast incremental parsing
libcst               # safe transforms + skeleton extraction
networkx             # dependency graph algorithms
pyreverse / erdantic # diagram generation
jedi / multilspy     # live LSP queries
chromadb             # semantic search over chunks
```

---

## Recommended Implementation Architecture

```
code_surface/
├── skeleton/
│   ├── ast_extractor.py       # AST-based signature extraction
│   └── libcst_extractor.py    # CST-based safer extraction
├── graph/
│   ├── dependency_builder.py  # import + type dependency graph
│   └── call_graph.py          # function call graph
├── index/
│   ├── symbol_index.py        # flat symbol map
│   └── semantic_index.py      # embedding-based search
├── diagram/
│   ├── mermaid_renderer.py    # Mermaid diagram output
│   └── plantuml_renderer.py   # PlantUML output
├── serializer/
│   └── llm_context.py         # compressed LLM-optimized output
└── surface.py                 # unified CodeSurface façade
```

---

## Possible Implementation Directions

| # | Component | Description |
|---|---|---|
| 1 | **`CodeSkeletonExtractor`** | AST-based signature extractor — classes, methods, types, docstrings |
| 2 | **`DependencyGraphBuilder`** | Type/class/module dependency graph with NetworkX |
| 3 | **`SemanticCodeIndex`** | Chunked + embedded code for RAG retrieval |
| 4 | **`CodeContextSerializer`** | LLM-optimized compressed representation |
| 5 | **All of the above** | Unified `CodeSurface` library façade |

---

## Quick Reference: Choose Your Tool by Goal

| Goal | Best Tool |
|---|---|
| Fast signature extraction | `ast` + `tree-sitter` |
| Safe code transforms | `libcst` |
| Class/type diagrams | `pyreverse`, `erdantic` |
| Import dependency graph | `pydeps`, `networkx` |
| Semantic code search | `llama-index` + `chromadb` |
| Call graph | `pycallgraph2` |
| LSP-level queries (agent) | `multilspy`, `jedi` |
| Mermaid diagrams | custom codegen over AST |
| Token-efficient LLM context | custom `CodeContextSerializer` |
