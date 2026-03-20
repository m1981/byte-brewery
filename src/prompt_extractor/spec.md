# chatmap — Specification

## Motivation

Google AI Studio lets you export conversations as JSON files. When you edit
a previous prompt you create a **branch** — a new version of the conversation
that diverges at that point. Branches are exported as separate files and share
significant history with each other, but there is no built-in way to see them
together.

**chatmap** turns a folder of exported conversation files into a single,
human-readable document so you can:

- Review what prompts you sent and what the model replied, without noise from
  internal reasoning (`isThought` chunks).
- Understand where a conversation branched and what changed.
- Compare multiple branches side-by-side.
- Keep a readable audit trail of AI-assisted work sessions.

---

## Use Cases

| # | Actor | Goal | Outcome |
|---|-------|------|---------|
| 1 | Prompt engineer | Review all prompts sent in a session | Timeline view shows every message in chronological order with timestamps |
| 2 | Prompt engineer | Understand what was changed when a branch was created | Branch rewind marker shows the fork point in the timeline |
| 3 | Researcher | Read each conversation thread from start to finish without interruption | Tree view groups messages into uninterrupted threads |
| 4 | Researcher | Compare how different branches handled the same starting context | HTML swimlane shows all branches as parallel lanes in one browser tab |
| 5 | Developer | Integrate chatmap into a script or pipeline | CLI accepts a directory and writes output to a file |

---

## Architecture Decision Records

### ADR-001 — Accept any file extension, not just `.json`

**Status:** Accepted

**Context:**
Google AI Studio exports conversation files with a `.txt` extension even
though the content is valid JSON. Restricting the directory scanner to
`*.json` silently skipped all real data files.

**Decision:**
`_find_files()` returns every regular file directly inside the target
directory. Non-JSON content is silently skipped by the JSON parser, so no
valid file is ever refused based on extension alone.

**Consequences:**
- Works with `.txt`, `.json`, or any future extension out of the box.
- Unrelated files in the directory (e.g. a README) are attempted and quietly
  dropped on parse failure.

---

### ADR-002 — `MessageNode` as the single internal data model

**Status:** Accepted

**Context:**
The original implementation had two separate dataclasses — `BranchInfo` and
`UserPrompt` — that only captured user turns. The v2.0 spec required model
responses, image attachments, timestamps, and branch relationships to all be
represented uniformly.

**Decision:**
Replace both dataclasses with a single `MessageNode`:

```python
@dataclass
class MessageNode:
    timestamp: datetime
    role: str               # "user" | "model"
    text: str
    image_id: Optional[str]
    branch_parent: Optional[dict]   # {"promptId": ..., "displayName": ...}
    children: List["MessageNode"]
```

All formatters operate on `List[MessageNode]`, which is the only type that
crosses module boundaries.

**Consequences:**
- One model to test, one model to evolve.
- `children` is available for future tree-traversal algorithms but unused by
  current formatters, which work on a flat sorted list.

---

### ADR-003 — Filter `isThought` chunks at parse time

**Status:** Accepted

**Context:**
Gemini models emit internal reasoning as separate chunks marked
`isThought: true`. Including them in output produces extremely long,
unreadable documents that obscure the actual conversation.

**Decision:**
`parse_chunks()` discards any chunk where `isThought` is truthy before
constructing `MessageNode` objects. This happens once, at ingest, so no
formatter needs to handle the flag.

**Consequences:**
- All downstream code is unaware of thought chunks.
- Thought content is permanently lost after parsing; this is intentional.

---

### ADR-004 — Sort by `createTime`, not by chunk order

**Status:** Accepted

**Context:**
The JSON `chunks` array is not guaranteed to be in chronological order.
Branches and image uploads at the same timestamp appeared out of sequence in
early tests.

**Decision:**
After filtering, all `MessageNode` objects are sorted ascending by
`timestamp` (parsed from `createTime`). Chunks with missing or unparseable
timestamps receive `datetime.min` (UTC) and sort to the top.

**Consequences:**
- Output is always chronologically correct.
- Two events at the exact same timestamp are sorted by their original array
  position (Python's `sort` is stable).

---

### ADR-005 — Three output formats behind a single `--view` flag

**Status:** Accepted

**Context:**
Different consumers need different representations of the same data:
a developer reviewing a session prefers a flat timeline; someone studying
conversation structure prefers grouped threads; visual comparison of branches
requires a browser-rendered layout.

**Decision:**
The `--view` flag selects one of three formatters:

| Value | Module | Output |
|-------|--------|--------|
| `timeline` (default) | `core.py` | Markdown, chronological, branch rewind markers |
| `tree` | `core.py` | Markdown, grouped by thread |
| `html` | `html_formatter.py` | Self-contained HTML swimlane |

Each formatter is a pure function: `(data) → str`. The CLI owns all I/O.

**Consequences:**
- Adding a new format means adding one function and one `choices` entry;
  no other code changes.
- `html_formatter.py` is kept separate because its output type and complexity
  differ substantially from the two Markdown formatters.

---

### ADR-006 — HTML swimlane: self-contained, no external dependencies

**Status:** Accepted

**Context:**
The HTML view needs to be shareable as a single file (email attachment,
saved to a wiki, opened offline). Depending on a CDN or npm bundle would
break in air-gapped or restricted environments.

**Decision:**
`format_html()` returns a single string with all CSS and JS inlined. No
framework, no CDN link, no build step. JavaScript is limited to a
progressive-enhancement collapse/expand toggle for long model responses.

**Consequences:**
- Output is one self-contained `.html` file, always works offline.
- CSS and JS live as module-level string constants in `html_formatter.py`,
  which makes them easy to read and modify but not separately testable.
- Visual regressions must be caught by manual inspection in a browser.

---

### ADR-007 — HTML swimlane: one lane per input file, not one lane per thread

**Status:** Accepted

**Context:**
Two design options were considered for the HTML view:

- **Option A:** One lane per conversation *file*.
- **Option B:** One lane per conversation *thread* (splitting branched files
  into multiple lanes).

**Decision:**
Option A. Each input file becomes exactly one lane. Branch markers appear
inline within the lane at the point of divergence.

**Consequences:**
- The mapping from file → lane is transparent; users always know which lane
  corresponds to which export.
- A branched file that contains both a main thread and a branch shows both
  in the same lane, separated by the branch marker. This is consistent with
  the tree view's behaviour.
- Option B would require cross-file deduplication logic to avoid showing the
  shared history N times, which adds significant complexity for uncertain
  benefit.

---

### ADR-008 — Directory output behaviour differs by view

**Status:** Accepted

**Context:**
When the input is a directory, the output destination has different natural
shapes depending on the view:

- `timeline` / `tree`: one Markdown file per input file → output is a
  directory of `.md` files.
- `html`: all files combined into one document → output is a single `.html`
  file.

**Decision:**
The CLI checks `--view` before deciding output shape:

- `--view html` + directory input → `-o` must point to a single file (or
  stdout). All conversations are collected first, then passed together to
  `format_html()`.
- `--view timeline|tree` + directory input → `-o` is treated as a directory;
  one `.md` is written per input file.

**Consequences:**
- Matches user mental model: html feels like "one report", markdown feels
  like "one file per conversation".
- The `-o` flag means different things depending on `--view`, which requires
  clear documentation.
