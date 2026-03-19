# Spec: Chat Branch Analyzer (`chatmap`)

## Overview

A CLI tool that scans a directory for AI Studio conversation files, detects branching
relationships between them using content fingerprinting, and renders a git-style hierarchy
tree showing which chat originated from which and where the conversations diverged.

---

## CLI

```
chatmap <directory>
```

- `<directory>` — path to scan (recursively)
- No flags needed for MVP; `--no-strip-signatures` could opt out of thoughtSignature removal

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

## Phase 6: Visualization

Output a tree in the style of `git log --graph`. Each node shows:
- Filename (relative to scanned directory)
- Total chunk count (excluding thought chunks)
- Change summary relative to parent

```
prompt_extractor/
├─ Czym jest aforyzm_                  [root]  7 chunks
│  └─ Branch of Czym jest aforyzm_    [=4 ~0 +1]  5 chunks
```

Multiple roots and deeper nesting are supported:
```
chats/
├─ Topic A                             [root]  12 chunks
│  ├─ Topic A — variation 1           [=6 ~0 +4]  10 chunks
│  │  └─ Topic A — variation 1b       [=8 ~1 +2]  11 chunks  [inferred]
│  └─ Topic A — variation 2           [=6 ~2 +0]  8 chunks
└─ Topic B                             [root]  5 chunks
```

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
    total_chunks: int  # non-thought chunks only

@dataclass
class BranchRelation:
    parent: ChatFile
    child: ChatFile
    shared_count: int          # length of common prefix
    unchanged: int             # = in shared prefix
    modified: int              # ~ in shared prefix
    new_count: int             # chunks added after branch point
    explicit_branch_parent: Optional[str]   # promptId if present in data
    inferred: bool             # True if no explicit branchParent confirmed it
```

---

## Module Structure

```
src/prompt_extractor/
    models.py          # existing + new dataclasses above
    core.py            # existing extraction logic
    fingerprint.py     # Phase 3: chunk fingerprinting
    branch.py          # Phase 4+5: relationship detection & change marking
    tree.py            # Phase 6: ASCII tree rendering
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

3. **`test_tree.py`**
   - `test_single_root_no_branches` — single file renders as `[root]`
   - `test_one_branch` — parent + one child renders correctly
   - `test_nested_branches` — grandchild indentation is correct
   - `test_inferred_label` — `[inferred]` appears when no explicit signal

4. **Integration** — run `chatmap prompt_extractor/` against the two real sample files
   and assert the output contains the correct tree structure.
