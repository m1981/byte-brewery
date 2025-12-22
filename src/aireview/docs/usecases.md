### 1. System Overview

**System Under Discussion (SuD):** `aireview` (AI Code Review CLI Tool)
**Scope:** Command-line interface, configuration management, git integration, and AI provider communication.
**Primary Actors:**
*   **Developer:** The person writing code and running the review.
*   **Git System:** The version control system triggering hooks.
*   **AI Provider:** External API (OpenAI, Anthropic, Google) providing intelligence.

---

### 2. Use Cases

#### Use Case 1: Initialize Configuration
**Goal Level:** 🌊 Sea-level (User Goal)
**Primary Actor:** Developer
**Preconditions:** Python environment is installed.
**Success Guarantee:** A valid configuration file (`ai-checks.yaml`) exists in the current directory.

**Main Success Scenario:**
1. Developer executes the initialization command (`aireview init`).
2. System checks for existing configuration file in the current directory.
3. System creates a default configuration file containing standard definitions, prompts, and checks.
4. System confirms successful initialization to the Developer.

**Extensions:**
*   *2a. Configuration file already exists:*
    *   2a1. System detects existing file.
    *   2a2. System overwrites the file with default values (based on current code logic, though typically this might warn first, the code implies a direct write/load logic).
    *   2a3. Resume at step 4.
*   *3a. File system permission error:*
    *   3a1. System reports write error.
    *   3a2. Use case ends failure.

---

#### Use Case 2: Install Git Hook
**Goal Level:** 🌊 Sea-level (User Goal)
**Primary Actor:** Developer
**Preconditions:** Current directory is a valid Git repository.
**Success Guarantee:** A `pre-push` hook is executable and configured to trigger the AI review.

**Main Success Scenario:**
1. Developer executes the install command (`aireview install`).
2. System validates the presence of a `.git` directory.
3. System generates the shell script content for the `pre-push` hook.
4. System writes the script to `.git/hooks/pre-push`.
5. System sets executable permissions on the hook file.
6. System confirms successful installation.

**Extensions:**
*   *2a. Not a git repository:*
    *   2a1. System reports error ("Not a git repository").
    *   2a2. Use case ends failure.
*   *4a. Write permission denied:*
    *   4a1. System reports failure to install hook.
    *   4a2. Use case ends failure.

---

#### Use Case 3: Run Code Review
**Goal Level:** 🌊 Sea-level (User Goal)
**Primary Actor:** Developer
**Preconditions:** Config exists.
**Success Guarantee:** Developer receives feedback.

**Main Success Scenario:**
1. Developer executes `aireview run`.
2. System checks git commit messages for skip tags (e.g., `[skip-ai]`).
3. System determines the git diff target (Staged changes, or specific commit if specified).
4. System loads configuration.
5. System iterates through checks:
    *   5.1. **(Include Use Case: Gather Context)**.
    *   5.2. System dumps the generated request to a debug file (if enabled).
    *   5.3. **(Include Use Case: Analyze with AI)**.
    *   5.4. System displays results.
6. System reports final status.

**Extensions:**
*   *2a. Skip tag found:*
    *   2a1. System prints "Skipping AI Review".
    *   2a2. Use case ends success.
*   *2b. Skip tag found BUT `--force` flag used:*
    *   2b1. System ignores the tag.
    *   2b2. Resume at step 3.
*   *3a. Specific commit SHA provided (`--commit`):*
    *   3a1. System sets diff target to `SHA^..SHA`.
    *   3a2. Resume at step 4.
*   *5.1a. Manual Context File provided (`--context-file`):*
    *   5.1a1. System skips command execution.
    *   5.1a2. System loads content from the specified file.
    *   5.1a3. Resume at step 5.2.
---

#### Use Case 4: Gather Context (Fish Level)
**Goal Level:** 🐟 Fish (Sub-function)
**Primary Actor:** System (Review Engine)
**Preconditions:** A Check Definition is selected.
**Success Guarantee:** A string buffer containing relevant code or diffs is returned.

**Main Success Scenario:**
1. System retrieves the list of Context IDs associated with the Check.
2. System iterates through each Context ID:
    *   2.1. System looks up the command definition (e.g., `git diff`).
    *   2.2. System executes the command via the shell.
    *   2.3. System captures the output.
    *   2.4. System appends output to the buffer, formatted with Markdown tags.
3. System returns the aggregated context string.

**Extensions:**
*   *2.1a. Context ID not defined in config:*
    *   2.1a1. System logs error.
    *   2.1a2. System skips this context item.
*   *2.3a. Output exceeds character limit:*
    *   2.3a1. System truncates the output.
    *   2.3a2. System appends a truncation warning.
    *   2.3a3. System stops gathering further context for this check.
    *   2.3a4. Resume at step 3.
*   *2.3b. Output is empty:*
    *   2.3b1. System warns that context returned empty output.
    *   2.3b2. Resume at step 2 (next context ID).

---

#### Use Case 5: Analyze with AI (Fish Level)
**Goal Level:** 🐟 Fish (Sub-function)
**Primary Actor:** System (Review Engine)
**Preconditions:** Context is gathered. Prompt is defined.
**Success Guarantee:** A structured JSON response (Pass/Fail) is obtained.

**Main Success Scenario:**
1. System constructs the full message (Prompt Text + Context).
2. System selects the appropriate AI Provider based on the model name (e.g., OpenAI, Anthropic).
3. System sends the message to the AI Provider API.
4. AI Provider returns the raw text response.
5. System parses the response as JSON.
6. System returns the parsed result object.

**Extensions:**
*   *2a. Dry Run mode is enabled:*
    *   2a1. System selects the Mock Provider.
    *   2a2. Mock Provider returns a static "PASS" response.
    *   2a3. Resume at step 5.
*   *3a. API Key is missing:*
    *   3a1. Provider returns a JSON error string indicating the client is not ready.
    *   3a2. Resume at step 5 (System parses this as a FAIL).
*   *3b. API Connection fails:*
    *   3b1. Provider catches exception.
    *   3b2. Provider returns a JSON error string.
    *   3b3. Resume at step 5.
*   *5a. Response is not valid JSON:*
    *   5a1. System attempts to extract JSON from Markdown code blocks.
    *   5a2. If extraction fails, System constructs a "FAIL" result object with the parsing error as the reason.
    *   5a3. Resume at step 6.

---

#### Use Case 6: Trigger Review via Git Push
**Goal Level:** 🪁 Kite (High-level Business Process)
**Primary Actor:** Developer (via Git)
**Preconditions:** `pre-push` hook is installed.
**Success Guarantee:** Push is allowed if checks pass, or rejected if checks fail.

**Main Success Scenario:**
1. Developer attempts to push code (`git push`).
2. Git System triggers the `pre-push` hook.
3. Hook script determines the diff target (remote vs local SHA).
4. Hook script executes **Use Case 3: Run Code Review**.
5. **Use Case 3** returns success (Exit Code 0).
6. Git System proceeds with the push.

**Extensions:**
*   *3a. Local SHA is zero (Branch deletion):*
    *   3a1. Hook script exits immediately with success.
    *   3a2. Git System proceeds with push.
*   *5a. **Use Case 3** returns failure (Exit Code 1):*
    *   5a1. Hook script prints "AI Review Failed."
    *   5a2. Hook script exits with failure status.
    *   5a3. Git System aborts the push.


#### Use Case 7: Debug AI Request (New)
**Goal Level:** 🐟 Fish (Sub-function)
**Primary Actor:** Developer
**Preconditions:** `aireview run` is executed with `--dump` or `--verbose`.

**Main Success Scenario:**
1. System constructs the full prompt (System Prompt + Context).
2. System generates a timestamped filename in `.aireview/debug/`.
3. System writes the full prompt content to the file.
4. System prints the file path to the console.
5. System proceeds to send the request to the AI Provider.


#### Use Case 8: Validate with Prepared Content (New)
**Goal Level:** 🌊 Sea-level
**Primary Actor:** Developer
**Preconditions:** A text file containing code or diffs exists (e.g., `test_diff.txt`).

**Main Success Scenario:**
1. Developer executes `aireview run --context-file test_diff.txt`.
2. System loads configuration.
3. System reads `test_diff.txt`.
4. System **bypasses** the standard context gathering commands (e.g., `git diff`).
5. System injects the file content as the context for the AI.
6. System performs the analysis and returns results.
7. Developer verifies if the AI behaves correctly for that specific content.


#### Use Case 9: Apply AI-Suggested Fix (Patching)
**Goal Level:** 🌊 Sea-level
**Primary Actor:** Developer
**Preconditions:** AI returns status `FIX` with `modified_files`.

**Main Success Scenario:**
1.  System receives `FIX` status and a list of modified file contents from AI.
2.  System (PatchManager) reads the corresponding local files from disk.
3.  System calculates the Unified Diff between Local File and AI Content.
4.  System saves the diff to `.aireview/patches/{timestamp}_{check_id}.patch`.
5.  System reports "FIX SUGGESTED" and displays the command to apply the patch.
6.  Developer reviews the patch file content.
7.  Developer executes `git apply <patch_file>`.
8.  Git updates the working tree with the changes.

**Extensions:**
*   **2a. AI suggests a file that doesn't exist locally:**
    *   2a1. System logs a warning.
    *   2a2. System skips diff generation for that specific file.
*   **3a. AI content is identical to local content:**
    *   3a1. System detects no diff.
    *   3a2. System reports "AI suggested fix, but no changes detected."
*   **7a. Patch fails to apply (Conflict):**
    *   7a1. Git reports a conflict error.
    *   7a2. Developer manually resolves the conflict in the code.

#### Use Case 10: Manage Artifacts across Branches
**Goal Level:** 🐟 Fish (Sub-function)
**Primary Actor:** Developer / Git System
**Preconditions:** `.aireview/` directory is added to `.gitignore`.

**Main Success Scenario:**
1.  Developer generates patches or debug logs on Branch A.
2.  Files are saved to `.aireview/patches/` and `.aireview/debug/`.
3.  Developer switches to Branch B (`git checkout branch-b`).
4.  Git ignores the `.aireview/` directory (no "untracked files" warning).
5.  Developer generates new patches on Branch B.
6.  System saves new files with new timestamps.
7.  Developer can access history from Branch A even while on Branch B (since files are local and persistent).

#### Use Case 11: Debug Context Generation
**Goal Level:** 🐟 Fish (Sub-function)
**Primary Actor:** Developer
**Preconditions:** Developer suspects the AI is receiving incorrect data.

**Main Success Scenario:**
1.  Developer runs `aireview run --dump`.
2.  System constructs the full prompt (System Prompt + Context Files + Diff).
3.  System saves the exact string sent to the API into `.aireview/debug/{timestamp}_{check_id}_req.txt`.
4.  System prints the path to the debug file.
5.  Developer opens the text file.
6.  Developer verifies if the expected code/diff is present in the text.

**Extensions:**
*   **6a. Expected code is missing:**
    *   6a1. Developer checks `ai-checks.yaml` configuration (e.g., `include_patterns`).
    *   6a2. Developer checks `git status` (is the file staged?).


#### Use Case 12: Revert AI Patch
**Goal Level:** 🌊 Sea-level
**Primary Actor:** Developer
**Preconditions:** A patch was previously applied using `git apply`. The user has **not** committed the patch yet, and may have other uncommitted work.

**Main Success Scenario:**
1.  Developer applies an AI patch (`git apply ...`).
2.  Developer runs tests or reviews code and realizes the AI broke a specific logic flow.
3.  Developer wants to undo the AI's changes **without** losing the manual code they wrote in the same file 5 minutes ago.
4.  Developer executes: `aireview revert --patch-file .aireview/patches/123.patch`.
5.  System validates that the reverse patch applies cleanly (no conflicts).
6.  System applies the reverse patch.
7.  The file is restored to its state *before* the patch, but *preserving* other uncommitted changes.

**Extensions:**
*   **5a. Conflict Detected:** (User changed the code significantly *after* applying the patch).
    *   5a1. System reports "Failed to revert patch."
    *   5a2. Developer must manually fix the code (standard git behavior).