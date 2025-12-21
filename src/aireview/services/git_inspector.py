import subprocess


class GitInspector:
    def should_skip(self, target_range: str) -> bool:
        """Checks commit messages in the range for skip tags."""

        # FIX: 'git log' does not support --cached.
        # If we are looking at staged changes (--cached), there is no commit message yet.
        if not target_range or target_range == "--cached":
            return False

        try:
            # Get all commit messages in the range
            cmd = f"git log {target_range} --format=%B"
            output = subprocess.check_output(cmd, shell=True, text=True).lower()

            skip_tags = ["[skip-ai]", "[no-ai]", "no_ai", "[ci-skip]"]
            for tag in skip_tags:
                if tag in output:
                    return True
            return False
        except subprocess.CalledProcessError:
            return False