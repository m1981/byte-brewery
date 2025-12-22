# File: src/aireview/services/patch_manager.py

import os
import time
import difflib
import logging
import subprocess
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger("aireview")


class PatchManager:
    def __init__(self, work_dir: str = ".aireview/patches"):
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)

    def generate_and_save_diff(self, check_id: str, modified_files: List[Dict[str, str]]) -> str:
        """
        Compares new content against local files, generates a Unified Diff,
        and saves it to a single patch file.
        """
        full_patch_buffer = []
        timestamp = int(time.time())

        for item in modified_files:
            file_path = item.get('path')
            new_content = item.get('content')

            if not file_path or new_content is None:
                continue

            if not os.path.exists(file_path):
                logger.warning(f"AI suggested fix for non-existent file: {file_path}")
                continue

            try:
                # Read original file
                with open(file_path, 'r', encoding='utf-8') as f:
                    original_lines = f.readlines()

                # Prepare new content (ensure it ends with newline for diff correctness)
                new_lines = new_content.splitlines(keepends=True)
                if new_lines and not new_lines[-1].endswith('\n'):
                    new_lines[-1] += '\n'

                # Generate Diff
                diff = difflib.unified_diff(
                    original_lines,
                    new_lines,
                    fromfile=f"a/{file_path}",
                    tofile=f"b/{file_path}",
                    lineterm=""
                )

                diff_text = "".join(diff)
                if diff_text:
                    full_patch_buffer.append(diff_text)

            except Exception as e:
                logger.error(f"Failed to generate diff for {file_path}: {e}")

        if not full_patch_buffer:
            return None

        # Save the combined patch
        patch_filename = self.work_dir / f"{timestamp}_{check_id}.patch"
        with open(patch_filename, "w", encoding="utf-8") as f:
            f.write("\n".join(full_patch_buffer))

        return str(patch_filename)


    def revert_patch(self, patch_path: str) -> bool:
        """
        Reverses a previously applied patch.
        Safe to use even with other uncommitted changes in the file.
        """
        if not os.path.exists(patch_path):
            logger.error(f"Patch file not found: {patch_path}")
            return False

        try:
            # 1. Check if it reverses cleanly
            subprocess.run(
                ["git", "apply", "--reverse", "--check", patch_path],
                check=True, capture_output=True
            )

            # 2. Apply reverse
            subprocess.run(
                ["git", "apply", "--reverse", patch_path],
                check=True, capture_output=True
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to revert patch (Conflict detected or not applied yet): {e}")
            return False