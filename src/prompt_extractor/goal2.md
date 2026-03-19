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

## Phase 2: Preprocessing — Drop Thought Chunks

- When loading a file, **skip entire chunks** where `isThought == true` — they are never
  stored in memory at all
- Original files are never modified or written
- Rationale: thought chunks are internal model reasoning, irrelevant to conversation
  structure, and can be enormous in 100 MB files; dropping them entirely (not just a field)
  maximises memory savings

```python
chunks = [c for c in raw_chunks if not c.get("isThought")]
```

**Impact on model**: `ChatFile.total_chunks`, `model_turn_count`, and fingerprint sequences
all naturally exclude thought chunks because they were never loaded. No special-casing
needed anywhere downstream.

---

## Phase 3: Chunk Fingerprinting

Each chunk in a conversation gets a **content fingerprint** (CRC32 of normalized content).
Thought chunks do not reach this phase — they were dropped at load time.

| Chunk type      | What to hash                            |
|-----------------|-----------------------------------------|
| user with text  | `"user:" + text.strip()`               |
| model with text | `"model:" + text.strip()`              |
| image-only user | `"user:__image__"` (stable placeholder) |

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

The report is a **single prompt-centric document** — no metadata tables, no ASCII tree
section. The goal is to let the user read all prompts in context, see where branches
happened, and quickly navigate to the conversation they want to continue.

---

### Document structure

```
# Chat Map — <directory>
Generated: <datetime> · <N> chats

## Contents          ← clickable index, one line per chat
---
## 🌱 <root name>   ← one ## section per chat, roots before their branches
...prompts...
## 🌿 <branch name>
...prompts...
```

---

### Contents index

A simple indented list, no table:

```markdown
## Contents

- [🌱 Czym jest aforyzm_](#czym-jest-aforyzm_) · 2 prompts · 2026-03-19 13:30 → 13:32
  - [🌿 Branch of Czym jest aforyzm_](#branch-of-czym-jest-aforyzm_) · 2 prompts · 2026-03-19 13:30 → 13:31
```

Nesting mirrors the branch hierarchy. Each line has a clickable anchor to the chat section.

---

### Root chat section

```markdown
## 🌱 Czym jest aforyzm_
*2026-03-19 13:30 → 13:32*

1. Napisz mi krótko czy jest aforyzm
   > 🌿 branched here → [Branch of Czym jest aforyzm_](#branch-of-czym-jest-aforyzm_)
2. Napisz trzy aforyzmy do poniższej instrukcji
```

- All user prompts listed in order, numbered
- After any prompt that is a branch point, a blockquote line names the branch and links to it
- A prompt can be a branch point for multiple branches — one `> 🌿` line per branch

---

### Branch chat section

```markdown
## 🌿 Branch of Czym jest aforyzm_
*🌱 root: [Czym jest aforyzm_](#czym-jest-aforyzm_) · 2026-03-19 13:30 → 13:31*

> 1. Napisz mi krótko czy jest aforyzm

**2. Napisz trzy aforyzmy do poniższej instrukcji**
```

Prompt rendering rules:

| Prompt status | Rendering |
|---|---|
| Shared, unchanged | Blockquote `> N. text` — visually muted, it's inherited context |
| Shared, edited | Blockquote with marker: `> N. ~text~ → **new text**` |
| New after branch | Bold: `**N. text**` — stands out as what's new in this branch |
| Image upload | Blockquote `> N. *(image)*` or bold `**N. *(image)***` depending on status |

- `[inferred]` appended to the header line when the relationship has no explicit `branchParent`

---

### Full rendered example — real sample files

```markdown
# Chat Map — prompt_extractor/
Generated: 2026-03-19 14:00 · 2 chats

## Contents

- [🌱 Czym jest aforyzm_](#czym-jest-aforyzm_) · 2 prompts · 2026-03-19 13:30 → 13:32
  - [🌿 Branch of Czym jest aforyzm_](#branch-of-czym-jest-aforyzm_) · 2 prompts · 2026-03-19 13:30 → 13:31

---

## 🌱 Czym jest aforyzm_
*2026-03-19 13:30 → 13:32*

1. Napisz mi krótko czy jest aforyzm
   > 🌿 branched here → [Branch of Czym jest aforyzm_](#branch-of-czym-jest-aforyzm_)
2. Napisz trzy aforyzmy do poniższej instrukcji

---

## 🌿 Branch of Czym jest aforyzm_
*🌱 root: [Czym jest aforyzm_](#czym-jest-aforyzm_) · 2026-03-19 13:30 → 13:31*

> 1. Napisz mi krótko czy jest aforyzm

**2. Napisz trzy aforyzmy do poniższej instrukcji**

---
```

---

### Full rendered example — hypothetical deeper tree

```markdown
## 🌱 Topic A — Getting started
*2026-03-01 09:00 → 10:45*

1. What is this about?
2. Can you explain point 3?
   > 🌿 branched here → [Topic A — deep dive on point 3](#topic-a--deep-dive-on-point-3)
   > 🌿 branched here → [Topic A — alternative ending](#topic-a--alternative-ending)
3. Summarise everything
...

---

## 🌿 Topic A — deep dive on point 3
*🌱 root: [Topic A — Getting started](#topic-a--getting-started) · 2026-03-01 09:00 → 11:30*

> 1. What is this about?
> 2. Can you explain point 3?

**3. Go deeper on the mechanism**
**4. How does this compare to X?**
   > 🌿 branched here → [Topic A — point 3 revised tone](#topic-a--point-3-revised-tone)
**5. Give me a summary**

---

## 🌿 Topic A — point 3 revised tone  *(inferred)*
*🌱 root: [Topic A — deep dive on point 3](#topic-a--deep-dive-on-point-3) · 2026-03-02 14:00 → 14:22*

> 1. What is this about?
> 2. Can you explain point 3?
> 3. Go deeper on the mechanism
> 4. ~How does this compare to X?~ → **Compare this to X and Y**

**5. Rewrite in simpler language**
```

---

## Data Models

```python
@dataclass
class ChunkFingerprint:
    index: int    # position in loaded (non-thought) chunk list
    role: str     # "user" | "model"
    crc: int      # CRC32 of normalized content

@dataclass
class UserPrompt:
    # already exists in models.py — extended with position for report rendering
    index: int              # position in loaded chunk list
    text: str               # empty string for image-only
    is_image: bool
    branch_info: Optional[BranchInfo]  # from chunk's branchParent field

@dataclass
class ChatFile:
    path: Path
    filename: str
    user_prompts: list[UserPrompt]   # ordered, thought chunks already excluded at load
    fingerprints: list[ChunkFingerprint]
    model_turn_count: int
    first_time: Optional[datetime]
    last_time: Optional[datetime]

@dataclass
class BranchRelation:
    parent: ChatFile
    child: ChatFile
    shared_count: int                       # length of common fingerprint prefix
    unchanged: int                          # shared prompts with matching fingerprint
    modified: int                           # shared prompts with differing fingerprint
    new_count: int                          # prompts added after branch point
    branched_after_text: Optional[str]      # text of last shared user prompt
    explicit_branch_parent: Optional[str]   # promptId from chunk data, if present
    inferred: bool                          # True when no explicit branchParent confirmed it
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

1. **`test_loader.py`**
   - `test_thought_chunks_dropped` — chunks with `isThought=true` are never loaded
   - `test_non_thought_model_chunks_kept` — normal model chunks are kept
   - `test_user_prompts_extracted` — user text chunks become `UserPrompt` objects
   - `test_image_chunk_loaded` — image-only chunk becomes `UserPrompt(is_image=True, text="")`

2. **`test_fingerprint.py`**
   - `test_user_chunk_fingerprint` — same text always produces same CRC
   - `test_image_chunk_placeholder` — image-only gets a stable, non-text fingerprint
   - `test_different_texts_differ` — different text produces different CRC

3. **`test_branch.py`**
   - `test_common_prefix_identical_files` — two identical files → full shared prefix
   - `test_branch_detected_by_content` — prefix match finds parent without explicit label
   - `test_branch_detected_by_explicit_label` — explicit branchParent with no matching file
   - `test_change_marking_unchanged` — all unchanged when shared fingerprints match
   - `test_change_marking_modified` — modified count when shared fingerprint differs

4. **`test_markdown.py`**
   - `test_contents_index_nesting` — branch indented under root in contents list
   - `test_root_section_header` — root section has `🌱` and date range
   - `test_branch_point_inline` — root prompt followed by `> 🌿 branched here →` line
   - `test_branch_section_header` — branch section has `🌿` and root back-link
   - `test_shared_prompt_blockquote` — shared unchanged prompt rendered as `> N. text`
   - `test_new_prompt_bold` — new prompt rendered as `**N. text**`
   - `test_edited_prompt_strikethrough` — edited prompt rendered as `> N. ~old~ → **new**`
   - `test_inferred_label_in_header` — `*(inferred)*` in branch section header

5. **Integration** — run `chatmap prompt_extractor/` against the two real sample files,
   read the output `.md` file, and assert:
   - contents index has root + indented branch with correct anchor links
   - root section has inline `> 🌿 branched here →` after prompt 1
   - branch section shows prompt 1 as blockquote, prompt 2 as bold
