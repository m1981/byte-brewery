# Spec: Chat Branch Analyzer (`chatmap`)

## Overview

A CLI tool that scans a directory for AI Studio conversation files, detects branching
relationships between them using content fingerprinting, and renders a git-style hierarchy
tree showing which chat originated from which and where the conversations diverged.

---

## CLI

```
chatmap <directory> [-o OUTPUT]
```

- `<directory>` — path to scan (recursively)
- `-o OUTPUT` — output Markdown file path (default: `<directory>/chat-map.md`)
- CLI prints a single confirmation to stdout: `Written: <output path>`

---

## Phase 1: File Discovery (content-based)

- Walk `<directory>` recursively (all files, any name, any extension)
- For each file: attempt JSON parse; if valid and has `chunkedPrompt.chunks` → include it
- Files that fail JSON parse or lack the expected structure are silently skipped
- **Do not rely on filename** — the test files have no extension at all

---

## Phase 2: Preprocessing — thoughtSignature Stripping

- When loading a file into memory, strip `thoughtSignature` from every chunk and every part
- This is done **in-memory only** — original files are never modified or written
- Rationale: `thoughtSignature` fields are large opaque blobs; stripping them can reduce
  in-memory size of 100 MB conversations significantly

```python
# strip from chunk level and from each part inside the chunk
chunk.pop("thoughtSignature", None)
for part in chunk.get("parts", []):
    part.pop("thoughtSignature", None)
```

---

## Phase 3: Chunk Fingerprinting

Each chunk in a conversation gets a **content fingerprint** (CRC32 of normalized content):

| Chunk type      | What to hash                                |
|-----------------|---------------------------------------------|
| user with text  | `"user:" + text.strip()`                   |
| model with text | `"model:" + text.strip()`                  |
| image-only      | `"user:__image__"` (stable placeholder)     |
| thought chunk   | Skipped — internal reasoning, not canonical |

A **thought chunk** is identified by `isThought == true` at the chunk level.

The result for each file is an ordered list of `(index, role, fingerprint)` tuples —
the **fingerprint sequence**.

---

## Phase 4: Branch Relationship Detection

Two signals are combined; neither is trusted alone:

### Signal A — Explicit `branchParent`
Some chunks carry:
```json
"branchParent": { "promptId": "prompts/ABC...", "displayName": "Czym jest aforyzm?" }
```
This labels the chunk as the branch point and names the source conversation by its AI
Studio ID. However, no file in the directory may match that ID directly, so this signal
alone is insufficient.`

### Signal B — Content prefix matching
For every pair of files (A, B):
- Compute the length of their **longest common fingerprint prefix** (shared chunks from
  index 0 upward in the same order)
- If the shared prefix length ≥ 1, B is a **candidate branch** of A (or vice versa)
- The file with **more total chunks** (or earlier `createTime` of last chunk) is the parent
- A branch of a branch is resolved by following the chain

### Combining signals
- If explicit `branchParent` points inside a file AND content matching confirms a shared
  prefix → high confidence; use the content-matched branch point index as authoritative
- If only content matching exists (no explicit `branchParent`) → still report as branched,
  mark as `[inferred]`
- If only explicit `branchParent` exists (no matching file found in directory) →
  report as `[external branch parent: <displayName>]`

---

## Phase 5: Change Marking

For the shared prefix between a parent and a branch:

- Compare fingerprints chunk-by-chunk
- `=` — fingerprint matches (chunk unchanged in branch)
- `~` — fingerprint differs (chunk was edited in the branch copy before diverging)

Summary notation: `[=N ~M +K]`
- `N` — shared chunks that are identical
- `M` — shared chunks that were modified in the branch
- `K` — new chunks added after the branch point

**Only the summary is printed** — no message content is ever printed to screen.

---

## Phase 6: Markdown Report Output

Output is a **Markdown file** (not console). The CLI prints only a single confirmation line
to stdout: `Written: <output path>`.

The Markdown file has three sections:

---

### Section 1 — Overview table

A summary table of all discovered chat files, one row per file, sorted by `first_time`.

```markdown
# Chat Map — prompt_extractor/
Generated: 2026-03-19 14:00

## Overview

| Chat | Prompts | Turns | From | To | Role |
|------|---------|-------|------|----|------|
| [Czym jest aforyzm_](#czym-jest-aforyzm_) | 2 | 2 | 2026-03-19 13:30 | 13:32 | 🌱 root |
| [Branch of Czym jest aforyzm_](#branch-of-czym-jest-aforyzm_) | 2 | 1 | 2026-03-19 13:30 | 13:31 | 🌿 branch |
```

- `Role` column: `🌱 root` or `🌿 branch`
- Chat name is an anchor link to its detail section below

---

### Section 2 — Branch tree

A Markdown fenced code block containing the ASCII tree (for monospace rendering), followed
immediately by a Markdown-native indented list version for readability in rendered views.

**Code block (raw tree, always readable):**
````markdown
## Branch Tree

```
prompt_extractor/
│
└─ 🌱 Czym jest aforyzm_                              [root]
     2 prompts · 2 turns · 2026-03-19 13:30 → 13:32
   │
   └─ 🌿 Branch of Czym jest aforyzm_                [=4 ~0 +1]
        2 prompts · 1 turn · 2026-03-19 13:30 → 13:31
        branched after: "Napisz mi krótko czy jest aforyzm"
```
````

Tree node format (same as agreed in Phase 6 console design, now inside a code block):
- Icon: `🌱` for root, `🌿` for branch
- Filename
- `[root]` or `[=N ~M +K]` — unchanged / modified in shared prefix / new after branch
- Second line: `N prompts · N turns · YYYY-MM-DD HH:MM → HH:MM`
- Branch nodes: `branched after: "<text of last shared user prompt, ≤60 chars>"`
- When `~` > 0: `⚠ N shared chunk(s) were edited before branching`
- When relationship is inferred from content only: `[inferred]` appended to change summary

---

### Section 3 — Per-chat detail cards

One `###` subsection per chat file, in tree order (root first, then children depth-first).
Each card contains:

```markdown
### Czym jest aforyzm_

| Field | Value |
|-------|-------|
| File | `Czym jest aforyzm_` |
| Role | 🌱 root |
| Prompts | 2 |
| Turns | 2 |
| Period | 2026-03-19 13:30 → 13:32 |

**User prompts:**
1. Napisz mi krótko czy jest aforyzm
2. Napisz trzy aforyzmy do poniższej instrukcji

---

### Branch of Czym jest aforyzm_

| Field | Value |
|-------|-------|
| File | `Branch of Czym jest aforyzm_` |
| Role | 🌿 branch |
| Parent | [Czym jest aforyzm_](#czym-jest-aforyzm_) |
| Branched after | "Napisz mi krótko czy jest aforyzm" |
| Shared chunks | 4 identical, 0 modified |
| New after branch | 1 |
| Period | 2026-03-19 13:30 → 13:31 |

**User prompts:**
1. Napisz mi krótko czy jest aforyzm *(shared)*
2. Napisz trzy aforyzmy do poniższej instrukcji *(new after branch)*
```

- Each user prompt is annotated: `*(shared)*`, `*(shared, edited)*`, or `*(new after branch)*`
- Model content is **never included** — only user prompts are listed
- `*(shared, edited)*` appears when a shared prompt's fingerprint differs from the parent

---

### Field definitions

| Field | Source |
|---|---|
| Prompts | User chunks with non-empty text |
| Turns | Non-thought model reply chunks |
| Period | `createTime` of first → last chunk, local time |
| `[=N ~M +K]` | Fingerprint diff: identical / modified in shared prefix / added after branch |
| `branched after` | Text of last shared user prompt before divergence (≤60 chars) |
| `[inferred]` | No explicit `branchParent` in data; detected by content fingerprint matching only |

---

## Data Models

```python
@dataclass
class ChunkFingerprint:
    index: int         # position in original chunk list
    role: str          # "user" | "model"
    crc: int           # CRC32 of normalized content

@dataclass
class ChatFile:
    path: Path
    filename: str
    fingerprints: list[ChunkFingerprint]
    total_chunks: int   # non-thought chunks only
    user_prompt_count: int
    model_turn_count: int
    first_time: Optional[datetime]
    last_time: Optional[datetime]

@dataclass
class BranchRelation:
    parent: ChatFile
    child: ChatFile
    shared_count: int          # length of common prefix
    unchanged: int             # = in shared prefix
    modified: int              # ~ in shared prefix
    new_count: int             # chunks added after branch point
    branched_after_text: Optional[str]      # text of last shared user prompt (≤60 chars)
    explicit_branch_parent: Optional[str]   # promptId if present in data
    inferred: bool                          # True if no explicit branchParent confirmed it
```

---

## Module Structure

```
src/prompt_extractor/
    models.py          # existing + new dataclasses above
    core.py            # existing extraction logic
    fingerprint.py     # Phase 3: chunk fingerprinting
    branch.py          # Phase 4+5: relationship detection & change marking
    markdown.py        # Phase 6: Markdown report generation (overview + tree + detail cards)
    chatmap_cli.py     # CLI entry point
```

New entry point in `pyproject.toml`:
```toml
chatmap = "prompt_extractor.chatmap_cli:main"
```

---

## Testing Strategy (TDD)

Tests are written before implementation, covering:

1. **`test_fingerprint.py`**
   - `test_user_chunk_fingerprint` — text chunks hash consistently
   - `test_model_thought_chunk_skipped` — `isThought=true` chunks excluded
   - `test_image_chunk_placeholder` — image-only gets stable fingerprint
   - `test_thoughtsignature_stripped` — stripping does not change fingerprint of text

2. **`test_branch.py`**
   - `test_common_prefix_identical_files` — two copies → full shared prefix
   - `test_branch_detected_by_content` — prefix match finds parent without explicit label
   - `test_branch_detected_by_explicit_label` — explicit branchParent with no file match
   - `test_change_marking_unchanged` — all `=` when shared chunks match
   - `test_change_marking_modified` — `~` when shared chunk text differs

3. **`test_markdown.py`**
   - `test_overview_table_root` — root file gets `🌱 root` role
   - `test_overview_table_branch` — branch file gets `🌿 branch` role and anchor link
   - `test_tree_block_single_root` — single file renders `[root]` inside fenced code block
   - `test_tree_block_one_branch` — parent + child renders correct `[=N ~M +K]` line
   - `test_tree_block_nested` — grandchild indentation correct
   - `test_tree_block_inferred` — `[inferred]` appended when no explicit signal
   - `test_detail_card_root` — root card has no Parent/Branched after rows
   - `test_detail_card_branch` — branch card has Parent anchor, Branched after, shared/new counts
   - `test_prompt_annotations` — shared prompts marked `*(shared)*`, new marked `*(new after branch)*`
   - `test_edited_prompt_annotation` — modified shared prompt marked `*(shared, edited)*`

4. **Integration** — run `chatmap prompt_extractor/` against the two real sample files,
   read the output `.md` file, and assert:
   - overview table has 2 rows with correct prompt/turn counts
   - tree block contains `🌿 Branch of Czym jest aforyzm_` with `[=4 ~0 +1]`
   - branch detail card shows `branched after: "Napisz mi krótko czy jest aforyzm"`
