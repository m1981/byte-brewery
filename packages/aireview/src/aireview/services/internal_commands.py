# File: src/aireview/services/internal_commands.py

import os
import subprocess
import fnmatch
import logging
from typing import List, Optional
from ..errors import CommandError

# <--- 2. Initialize Logger
logger = logging.getLogger("aireview")

class InternalCommandHandler:
    """Registry and executor for internal commands with support for file filtering."""

    def __init__(self):
        self._registry = {
            "push_diff": self._push_diff,  # Legacy (Diff + Content)
            "git_diff": self._git_diff_only,  # New: Just the diff
            "changed_files_content": self._full_content  # New: Just the full files
        }

    def execute(self, command_str: str, include: Optional[List[str]] = None,
                exclude: Optional[List[str]] = None) -> str:
        try:
            prefix, action = command_str.split(":", 1)
        except ValueError:
            raise CommandError(f"Invalid internal command format: '{command_str}'. Expected 'internal:action'")

        if action not in self._registry:
            valid = ", ".join([f"internal:{k}" for k in self._registry.keys()])
            raise CommandError(f"Unknown internal command 'internal:{action}'. Available: {valid}")

        return self._registry[action](include, exclude)

    # --- Helper to get file list ---
    def _get_changed_files(self, target: str, include: Optional[List[str]], exclude: Optional[List[str]]) -> List[str]:
        try:
            # --diff-filter=d excludes deleted files
            files_cmd = f"git diff --name-only --diff-filter=d {target}"
            logger.debug(f"command: {files_cmd}")
            files_output = subprocess.check_output(files_cmd, shell=True, text=True).strip()

            if not files_output:
                logger.debug(f"No changed files found for target: {target}")
                return []

            all_files = files_output.splitlines()

            # --- IMPROVED LOGGING START ---
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Found {len(all_files)} changed files:")
                for f in all_files:
                    logger.debug(f"  {f}")
            # --- IMPROVED LOGGING END ---

            filtered = self._filter_files(all_files, include, exclude)

            if logger.isEnabledFor(logging.DEBUG) and len(filtered) != len(all_files):
                logger.debug(f"Files remaining after filter ({len(filtered)}):")
                for f in filtered:
                    logger.debug(f"  ✓ {f}")

            return filtered

        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {e}")
            return []

    # --- Command Implementations ---

    def _git_diff_only(self, include: Optional[List[str]] = None, exclude: Optional[List[str]] = None) -> str:
        """Returns ONLY the git diff for the filtered files."""
        target = os.environ.get("AI_DIFF_TARGET", "--cached")
        valid_files = self._get_changed_files(target, include, exclude)

        if not valid_files: return ""

        path_args = " ".join(f"'{f}'" for f in valid_files)
        diff_cmd = f"git diff {target} -- {path_args}"
        try:
            return subprocess.check_output(diff_cmd, shell=True, text=True).strip()
        except subprocess.CalledProcessError as e:
            raise CommandError(f"Git diff failed: {e}")

    def _full_content(self, include: Optional[List[str]] = None, exclude: Optional[List[str]] = None) -> str:
        """Returns ONLY the full content of the changed files."""
        target = os.environ.get("AI_DIFF_TARGET", "--cached")
        valid_files = self._get_changed_files(target, include, exclude)

        if not valid_files: return ""

        buffer = []
        for filename in valid_files:
            if os.path.exists(filename) and os.path.isfile(filename):
                buffer.append(f"\n=== FILE: {filename} ===")
                try:
                    with open(filename, 'r', encoding='utf-8', errors='replace') as f:
                        buffer.append(f.read())
                except Exception as e:
                    buffer.append(f"[Error reading file: {e}]")

        return "\n".join(buffer)

    def _push_diff(self, include: Optional[List[str]] = None, exclude: Optional[List[str]] = None) -> str:
        """Legacy: Combines Diff AND Full Content."""
        diff = self._git_diff_only(include, exclude)
        content = self._full_content(include, exclude)

        if not diff and not content: return ""

        return f"=== GIT DIFF ===\n{diff}\n\n=== FULL FILE CONTEXT ===\n{content}"

    def _filter_files(self, files: List[str], include: Optional[List[str]], exclude: Optional[List[str]]) -> List[str]:
        filtered = []
        for filename in files:
            # Step 1: Check Include
            if include:
                matched_include = False
                for pattern in include:
                    if fnmatch.fnmatch(filename, pattern):
                        matched_include = True
                        break
                if not matched_include:
                    logger.debug(f"Excluded '{filename}' (Not in include patterns)")
                    continue

            # Step 2: Check Exclude
            if exclude:
                matched_exclude = False
                for pattern in exclude:
                    if fnmatch.fnmatch(filename, pattern):
                        matched_exclude = True
                        break
                if matched_exclude:
                    logger.debug(f"Excluded '{filename}' (Matched exclude pattern)")
                    continue

            filtered.append(filename)
        return filtered