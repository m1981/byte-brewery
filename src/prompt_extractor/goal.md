# Specification: Conversation Branch Mapper (v2.0)

## 1. Overview
The **Conversation Branch Mapper** is a Python-based CLI application designed to parse exported LLM conversation files (specifically Google AI Studio / Gemini JSON formats). It extracts user prompts, model responses, and image uploads, and reconstructs the conversation history into a human-readable Markdown document. 

Crucially, it handles non-linear conversations (where a user edits a previous prompt to create a "branch") and offers two distinct ways to visualize this history: a chronological **Timeline View** and a grouped **Tree View**.

## 2. Input Data Schema
The application expects a JSON file containing a `chunkedPrompt` object with a `chunks` array.
*   **Fields to Extract:**
    *   `role`: `"user"` or `"model"`.
    *   `text`: The text content of the message.
    *   `createTime`: Timestamp of the message (used for sorting).
    *   `branchParent`: Metadata (`promptId`, `displayName`) indicating the user edited a previous prompt.
    *   `driveImage`: Dictionary containing an `id` for uploaded images.
*   **Fields to Ignore:**
    *   `isThought`: Boolean. **Any chunk where `isThought` is `true` must be completely ignored** (we do not want to clutter the output with the model's internal reasoning).
    *   `runSettings`, `tokenCount`, `parts`, etc.

## 3. Internal Data Models
The application will use Python `dataclasses` to represent the parsed data.

*   **`MessageNode`**
    *   `timestamp` (datetime): Parsed from `createTime`.
    *   `role` (str): "user" or "model".
    *   `text` (str): The message content.
    *   `image_id` (Optional[str]): Extracted from `driveImage`.
    *   `branch_parent` (Optional[dict]): Contains `promptId` and `displayName`.
    *   `children` (List['MessageNode']): Used for building the Tree View.

## 4. Core Processing Logic
1.  **Ingestion:** Read the JSON file and extract the `chunks` array.
2.  **Filtering:** Discard any chunk where `isThought == True`. Discard chunks that have no `text` AND no `driveImage`.
3.  **Node Creation:** Convert valid chunks into `MessageNode` objects.
4.  **Sorting:** Sort all `MessageNode` objects chronologically using `timestamp`.
5.  **Tree Building (For Tree View):** Link nodes together based on chronological order, using `branchParent` to create forks/new threads when a branch is detected.

## 5. Command Line Interface (CLI)
The CLI will be updated to handle batch processing and view switching.

**Usage:**
`python cli.py <input_path> [options]`

**Arguments:**
*   `input_path`: Path to a single file OR a directory. Files of any extension are accepted; non-JSON content is skipped silently.
*   `-o, --output`: (Optional) Output path. For `--view html` with a directory input, provide a single `.html` file to receive all lanes in one document. For `timeline`/`tree` views with a directory, provide an output directory. If omitted, prints to `stdout`.
*   `--view`: (Optional) Determines the output format.
    *   `timeline` (Default): Outputs chronologically with branch rewind markers.
    *   `tree`: Outputs grouped by conversation threads.
    *   `html`: Self-contained HTML swimlane document — each file becomes a vertical lane, branch markers shown inline, long model responses collapsible.

## 6. Output Formats (Markdown Rendering)

### Option A: Timeline View (`--view timeline`) - *Default*
This view presents the conversation exactly as it was experienced in real-time. When a branch occurs, a visual "Rewind" marker is inserted to explain the context shift.

**Example Output:**
```markdown
# Conversation Timeline

**[13:30:56] User:** 
Napisz mi krótko czy jest aforyzm

**[13:31:05] Model:** 
**Aforyzm** to krótkie, zwięzłe i błyskotliwe zdanie...

---
🔄 **[13:31:54] TIMELINE BRANCH (Rewind)**
*Branched from: "Czym jest aforyzm?"*
---

**[13:31:54] User:** 
`[Attached Image ID: 1M1J2xkyNfQbBIjqXCERObECjmzZatjhz]`
Napisz trzy aforyzmy do poniższej instrukcji

**[13:32:07] Model:** 
Oto trzy aforyzmy inspirowane tą instrukcją...
```

### Option B: Tree View (`--view tree`)
This view groups the conversation into distinct, uninterrupted threads. It is best for reading one complete version of the conversation from start to finish, followed by alternate versions.

**Example Output:**
```markdown
# Conversation Threads

## 🌿 Main Thread
**[13:30:56] User:** 
Napisz mi krótko czy jest aforyzm

**[13:31:05] Model:** 
**Aforyzm** to krótkie, zwięzłe i błyskotliwe zdanie...

---

## 🌿 Branch 1
*Branched from: "Czym jest aforyzm?"*

**[13:31:54] User:** 
`[Attached Image ID: 1M1J2xkyNfQbBIjqXCERObECjmzZatjhz]`
Napisz trzy aforyzmy do poniższej instrukcji

**[13:32:07] Model:** 
Oto trzy aforyzmy inspirowane tą instrukcją...
```