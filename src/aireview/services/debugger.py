import os
import time
from pathlib import Path


class Debugger:
    def __init__(self, enabled: bool):
        self.enabled = enabled
        self.debug_dir = Path(".aireview/debug")

    def dump_request(self, check_id: str, content: str):
        if not self.enabled: return

        self.debug_dir.mkdir(parents=True, exist_ok=True)
        timestamp = int(time.time())
        filename = self.debug_dir / f"{timestamp}_{check_id}_req.txt"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"  [DEBUG] Request dumped to: {filename}")