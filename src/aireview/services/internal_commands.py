import os
import subprocess
from ..errors import CommandError


class InternalCommandHandler:
    """Registry and executor for internal commands."""

    def __init__(self):
        self._registry = {
            "push_diff": self._push_diff
        }

    def execute(self, command_str: str) -> str:
        # command_str is like "internal:push_diff"
        action = command_str.split(":", 1)[1]

        if action not in self._registry:
            valid = ", ".join([f"internal:{k}" for k in self._registry.keys()])
            raise CommandError(f"Unknown internal command 'internal:{action}'. Available: {valid}")

        return self._registry[action]()

    def _push_diff(self) -> str:
        target = os.environ.get("AI_DIFF_TARGET", "--cached")
        buffer = []
        try:
            diff_cmd = f"git diff {target}"
            diff_output = subprocess.check_output(diff_cmd, shell=True, text=True).strip()

            if not diff_output: return ""

            buffer.append(f"=== GIT DIFF ({target}) ===")
            buffer.append(diff_output)
            buffer.append("\n=== FULL FILE CONTEXT ===")

            files_cmd = f"git diff --name-only --diff-filter=d {target}"
            files_output = subprocess.check_output(files_cmd, shell=True, text=True).strip()

            if files_output:
                for filename in files_output.splitlines():
                    if os.path.exists(filename) and os.path.isfile(filename):
                        buffer.append(f"\n--- FILE: {filename} ---")
                        try:
                            with open(filename, 'r', encoding='utf-8', errors='replace') as f:
                                buffer.append(f.read())
                        except Exception as e:
                            buffer.append(f"[Error reading file: {e}]")
            return "\n".join(buffer)
        except subprocess.CalledProcessError as e:
            raise CommandError(f"Internal push_diff failed: {e}")